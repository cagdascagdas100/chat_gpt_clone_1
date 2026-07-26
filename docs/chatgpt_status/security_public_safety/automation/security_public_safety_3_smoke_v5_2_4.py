from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import BinaryIO

BASE_PATH = Path(__file__).with_name("security_public_safety_3_smoke_v5_2.py")
TASK_VERSION = "5.2.4-low-memory-canonical-streaming"
ATTEMPT_ID = "security-public-safety-3-20260721-013"
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
FEATURES_ARRAY_RE = re.compile(br'"features"\s*:\s*\[')
DEFAULT_CHUNK_BYTES = 1024 * 1024
LARGE_JSON_THRESHOLD_BYTES = 8 * 1024 * 1024

STREAM_METRICS: dict[str, object] = {
    "enabled": True,
    "canonical_full_json_load_avoided": False,
    "chunk_bytes": DEFAULT_CHUNK_BYTES,
    "features_scanned": 0,
    "targets_found": [],
    "max_feature_object_bytes": 0,
    "source_path": None,
    "error": None,
}


def load_base():
    spec = importlib.util.spec_from_file_location("security_public_safety_3_smoke_v5_2_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load V5.2 base verifier: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _find_features_array(handle: BinaryIO, chunk_bytes: int) -> tuple[bytes, int] | None:
    tail = b""
    absolute_read = 0
    overlap = 128
    while True:
        chunk = handle.read(chunk_bytes)
        if not chunk:
            return None
        data = tail + chunk
        match = FEATURES_ARRAY_RE.search(data)
        if match:
            after = data[match.end():]
            absolute_array_offset = absolute_read - len(tail) + match.end()
            return after, absolute_array_offset
        absolute_read += len(chunk)
        tail = data[-overlap:]


def stream_target_features(
    path: Path,
    target_ids: list[str],
    chunk_bytes: int = DEFAULT_CHUNK_BYTES,
) -> tuple[dict[str, dict], dict]:
    targets = set(target_ids)
    found: dict[str, dict] = {}
    metrics: dict[str, object] = {
        "parser": "binary-feature-object-stream-v1",
        "chunk_bytes": chunk_bytes,
        "features_array_found": False,
        "features_scanned": 0,
        "targets_found": [],
        "max_feature_object_bytes": 0,
        "source_path": str(path),
        "source_size_bytes": None,
        "stopped_after_all_targets": False,
        "error": None,
    }
    try:
        metrics["source_size_bytes"] = path.stat().st_size
        with path.open("rb") as handle:
            located = _find_features_array(handle, chunk_bytes)
            if located is None:
                metrics["error"] = "FEATURES_ARRAY_NOT_FOUND"
                return found, metrics
            initial, _ = located
            metrics["features_array_found"] = True
            pending = initial
            root_object = bytearray()
            depth = 0
            in_string = False
            escaped = False
            array_done = False

            while True:
                if not pending:
                    pending = handle.read(chunk_bytes)
                    if not pending:
                        break
                position = 0
                pending_length = len(pending)
                while position < pending_length:
                    byte = pending[position]
                    position += 1
                    if depth == 0:
                        if byte in b" \t\r\n,":
                            continue
                        if byte == ord("]"):
                            array_done = True
                            break
                        if byte != ord("{"):
                            metrics["error"] = f"UNEXPECTED_FEATURE_TOKEN_{byte}"
                            return found, metrics
                        root_object = bytearray(b"{")
                        depth = 1
                        in_string = False
                        escaped = False
                        continue

                    root_object.append(byte)
                    if in_string:
                        if escaped:
                            escaped = False
                        elif byte == ord("\\"):
                            escaped = True
                        elif byte == ord('"'):
                            in_string = False
                        continue
                    if byte == ord('"'):
                        in_string = True
                    elif byte == ord("{"):
                        depth += 1
                    elif byte == ord("}"):
                        depth -= 1
                        if depth == 0:
                            metrics["features_scanned"] = int(metrics["features_scanned"]) + 1
                            metrics["max_feature_object_bytes"] = max(
                                int(metrics["max_feature_object_bytes"]), len(root_object)
                            )
                            try:
                                feature = json.loads(root_object.decode("utf-8"))
                            except Exception as exc:
                                metrics["error"] = f"FEATURE_JSON_PARSE_FAILED: {exc}"
                                return found, metrics
                            if isinstance(feature, dict):
                                props = feature.get("properties") or {}
                                if isinstance(props, dict):
                                    parcel_id = props.get("security_parcel_id") or props.get("parcel_id")
                                    if parcel_id in targets:
                                        found[str(parcel_id)] = feature
                                        metrics["targets_found"] = sorted(found)
                                        if len(found) == len(targets):
                                            metrics["stopped_after_all_targets"] = True
                                            return found, metrics
                            root_object = bytearray()
                if array_done:
                    break
                pending = b""
    except Exception as exc:
        metrics["error"] = str(exc)
    return found, metrics


def make_low_memory_locator(core):
    def locate_targets(materialized_path: Path | None = None):
        found: dict[str, dict] = {}
        audit: list[dict] = []
        for path in core.source_candidates(materialized_path):
            try:
                size = path.stat().st_size
            except OSError as exc:
                audit.append({"path": str(path), "decision": "STAT_FAILED", "error": str(exc)})
                continue
            if path.name == "parcel_security_scores_verified.geojson" and size < 1024 * 1024:
                audit.append({"path": str(path), "decision": "SKIP_KNOWN_SMALL_UNUSABLE_VERIFIED_OUTPUT"})
                continue

            use_streaming = bool(
                size >= LARGE_JSON_THRESHOLD_BYTES
                or (materialized_path is not None and path == materialized_path)
            )
            if use_streaming:
                streamed, metrics = stream_target_features(path, list(core.TARGET_IDS))
                found.update(streamed)
                audit.append({
                    "path": str(path),
                    "decision": "STREAM_PARSED",
                    "targets_found": sorted(found),
                    "stream_metrics": metrics,
                })
                if materialized_path is not None and path == materialized_path:
                    STREAM_METRICS.update(metrics)
                    STREAM_METRICS["canonical_full_json_load_avoided"] = True
                if len(found) == len(core.TARGET_IDS):
                    return path, found, audit
                continue

            if not core.file_contains_targets(path):
                audit.append({"path": str(path), "decision": "NO_TARGET_ID_TEXT"})
                continue
            try:
                with path.open("r", encoding="utf-8-sig") as handle:
                    payload = json.load(handle)
            except Exception as exc:
                audit.append({"path": str(path), "decision": "JSON_PARSE_FAILED", "error": str(exc)})
                continue
            features = payload.get("features") if isinstance(payload, dict) else None
            if not isinstance(features, list):
                audit.append({"path": str(path), "decision": "NO_FEATURE_ARRAY"})
                continue
            for feature in features:
                props = feature.get("properties") or {}
                parcel_id = props.get("security_parcel_id") or props.get("parcel_id")
                if parcel_id in core.TARGET_IDS:
                    found[parcel_id] = feature
            audit.append({"path": str(path), "decision": "SMALL_JSON_PARSED", "targets_found": sorted(found)})
            if len(found) == len(core.TARGET_IDS):
                return path, found, audit
        return None, found, audit

    return locate_targets


def enrich_outputs(repo_root: Path) -> None:
    output_path = repo_root / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_candidates_v5_2_latest.json"
    reconciliation_path = repo_root / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_reconciliation_v5_2_latest.json"
    website_path = repo_root / "england_map_web/data/security_public_safety/security_public_safety_3_smoke_rows_latest.json"

    for path in (output_path, website_path):
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["task_version"] = TASK_VERSION
        payload["attempt_id"] = ATTEMPT_ID
        payload["low_memory_streaming_extractor"] = dict(STREAM_METRICS)
        payload["strict_gate_version"] = (
            "exact-blob-low-memory-stream-point-numeric-force-lookup-territorial-coverage-"
            "list-payload-sha256-iod25-fields-v3"
        )
        payload["success_rule"] = (
            "exit zero only when the exact blob is streamed without full JSON loading, ordered identity, "
            "valid latest-month metadata, accepted force lookup and territorial coverage, strict API lists, "
            "strict IoD fields, core success, null suppression and at least one strict 4/4 row are all present"
        )
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if reconciliation_path.is_file():
        payload = json.loads(reconciliation_path.read_text(encoding="utf-8"))
        payload["task_version"] = TASK_VERSION
        payload["attempt_id"] = ATTEMPT_ID
        payload["low_memory_streaming_extractor"] = dict(STREAM_METRICS)
        payload["requires_canonical_full_json_load_avoided"] = True
        payload["canonical_full_json_load_avoided"] = bool(
            STREAM_METRICS.get("canonical_full_json_load_avoided")
        )
        reconciliation_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def main() -> int:
    base = load_base()
    original_load_core = base.load_core

    def patched_load_core():
        core = original_load_core()
        core.locate_targets = make_low_memory_locator(core)
        return core

    base.load_core = patched_load_core
    base.TASK_VERSION = TASK_VERSION
    base.ATTEMPT_ID = ATTEMPT_ID

    stale_temp = Path(tempfile.gettempdir()) / "aays_security_public_safety_slot3_smoke_v5_2_3"
    shutil.rmtree(stale_temp, ignore_errors=True)
    return_code = int(base.main())

    repo_root = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
    enrich_outputs(repo_root)

    print("LOW_MEMORY_STREAMING_ENABLED=true")
    print(f"CANONICAL_FULL_JSON_LOAD_AVOIDED={bool(STREAM_METRICS.get('canonical_full_json_load_avoided'))}")
    print(f"STREAM_FEATURES_SCANNED={STREAM_METRICS.get('features_scanned', 0)}")
    print(f"STREAM_TARGETS_FOUND={len(STREAM_METRICS.get('targets_found') or [])}")
    print(f"ATTEMPT_ID={ATTEMPT_ID}")
    print("FINAL_READY=false")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())

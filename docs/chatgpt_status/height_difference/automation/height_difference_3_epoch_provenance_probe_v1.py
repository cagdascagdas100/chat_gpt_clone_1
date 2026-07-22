from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_3"
SOURCE_BRANCH = "codex/aays-single-runner-v5-20260706"
SOURCE_PATH = "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
EXPECTED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
RUNNER_OUTPUT = Path("docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_epoch_provenance_probe_latest.json")
WEBSITE_OUTPUT = Path("england_map_web/data/height_difference/height_difference_3_epoch_provenance_probe_latest.json")
MAX_PREFIX_BYTES = 2 * 1024 * 1024
FEATURES_MARKER = re.compile(br'\"features\"\s*:\s*\[')


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(repo: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
        encoding="utf-8" if text else None,
        errors="replace" if text else None,
    )


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = Path(tmp.name)
    os.replace(tmp_name, path)


def parse_metadata_prefix(prefix: bytes) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    match = FEATURES_MARKER.search(prefix)
    if not match:
        return None, ["FEATURES_MARKER_NOT_FOUND_IN_BOUNDED_PREFIX"]
    header = prefix[: match.start()].rstrip()
    if header.endswith(b","):
        header = header[:-1]
    candidate = header + b"}"
    try:
        root = json.loads(candidate.decode("utf-8"))
    except Exception as exc:
        return None, [f"METADATA_PREFIX_JSON_PARSE_FAILED:{exc}"]
    metadata = root.get("metadata") if isinstance(root, dict) else None
    if not isinstance(metadata, dict):
        errors.append("METADATA_OBJECT_MISSING")
        return None, errors
    return metadata, errors


def read_bounded_prefix(repo: Path) -> tuple[bytes, int]:
    proc = subprocess.Popen(
        ["git", "-C", str(repo), "cat-file", "blob", EXPECTED_BLOB_SHA],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None
    prefix = bytearray()
    while len(prefix) < MAX_PREFIX_BYTES:
        chunk = proc.stdout.read(min(65536, MAX_PREFIX_BYTES - len(prefix)))
        if not chunk:
            break
        prefix.extend(chunk)
        if FEATURES_MARKER.search(prefix):
            break
    proc.kill()
    proc.wait(timeout=10)
    return bytes(prefix), len(prefix)


def main() -> int:
    raw_root = os.environ.get("AAYS_REPO_ROOT")
    errors: list[str] = []
    if not raw_root:
        raise SystemExit("AAYS_REPO_ROOT_REQUIRED")
    repo = Path(raw_root).resolve()

    object_type = None
    object_size = None
    path_blob_sha = None
    metadata: dict[str, Any] | None = None
    prefix_sha256 = None
    prefix_bytes = 0
    history_rows: list[dict[str, str]] = []

    try:
        object_type = run_git(repo, "cat-file", "-t", EXPECTED_BLOB_SHA).stdout.strip()
        object_size = int(run_git(repo, "cat-file", "-s", EXPECTED_BLOB_SHA).stdout.strip())
        path_blob_sha = run_git(repo, "rev-parse", f"{SOURCE_BRANCH}:{SOURCE_PATH}").stdout.strip()
    except Exception as exc:
        errors.append(f"GIT_OBJECT_PROBE_FAILED:{exc}")

    if object_type != "blob":
        errors.append(f"OBJECT_TYPE_MISMATCH:{object_type}")
    if path_blob_sha != EXPECTED_BLOB_SHA:
        errors.append(f"PATH_BLOB_MISMATCH:{path_blob_sha}")

    if not errors:
        try:
            prefix, prefix_bytes = read_bounded_prefix(repo)
            prefix_sha256 = hashlib.sha256(prefix).hexdigest()
            metadata, parse_errors = parse_metadata_prefix(prefix)
            errors.extend(parse_errors)
        except Exception as exc:
            errors.append(f"METADATA_PREFIX_PROBE_FAILED:{exc}")

        try:
            history = run_git(
                repo,
                "log",
                "--follow",
                "--format=%H%x09%aI%x09%cI%x09%s",
                SOURCE_BRANCH,
                "--",
                SOURCE_PATH,
            ).stdout
            for line in history.splitlines()[:50]:
                parts = line.split("\t", 3)
                if len(parts) == 4:
                    history_rows.append({
                        "commit_sha": parts[0],
                        "author_time": parts[1],
                        "commit_time": parts[2],
                        "subject": parts[3],
                    })
        except Exception as exc:
            errors.append(f"GIT_HISTORY_PROBE_FAILED:{exc}")

    metadata_keys = sorted(metadata.keys()) if isinstance(metadata, dict) else []
    crs_keys = [
        key
        for key in metadata_keys
        if any(token in key.lower() for token in ("crs", "datum", "epoch", "reference_frame", "coordinate_system", "etrs", "wgs"))
    ]
    explicit_epoch_fields = {
        key: metadata[key]
        for key in crs_keys
        if "epoch" in key.lower()
    } if isinstance(metadata, dict) else {}
    explicit_crs_fields = {
        key: metadata[key]
        for key in crs_keys
        if any(token in key.lower() for token in ("crs", "datum", "reference_frame", "coordinate_system", "etrs", "wgs"))
    } if isinstance(metadata, dict) else {}

    authoritative_epoch_proven = bool(explicit_epoch_fields and explicit_crs_fields)
    accepted = False
    blockers = []
    if not authoritative_epoch_proven:
        blockers.append("CANONICAL_POINT_CRS_EPOCH_PROVENANCE_NOT_CONFIRMED")
    blockers.append("HUMAN_REVIEWED_EPOCH_POLICY_FILE_REQUIRED")

    report: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "probe_id": "height-difference-3-epoch-provenance-probe-v1-20260722",
        "generated_at": utc_now(),
        "source": {
            "branch": SOURCE_BRANCH,
            "path": SOURCE_PATH,
            "expected_blob_sha": EXPECTED_BLOB_SHA,
            "resolved_path_blob_sha": path_blob_sha,
            "object_type": object_type,
            "object_size_bytes": object_size,
            "bounded_prefix_bytes": prefix_bytes,
            "bounded_prefix_sha256": prefix_sha256,
        },
        "geojson_standard_semantics": {
            "coordinate_order": "longitude_latitude",
            "datum_label": "WGS84_CRS84_PER_RFC7946",
            "observation_epoch_disclosed_by_rfc7946": False,
            "etrs89_equivalence_implied": False,
        },
        "embedded_metadata": metadata,
        "embedded_metadata_keys": metadata_keys,
        "explicit_crs_fields": explicit_crs_fields,
        "explicit_epoch_fields": explicit_epoch_fields,
        "git_history": history_rows,
        "history_commit_count_returned": len(history_rows),
        "decision": {
            "authoritative_epoch_proven": authoritative_epoch_proven,
            "accepted": accepted,
            "policy": "UNKNOWN_FAIL_CLOSED",
            "reason": "Neither RFC7946 WGS84 labelling nor file/commit timestamps establish an observation epoch or authoritative ETRS89 lineage.",
            "blockers": blockers,
        },
        "errors": errors,
        "actual_business_data_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    atomic_write_json(repo / RUNNER_OUTPUT, report)
    atomic_write_json(repo / WEBSITE_OUTPUT, report)
    print(f"EPOCH_PROVENANCE_PROBE_ERRORS={len(errors)}")
    print("EPOCH_PROVENANCE_ACCEPTED=false")
    print("EPOCH_POLICY=UNKNOWN_FAIL_CLOSED")
    print("FINAL_READY=false")
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())

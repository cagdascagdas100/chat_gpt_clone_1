from __future__ import annotations

import importlib.util
import json
import mmap
import os
from pathlib import Path

BASE_PATH = Path(__file__).with_name("security_public_safety_3_smoke_v5_2_4.py")
TASK_VERSION = "5.2.5-memory-safe-canonical-sha256"
ATTEMPT_ID = "security-public-safety-3-20260721-014"
CANONICAL_FILENAME = "parcel_security_scores_rechecked_0_120m_spatial.geojson"
LARGE_FILE_THRESHOLD_BYTES = 8 * 1024 * 1024

MEMORY_SAFE_HASH_METRICS: dict[str, object] = {
    "enabled": True,
    "canonical_full_heap_read_avoided": False,
    "mmap_sha256_used": False,
    "intercepted_path": None,
    "intercepted_size_bytes": None,
    "fallback_read_bytes_count": 0,
    "error": None,
}


def load_base():
    spec = importlib.util.spec_from_file_location("security_public_safety_3_smoke_v5_2_4_base", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load V5.2.4 verifier: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def post_enrich(repo_root: Path, original_return_code: int) -> int:
    output_path = repo_root / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_candidates_v5_2_latest.json"
    reconciliation_path = repo_root / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_reconciliation_v5_2_latest.json"
    website_path = repo_root / "england_map_web/data/security_public_safety/security_public_safety_3_smoke_rows_latest.json"

    mmap_gate = bool(
        MEMORY_SAFE_HASH_METRICS.get("canonical_full_heap_read_avoided")
        and MEMORY_SAFE_HASH_METRICS.get("mmap_sha256_used")
        and not MEMORY_SAFE_HASH_METRICS.get("error")
    )

    runtime_pass = False
    for path in (output_path, website_path):
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        previous_runtime_pass = bool(payload.get("runtime_acceptance_passed"))
        runtime_pass = bool(previous_runtime_pass and mmap_gate and original_return_code == 0)
        payload["task_version"] = TASK_VERSION
        payload["attempt_id"] = ATTEMPT_ID
        payload["memory_safe_sha256"] = dict(MEMORY_SAFE_HASH_METRICS)
        payload["canonical_full_heap_read_avoided"] = mmap_gate
        payload["runtime_acceptance_passed"] = runtime_pass
        payload["runtime_execution_success"] = runtime_pass
        payload["strict_gate_version"] = (
            "exact-blob-low-memory-stream-mmap-sha256-point-numeric-force-lookup-"
            "territorial-coverage-list-payload-sha256-iod25-fields-v4"
        )
        payload["success_rule"] = (
            "exit zero only when the exact blob is streamed without full JSON loading, its full-file SHA256 "
            "is computed through read-only mmap without a Python heap copy, ordered identity, valid latest-month "
            "metadata, accepted force lookup and territorial coverage, strict API lists, strict IoD fields, "
            "core success, null suppression and at least one strict 4/4 row are all present"
        )
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if reconciliation_path.is_file():
        payload = json.loads(reconciliation_path.read_text(encoding="utf-8"))
        previous_runtime_pass = bool(payload.get("runtime_acceptance_passed"))
        runtime_pass = bool(previous_runtime_pass and mmap_gate and original_return_code == 0)
        payload["task_version"] = TASK_VERSION
        payload["attempt_id"] = ATTEMPT_ID
        payload["memory_safe_sha256"] = dict(MEMORY_SAFE_HASH_METRICS)
        payload["requires_mmap_sha256_without_heap_copy"] = True
        payload["canonical_full_heap_read_avoided"] = mmap_gate
        payload["runtime_acceptance_passed"] = runtime_pass
        payload["fake_data"] = False
        payload["final_ready"] = False
        reconciliation_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return 0 if runtime_pass else 2


def main() -> int:
    base = load_base()
    base.TASK_VERSION = TASK_VERSION
    base.ATTEMPT_ID = ATTEMPT_ID

    original_read_bytes = Path.read_bytes
    mapped_resources: list[tuple[object, mmap.mmap]] = []

    def memory_safe_read_bytes(path: Path):
        try:
            size = path.stat().st_size
        except Exception:
            MEMORY_SAFE_HASH_METRICS["fallback_read_bytes_count"] = (
                int(MEMORY_SAFE_HASH_METRICS["fallback_read_bytes_count"]) + 1
            )
            return original_read_bytes(path)

        if path.name == CANONICAL_FILENAME and size >= LARGE_FILE_THRESHOLD_BYTES:
            try:
                handle = path.open("rb")
                mapped = mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ)
                mapped_resources.append((handle, mapped))
                MEMORY_SAFE_HASH_METRICS.update(
                    {
                        "canonical_full_heap_read_avoided": True,
                        "mmap_sha256_used": True,
                        "intercepted_path": str(path),
                        "intercepted_size_bytes": size,
                        "error": None,
                    }
                )
                return mapped
            except Exception as exc:
                MEMORY_SAFE_HASH_METRICS["error"] = str(exc)
                raise

        MEMORY_SAFE_HASH_METRICS["fallback_read_bytes_count"] = (
            int(MEMORY_SAFE_HASH_METRICS["fallback_read_bytes_count"]) + 1
        )
        return original_read_bytes(path)

    Path.read_bytes = memory_safe_read_bytes
    original_return_code = 2
    try:
        original_return_code = int(base.main())
    finally:
        Path.read_bytes = original_read_bytes
        for handle, mapped in reversed(mapped_resources):
            try:
                mapped.close()
            except Exception:
                pass
            try:
                handle.close()
            except Exception:
                pass

    repo_root = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
    final_return_code = post_enrich(repo_root, original_return_code)

    print("MEMORY_SAFE_SHA256_ENABLED=true")
    print(
        "CANONICAL_FULL_HEAP_READ_AVOIDED="
        f"{bool(MEMORY_SAFE_HASH_METRICS.get('canonical_full_heap_read_avoided'))}"
    )
    print(f"MMAP_SHA256_USED={bool(MEMORY_SAFE_HASH_METRICS.get('mmap_sha256_used'))}")
    print(f"ATTEMPT_ID={ATTEMPT_ID}")
    print("FINAL_READY=false")
    return final_return_code


if __name__ == "__main__":
    raise SystemExit(main())

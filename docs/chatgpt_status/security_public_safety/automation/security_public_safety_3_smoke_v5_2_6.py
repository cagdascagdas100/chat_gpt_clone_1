from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

BASE_PATH = Path(__file__).with_name("security_public_safety_3_smoke_v5_2_5.py")
TASK_VERSION = "5.2.6-row-bound-memory-evidence"
ATTEMPT_ID = "security-public-safety-3-20260721-015"
EXPECTED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]


def load_base():
    spec = importlib.util.spec_from_file_location(
        "security_public_safety_3_smoke_v5_2_5_base", BASE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load V5.2.5 verifier: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalized_path(value: object) -> str | None:
    if not value:
        return None
    try:
        return os.path.normcase(os.path.abspath(os.fspath(value)))
    except (TypeError, ValueError, OSError):
        return None


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def row_memory_gates(payload: dict) -> tuple[dict[str, bool], dict]:
    stream = payload.get("low_memory_streaming_extractor")
    memory = payload.get("memory_safe_sha256")
    stream = stream if isinstance(stream, dict) else {}
    memory = memory if isinstance(memory, dict) else {}

    source_file = normalized_path(payload.get("source_file"))
    intercepted_path = normalized_path(memory.get("intercepted_path"))
    exact_blob = payload.get("source_file_git_blob_sha") == EXPECTED_BLOB_SHA
    source_binding = bool(source_file and intercepted_path and source_file == intercepted_path)
    stream_targets = {str(value) for value in (stream.get("targets_found") or [])}

    common = {
        "stream_extraction_gate": bool(
            stream.get("enabled")
            and stream.get("features_array_found")
            and stream.get("stopped_after_all_targets")
            and set(TARGET_IDS).issubset(stream_targets)
        ),
        "full_json_load_avoided_gate": bool(
            stream.get("canonical_full_json_load_avoided")
        ),
        "mmap_sha256_gate": bool(
            exact_blob
            and source_binding
            and memory.get("mmap_sha256_used")
            and not memory.get("error")
        ),
        "full_heap_copy_avoided_gate": bool(
            exact_blob
            and source_binding
            and memory.get("canonical_full_heap_read_avoided")
            and not memory.get("error")
        ),
    }
    evidence = {
        "expected_blob_sha": EXPECTED_BLOB_SHA,
        "source_file": payload.get("source_file"),
        "intercepted_path": memory.get("intercepted_path"),
        "source_path_binding_passed": source_binding,
        "exact_blob_passed": exact_blob,
        "stream_targets_found": sorted(stream_targets),
        "all_target_ids_in_stream_metrics": set(TARGET_IDS).issubset(stream_targets),
        "memory_metrics_error": memory.get("error"),
    }
    return common, evidence


def enrich(repo_root: Path, prior_return_code: int) -> int:
    output_path = repo_root / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_candidates_v5_2_latest.json"
    reconciliation_path = repo_root / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_reconciliation_v5_2_latest.json"
    website_path = repo_root / "england_map_web/data/security_public_safety/security_public_safety_3_smoke_rows_latest.json"

    final_pass = False
    reference_gates: dict[str, bool] = {}
    reference_evidence: dict = {}
    row_gate_pass_count = 0

    for path in (output_path, website_path):
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        gates, binding_evidence = row_memory_gates(payload)
        rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
        row_ids = [row.get("parcel_id") for row in rows if isinstance(row, dict)]
        identity_ok = row_ids == TARGET_IDS and len(set(row_ids)) == len(TARGET_IDS)
        for row in rows:
            if not isinstance(row, dict):
                continue
            row.update(gates)
            row["memory_evidence_bound_to_source"] = bool(
                gates["mmap_sha256_gate"] and gates["full_heap_copy_avoided_gate"]
            )
            row["memory_gate_version"] = "row-bound-stream-mmap-v1"
            row["task_version"] = TASK_VERSION
            row["attempt_id"] = ATTEMPT_ID
        all_row_memory_gates = bool(
            len(rows) == len(TARGET_IDS)
            and identity_ok
            and all(
                all(bool(row.get(name)) for name in gates)
                for row in rows
                if isinstance(row, dict)
            )
        )
        row_gate_pass_count = sum(
            1
            for row in rows
            if isinstance(row, dict)
            and all(bool(row.get(name)) for name in gates)
        )
        prior_pass = bool(payload.get("runtime_acceptance_passed"))
        final_pass = bool(prior_return_code == 0 and prior_pass and all_row_memory_gates)
        payload.update(
            {
                "task_version": TASK_VERSION,
                "attempt_id": ATTEMPT_ID,
                "memory_row_gate_version": "row-bound-stream-mmap-v1",
                "memory_source_binding": binding_evidence,
                "memory_row_gate_names": list(gates),
                "memory_row_gate_pass_count": row_gate_pass_count,
                "memory_row_gate_expected_count": len(TARGET_IDS),
                "all_row_memory_gates_passed": all_row_memory_gates,
                "runtime_acceptance_passed": final_pass,
                "runtime_execution_success": final_pass,
                "strict_gate_version": (
                    "exact-blob-low-memory-stream-mmap-source-binding-row-evidence-point-numeric-"
                    "force-lookup-territorial-coverage-list-payload-sha256-iod25-fields-v5"
                ),
                "success_rule": (
                    "exit zero only when exact blob streaming and read-only mmap SHA256 evidence are bound "
                    "to the reported canonical source and written to all three ordered parcel rows, together "
                    "with valid latest-month, force coverage, strict API and IoD evidence and at least one 4/4 row"
                ),
                "fake_data": False,
                "final_ready": False,
            }
        )
        write_json(path, payload)
        reference_gates = gates
        reference_evidence = binding_evidence

    if reconciliation_path.is_file():
        payload = json.loads(reconciliation_path.read_text(encoding="utf-8"))
        payload.update(
            {
                "task_version": TASK_VERSION,
                "attempt_id": ATTEMPT_ID,
                "memory_row_gate_version": "row-bound-stream-mmap-v1",
                "memory_source_binding": reference_evidence,
                "memory_row_gate_names": list(reference_gates),
                "memory_row_gate_pass_count": row_gate_pass_count,
                "memory_row_gate_expected_count": len(TARGET_IDS),
                "requires_row_bound_stream_and_mmap_evidence": True,
                "all_row_memory_gates_passed": row_gate_pass_count == len(TARGET_IDS),
                "runtime_acceptance_passed": final_pass,
                "fake_data": False,
                "final_ready": False,
            }
        )
        write_json(reconciliation_path, payload)

    return 0 if final_pass else 2


def main() -> int:
    base = load_base()
    base.TASK_VERSION = TASK_VERSION
    base.ATTEMPT_ID = ATTEMPT_ID
    prior_return_code = int(base.main())
    repo_root = Path(os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main"))
    final_return_code = enrich(repo_root, prior_return_code)
    print("ROW_BOUND_MEMORY_EVIDENCE_REQUIRED=true")
    print(f"ATTEMPT_ID={ATTEMPT_ID}")
    print("FINAL_READY=false")
    return final_return_code


if __name__ == "__main__":
    raise SystemExit(main())

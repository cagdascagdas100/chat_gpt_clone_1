from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("security_public_safety_3_smoke_v5_2_6.py")
TASK_VERSION = "5.2.7-artifact-quorum-fingerprint"
ATTEMPT_ID = "security-public-safety-3-20260721-016"
BASE_ATTEMPT_ID = "security-public-safety-3-20260721-015"
EXPECTED_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
MEMORY_GATES = [
    "stream_extraction_gate",
    "full_json_load_avoided_gate",
    "mmap_sha256_gate",
    "full_heap_copy_avoided_gate",
    "memory_evidence_bound_to_source",
]
FOUR_GATES = ["canonical_gate", "crime_api_gate", "outcomes_api_gate", "iod25_gate"]


def load_base():
    spec = importlib.util.spec_from_file_location(
        "security_public_safety_3_smoke_v5_2_6_base", BASE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load V5.2.6 verifier: {BASE_PATH}")
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def row_signature(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "parcel_id": row.get("parcel_id"),
        "accuracy_score_4": row.get("accuracy_score_4"),
        "security_score_percent": row.get("security_score_percent"),
        **{name: bool(row.get(name)) for name in MEMORY_GATES + FOUR_GATES},
        "force_lookup_gate": bool(row.get("force_lookup_gate")),
        "territorial_crime_coverage_gate": bool(row.get("territorial_crime_coverage_gate")),
        "territorial_outcomes_coverage_gate": bool(row.get("territorial_outcomes_coverage_gate")),
    }


def artifact_signature(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    dict_rows = [row for row in rows if isinstance(row, dict)]
    row_ids = [row.get("parcel_id") for row in dict_rows]
    if len(rows) != len(TARGET_IDS) or len(dict_rows) != len(TARGET_IDS):
        errors.append("ROW_COUNT_OR_TYPE_MISMATCH")
    if row_ids != TARGET_IDS or len(set(row_ids)) != len(TARGET_IDS):
        errors.append("ORDERED_IDENTITY_MISMATCH")
    if payload.get("attempt_id") != BASE_ATTEMPT_ID:
        errors.append("BASE_ATTEMPT_MISMATCH")
    if not payload.get("runtime_acceptance_passed"):
        errors.append("BASE_RUNTIME_ACCEPTANCE_FALSE")
    if payload.get("source_file_git_blob_sha") != EXPECTED_BLOB_SHA:
        errors.append("EXACT_BLOB_MISMATCH")

    source_file = normalized_path(payload.get("source_file"))
    binding = payload.get("memory_source_binding")
    binding = binding if isinstance(binding, dict) else {}
    bound_source = normalized_path(binding.get("source_file"))
    intercepted = normalized_path(binding.get("intercepted_path"))
    if not source_file or source_file != bound_source or source_file != intercepted:
        errors.append("SOURCE_BINDING_MISMATCH")
    if not binding.get("source_path_binding_passed") or not binding.get("exact_blob_passed"):
        errors.append("SOURCE_BINDING_FLAGS_FALSE")

    accuracy_4_count = 0
    for row in dict_rows:
        if not all(bool(row.get(name)) for name in MEMORY_GATES):
            errors.append(f"ROW_MEMORY_GATE_FALSE:{row.get('parcel_id')}")
        accuracy = row.get("accuracy_score_4")
        score = row.get("security_score_percent")
        if accuracy == 4:
            accuracy_4_count += 1
            if score is None:
                errors.append(f"FOUR_OF_FOUR_SCORE_NULL:{row.get('parcel_id')}")
        elif score is not None:
            errors.append(f"UNVERIFIED_SCORE_NOT_NULL:{row.get('parcel_id')}")
    if accuracy_4_count < 1:
        errors.append("ZERO_STRICT_FOUR_OF_FOUR_ROWS")

    signature = {
        "canonical_blob_sha": payload.get("source_file_git_blob_sha"),
        "source_file": source_file,
        "ordered_rows": [row_signature(row) for row in dict_rows],
        "accuracy_score_4_count": accuracy_4_count,
    }
    return signature, sorted(set(errors))


def fingerprint(signature: dict[str, Any]) -> str:
    encoded = json.dumps(
        signature, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def reconciliation_errors(payload: dict[str, Any], expected_fingerprint: str) -> list[str]:
    errors: list[str] = []
    if payload.get("attempt_id") != BASE_ATTEMPT_ID:
        errors.append("RECONCILIATION_ATTEMPT_MISMATCH")
    if not payload.get("runtime_acceptance_passed"):
        errors.append("RECONCILIATION_RUNTIME_FALSE")
    if not payload.get("all_row_memory_gates_passed"):
        errors.append("RECONCILIATION_MEMORY_GATES_FALSE")
    if payload.get("memory_row_gate_pass_count") != len(TARGET_IDS):
        errors.append("RECONCILIATION_MEMORY_COUNT_MISMATCH")
    existing = payload.get("run_evidence_fingerprint")
    if existing and existing != expected_fingerprint:
        errors.append("RECONCILIATION_PREEXISTING_FINGERPRINT_MISMATCH")
    return errors


def enrich(repo_root: Path, prior_return_code: int) -> int:
    output_path = repo_root / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_candidates_v5_2_latest.json"
    reconciliation_path = repo_root / "docs/chatgpt_status/security_public_safety/runner_outputs/security_public_safety_3_smoke_reconciliation_v5_2_latest.json"
    website_path = repo_root / "england_map_web/data/security_public_safety/security_public_safety_3_smoke_rows_latest.json"
    paths = {
        "output": output_path,
        "website": website_path,
        "reconciliation": reconciliation_path,
    }
    exists = {name: path.is_file() for name, path in paths.items()}
    errors: list[str] = []
    if prior_return_code != 0:
        errors.append(f"BASE_EXIT_NONZERO:{prior_return_code}")
    for name, present in exists.items():
        if not present:
            errors.append(f"MISSING_ARTIFACT:{name}")

    payloads: dict[str, dict[str, Any]] = {}
    if all(exists.values()):
        for name, path in paths.items():
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(value, dict):
                    raise ValueError("top-level JSON is not an object")
                payloads[name] = value
            except Exception as exc:
                errors.append(f"ARTIFACT_PARSE_FAILED:{name}:{type(exc).__name__}")

    run_fingerprint: str | None = None
    if "output" in payloads and "website" in payloads:
        output_signature, output_errors = artifact_signature(payloads["output"])
        website_signature, website_errors = artifact_signature(payloads["website"])
        errors.extend(f"OUTPUT:{value}" for value in output_errors)
        errors.extend(f"WEBSITE:{value}" for value in website_errors)
        output_fp = fingerprint(output_signature)
        website_fp = fingerprint(website_signature)
        if output_fp != website_fp:
            errors.append("OUTPUT_WEBSITE_FINGERPRINT_MISMATCH")
        else:
            run_fingerprint = output_fp

    if run_fingerprint and "reconciliation" in payloads:
        errors.extend(reconciliation_errors(payloads["reconciliation"], run_fingerprint))

    quorum_passed = bool(not errors and run_fingerprint and all(exists.values()))
    common = {
        "task_version": TASK_VERSION,
        "attempt_id": ATTEMPT_ID,
        "supersedes_attempt_id": BASE_ATTEMPT_ID,
        "artifact_quorum_required": True,
        "artifact_quorum_members": list(paths),
        "artifact_presence": exists,
        "artifact_quorum_passed": quorum_passed,
        "run_evidence_fingerprint": run_fingerprint,
        "artifact_quorum_errors": sorted(set(errors)),
        "runtime_acceptance_passed": quorum_passed,
        "runtime_execution_success": quorum_passed,
        "strict_gate_version": "exact-blob-stream-mmap-row-bound-artifact-quorum-fingerprint-official-four-gate-v6",
        "fake_data": False,
        "final_ready": False,
    }
    for name, payload in payloads.items():
        payload.update(common)
        if name in ("output", "website"):
            for row in payload.get("rows", []):
                if isinstance(row, dict):
                    row["artifact_quorum_gate"] = quorum_passed
                    row["run_evidence_fingerprint"] = run_fingerprint
                    row["task_version"] = TASK_VERSION
                    row["attempt_id"] = ATTEMPT_ID
        write_json(paths[name], payload)

    print(f"ARTIFACT_QUORUM_PRESENT={sum(exists.values())}/3")
    print(f"ARTIFACT_QUORUM_PASSED={str(quorum_passed).lower()}")
    print(f"RUN_EVIDENCE_FINGERPRINT={run_fingerprint or ''}")
    return 0 if quorum_passed else 2


def main() -> int:
    base = load_base()
    base.TASK_VERSION = TASK_VERSION
    base.ATTEMPT_ID = ATTEMPT_ID
    prior_return_code = int(base.main())
    repo_root = Path(
        os.environ.get("AAYS_REPO_ROOT", r"F:\chatgpt\chat_gpt_clone_1_main")
    )
    result = enrich(repo_root, prior_return_code)
    print(f"ATTEMPT_ID={ATTEMPT_ID}")
    print("FINAL_READY=false")
    return result


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

BASE_PATH = Path(__file__).with_name("security_public_safety_3_smoke_v5_2_6.py")
TASK_VERSION = "5.2.9-immutable-evidence-fingerprint"
ATTEMPT_ID = "security-public-safety-3-20260721-018"
SUPERSEDES_ATTEMPT_ID = "security-public-safety-3-20260721-017"
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


def finite_number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def non_negative_int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def sha256_hex(value: object) -> str | None:
    text = str(value or "").lower()
    return text if len(text) == 64 and all(c in "0123456789abcdef" for c in text) else None


def derived_force_fields(row: dict[str, Any]) -> dict[str, bool]:
    force = row.get("force_lookup_evidence")
    force = force if isinstance(force, dict) else {}
    coverage = row.get("territorial_coverage")
    coverage = coverage if isinstance(coverage, dict) else {}
    return {
        "force_lookup_gate": bool(force.get("acceptance_passed")),
        "territorial_crime_coverage_gate": bool(
            coverage.get("territorial_crime_coverage_available")
        ),
        "territorial_outcomes_coverage_gate": bool(
            coverage.get("territorial_outcomes_coverage_available")
        ),
    }


def official_row_evidence_signature(row: dict[str, Any]) -> dict[str, Any]:
    area = row.get("area_evidence")
    area = area if isinstance(area, dict) else {}
    force = row.get("force_lookup_evidence")
    force = force if isinstance(force, dict) else {}
    coverage = row.get("territorial_coverage")
    coverage = coverage if isinstance(coverage, dict) else {}
    iod = row.get("iod25_v2")
    iod = iod if isinstance(iod, dict) else {}
    geometry = row.get("geometry")
    geometry = geometry if isinstance(geometry, dict) else {}
    return {
        "geometry_type": geometry.get("type"),
        "coordinates": geometry.get("coordinates"),
        "lsoa_code": row.get("lsoa_code"),
        "official_api_month": row.get("official_api_month"),
        "crime_url": area.get("crime_url"),
        "crime_http_status": area.get("crime_http_status"),
        "crime_response_sha256": sha256_hex(area.get("crime_response_sha256")),
        "crime_count": non_negative_int(area.get("crime_one_mile_supporting_count")),
        "outcomes_url": area.get("outcomes_url"),
        "outcomes_http_status": area.get("outcomes_http_status"),
        "outcomes_response_sha256": sha256_hex(area.get("outcomes_response_sha256")),
        "outcomes_count": non_negative_int(
            area.get("outcomes_one_mile_supporting_count")
        ),
        "force_lookup_url": force.get("url"),
        "force_lookup_http_status": force.get("http_status"),
        "force_lookup_response_sha256": sha256_hex(force.get("response_sha256")),
        "force_id": force.get("force_id"),
        "neighbourhood_id": force.get("neighbourhood_id"),
        "force_lookup_acceptance_passed": bool(force.get("acceptance_passed")),
        "coverage_force_id": coverage.get("force_id"),
        "coverage_latest_month": coverage.get("latest_month"),
        "territorial_crime_coverage_available": bool(
            coverage.get("territorial_crime_coverage_available")
        ),
        "territorial_outcomes_coverage_available": bool(
            coverage.get("territorial_outcomes_coverage_available")
        ),
        "iod_lsoa_code": iod.get("lsoa_code_2021"),
        "iod_crime_score": finite_number(iod.get("iod25_crime_score")),
        "iod_crime_rank": non_negative_int(iod.get("iod25_crime_rank")),
        "iod_crime_decile": non_negative_int(iod.get("iod25_crime_decile")),
    }


def row_signature(row: dict[str, Any]) -> dict[str, Any]:
    force_fields = derived_force_fields(row)
    return {
        "parcel_id": row.get("parcel_id"),
        "task_version": row.get("task_version"),
        "attempt_id": row.get("attempt_id"),
        "accuracy_score_4": row.get("accuracy_score_4"),
        "candidate_security_score_percent": row.get(
            "candidate_security_score_percent"
        ),
        "security_score_percent": row.get("security_score_percent"),
        **{name: bool(row.get(name)) for name in MEMORY_GATES + FOUR_GATES},
        **force_fields,
        "official_evidence": official_row_evidence_signature(row),
    }


def artifact_signature(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[str], dict[str, int]]:
    errors: list[str] = []
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    dict_rows = [row for row in rows if isinstance(row, dict)]
    row_ids = [row.get("parcel_id") for row in dict_rows]

    if len(rows) != len(TARGET_IDS) or len(dict_rows) != len(TARGET_IDS):
        errors.append("ROW_COUNT_OR_TYPE_MISMATCH")
    if row_ids != TARGET_IDS or len(set(row_ids)) != len(TARGET_IDS):
        errors.append("ORDERED_IDENTITY_MISMATCH")
    if payload.get("target_parcels") != TARGET_IDS:
        errors.append("TARGET_PARCELS_MISMATCH")
    if payload.get("attempt_id") != ATTEMPT_ID:
        errors.append("CURRENT_ATTEMPT_MISMATCH")
    if payload.get("task_version") != TASK_VERSION:
        errors.append("CURRENT_TASK_VERSION_MISMATCH")
    if not payload.get("runtime_execution_complete"):
        errors.append("RUNTIME_EXECUTION_INCOMPLETE")
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
    if not binding.get("source_path_binding_passed") or not binding.get(
        "exact_blob_passed"
    ):
        errors.append("SOURCE_BINDING_FLAGS_FALSE")

    latest = payload.get("official_api_latest")
    latest = latest if isinstance(latest, dict) else {}
    iod_evidence = payload.get("iod25_v2_evidence")
    iod_evidence = iod_evidence if isinstance(iod_evidence, dict) else {}
    top_official_signature = {
        "latest_month": latest.get("month"),
        "latest_http_status": latest.get("http_status"),
        "latest_response_sha256": sha256_hex(latest.get("response_sha256")),
        "iod_url": iod_evidence.get("url"),
        "iod_http_status": iod_evidence.get("http_status"),
        "iod_response_sha256": sha256_hex(iod_evidence.get("response_sha256")),
        "iod_bytes": non_negative_int(iod_evidence.get("bytes")),
        "iod_matched_lsoa_count": non_negative_int(
            iod_evidence.get("matched_lsoa_count")
        ),
    }

    accuracy_4_count = 0
    passed_gate_cells = 0
    force_lookup_pass_count = 0
    for row in dict_rows:
        parcel_id = row.get("parcel_id")
        raw_task_version = row.get("task_version")
        raw_attempt_id = row.get("attempt_id")
        if raw_attempt_id != ATTEMPT_ID:
            errors.append(f"ROW_ATTEMPT_MISMATCH:{parcel_id}")
        if raw_task_version != TASK_VERSION:
            errors.append(f"ROW_TASK_VERSION_MISMATCH:{parcel_id}")
        if not all(bool(row.get(name)) for name in MEMORY_GATES):
            errors.append(f"ROW_MEMORY_GATE_FALSE:{parcel_id}")

        force_fields = derived_force_fields(row)
        for name, derived_value in force_fields.items():
            if row.get(name) is not None and bool(row.get(name)) != derived_value:
                errors.append(f"ROW_DERIVED_FORCE_FIELD_MISMATCH:{name}:{parcel_id}")

        four_gate_count = sum(bool(row.get(name)) for name in FOUR_GATES)
        passed_gate_cells += four_gate_count
        if row.get("accuracy_score_4") != four_gate_count:
            errors.append(f"ROW_ACCURACY_GATE_COUNT_MISMATCH:{parcel_id}")

        accuracy = row.get("accuracy_score_4")
        score = finite_number(row.get("security_score_percent"))
        candidate = finite_number(row.get("candidate_security_score_percent"))
        if accuracy == 4:
            accuracy_4_count += 1
            if score is None:
                errors.append(f"FOUR_OF_FOUR_SCORE_NULL_OR_NONFINITE:{parcel_id}")
            elif not 0.0 <= score <= 100.0:
                errors.append(f"FOUR_OF_FOUR_SCORE_OUT_OF_RANGE:{parcel_id}")
            if candidate is None or score is None or abs(candidate - score) > 1e-9:
                errors.append(f"PUBLISHED_SCORE_NOT_CANONICAL_CANDIDATE:{parcel_id}")
        elif row.get("security_score_percent") is not None:
            errors.append(f"UNVERIFIED_SCORE_NOT_NULL:{parcel_id}")

        if force_fields["force_lookup_gate"]:
            force_lookup_pass_count += 1

    if accuracy_4_count < 1:
        errors.append("ZERO_STRICT_FOUR_OF_FOUR_ROWS")

    counts = {
        "actual_rows": len(dict_rows),
        "unique_rows": len(set(row_ids)),
        "passed_gate_cells": passed_gate_cells,
        "accuracy_score_4_count": accuracy_4_count,
        "force_lookup_acceptance_pass_count": force_lookup_pass_count,
    }
    top_expected = {
        "sample_count": len(dict_rows),
        "prepared_acceptance_gate_cells": len(TARGET_IDS) * len(FOUR_GATES),
        "passed_acceptance_gate_cells": passed_gate_cells,
        "accuracy_score_4_count": accuracy_4_count,
        "verified_slot_rows": accuracy_4_count,
        "actual_slot_rows_written": accuracy_4_count,
        "memory_row_gate_pass_count": len(TARGET_IDS),
        "memory_row_gate_expected_count": len(TARGET_IDS),
    }
    for name, expected in top_expected.items():
        if payload.get(name) != expected:
            errors.append(f"TOP_LEVEL_COUNT_MISMATCH:{name}")
    if not payload.get("all_row_memory_gates_passed"):
        errors.append("TOP_LEVEL_MEMORY_GATES_FALSE")

    signature = {
        "canonical_blob_sha": payload.get("source_file_git_blob_sha"),
        "canonical_file_sha256": sha256_hex(payload.get("source_file_sha256")),
        "source_file": source_file,
        "top_official_evidence": top_official_signature,
        "ordered_rows": [row_signature(row) for row in dict_rows],
        **counts,
    }
    return signature, sorted(set(errors)), counts


def fingerprint(signature: dict[str, Any]) -> str:
    encoded = json.dumps(
        signature, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def reconciliation_errors(
    payload: dict[str, Any],
    expected_counts: dict[str, int],
    expected_fingerprint: str,
) -> list[str]:
    errors: list[str] = []
    required_true = [
        "runtime_execution_complete",
        "runtime_acceptance_passed",
        "canonical_source_acceptance_passed",
        "target_identity_acceptance_passed",
        "official_latest_month_acceptance_passed",
        "ordered_identity_match",
        "requires_at_least_one_accuracy_4_for_success",
        "requires_list_payload_for_api_gates",
        "requires_force_lookup_for_api_gates",
        "requires_territorial_coverage_for_api_gates",
        "requires_nonempty_iod25_crime_fields",
        "all_unverified_published_scores_null",
        "all_row_memory_gates_passed",
    ]
    if payload.get("attempt_id") != ATTEMPT_ID:
        errors.append("RECONCILIATION_ATTEMPT_MISMATCH")
    if payload.get("task_version") != TASK_VERSION:
        errors.append("RECONCILIATION_TASK_VERSION_MISMATCH")
    for name in required_true:
        if not payload.get(name):
            errors.append(f"RECONCILIATION_FLAG_FALSE:{name}")
    expected_values = {
        "expected_rows": len(TARGET_IDS),
        "actual_rows": expected_counts["actual_rows"],
        "unique_rows": expected_counts["unique_rows"],
        "expected_gate_cells": len(TARGET_IDS) * len(FOUR_GATES),
        "passed_gate_cells": expected_counts["passed_gate_cells"],
        "accuracy_score_4_count": expected_counts["accuracy_score_4_count"],
        "force_lookup_acceptance_pass_count": expected_counts[
            "force_lookup_acceptance_pass_count"
        ],
        "memory_row_gate_pass_count": len(TARGET_IDS),
        "memory_row_gate_expected_count": len(TARGET_IDS),
    }
    for name, expected in expected_values.items():
        if payload.get(name) != expected:
            errors.append(f"RECONCILIATION_COUNT_MISMATCH:{name}")
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
    expected_counts: dict[str, int] | None = None
    if "output" in payloads and "website" in payloads:
        output_signature, output_errors, output_counts = artifact_signature(
            payloads["output"]
        )
        website_signature, website_errors, website_counts = artifact_signature(
            payloads["website"]
        )
        errors.extend(f"OUTPUT:{value}" for value in output_errors)
        errors.extend(f"WEBSITE:{value}" for value in website_errors)
        output_fp = fingerprint(output_signature)
        website_fp = fingerprint(website_signature)
        if output_fp != website_fp or output_counts != website_counts:
            errors.append("OUTPUT_WEBSITE_EVIDENCE_FINGERPRINT_OR_COUNT_MISMATCH")
        else:
            run_fingerprint = output_fp
            expected_counts = output_counts

    if run_fingerprint and expected_counts and "reconciliation" in payloads:
        errors.extend(
            reconciliation_errors(
                payloads["reconciliation"], expected_counts, run_fingerprint
            )
        )

    quorum_passed = bool(not errors and run_fingerprint and all(exists.values()))
    common = {
        "task_version": TASK_VERSION,
        "attempt_id": ATTEMPT_ID,
        "supersedes_attempt_id": SUPERSEDES_ATTEMPT_ID,
        "artifact_quorum_required": True,
        "artifact_quorum_members": list(paths),
        "artifact_presence": exists,
        "artifact_quorum_passed": quorum_passed,
        "attempt_lineage_gate": quorum_passed,
        "row_lineage_immutable_gate": quorum_passed,
        "reconciliation_consistency_gate": quorum_passed,
        "gate_count_consistency_gate": quorum_passed,
        "top_level_counter_consistency_gate": quorum_passed,
        "official_evidence_fingerprint_gate": quorum_passed,
        "run_evidence_fingerprint": run_fingerprint,
        "artifact_quorum_errors": sorted(set(errors)),
        "runtime_acceptance_passed": quorum_passed,
        "runtime_execution_success": quorum_passed,
        "strict_gate_version": "exact-blob-stream-mmap-row-bound-immutable-lineage-official-evidence-fingerprint-reconciliation-quorum-v8",
        "fake_data": False,
        "final_ready": False,
    }
    for name, payload in payloads.items():
        payload.update(common)
        if name in ("output", "website"):
            for row in payload.get("rows", []):
                if isinstance(row, dict):
                    force_fields = derived_force_fields(row)
                    row.update(force_fields)
                    row["artifact_quorum_gate"] = quorum_passed
                    row["attempt_lineage_gate"] = quorum_passed
                    row["row_lineage_immutable_gate"] = quorum_passed
                    row["reconciliation_consistency_gate"] = quorum_passed
                    row["gate_count_consistency_gate"] = quorum_passed
                    row["top_level_counter_consistency_gate"] = quorum_passed
                    row["official_evidence_fingerprint_gate"] = quorum_passed
                    row["run_evidence_fingerprint"] = run_fingerprint
        atomic_write_json(paths[name], payload)

    print(f"ARTIFACT_QUORUM_PRESENT={sum(exists.values())}/3")
    print(f"ARTIFACT_QUORUM_PASSED={str(quorum_passed).lower()}")
    print(f"ROW_LINEAGE_IMMUTABLE_PASSED={str(quorum_passed).lower()}")
    print(f"OFFICIAL_EVIDENCE_FINGERPRINT_PASSED={str(quorum_passed).lower()}")
    print(f"RECONCILIATION_CONSISTENCY_PASSED={str(quorum_passed).lower()}")
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

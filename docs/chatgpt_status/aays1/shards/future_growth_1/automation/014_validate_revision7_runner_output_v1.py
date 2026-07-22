#!/usr/bin/env python3
"""Fail-closed validator for the future_growth_1 revision-7 shared-runner output.

This validator accepts only the exact no-score completion contract emitted by
future_growth_1_official_geometry_entry_v7.py. It never executes network calls,
never writes business rows, and never treats a blocked/partial runner artifact
as success.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SLOT_ID = "future_growth_1"
WORKSTREAM_ID = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
TASK_ID = "aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID = "future-growth-1-20260722-005"
CONTRACT_REVISION = 7
COMPLETED_STATE = "COMPLETED_SLOT_LOCAL_GEOMETRY_AND_PLANNING_QUERY_SAMPLE"
COMPLETED_STATUS = "COMPLETED_REVISION7_EXACT_ROWS_GEOMETRY_AND_19_QUERIES_NO_SCORE"
EXPECTED_SOURCE_SHA_KEYS = {
    "entry_v7",
    "geometry_entry",
    "extractor",
    "query_executor",
    "query_validator",
    "rows_output",
    "relation_output",
    "query_evidence",
    "query_validation",
}
EXPECTED_ROW_ACCEPTANCE_KEYS = {
    "semantics",
    "canonical_sha",
    "five_rows",
    "row_numbers",
    "parcel_ids",
    "unique_hmlr_ids",
    "no_nearest",
}
EXPECTED_QUERY_ACCEPTANCE_KEYS = {
    "requests",
    "rows",
    "evidence_rows",
    "promotion_zero",
    "scores_zero",
    "validation_pass",
    "validated_rows",
    "polygon_claim_false",
}
REQUIRED_SOURCE_STEPS = {
    "rows_20_24_extraction",
    "slot_local_geometry",
    "planning_query_execution",
    "planning_query_validation",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_CROSS_SLOT_TOKENS = (
    "height_difference_2",
    "future_growth_2",
    "future_growth_3",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("runner output must be a JSON object")
    return value


def all_true_exact(value: Any, expected_keys: set[str]) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == expected_keys
        and all(item is True for item in value.values())
    )


def validate(payload: dict[str, Any]) -> dict[str, Any]:
    source_steps = payload.get("source_steps")
    geometry = payload.get("geometry_status")
    query_evidence = payload.get("planning_query_evidence")
    query_validation = payload.get("planning_query_validation")
    source_sha = payload.get("source_sha256")
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)

    checks: dict[str, bool] = {
        "slot_id_exact": payload.get("slot_id") == SLOT_ID,
        "workstream_exact": payload.get("workstream_id") == WORKSTREAM_ID,
        "task_id_exact": payload.get("task_id") == TASK_ID,
        "attempt_id_exact": payload.get("attempt_id") == ATTEMPT_ID,
        "contract_revision_exact": payload.get("contract_revision") == CONTRACT_REVISION,
        "completed_state_exact": payload.get("state") == COMPLETED_STATE,
        "completed_status_exact": payload.get("status") == COMPLETED_STATUS,
        "no_blocker_on_completed_output": not payload.get("blocker"),
        "row_acceptance_exact_all_true": all_true_exact(
            payload.get("rows_20_24_acceptance"), EXPECTED_ROW_ACCEPTANCE_KEYS
        ),
        "source_steps_exact": isinstance(source_steps, dict)
        and set(source_steps) == REQUIRED_SOURCE_STEPS,
        "source_steps_exit_zero": isinstance(source_steps, dict)
        and all(
            isinstance(source_steps.get(key), dict)
            and source_steps[key].get("exit_code") == 0
            for key in REQUIRED_SOURCE_STEPS
        ),
        "geometry_status_object": isinstance(geometry, dict),
        "geometry_slot_exact": isinstance(geometry, dict)
        and geometry.get("slot_id") == SLOT_ID,
        "geometry_completed": isinstance(geometry, dict)
        and geometry.get("state") == "COMPLETED_SOURCE_GEOMETRY_WAVE",
        "geometry_acceptance_present_all_true": isinstance(geometry, dict)
        and isinstance(geometry.get("acceptance"), dict)
        and bool(geometry["acceptance"])
        and all(value is True for value in geometry["acceptance"].values()),
        "geometry_truth_flags_false": isinstance(geometry, dict)
        and geometry.get("fake_data") is False
        and geometry.get("db_write") is False
        and geometry.get("migration") is False
        and geometry.get("production_deploy") is False,
        "query_evidence_object": isinstance(query_evidence, dict),
        "query_network_requests_19": isinstance(query_evidence, dict)
        and query_evidence.get("network_requests_executed") == 19,
        "query_rows_completed_19": isinstance(query_evidence, dict)
        and query_evidence.get("rows_completed") == 19,
        "query_evidence_rows_19": isinstance(query_evidence, dict)
        and isinstance(query_evidence.get("rows"), list)
        and len(query_evidence["rows"]) == 19,
        "query_evidence_zero_promotion_and_scores": isinstance(query_evidence, dict)
        and query_evidence.get("promotion_eligible_rows") == 0
        and query_evidence.get("scores_emitted") == 0,
        "query_validation_pass": isinstance(query_validation, dict)
        and query_validation.get("result") == "PASS",
        "query_validation_rows_19": isinstance(query_validation, dict)
        and query_validation.get("rows_validated") == 19,
        "query_validation_polygon_claim_false": isinstance(query_validation, dict)
        and query_validation.get("polygon_relation_claimed") is False,
        "query_acceptance_exact_all_true": all_true_exact(
            payload.get("planning_query_acceptance"), EXPECTED_QUERY_ACCEPTANCE_KEYS
        ),
        "canonical_rows_exact_5": payload.get("canonical_rows_20_24_extracted") == 5,
        "official_site_polygons_exact_4": payload.get("official_site_polygons_downloaded") == 4,
        "exact_hmlr_polygons_exact_6": payload.get("exact_hmlr_parcel_polygons") == 6,
        "verified_relations_exact_14": payload.get("verified_polygon_relations") == 14,
        "planning_requests_exact_19": payload.get("planning_query_requests_executed") == 19,
        "planning_rows_validated_exact_19": payload.get("planning_query_rows_validated") == 19,
        "promoted_rows_zero": payload.get("source_wave_parcel_rows_promoted") == 0,
        "scored_rows_zero": payload.get("scored_business_rows") == 0,
        "business_rows_zero": payload.get("actual_business_data_rows_written") == 0,
        "source_sha_keys_exact": isinstance(source_sha, dict)
        and set(source_sha) == EXPECTED_SOURCE_SHA_KEYS,
        "source_sha_values_valid": isinstance(source_sha, dict)
        and all(isinstance(value, str) and SHA256_RE.fullmatch(value) for value in source_sha.values()),
        "final_ready_false": payload.get("final_ready") is False,
        "fake_data_false": payload.get("fake_data") is False,
        "db_write_false": payload.get("db_write") is False,
        "migration_false": payload.get("migration") is False,
        "production_deploy_false": payload.get("production_deploy") is False,
        "no_cross_slot_token": not any(token in serialized for token in FORBIDDEN_CROSS_SLOT_TOKENS),
        "next_step_exact": payload.get("next_unverified_step")
        == "BUILD_ROWS_20_24_CANDIDATES_AND_FULL_30761_FACTOR_MATRIX",
    }
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "validation_kind": "REVISION7_RUNNER_OUTPUT_FAIL_CLOSED_ACCEPTANCE",
        "result": "PASS" if not failed else "FAIL",
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "runner_execution_claimed": False,
        "business_progress_claimed": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runner_output", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = validate(load_json(args.runner_output))
    except Exception as exc:
        result = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "validation_kind": "REVISION7_RUNNER_OUTPUT_FAIL_CLOSED_ACCEPTANCE",
            "result": "FAIL",
            "checks_passed": 0,
            "checks_total": 1,
            "checks": {"json_load": False},
            "failed_checks": [f"json_load:{type(exc).__name__}:{exc}"],
            "runner_execution_claimed": False,
            "business_progress_claimed": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if result["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

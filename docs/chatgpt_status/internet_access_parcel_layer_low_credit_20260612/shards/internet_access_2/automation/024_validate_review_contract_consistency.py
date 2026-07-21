#!/usr/bin/env python3
"""Fail-closed consistency audit for the internet_access_2 frozen review contract."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
EXPECTED_ROWS = 30761
EXPECTED_START = 30762
EXPECTED_END = 61522
EXPECTED_COMPLETED = 134
EXPECTED_TOTAL = 135
EXPECTED_COMBINED = 314
EXPECTED_SCOPE_FILES = 79
EXPECTED_HISTORICAL_OVERRIDE_IDS = {55, 90}

SHARD = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2")
WEB = Path("england_map_web/data/aays_18_slots/internet_access_2")


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def pair(value: Any) -> tuple[int, int]:
    if not isinstance(value, dict):
        raise ValueError(f"Expected pass/total object, got {type(value).__name__}")
    return int(value["passed"]), int(value["total"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--audit-output", type=Path)
    args = parser.parse_args()

    repo = args.repo_root
    progress = load(repo / WEB / "progress_latest.json")
    provenance = load(repo / WEB / "provenance_contract_latest.json")
    readiness = load(repo / WEB / "runner_readiness_latest.json")
    scope = load(repo / WEB / "final_review_scope_latest.json")
    task1 = load(repo / SHARD / "runner_tasks/001_extract_shard2_postcode_candidates.task.json")
    task2 = load(repo / SHARD / "runner_tasks/002_complete_candidate_integrity_extension.task.json")

    operation_rows: list[dict[str, Any]] = []
    for name in ("operations_latest.json", "scope_operations_latest.json", "operations_provenance_latest.json"):
        payload = load(repo / WEB / name)
        operation_rows.extend(payload.get("operations") or [])
    id_counts = Counter(int(row["id"]) for row in operation_rows)
    duplicate_ids = {operation_id for operation_id, count in id_counts.items() if count > 1}
    by_id = {int(row["id"]): row for row in operation_rows}
    done = sum(row.get("status") == "DONE" for row in by_id.values())
    blocked = [row for row in by_id.values() if row.get("status") != "DONE"]

    suites = {
        "extractor": (12, 12),
        "publisher": (10, 10),
        "streaming_slicer": (12, 12),
        "inner_runner_contract": (39, 39),
        "dispatch_readiness": (16, 16),
        "ofcom_v2_validator": (43, 43),
        "zip_container_safety": (18, 18),
        "published_bundle": (23, 23),
        "candidate_jsonl": (25, 25),
        "candidate_postcode_resolution": (18, 18),
        "single_run_provenance": (24, 24),
        "run_and_audit_wrapper": (40, 40),
        "candidate_web_contract": (20, 20),
        "review_contract_consistency": (14, 14),
    }
    suite_total = sum(total for _, total in suites.values())
    suite_passed = sum(passed for passed, _ in suites.values())

    checks = {
        "slot_identity_consistent": all(payload.get("slot_id") == SLOT_ID for payload in (progress, provenance, readiness, scope, task1, task2)),
        "parcel_partition_exact": progress.get("parcel_start") == EXPECTED_START and progress.get("parcel_end") == EXPECTED_END and progress.get("parcel_count") == EXPECTED_ROWS,
        "operation_override_contract": duplicate_ids == EXPECTED_HISTORICAL_OVERRIDE_IDS and sorted(by_id) == list(range(1, EXPECTED_TOTAL + 1)) and all(by_id[operation_id].get("status") == "DONE" for operation_id in EXPECTED_HISTORICAL_OVERRIDE_IDS),
        "single_current_blocker": done == EXPECTED_COMPLETED and len(blocked) == 1 and int(blocked[0]["id"]) == EXPECTED_TOTAL,
        "progress_operation_counts_match": progress.get("completed_operations") == EXPECTED_COMPLETED and progress.get("total_operations") == EXPECTED_TOTAL and progress.get("visible_operation_rows") == EXPECTED_TOTAL,
        "source_decision_totals_match": progress.get("official_source_candidates") == 8 and progress.get("promoted_sources", 0) + progress.get("held_sources", 0) + progress.get("rejected_sources", 0) == 8,
        "suite_definition_total_314": suite_passed == EXPECTED_COMBINED and suite_total == EXPECTED_COMBINED,
        "progress_validation_total_match": progress.get("combined_validation_passed") == EXPECTED_COMBINED and progress.get("combined_validation_total") == EXPECTED_COMBINED,
        "provenance_validation_total_match": pair(provenance.get("combined_validation")) == (EXPECTED_COMBINED, EXPECTED_COMBINED),
        "primary_task_validation_total_match": pair(task1["preflight_validation"]["combined"]) == (EXPECTED_COMBINED, EXPECTED_COMBINED),
        "extension_task_validation_total_match": pair(task2["required_preflight"]["combined_all_suites"]) == (EXPECTED_COMBINED, EXPECTED_COMBINED),
        "readiness_validation_total_match": readiness["official_v2_semantic_preflight"].get("combined_tests_passed") == EXPECTED_COMBINED and readiness["official_v2_semantic_preflight"].get("combined_tests_total") == EXPECTED_COMBINED,
        "scope_is_exact_and_authorized": scope.get("review_scope_file_count") == EXPECTED_SCOPE_FILES and scope.get("other_slot_path_count") == 0 and scope.get("shared_state_path_count") == 0 and scope.get("queue_path_count") == 0 and scope.get("disallowed_path_count") == 0,
        "truth_boundary_preserved": all(payload.get("actual_business_data_rows_written", payload.get("business_rows_written", 0)) == 0 and payload.get("final_ready") is False for payload in (progress, provenance, readiness, scope, task2)) and task1["write_policy"] == {"fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "direct_push": False, "final_ready": False},
    }

    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise ValueError("Review contract consistency failed: " + ", ".join(failed))

    result = {
        "schema_version": 4,
        "slot_id": SLOT_ID,
        "status": "PASS_REVIEW_CONTRACT_CONSISTENCY_AUDITED_REVIEW_ONLY",
        "tests_passed": len(checks),
        "tests_total": len(checks),
        "test_names": list(checks),
        "historical_override_ids": sorted(EXPECTED_HISTORICAL_OVERRIDE_IDS),
        "completed_operations": EXPECTED_COMPLETED,
        "total_operations": EXPECTED_TOTAL,
        "combined_validation_passed": EXPECTED_COMBINED,
        "combined_validation_total": EXPECTED_COMBINED,
        "review_scope_file_count": EXPECTED_SCOPE_FILES,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
    }
    if args.audit_output:
        args.audit_output.parent.mkdir(parents=True, exist_ok=True)
        args.audit_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

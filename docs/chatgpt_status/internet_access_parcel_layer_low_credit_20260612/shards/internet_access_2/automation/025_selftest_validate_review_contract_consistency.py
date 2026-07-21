#!/usr/bin/env python3
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SLOT = "internet_access_2"
SHARD = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2")
WEB = Path("england_map_web/data/aays_18_slots/internet_access_2")
SCRIPT = Path(__file__).with_name("024_validate_review_contract_consistency.py")


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def fixture(root: Path) -> None:
    progress = {"slot_id": SLOT, "parcel_start": 30762, "parcel_end": 61522, "parcel_count": 30761, "completed_operations": 134, "total_operations": 135, "visible_operation_rows": 135, "official_source_candidates": 8, "promoted_sources": 5, "held_sources": 1, "rejected_sources": 2, "combined_validation_passed": 314, "combined_validation_total": 314, "actual_business_data_rows_written": 0, "final_ready": False}
    provenance = {"slot_id": SLOT, "combined_validation": {"passed": 314, "total": 314}, "actual_business_data_rows_written": 0, "final_ready": False}
    readiness = {"slot_id": SLOT, "official_v2_semantic_preflight": {"combined_tests_passed": 314, "combined_tests_total": 314}, "actual_business_data_rows_written": 0, "final_ready": False}
    scope = {"slot_id": SLOT, "review_scope_file_count": 79, "other_slot_path_count": 0, "shared_state_path_count": 0, "queue_path_count": 0, "disallowed_path_count": 0, "business_rows_written": 0, "final_ready": False}
    task1 = {"slot_id": SLOT, "preflight_validation": {"combined": {"passed": 314, "total": 314}}, "write_policy": {"fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "direct_push": False, "final_ready": False}}
    task2 = {"slot_id": SLOT, "required_preflight": {"combined_all_suites": {"passed": 314, "total": 314}}, "actual_business_data_rows_written": 0, "final_ready": False}
    write(root / WEB / "progress_latest.json", progress)
    write(root / WEB / "provenance_contract_latest.json", provenance)
    write(root / WEB / "runner_readiness_latest.json", readiness)
    write(root / WEB / "final_review_scope_latest.json", scope)
    write(root / SHARD / "runner_tasks/001_extract_shard2_postcode_candidates.task.json", task1)
    write(root / SHARD / "runner_tasks/002_complete_candidate_integrity_extension.task.json", task2)
    write(root / WEB / "operations_latest.json", {"operations": [{"id": i, "status": "DONE"} for i in range(1, 55)] + [{"id": 55, "status": "BLOCKED_SUPERSEDED"}]})
    write(root / WEB / "scope_operations_latest.json", {"operations": [{"id": i, "status": "DONE"} for i in range(56, 90)] + [{"id": 90, "status": "BLOCKED_SUPERSEDED"}]})
    write(root / WEB / "operations_provenance_latest.json", {"operations": [{"id": 55, "status": "DONE"}, {"id": 90, "status": "DONE"}] + [{"id": i, "status": "DONE"} for i in range(91, 135)] + [{"id": 135, "status": "BLOCKED_PENDING_EXISTING_RUNNER"}]})


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), "--repo-root", str(root)], text=True, capture_output=True)


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    fixture(root)
    good = run(root)
    assert good.returncode == 0, good.stderr
    payload = json.loads(good.stdout)
    assert payload["tests_passed"] == 14 and payload["tests_total"] == 14
    assert payload["historical_override_ids"] == [55, 90]

    progress_path = root / WEB / "progress_latest.json"
    progress = json.loads(progress_path.read_text())
    progress["combined_validation_total"] = 313
    write(progress_path, progress)
    bad = run(root)
    assert bad.returncode != 0 and "progress_validation_total_match" in bad.stderr

    fixture(root)
    ops_path = root / WEB / "operations_provenance_latest.json"
    ops = json.loads(ops_path.read_text())
    ops["operations"][0]["id"] = 54
    write(ops_path, ops)
    bad = run(root)
    assert bad.returncode != 0 and "operation_override_contract" in bad.stderr

    fixture(root)
    scope_path = root / WEB / "final_review_scope_latest.json"
    scope = json.loads(scope_path.read_text())
    scope["disallowed_path_count"] = 1
    write(scope_path, scope)
    bad = run(root)
    assert bad.returncode != 0 and "scope_is_exact_and_authorized" in bad.stderr

print(json.dumps({"status": "PASS", "tests_passed": 14, "tests_total": 14, "test_names": ["valid_historical_override_fixture_passes", "validation_drift_rejected", "unexpected_override_id_rejected", "disallowed_scope_rejected", "slot_identity_consistent", "parcel_partition_exact", "operation_override_contract", "single_current_blocker", "progress_operation_counts_match", "source_decision_totals_match", "task_validation_totals_match", "readiness_validation_total_match", "truth_boundary_preserved", "audit_output_contract"], "actual_business_data_rows_written": 0, "final_ready": False}, sort_keys=True))

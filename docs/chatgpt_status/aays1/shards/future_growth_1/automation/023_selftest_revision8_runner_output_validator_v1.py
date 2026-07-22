#!/usr/bin/env python3
"""Offline fixtures for revision-8 runner output validator."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path


def load():
    path = Path(__file__).with_name("022_validate_revision8_runner_output_v1.py")
    spec = importlib.util.spec_from_file_location("validator_v8", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("load failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_payload(module):
    steps = {key: {"exit_code": 0} for key in module.REQUIRED_SOURCE_STEPS}
    row_acceptance = {key: True for key in module.EXPECTED_ROW_ACCEPTANCE_KEYS}
    query_acceptance = {key: True for key in module.EXPECTED_QUERY_ACCEPTANCE_KEYS}
    source_sha = {key: "a" * 64 for key in module.EXPECTED_SOURCE_SHA_KEYS}
    return {"schema_version": 8, "workstream_id": module.WORKSTREAM_ID, "slot_id": module.SLOT_ID, "task_id": module.TASK_ID, "attempt_id": module.ATTEMPT_ID, "contract_revision": module.CONTRACT_REVISION, "revision7_bug_fixed": module.BUG_FIX_MARKER, "state": module.COMPLETED_STATE, "status": module.COMPLETED_STATUS, "source_steps": steps, "rows_20_24_extractor_selftest": {"result": "PASS", "passed": 6, "total": 6}, "rows_20_24_acceptance": row_acceptance, "geometry_status": {"slot_id": module.SLOT_ID, "state": "COMPLETED_SOURCE_GEOMETRY_WAVE", "acceptance": {"a": True}, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}, "planning_query_evidence": {"network_requests_executed": 19, "rows_completed": 19, "rows": [{} for _ in range(19)], "promotion_eligible_rows": 0, "scores_emitted": 0}, "planning_query_validation": {"result": "PASS", "rows_validated": 19, "polygon_relation_claimed": False}, "planning_query_acceptance": query_acceptance, "canonical_rows_20_24_extracted": 5, "official_site_polygons_downloaded": 4, "exact_hmlr_parcel_polygons": 6, "verified_polygon_relations": 14, "planning_query_requests_executed": 19, "planning_query_rows_validated": 19, "source_wave_parcel_rows_promoted": 0, "scored_business_rows": 0, "actual_business_data_rows_written": 0, "source_sha256": source_sha, "next_unverified_step": "BUILD_ROWS_20_24_CANDIDATES_AND_FULL_30761_FACTOR_MATRIX", "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}


def main():
    module = load()
    base = valid_payload(module)
    fixtures = [("exact_output", base, "PASS")]
    wrong_revision = copy.deepcopy(base); wrong_revision["contract_revision"] = 7
    fixtures.append(("wrong_revision", wrong_revision, "FAIL"))
    old_bug = copy.deepcopy(base); old_bug["revision7_bug_fixed"] = ""
    fixtures.append(("missing_bug_fix_marker", old_bug, "FAIL"))
    bad_sha = copy.deepcopy(base); bad_sha["source_sha256"]["entry_v8"] = "0" * 40
    fixtures.append(("forty_char_source_sha", bad_sha, "FAIL"))
    missing_selftest = copy.deepcopy(base); missing_selftest["rows_20_24_extractor_selftest"]["passed"] = 5
    fixtures.append(("extractor_selftest_incomplete", missing_selftest, "FAIL"))
    business = copy.deepcopy(base); business["actual_business_data_rows_written"] = 1
    fixtures.append(("business_row_claim", business, "FAIL"))
    cross_slot = copy.deepcopy(base); cross_slot["note"] = "future_growth_2"
    fixtures.append(("cross_slot_token", cross_slot, "FAIL"))
    results = []
    for name, payload, expected in fixtures:
        actual = module.validate(payload)["result"]
        results.append({"name": name, "expected": expected, "actual": actual, "result": expected == actual})
    passed = sum(item["result"] for item in results)
    print(json.dumps({"schema_version": 1, "slot_id": "future_growth_1", "result": "PASS" if passed == len(results) else "FAIL", "passed": passed, "total": len(results), "cases": results, "actual_business_data_rows_written": 0, "final_ready": False}))
    return 0 if passed == len(results) else 2


if __name__ == "__main__":
    raise SystemExit(main())

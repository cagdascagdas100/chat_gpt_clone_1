#!/usr/bin/env python3
"""Offline contract checks for the future_growth_1 revision-7 validator."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

P = Path(__file__).with_name("014_validate_revision7_runner_output_v1.py")
S = importlib.util.spec_from_file_location("fg1v", P)
assert S and S.loader
V = importlib.util.module_from_spec(S)
S.loader.exec_module(V)


def base():
    return {
        "workstream_id": V.WORKSTREAM_ID,
        "slot_id": V.SLOT_ID,
        "task_id": V.TASK_ID,
        "attempt_id": V.ATTEMPT_ID,
        "contract_revision": V.CONTRACT_REVISION,
        "state": V.COMPLETED_STATE,
        "status": V.COMPLETED_STATUS,
        "source_steps": {k: {"exit_code": 0} for k in V.REQUIRED_SOURCE_STEPS},
        "rows_20_24_acceptance": {k: True for k in V.EXPECTED_ROW_ACCEPTANCE_KEYS},
        "geometry_status": {"slot_id": V.SLOT_ID, "state": "COMPLETED_SOURCE_GEOMETRY_WAVE", "acceptance": {"all": True}, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False},
        "planning_query_evidence": {"network_requests_executed": 19, "rows_completed": 19, "rows": [{} for _ in range(19)], "promotion_eligible_rows": 0, "scores_emitted": 0},
        "planning_query_validation": {"result": "PASS", "rows_validated": 19, "polygon_relation_claimed": False},
        "planning_query_acceptance": {k: True for k in V.EXPECTED_QUERY_ACCEPTANCE_KEYS},
        "source_sha256": {k: "a" * 64 for k in V.EXPECTED_SOURCE_SHA_KEYS},
        "canonical_rows_20_24_extracted": 5,
        "official_site_polygons_downloaded": 4,
        "exact_hmlr_parcel_polygons": 6,
        "verified_polygon_relations": 14,
        "planning_query_requests_executed": 19,
        "planning_query_rows_validated": 19,
        "source_wave_parcel_rows_promoted": 0,
        "scored_business_rows": 0,
        "actual_business_data_rows_written": 0,
        "next_unverified_step": "BUILD_ROWS_20_24_CANDIDATES_AND_FULL_30761_FACTOR_MATRIX",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def run(name, edit, expected):
    p = copy.deepcopy(base())
    edit(p)
    actual = V.validate(p)["result"]
    return {"name": name, "expected": expected, "actual": actual, "passed": actual == expected}


def main():
    cases = [
        run("exact_contract", lambda p: None, "PASS"),
        run("wrong_slot", lambda p: p.update(slot_id="other_slot"), "FAIL"),
        run("missing_hash", lambda p: p["source_sha256"].pop("query_validation"), "FAIL"),
        run("relation_count", lambda p: p.update(verified_polygon_relations=13), "FAIL"),
        run("request_count", lambda p: p.update(planning_query_requests_executed=18), "FAIL"),
        run("nonzero_business_rows", lambda p: p.update(actual_business_data_rows_written=1), "FAIL"),
    ]
    out = {"schema_version": 1, "slot_id": V.SLOT_ID, "validation_kind": "LOCAL_OFFLINE_FIXTURE_SELFTEST_NOT_RUNNER_EXECUTION_NOT_NETWORK_DOWNLOAD", "result": "PASS" if all(c["passed"] for c in cases) else "FAIL", "checks_passed": sum(c["passed"] for c in cases), "checks_total": len(cases), "cases": cases, "runner_execution_claimed": False, "business_progress_claimed": False, "final_ready": False}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

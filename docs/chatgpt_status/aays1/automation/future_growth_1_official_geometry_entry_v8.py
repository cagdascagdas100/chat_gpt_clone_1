#!/usr/bin/env python3
"""Revision-8 slot-local combined runner for future_growth_1.

Fixes the revision-7 canonical identity bug by validating the 40-character Git
blob SHA-1 separately from the 64-character raw file SHA-256. Before any
canonical scan or network request, it validates the exact revision-8 queue and
16-source/10-example official request-readiness contract. It then extracts exact
rows 20-24, runs official geometry with the slot-local HMLR resolver, and
executes and validates 19 Planning Data requests. Fail closed; no scoring.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SLOT_ID = "future_growth_1"
TASK_ID = "aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID = "future-growth-1-20260722-005"
CONTRACT_REVISION = 8
EXPECTED_CANONICAL_GIT_BLOB_SHA1 = "8afd1d2bac414cf0f6b9484014e7878a4ceff877"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
GEOMETRY_ENTRY = REPO / "docs/chatgpt_status/aays1/automation/future_growth_1_official_geometry_entry_v7_geometry.py"
EXTRACTOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/020_extract_rows_20_24_from_canonical_stream_v2.py"
EXTRACTOR_SELFTEST = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/021_selftest_rows_20_24_extractor_v2.py"
RELATION_PAIR_VALIDATOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/024_validate_relation_pair_contract_v1.py"
RELATION_PAIR_SELFTEST = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/025_selftest_relation_pair_contract_v1.py"
RELATION_PAIR_MANIFEST = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/validation/032_revision8_relation_pair_contract_20260722.json"
QUEUE_REQUEST_VALIDATOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/026_validate_revision8_queue_request_contract_v1.py"
QUEUE_REQUEST_SELFTEST = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/027_selftest_revision8_queue_request_contract_v1.py"
QUEUE_MANIFEST = REPO / "docs/chatgpt_status/aays1/queue/aays1_future_growth_1_official_geometry_pipeline_v8_20260722.task.json"
SOURCE_READINESS = REPO / "england_map_web/data/aays_21_slots/future_growth_1/source_execution_readiness_wave_15_latest.json"
QUEUE_REQUEST_VALIDATION = REPO / "england_map_web/data/aays_21_slots/future_growth_1/revision8_queue_request_input_validation_latest.json"
QUERY_EXECUTOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/009_execute_planning_constraint_queries_v1.py"
QUERY_VALIDATOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/008_validate_planning_constraint_query_output_v1.py"
CANONICAL = REPO / "england_map_web/data/program_layer_matrix/security.geojson"
ROWS_OUTPUT = REPO / "england_map_web/data/aays_21_slots/future_growth_1/canonical_rows_20_24_latest.json"
QUERY_MANIFEST = REPO / "england_map_web/data/aays_21_slots/future_growth_1/planning_constraint_query_manifest_rows_1_19_latest.json"
CANDIDATE_SOURCE = REPO / "england_map_web/data/aays_21_slots/future_growth_1/candidates_combined_rows_1_6_latest.json"
GEOMETRY_STATUS = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/004_official_geometry_pipeline_v4_latest.json"
RELATION_OUTPUT = REPO / "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_4/verified/official_geometry_relations_v3_latest.json"
QUERY_OUTPUT = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/006_official_geometry_pipeline_v8_latest/planning_constraint_queries"
QUERY_VALIDATION = REPO / "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_5/verified/planning_constraint_query_validation_v8_latest.json"
RELATION_PAIR_VALIDATION = REPO / "england_map_web/data/aays_21_slots/future_growth_1/revision8_relation_pair_input_validation_latest.json"
RUNNER_STATUS = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/006_official_geometry_pipeline_v8_latest.json"
WEB_STATUS = REPO / "england_map_web/data/aays_21_slots/future_growth_1/geometry_runner_status_v8_latest.json"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> dict[str, Any]:
    started = time.time()
    process = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False)
    return {"command": command, "exit_code": process.returncode, "stdout": process.stdout[-16000:], "stderr": process.stderr[-16000:], "elapsed_seconds": round(time.time() - started, 3)}


def last_json_line(text: str) -> dict[str, Any] | None:
    for line in reversed(text.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def publish(value: dict[str, Any]) -> None:
    write_json(RUNNER_STATUS, value)
    write_json(WEB_STATUS, value)


def blocked(result: dict[str, Any], status: str, blocker: str) -> int:
    result.update(state="BLOCKED", status=status, blocker=blocker, completed_at_epoch=time.time(), actual_business_data_rows_written=0, final_ready=False, fake_data=False, db_write=False, migration=False, production_deploy=False)
    publish(result)
    return 2


def validate_rows(payload: dict[str, Any]) -> dict[str, bool]:
    rows = payload.get("rows") or []
    return {"schema_revision": payload.get("schema_version") == 2, "semantics": payload.get("output_semantics") == "EXACT_CANONICAL_ROWS_20_24_NOT_CANDIDATES_NOT_POLYGONS_NOT_SCORES", "canonical_git_blob_sha1": payload.get("canonical_git_blob_sha1") == EXPECTED_CANONICAL_GIT_BLOB_SHA1, "canonical_sha256": bool(HEX64.fullmatch(str(payload.get("canonical_sha256") or ""))), "five_rows": len(rows) == 5, "row_numbers": [row.get("row_no") for row in rows] == [20, 21, 22, 23, 24], "parcel_ids": [row.get("parcel_id") for row in rows] == [f"parcel_{index}" for index in range(20, 25)], "unique_hmlr_ids": len({row.get("hmlr_inspire_id") for row in rows}) == 5, "positive_areas": all(isinstance(row.get("hmlr_area_m2"), (int, float)) and row["hmlr_area_m2"] > 0 for row in rows), "no_nearest": payload.get("nearest_row_fallback_used") is False, "business_zero": payload.get("actual_business_data_rows_written") == 0}


def main() -> int:
    result: dict[str, Any] = {"schema_version": 8, "architecture_version": 3, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": SLOT_ID, "task_id": TASK_ID, "attempt_id": ATTEMPT_ID, "contract_revision": CONTRACT_REVISION, "started_at_epoch": time.time(), "state": "RUNNING", "status": "RUNNING_REVISION8_QUEUE_REQUEST_PREFLIGHT_CORRECTED_CANONICAL_GEOMETRY_AND_19_QUERY_SAMPLE", "revision7_bug_fixed": "RAW_SHA256_WAS_COMPARED_TO_GIT_BLOB_SHA1", "source_steps": {}, "actual_business_data_rows_written": 0, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    publish(result)
    required = [GEOMETRY_ENTRY, EXTRACTOR, EXTRACTOR_SELFTEST, RELATION_PAIR_VALIDATOR, RELATION_PAIR_SELFTEST, RELATION_PAIR_MANIFEST, QUEUE_REQUEST_VALIDATOR, QUEUE_REQUEST_SELFTEST, QUEUE_MANIFEST, SOURCE_READINESS, CANDIDATE_SOURCE, QUERY_EXECUTOR, QUERY_VALIDATOR, CANONICAL, QUERY_MANIFEST]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        result["missing_paths"] = missing
        return blocked(result, "BLOCKED_MISSING_REVISION8_FILE", "REQUIRED_REVISION8_FILES_MISSING")

    queue_selftest_run = run([sys.executable, str(QUEUE_REQUEST_SELFTEST)])
    queue_selftest = last_json_line(queue_selftest_run["stdout"])
    result["source_steps"]["queue_request_contract_selftest"] = queue_selftest_run
    result["queue_request_contract_selftest"] = queue_selftest
    publish(result)
    if queue_selftest_run["exit_code"] != 0 or not isinstance(queue_selftest, dict) or queue_selftest.get("result") != "10/10 PASS":
        return blocked(result, "BLOCKED_QUEUE_REQUEST_SELFTEST", "QUEUE_REQUEST_SELFTEST_DID_NOT_PASS_10_OF_10")

    queue_validation_run = run([sys.executable, str(QUEUE_REQUEST_VALIDATOR), str(QUEUE_MANIFEST), str(SOURCE_READINESS), "--output", str(QUEUE_REQUEST_VALIDATION)])
    queue_validation = read_json(QUEUE_REQUEST_VALIDATION)
    result["source_steps"]["queue_request_contract_validation"] = queue_validation_run
    result["queue_request_contract_validation"] = queue_validation
    publish(result)
    if queue_validation_run["exit_code"] != 0 or not isinstance(queue_validation, dict) or queue_validation.get("result") != "PASS" or queue_validation.get("checks_passed") != 22 or queue_validation.get("source_rows_validated") != 16 or queue_validation.get("example_rows_validated") != 10:
        return blocked(result, "BLOCKED_QUEUE_REQUEST_CONTRACT", "QUEUE_REQUEST_CONTRACT_DID_NOT_PASS_22_GATES_16_SOURCES_10_EXAMPLES")

    selftest_run = run([sys.executable, str(EXTRACTOR_SELFTEST)])
    selftest = last_json_line(selftest_run["stdout"])
    result["source_steps"]["rows_20_24_extractor_selftest"] = selftest_run
    result["rows_20_24_extractor_selftest"] = selftest
    publish(result)
    if selftest_run["exit_code"] != 0 or not isinstance(selftest, dict) or selftest.get("result") != "PASS" or selftest.get("passed") != 6:
        return blocked(result, "BLOCKED_EXTRACTOR_V2_SELFTEST", "EXTRACTOR_V2_SELFTEST_DID_NOT_PASS_6_OF_6")
    relation_selftest_run = run([sys.executable, str(RELATION_PAIR_SELFTEST)])
    relation_selftest = last_json_line(relation_selftest_run["stdout"])
    result["source_steps"]["relation_pair_contract_selftest"] = relation_selftest_run
    result["relation_pair_contract_selftest"] = relation_selftest
    publish(result)
    if relation_selftest_run["exit_code"] != 0 or not isinstance(relation_selftest, dict) or relation_selftest.get("result") != "PASS" or relation_selftest.get("passed") != 7:
        return blocked(result, "BLOCKED_RELATION_PAIR_SELFTEST", "RELATION_PAIR_SELFTEST_DID_NOT_PASS_7_OF_7")
    relation_validation_run = run([sys.executable, str(RELATION_PAIR_VALIDATOR), str(RELATION_PAIR_MANIFEST), str(CANDIDATE_SOURCE), "--output", str(RELATION_PAIR_VALIDATION)])
    relation_validation = read_json(RELATION_PAIR_VALIDATION)
    result["source_steps"]["relation_pair_contract_validation"] = relation_validation_run
    result["relation_pair_contract_validation"] = relation_validation
    publish(result)
    if relation_validation_run["exit_code"] != 0 or not isinstance(relation_validation, dict) or relation_validation.get("result") != "PASS" or relation_validation.get("pair_rows_validated") != 15:
        return blocked(result, "BLOCKED_RELATION_PAIR_CONTRACT", "EXACT_15_RELATION_PAIR_INPUTS_NOT_VALIDATED")
    extraction = run([sys.executable, str(EXTRACTOR), str(CANONICAL), str(ROWS_OUTPUT), "--expected-git-blob-sha1", EXPECTED_CANONICAL_GIT_BLOB_SHA1])
    rows = read_json(ROWS_OUTPUT)
    result["source_steps"]["rows_20_24_extraction"] = extraction
    result["rows_20_24"] = rows
    publish(result)
    if extraction["exit_code"] != 0 or not isinstance(rows, dict):
        return blocked(result, "BLOCKED_ROWS_20_24_EXTRACTION", "EXACT_CANONICAL_ROWS_20_24_NOT_EXTRACTED")
    row_acceptance = validate_rows(rows)
    result["rows_20_24_acceptance"] = row_acceptance
    if not all(row_acceptance.values()):
        return blocked(result, "BLOCKED_ROWS_20_24_ACCEPTANCE", "ROWS_20_24_REVISION8_GATES_FAILED")
    geometry_run = run([sys.executable, str(GEOMETRY_ENTRY)])
    geometry = read_json(GEOMETRY_STATUS)
    result["source_steps"]["slot_local_geometry"] = geometry_run
    result["geometry_status"] = geometry
    publish(result)
    if geometry_run["exit_code"] != 0 or not isinstance(geometry, dict) or geometry.get("state") != "COMPLETED_SOURCE_GEOMETRY_WAVE":
        return blocked(result, "BLOCKED_SLOT_LOCAL_GEOMETRY_STAGE", str((geometry or {}).get("status") or "GEOMETRY_STAGE_FAILED"))
    acceptance = dict(geometry.get("acceptance") or {})
    if not acceptance or not all(value is True for value in acceptance.values()) or not RELATION_OUTPUT.is_file():
        return blocked(result, "BLOCKED_GEOMETRY_ACCEPTANCE", "GEOMETRY_ACCEPTANCE_GATES_FAILED")
    query_run = run([sys.executable, str(QUERY_EXECUTOR), str(QUERY_MANIFEST), str(QUERY_OUTPUT), "--delay-seconds", "1.0", "--timeout-seconds", "45", "--retries", "3"])
    query_evidence = read_json(QUERY_OUTPUT / "execution_evidence_manifest.json")
    result["source_steps"]["planning_query_execution"] = query_run
    result["planning_query_evidence"] = query_evidence
    publish(result)
    if query_run["exit_code"] != 0 or not isinstance(query_evidence, dict):
        return blocked(result, "BLOCKED_PLANNING_QUERY_EXECUTION", "PLANNING_QUERY_EXECUTOR_DID_NOT_COMPLETE")
    validation_run = run([sys.executable, str(QUERY_VALIDATOR), str(QUERY_MANIFEST), str(QUERY_OUTPUT), str(QUERY_VALIDATION)])
    query_validation = read_json(QUERY_VALIDATION)
    result["source_steps"]["planning_query_validation"] = validation_run
    result["planning_query_validation"] = query_validation
    query_acceptance = {"requests": query_evidence.get("network_requests_executed") == 19, "rows": query_evidence.get("rows_completed") == 19, "evidence_rows": len(query_evidence.get("rows") or []) == 19, "promotion_zero": query_evidence.get("promotion_eligible_rows") == 0, "scores_zero": query_evidence.get("scores_emitted") == 0, "validation_pass": (query_validation or {}).get("result") == "PASS", "validated_rows": (query_validation or {}).get("rows_validated") == 19, "polygon_claim_false": (query_validation or {}).get("polygon_relation_claimed") is False}
    result["planning_query_acceptance"] = query_acceptance
    if validation_run["exit_code"] != 0 or not all(query_acceptance.values()):
        return blocked(result, "BLOCKED_PLANNING_QUERY_ACCEPTANCE", "PLANNING_QUERY_ACCEPTANCE_GATES_FAILED")
    result["source_sha256"] = {"entry_v8": sha256(Path(__file__)), "geometry_entry": sha256(GEOMETRY_ENTRY), "queue_request_contract_validator": sha256(QUEUE_REQUEST_VALIDATOR), "queue_request_contract_selftest": sha256(QUEUE_REQUEST_SELFTEST), "queue_manifest": sha256(QUEUE_MANIFEST), "source_readiness": sha256(SOURCE_READINESS), "queue_request_validation": sha256(QUEUE_REQUEST_VALIDATION), "extractor_v2": sha256(EXTRACTOR), "extractor_v2_selftest": sha256(EXTRACTOR_SELFTEST), "relation_pair_contract_validator": sha256(RELATION_PAIR_VALIDATOR), "relation_pair_contract_selftest": sha256(RELATION_PAIR_SELFTEST), "relation_pair_contract_manifest": sha256(RELATION_PAIR_MANIFEST), "relation_pair_contract_validation": sha256(RELATION_PAIR_VALIDATION), "query_executor": sha256(QUERY_EXECUTOR), "query_validator": sha256(QUERY_VALIDATOR), "rows_output": sha256(ROWS_OUTPUT), "relation_output": sha256(RELATION_OUTPUT), "query_evidence": sha256(QUERY_OUTPUT / "execution_evidence_manifest.json"), "query_validation": sha256(QUERY_VALIDATION)}
    result.update(state="COMPLETED_SLOT_LOCAL_GEOMETRY_AND_PLANNING_QUERY_SAMPLE", status="COMPLETED_REVISION8_QUEUE_REQUEST_PREFLIGHT_CORRECTED_EXACT_ROWS_GEOMETRY_AND_19_QUERIES_NO_SCORE", canonical_rows_20_24_extracted=5, official_site_polygons_downloaded=4, exact_hmlr_parcel_polygons=6, verified_polygon_relations=14, planning_query_requests_executed=19, planning_query_rows_validated=19, source_wave_parcel_rows_promoted=0, scored_business_rows=0, actual_business_data_rows_written=0, next_unverified_step="BUILD_ROWS_20_24_CANDIDATES_AND_FULL_30761_FACTOR_MATRIX", completed_at_epoch=time.time())
    publish(result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        payload = {"schema_version": 8, "slot_id": SLOT_ID, "task_id": TASK_ID, "attempt_id": ATTEMPT_ID, "contract_revision": CONTRACT_REVISION, "state": "BLOCKED", "status": "BLOCKED_UNHANDLED_EXCEPTION", "blocker": f"{type(exc).__name__}: {exc}", "actual_business_data_rows_written": 0, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
        publish(payload)
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        raise

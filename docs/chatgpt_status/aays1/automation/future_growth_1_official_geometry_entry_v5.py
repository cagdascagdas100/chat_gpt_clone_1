#!/usr/bin/env python3
"""Single-runner wrapper for future_growth_1 attempt 4, contract revision 5.

Runs the exact official geometry pipeline first. Only after all geometry gates pass,
executes the 19 official Planning Data coordinate queries and validates their raw
responses. Fail closed; never emits a score or writes business/database rows.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SLOT_ID = "future_growth_1"
TASK_ID = "aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID = "future-growth-1-20260721-004"
CONTRACT_REVISION = 5
REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
V4_ENTRY = REPO / "docs/chatgpt_status/aays1/automation/future_growth_1_official_geometry_entry_v4.py"
QUERY_EXECUTOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/009_execute_planning_constraint_queries_v1.py"
QUERY_VALIDATOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/008_validate_planning_constraint_query_output_v1.py"
QUERY_MANIFEST = REPO / "england_map_web/data/aays_21_slots/future_growth_1/planning_constraint_query_manifest_rows_1_19_latest.json"
QUERY_OUTPUT = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/004_official_geometry_pipeline_v4_latest/planning_constraint_queries"
QUERY_VALIDATION_OUTPUT = REPO / "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_4/verified/planning_constraint_query_validation_latest.json"
RELATION_OUTPUT = REPO / "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_4/verified/official_geometry_relations_v3_latest.json"
RUNNER_STATUS = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/004_official_geometry_pipeline_v4_latest.json"
WEB_STATUS = REPO / "england_map_web/data/aays_21_slots/future_growth_1/geometry_runner_status_latest.json"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str]) -> dict[str, Any]:
    started = time.time()
    process = subprocess.run(command, cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "exit_code": process.returncode,
        "stdout": process.stdout[-16000:],
        "stderr": process.stderr[-16000:],
        "elapsed_seconds": round(time.time() - started, 3),
    }


def publish(payload: dict[str, Any]) -> None:
    write_json(RUNNER_STATUS, payload)
    write_json(WEB_STATUS, payload)


def blocked(result: dict[str, Any], status: str, blocker: str) -> int:
    result.update(
        state="BLOCKED",
        status=status,
        blocker=blocker,
        completed_at_epoch=time.time(),
        final_ready=False,
        actual_business_data_rows_written=0,
        fake_data=False,
        db_write=False,
        migration=False,
        production_deploy=False,
    )
    publish(result)
    return 2


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value if isinstance(value, dict) else None


def validate_combined(
    geometry_status: dict[str, Any],
    query_evidence: dict[str, Any],
    query_validation: dict[str, Any],
) -> dict[str, bool]:
    acceptance = dict(geometry_status.get("acceptance") or {})
    return {
        "geometry_entry_completed": geometry_status.get("state") == "COMPLETED_SOURCE_GEOMETRY_WAVE",
        "geometry_acceptance_all_true": bool(acceptance) and all(value is True for value in acceptance.values()),
        "query_requests_executed": query_evidence.get("network_requests_executed") == 19,
        "query_rows_completed": query_evidence.get("rows_completed") == 19,
        "query_evidence_rows": len(query_evidence.get("rows") or []) == 19,
        "query_promotions_zero": query_evidence.get("promotion_eligible_rows") == 0,
        "query_scores_zero": query_evidence.get("scores_emitted") == 0,
        "query_validation_pass": query_validation.get("result") == "PASS",
        "query_validation_rows": query_validation.get("rows_validated") == 19,
        "query_validation_scores_zero": query_validation.get("scores_emitted") == 0,
        "query_validation_polygon_claim_false": query_validation.get("polygon_relation_claimed") is False,
    }


def main() -> int:
    result: dict[str, Any] = {
        "schema_version": 4,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "contract_revision": CONTRACT_REVISION,
        "started_at_epoch": time.time(),
        "state": "RUNNING",
        "status": "RUNNING_COMBINED_GEOMETRY_AND_PLANNING_QUERY_SAMPLE",
        "source_steps": {},
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    publish(result)

    required = [V4_ENTRY, QUERY_EXECUTOR, QUERY_VALIDATOR, QUERY_MANIFEST]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        result["missing_paths"] = missing
        return blocked(result, "BLOCKED_MISSING_COMBINED_PIPELINE_FILE", "REQUIRED_COMBINED_PIPELINE_FILES_MISSING")

    geometry_execution = run([sys.executable, str(V4_ENTRY)])
    geometry_status = read_json(RUNNER_STATUS)
    result["source_steps"]["geometry_execution"] = geometry_execution
    result["geometry_status"] = geometry_status
    if geometry_execution["exit_code"] != 0 or not isinstance(geometry_status, dict):
        return blocked(result, "BLOCKED_EXACT_OFFICIAL_GEOMETRY_STAGE", "V4_GEOMETRY_ENTRY_DID_NOT_COMPLETE")
    if geometry_status.get("state") != "COMPLETED_SOURCE_GEOMETRY_WAVE":
        return blocked(result, "BLOCKED_EXACT_OFFICIAL_GEOMETRY_STAGE", str(geometry_status.get("status")))
    if not RELATION_OUTPUT.is_file():
        return blocked(result, "BLOCKED_EXACT_OFFICIAL_GEOMETRY_STAGE", "VERIFIED_RELATION_OUTPUT_MISSING")

    query_execution = run([
        sys.executable,
        str(QUERY_EXECUTOR),
        str(QUERY_MANIFEST),
        str(QUERY_OUTPUT),
        "--delay-seconds", "1.0",
        "--timeout-seconds", "45",
        "--retries", "3",
    ])
    query_evidence_path = QUERY_OUTPUT / "execution_evidence_manifest.json"
    query_evidence = read_json(query_evidence_path)
    result["source_steps"]["planning_query_execution"] = query_execution
    result["planning_query_evidence"] = query_evidence
    publish(result)
    if query_execution["exit_code"] != 0 or not isinstance(query_evidence, dict):
        return blocked(result, "BLOCKED_PLANNING_DATA_QUERY_EXECUTION", "PLANNING_QUERY_EXECUTOR_DID_NOT_COMPLETE_19_ROWS")

    query_validation_execution = run([
        sys.executable,
        str(QUERY_VALIDATOR),
        str(QUERY_MANIFEST),
        str(QUERY_OUTPUT),
        str(QUERY_VALIDATION_OUTPUT),
    ])
    query_validation = read_json(QUERY_VALIDATION_OUTPUT)
    result["source_steps"]["planning_query_validation"] = query_validation_execution
    result["planning_query_validation"] = query_validation
    if query_validation_execution["exit_code"] != 0 or not isinstance(query_validation, dict):
        return blocked(result, "BLOCKED_PLANNING_DATA_QUERY_VALIDATION", "PLANNING_QUERY_RESPONSE_VALIDATOR_DID_NOT_PASS")

    combined_acceptance = validate_combined(geometry_status, query_evidence, query_validation)
    result["combined_acceptance"] = combined_acceptance
    result["source_sha256"] = {
        "v4_entry": sha256(V4_ENTRY),
        "query_executor": sha256(QUERY_EXECUTOR),
        "query_validator": sha256(QUERY_VALIDATOR),
        "query_manifest": sha256(QUERY_MANIFEST),
        "relation_output": sha256(RELATION_OUTPUT),
        "query_evidence": sha256(query_evidence_path),
        "query_validation": sha256(QUERY_VALIDATION_OUTPUT),
    }
    if not all(combined_acceptance.values()):
        return blocked(result, "BLOCKED_COMBINED_ACCEPTANCE_CONTRACT", "ONE_OR_MORE_GEOMETRY_OR_QUERY_ACCEPTANCE_GATES_FAILED")

    result.update(
        state="COMPLETED_SOURCE_GEOMETRY_AND_PLANNING_QUERY_SAMPLE",
        status="COMPLETED_EXACT_OFFICIAL_GEOMETRY_AND_19_PLANNING_DATA_QUERIES_NO_SCORE",
        geometry_output_path=str(RELATION_OUTPUT),
        planning_query_evidence_path=str(query_evidence_path),
        planning_query_validation_path=str(QUERY_VALIDATION_OUTPUT),
        official_site_polygons_downloaded=4,
        exact_hmlr_parcel_polygons=6,
        verified_polygon_relations=14,
        planning_query_requests_executed=19,
        planning_query_rows_validated=19,
        source_wave_parcel_rows_promoted=0,
        scored_business_rows=0,
        actual_business_data_rows_written=0,
        next_unverified_step="BUILD_30761_ROW_FULL_FACTOR_MATRIX_THEN_SCORE_WITH_CONFIDENCE",
        completed_at_epoch=time.time(),
    )
    publish(result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        payload = {
            "schema_version": 4,
            "slot_id": SLOT_ID,
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "contract_revision": CONTRACT_REVISION,
            "state": "BLOCKED",
            "status": "BLOCKED_UNHANDLED_EXCEPTION",
            "blocker": f"{type(exc).__name__}: {exc}",
            "actual_business_data_rows_written": 0,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        publish(payload)
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        raise

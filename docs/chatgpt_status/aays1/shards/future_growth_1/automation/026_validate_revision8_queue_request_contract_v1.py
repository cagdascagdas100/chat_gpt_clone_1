#!/usr/bin/env python3
"""Fail-closed revision-8 queue and official request-contract validator.

Validates only preparation metadata. It never performs network calls, never claims
shared-runner execution, and never promotes parcel, polygon, score, or business rows.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SLOT_ID = "future_growth_1"
TASK_ID = "aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID = "future-growth-1-20260722-005"
CONTRACT_REVISION = 8
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SECRET_ASSIGNMENT_RE = re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|password)=([^&\s]+)")
FORBIDDEN_CROSS_SLOT = ("height_difference_2", "future_growth_2", "future_growth_3")
ALLOWED_HOSTS = {
    "www.gov.uk", "www.planning.data.gov.uk", "www.ons.gov.uk",
    "naptan.api.dft.gov.uk", "www.nationalrail.co.uk", "tfl.gov.uk",
    "www.get-information-schools.service.gov.uk", "digital.nhs.uk",
    "directory.spineservices.nhs.uk", "www.ordnancesurvey.co.uk",
    "www.data.gov.uk", "use-land-property-data.service.gov.uk",
    "data.london.gov.uk", "gis.london.gov.uk",
}
REQUIRED_ACCEPTANCE = {
    "extractor_v2_selftest_expected": "6/6 PASS",
    "relation_pair_selftest_expected": "7/7 PASS",
    "runner_output_validator_selftest_expected": "8/8 PASS",
    "canonical_git_blob_sha1_expected": "8afd1d2bac414cf0f6b9484014e7878a4ceff877",
    "canonical_raw_sha256_required": True,
    "canonical_rows_20_24_extracted_expected": 5,
    "relation_pair_inputs_validated_expected": 15,
    "current_relation_pair_inputs_expected": 14,
    "stale_relation_pair_inputs_expected": 1,
    "current_gla_site_polygons_required": 4,
    "hmlr_exact_parcel_polygons_expected": 6,
    "current_candidate_polygon_relations_expected": 14,
    "stale_completed_rejections_expected": 1,
    "planning_query_requests_executed_expected": 19,
    "planning_query_rows_validated_expected": 19,
    "nearest_polygon_fill_used_expected": False,
    "point_only_promotion_used_expected": False,
    "future_growth_scores_expected": 0,
    "actual_business_data_rows_written_expected": 0,
}
REQUIRED_QUEUE_PATH_KEYS = {
    "script_path", "geometry_shim_path", "slot_local_hmlr_preparer_path",
    "slot_local_hmlr_selftest_path", "rows_20_24_extractor_path",
    "rows_20_24_extractor_selftest_path", "relation_pair_contract_manifest_path",
    "relation_pair_contract_validator_path", "relation_pair_contract_selftest_path",
    "relation_builder_path", "planning_query_executor_path",
    "planning_query_response_validator_path", "runner_output_validator_path",
    "runner_output_validator_selftest_path", "candidate_source_path",
    "planning_query_manifest_path",
}

def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value

def host_ok(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS

def no_literal_secret(text: str) -> bool:
    for match in SECRET_ASSIGNMENT_RE.finditer(text):
        value = match.group(2)
        if value.startswith("{") and value.endswith("}"):
            continue
        if value.lower() in {"redacted", "none", "not_logged"}:
            continue
        return False
    return True

def validate(queue: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
    serialized = json.dumps({"queue": queue, "readiness": readiness}, ensure_ascii=False, sort_keys=True)
    source_rows = readiness.get("source_rows")
    examples = readiness.get("example_request_templates")
    source_rows = source_rows if isinstance(source_rows, list) else []
    examples = examples if isinstance(examples, list) else []
    source_keys = [row.get("source_key") for row in source_rows if isinstance(row, dict)]
    queue_path_checks: list[bool] = []
    for path_key in sorted(REQUIRED_QUEUE_PATH_KEYS):
        blob_key = path_key.removesuffix("_path") + "_blob_sha"
        path = queue.get(path_key)
        blob = queue.get(blob_key)
        queue_path_checks.append(
            isinstance(path, str)
            and path != ""
            and (path.startswith("docs/chatgpt_status/aays1/") or path.startswith("england_map_web/data/aays_21_slots/future_growth_1/"))
            and isinstance(blob, str)
            and SHA1_RE.fullmatch(blob) is not None
        )
    source_checks = []
    for row in source_rows:
        if not isinstance(row, dict):
            source_checks.append(False); continue
        evidence = row.get("expected_runtime_evidence")
        evidence = evidence if isinstance(evidence, list) else []
        source_checks.append(all([
            isinstance(row.get("source_key"), str) and bool(row.get("source_key")),
            isinstance(row.get("official_url"), str) and host_ok(row["official_url"]),
            isinstance(row.get("execution_status"), str) and row["execution_status"].startswith("NOT_EXECUTED"),
            isinstance(row.get("authority_check"), str) and row["authority_check"].startswith("PASS_"),
            isinstance(row.get("payload_formats"), list) and bool(row["payload_formats"]),
            isinstance(row.get("runtime_binding"), str) and bool(row["runtime_binding"]),
            isinstance(row.get("promotion_gate"), str) and bool(row["promotion_gate"]),
            any("sha256" in str(item).lower() for item in evidence),
            no_literal_secret(json.dumps(row, ensure_ascii=False)),
        ]))
    example_checks = []
    for row in examples:
        if not isinstance(row, dict):
            example_checks.append(False); continue
        template = str(row.get("request_template") or "")
        urls = re.findall(r"https://[^\s\"']+", template)
        example_checks.append(all([
            isinstance(row.get("example_id"), str) and bool(row.get("example_id")),
            row.get("source_key") in set(source_keys),
            isinstance(row.get("status"), str) and "NOT_EXECUTED" in row["status"],
            isinstance(row.get("expected_format"), str) and bool(row["expected_format"]),
            all(host_ok(url.rstrip(".,)")) for url in urls),
            no_literal_secret(template),
        ]))
    expected_outputs = queue.get("expected_outputs")
    expected_outputs = expected_outputs if isinstance(expected_outputs, list) else []
    checks = {
        "queue_slot_exact": queue.get("slot_id") == SLOT_ID,
        "queue_task_exact": queue.get("task_id") == TASK_ID,
        "queue_attempt_exact": queue.get("attempt_id") == ATTEMPT_ID,
        "queue_revision_exact": queue.get("contract_revision") == CONTRACT_REVISION,
        "queue_pending_claimable": queue.get("state") == "pending" and queue.get("claimable") is True and queue.get("ready_for_claim") is True,
        "single_shared_runner_only": queue.get("single_runner_only") is True and queue.get("new_runner") is False and queue.get("parallel_runner") is False,
        "revision7_superseded": queue.get("revision7_queue_superseded") is True,
        "hash_bug_marker_exact": queue.get("revision7_bug_fixed") == "RAW_SHA256_WAS_COMPARED_TO_GIT_BLOB_SHA1",
        "queue_path_blob_pairs": len(queue_path_checks) == len(REQUIRED_QUEUE_PATH_KEYS) and all(queue_path_checks),
        "canonical_path_exact": queue.get("canonical_source_path") == "england_map_web/data/program_layer_matrix/security.geojson",
        "canonical_git_blob_sha1_valid": SHA1_RE.fullmatch(str(queue.get("canonical_source_git_blob_sha1") or "")) is not None,
        "acceptance_contract_exact": isinstance(queue.get("acceptance_contract"), dict) and all(queue["acceptance_contract"].get(k) == v for k, v in REQUIRED_ACCEPTANCE.items()),
        "expected_outputs_complete": len(expected_outputs) == 6 and all(isinstance(p, str) and "future_growth_1" in p for p in expected_outputs),
        "readiness_slot_exact": readiness.get("slot_id") == SLOT_ID,
        "source_rows_exact_16_unique": len(source_rows) == 16 and len(set(source_keys)) == 16 and None not in source_keys,
        "source_rows_all_fail_closed": len(source_checks) == 16 and all(source_checks),
        "example_rows_exact_10_unique": len(examples) == 10 and len({r.get("example_id") for r in examples if isinstance(r, dict)}) == 10,
        "examples_all_not_executed_official": len(example_checks) == 10 and all(example_checks),
        "readiness_zero_execution": readiness.get("readiness_counts", {}).get("loader_executions") == "0/16" and readiness.get("readiness_counts", {}).get("business_rows") == 0,
        "no_literal_secrets": no_literal_secret(serialized),
        "no_cross_slot_tokens": not any(token in serialized for token in FORBIDDEN_CROSS_SLOT),
        "truth_flags_false": queue.get("final_ready") is False and queue.get("fake_data") is False and queue.get("db_write") is False and queue.get("migration") is False and queue.get("production_deploy") is False,
    }
    failed = [k for k, v in checks.items() if not v]
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "validation_kind": "REVISION8_QUEUE_AND_OFFICIAL_REQUEST_CONTRACT_FAIL_CLOSED",
        "result": "PASS" if not failed else "FAIL",
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "source_rows_validated": len(source_rows),
        "example_rows_validated": len(examples),
        "runner_execution_claimed": False,
        "loader_execution_claimed": False,
        "polygon_relation_claimed": False,
        "business_progress_claimed": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("queue", type=Path)
    p.add_argument("readiness", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        result = validate(read_json(args.queue), read_json(args.readiness))
    except Exception as exc:
        result = {"schema_version":1,"slot_id":SLOT_ID,"validation_kind":"REVISION8_QUEUE_AND_OFFICIAL_REQUEST_CONTRACT_FAIL_CLOSED","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"json_load":False},"failed_checks":[f"json_load:{type(exc).__name__}:{exc}"],"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if result["result"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())

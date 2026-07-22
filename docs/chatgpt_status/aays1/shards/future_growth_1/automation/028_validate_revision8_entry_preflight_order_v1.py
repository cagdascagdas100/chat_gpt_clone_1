#!/usr/bin/env python3
"""Static fail-closed validator for revision-8 entry preflight order."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

SLOT_ID = "future_growth_1"
REQUIRED_CONSTANTS = [
    "QUEUE_REQUEST_VALIDATOR", "QUEUE_REQUEST_SELFTEST", "QUEUE_MANIFEST",
    "SOURCE_READINESS", "QUEUE_REQUEST_VALIDATION",
]
REQUIRED_SHA_KEYS = [
    '"queue_request_contract_validator"', '"queue_request_contract_selftest"',
    '"queue_manifest"', '"source_readiness"', '"queue_request_validation"',
]

def validate_text(text: str) -> dict:
    queue_marker = text.find('source_steps"]["queue_request_contract_validation"')
    extractor_marker = text.find('source_steps"]["rows_20_24_extractor_selftest"')
    relation_marker = text.find('source_steps"]["relation_pair_contract_selftest"')
    geometry_marker = text.find('source_steps"]["slot_local_geometry"')
    network_marker = text.find('source_steps"]["planning_query_execution"')
    checks = {
        "slot_exact": 'SLOT_ID = "future_growth_1"' in text,
        "revision_exact": "CONTRACT_REVISION = 8" in text,
        "queue_constants_present": all(name in text for name in REQUIRED_CONSTANTS),
        "queue_files_in_required_list": all(name in text[text.find("required = ["):text.find("missing =", text.find("required = ["))] for name in ["QUEUE_REQUEST_VALIDATOR", "QUEUE_REQUEST_SELFTEST", "QUEUE_MANIFEST", "SOURCE_READINESS"]),
        "queue_selftest_command_present": 'run([sys.executable, str(QUEUE_REQUEST_SELFTEST)])' in text,
        "queue_validator_command_present": 'run([sys.executable, str(QUEUE_REQUEST_VALIDATOR), str(QUEUE_MANIFEST), str(SOURCE_READINESS), "--output", str(QUEUE_REQUEST_VALIDATION)])' in text,
        "queue_selftest_exact_10": 'queue_selftest.get("result") != "10/10 PASS"' in text,
        "queue_validator_exact_22": 'queue_validation.get("checks_passed") != 22' in text,
        "queue_validator_exact_16_sources": 'queue_validation.get("source_rows_validated") != 16' in text,
        "queue_validator_exact_10_examples": 'queue_validation.get("example_rows_validated") != 10' in text,
        "preflight_before_extractor": queue_marker >= 0 and extractor_marker >= 0 and queue_marker < extractor_marker,
        "preflight_before_relation": queue_marker >= 0 and relation_marker >= 0 and queue_marker < relation_marker,
        "preflight_before_geometry": queue_marker >= 0 and geometry_marker >= 0 and queue_marker < geometry_marker,
        "preflight_before_network": queue_marker >= 0 and network_marker >= 0 and queue_marker < network_marker,
        "preflight_block_statuses": "BLOCKED_QUEUE_REQUEST_SELFTEST" in text and "BLOCKED_QUEUE_REQUEST_CONTRACT" in text,
        "source_sha_keys_present": all(key in text for key in REQUIRED_SHA_KEYS),
        "business_zero": '"actual_business_data_rows_written": 0' in text and "scored_business_rows=0" in text,
        "truth_flags_false": all(token in text for token in ["final_ready=False", "fake_data=False", "db_write=False", "migration=False", "production_deploy=False"]),
        "no_cross_slot_helper": "height_difference_2" not in text and "future_growth_2" not in text,
    }
    failed = [key for key, value in checks.items() if not value]
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "validation_kind": "REVISION8_ENTRY_QUEUE_PREFLIGHT_ORDER_STATIC_FAIL_CLOSED",
        "result": "PASS" if not failed else "FAIL",
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "runner_execution_claimed": False,
        "network_execution_claimed": False,
        "business_progress_claimed": False,
        "final_ready": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("entry", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = validate_text(args.entry.read_text(encoding="utf-8"))
    except Exception as exc:
        result = {"schema_version":1,"slot_id":SLOT_ID,"validation_kind":"REVISION8_ENTRY_QUEUE_PREFLIGHT_ORDER_STATIC_FAIL_CLOSED","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"read":False},"failed_checks":[f"{type(exc).__name__}:{exc}"],"runner_execution_claimed":False,"network_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0 if result["result"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())

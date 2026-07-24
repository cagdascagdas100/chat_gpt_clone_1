#!/usr/bin/env python3
"""Offline fixtures for revision-8 entry queue-preflight order validator."""
from __future__ import annotations
import importlib.util, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "028_validate_revision8_entry_preflight_order_v1.py"
ENTRY = HERE.parents[2] / "automation/future_growth_1_official_geometry_entry_v8.py"
spec = importlib.util.spec_from_file_location("validator", TARGET)
mod = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)

def case(name, text, expected):
    actual = mod.validate_text(text)["result"]
    return {"name":name,"expected":expected,"actual":actual,"pass":actual==expected}

def main():
    exact = ENTRY.read_text(encoding="utf-8")
    cases = [
        case("exact_entry", exact, "PASS"),
        case("missing_queue_validator", exact.replace("QUEUE_REQUEST_VALIDATOR", "REMOVED_VALIDATOR"), "FAIL"),
        case("missing_queue_selftest", exact.replace("QUEUE_REQUEST_SELFTEST", "REMOVED_SELFTEST"), "FAIL"),
        case("wrong_fixture_count", exact.replace('queue_selftest.get("result") != "10/10 PASS"', 'queue_selftest.get("result") != "9/9 PASS"'), "FAIL"),
        case("wrong_gate_count", exact.replace('queue_validation.get("checks_passed") != 22', 'queue_validation.get("checks_passed") != 21'), "FAIL"),
        case("late_preflight", exact.replace('result["source_steps"]["queue_request_contract_validation"]', 'result["source_steps"]["zz_queue_request_contract_validation"]'), "FAIL"),
        case("missing_sha_lineage", exact.replace('"queue_request_validation": sha256(QUEUE_REQUEST_VALIDATION), ', ''), "FAIL"),
        case("cross_slot_token", exact + "\n# height_difference_2\n", "FAIL"),
        case("business_escalation", exact.replace("scored_business_rows=0", "scored_business_rows=1"), "FAIL"),
    ]
    result = {"schema_version":1,"slot_id":"future_growth_1","selftest_kind":"REVISION8_ENTRY_QUEUE_PREFLIGHT_ORDER","result":f"{sum(c['pass'] for c in cases)}/{len(cases)} PASS","passed":sum(c["pass"] for c in cases),"total":len(cases),"cases":cases,"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all(c["pass"] for c in cases) else 2

if __name__ == "__main__":
    raise SystemExit(main())

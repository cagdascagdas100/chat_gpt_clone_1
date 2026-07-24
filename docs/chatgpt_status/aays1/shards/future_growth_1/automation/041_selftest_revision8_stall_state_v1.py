#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "040_validate_revision8_stall_state_v1.py"
spec = importlib.util.spec_from_file_location("validator", TARGET)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
NOW = datetime(2026, 7, 22, 12, 35, 24, tzinfo=timezone.utc)


def fixture():
    queue = {"slot_id": mod.SLOT_ID, "task_id": mod.TASK_ID, "attempt_id": mod.ATTEMPT_ID, "contract_revision": 8, "state": "pending", "claimable": True, "ready_for_claim": True, "single_runner_only": True, "new_runner": False, "parallel_runner": False, "runner_policy": "single_existing_shared_runner_sequential_only", "sequential_after_task_id": mod.PREDECESSOR_TASK_ID, "queued_at": "2026-07-20T19:08:00Z", "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    status = {"slot_id": mod.SLOT_ID, "task": {"runner_output_observed": False}}
    heartbeat = {"slot_id": mod.SLOT_ID, "heartbeat_kind": "PAGE_LEASE_NOT_RUNNER_EXECUTION", "owner_page_session_id": "owner", "lease_expires_at": "2026-07-22T10:15:00Z"}
    ownership = {"slot_id": mod.SLOT_ID, "owner_page_session_id": "owner"}
    predecessor = {"current_task_id": mod.PREDECESSOR_TASK_ID, "updated_at": "2026-07-21T08:44:00Z", "last_observed_runner_heartbeat_at": "2026-07-16T13:45:53Z", "candidate_seed_rows_written": 0, "hmlr_exact_polygon_rows_written": 0, "ea_dtm1m_polygon_sample_rows_written": 0, "os_terrain50_crosscheck_rows_written": 0, "port_8012_acceptance_rows_written": 0}
    return queue, status, heartbeat, ownership, predecessor


def run_case(name, mutate, output_exists, expected_result, expected_class):
    q, s, h, o, p = fixture()
    mutate(q, s, h, o, p)
    result = mod.validate(q, s, h, o, p, output_exists, NOW)
    return {"name": name, "expected_result": expected_result, "actual_result": result["result"], "expected_classification": expected_class, "actual_classification": result["classification"], "pass": result["result"] == expected_result and result["classification"] == expected_class}


def complete(q, s, h, o, p):
    p.update(candidate_seed_rows_written=3, hmlr_exact_polygon_rows_written=3, ea_dtm1m_polygon_sample_rows_written=3, os_terrain50_crosscheck_rows_written=3, port_8012_acceptance_rows_written=1)


def main() -> int:
    cases = [
        run_case("stale_external_runner", lambda *args: None, False, "BLOCKED", "BLOCKED_EXTERNAL_RUNNER_HOST_RECOVERY_REQUIRED"),
        run_case("predecessor_complete", complete, False, "PASS", "READY_FOR_SHARED_RUNNER_PICKUP"),
        run_case("runner_output_present", lambda q, s, h, o, p: s["task"].__setitem__("runner_output_observed", True), True, "PASS", "RUNNER_OUTPUT_ALREADY_PRESENT_REVALIDATE"),
        run_case("wrong_slot", lambda q, s, h, o, p: q.__setitem__("slot_id", "future_growth_2"), False, "BLOCKED", "BLOCKED_STALL_DIAGNOSTIC_CONTRACT"),
        run_case("wrong_task", lambda q, s, h, o, p: q.__setitem__("task_id", "wrong"), False, "BLOCKED", "BLOCKED_STALL_DIAGNOSTIC_CONTRACT"),
        run_case("wrong_attempt", lambda q, s, h, o, p: q.__setitem__("attempt_id", "wrong"), False, "BLOCKED", "BLOCKED_STALL_DIAGNOSTIC_CONTRACT"),
        run_case("wrong_revision", lambda q, s, h, o, p: q.__setitem__("contract_revision", 7), False, "BLOCKED", "BLOCKED_STALL_DIAGNOSTIC_CONTRACT"),
        run_case("not_claimable", lambda q, s, h, o, p: q.__setitem__("claimable", False), False, "BLOCKED", "BLOCKED_STALL_DIAGNOSTIC_CONTRACT"),
        run_case("parallel_runner", lambda q, s, h, o, p: q.__setitem__("parallel_runner", True), False, "BLOCKED", "BLOCKED_STALL_DIAGNOSTIC_CONTRACT"),
        run_case("heartbeat_claims_runner", lambda q, s, h, o, p: h.__setitem__("heartbeat_kind", "RUNNER_EXECUTION"), False, "BLOCKED", "BLOCKED_STALL_DIAGNOSTIC_CONTRACT"),
        run_case("owner_mismatch", lambda q, s, h, o, p: o.__setitem__("owner_page_session_id", "other"), False, "BLOCKED", "BLOCKED_STALL_DIAGNOSTIC_CONTRACT"),
        run_case("unsafe_truth", lambda q, s, h, o, p: q.__setitem__("production_deploy", True), False, "BLOCKED", "BLOCKED_STALL_DIAGNOSTIC_CONTRACT"),
    ]
    passed = sum(case["pass"] for case in cases)
    output = {"schema_version": 1, "slot_id": mod.SLOT_ID, "selftest_kind": "REVISION8_LONG_PENDING_STALL_DIAGNOSTIC", "result": f"{passed}/{len(cases)} PASS", "passed": passed, "total": len(cases), "cases": cases, "runner_execution_claimed": False, "business_progress_claimed": False, "final_ready": False}
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if passed == len(cases) else 2


if __name__ == "__main__":
    raise SystemExit(main())

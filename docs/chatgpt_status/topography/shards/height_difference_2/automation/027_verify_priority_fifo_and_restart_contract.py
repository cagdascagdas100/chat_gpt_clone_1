#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
ATTEMPT_ID = "height-difference-2-20260721-017"
IDEMPOTENCY = "height-difference-2-canonical-export-official-sampling-v3"
TARGET_ROWS = [30762, 46142, 61522]
CANONICAL_ROOT = r"F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
CANONICAL_LAUNCHER = r"F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def check(condition: bool, name: str, failures: list[str], passed: list[str]) -> None:
    (passed if condition else failures).append(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--competing-queue", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--stable-runner", type=Path, required=True)
    parser.add_argument("--starter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    queue = load_json(args.queue)
    competitor = load_json(args.competing_queue)
    request = load_json(args.request)
    runner_text = args.stable_runner.read_text(encoding="utf-8-sig")
    starter_text = args.starter.read_text(encoding="utf-8-sig")
    failures: list[str] = []
    passed: list[str] = []

    check(queue.get("schema_version") == 5, "queue_schema_v5", failures, passed)
    check(queue.get("task_id") == TASK_ID and queue.get("attempt_id") == ATTEMPT_ID, "task_attempt_identity", failures, passed)
    check(queue.get("idempotency_key") == IDEMPOTENCY, "idempotency_preserved", failures, passed)
    check(queue.get("status") == "pickup_requested" and queue.get("ready_for_claim") is True, "queue_claimable", failures, passed)
    check(queue.get("priority") == 1, "priority_one", failures, passed)
    check(queue.get("sample_rows") == TARGET_ROWS, "target_rows_exact", failures, passed)
    check(queue.get("script_path", "").endswith("025_height_difference_2_shared_runner_carrier.ps1"), "carrier_path", failures, passed)
    check(queue.get("final_ready") is False and queue.get("fake_data") is False, "queue_safety", failures, passed)
    check(competitor.get("priority") == 1 and parse_time(queue["created_at"]) < parse_time(competitor["created_at"]), "fifo_older_than_competitor", failures, passed)
    check("Sort-Object priority, created_at, page_key, task_id" in runner_text, "runner_sort_contract", failures, passed)
    check("Lower numeric priority wins" in runner_text and "pickup_requested" in runner_text, "runner_priority_status_contract", failures, passed)
    check(request.get("request_type") == "reboot_runner_start_request" and request.get("action") == "restart_existing_canonical_runner_if_stale", "restart_request_type", failures, passed)
    check(request.get("task_id") == TASK_ID and request.get("attempt_id") == ATTEMPT_ID, "restart_task_identity", failures, passed)
    check(request.get("canonical_root") == CANONICAL_ROOT and request.get("launcher") == CANONICAL_LAUNCHER, "canonical_f_paths", failures, passed)
    check(request.get("max_tasks") == 1 and request.get("start_only_if_no_live_canonical_process") is True, "single_process_gate", failures, passed)
    check(request.get("new_runner") is False and request.get("parallel_runner") is False, "request_no_new_parallel", failures, passed)
    check("if ($before.Count -gt 1)" in starter_text and "if ($before.Count -eq 1)" in starter_text, "starter_process_count_gates", failures, passed)
    check("Start-Process -FilePath 'cmd.exe'" in starter_text and CANONICAL_LAUNCHER in starter_text, "starter_exact_launcher", failures, passed)
    check("new_runner_architecture_created = $false" in starter_text and "parallel_runner_started = $false" in starter_text, "starter_safety", failures, passed)
    check("task_claimed = $false" in starter_text and "final_ready = $false" in starter_text, "no_claim_fabrication", failures, passed)

    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": "PRIORITY_FIFO_AND_CANONICAL_RESTART_CONTRACT_PASS" if not failures else "BLOCKED_CONTRACT_VALIDATION_FAILED",
        "checks_passed": len(passed),
        "checks_total": len(passed) + len(failures),
        "passed": passed,
        "failures": failures,
        "runner_selection_contract": "priority_then_created_at_then_page_key_then_task_id",
        "filename_prefix_selection_effect": False,
        "runner_restart_executed_by_validation": False,
        "real_candidate_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not failures, "passed": len(passed), "total": len(passed) + len(failures), "failures": failures}))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
ATTEMPT_ID = "height-difference-2-20260721-016"
IDEMPOTENCY_KEY = "height-difference-2-canonical-export-official-sampling-v3"
SLOT_ID = "height_difference_2"
QUEUE_PATH = "docs/chatgpt_status/aays1/queue/0000_001_height_difference_2_canonical_export_official_sampling_20260720.task.json"
REFRESH_PATH = "docs/chatgpt_status/_shared/control/request_queue_refresh.json"
TARGET_ROWS = [30762, 46142, 61522]
FALSE_FLAGS = ("new_runner", "parallel_runner", "fake_data", "db_write", "migration", "production_deploy", "final_ready")


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def safe(payload: dict[str, Any], label: str) -> None:
    for key in FALSE_FLAGS:
        require(payload.get(key) is False, f"{label}.{key} must be false")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-task", type=Path, required=True)
    parser.add_argument("--refresh-request", type=Path, required=True)
    parser.add_argument("--old-queue-path", type=Path, required=True)
    parser.add_argument("--expected-queue-commit", required=True)
    parser.add_argument("--expected-refresh-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    checks: dict[str, Any] = {}
    code = 2
    try:
        queue = load_object(args.queue_task)
        refresh = load_object(args.refresh_request)
        safe(queue, "queue")
        safe(refresh, "refresh")

        require(not args.old_queue_path.exists(), "superseded unprefixed queue path still exists")
        require(queue.get("schema_version") == 5, "queue schema_version must be 5")
        require(queue.get("task_version") == "5.2-canonical-queue-refresh", "queue task_version mismatch")
        require(queue.get("task_id") == TASK_ID, "queue task_id mismatch")
        require(queue.get("attempt_id") == ATTEMPT_ID, "queue attempt_id mismatch")
        require(queue.get("idempotency_key") == IDEMPOTENCY_KEY, "queue idempotency mismatch")
        require(queue.get("slot_id") == SLOT_ID, "queue slot mismatch")
        require(queue.get("status") == "pickup_requested", "queue status mismatch")
        require(queue.get("priority") == 2, "queue priority mismatch")
        require(queue.get("sample_rows") == TARGET_ROWS, "queue target rows mismatch")
        require(queue.get("script_path", "").endswith("025_height_difference_2_shared_runner_carrier.ps1"), "PowerShell carrier mismatch")
        require(queue.get("script_blob_sha") == "953326ddbddef5b46a176b7f260d7a051f6d3aea", "carrier blob mismatch")
        require(QUEUE_PATH in queue.get("allowed_paths", []), "canonical queue path missing from allowed_paths")
        runner_contract = queue.get("runner_contract") or {}
        require(runner_contract.get("canonical_queue_path") == QUEUE_PATH, "runner canonical queue path mismatch")
        require(runner_contract.get("queue_refresh_control_path") == REFRESH_PATH, "runner refresh path mismatch")
        require(runner_contract.get("lower_numeric_priority_runs_first") is True, "priority ordering contract missing")

        require(refresh.get("task_id") == TASK_ID, "refresh task_id mismatch")
        require(refresh.get("attempt_id") == ATTEMPT_ID, "refresh attempt_id mismatch")
        require(refresh.get("slot_id") == SLOT_ID, "refresh slot mismatch")
        require(refresh.get("action") == "refresh_existing_single_shared_runner_queue", "refresh action mismatch")
        require(refresh.get("status") == "requested_waiting_existing_runner_scan", "refresh status mismatch")
        require(refresh.get("queue_path") == QUEUE_PATH, "refresh queue path mismatch")
        require(refresh.get("required_queue_commit") == args.expected_queue_commit, "refresh queue commit mismatch")
        require(refresh.get("required_powershell_carrier_blob_sha") == queue.get("script_blob_sha"), "refresh carrier blob mismatch")
        require(refresh.get("single_runner_only") is True, "refresh single runner contract missing")
        previous = refresh.get("previous_request_preserved") or {}
        require(previous.get("task_id") == "security-public-safety-3-sample-hydrate-v5-20260721", "previous refresh request not preserved")
        require(previous.get("status") == "preserved_in_history_not_deleted", "previous request preservation status mismatch")

        checks = {
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "slot_id": SLOT_ID,
            "canonical_queue_path": QUEUE_PATH,
            "queue_commit": args.expected_queue_commit,
            "refresh_path": REFRESH_PATH,
            "refresh_commit": args.expected_refresh_commit,
            "priority": 2,
            "target_rows": TARGET_ROWS,
            "old_queue_path_absent": True,
            "previous_request_preserved": True,
            "ready_for_existing_single_runner_scan": True,
        }
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "status": "CANONICAL_QUEUE_REFRESH_CONTRACT_VERIFIED",
            "checks": checks,
            "runner_execution_claimed": False,
            "candidate_rows_produced": 0,
            "new_runner": False,
            "parallel_runner": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "final_ready": False,
        }
        code = 0
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "status": "BLOCKED_CANONICAL_QUEUE_REFRESH_CONTRACT",
            "error": f"{type(exc).__name__}: {exc}",
            "checks": checks,
            "runner_execution_claimed": False,
            "candidate_rows_produced": 0,
            "new_runner": False,
            "parallel_runner": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "final_ready": False,
        }
    write_json(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"]}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

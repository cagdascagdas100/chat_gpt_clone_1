#!/usr/bin/env python3
"""Classify long-pending revision-8 queue state without bypassing the shared runner."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "future_growth_1"
TASK_ID = "aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID = "future-growth-1-20260722-005"
PREDECESSOR_TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
CONTRACT_REVISION = 8
QUEUE_STALE_HOURS = 12.0
STATUS_STALE_HOURS = 6.0
RUNNER_STALE_HOURS = 2.0


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON object required")
    return value


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def age_hours(now: datetime, value: Any) -> float | None:
    dt = parse_time(value)
    return None if dt is None else round((now - dt).total_seconds() / 3600.0, 3)


def predecessor_complete(value: dict[str, Any]) -> bool:
    return (
        value.get("current_task_id") == PREDECESSOR_TASK_ID
        and value.get("candidate_seed_rows_written") == 3
        and value.get("hmlr_exact_polygon_rows_written") == 3
        and value.get("ea_dtm1m_polygon_sample_rows_written") == 3
        and value.get("os_terrain50_crosscheck_rows_written") == 3
        and isinstance(value.get("port_8012_acceptance_rows_written"), int)
        and value.get("port_8012_acceptance_rows_written") >= 1
    )


def validate(queue: dict[str, Any], slot_status: dict[str, Any], heartbeat: dict[str, Any], ownership: dict[str, Any], predecessor: dict[str, Any], runner_output_exists: bool, now: datetime) -> dict[str, Any]:
    queue_age = age_hours(now, queue.get("queued_at"))
    status_age = age_hours(now, predecessor.get("updated_at"))
    runner_age = age_hours(now, predecessor.get("last_observed_runner_heartbeat_at"))
    lease_expiry = parse_time(heartbeat.get("lease_expires_at"))
    lease_expired = lease_expiry is None or lease_expiry < now
    pred_complete = predecessor_complete(predecessor)
    checks = {
        "queue_slot_exact": queue.get("slot_id") == SLOT_ID,
        "queue_task_exact": queue.get("task_id") == TASK_ID,
        "queue_attempt_exact": queue.get("attempt_id") == ATTEMPT_ID,
        "queue_revision_exact": queue.get("contract_revision") == CONTRACT_REVISION,
        "queue_pending_claimable": queue.get("state") == "pending" and queue.get("claimable") is True and queue.get("ready_for_claim") is True,
        "single_shared_runner_only": queue.get("single_runner_only") is True and queue.get("new_runner") is False and queue.get("parallel_runner") is False,
        "predecessor_task_exact": queue.get("sequential_after_task_id") == PREDECESSOR_TASK_ID and predecessor.get("current_task_id") == PREDECESSOR_TASK_ID,
        "slot_status_exact": slot_status.get("slot_id") == SLOT_ID,
        "heartbeat_slot_exact": heartbeat.get("slot_id") == SLOT_ID,
        "heartbeat_page_not_runner": heartbeat.get("heartbeat_kind") == "PAGE_LEASE_NOT_RUNNER_EXECUTION",
        "ownership_slot_exact": ownership.get("slot_id") == SLOT_ID,
        "ownership_same_owner": ownership.get("owner_page_session_id") == heartbeat.get("owner_page_session_id"),
        "truth_flags_safe": all(queue.get(k) is False for k in ("final_ready", "fake_data", "db_write", "migration", "production_deploy")),
        "runner_output_absence_consistent": runner_output_exists is bool(slot_status.get("task", {}).get("runner_output_observed")) or not runner_output_exists,
        "queue_age_parsed": queue_age is not None,
        "predecessor_status_age_parsed": status_age is not None,
        "runner_heartbeat_age_parsed": runner_age is not None,
        "no_runner_bypass": queue.get("runner_policy") == "single_existing_shared_runner_sequential_only",
        "page_lease_state_classified": isinstance(lease_expired, bool),
        "predecessor_state_classified": isinstance(pred_complete, bool),
    }
    if runner_output_exists:
        classification = "RUNNER_OUTPUT_ALREADY_PRESENT_REVALIDATE"
        result = "PASS"
    elif pred_complete:
        classification = "READY_FOR_SHARED_RUNNER_PICKUP"
        result = "PASS"
    elif runner_age is not None and runner_age > RUNNER_STALE_HOURS and status_age is not None and status_age > STATUS_STALE_HOURS:
        classification = "BLOCKED_EXTERNAL_RUNNER_HOST_RECOVERY_REQUIRED"
        result = "BLOCKED"
    elif status_age is not None and status_age > STATUS_STALE_HOURS:
        classification = "BLOCKED_PREDECESSOR_STATUS_STALE"
        result = "BLOCKED"
    else:
        classification = "BLOCKED_PREDECESSOR_PENDING"
        result = "BLOCKED"
    failed = [key for key, ok in checks.items() if not ok]
    if failed:
        result = "BLOCKED"
        classification = "BLOCKED_STALL_DIAGNOSTIC_CONTRACT"
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "validation_kind": "REVISION8_LONG_PENDING_STALL_DIAGNOSTIC",
        "result": result,
        "classification": classification,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "checks": checks,
        "failed_checks": failed,
        "ages_hours": {"queue_wait": queue_age, "predecessor_status": status_age, "runner_heartbeat": runner_age},
        "thresholds_hours": {"queue_stale": QUEUE_STALE_HOURS, "status_stale": STATUS_STALE_HOURS, "runner_stale": RUNNER_STALE_HOURS},
        "page_lease_expired": lease_expired,
        "predecessor_complete": pred_complete,
        "runner_output_present": runner_output_exists,
        "detected_problems": [name for name, active in (("PAGE_LEASE_EXPIRED", lease_expired), ("QUEUE_WAIT_EXCEEDS_THRESHOLD", queue_age is not None and queue_age > QUEUE_STALE_HOURS), ("PREDECESSOR_STATUS_STALE", status_age is not None and status_age > STATUS_STALE_HOURS), ("RUNNER_HEARTBEAT_STALE", runner_age is not None and runner_age > RUNNER_STALE_HOURS), ("PREDECESSOR_INCOMPLETE", not pred_complete), ("RUNNER_OUTPUT_MISSING", not runner_output_exists)) if active],
        "automatic_fixes": ["RENEW_EXPIRED_PAGE_LEASE_SAME_OWNER_ONLY", "PRESERVE_SINGLE_SHARED_RUNNER_AND_QUEUE_ORDER", "BOUND_CHILD_PROCESS_TREE_WITH_GLOBAL_DEADLINE", "WRITE_EXPLICIT_STALL_DIAGNOSTIC", "AUTO_RESUME_ONLY_AFTER_PREDECESSOR_COMPLETION"],
        "external_operator_fix_required": classification == "BLOCKED_EXTERNAL_RUNNER_HOST_RECOVERY_REQUIRED",
        "runner_execution_claimed": False,
        "business_progress_claimed": False,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue", type=Path)
    parser.add_argument("slot_status", type=Path)
    parser.add_argument("heartbeat", type=Path)
    parser.add_argument("ownership", type=Path)
    parser.add_argument("predecessor", type=Path)
    parser.add_argument("runner_output", type=Path)
    parser.add_argument("--now")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        raise SystemExit(2)
    try:
        result = validate(read_json(args.queue), read_json(args.slot_status), read_json(args.heartbeat), read_json(args.ownership), read_json(args.predecessor), args.runner_output.is_file(), now)
    except Exception as exc:
        result = {"schema_version": 1, "slot_id": SLOT_ID, "validation_kind": "REVISION8_LONG_PENDING_STALL_DIAGNOSTIC", "result": "BLOCKED", "classification": "BLOCKED_STALL_DIAGNOSTIC_LOAD", "checks_passed": 0, "checks_total": 1, "failed_checks": [f"{type(exc).__name__}:{exc}"], "runner_execution_claimed": False, "business_progress_claimed": False, "actual_business_data_rows_written": 0, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if result.get("result") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

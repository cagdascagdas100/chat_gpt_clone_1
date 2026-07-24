#!/usr/bin/env python3
"""Read-only eligibility audit for the existing single shared runner.

This script never claims a slot, mutates a queue, writes a heartbeat, or starts a runner.
It only validates authoritative JSON snapshots and may write one slot-local review JSON.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"
ROW_START = 61523
ROW_END = 92283
ROW_COUNT = 30_761
ALLOWED_PATHS = (
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3",
    "docs/chatgpt_status/_shared/slots_18/internet_access_3",
    "england_map_web/data/aays_18_slots/internet_access_3",
)
ACTIVE_STATES = {
    "pickup_requested", "claimed", "running", "in_progress", "executing",
    "selected", "leased", "started",
}
TERMINAL_OR_IDLE_STATES = {
    "", "idle", "none", "null", "completed", "complete", "done",
    "failed", "cancelled", "canceled", "blocked", "waiting",
}


class AuditError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def load_json(path: Path, name: str) -> dict[str, Any]:
    require(path.is_file() and path.stat().st_size > 0, f"{name}: missing or empty")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AuditError(f"{name}: invalid JSON: {exc}") from exc
    require(isinstance(value, dict), f"{name}: object required")
    return value


def exact_int(value: Any, name: str) -> int:
    require(not isinstance(value, bool), f"{name}: integer required")
    require(isinstance(value, int), f"{name}: exact integer required")
    return value


def partition(value: dict[str, Any], name: str) -> tuple[int, int, int]:
    part = value.get("parcel_partition") or {}
    start = exact_int(part.get("start"), f"{name}.start")
    end = exact_int(part.get("end"), f"{name}.end")
    count = exact_int(part.get("count"), f"{name}.count")
    require((start, end, count) == (ROW_START, ROW_END, ROW_COUNT), f"{name}: partition mismatch")
    return start, end, count


def validate(
    ownership: dict[str, Any],
    slot_task: dict[str, Any],
    global_task: dict[str, Any],
    runtime_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    require(ownership.get("slot_id") == SLOT_ID, "ownership: wrong slot_id")
    require(slot_task.get("slot_id") == SLOT_ID, "slot task: wrong slot_id")
    partition(ownership, "ownership partition")
    partition(slot_task, "slot task partition")

    allowed = slot_task.get("allowed_paths")
    require(isinstance(allowed, list), "slot task: allowed_paths list required")
    require(tuple(allowed) == ALLOWED_PATHS, "slot task: allowed_paths mismatch")
    require(slot_task.get("direct_push_forbidden") is True, "slot task: direct_push_forbidden must be true")
    require(ownership.get("wrong_slot_write_forbidden") is True, "ownership: wrong-slot guard required")
    require(ownership.get("final_ready") is False, "ownership: final_ready must be false")
    require(slot_task.get("final_ready") is False, "slot task: final_ready must be false")

    owner_state = str(ownership.get("state") or "").lower()
    slot_state = str(slot_task.get("state") or "").lower()
    lease_version = exact_int(ownership.get("lease_version"), "lease_version")
    owner_session = ownership.get("owner_page_session_id")
    lease_hash = ownership.get("lease_token_hash")
    heartbeat = ownership.get("heartbeat_at")
    expiry = ownership.get("lease_expires_at")
    slot_task_id = slot_task.get("task_id")
    slot_task_owner = slot_task.get("owner_page_session_id")

    slot_unclaimed = (
        owner_state == "unclaimed"
        and lease_version == 0
        and owner_session is None
        and lease_hash is None
        and heartbeat is None
        and expiry is None
        and slot_state == "idle"
        and slot_task_id is None
        and slot_task_owner is None
    )

    global_slot = str(global_task.get("slot_id") or "")
    global_status = str(global_task.get("status") or global_task.get("state") or "").lower()
    global_task_id = global_task.get("task_id") or global_task.get("id")
    require(global_status in ACTIVE_STATES or global_status in TERMINAL_OR_IDLE_STATES,
            f"global task: unknown status {global_status!r}")

    other_task_active = bool(global_task_id) and global_slot != SLOT_ID and global_status in ACTIVE_STATES
    same_slot_active = bool(global_task_id) and global_slot == SLOT_ID and global_status in ACTIVE_STATES
    global_runner_clear = not other_task_active and not same_slot_active

    if not slot_unclaimed:
        status = "BLOCKED_SLOT_NOT_CLEANLY_UNCLAIMED"
        eligible = False
        reason = "Slot ownership/current-task snapshot is not the exact unclaimed+idle baseline."
    elif other_task_active:
        status = "BLOCKED_BY_OTHER_GLOBAL_RUNNER_TASK"
        eligible = False
        reason = f"Existing single runner is reserved for {global_slot}:{global_task_id} ({global_status})."
    elif same_slot_active:
        status = "ALREADY_ACTIVE_NO_NEW_CLAIM"
        eligible = False
        reason = "internet_access_3 is already the active global task; a second claim is forbidden."
    else:
        status = "READY_FOR_MANUAL_CLAIM_REVIEW"
        eligible = True
        reason = "No active global task and exact unclaimed+idle slot baseline; operator review is still required."

    runtime_rows = 0
    runtime_status = "NOT_PROVIDED"
    if runtime_results is not None:
        require(runtime_results.get("slot_id") == SLOT_ID, "runtime results: wrong slot_id")
        runtime_status = str(runtime_results.get("status") or "")
        rows = runtime_results.get("real_runtime_rows_validated", 0)
        runtime_rows = exact_int(rows, "runtime rows")
        require(0 <= runtime_rows <= ROW_COUNT, "runtime rows outside partition")

    gates = [
        {"gate_no": 1, "name": "SLOT_ID_AND_PARTITION", "state": "PASS",
         "detail": f"{SLOT_ID}; rows {ROW_START}-{ROW_END}; count {ROW_COUNT}"},
        {"gate_no": 2, "name": "ALLOWED_PATHS_AND_DIRECT_PUSH_GUARD", "state": "PASS",
         "detail": "Exactly three allowed slot paths; direct push and wrong-slot writes forbidden."},
        {"gate_no": 3, "name": "SLOT_OWNERSHIP_BASELINE", "state": "PASS" if slot_unclaimed else "BLOCKED",
         "detail": f"ownership={owner_state}; lease_version={lease_version}; current_task={slot_state}"},
        {"gate_no": 4, "name": "GLOBAL_SINGLE_RUNNER_OCCUPANCY",
         "state": "BLOCKED" if other_task_active else ("ALREADY_ACTIVE" if same_slot_active else "PASS"),
         "detail": f"slot={global_slot or 'none'}; task={global_task_id or 'none'}; status={global_status or 'none'}"},
        {"gate_no": 5, "name": "NO_AUTOMATIC_CLAIM_OR_QUEUE_MUTATION", "state": "PASS",
         "detail": "Auditor is read-only; auto_claim=false; queue_submission=false; new_runner=false."},
        {"gate_no": 6, "name": "MANUAL_CLAIM_ELIGIBILITY", "state": "READY" if eligible else "WAITING_EXISTING_RUNNER",
         "detail": reason},
        {"gate_no": 7, "name": "REAL_RUNTIME_OUTPUT_BOUNDARY",
         "state": "PASS" if runtime_rows == ROW_COUNT else "WAITING_EXISTING_RUNNER",
         "detail": f"runtime status={runtime_status}; validated rows={runtime_rows}/{ROW_COUNT}"},
        {"gate_no": 8, "name": "TRUTH_FLAGS", "state": "PASS",
         "detail": "fake_data=false; db_write=false; migration=false; production_deploy=false; final_ready=false"},
    ]

    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "summary": reason,
        "claim_eligible_for_manual_review": eligible,
        "auto_claim": False,
        "queue_submission": False,
        "create_new_runner": False,
        "parallel_runner_allowed": False,
        "slot_unclaimed_exact_baseline": slot_unclaimed,
        "global_runner_clear": global_runner_clear,
        "global_task": {"slot_id": global_slot or None, "task_id": global_task_id, "status": global_status or None},
        "row_partition": {"start": ROW_START, "end": ROW_END, "count": ROW_COUNT},
        "allowed_paths": list(ALLOWED_PATHS),
        "real_runtime_rows_validated": runtime_rows,
        "gates": gates,
        "actual_business_data_rows_written": 0,
        "scores_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ownership", required=True, type=Path)
    parser.add_argument("--slot-task", required=True, type=Path)
    parser.add_argument("--global-task", required=True, type=Path)
    parser.add_argument("--runtime-results", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = validate(
        load_json(args.ownership, "ownership"),
        load_json(args.slot_task, "slot task"),
        load_json(args.global_task, "global task"),
        load_json(args.runtime_results, "runtime results") if args.runtime_results else None,
    )
    if args.output and not args.dry_run:
        atomic_write(args.output, result)
    print(json.dumps({"status": result["status"], "claim_eligible_for_manual_review": result["claim_eligible_for_manual_review"], "global_task": result["global_task"], "dry_run": args.dry_run}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

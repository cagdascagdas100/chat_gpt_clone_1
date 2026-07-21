#!/usr/bin/env python3
"""Fail-closed control-plane readiness audit for the existing shared runner.

The audit accepts either a coherent pre-claim state or a coherent claimed/running
state for the existing task. It never creates or changes a claim, queue item,
lease, owner, heartbeat, task, or runner.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_3"
PARTITION = {"start": 61523, "end": 92283, "count": 30761, "canonical_count": 92283}
EXPECTED_PATHS = {
    "docs/chatgpt_status/topography/shards/height_difference_3",
    "docs/chatgpt_status/_shared/slots_21/height_difference_3",
    "england_map_web/data/aays_18_slots/height_difference_3",
}
EXPECTED_COMMANDS = {
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/032_run_full_pipeline_and_website_acceptance.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/037_audit_control_then_run_full_pipeline.py",
}
SAFETY_KEYS = ("final_ready", "product_final_ready", "fake_data", "db_write", "migration", "production_deploy")
ACTIVE_STATES = {"claimed", "running", "executing", "active", "busy", "in_progress"}
RUNTIME_ACTIVE_PREFIXES = (
    "BLOCKED_", "RUNNING_", "IN_PROGRESS_", "RESUMABLE_", "FAILED_",
    "THREE_REAL_", "CONTROL_PLANE_", "PREFLIGHT_", "PIPELINE_", "WEBSITE_",
)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def require_identity(label: str, value: dict[str, Any]) -> None:
    if value.get("slot_id") != SLOT_ID:
        raise ValueError(f"{label} slot mismatch")
    partition = value.get("parcel_partition")
    if not isinstance(partition, dict):
        raise ValueError(f"{label} parcel partition missing")
    for key, expected in PARTITION.items():
        if int(partition.get(key, -1)) != expected:
            raise ValueError(f"{label} partition {key} mismatch")


def require_safety(label: str, value: dict[str, Any]) -> None:
    for key in SAFETY_KEYS:
        if value.get(key) not in (False, None):
            raise ValueError(f"{label} unsafe flag {key}={value.get(key)!r}")


def coherent_control_mode(current: dict[str, Any], heartbeat: dict[str, Any], task_id: str) -> str:
    current_state = str(current.get("state", "")).strip().casefold()
    heartbeat_state = str(heartbeat.get("state", "")).strip().casefold()
    if (
        current_state == "idle"
        and current.get("task_id") is None
        and current.get("owner_page_session_id") is None
        and heartbeat_state == "unclaimed"
        and heartbeat.get("current_task_id") is None
        and heartbeat.get("owner_page_session_id") is None
        and heartbeat.get("stale") is True
    ):
        return "PRECLAIM_IDLE_UNCLAIMED"

    current_task_id = current.get("task_id")
    heartbeat_task_id = heartbeat.get("current_task_id")
    current_owner = current.get("owner_page_session_id")
    heartbeat_owner = heartbeat.get("owner_page_session_id")
    if (
        current_state in ACTIVE_STATES
        and heartbeat_state in ACTIVE_STATES
        and current_task_id == task_id
        and heartbeat_task_id == task_id
        and isinstance(current_owner, str)
        and bool(current_owner.strip())
        and heartbeat_owner == current_owner
        and heartbeat.get("stale") is False
        and isinstance(heartbeat.get("heartbeat_at"), str)
        and bool(heartbeat.get("heartbeat_at").strip())
    ):
        return "CLAIMED_RUNNING_COHERENT"

    raise ValueError(
        "control-plane state is neither coherent preclaim nor coherent claimed execution: "
        f"current={current_state!r}/{current_task_id!r}, heartbeat={heartbeat_state!r}/{heartbeat_task_id!r}"
    )


def validate_runtime(runtime: dict[str, Any]) -> str:
    status = str(runtime.get("status", ""))
    counts = runtime.get("real_counts")
    if not isinstance(counts, dict) or not counts:
        raise ValueError("runtime real_counts missing")
    normalized_counts: dict[str, int] = {}
    for key, value in counts.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"runtime count {key} invalid: {value!r}")
        normalized_counts[str(key)] = value

    operations = runtime.get("operations")
    operation_count = runtime.get("operation_count")
    if not isinstance(operations, list) or isinstance(operation_count, bool) or not isinstance(operation_count, int):
        raise ValueError("runtime operations/operation_count invalid")
    if operation_count != len(operations):
        raise ValueError("runtime operation_count differs from operations length")

    if status.startswith("NOT_STARTED"):
        if operations or any(normalized_counts.values()):
            raise ValueError("NOT_STARTED runtime must have zero counts and no operations")
        return "NOT_STARTED_ZERO"

    if not status.startswith(RUNTIME_ACTIVE_PREFIXES):
        raise ValueError(f"unsupported resumable runtime status: {status!r}")

    numbers: list[int] = []
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            raise ValueError(f"runtime operation {index} is not an object")
        number = operation.get("operation_no")
        if isinstance(number, bool) or not isinstance(number, int):
            raise ValueError(f"runtime operation {index} has invalid operation_no")
        numbers.append(number)
    if len(numbers) != len(set(numbers)):
        raise ValueError("runtime operation numbers are duplicated")
    if numbers and numbers != list(range(numbers[0], numbers[0] + len(numbers))):
        raise ValueError("runtime operation numbers are not contiguous and ordered")
    return "RESUMABLE_RUNTIME_VALID"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot-root", required=True, type=Path)
    parser.add_argument("--task-contract", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    slot_root = args.slot_root.resolve()
    current = load(slot_root / "current_task_latest.json")
    heartbeat = load(slot_root / "heartbeat_latest.json")
    checkpoint = load(slot_root / "checkpoint_latest.json")
    status = load(slot_root / "status_latest.json")
    task = load(args.task_contract.resolve())
    runtime = load(args.runtime.resolve())

    values = {
        "current_task": current,
        "heartbeat": heartbeat,
        "checkpoint": checkpoint,
        "status": status,
        "task_contract": task,
        "runtime": runtime,
    }
    for label, value in values.items():
        require_identity(label, value)
        require_safety(label, value)

    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, detail: str) -> None:
        if not condition:
            raise ValueError(f"{name}: {detail}")
        checks.append({"name": name, "status": "PASS", "detail": detail})

    allowed = current.get("allowed_paths")
    check("allowed_paths_exact", isinstance(allowed, list) and set(map(str, allowed)) == EXPECTED_PATHS, "allowed paths use slots_21 and canonical shard/web roots")
    migration = current.get("control_plane_path_migration")
    check("slots_21_migration_recorded", isinstance(migration, dict) and migration.get("to") in EXPECTED_PATHS and migration.get("claim_created") is False, "slots_18 to slots_21 migration is recorded without a synthetic claim")

    sequence = int(checkpoint.get("sequence", -1))
    check("checkpoint_status_sequence", sequence >= 0 and int(status.get("checkpoint_sequence", -2)) == sequence, "checkpoint and status sequences match")
    check("first_step_consistent", checkpoint.get("first_unverified_step") == status.get("first_unverified_step"), "checkpoint and status first step match")

    runner_policy = task.get("runner_policy")
    check("existing_runner_only", isinstance(runner_policy, dict) and runner_policy.get("existing_shared_runner_only") is True, "task is restricted to the existing shared runner")
    check("no_queue_lease_runner", isinstance(runner_policy, dict) and all(runner_policy.get(key) is False for key in ("new_runner", "parallel_runner", "queue_submission", "lease_creation")), "task creates no queue, lease, new runner, or parallel runner")

    command = task.get("command")
    check("task_command_present", isinstance(command, list) and len(command) >= 2 and command[0] == "python", "task command is explicit")
    check("task_bootstrap_known", isinstance(command, list) and any(path in command for path in EXPECTED_COMMANDS), "task command invokes an approved audited full-pipeline entrypoint")
    check("task_final_false", task.get("final_ready") is False, "task final_ready remains false")

    task_id = str(task.get("task_id", "")).strip()
    check("task_id_present", bool(task_id), "task contract has a stable task id")
    control_mode = coherent_control_mode(current, heartbeat, task_id)
    check("control_mode_coherent", True, control_mode)

    runtime_mode = validate_runtime(runtime)
    check("runtime_coherent", True, runtime_mode)

    report = {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "parcel_partition": PARTITION,
        "updated_at": now(),
        "status": "CONTROL_PLANE_READY_FOR_EXISTING_RUNNER",
        "control_mode": control_mode,
        "runtime_mode": runtime_mode,
        "check_count": len(checks),
        "checks": checks,
        "checkpoint_sequence": sequence,
        "task_id": task_id,
        "task_contract": str(args.task_contract.resolve()),
        "runtime": str(args.runtime.resolve()),
        "claim_created": False,
        "task_assigned_by_audit": False,
        "owner_assigned_by_audit": False,
        "queue_submission": False,
        "lease_creation": False,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "single_shared_runner_only": True,
        "next_required_step": status.get("first_unverified_step"),
        "blocker": None if control_mode == "CLAIMED_RUNNING_COHERENT" else "EXISTING_F_RUNNER_HAS_NOT_CLAIMED_OR_EXECUTED_THE_COMMITTED_TASK",
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    atomic_json(args.output.resolve(), report)
    print(json.dumps({"ok": True, "status": report["status"], "mode": control_mode, "checks": len(checks), "output": str(args.output.resolve())}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

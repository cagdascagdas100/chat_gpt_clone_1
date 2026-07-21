#!/usr/bin/env python3
"""Fail-closed control-plane readiness audit for the existing shared runner.

This script never creates a claim, queue item, lease, owner, heartbeat, task, or
runner. It only verifies that the existing height_difference_3 control files and
the already-committed task contract agree before official-source work begins.
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

    check("current_task_idle", current.get("state") == "idle", "current task is idle")
    check("current_task_unassigned", current.get("task_id") is None and current.get("owner_page_session_id") is None, "no task or owner is assigned")
    allowed = current.get("allowed_paths")
    check("allowed_paths_exact", isinstance(allowed, list) and set(map(str, allowed)) == EXPECTED_PATHS, "allowed paths use slots_21 and canonical shard/web roots")
    migration = current.get("control_plane_path_migration")
    check("slots_21_migration_recorded", isinstance(migration, dict) and migration.get("to") in EXPECTED_PATHS and migration.get("claim_created") is False, "slots_18 to slots_21 migration is recorded without a claim")

    check("heartbeat_unclaimed", heartbeat.get("state") == "unclaimed", "heartbeat remains unclaimed")
    check("heartbeat_stale", heartbeat.get("stale") is True and heartbeat.get("current_task_id") is None, "no live task heartbeat exists")
    check("heartbeat_unowned", heartbeat.get("owner_page_session_id") is None, "heartbeat owner remains null")

    sequence = int(checkpoint.get("sequence", -1))
    check("checkpoint_status_sequence", sequence >= 0 and int(status.get("checkpoint_sequence", -2)) == sequence, "checkpoint and status sequences match")
    check("first_step_consistent", checkpoint.get("first_unverified_step") == status.get("first_unverified_step"), "checkpoint and status first step match")

    runner_policy = task.get("runner_policy")
    check("existing_runner_only", isinstance(runner_policy, dict) and runner_policy.get("existing_shared_runner_only") is True, "task is restricted to the existing shared runner")
    check("no_queue_lease_runner", isinstance(runner_policy, dict) and all(runner_policy.get(key) is False for key in ("new_runner", "parallel_runner", "queue_submission", "lease_creation")), "task creates no queue, lease, new runner, or parallel runner")

    command = task.get("command")
    check("task_command_present", isinstance(command, list) and len(command) >= 2 and command[0] == "python", "task command is explicit")
    check("task_bootstrap_known", isinstance(command, list) and any(path in command for path in EXPECTED_COMMANDS), "task command invokes the approved full-pipeline entrypoint")
    check("task_final_false", task.get("final_ready") is False, "task final_ready remains false")

    counts = runtime.get("real_counts")
    check("runtime_not_started", str(runtime.get("status", "")).startswith("NOT_STARTED"), "runtime is not started")
    check("runtime_zero_counts", isinstance(counts, dict) and all(int(value) == 0 for value in counts.values()), "all real runtime counters remain zero")
    check("runtime_no_operations", runtime.get("operation_count") == 0 and runtime.get("operations") == [], "runtime has no fabricated operations")

    report = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "parcel_partition": PARTITION,
        "updated_at": now(),
        "status": "CONTROL_PLANE_READY_EXISTING_RUNNER_UNCLAIMED",
        "check_count": len(checks),
        "checks": checks,
        "checkpoint_sequence": sequence,
        "task_contract": str(args.task_contract.resolve()),
        "runtime": str(args.runtime.resolve()),
        "claim_created": False,
        "task_assigned": False,
        "owner_assigned": False,
        "queue_submission": False,
        "lease_creation": False,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "single_shared_runner_only": True,
        "next_required_step": status.get("first_unverified_step"),
        "blocker": "EXISTING_F_RUNNER_HAS_NOT_CLAIMED_OR_EXECUTED_THE_COMMITTED_TASK",
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    atomic_json(args.output.resolve(), report)
    print(json.dumps({"ok": True, "status": report["status"], "checks": len(checks), "output": str(args.output.resolve())}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

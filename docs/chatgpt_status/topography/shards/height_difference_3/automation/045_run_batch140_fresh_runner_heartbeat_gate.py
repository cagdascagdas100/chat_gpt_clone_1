#!/usr/bin/env python3
"""Fail-closed fresh portable-runner heartbeat gate for height_difference_3.

This gate is executed after exact branch/HEAD validation and before the runtime
environment preflight. It uses the slot heartbeat's declared stale_after_seconds
as the host-liveness freshness budget, verifies the stable runner is alive on the
canonical branch and not busy with another detected task, then invokes 044.
It never mutates the queue, starts a runner, publishes, or writes numeric data.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
ATTEMPT_ID = "height-difference-3-20260721-011"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
BRANCH = "codex/aays-single-runner-v5-20260706"
SLOT_HEARTBEAT_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/heartbeat_latest.json"
GLOBAL_HEARTBEAT_REL = "docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json"
ENV_GATE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/044_run_batch137_runtime_environment_preflight.py"
OUTPUT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json"


def root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def parse_utc(value: Any) -> datetime:
    token = str(value or "").strip()
    if not token:
        raise ValueError("missing timestamp")
    if token.endswith("Z"):
        token = token[:-1] + "+00:00"
    parsed = datetime.fromisoformat(token)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def main() -> int:
    repo = root(Path(__file__).resolve())
    slot_hb = load(repo / SLOT_HEARTBEAT_REL)
    global_hb = load(repo / GLOBAL_HEARTBEAT_REL)
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            raise RuntimeError(f"FRESH_HEARTBEAT_GATE_FAILED:{name}:{detail}")

    check("slot_task_identity", slot_hb.get("task_id") == TASK_ID, slot_hb.get("task_id"))
    check("slot_attempt_identity", slot_hb.get("attempt_id") == ATTEMPT_ID, slot_hb.get("attempt_id"))
    stale_after = int(slot_hb.get("stale_after_seconds") or 0)
    check("slot_stale_after_seconds_present", stale_after > 0, stale_after)

    now = datetime.now(timezone.utc)
    slot_at = parse_utc(slot_hb.get("heartbeat_at"))
    global_at = parse_utc(global_hb.get("heartbeat_at"))
    slot_age = max(0.0, (now - slot_at).total_seconds())
    global_age = max(0.0, (now - global_at).total_seconds())

    check("global_runner_active", global_hb.get("runner_active") is True, global_hb.get("runner_active"))
    check("global_pid_alive", global_hb.get("pid_alive") is True, global_hb.get("pid_alive"))
    check("global_lock_valid", global_hb.get("lock_valid") is True, global_hb.get("lock_valid"))
    check("global_branch", global_hb.get("branch") == BRANCH, global_hb.get("branch"))
    check("global_heartbeat_not_future", global_at <= now, global_hb.get("heartbeat_at"))
    check("global_heartbeat_fresh", global_age <= stale_after, {"age_seconds": global_age, "max_age_seconds": stale_after})

    current_detected = bool(global_hb.get("current_task_detected"))
    current_id = str(global_hb.get("current_task_id") or "")
    check(
        "runner_not_busy_with_other_detected_task",
        (not current_detected) or current_id == TASK_ID,
        {"current_task_detected": current_detected, "current_task_id": current_id},
    )

    env_gate = repo / ENV_GATE_REL
    check("environment_gate_044_exists", env_gate.is_file(), str(env_gate))
    proc = subprocess.run([sys.executable, str(env_gate)], cwd=repo, text=True, capture_output=True, check=False)
    check("environment_gate_044_passed", proc.returncode == 0, {"exit": proc.returncode, "stdout": proc.stdout[-3000:], "stderr": proc.stderr[-3000:]})

    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "continuation_key": CONTINUATION,
        "canonical_branch": BRANCH,
        "checked_at_utc": now.isoformat().replace("+00:00", "Z"),
        "slot_heartbeat_at": slot_at.isoformat().replace("+00:00", "Z"),
        "slot_heartbeat_age_seconds": slot_age,
        "slot_stale_after_seconds": stale_after,
        "global_heartbeat_at": global_at.isoformat().replace("+00:00", "Z"),
        "global_heartbeat_age_seconds": global_age,
        "fresh_host_heartbeat_passed": True,
        "runner_active": True,
        "pid_alive": True,
        "lock_valid": True,
        "runner_not_busy_with_other_detected_task": True,
        "environment_gate_044_executed": True,
        "environment_gate_044_exit_code": proc.returncode,
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "coordinator_action_performed": False,
        "queue_mutated": False,
        "runner_started": False,
        "numeric_values_written": 0,
        "final_ready": False,
        "fake_data": False,
    }
    out = repo / OUTPUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "global_heartbeat_age_seconds": global_age, "max_age_seconds": stale_after, "output": str(out)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

#!/usr/bin/env python3
"""Fail-closed fresh portable-runner heartbeat gate using exact Git HEAD evidence."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
ATTEMPT_ID = "height-difference-3-20260721-011"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
BRANCH = "codex/aays-single-runner-v5-20260706"
DOWNSTREAM_PREFLIGHT_TTL_SECONDS = 900
SLOT_HEARTBEAT_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/heartbeat_latest.json"
GLOBAL_HEARTBEAT_REL = "docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json"
ENV_GATE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/044_run_batch137_runtime_environment_preflight.py"
OUTPUT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json"


def root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs/chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def resolve_git() -> str:
    token = str(os.environ.get("AAYS_GIT_EXE") or "git").strip()
    found = shutil.which(token)
    if found:
        return str(Path(found).resolve())
    candidate = Path(token)
    if candidate.is_file():
        return str(candidate.resolve())
    raise RuntimeError("GIT_EXECUTABLE_NOT_FOUND")


def load_head(git_exe: str, repo: Path, rel: str) -> dict[str, Any]:
    proc = subprocess.run([git_exe, "-C", str(repo), "show", f"HEAD:{rel}"], text=True, capture_output=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"HEAD_HEARTBEAT_READ_FAILED:{rel}:{proc.stderr[-800:]}")
    value = json.loads(proc.stdout)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object at HEAD:{rel}")
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


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}_", suffix=".json.tmp", dir=path.parent)
    os.close(fd)
    temporary = Path(temp_name)
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    repo = root(Path(__file__).resolve())
    git_exe = resolve_git()
    slot_heartbeat = load_head(git_exe, repo, SLOT_HEARTBEAT_REL)
    global_heartbeat = load_head(git_exe, repo, GLOBAL_HEARTBEAT_REL)
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            raise RuntimeError(f"FRESH_HEARTBEAT_GATE_FAILED:{name}:{detail}")

    check("heartbeat_evidence_source_exact_head", True, {"slot": SLOT_HEARTBEAT_REL, "global": GLOBAL_HEARTBEAT_REL})
    check("slot_task_identity", slot_heartbeat.get("task_id") == TASK_ID, slot_heartbeat.get("task_id"))
    check("slot_attempt_identity", slot_heartbeat.get("attempt_id") == ATTEMPT_ID, slot_heartbeat.get("attempt_id"))
    stale_after = int(slot_heartbeat.get("stale_after_seconds") or 0)
    check("slot_stale_after_seconds_gt_downstream_ttl", stale_after > DOWNSTREAM_PREFLIGHT_TTL_SECONDS, {"stale_after_seconds": stale_after, "downstream_ttl_seconds": DOWNSTREAM_PREFLIGHT_TTL_SECONDS})
    entry_budget = stale_after - DOWNSTREAM_PREFLIGHT_TTL_SECONDS

    now = datetime.now(timezone.utc)
    slot_at = parse_utc(slot_heartbeat.get("heartbeat_at"))
    global_at = parse_utc(global_heartbeat.get("heartbeat_at"))
    slot_age = max(0.0, (now - slot_at).total_seconds())
    global_age = max(0.0, (now - global_at).total_seconds())
    check("slot_heartbeat_not_future", slot_at <= now, slot_heartbeat.get("heartbeat_at"))
    check("slot_heartbeat_fresh", slot_age <= stale_after, {"age_seconds": slot_age, "stale_after_seconds": stale_after})
    check("global_runner_active", global_heartbeat.get("runner_active") is True, global_heartbeat.get("runner_active"))
    check("global_pid_alive", global_heartbeat.get("pid_alive") is True, global_heartbeat.get("pid_alive"))
    check("global_lock_valid", global_heartbeat.get("lock_valid") is True, global_heartbeat.get("lock_valid"))
    check("global_branch", global_heartbeat.get("branch") == BRANCH, global_heartbeat.get("branch"))
    check("global_heartbeat_not_future", global_at <= now, global_heartbeat.get("heartbeat_at"))
    check("global_heartbeat_fresh_with_full_ttl_reserve", global_age <= entry_budget, {"age_seconds": global_age, "entry_max_age_seconds": entry_budget, "slot_stale_after_seconds": stale_after, "reserved_downstream_ttl_seconds": DOWNSTREAM_PREFLIGHT_TTL_SECONDS})
    current_detected = bool(global_heartbeat.get("current_task_detected"))
    current_id = str(global_heartbeat.get("current_task_id") or "")
    check("runner_not_busy_with_other_detected_task", (not current_detected) or current_id == TASK_ID, {"current_task_detected": current_detected, "current_task_id": current_id})

    output = repo / OUTPUT_REL
    base = {
        "schema_version": 5,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "continuation_key": CONTINUATION,
        "canonical_branch": BRANCH,
        "heartbeat_evidence_source": "EXACT_GIT_HEAD_SNAPSHOT",
        "portable_git_executable": git_exe,
        "portable_git_contract_passed": True,
        "checked_at_utc": now.isoformat().replace("+00:00", "Z"),
        "slot_heartbeat_at": slot_at.isoformat().replace("+00:00", "Z"),
        "slot_heartbeat_age_seconds": slot_age,
        "slot_stale_after_seconds": stale_after,
        "downstream_runtime_preflight_ttl_seconds": DOWNSTREAM_PREFLIGHT_TTL_SECONDS,
        "global_heartbeat_entry_max_age_seconds": entry_budget,
        "global_heartbeat_at": global_at.isoformat().replace("+00:00", "Z"),
        "global_heartbeat_age_seconds": global_age,
        "fresh_host_heartbeat_passed": True,
        "heartbeat_freshness_reserves_full_preflight_ttl": True,
        "runner_active": True,
        "pid_alive": True,
        "lock_valid": True,
        "runner_not_busy_with_other_detected_task": True,
        "environment_gate_044_executed": False,
        "environment_gate_044_exit_code": None,
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "coordinator_action_performed": False,
        "queue_mutated": False,
        "runner_started": False,
        "numeric_values_written": 0,
        "atomic_output_materialization": True,
        "final_ready": False,
        "fake_data": False,
    }
    atomic_json(output, base)

    environment_gate = repo / ENV_GATE_REL
    check("environment_gate_044_exists", environment_gate.is_file(), str(environment_gate))
    env = os.environ.copy()
    env["AAYS_GIT_EXE"] = git_exe
    proc = subprocess.run([sys.executable, str(environment_gate)], cwd=repo, env=env, text=True, capture_output=True, check=False)
    check("environment_gate_044_passed", proc.returncode == 0, {"exit": proc.returncode, "stdout": proc.stdout[-3000:], "stderr": proc.stderr[-3000:]})
    base.update({
        "environment_gate_044_executed": True,
        "environment_gate_044_exit_code": proc.returncode,
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "completed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    })
    atomic_json(output, base)
    print(json.dumps({"ok": True, "global_heartbeat_age_seconds": global_age, "entry_max_age_seconds": entry_budget, "reserved_downstream_ttl_seconds": DOWNSTREAM_PREFLIGHT_TTL_SECONDS, "output": str(output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

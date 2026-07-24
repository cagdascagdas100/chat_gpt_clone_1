#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
SLOT_ID = "height_difference_2"
IDEMPOTENCY_KEY = "height-difference-2-canonical-export-official-sampling-v3"
ATTEMPT_ID = "height-difference-2-20260721-014"


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "exit_code": process.returncode,
        "stdout": process.stdout[-8000:],
        "stderr": process.stderr[-8000:],
    }


def _validate_task(task: dict[str, Any]) -> None:
    if task.get("task_id") != TASK_ID or task.get("slot_id") != SLOT_ID:
        raise ValueError("task identity mismatch")
    if task.get("idempotency_key") != IDEMPOTENCY_KEY:
        raise ValueError("idempotency key mismatch")
    if any(bool(task.get(k)) for k in ("new_runner", "parallel_runner", "fake_data", "db_write", "migration", "production_deploy", "final_ready")):
        raise ValueError("task safety flag mismatch")


def _same_task_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if TASK_ID in path.name:
        return True
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return isinstance(value, dict) and value.get("task_id") == TASK_ID
    except Exception:
        return False


def _find_markers(bridge_root: Path) -> dict[str, list[str]]:
    states = ("pending", "running", "done", "failed", "processed", "error")
    result: dict[str, list[str]] = {}
    for state in states:
        directory = bridge_root / "ai-queue" / state
        hits = [] if not directory.is_dir() else [str(path) for path in directory.iterdir() if _same_task_file(path)]
        result[state] = sorted(hits)
    return result


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-repo-root", type=Path, required=True)
    p.add_argument("--active-repo-root", type=Path, required=True)
    p.add_argument("--watch-worktree", type=Path, required=True)
    p.add_argument("--bridge-root", type=Path, required=True)
    p.add_argument("--task-json", type=Path, required=True)
    p.add_argument("--recovery-script", type=Path, required=True)
    p.add_argument("--recovery-output", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args(argv)

    stages: list[dict[str, Any]] = []
    code = 2
    try:
        task = _read(args.task_json)
        _validate_task(task)
        if not args.recovery_script.is_file():
            raise FileNotFoundError(f"recovery script missing: {args.recovery_script}")
        markers_before = _find_markers(args.bridge_root)
        terminal_or_running = sum(len(markers_before[s]) for s in ("running", "done", "processed"))
        if terminal_or_running:
            raise ValueError("same task already running or terminal; runtime receipt not rewritten")

        existing_pending = markers_before.get("pending") or []
        if existing_pending:
            if len(existing_pending) != 1:
                raise ValueError("multiple pending files resolve to the same task identity")
            pending_path = Path(existing_pending[0])
            recovery = {
                "schema_version": 1,
                "slot_id": SLOT_ID,
                "task_id": TASK_ID,
                "status": "SAME_TASK_EXISTING_PENDING_REUSED",
                "bridge_task_path": str(pending_path),
                "bridge_task_queued": False,
                "existing_pending_reused": True,
                "new_runner": False,
                "parallel_runner": False,
                "new_task_created": False,
                "new_worktree_created": False,
                "process_started": False,
                "active_repo_branch_changed": False,
            }
            _write(args.recovery_output, recovery)
            stages.append({"stage": "SAME_TASK_EXISTING_PENDING_REUSE", "exit_code": 0, "status": recovery["status"]})
        else:
            command = [
                sys.executable,
                str(args.recovery_script),
                "--source-repo-root", str(args.source_repo_root),
                "--active-repo-root", str(args.active_repo_root),
                "--watch-worktree", str(args.watch_worktree),
                "--bridge-root", str(args.bridge_root),
                "--task-json", str(args.task_json),
                "--output", str(args.recovery_output),
            ]
            if args.apply:
                command.append("--apply")
            recovery_stage = {"stage": "SAME_TASK_BRANCH_RECOVERY", **_run(command, args.source_repo_root)}
            stages.append(recovery_stage)
            if recovery_stage["exit_code"] != 0:
                raise RuntimeError("same-task recovery stage failed")
            recovery = _read(args.recovery_output)
            expected_status = "SAME_TASK_BRIDGE_RECOVERY_APPLIED" if args.apply else "SAME_TASK_BRIDGE_RECOVERY_PREFLIGHT_READY"
            if recovery.get("status") != expected_status:
                raise ValueError("recovery output status mismatch")

        if any(bool(recovery.get(k)) for k in ("new_runner", "parallel_runner", "new_task_created", "new_worktree_created", "process_started", "active_repo_branch_changed")):
            raise ValueError("recovery safety invariant violated")

        pending_path = Path(str(recovery.get("bridge_task_path") or ""))
        runtime_receipt_written = False
        runtime_task_sha256 = None
        if args.apply:
            if not pending_path.is_file():
                raise FileNotFoundError("recovered pending task missing")
            runtime_task = _read(pending_path)
            _validate_task(runtime_task)
            runtime_task.update({
                "attempt_id": ATTEMPT_ID,
                "status": "pending",
                "state": "pending",
                "claimable": True,
                "ready_for_claim": True,
                "runtime_recovery_applied": True,
                "runtime_recovery_contract": "branch_aware_same_task_existing_bridge_v1",
                "runtime_source_branch": "codex/aays-single-runner-v5-20260706",
                "runtime_recovery_output": str(args.recovery_output),
                "new_runner": False,
                "parallel_runner": False,
                "new_task_created": False,
                "final_ready": False,
                "fake_data": False,
                "db_write": False,
                "migration": False,
                "production_deploy": False,
            })
            _write(pending_path, runtime_task)
            runtime_task_sha256 = _sha256(pending_path)
            runtime_receipt_written = True

        markers_after = _find_markers(args.bridge_root)
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "status": "SAME_TASK_RUNTIME_READY_RECEIPT_WRITTEN" if args.apply else "SAME_TASK_RUNTIME_RECOVERY_PREFLIGHT_READY",
            "stages": stages,
            "recovery_output": str(args.recovery_output),
            "recovery_output_sha256": _sha256(args.recovery_output),
            "bridge_task_path": str(pending_path),
            "bridge_task_sha256": runtime_task_sha256,
            "runtime_receipt_written": runtime_receipt_written,
            "ready_for_claim": bool(args.apply),
            "markers_before": markers_before,
            "markers_after": markers_after,
            "existing_worktree_reused": True,
            "existing_bridge_reused": True,
            "process_started": False,
            "process_stopped": False,
            "new_worktree_created": False,
            "new_runner": False,
            "parallel_runner": False,
            "new_task_created": False,
            "active_repo_branch_changed": False,
            "same_idempotent_task_only": True,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 0
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "status": "BLOCKED_SAME_TASK_RUNTIME_RECOVERY",
            "error": f"{type(exc).__name__}: {exc}",
            "stages": stages,
            "ready_for_claim": False,
            "process_started": False,
            "new_worktree_created": False,
            "new_runner": False,
            "parallel_runner": False,
            "new_task_created": False,
            "active_repo_branch_changed": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"], "ready_for_claim": payload.get("ready_for_claim", False)}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

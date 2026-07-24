#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_STALE_SECONDS = 180


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _parse_kv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().casefold()] = value.strip()
    return values


def _parse_time(value: str) -> datetime:
    value = value.strip()
    for fmt in ("%Y%m%d_%H%M%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            parsed = datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--watcher-heartbeat", type=Path, required=True)
    parser.add_argument("--slot-heartbeat", type=Path, required=True)
    parser.add_argument("--task-json", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--watcher-branch", default="main")
    parser.add_argument("--source-branch", required=True)
    parser.add_argument("--now")
    parser.add_argument("--stale-seconds", type=int, default=DEFAULT_STALE_SECONDS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    blockers: list[str] = []
    checks: dict[str, Any] = {}
    try:
        watcher = _parse_kv(args.watcher_heartbeat)
        slot = _load_json(args.slot_heartbeat)
        task = _load_json(args.task_json)
        now = _parse_time(args.now) if args.now else datetime.now(timezone.utc)
        watcher_time_text = watcher.get("updated_at") or watcher.get("heartbeat_at")
        if not watcher_time_text:
            raise ValueError("watcher heartbeat lacks updated_at/heartbeat_at")
        watcher_time = _parse_time(watcher_time_text)
        age_seconds = max(0, int((now - watcher_time).total_seconds()))
        watcher_fresh = age_seconds <= args.stale_seconds
        if not watcher_fresh:
            blockers.append("WATCHER_HEARTBEAT_STALE")

        watcher_status = watcher.get("status", "").upper()
        if watcher_status != "WATCHING":
            blockers.append("WATCHER_STATUS_NOT_WATCHING")

        source_branch_visible = args.source_branch == args.watcher_branch
        if not source_branch_visible:
            blockers.append("TASK_SOURCE_BRANCH_NOT_WATCHER_VISIBLE")

        task_id = str(task.get("task_id") or "")
        if not task_id:
            blockers.append("TASK_ID_MISSING")

        script_rel = str(task.get("script_path") or "")
        script_exists = bool(script_rel) and (args.repo_root / script_rel).is_file()
        if not script_exists:
            blockers.append("TASK_SCRIPT_NOT_PRESENT_IN_ACTIVE_REPO")

        expected = [str(value) for value in task.get("expected_outputs", []) if str(value).strip()]
        expected_presence = {path: (args.repo_root / path).is_file() for path in expected}
        produced_count = sum(expected_presence.values())

        slot_state = str(slot.get("state") or slot.get("status") or "").casefold()
        slot_claimed = slot_state not in {"", "unclaimed", "pending", "pending_runner_claim"} or bool(
            slot.get("owner_page_session_id") or slot.get("current_task_id")
        )

        checks = {
            "watcher_status": watcher_status,
            "watcher_updated_at": watcher_time.isoformat(),
            "watcher_age_seconds": age_seconds,
            "watcher_stale_seconds": args.stale_seconds,
            "watcher_fresh": watcher_fresh,
            "watcher_branch": args.watcher_branch,
            "task_source_branch": args.source_branch,
            "task_source_branch_visible": source_branch_visible,
            "task_id": task_id,
            "task_script_path": script_rel,
            "task_script_exists_in_active_repo": script_exists,
            "slot_state": slot_state,
            "slot_claimed": slot_claimed,
            "expected_output_count": len(expected),
            "expected_output_presence": expected_presence,
            "expected_output_produced_count": produced_count,
        }

        status = "READY_FOR_EXISTING_SINGLE_RUNNER" if not blockers else "BLOCKED_WATCHER_OR_VISIBILITY_GATE"
        code = 0 if not blockers else 2
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "task_id": task_id,
            "status": status,
            "checks": checks,
            "blockers": blockers,
            "process_started": False,
            "branch_modified": False,
            "queue_task_created": False,
            "new_runner": False,
            "parallel_runner": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": "BLOCKED_WATCHER_DIAGNOSTIC_ERROR",
            "error": f"{type(exc).__name__}: {exc}",
            "checks": checks,
            "blockers": ["WATCHER_DIAGNOSTIC_ERROR"],
            "process_started": False,
            "branch_modified": False,
            "queue_task_created": False,
            "new_runner": False,
            "parallel_runner": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 2

    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"], "blockers": payload.get("blockers", [])}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

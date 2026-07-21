#!/usr/bin/env python3
"""Fail-closed readiness audit for dispatching internet_access_2 to the existing shared runner.

This utility is read-only. It does not claim a slot, create a queue entry, start a
runner, modify heartbeat files, or write business data. It consumes exported
remote state snapshots and emits an evidence-only readiness report.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_2"
WATCHED_BRANCH = "main"
EXPECTED_ALLOWED_WEB_PATH = "england_map_web/data/aays_18_slots/internet_access_2"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object: {path}")
    return payload


def parse_kv_text(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(value, "%Y%m%d_%H%M%S").replace(tzinfo=timezone(timedelta(hours=3)))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def gate(gate_id: str, title: str, passed: bool, evidence: str, blocker: str | None = None) -> dict[str, Any]:
    return {"gate_id": gate_id, "title": title, "state": "PASS" if passed else "BLOCKED", "evidence": evidence, "blocker": None if passed else blocker}


def evaluate(checkpoint: dict[str, Any], status: dict[str, Any], heartbeat: dict[str, Any], current_task: dict[str, Any], ownership: dict[str, Any], watcher: dict[str, str], active_runner_task: dict[str, Any], review_pr: dict[str, Any], *, now: datetime, freshness_seconds: int) -> dict[str, Any]:
    allowed_paths = set(current_task.get("allowed_paths") or [])
    watcher_at = parse_time(watcher.get("updated_at"))
    watcher_age = None if watcher_at is None else max(0, int((now - watcher_at).total_seconds()))
    watcher_fresh = watcher_age is not None and watcher_age <= freshness_seconds
    active_status = str(active_runner_task.get("status") or "")
    active_other_task = bool(active_runner_task.get("task_id")) and active_runner_task.get("slot_id") != SLOT_ID and active_status not in {"IDLE", "COMPLETE", "COMPLETED", "TERMINAL", "FINAL_READY"}
    gates = [
        gate("SLOT_ID", "All authoritative slot files target internet_access_2", all(x.get("slot_id") == SLOT_ID for x in (checkpoint, status, heartbeat, current_task, ownership)), "checkpoint/status/heartbeat/current-task/ownership slot IDs checked", "authoritative slot ID mismatch"),
        gate("CHECKPOINT", "Checkpoint remains non-terminal sequence 0", int(checkpoint.get("sequence", -1)) == 0 and checkpoint.get("final_ready") is False, f"sequence={checkpoint.get('sequence')}; final_ready={checkpoint.get('final_ready')}", "checkpoint changed or is terminal"),
        gate("STATUS", "Slot is ready for claim", status.get("state") == "ready_for_claim" and not status.get("owner_page_session_id"), f"state={status.get('state')}; owner={status.get('owner_page_session_id')}", "slot is not ready_for_claim or has an owner"),
        gate("OWNERSHIP", "Ownership lease is absent", ownership.get("state") == "unclaimed" and not ownership.get("lease_token_hash"), f"state={ownership.get('state')}; lease_version={ownership.get('lease_version')}", "slot ownership is already claimed"),
        gate("SLOT_HEARTBEAT", "Slot heartbeat is unclaimed/stale", heartbeat.get("state") == "unclaimed" and heartbeat.get("stale") is True, f"state={heartbeat.get('state')}; stale={heartbeat.get('stale')}", "slot heartbeat indicates an active owner"),
        gate("SLOT_TASK", "Slot current task is idle", current_task.get("state") == "idle" and not current_task.get("task_id"), f"state={current_task.get('state')}; task_id={current_task.get('task_id')}", "slot already has a current task"),
        gate("ALLOWED_PATH", "Authorized aays_18 web path is present", EXPECTED_ALLOWED_WEB_PATH in allowed_paths, EXPECTED_ALLOWED_WEB_PATH, "authorized web path missing from current-task contract"),
        gate("WATCHER_FRESH", "Repo-to-bridge watcher heartbeat is fresh", watcher_fresh, f"watcher_updated_at={watcher.get('updated_at')}; age_seconds={watcher_age}; threshold={freshness_seconds}", "repo-to-bridge watcher heartbeat is stale"),
        gate("RUNNER_FRESH", "Existing shared runner heartbeat is fresh", active_runner_task.get("runner_heartbeat_fresh") is True, f"runner_last_heartbeat_at={active_runner_task.get('runner_last_heartbeat_at')}; fresh={active_runner_task.get('runner_heartbeat_fresh')}", "shared runner heartbeat is stale"),
        gate("QUEUE_HEAD_FREE", "No other watcher-visible task is pending or active", not active_other_task, f"slot_id={active_runner_task.get('slot_id')}; task_id={active_runner_task.get('task_id')}; status={active_status}", "another task is already pending at the watcher-visible queue head"),
        gate("REVIEW_MERGED", "Slot implementation is merged to watcher-visible branch", review_pr.get("merged") is True and review_pr.get("base") == WATCHED_BRANCH, f"pr={review_pr.get('number')}; state={review_pr.get('state')}; merged={review_pr.get('merged')}; base={review_pr.get('base')}", "slot implementation is not merged to main"),
        gate("PR_MERGEABLE", "Review branch is mergeable before integration", review_pr.get("mergeable") is True, f"pr={review_pr.get('number')}; mergeable={review_pr.get('mergeable')}; draft={review_pr.get('draft')}", "review PR is not currently mergeable"),
        gate("NO_DIRECT_PUSH", "Direct-push prohibition remains enforced", current_task.get("direct_push_forbidden") is True, f"direct_push_forbidden={current_task.get('direct_push_forbidden')}", "direct-push prohibition missing"),
    ]
    blocked = [item for item in gates if item["state"] == "BLOCKED"]
    return {"schema_version": 3, "slot_id": SLOT_ID, "status": "READY_FOR_EXISTING_RUNNER_DISPATCH" if not blocked else "BLOCKED_FAIL_CLOSED", "dispatch_permitted": not blocked, "gate_count": len(gates), "passed_gate_count": len(gates) - len(blocked), "blocked_gate_count": len(blocked), "gates": gates, "next_step": "CLAIM_WITH_FRESH_REMOTE_READBACK_AND_DISPATCH_EXISTING_RUNNER" if not blocked else "WAIT_FOR_CURRENT_QUEUE_HEAD_TERMINAL_AND_RECOVER_WATCHER_RUNNER_HEARTBEATS_THEN_MERGE_TO_MAIN_AND_RECHECK", "single_shared_runner_only": True, "new_runner_started": False, "ownership_claimed": False, "queue_entry_written": False, "actual_business_data_rows_written": 0, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False, "final_ready": False, "evaluated_at": now.isoformat().replace("+00:00", "Z")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--status", required=True, type=Path)
    parser.add_argument("--heartbeat", required=True, type=Path)
    parser.add_argument("--current-task", required=True, type=Path)
    parser.add_argument("--ownership", required=True, type=Path)
    parser.add_argument("--watcher-heartbeat", required=True, type=Path)
    parser.add_argument("--active-runner-task", required=True, type=Path)
    parser.add_argument("--review-pr", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--freshness-seconds", type=int, default=900)
    args = parser.parse_args()
    report = evaluate(load_json(args.checkpoint), load_json(args.status), load_json(args.heartbeat), load_json(args.current_task), load_json(args.ownership), parse_kv_text(args.watcher_heartbeat), load_json(args.active_runner_task), load_json(args.review_pr), now=datetime.now(timezone.utc), freshness_seconds=args.freshness_seconds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["dispatch_permitted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_1"
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
TASK_BRANCH = "codex/aays-single-runner-v5-20260706"
WATCHER_REF = os.environ.get("AAYS_WATCHER_REF", "origin/main")
STALE_AFTER_SECONDS = 900

QUEUE_PATH = "docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json"
AUTOMATION_PATH = "docs/chatgpt_status/topography/shards/height_difference_1/automation/013_height_difference_1_revision_9_height_difference_metric_20260721.py"
WATCHER_HEARTBEAT_PATH = "docs/chatgpt_status/aays1/status/061_repo_to_bridge_watch_heartbeat_latest.txt"
SLOT_HEARTBEAT_PATH = "docs/chatgpt_status/_shared/slots_21/height_difference_1/heartbeat_latest.json"
EXPECTED_OUTPUT_PATH = "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/011_height_difference_metric_gate_latest.json"


def parse_kv(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in text.lstrip("\ufeff").splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def parse_compact_timestamp(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def classify(*, watcher_fresh: bool, queue_on_watcher_ref: bool, automation_on_watcher_ref: bool, slot_claimed: bool, output_present: bool) -> tuple[str, list[str]]:
    blockers: list[str] = []
    if not watcher_fresh:
        blockers.append("REPO_TO_BRIDGE_WATCHER_HEARTBEAT_STALE")
    if not queue_on_watcher_ref:
        blockers.append("TASK_QUEUE_NOT_PRESENT_ON_WATCHER_REF")
    if not automation_on_watcher_ref:
        blockers.append("TASK_AUTOMATION_NOT_PRESENT_ON_WATCHER_REF")
    if not slot_claimed:
        blockers.append("EXISTING_SINGLE_SHARED_RUNNER_CLAIM_NOT_OBSERVED")
    if not output_present:
        blockers.append("REVISION_9_RUNNER_OUTPUT_NOT_PRESENT")
    return ("READY_FOR_RESULT_INSPECTION" if not blockers else "BLOCKED_WATCHER_VISIBILITY_OR_RUNNER_HEALTH", blockers)


def git_output(repo: Path, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=str(repo), text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout.strip()


def git_path_exists(repo: Path, ref: str, path: str) -> bool:
    code, _ = git_output(repo, ["cat-file", "-e", f"{ref}:{path}"])
    return code == 0


def git_show_text(repo: Path, ref: str, path: str) -> str:
    code, text = git_output(repo, ["show", f"{ref}:{path}"])
    return text if code == 0 else ""


def diagnose(repo: Path, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    branch_code, current_branch = git_output(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    current_branch = current_branch if branch_code == 0 else "UNKNOWN"

    watcher_text = git_show_text(repo, WATCHER_REF, WATCHER_HEARTBEAT_PATH)
    watcher_kv = parse_kv(watcher_text)
    watcher_dt = parse_compact_timestamp(watcher_kv.get("updated_at", ""))
    watcher_age_seconds = int((now - watcher_dt).total_seconds()) if watcher_dt else None
    watcher_fresh = watcher_age_seconds is not None and 0 <= watcher_age_seconds <= STALE_AFTER_SECONDS

    queue_on_task_branch = git_path_exists(repo, f"origin/{TASK_BRANCH}", QUEUE_PATH) or (repo / QUEUE_PATH).exists()
    automation_on_task_branch = git_path_exists(repo, f"origin/{TASK_BRANCH}", AUTOMATION_PATH) or (repo / AUTOMATION_PATH).exists()
    queue_on_watcher_ref = git_path_exists(repo, WATCHER_REF, QUEUE_PATH)
    automation_on_watcher_ref = git_path_exists(repo, WATCHER_REF, AUTOMATION_PATH)

    slot_hb: dict[str, Any] = {}
    slot_hb_path = repo / SLOT_HEARTBEAT_PATH
    if slot_hb_path.exists():
        try:
            slot_hb = json.loads(slot_hb_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            slot_hb = {}
    slot_claimed = slot_hb.get("state") in {"claimed", "running"} and slot_hb.get("current_task_id") == TASK_ID
    output_present = (repo / EXPECTED_OUTPUT_PATH).exists()

    status, blockers = classify(
        watcher_fresh=watcher_fresh,
        queue_on_watcher_ref=queue_on_watcher_ref,
        automation_on_watcher_ref=automation_on_watcher_ref,
        slot_claimed=slot_claimed,
        output_present=output_present,
    )

    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "payload_revision": 9,
        "status": status,
        "checked_at": now.isoformat(),
        "checks": {
            "current_branch": current_branch,
            "task_branch": TASK_BRANCH,
            "watcher_ref": WATCHER_REF,
            "watcher_status": watcher_kv.get("status"),
            "watcher_repo_root": watcher_kv.get("repo_root"),
            "watcher_worktree": watcher_kv.get("watch_repo"),
            "watcher_queue_dir": watcher_kv.get("queue_dir"),
            "watcher_heartbeat_updated_at_raw": watcher_kv.get("updated_at"),
            "watcher_heartbeat_age_seconds": watcher_age_seconds,
            "watcher_heartbeat_fresh": watcher_fresh,
            "queue_on_task_branch": queue_on_task_branch,
            "automation_on_task_branch": automation_on_task_branch,
            "queue_on_watcher_ref": queue_on_watcher_ref,
            "automation_on_watcher_ref": automation_on_watcher_ref,
            "slot_heartbeat_state": slot_hb.get("state"),
            "slot_heartbeat_at": slot_hb.get("heartbeat_at"),
            "slot_current_task_id": slot_hb.get("current_task_id"),
            "slot_claimed_for_expected_task": slot_claimed,
            "revision_9_output_present": output_present,
        },
        "blockers": blockers,
        "required_operator_action": "Recover the existing repo-to-bridge watcher and existing single runner, then expose the complete same-task queue plus automation under the operator-approved watcher branch policy. Do not mirror queue only.",
        "unsafe_actions_rejected": [
            "queue-only mirror to main without automation",
            "duplicate task creation",
            "new runner creation",
            "parallel runner creation",
            "fabricated heartbeat",
            "fabricated official measurement output",
        ],
        "process_started": False,
        "branch_modified_outside_authoritative_branch": False,
        "new_task_created": False,
        "new_runner": False,
        "parallel_runner": False,
        "official_height_difference_rows_written": 0,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def main() -> int:
    repo = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
    result = diagnose(repo)
    outputs = [
        repo / "docs/chatgpt_status/topography/shards/height_difference_1/diagnostics/012_watcher_visibility_health_latest.json",
        repo / "england_map_web/data/aays_21_slots/height_difference_1/watcher_visibility_health_latest.json",
    ]
    text = json.dumps(result, ensure_ascii=False, indent=2)
    for path in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(json.dumps({"status": result["status"], "blockers": result["blockers"], "outputs": [str(p) for p in outputs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-closed validation for the Batch 134 same-task coordinator wiring request.

This validator never edits the legacy queue, starts a runner, publishes, or changes
numeric measurements. It proves whether the existing queue record can safely be
runtime-wired to the canonical no-argument entrypoint without creating a duplicate.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
ATTEMPT_ID = "height-difference-3-20260721-011"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
LEGACY_SCRIPT = "docs/chatgpt_status/topography/shards/height_difference_3/automation/023_runner_entry_canonical_api_measurement.py"
CANONICAL_SCRIPT = "docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py"
POST_SCRIPT = "docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py"
EXPECTED_ROWS = list(range(61540, 61552))


def repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def git_blob(repo: Path, path: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "hash-object", "--no-filters", "--", str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git hash-object failed: {proc.stderr[-1000:]}")
    value = proc.stdout.strip().lower()
    if len(value) != 40:
        raise ValueError(f"invalid git blob hash: {value!r}")
    return value


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    repo = repo_root(Path(__file__).resolve())
    request_path = repo / "docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json"
    task_path = repo / "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
    queue_path = repo / "docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json"
    ownership_path = repo / "docs/chatgpt_status/_shared/slots_21/height_difference_3/ownership_latest.json"
    output_path = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/035_batch134_coordinator_wiring_qa/coordinator_wiring_request_validation.json"

    request = load(request_path)
    task = load(task_path)
    queue = load(queue_path)
    ownership = load(ownership_path)
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            raise ValueError(f"wiring validation failed: {name}: {detail}")

    check("request_task", request.get("task_id") == TASK_ID)
    check("request_attempt", request.get("attempt_id") == ATTEMPT_ID)
    check("request_continuation", request.get("continuation_key") == CONTINUATION)
    check("request_coordinator_only", request.get("coordinator_only") is True)
    check("request_new_task_forbidden", request.get("new_task_forbidden") is True)
    check("request_duplicate_forbidden", request.get("duplicate_task_forbidden") is True)
    check("request_new_runner_forbidden", request.get("new_runner_forbidden") is True)
    check("request_parallel_runner_forbidden", request.get("parallel_runner_forbidden") is True)

    check("task_id", task.get("task_id") == TASK_ID)
    check("task_attempt", task.get("attempt_id") == ATTEMPT_ID)
    check("task_continuation", task.get("continuation_key") == CONTINUATION)
    check("task_script_039", task.get("script_path") == CANONICAL_SCRIPT)
    check("task_post_script_040", task.get("post_publish_script_path") == POST_SCRIPT)
    check("task_single_runner", task.get("single_runner_only") is True)
    check("task_new_runner_false", task.get("new_runner") is False)
    check("task_parallel_runner_false", task.get("parallel_runner") is False)
    check("task_child_push_forbidden", task.get("child_direct_push_forbidden") is True)
    check("task_expected_outputs_15", len(task.get("expected_outputs") or []) == 15)
    check("task_read_paths_38", len(task.get("read_paths") or []) == 38)

    check("queue_task", queue.get("task_id") == TASK_ID)
    check("queue_attempt", queue.get("attempt_id") == ATTEMPT_ID)
    check("queue_idempotency", queue.get("idempotency_key") == task.get("idempotency_key"))
    check("queue_single_runner", queue.get("single_runner_only") is True)
    check("queue_new_runner_false", queue.get("new_runner") is False)
    check("queue_parallel_runner_false", queue.get("parallel_runner") is False)
    check("queue_child_push_forbidden", queue.get("child_direct_push_forbidden") is True)
    check("queue_state_queued", queue.get("state") == "queued")
    check("queue_script_known", queue.get("script_path") in {LEGACY_SCRIPT, CANONICAL_SCRIPT}, queue.get("script_path"))

    pre = request.get("preconditions") or {}
    task_blob = git_blob(repo, task_path)
    queue_blob = git_blob(repo, queue_path)
    check("task_blob_pinned", task_blob == str(pre.get("canonical_current_task_expected_blob_sha") or "").lower(), task_blob)
    check("queue_blob_pinned", queue_blob == str(pre.get("legacy_queue_expected_blob_sha") or "").lower(), queue_blob)

    override = request.get("coordinator_runtime_override") or {}
    check("override_uses_existing_queue", override.get("use_existing_queue_record") is True)
    check("override_no_new_queue", override.get("do_not_create_new_queue_record") is True)
    check("override_script_039", override.get("runtime_script_path") == CANONICAL_SCRIPT)
    check("override_post_script_040", override.get("post_publish_script_path") == POST_SCRIPT)
    check("override_no_args", override.get("runtime_arguments") == [] and override.get("post_publish_arguments") == [])
    check("expected_rows", [int(v) for v in (request.get("expected_rows") or [])] == EXPECTED_ROWS)

    owner_state = str(ownership.get("state") or "")
    owner_id = ownership.get("owner_page_session_id")
    ownership_safe_for_future_coordinator = owner_state == "UNCLAIMED" or (
        owner_state == "CLAIMED" and owner_id == "chatgpt-height-difference-3-batch134-20260726"
    )
    check("ownership_not_conflicting", ownership_safe_for_future_coordinator, {"state": owner_state, "owner": owner_id})

    already_aligned = queue.get("script_path") == CANONICAL_SCRIPT
    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION,
        "status": "ALREADY_ALIGNED" if already_aligned else "SAFE_FOR_COORDINATOR_RUNTIME_REWIRE_AFTER_FRESH_HOST_HEARTBEAT",
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "current_task_git_blob_sha": task_blob,
        "legacy_queue_git_blob_sha": queue_blob,
        "legacy_queue_script_path": queue.get("script_path"),
        "requested_runtime_script_path": CANONICAL_SCRIPT,
        "requested_post_publish_script_path": POST_SCRIPT,
        "fresh_host_heartbeat_still_required": True,
        "coordinator_action_performed": False,
        "legacy_queue_mutated": False,
        "new_task_created": False,
        "new_runner_created": False,
        "numeric_values_written": 0,
        "expected_rows": EXPECTED_ROWS,
        "final_ready": False,
        "fake_data": False,
    }
    write(output_path, payload)
    print(json.dumps({"ok": True, "status": payload["status"], "checks": len(checks), "output": str(output_path)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

#!/usr/bin/env python3
"""Fail-closed validation for the same-task coordinator wiring request.

Git blob pins are resolved from Git trees, not raw Windows working-tree bytes.
A freshly fetched origin remote-tracking ref is required and critical local HEAD
blobs must equal the fetched origin blobs. Batch138 validates the complete
runtime executable-identity chain through 039/036/033/032 and resume input 076.
This script never edits the legacy queue, starts a runner, publishes, or changes
numeric values.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
ATTEMPT_ID = "height-difference-3-20260721-011"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
BRANCH = "codex/aays-single-runner-v5-20260706"
LEGACY_SCRIPT = "docs/chatgpt_status/topography/shards/height_difference_3/automation/023_runner_entry_canonical_api_measurement.py"
CANONICAL_SCRIPT = "docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py"
POST_SCRIPT = "docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py"
EXPECTED_ROWS = list(range(61540, 61552))
EXPECTED_READ_PATH_COUNT = 48
EXPECTED_OUTPUT_COUNT = 19

REQUEST_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json"
TASK_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
QUEUE_REL = "docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json"
OWNERSHIP_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/ownership_latest.json"
VALIDATOR_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/041_validate_batch134_coordinator_wiring_request.py"
BOOTSTRAP_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/042_run_batch135_fresh_origin_wiring_preflight.py"
HEAD_GATE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/043_run_batch136_exact_branch_head_and_dependency_preflight.py"
ENV_GATE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/044_run_batch137_runtime_environment_preflight.py"
STRICT036_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/036_run_batch131_strict12_with_local_acceptance.ps1"
STRICT033_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/033_run_batch130_prepare12_strict_measurement_chain.ps1"
STRICT032_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/032_run_batch129_range_extract_and_prepare12.ps1"
RESUME076_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/076_batch138_runtime_executable_identity_resume.json"
ENV_RECORD_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json"


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


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr[-1200:]}")
    return proc.stdout.strip()


def tree_blob(repo: Path, ref: str, rel: str) -> str:
    value = git(repo, "rev-parse", f"{ref}:{rel}").lower()
    if len(value) != 40:
        raise ValueError(f"invalid tree blob for {ref}:{rel}: {value!r}")
    return value


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    repo = repo_root(Path(__file__).resolve())
    request_path = repo / REQUEST_REL
    task_path = repo / TASK_REL
    queue_path = repo / QUEUE_REL
    ownership_path = repo / OWNERSHIP_REL
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

    check("request_schema_5_plus", int(request.get("schema_version") or 0) >= 5, request.get("schema_version"))
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
    check("task_expected_outputs_19", len(task.get("expected_outputs") or []) == EXPECTED_OUTPUT_COUNT)
    check("task_read_paths_48", len(task.get("read_paths") or []) == EXPECTED_READ_PATH_COUNT)
    check("task_has_resume_076", RESUME076_REL in (task.get("read_paths") or []))
    check("task_can_read_runtime_identity_record", ENV_RECORD_REL in (task.get("read_paths") or []))

    check("queue_task", queue.get("task_id") == TASK_ID)
    check("queue_attempt", queue.get("attempt_id") == ATTEMPT_ID)
    check("queue_idempotency", queue.get("idempotency_key") == task.get("idempotency_key"))
    check("queue_single_runner", queue.get("single_runner_only") is True)
    check("queue_new_runner_false", queue.get("new_runner") is False)
    check("queue_parallel_runner_false", queue.get("parallel_runner") is False)
    check("queue_child_push_forbidden", queue.get("child_direct_push_forbidden") is True)
    check("queue_state_queued", queue.get("state") == "queued")
    check("queue_script_known", queue.get("script_path") in {LEGACY_SCRIPT, CANONICAL_SCRIPT}, queue.get("script_path"))

    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    git(repo, "fetch", "--no-tags", "origin", fetch_spec)
    remote_ref = f"refs/remotes/origin/{BRANCH}"
    remote_head = git(repo, "rev-parse", remote_ref)
    local_head = git(repo, "rev-parse", "HEAD")
    check("remote_head_resolved", len(remote_head) == 40, remote_head)
    check("local_head_resolved", len(local_head) == 40, local_head)

    pre = request.get("preconditions") or {}
    check("request_read_path_count_48", int(pre.get("canonical_current_task_read_path_count_required") or 0) == EXPECTED_READ_PATH_COUNT)
    check("request_output_count_19", int(pre.get("canonical_current_task_expected_output_count_required") or 0) == EXPECTED_OUTPUT_COUNT)
    check("request_runtime_identity_required", pre.get("runtime_executable_identity_required") is True)
    check("request_same_python_required", pre.get("preflight_python_must_equal_runtime_python") is True)
    check("request_same_powershell_required", pre.get("preflight_powershell_must_equal_runtime_powershell") is True)

    local_task_blob = tree_blob(repo, "HEAD", TASK_REL)
    local_queue_blob = tree_blob(repo, "HEAD", QUEUE_REL)
    remote_task_blob = tree_blob(repo, remote_head, TASK_REL)
    remote_queue_blob = tree_blob(repo, remote_head, QUEUE_REL)
    expected_task_blob = str(pre.get("canonical_current_task_expected_blob_sha") or "").lower()
    expected_queue_blob = str(pre.get("legacy_queue_expected_blob_sha") or "").lower()

    check("remote_task_blob_pinned", remote_task_blob == expected_task_blob, remote_task_blob)
    check("remote_queue_blob_pinned", remote_queue_blob == expected_queue_blob, remote_queue_blob)
    check("local_task_tree_matches_remote", local_task_blob == remote_task_blob, {"local": local_task_blob, "remote": remote_task_blob})
    check("local_queue_tree_matches_remote", local_queue_blob == remote_queue_blob, {"local": local_queue_blob, "remote": remote_queue_blob})

    critical_paths = [
        REQUEST_REL,
        TASK_REL,
        QUEUE_REL,
        CANONICAL_SCRIPT,
        POST_SCRIPT,
        VALIDATOR_REL,
        BOOTSTRAP_REL,
        HEAD_GATE_REL,
        ENV_GATE_REL,
        STRICT036_REL,
        STRICT033_REL,
        STRICT032_REL,
        RESUME076_REL,
    ]
    critical_blob_rows: list[dict[str, str]] = []
    remote_blobs: dict[str, str] = {}
    for rel in critical_paths:
        local_blob = tree_blob(repo, "HEAD", rel)
        remote_blob = tree_blob(repo, remote_head, rel)
        check(f"critical_blob_parity:{rel}", local_blob == remote_blob, {"local": local_blob, "remote": remote_blob})
        remote_blobs[rel] = remote_blob
        critical_blob_rows.append({"path": rel, "local_head_blob": local_blob, "remote_blob": remote_blob})

    status = git(repo, "status", "--porcelain", "--untracked-files=no", "--", *critical_paths)
    check("critical_worktree_clean", status == "", status)

    validator_chain = request.get("validator_chain") or {}
    identity_chain = request.get("runtime_identity_chain") or {}
    override = request.get("coordinator_runtime_override") or {}
    check("pin_043", str(validator_chain.get("exact_branch_head_gate_expected_blob_sha") or "").lower() == remote_blobs[HEAD_GATE_REL])
    check("pin_044", str(validator_chain.get("runtime_environment_gate_expected_blob_sha") or "").lower() == remote_blobs[ENV_GATE_REL])
    check("pin_042", str(validator_chain.get("fresh_origin_bootstrap_expected_blob_sha") or "").lower() == remote_blobs[BOOTSTRAP_REL])
    check("pin_041", str(validator_chain.get("same_task_validator_expected_blob_sha") or "").lower() == remote_blobs[VALIDATOR_REL])
    check("pin_039", str(override.get("runtime_script_expected_blob_sha") or "").lower() == remote_blobs[CANONICAL_SCRIPT])
    check("pin_036", str(identity_chain.get("strict036_expected_blob_sha") or "").lower() == remote_blobs[STRICT036_REL])
    check("pin_033", str(identity_chain.get("strict033_expected_blob_sha") or "").lower() == remote_blobs[STRICT033_REL])
    check("pin_032", str(identity_chain.get("strict032_expected_blob_sha") or "").lower() == remote_blobs[STRICT032_REL])
    check("pin_resume_076", str(identity_chain.get("resume_076_expected_blob_sha") or "").lower() == remote_blobs[RESUME076_REL])
    check("identity_python_propagation", identity_chain.get("python_executable_propagates_039_036_033_032") is True)
    check("identity_powershell_propagation", identity_chain.get("powershell_executable_propagates_039_036_033_032") is True)
    check("identity_039_consumes_preflight", identity_chain.get("runtime_039_consumes_preflight_identity_record") is True)

    check("override_uses_existing_queue", override.get("use_existing_queue_record") is True)
    check("override_no_new_queue", override.get("do_not_create_new_queue_record") is True)
    check("override_script_039", override.get("runtime_script_path") == CANONICAL_SCRIPT)
    check("override_post_script_040", override.get("post_publish_script_path") == POST_SCRIPT)
    check("override_no_args", override.get("runtime_arguments") == [] and override.get("post_publish_arguments") == [])
    check("expected_rows", [int(v) for v in (request.get("expected_rows") or [])] == EXPECTED_ROWS)

    owner_state = str(ownership.get("state") or "")
    owner_id = ownership.get("owner_page_session_id")
    ownership_safe_for_future_coordinator = owner_state == "UNCLAIMED" or (
        owner_state == "CLAIMED" and owner_id in {
            "chatgpt-height-difference-3-batch137-20260726",
            "chatgpt-height-difference-3-batch138-20260726",
        }
    )
    check("ownership_not_conflicting", ownership_safe_for_future_coordinator, {"state": owner_state, "owner": owner_id})

    already_aligned = queue.get("script_path") == CANONICAL_SCRIPT
    payload = {
        "schema_version": 4,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION,
        "status": "ALREADY_ALIGNED" if already_aligned else "SAFE_FOR_COORDINATOR_RUNTIME_REWIRE_AFTER_ALL_PREFLIGHT_GATES",
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "branch": BRANCH,
        "explicit_fetch_refspec": fetch_spec,
        "local_head": local_head,
        "fresh_remote_head": remote_head,
        "local_task_tree_blob_sha": local_task_blob,
        "remote_task_blob_sha": remote_task_blob,
        "local_queue_tree_blob_sha": local_queue_blob,
        "remote_queue_blob_sha": remote_queue_blob,
        "critical_blob_parity": critical_blob_rows,
        "critical_worktree_clean": True,
        "windows_line_ending_safe_tree_blob_validation": True,
        "expected_read_path_count": EXPECTED_READ_PATH_COUNT,
        "expected_output_count": EXPECTED_OUTPUT_COUNT,
        "runtime_executable_identity_chain_pinned": True,
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
    print(json.dumps({"ok": True, "status": payload["status"], "checks": len(checks), "remote_head": remote_head, "output": str(output_path)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

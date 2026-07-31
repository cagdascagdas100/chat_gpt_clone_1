#!/usr/bin/env python3
"""Bootstrap coordinator wiring validation from a fresh origin using portable Git."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

BRANCH = "codex/aays-single-runner-v5-20260706"
TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
ATTEMPT_ID = "height-difference-3-20260721-011"
IDEMPOTENCY = "height_difference_3:canonical_security_stream:hmlr_ea_terrain50:v1"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
TASK_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
REQUEST_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json"
QUEUE_REL = "docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json"
VALIDATOR_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/041_validate_batch134_coordinator_wiring_request.py"
CRITICAL = [
    REQUEST_REL,
    TASK_REL,
    QUEUE_REL,
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/032_run_batch129_range_extract_and_prepare12.ps1",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/033_run_batch130_prepare12_strict_measurement_chain.ps1",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/036_run_batch131_strict12_with_local_acceptance.ps1",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/037_prepare_batch132_publish_manifest.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/038_verify_batch132_origin_remote_readback.ps1",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py",
    VALIDATOR_REL,
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/042_run_batch135_fresh_origin_wiring_preflight.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/043_run_batch136_exact_branch_head_and_dependency_preflight.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/044_run_batch137_runtime_environment_preflight.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/045_run_batch140_fresh_runner_heartbeat_gate.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/046_validate_batch141_coordinator_rewire_receipt.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/047_generate_batch142_coordinator_rewire_receipt.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/072_batch134_coordinator_wiring_request.json",
    "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/073_batch135_fresh_origin_coordinator_preflight.json",
    "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/074_batch136_exact_branch_head_coordinator_preflight.json",
    "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/075_batch137_runtime_environment_coordinator_preflight.json",
    "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/076_batch138_runtime_executable_identity_resume.json",
    "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/077_batch139_remote_history_binding_resume.json",
    "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/078_batch140_fresh_heartbeat_ttl_and_commit_delta_resume.json",
    "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/079_batch141_coordinator_receipt_duplicate_census_and_entry_origin_resume.json",
    "docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/080_batch142_deterministic_receipt_generator_and_seal_resume.json",
]
OUTPUT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/037_batch135_fresh_origin_wiring_qa/fresh_origin_wiring_preflight_runtime.json"


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


def git(executable: str, repo: Path, *args: str) -> str:
    proc = subprocess.run([executable, "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr[-1600:]}")
    return proc.stdout.strip()


def blob(executable: str, repo: Path, ref: str, rel: str) -> str:
    value = git(executable, repo, "rev-parse", f"{ref}:{rel}").lower()
    if len(value) != 40:
        raise ValueError(f"invalid blob {ref}:{rel}: {value!r}")
    return value


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def identity(label: str, value: dict[str, Any]) -> None:
    expected = {
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "idempotency_key": IDEMPOTENCY,
        "continuation_key": CONTINUATION,
    }
    for field, wanted in expected.items():
        if value.get(field) != wanted:
            raise ValueError(f"{label} {field} mismatch")


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


def capture(executable: str, repo: Path, ref: str) -> dict[str, str]:
    return {rel: blob(executable, repo, ref, rel) for rel in CRITICAL}


def main() -> int:
    repo = root(Path(__file__).resolve())
    git_exe = resolve_git()
    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    git(git_exe, repo, "fetch", "--no-tags", "origin", fetch_spec)
    remote_ref = f"refs/remotes/origin/{BRANCH}"
    remote_head_before = git(git_exe, repo, "rev-parse", remote_ref)
    local_head_before = git(git_exe, repo, "rev-parse", "HEAD")
    if local_head_before != remote_head_before:
        raise RuntimeError(f"LOCAL_HEAD_NOT_FRESH_ORIGIN:{local_head_before}:{remote_head_before}")

    task = load(repo / TASK_REL)
    request = load(repo / REQUEST_REL)
    queue = load(repo / QUEUE_REL)
    identity("task", task)
    identity("request", request)
    if queue.get("task_id") != TASK_ID or queue.get("attempt_id") != ATTEMPT_ID or queue.get("idempotency_key") != IDEMPOTENCY:
        raise ValueError("queue identity mismatch")

    local_blobs_before = capture(git_exe, repo, "HEAD")
    remote_blobs_before = capture(git_exe, repo, remote_head_before)
    if local_blobs_before != remote_blobs_before:
        raise RuntimeError("CRITICAL_LOCAL_HEAD_REMOTE_BLOB_MISMATCH")
    status_before = git(git_exe, repo, "status", "--porcelain", "--untracked-files=no", "--", *CRITICAL)
    if status_before:
        raise RuntimeError(f"CRITICAL_WORKTREE_DIRTY_BEFORE:{status_before[-4000:]}")

    validator = repo / VALIDATOR_REL
    env = os.environ.copy()
    env["AAYS_GIT_EXE"] = git_exe
    proc = subprocess.run([sys.executable, str(validator)], cwd=repo, env=env, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"WIRING_VALIDATOR_FAILED:{proc.returncode}:{proc.stderr[-2000:]}")

    git(git_exe, repo, "fetch", "--no-tags", "origin", fetch_spec)
    remote_head_after = git(git_exe, repo, "rev-parse", remote_ref)
    local_head_after = git(git_exe, repo, "rev-parse", "HEAD")
    if local_head_after != local_head_before or remote_head_after != remote_head_before or local_head_after != remote_head_after:
        raise RuntimeError(f"HEAD_OR_REMOTE_DRIFT_DURING_VALIDATOR:{local_head_before}:{local_head_after}:{remote_head_before}:{remote_head_after}")
    local_blobs_after = capture(git_exe, repo, "HEAD")
    remote_blobs_after = capture(git_exe, repo, remote_head_after)
    if local_blobs_after != local_blobs_before or remote_blobs_after != remote_blobs_before or local_blobs_after != remote_blobs_after:
        raise RuntimeError("CRITICAL_BLOB_DRIFT_DURING_VALIDATOR")
    status_after = git(git_exe, repo, "status", "--porcelain", "--untracked-files=no", "--", *CRITICAL)
    if status_after:
        raise RuntimeError(f"CRITICAL_WORKTREE_DIRTY_AFTER:{status_after[-4000:]}")

    rows = [
        {
            "path": rel,
            "local_head_blob_before": local_blobs_before[rel],
            "remote_blob_before": remote_blobs_before[rel],
            "local_head_blob_after": local_blobs_after[rel],
            "remote_blob_after": remote_blobs_after[rel],
            "passed": True,
        }
        for rel in CRITICAL
    ]
    payload = {
        "schema_version": 3,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "idempotency_key": IDEMPOTENCY,
        "continuation_key": CONTINUATION,
        "canonical_branch": BRANCH,
        "explicit_fetch_refspec": fetch_spec,
        "local_head_before": local_head_before,
        "fresh_remote_head_before": remote_head_before,
        "local_head_after": local_head_after,
        "fresh_remote_head_after": remote_head_after,
        "head_and_remote_stable_during_validator": True,
        "critical_file_count": len(rows),
        "critical_blob_parity": rows,
        "critical_blob_map_stable_during_validator": True,
        "critical_worktree_clean_before": True,
        "critical_worktree_clean_after": True,
        "portable_git_executable": git_exe,
        "portable_git_contract_passed": True,
        "validator_041_executed": True,
        "validator_exit_code": proc.returncode,
        "validator_stdout_tail": proc.stdout[-4000:],
        "coordinator_action_performed": False,
        "queue_mutated": False,
        "runner_started": False,
        "numeric_values_written": 0,
        "atomic_output_materialization": True,
        "final_ready": False,
        "fake_data": False,
    }
    output = repo / OUTPUT_REL
    atomic_json(output, payload)
    print(json.dumps({"ok": True, "head": local_head_after, "critical_files": len(rows), "output": str(output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

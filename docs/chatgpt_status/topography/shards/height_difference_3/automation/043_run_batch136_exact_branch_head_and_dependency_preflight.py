#!/usr/bin/env python3
"""Fail-closed exact branch/HEAD and tracked-input preflight using portable Git."""
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
TASK_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
HEARTBEAT_GATE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/045_run_batch140_fresh_runner_heartbeat_gate.py"
OUTPUT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/039_batch136_exact_head_preflight/exact_branch_head_and_dependency_preflight_runtime.json"
TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
ATTEMPT_ID = "height-difference-3-20260721-011"
IDEMPOTENCY = "height_difference_3:canonical_security_stream:hmlr_ea_terrain50:v1"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
EXPECTED_READ_PATH_COUNT = 57
EXPECTED_OUTPUT_COUNT = 22
DIRECTORY_SNAPSHOT_READS = {
    "docs/chatgpt_status/_shared/slots_21/height_difference_3",
    "docs/chatgpt_status/topography/queue",
}
VOLATILE_FILE_READS = {
    "docs/chatgpt_status/_shared/slots_21/height_difference_3/heartbeat_latest.json",
    "docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json",
}
SNAPSHOT_ONLY_READS = DIRECTORY_SNAPSHOT_READS | VOLATILE_FILE_READS


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


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def blob(executable: str, repo: Path, ref: str, rel: str) -> str:
    value = git(executable, repo, "rev-parse", f"{ref}:{rel}").lower()
    if len(value) != 40:
        raise ValueError(f"invalid blob {ref}:{rel}: {value!r}")
    return value


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
    branch = git(git_exe, repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch != BRANCH:
        raise RuntimeError(f"WRONG_OR_DETACHED_BRANCH:{branch!r}:expected={BRANCH}")
    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    remote_ref = f"refs/remotes/origin/{BRANCH}"
    git(git_exe, repo, "fetch", "--no-tags", "origin", fetch_spec)
    remote_before = git(git_exe, repo, "rev-parse", remote_ref)
    local_before = git(git_exe, repo, "rev-parse", "HEAD")
    if local_before != remote_before:
        raise RuntimeError(f"LOCAL_HEAD_NOT_FRESH_ORIGIN:{local_before}:{remote_before}")

    task = load(repo / TASK_REL)
    expected_identity = {
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "idempotency_key": IDEMPOTENCY,
        "continuation_key": CONTINUATION,
    }
    for field, wanted in expected_identity.items():
        if task.get(field) != wanted:
            raise ValueError(f"current task {field} mismatch")
    reads = [str(value) for value in task.get("read_paths") or []]
    outputs = [str(value) for value in task.get("expected_outputs") or []]
    if len(reads) != EXPECTED_READ_PATH_COUNT:
        raise ValueError(f"expected {EXPECTED_READ_PATH_COUNT} read paths, got {len(reads)}")
    if len(outputs) != EXPECTED_OUTPUT_COUNT:
        raise ValueError(f"expected {EXPECTED_OUTPUT_COUNT} outputs, got {len(outputs)}")
    if len(set(reads)) != len(reads) or len(set(outputs)) != len(outputs):
        raise ValueError("duplicate task path")
    if not SNAPSHOT_ONLY_READS.issubset(set(reads)):
        raise ValueError("snapshot-only read paths missing from canonical task")

    tracked: list[dict[str, Any]] = []
    for rel in reads:
        proc = subprocess.run([git_exe, "-C", str(repo), "cat-file", "-e", f"HEAD:{rel}"], text=True, capture_output=True, check=False)
        if proc.returncode:
            raise RuntimeError(f"UNTRACKED_OR_MISSING_READ_PATH:{rel}:{proc.stderr[-600:]}")
        tracked.append({
            "path": rel,
            "tracked_at_head": True,
            "directory_snapshot": rel in DIRECTORY_SNAPSHOT_READS,
            "volatile_file_snapshot": rel in VOLATILE_FILE_READS,
            "snapshot_only_worktree_clean_exempt": rel in SNAPSHOT_ONLY_READS,
        })
    task_blob_before = blob(git_exe, repo, "HEAD", TASK_REL)
    clean_targets = [rel for rel in reads if rel not in SNAPSHOT_ONLY_READS]
    if TASK_REL not in clean_targets:
        clean_targets.append(TASK_REL)
    if len(set(clean_targets)) != len(clean_targets):
        raise ValueError("duplicate clean target")
    status_before = git(git_exe, repo, "status", "--porcelain", "--untracked-files=no", "--", *clean_targets)
    if status_before:
        raise RuntimeError(f"TASK_READ_PATH_WORKTREE_DIRTY_BEFORE:{status_before[-4000:]}")

    gate = repo / HEARTBEAT_GATE_REL
    if not gate.is_file():
        raise FileNotFoundError(gate)
    env = os.environ.copy()
    env["AAYS_GIT_EXE"] = git_exe
    proc = subprocess.run([sys.executable, str(gate)], cwd=repo, env=env, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"BATCH142_FRESH_HEARTBEAT_GATE_FAILED:{proc.returncode}:{proc.stderr[-3000:]}")

    git(git_exe, repo, "fetch", "--no-tags", "origin", fetch_spec)
    remote_after = git(git_exe, repo, "rev-parse", remote_ref)
    local_after = git(git_exe, repo, "rev-parse", "HEAD")
    if local_after != local_before or remote_after != remote_before or local_after != remote_after:
        raise RuntimeError(f"HEAD_OR_REMOTE_DRIFT_DURING_HEARTBEAT_CHAIN:{local_before}:{local_after}:{remote_before}:{remote_after}")
    task_blob_after = blob(git_exe, repo, "HEAD", TASK_REL)
    if task_blob_after != task_blob_before:
        raise RuntimeError(f"CURRENT_TASK_BLOB_DRIFT_DURING_HEARTBEAT_CHAIN:{task_blob_before}:{task_blob_after}")
    status_after = git(git_exe, repo, "status", "--porcelain", "--untracked-files=no", "--", *clean_targets)
    if status_after:
        raise RuntimeError(f"TASK_READ_PATH_WORKTREE_DIRTY_AFTER:{status_after[-4000:]}")

    payload = {
        "schema_version": 11,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "idempotency_key": IDEMPOTENCY,
        "continuation_key": CONTINUATION,
        "canonical_branch": BRANCH,
        "symbolic_branch_verified": True,
        "explicit_fetch_refspec": fetch_spec,
        "local_head_before": local_before,
        "fresh_remote_head_before": remote_before,
        "local_head_after": local_after,
        "fresh_remote_head_after": remote_after,
        "exact_head_parity_before": True,
        "exact_head_parity_after": True,
        "head_and_remote_stable_during_heartbeat_chain": True,
        "current_task_blob_before": task_blob_before,
        "current_task_blob_after": task_blob_after,
        "current_task_blob_stable_during_heartbeat_chain": True,
        "current_task_read_path_count": len(reads),
        "current_task_expected_output_count": len(outputs),
        "generated_expected_outputs_not_required_at_head": True,
        "all_read_paths_tracked_at_head": True,
        "directory_snapshot_read_paths": sorted(DIRECTORY_SNAPSHOT_READS),
        "volatile_file_snapshot_read_paths": sorted(VOLATILE_FILE_READS),
        "snapshot_only_read_paths": sorted(SNAPSHOT_ONLY_READS),
        "snapshot_only_worktree_clean_exempt": True,
        "current_task_explicit_worktree_clean_required": True,
        "non_snapshot_read_path_worktree_clean_before": True,
        "non_snapshot_read_path_worktree_clean_after": True,
        "read_path_rows": tracked,
        "portable_git_executable": git_exe,
        "portable_git_contract_passed": True,
        "fresh_heartbeat_gate_045_executed": True,
        "fresh_heartbeat_gate_045_exit_code": proc.returncode,
        "fresh_heartbeat_gate_045_stdout_tail": proc.stdout[-4000:],
        "environment_gate_044_transitively_required": True,
        "deterministic_coordinator_receipt_generator_required": True,
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
    print(json.dumps({
        "ok": True,
        "head": local_after,
        "read_paths": len(reads),
        "outputs": len(outputs),
        "snapshot_only_reads": len(SNAPSHOT_ONLY_READS),
        "clean_targets": len(clean_targets),
        "output": str(output),
    }))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

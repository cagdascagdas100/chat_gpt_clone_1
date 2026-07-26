#!/usr/bin/env python3
"""Fail-closed exact-branch/HEAD preflight before the runtime environment gate.

This script does not mutate the legacy queue, start a runner, publish, or write
numeric measurements. It requires the runner checkout to be on the canonical
branch, fetches origin with an explicit refspec, requires local HEAD to equal the
fresh origin HEAD, verifies every canonical current-task read path is tracked and
clean, then invokes Batch137 environment gate 044 (which invokes 042 -> 041).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

BRANCH = "codex/aays-single-runner-v5-20260706"
TASK_REL = "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
ENV_GATE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/044_run_batch137_runtime_environment_preflight.py"
EXPECTED_TASK = "height_difference_3-canonical-api-measurement-20260721-01"
EXPECTED_CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
EXPECTED_READ_PATH_COUNT = 46


def root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr[-1600:]}")
    return proc.stdout.strip()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def main() -> int:
    repo = root(Path(__file__).resolve())
    branch = git(repo, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch != BRANCH:
        raise RuntimeError(f"WRONG_OR_DETACHED_BRANCH:{branch!r}:expected={BRANCH}")

    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    git(repo, "fetch", "--no-tags", "origin", fetch_spec)
    remote_ref = f"refs/remotes/origin/{BRANCH}"
    remote_head = git(repo, "rev-parse", remote_ref)
    local_head = git(repo, "rev-parse", "HEAD")
    if len(remote_head) != 40 or len(local_head) != 40:
        raise RuntimeError("INVALID_HEAD_SHA")
    if local_head != remote_head:
        raise RuntimeError(f"LOCAL_HEAD_NOT_FRESH_ORIGIN:{local_head}:{remote_head}")

    task = load(repo / TASK_REL)
    if task.get("task_id") != EXPECTED_TASK:
        raise ValueError("current task_id mismatch")
    if task.get("continuation_key") != EXPECTED_CONTINUATION:
        raise ValueError("current continuation_key mismatch")
    read_paths = [str(v) for v in (task.get("read_paths") or [])]
    if len(read_paths) != EXPECTED_READ_PATH_COUNT:
        raise ValueError(f"expected {EXPECTED_READ_PATH_COUNT} current-task read paths, got {len(read_paths)}")
    if len(set(read_paths)) != len(read_paths):
        raise ValueError("duplicate current-task read path")

    tracked_rows: list[dict[str, str | bool]] = []
    for rel in read_paths:
        proc = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"HEAD:{rel}"],
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"UNTRACKED_OR_MISSING_READ_PATH:{rel}:{proc.stderr[-600:]}")
        tracked_rows.append({"path": rel, "tracked_at_head": True})

    status = git(repo, "status", "--porcelain", "--untracked-files=no", "--", *read_paths)
    if status:
        raise RuntimeError(f"TASK_READ_PATH_WORKTREE_DIRTY:{status[-4000:]}")

    env_gate = repo / ENV_GATE_REL
    if not env_gate.is_file():
        raise FileNotFoundError(env_gate)
    proc = subprocess.run([sys.executable, str(env_gate)], cwd=repo, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"BATCH137_ENVIRONMENT_GATE_FAILED:{proc.stderr[-3000:]}")

    payload = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "canonical_branch": BRANCH,
        "symbolic_branch_verified": True,
        "explicit_fetch_refspec": fetch_spec,
        "local_head": local_head,
        "fresh_remote_head": remote_head,
        "exact_head_parity": True,
        "current_task_read_path_count": len(read_paths),
        "current_task_read_paths_unique": True,
        "all_read_paths_tracked_at_head": True,
        "read_path_rows": tracked_rows,
        "task_read_path_worktree_clean": True,
        "environment_gate_044_executed": True,
        "environment_gate_044_exit_code": proc.returncode,
        "environment_gate_044_stdout_tail": proc.stdout[-4000:],
        "coordinator_action_performed": False,
        "queue_mutated": False,
        "runner_started": False,
        "numeric_values_written": 0,
        "final_ready": False,
        "fake_data": False,
    }
    out = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/039_batch136_exact_head_preflight/exact_branch_head_and_dependency_preflight_runtime.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "head": local_head, "read_paths": len(read_paths), "output": str(out)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

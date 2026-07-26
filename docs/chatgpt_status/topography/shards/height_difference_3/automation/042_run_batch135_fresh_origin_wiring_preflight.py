#!/usr/bin/env python3
"""Bootstrap the Batch135 coordinator wiring validation from a fresh origin view.

This script performs no queue mutation, runner start, publish, or numeric write.
It explicitly fetches the canonical branch, requires critical local HEAD blobs to
match the fetched origin tree and a clean critical worktree, then invokes 041.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BRANCH = "codex/aays-single-runner-v5-20260706"
CRITICAL = [
    "docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json",
    "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json",
    "docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/041_validate_batch134_coordinator_wiring_request.py",
]


def root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND")


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr[-1200:]}")
    return proc.stdout.strip()


def blob(repo: Path, ref: str, rel: str) -> str:
    value = git(repo, "rev-parse", f"{ref}:{rel}").lower()
    if len(value) != 40:
        raise ValueError(f"invalid blob {ref}:{rel}: {value!r}")
    return value


def main() -> int:
    repo = root(Path(__file__).resolve())
    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    git(repo, "fetch", "--no-tags", "origin", fetch_spec)
    remote_ref = f"refs/remotes/origin/{BRANCH}"
    remote_head = git(repo, "rev-parse", remote_ref)
    local_head = git(repo, "rev-parse", "HEAD")

    rows = []
    for rel in CRITICAL:
        local_blob = blob(repo, "HEAD", rel)
        remote_blob = blob(repo, remote_head, rel)
        if local_blob != remote_blob:
            raise RuntimeError(f"CRITICAL_LOCAL_HEAD_STALE:{rel}:{local_blob}:{remote_blob}")
        rows.append({"path": rel, "local_head_blob": local_blob, "remote_blob": remote_blob, "passed": True})

    status = git(repo, "status", "--porcelain", "--untracked-files=no", "--", *CRITICAL)
    if status:
        raise RuntimeError(f"CRITICAL_WORKTREE_DIRTY:{status}")

    validator = repo / "docs/chatgpt_status/topography/shards/height_difference_3/automation/041_validate_batch134_coordinator_wiring_request.py"
    proc = subprocess.run([sys.executable, str(validator)], cwd=repo, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"WIRING_VALIDATOR_FAILED:{proc.stderr[-2000:]}")

    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "canonical_branch": BRANCH,
        "explicit_fetch_refspec": fetch_spec,
        "local_head": local_head,
        "fresh_remote_head": remote_head,
        "critical_file_count": len(rows),
        "critical_blob_parity": rows,
        "critical_worktree_clean": True,
        "validator_041_executed": True,
        "validator_exit_code": proc.returncode,
        "validator_stdout_tail": proc.stdout[-4000:],
        "coordinator_action_performed": False,
        "queue_mutated": False,
        "runner_started": False,
        "numeric_values_written": 0,
        "final_ready": False,
        "fake_data": False,
    }
    out = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/037_batch135_fresh_origin_wiring_qa/fresh_origin_wiring_preflight_runtime.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "remote_head": remote_head, "critical_files": len(rows), "output": str(out)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

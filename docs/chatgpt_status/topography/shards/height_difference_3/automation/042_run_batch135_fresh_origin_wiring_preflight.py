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
CRITICAL = [
    "docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json",
    "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json",
    "docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/041_validate_batch134_coordinator_wiring_request.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/046_validate_batch141_coordinator_rewire_receipt.py",
    "docs/chatgpt_status/topography/shards/height_difference_3/automation/047_generate_batch142_coordinator_rewire_receipt.py",
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
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr[-1200:]}")
    return proc.stdout.strip()


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
    fetch_spec = f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    git(git_exe, repo, "fetch", "--no-tags", "origin", fetch_spec)
    remote_ref = f"refs/remotes/origin/{BRANCH}"
    remote_head = git(git_exe, repo, "rev-parse", remote_ref)
    local_head = git(git_exe, repo, "rev-parse", "HEAD")
    if local_head != remote_head:
        raise RuntimeError(f"LOCAL_HEAD_NOT_FRESH_ORIGIN:{local_head}:{remote_head}")

    rows: list[dict[str, Any]] = []
    for rel in CRITICAL:
        local_blob = blob(git_exe, repo, "HEAD", rel)
        remote_blob = blob(git_exe, repo, remote_head, rel)
        if local_blob != remote_blob:
            raise RuntimeError(f"CRITICAL_LOCAL_HEAD_STALE:{rel}:{local_blob}:{remote_blob}")
        rows.append({"path": rel, "local_head_blob": local_blob, "remote_blob": remote_blob, "passed": True})
    status = git(git_exe, repo, "status", "--porcelain", "--untracked-files=no", "--", *CRITICAL)
    if status:
        raise RuntimeError(f"CRITICAL_WORKTREE_DIRTY:{status}")

    validator = repo / "docs/chatgpt_status/topography/shards/height_difference_3/automation/041_validate_batch134_coordinator_wiring_request.py"
    env = os.environ.copy()
    env["AAYS_GIT_EXE"] = git_exe
    proc = subprocess.run([sys.executable, str(validator)], cwd=repo, env=env, text=True, capture_output=True, check=False)
    if proc.returncode:
        raise RuntimeError(f"WIRING_VALIDATOR_FAILED:{proc.stderr[-2000:]}")

    payload = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "canonical_branch": BRANCH,
        "explicit_fetch_refspec": fetch_spec,
        "local_head": local_head,
        "fresh_remote_head": remote_head,
        "critical_file_count": len(rows),
        "critical_blob_parity": rows,
        "critical_worktree_clean": True,
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
    print(json.dumps({"ok": True, "remote_head": remote_head, "critical_files": len(rows), "output": str(output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

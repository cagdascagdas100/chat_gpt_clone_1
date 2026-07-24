#!/usr/bin/env python3
"""Safely fast-forward the existing F worktree to the fetched continuation branch.

The script never resets, rebases, force-checkouts, creates commits, or touches a
queue/lease/runner. It updates the current branch only when the worktree has no
tracked modifications and local HEAD is an ancestor of the freshly fetched
remote HEAD. Local-ahead, diverged, dirty, wrong-repository and wrong-branch
states fail closed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REMOTE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(repo: Path, *args: str, check: bool = True, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update({"GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never"})
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git {' '.join(args)} timed out after {timeout}s") from exc
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail[-4000:]}")
    return proc


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def normalize_repository_slug(value: str) -> str:
    slug = value.strip().strip("/")
    if slug.casefold().endswith(".git"):
        slug = slug[:-4]
    if not REPOSITORY_RE.fullmatch(slug):
        raise ValueError(f"invalid expected remote repository: {value!r}")
    return slug.casefold()


def repository_slug_from_remote_url(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError("remote URL is empty")
    if Path(raw).is_absolute():
        path = raw
    elif "://" not in raw and ":" in raw:
        _, path = raw.split(":", 1)
    else:
        parsed = urlparse(raw)
        if parsed.scheme not in {"https", "http", "ssh", "git", "file"}:
            raise ValueError("remote URL must be an HTTPS/SSH/file Git URL")
        if parsed.scheme != "file":
            host = (parsed.hostname or "").casefold()
            if host not in {"github.com", "www.github.com"}:
                raise ValueError(f"unexpected remote host: {host!r}")
        path = parsed.path
    slug = path.strip("/")
    if slug.casefold().endswith(".git"):
        slug = slug[:-4]
    parts = [part for part in slug.split("/") if part]
    if len(parts) >= 2:
        slug = "/".join(parts[-2:])
    return normalize_repository_slug(slug)


def validate_ref_component(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned or cleaned != value or ".." in cleaned or cleaned.startswith("-"):
        raise ValueError(f"unsafe {label}: {value!r}")
    return cleaned


def git_path_exists(repo: Path, name: str, timeout: int) -> bool:
    path = Path(run_git(repo, "rev-parse", "--git-path", name, timeout=timeout).stdout.strip())
    if not path.is_absolute():
        path = repo / path
    return path.exists()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--expected-branch", required=True)
    parser.add_argument("--remote-name", default="origin")
    parser.add_argument("--expected-remote-repository", default="cagdascagdas100/chat_gpt_clone_1")
    parser.add_argument("--git-timeout", type=int, default=120)
    parser.add_argument("--skip-fetch", action="store_true", help="Fixture-only: use existing remote-tracking ref")
    parser.add_argument("--allow-file-remote", action="store_true", help="Fixture-only: permit file:// remotes")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not 1 <= args.git_timeout <= 900:
        raise ValueError("git-timeout must be between 1 and 900 seconds")

    repo = args.repo_root.resolve()
    if not repo.is_dir():
        raise NotADirectoryError(repo)
    top = Path(run_git(repo, "rev-parse", "--show-toplevel", timeout=args.git_timeout).stdout.strip()).resolve()
    if top != repo:
        raise ValueError(f"repo root mismatch: {repo} != {top}")

    branch = validate_ref_component(args.expected_branch, "expected branch")
    remote_name = validate_ref_component(args.remote_name, "remote name")
    if not REMOTE_RE.fullmatch(remote_name):
        raise ValueError(f"invalid remote name: {remote_name!r}")
    if run_git(repo, "check-ref-format", "--branch", branch, check=False, timeout=args.git_timeout).returncode != 0:
        raise ValueError(f"invalid expected branch: {branch!r}")

    current_branch = run_git(repo, "branch", "--show-current", timeout=args.git_timeout).stdout.strip()
    if current_branch != branch:
        raise ValueError(f"branch mismatch: {current_branch!r} != {branch!r}")

    remote_url = run_git(repo, "remote", "get-url", remote_name, timeout=args.git_timeout).stdout.strip()
    parsed = urlparse(remote_url)
    if parsed.scheme == "file" and not args.allow_file_remote:
        raise ValueError("file remote is fixture-only")
    expected_repository = normalize_repository_slug(args.expected_remote_repository)
    remote_repository = repository_slug_from_remote_url(remote_url)
    if remote_repository != expected_repository:
        raise ValueError(f"remote repository mismatch: {remote_repository!r} != {expected_repository!r}")

    for state_name in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply"):
        if git_path_exists(repo, state_name, args.git_timeout):
            raise ValueError(f"Git operation already in progress: {state_name}")

    remote_ref = f"refs/remotes/{remote_name}/{branch}"
    if not args.skip_fetch:
        refspec = f"+refs/heads/{branch}:{remote_ref}"
        run_git(repo, "fetch", "--no-tags", "--prune", remote_name, refspec, timeout=args.git_timeout)

    before_head = run_git(repo, "rev-parse", "HEAD", timeout=args.git_timeout).stdout.strip()
    remote_head = run_git(repo, "rev-parse", f"{remote_ref}^{{commit}}", timeout=args.git_timeout).stdout.strip()
    tracked_dirty = run_git(repo, "status", "--porcelain=v1", "--untracked-files=no", timeout=args.git_timeout).stdout.strip()
    if tracked_dirty:
        raise ValueError(f"tracked worktree/index changes block safe fast-forward: {tracked_dirty[:4000]}")

    local_is_ancestor = run_git(repo, "merge-base", "--is-ancestor", before_head, remote_head, check=False, timeout=args.git_timeout).returncode == 0
    remote_is_ancestor = run_git(repo, "merge-base", "--is-ancestor", remote_head, before_head, check=False, timeout=args.git_timeout).returncode == 0
    if before_head == remote_head:
        action = "ALREADY_AT_FETCHED_REMOTE_HEAD"
        advanced_commit_count = 0
    elif local_is_ancestor:
        advanced_commit_count = int(run_git(repo, "rev-list", "--count", f"{before_head}..{remote_head}", timeout=args.git_timeout).stdout.strip())
        run_git(repo, "merge", "--ff-only", remote_ref, timeout=args.git_timeout)
        action = "FAST_FORWARDED_TO_FETCHED_REMOTE_HEAD"
    elif remote_is_ancestor:
        raise ValueError(f"local HEAD is ahead of fetched remote HEAD: {before_head} != {remote_head}")
    else:
        raise ValueError(f"local and fetched remote HEADs diverged: {before_head} != {remote_head}")

    after_head = run_git(repo, "rev-parse", "HEAD", timeout=args.git_timeout).stdout.strip()
    if after_head != remote_head:
        raise ValueError(f"post-sync HEAD mismatch: {after_head} != {remote_head}")
    if run_git(repo, "status", "--porcelain=v1", "--untracked-files=no", timeout=args.git_timeout).stdout.strip():
        raise ValueError("tracked worktree/index became dirty after fast-forward")

    untracked = [line for line in run_git(repo, "status", "--porcelain=v1", "--untracked-files=normal", timeout=args.git_timeout).stdout.splitlines() if line.startswith("?? ")]
    report = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "updated_at": now(),
        "status": "EXISTING_F_WORKTREE_FAST_FORWARD_SYNC_VERIFIED",
        "action": action,
        "repo_root": str(repo),
        "branch": current_branch,
        "remote_name": remote_name,
        "remote_repository": remote_repository,
        "remote_ref": remote_ref,
        "remote_fetch_performed": not args.skip_fetch,
        "before_head": before_head,
        "remote_head": remote_head,
        "after_head": after_head,
        "advanced_commit_count": advanced_commit_count,
        "local_head_equals_remote_head": True,
        "tracked_worktree_clean_before_and_after": True,
        "untracked_file_count": len(untracked),
        "untracked_files_not_modified": True,
        "sync_policy": "FETCH_EXACT_BRANCH_THEN_FAST_FORWARD_ONLY_IF_CLEAN_AND_LOCAL_IS_ANCESTOR",
        "reset_used": False,
        "rebase_used": False,
        "force_checkout_used": False,
        "commit_created": False,
        "single_shared_runner_only": True,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_submission": False,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    atomic_json(args.output.resolve(), report)
    print(json.dumps({"ok": True, "status": report["status"], "action": action, "before_head": before_head, "after_head": after_head, "remote_head": remote_head, "output": str(args.output.resolve())}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

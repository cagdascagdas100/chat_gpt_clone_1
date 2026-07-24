#!/usr/bin/env python3
"""Fail-closed Git worktree and remote-head verification for the existing F runner."""
from __future__ import annotations

import argparse
import hashlib
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
        proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=False, timeout=timeout, env=env)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git {' '.join(args)} timed out after {timeout}s") from exc
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail[-4000:]}")
    return proc


def git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()  # nosec - Git object identity, not a security digest
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    if "://" not in raw and ":" in raw:
        _, path = raw.split(":", 1)
    else:
        parsed = urlparse(raw)
        if parsed.scheme not in {"https", "http", "ssh", "git"}:
            raise ValueError("remote URL must be an HTTPS/SSH Git URL")
        host = (parsed.hostname or "").casefold()
        if host not in {"github.com", "www.github.com"}:
            raise ValueError(f"unexpected remote host: {host!r}")
        path = parsed.path
    slug = path.strip("/")
    if slug.casefold().endswith(".git"):
        slug = slug[:-4]
    return normalize_repository_slug(slug)


def validate_ref_component(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned or cleaned != value or ".." in cleaned or cleaned.startswith("-"):
        raise ValueError(f"unsafe {label}: {value!r}")
    return cleaned


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--expected-branch", required=True)
    parser.add_argument("--minimum-commit", required=True)
    parser.add_argument("--remote-name", default="origin")
    parser.add_argument("--expected-remote-repository", default="cagdascagdas100/chat_gpt_clone_1")
    parser.add_argument("--skip-fetch", action="store_true", help="Fixture-only: use the existing remote-tracking ref")
    parser.add_argument("--git-timeout", type=int, default=120)
    parser.add_argument("--required-file", action="append", default=[])
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
    ref_check = run_git(repo, "check-ref-format", "--branch", branch, check=False, timeout=args.git_timeout)
    if ref_check.returncode != 0:
        raise ValueError(f"invalid expected branch: {branch!r}")

    current_branch = run_git(repo, "branch", "--show-current", timeout=args.git_timeout).stdout.strip()
    if not current_branch or current_branch != branch:
        raise ValueError(f"branch mismatch: {current_branch!r} != {branch!r}")

    expected_repository = normalize_repository_slug(args.expected_remote_repository)
    remote_url = run_git(repo, "remote", "get-url", remote_name, timeout=args.git_timeout).stdout.strip()
    remote_repository = repository_slug_from_remote_url(remote_url)
    if remote_repository != expected_repository:
        raise ValueError(f"remote repository mismatch: {remote_repository!r} != {expected_repository!r}")

    remote_ref = f"refs/remotes/{remote_name}/{branch}"
    if not args.skip_fetch:
        refspec = f"+refs/heads/{branch}:{remote_ref}"
        run_git(repo, "fetch", "--no-tags", "--prune", remote_name, refspec, timeout=args.git_timeout)

    head = run_git(repo, "rev-parse", "HEAD", timeout=args.git_timeout).stdout.strip()
    remote_head = run_git(repo, "rev-parse", f"{remote_ref}^{{commit}}", timeout=args.git_timeout).stdout.strip()
    if head != remote_head:
        raise ValueError(f"local HEAD is not the fetched remote branch HEAD: {head} != {remote_head}")

    minimum = run_git(repo, "rev-parse", f"{args.minimum_commit}^{{commit}}", timeout=args.git_timeout).stdout.strip()
    ancestor = run_git(repo, "merge-base", "--is-ancestor", minimum, head, check=False, timeout=args.git_timeout)
    if ancestor.returncode != 0:
        raise ValueError(f"HEAD {head} does not contain minimum commit {minimum}")

    required = []
    seen: set[str] = set()
    for raw in args.required_file:
        rel = Path(raw)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"required-file must be a safe repo-relative path: {raw}")
        key = rel.as_posix()
        if key in seen:
            raise ValueError(f"duplicate required-file: {key}")
        seen.add(key)
        path = repo / rel
        if not path.is_file():
            raise FileNotFoundError(path)
        head_blob = run_git(repo, "rev-parse", f"HEAD:{key}", timeout=args.git_timeout).stdout.strip()
        worktree_blob = git_blob_sha1(path)
        if worktree_blob != head_blob:
            raise ValueError(f"worktree blob differs from HEAD for {key}: {worktree_blob} != {head_blob}")
        status = run_git(repo, "status", "--porcelain=v1", "--", key, timeout=args.git_timeout).stdout.strip()
        if status:
            raise ValueError(f"required pipeline file is dirty: {key}: {status}")
        required.append({"path": key, "head_blob_sha1": head_blob, "worktree_blob_sha1": worktree_blob, "clean": True})

    report = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "updated_at": now(),
        "status": "EXISTING_F_WORKTREE_AND_REMOTE_HEAD_VERIFIED",
        "repo_root": str(repo),
        "branch": current_branch,
        "head": head,
        "remote_name": remote_name,
        "remote_repository": remote_repository,
        "remote_ref": remote_ref,
        "remote_head": remote_head,
        "remote_fetch_performed": not args.skip_fetch,
        "local_head_equals_remote_head": True,
        "minimum_commit": minimum,
        "minimum_commit_is_ancestor": True,
        "required_file_count": len(required),
        "required_files": required,
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
    print(json.dumps({"ok": True, "status": report["status"], "head": head, "remote_head": remote_head, "files": len(required), "output": str(args.output.resolve())}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

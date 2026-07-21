#!/usr/bin/env python3
"""Fail-closed Git worktree verification for the existing F portable runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc


def git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()  # nosec - Git object identity
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--expected-branch", required=True)
    parser.add_argument("--minimum-commit", required=True)
    parser.add_argument("--required-file", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    if not repo.is_dir():
        raise NotADirectoryError(repo)
    top = Path(run_git(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if top != repo:
        raise ValueError(f"repo root mismatch: {repo} != {top}")
    branch = run_git(repo, "branch", "--show-current").stdout.strip()
    if not branch or branch != args.expected_branch:
        raise ValueError(f"branch mismatch: {branch!r} != {args.expected_branch!r}")
    head = run_git(repo, "rev-parse", "HEAD").stdout.strip()
    minimum = run_git(repo, "rev-parse", f"{args.minimum_commit}^{{commit}}").stdout.strip()
    ancestor = run_git(repo, "merge-base", "--is-ancestor", minimum, head, check=False)
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
        head_blob = run_git(repo, "rev-parse", f"HEAD:{key}").stdout.strip()
        worktree_blob = git_blob_sha1(path)
        if worktree_blob != head_blob:
            raise ValueError(f"worktree blob differs from HEAD for {key}: {worktree_blob} != {head_blob}")
        status = run_git(repo, "status", "--porcelain=v1", "--", key).stdout.strip()
        if status:
            raise ValueError(f"required pipeline file is dirty: {key}: {status}")
        required.append({"path": key, "head_blob_sha1": head_blob, "worktree_blob_sha1": worktree_blob, "clean": True})

    report = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "updated_at": now(),
        "status": "EXISTING_F_WORKTREE_VERIFIED",
        "repo_root": str(repo),
        "branch": branch,
        "head": head,
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
    print(json.dumps({"ok": True, "status": report["status"], "head": head, "files": len(required), "output": str(args.output.resolve())}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

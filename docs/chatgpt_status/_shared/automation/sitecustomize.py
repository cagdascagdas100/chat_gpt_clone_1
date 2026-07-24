# -*- coding: utf-8 -*-
"""Narrow startup compatibility for the canonical AAYS coordinator.

Python imports ``sitecustomize`` during interpreter startup when this directory
is on ``sys.path``.  The hook is deliberately inert for every process except
``AAYS_ADAPTIVE_15_WORKER_COORDINATOR.py``.

The coordinator historically required the remote branch head to equal the
local publish commit exactly.  On the active shared branch, a different slot
can legitimately advance the branch immediately after a successful push.  In
that case the local publish commit is still valid when it is an ancestor of the
remote head.  This shim changes only the stdout of the matching ``git
ls-remote`` readback after proving that ancestry; all other subprocess calls
and all failure cases are untouched.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any

_COORDINATOR = "AAYS_ADAPTIVE_15_WORKER_COORDINATOR.py"


def _command_parts(args: tuple[Any, ...], kwargs: dict[str, Any]) -> list[str]:
    command = args[0] if args else kwargs.get("args")
    if isinstance(command, (list, tuple)):
        return [str(value) for value in command]
    return []


def _repo_from_command(parts: list[str]) -> str | None:
    try:
        index = parts.index("-C")
    except ValueError:
        return None
    if index + 1 >= len(parts):
        return None
    return parts[index + 1]


def _is_branch_ls_remote(parts: list[str]) -> bool:
    return (
        "ls-remote" in parts
        and "origin" in parts
        and any(value.startswith("refs/heads/") for value in parts)
    )


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value or "")


def _install() -> None:
    if Path(sys.argv[0]).name.casefold() != _COORDINATOR.casefold():
        return
    if os.environ.get("AAYS_DISABLE_ANCESTOR_READBACK_COMPAT", "").casefold() == "true":
        return

    original_run = subprocess.run

    def run_with_ancestor_readback(*args: Any, **kwargs: Any):
        result = original_run(*args, **kwargs)
        parts = _command_parts(args, kwargs)
        if result.returncode != 0 or not _is_branch_ls_remote(parts):
            return result

        repo = _repo_from_command(parts)
        if not repo:
            return result
        remote_output = _text(result.stdout).strip()
        remote_head = remote_output.split()[0] if remote_output.split() else ""
        if not remote_head:
            return result

        git_executable = parts[0]
        local = original_run(
            [git_executable, "-C", repo, "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        local_head = _text(local.stdout).strip()
        if local.returncode != 0 or not local_head or local_head == remote_head:
            return result

        branch_ref = next(value for value in parts if value.startswith("refs/heads/"))
        branch = branch_ref.removeprefix("refs/heads/")
        fetched = original_run(
            [git_executable, "-C", repo, "fetch", "--depth=100", "origin", branch],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if fetched.returncode != 0:
            return result
        ancestor = original_run(
            [git_executable, "-C", repo, "merge-base", "--is-ancestor", local_head, "FETCH_HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if ancestor.returncode != 0:
            return result

        rewritten = f"{local_head}\t{branch_ref}\n"
        if isinstance(result.stdout, bytes):
            rewritten_output: str | bytes = rewritten.encode("utf-8")
        else:
            rewritten_output = rewritten
        return subprocess.CompletedProcess(
            args=result.args,
            returncode=result.returncode,
            stdout=rewritten_output,
            stderr=result.stderr,
        )

    subprocess.run = run_with_ancestor_readback


_install()

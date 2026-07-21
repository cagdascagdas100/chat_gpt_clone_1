#!/usr/bin/env python3
"""Safely synchronize, audit control state, then execute the existing full pipeline.

This wrapper never creates or mutates a claim, queue item, lease, owner,
heartbeat, task, runner, or parallel runner. It re-executes itself from the
freshly fast-forwarded worktree before auditing and invoking 032.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_3"
SYNC_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/035_sync_existing_f_worktree_ff_only.py"
AUDIT_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/036_audit_existing_runner_control_plane.py"
WRAPPER_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/037_audit_control_then_run_full_pipeline.py"
PIPELINE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/032_run_full_pipeline_and_website_acceptance.py"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def run(command: list[str], cwd: Path | None = None) -> dict[str, Any]:
    started = now()
    proc = subprocess.run(command, text=True, capture_output=True, check=False, cwd=str(cwd) if cwd else None)
    return {
        "started_at": started,
        "finished_at": now(),
        "command": command,
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-16000:],
        "stderr_tail": proc.stderr[-16000:],
    }


def git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()  # nosec - Git blob identity
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_head_file(repo: Path, rel: str) -> dict[str, Any]:
    path = repo / rel
    if not path.is_file():
        raise FileNotFoundError(path)
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", f"HEAD:{rel}"], text=True, capture_output=True, check=False)
    if head.returncode != 0:
        raise RuntimeError(head.stderr.strip() or head.stdout.strip())
    expected = head.stdout.strip()
    actual = git_blob_sha1(path)
    if actual != expected:
        raise ValueError(f"worktree file differs from HEAD: {rel}: {actual} != {expected}")
    dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain=v1", "--", rel], text=True, capture_output=True, check=False)
    if dirty.returncode != 0:
        raise RuntimeError(dirty.stderr.strip() or dirty.stdout.strip())
    if dirty.stdout.strip():
        raise ValueError(f"required audited entrypoint is dirty: {rel}: {dirty.stdout.strip()}")
    return {"path": rel, "head_blob_sha1": expected, "worktree_blob_sha1": actual, "clean": True}


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--expected-branch", required=True)
    parser.add_argument("--remote-name", default="origin")
    parser.add_argument("--expected-remote-repository", required=True)
    parser.add_argument("--git-timeout", type=int, default=120)
    parser.add_argument("--slot-root", required=True, type=Path)
    parser.add_argument("--task-contract", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--sync-output", required=True, type=Path)
    parser.add_argument("--audit-output", required=True, type=Path)
    parser.add_argument("--execution-report", required=True, type=Path)
    parser.add_argument("--post-sync", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("pipeline_command", nargs=argparse.REMAINDER)
    return parser.parse_args()


def normalized_pipeline(command: list[str]) -> list[str]:
    value = list(command)
    if value and value[0] == "--":
        value = value[1:]
    if len(value) < 2 or value[0] != "python" or value[1] != PIPELINE_REL:
        raise ValueError("pipeline command must explicitly invoke the approved 032 entrypoint")
    value[0] = sys.executable
    return value


def child_args(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable, str(args.repo_root.resolve() / WRAPPER_REL),
        "--repo-root", str(args.repo_root.resolve()),
        "--expected-branch", args.expected_branch,
        "--remote-name", args.remote_name,
        "--expected-remote-repository", args.expected_remote_repository,
        "--git-timeout", str(args.git_timeout),
        "--slot-root", str(args.slot_root.resolve()),
        "--task-contract", str(args.task_contract.resolve()),
        "--runtime", str(args.runtime.resolve()),
        "--sync-output", str(args.sync_output.resolve()),
        "--audit-output", str(args.audit_output.resolve()),
        "--execution-report", str(args.execution_report.resolve()),
        "--post-sync", "--",
    ]
    command.extend(args.pipeline_command[1:] if args.pipeline_command and args.pipeline_command[0] == "--" else args.pipeline_command)
    return command


def initial_report() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "updated_at": now(),
        "status": "SAFE_SYNC_035_STARTING",
        "worktree_sync": None,
        "entrypoint_integrity": None,
        "control_plane_audit": None,
        "pipeline": None,
        "single_shared_runner_only": True,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_submission": False,
        "lease_creation": False,
        "claim_created": False,
        "task_assigned_by_wrapper": False,
        "owner_assigned_by_wrapper": False,
        "heartbeat_written_by_wrapper": False,
        "final_ready": False,
        "product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def main() -> int:
    args = parse()
    if not 1 <= args.git_timeout <= 900:
        raise ValueError("git-timeout must be between 1 and 900 seconds")
    repo = args.repo_root.resolve()
    report_path = args.execution_report.resolve()
    pipeline = normalized_pipeline(args.pipeline_command)

    if not args.post_sync:
        report = initial_report()
        atomic_json(report_path, report)
        sync_script = repo / SYNC_REL
        if not sync_script.is_file():
            raise FileNotFoundError(sync_script)
        sync = [
            sys.executable, str(sync_script),
            "--repo-root", str(repo),
            "--expected-branch", args.expected_branch,
            "--remote-name", args.remote_name,
            "--expected-remote-repository", args.expected_remote_repository,
            "--git-timeout", str(args.git_timeout),
            "--output", str(args.sync_output.resolve()),
        ]
        report["worktree_sync"] = run(sync, cwd=repo)
        report["updated_at"] = now()
        if report["worktree_sync"]["exit_code"] != 0:
            report["status"] = "BLOCKED_SAFE_SYNC_035"
            atomic_json(report_path, report)
            return int(report["worktree_sync"]["exit_code"])
        report["status"] = "REEXECUTING_FRESH_037_AFTER_SYNC"
        atomic_json(report_path, report)
        child = subprocess.run(child_args(args), text=True, capture_output=True, check=False, cwd=str(repo))
        if child.returncode != 0 and report_path.is_file():
            value = json.loads(report_path.read_text(encoding="utf-8"))
            value["reexec_stderr_tail"] = child.stderr[-16000:]
            value["reexec_stdout_tail"] = child.stdout[-16000:]
            value["updated_at"] = now()
            atomic_json(report_path, value)
        return int(child.returncode)

    report = initial_report()
    report["status"] = "FRESH_ENTRYPOINT_INTEGRITY_CHECK"
    if args.sync_output.is_file():
        report["worktree_sync"] = json.loads(args.sync_output.read_text(encoding="utf-8"))
    task_rel = args.task_contract.resolve().relative_to(repo).as_posix()
    integrity = [verify_head_file(repo, AUDIT_REL), verify_head_file(repo, WRAPPER_REL), verify_head_file(repo, task_rel)]
    report["entrypoint_integrity"] = {"status": "AUDIT_WRAPPER_AND_TASK_MATCH_HEAD", "files": integrity}
    atomic_json(report_path, report)

    audit = [
        sys.executable, str(repo / AUDIT_REL),
        "--slot-root", str(args.slot_root.resolve()),
        "--task-contract", str(args.task_contract.resolve()),
        "--runtime", str(args.runtime.resolve()),
        "--output", str(args.audit_output.resolve()),
    ]
    report["status"] = "CONTROL_PLANE_AUDIT_036_STARTING"
    report["control_plane_audit"] = run(audit, cwd=repo)
    report["updated_at"] = now()
    if report["control_plane_audit"]["exit_code"] != 0:
        report["status"] = "BLOCKED_CONTROL_PLANE_AUDIT_036"
        atomic_json(report_path, report)
        return int(report["control_plane_audit"]["exit_code"])

    report["status"] = "FULL_PIPELINE_032_STARTING"
    atomic_json(report_path, report)
    report["pipeline"] = run(pipeline, cwd=repo)
    report["updated_at"] = now()
    if report["pipeline"]["exit_code"] != 0:
        report["status"] = "BLOCKED_FULL_PIPELINE_032"
        atomic_json(report_path, report)
        return int(report["pipeline"]["exit_code"])

    report["status"] = "CONTROL_AUDIT_AND_FULL_PIPELINE_SUCCEEDED"
    atomic_json(report_path, report)
    print(json.dumps({"ok": True, "status": report["status"], "report": str(report_path)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

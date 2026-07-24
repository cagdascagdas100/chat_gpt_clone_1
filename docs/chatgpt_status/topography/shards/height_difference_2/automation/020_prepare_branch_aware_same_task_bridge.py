#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
SLOT_ID = "height_difference_2"
SOURCE_BRANCH = "codex/aays-single-runner-v5-20260706"
QUEUE_STATES = ("pending", "running", "done", "failed", "processed", "error")
PATH_FIELDS = (
    "script_path", "previous_entrypoint_path", "candidate_extractor_path", "seed_adapter_path",
    "hmlr_source_preparer_path", "hmlr_exact_matcher_path", "hmlr_orchestrator_path",
    "ea_dtm1m_sampler_path", "terrain50_crosscheck_path", "numeric_orchestrator_path",
    "terrain50_resolver_path", "terrain50_preparation_path", "web_acceptance_path",
    "watcher_visibility_diagnostic_path", "existing_runner_health_readback_path",
    "canonical_source_path", "legacy_script_path",
)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _load_task(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("task JSON must be an object")
    if value.get("task_id") != TASK_ID or value.get("slot_id") != SLOT_ID:
        raise ValueError("task identity mismatch")
    if value.get("idempotency_key") != "height-difference-2-canonical-export-official-sampling-v3":
        raise ValueError("idempotency key mismatch")
    if any(bool(value.get(key)) for key in ("new_runner", "parallel_runner", "fake_data", "db_write", "migration", "production_deploy", "final_ready")):
        raise ValueError("task safety flag mismatch")
    return value


def _required_paths(task: dict[str, Any]) -> list[str]:
    paths = {str(task.get(field) or "").strip() for field in PATH_FIELDS}
    paths.update(str(v).strip() for v in task.get("read_paths", []) if str(v).strip())
    paths.add("docs/chatgpt_status/aays1/queue/aays1_height_difference_2_canonical_export_official_sampling_20260720.task.json")
    return sorted(path for path in paths if path and not path.startswith("ai-tasks/"))


def _markers(bridge_root: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for state in QUEUE_STATES:
        directory = bridge_root / "ai-queue" / state
        hits = [] if not directory.is_dir() else [str(p) for p in directory.iterdir() if p.is_file() and TASK_ID in p.name]
        result[state] = sorted(hits)
    return result


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-repo-root", type=Path, required=True)
    p.add_argument("--active-repo-root", type=Path, required=True)
    p.add_argument("--watch-worktree", type=Path, required=True)
    p.add_argument("--bridge-root", type=Path, required=True)
    p.add_argument("--task-json", type=Path, required=True)
    p.add_argument("--source-branch", default=SOURCE_BRANCH)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)

    payload: dict[str, Any]
    code = 2
    try:
        if args.source_branch != SOURCE_BRANCH:
            raise ValueError("source branch mismatch")
        task = _load_task(args.task_json)
        for root, name in ((args.source_repo_root, "source repo"), (args.active_repo_root, "active repo"), (args.watch_worktree, "watch worktree")):
            if not root.is_dir():
                raise FileNotFoundError(f"{name} missing: {root}")
        if not (args.bridge_root / "ai-queue").is_dir():
            raise FileNotFoundError("existing bridge ai-queue missing")

        markers_before = _markers(args.bridge_root)
        running_or_terminal = sum(len(markers_before[s]) for s in ("running", "done", "processed"))
        if running_or_terminal:
            raise ValueError("same task already running or terminal; no duplicate bridge copy")

        if args.apply:
            fetch = _run(["git", "fetch", "origin", args.source_branch], args.source_repo_root)
            if fetch.returncode:
                raise RuntimeError(f"git fetch failed: {fetch.stderr[-1000:]}")
            reset = _run(["git", "reset", "--hard", f"origin/{args.source_branch}"], args.watch_worktree)
            if reset.returncode:
                raise RuntimeError(f"watch worktree reset failed: {reset.stderr[-1000:]}")

        required = _required_paths(task)
        missing = []
        copied = []
        hashes = []
        for rel in required:
            source = args.watch_worktree / rel
            if not source.is_file():
                missing.append(rel)
                continue
            hashes.append({"path": rel, "git_blob_sha": _git_blob_sha(source), "size_bytes": source.stat().st_size})
            if args.apply:
                destination = args.active_repo_root / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                if _git_blob_sha(destination) != _git_blob_sha(source):
                    raise RuntimeError(f"copied file hash mismatch: {rel}")
                copied.append(rel)
        if missing:
            raise FileNotFoundError(f"source snapshot lacks required paths: {missing}")

        pending_path = args.bridge_root / "ai-queue" / "pending" / args.task_json.name
        queued = False
        if args.apply and not any(markers_before.values()):
            pending_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.task_json, pending_path)
            queued = True

        markers_after = _markers(args.bridge_root)
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": TASK_ID,
            "status": "SAME_TASK_BRIDGE_RECOVERY_APPLIED" if args.apply else "SAME_TASK_BRIDGE_RECOVERY_PREFLIGHT_READY",
            "source_branch": args.source_branch,
            "required_path_count": len(required),
            "required_paths": hashes,
            "missing_paths": missing,
            "copied_path_count": len(copied),
            "copied_paths": copied,
            "bridge_task_path": str(pending_path),
            "bridge_task_queued": queued,
            "markers_before": markers_before,
            "markers_after": markers_after,
            "existing_worktree_reused": True,
            "existing_bridge_reused": True,
            "process_started": False,
            "process_stopped": False,
            "new_worktree_created": False,
            "new_runner": False,
            "parallel_runner": False,
            "new_task_created": False,
            "same_idempotent_task_only": True,
            "active_repo_branch_changed": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 0
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": TASK_ID,
            "status": "BLOCKED_SAME_TASK_BRIDGE_RECOVERY",
            "error": f"{type(exc).__name__}: {exc}",
            "process_started": False,
            "new_worktree_created": False,
            "new_runner": False,
            "parallel_runner": False,
            "new_task_created": False,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"]}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

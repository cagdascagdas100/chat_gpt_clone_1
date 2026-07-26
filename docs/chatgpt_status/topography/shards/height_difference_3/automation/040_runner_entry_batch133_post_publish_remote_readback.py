#!/usr/bin/env python3
"""No-argument post-publish origin-readback entrypoint for the same task.

Run only after the existing serial publisher has published the exact Batch132
manifest. This script performs no push and changes no numeric measurement.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

TASK_ID = "height_difference_3-canonical-api-measurement-20260721-01"
CONTINUATION = "6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
EXPECTED_ROWS = list(range(61540, 61552))


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "england_map_web").is_dir() and (candidate / "docs" / "chatgpt_status").is_dir():
            return candidate
    raise RuntimeError("PUBLISHER_REPO_ROOT_NOT_FOUND")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def run(command: list[str], cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-16000:],
        "stderr": proc.stderr[-16000:],
    }


def write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    repo = find_repo_root(script_dir)
    current_task = load_json(repo / "docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json")
    if current_task.get("task_id") != TASK_ID or current_task.get("continuation_key") != CONTINUATION:
        raise ValueError("current task/continuation mismatch")

    handoff_path = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_prepare_publish_handoff.json"
    handoff = load_json(handoff_path)
    if handoff.get("status") != "PUBLISH_PENDING_SERIAL_PUBLISHER_REQUIRED":
        raise ValueError("pre-publish handoff missing or invalid")
    if [int(v) for v in (handoff.get("expected_rows") or [])] != EXPECTED_ROWS:
        raise ValueError("handoff row set mismatch")

    powershell = os.environ.get("AAYS_POWERSHELL_EXE", "powershell")
    verifier = script_dir / "038_verify_batch132_origin_remote_readback.ps1"
    if not verifier.is_file():
        raise FileNotFoundError(verifier)
    result = run(
        [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(verifier),
            "-RepoRoot",
            str(repo),
            "-GitExe",
            os.environ.get("AAYS_GIT_EXE", "git"),
        ],
        repo,
    )
    if result["exit_code"] != 0:
        raise RuntimeError(f"origin remote readback failed: {result['stderr'][-2000:]}")

    remote_path = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/031_batch132_remote_readback/batch132_origin_remote_readback.json"
    remote = load_json(remote_path)
    if remote.get("task_id") != TASK_ID or remote.get("continuation_key") != CONTINUATION:
        raise ValueError("remote readback task/continuation mismatch")
    if [int(v) for v in (remote.get("expected_rows") or [])] != EXPECTED_ROWS:
        raise ValueError("remote readback row set mismatch")
    if remote.get("all_remote_blobs_match") is not True:
        raise ValueError("remote blob parity did not pass")
    if int(remote.get("file_count") or 0) != 7:
        raise ValueError("remote readback file count must equal 7")
    if remote.get("remote_tracking_ref_freshly_updated") is not True:
        raise ValueError("remote tracking ref was not freshly updated")
    if remote.get("numeric_publish_acceptance_for_12_rows") is not True:
        raise ValueError("numeric publish acceptance not granted")

    output = repo / "docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_post_publish_remote_acceptance.json"
    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION,
        "status": "REMOTE_READBACK_ACCEPTED_12_ROWS",
        "expected_rows": EXPECTED_ROWS,
        "verified_count": 12,
        "remote_head": remote.get("remote_head"),
        "remote_file_count": 7,
        "all_remote_blobs_match": True,
        "numeric_publish_acceptance_for_12_rows": True,
        "child_direct_push_performed": False,
        "numeric_values_changed": 0,
        "new_task_created": False,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "overall_product_final_ready": False,
        "final_ready": False,
        "fake_data": False,
        "remote_readback_stage": result,
    }
    write(output, payload)
    print(json.dumps({"ok": True, "status": payload["status"], "output": str(output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

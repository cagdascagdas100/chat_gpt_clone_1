#!/usr/bin/env python3
"""Run preflight, then the existing 026 pipeline with alias-safe validator 027.

This is a bootstrap inside one already-running shared runner. It does not create
or submit a queue item, lease, owner, heartbeat, new runner or parallel runner.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def run(command: list[str], cwd: Path) -> dict[str, Any]:
    started = utc_now()
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "started_at": started,
        "finished_at": utc_now(),
        "command": command,
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-16000:],
        "stderr_tail": proc.stderr[-16000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--security-geojson", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--web-runtime-status", required=True, type=Path)
    parser.add_argument("--script-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--operation-start", type=int, default=331)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--preflight-timeout", type=int, default=30)
    parser.add_argument("--min-free-bytes", type=int, default=4 * 1024 * 1024 * 1024)
    parser.add_argument("--expected-git-blob-sha1", default="8afd1d2bac414cf0f6b9484014e7878a4ceff877")
    args = parser.parse_args()

    script_dir = args.script_dir.resolve()
    source = args.security_geojson.resolve()
    output_dir = args.output_dir.resolve()
    web_runtime = args.web_runtime_status.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    execution_path = output_dir / "preflight_then_resumable_execution.json"
    preflight_report = output_dir / "preflight_latest.json"

    preflight_script = script_dir / "028_preflight_existing_f_runner.py"
    orchestrator = script_dir / "026_execute_resumable_targeted_sources.py"
    validator = script_dir / "027_validate_resumable_alias_safe.py"
    for path in (preflight_script, orchestrator, validator):
        if not path.is_file():
            raise FileNotFoundError(path)

    preflight_command = [
        sys.executable, str(preflight_script),
        "--security-geojson", str(source),
        "--output-dir", str(output_dir),
        "--script-dir", str(script_dir),
        "--report-output", str(preflight_report),
        "--web-runtime-status", str(web_runtime),
        "--expected-git-blob-sha1", args.expected_git_blob_sha1,
        "--min-free-bytes", str(args.min_free_bytes),
        "--operation-start", str(args.operation_start),
        "--timeout", str(args.preflight_timeout),
    ]
    state: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "updated_at": utc_now(),
        "status": "PREFLIGHT_RUNNING",
        "preflight": None,
        "pipeline": None,
        "single_shared_runner_only": True,
        "maximum_parallel_network_stages": 2,
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
    atomic_json(execution_path, state)
    preflight_result = run(preflight_command, Path.cwd())
    state["preflight"] = preflight_result
    if preflight_result["exit_code"] != 0:
        state["updated_at"] = utc_now()
        state["status"] = "BLOCKED_PREFLIGHT_026_NOT_STARTED"
        atomic_json(execution_path, state)
        return preflight_result["exit_code"]

    pipeline_operation_start = args.operation_start + 8
    pipeline_command = [
        sys.executable, str(orchestrator),
        "--security-geojson", str(source),
        "--output-dir", str(output_dir),
        "--validator-script", str(validator),
        "--web-runtime-status", str(web_runtime),
        "--operation-start", str(pipeline_operation_start),
        "--timeout", str(args.timeout),
    ]
    state["status"] = "PREFLIGHT_PASSED_026_RUNNING"
    state["updated_at"] = utc_now()
    atomic_json(execution_path, state)
    pipeline_result = run(pipeline_command, Path.cwd())
    state["pipeline"] = pipeline_result
    state["updated_at"] = utc_now()
    state["status"] = (
        "026_COMPLETED_READ_REMOTE_OUTPUTS_NEXT"
        if pipeline_result["exit_code"] == 0
        else "BLOCKED_026_SEE_RUNTIME_AND_EXECUTION_OUTPUT"
    )
    atomic_json(execution_path, state)
    return pipeline_result["exit_code"]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

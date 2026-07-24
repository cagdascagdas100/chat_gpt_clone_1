#!/usr/bin/env python3
"""Run preflight, then the existing 026 pipeline with alias-safe validator 027.

This bootstrap runs inside one already-running shared runner. It creates no queue,
lease, owner, heartbeat, new runner or parallel runner. Runtime operation numbers
are allocated after the latest committed website operation row. The 030 bridge
preserves preflight rows while streaming 026 rows into the same web runtime JSON.
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


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def history_operation_floor(path: Path) -> dict[str, int]:
    payload = load_json_object(path)
    operations = payload.get("operations")
    if not isinstance(operations, list):
        raise ValueError("website operation history lacks an operations list")
    numbers: list[int] = []
    for index, item in enumerate(operations, 1):
        if not isinstance(item, dict):
            raise ValueError(f"website operation {index} is not an object")
        value = item.get("operation_no")
        if isinstance(value, bool):
            raise ValueError(f"website operation {index} has a boolean operation_no")
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"website operation {index} has invalid operation_no={value!r}") from exc
        if number < 1:
            raise ValueError(f"website operation {index} has non-positive operation_no={number}")
        numbers.append(number)
    if len(numbers) != len(set(numbers)):
        raise ValueError("website operation history contains duplicate operation numbers")
    max_operation = max(numbers, default=0)
    cumulative = payload.get("cumulative_website_operation_rows")
    if cumulative is not None and int(cumulative) != max_operation:
        raise ValueError(
            f"website cumulative row count {cumulative} does not match maximum operation_no {max_operation}"
        )
    return {"max_operation_no": max_operation, "next_operation_no": max_operation + 1}


def resolve_preflight_start(history_path: Path, requested: int | None) -> dict[str, int]:
    floor = history_operation_floor(history_path)
    computed = floor["next_operation_no"]
    if requested is not None:
        if requested < 1:
            raise ValueError("operation-start must be positive")
        if requested != computed:
            raise ValueError(
                f"operation-start {requested} is stale or non-contiguous; expected exactly {computed}"
            )
    return {**floor, "preflight_operation_start": computed}


def pipeline_start_from_preflight(report_path: Path, preflight_start: int) -> dict[str, int]:
    report = load_json_object(report_path)
    operations = report.get("operations")
    operation_count = int(report.get("operation_count", -1))
    if not isinstance(operations, list) or operation_count != len(operations) or operation_count < 1:
        raise ValueError("preflight report operation_count does not match its operations")
    expected = list(range(preflight_start, preflight_start + operation_count))
    actual: list[int] = []
    for index, item in enumerate(operations, 1):
        if not isinstance(item, dict):
            raise ValueError(f"preflight operation {index} is not an object")
        actual.append(int(item.get("operation_no")))
    if actual != expected:
        raise ValueError(f"preflight operation numbers are not contiguous: {actual} != {expected}")
    return {
        "preflight_operation_count": operation_count,
        "preflight_first_operation_no": expected[0],
        "preflight_last_operation_no": expected[-1],
        "pipeline_operation_start": expected[-1] + 1,
    }


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
    parser.add_argument("--web-operations-history", required=True, type=Path)
    parser.add_argument("--script-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--operation-start", type=int)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--preflight-timeout", type=int, default=30)
    parser.add_argument("--runtime-poll-seconds", type=float, default=0.5)
    parser.add_argument("--min-free-bytes", type=int, default=4 * 1024 * 1024 * 1024)
    parser.add_argument("--expected-git-blob-sha1", default="8afd1d2bac414cf0f6b9484014e7878a4ceff877")
    args = parser.parse_args()

    script_dir = args.script_dir.resolve()
    source = args.security_geojson.resolve()
    output_dir = args.output_dir.resolve()
    web_runtime = args.web_runtime_status.resolve()
    history_path = args.web_operations_history.resolve()
    numbering = resolve_preflight_start(history_path, args.operation_start)
    preflight_start = numbering["preflight_operation_start"]

    output_dir.mkdir(parents=True, exist_ok=True)
    execution_path = output_dir / "preflight_then_resumable_execution.json"
    preflight_report = output_dir / "preflight_latest.json"
    pipeline_runtime = output_dir / "runtime_progress_latest.json"

    preflight_script = script_dir / "028_preflight_existing_f_runner.py"
    orchestrator = script_dir / "026_execute_resumable_targeted_sources.py"
    validator = script_dir / "027_validate_resumable_alias_safe.py"
    runtime_bridge = script_dir / "030_stream_combined_runtime.py"
    for path in (preflight_script, orchestrator, validator, runtime_bridge):
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
        "--operation-start", str(preflight_start),
        "--timeout", str(args.preflight_timeout),
    ]
    state: dict[str, Any] = {
        "schema_version": 3,
        "slot_id": "height_difference_3",
        "updated_at": utc_now(),
        "status": "PREFLIGHT_RUNNING",
        "operation_numbering": {
            **numbering,
            "website_operations_history": str(history_path),
            "monotonic_contiguous_required": True,
        },
        "runtime_visibility": {
            "preflight_and_pipeline_rows_preserved": True,
            "runtime_bridge": str(runtime_bridge),
            "web_runtime_status": str(web_runtime),
            "pipeline_internal_runtime": str(pipeline_runtime),
        },
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

    preflight_numbering = pipeline_start_from_preflight(preflight_report, preflight_start)
    state["operation_numbering"].update(preflight_numbering)
    pipeline_operation_start = preflight_numbering["pipeline_operation_start"]
    child_pipeline_command = [
        sys.executable, str(orchestrator),
        "--security-geojson", str(source),
        "--output-dir", str(output_dir),
        "--validator-script", str(validator),
        "--operation-start", str(pipeline_operation_start),
        "--timeout", str(args.timeout),
    ]
    bridge_command = [
        sys.executable, str(runtime_bridge),
        "--preflight-report", str(preflight_report),
        "--pipeline-runtime", str(pipeline_runtime),
        "--web-runtime-status", str(web_runtime),
        "--pipeline-operation-start", str(pipeline_operation_start),
        "--poll-seconds", str(args.runtime_poll_seconds),
        "--",
        *child_pipeline_command,
    ]
    state["status"] = "PREFLIGHT_PASSED_COMBINED_RUNTIME_BRIDGE_RUNNING"
    state["updated_at"] = utc_now()
    state["runtime_visibility"]["pipeline_child_command"] = child_pipeline_command
    atomic_json(execution_path, state)
    pipeline_result = run(bridge_command, Path.cwd())
    state["pipeline"] = pipeline_result
    state["updated_at"] = utc_now()
    state["status"] = (
        "026_COMPLETED_COMBINED_RUNTIME_READY_READ_REMOTE_OUTPUTS_NEXT"
        if pipeline_result["exit_code"] == 0
        else "BLOCKED_026_SEE_COMBINED_RUNTIME_AND_EXECUTION_OUTPUT"
    )
    atomic_json(execution_path, state)
    return pipeline_result["exit_code"]


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

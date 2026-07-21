#!/usr/bin/env python3
"""Bridge preflight and pipeline runtime rows into one atomic web runtime stream.

Runs 026 as a child process inside the existing shared runner. The child writes
its own runtime JSON; this bridge validates and merges those rows after the
preflight rows without creating a queue, lease, owner, heartbeat, or runner.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
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


def load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON object required: {path}")
    return payload


def normalized_operations(payload: dict[str, Any], label: str) -> list[dict[str, Any]]:
    values = payload.get("operations")
    if not isinstance(values, list):
        raise ValueError(f"{label} lacks operations list")
    result: list[dict[str, Any]] = []
    seen: set[int] = set()
    for index, raw in enumerate(values, 1):
        if not isinstance(raw, dict):
            raise ValueError(f"{label} operation {index} is not an object")
        value = raw.get("operation_no")
        if isinstance(value, bool):
            raise ValueError(f"{label} operation {index} has boolean operation_no")
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} operation {index} has invalid operation_no={value!r}") from exc
        if number < 1 or number in seen:
            raise ValueError(f"{label} operation number is invalid or duplicated: {number}")
        seen.add(number)
        result.append({**raw, "operation_no": number})
    return result


def validate_contiguous(rows: list[dict[str, Any]], start: int, label: str) -> None:
    numbers = [int(row["operation_no"]) for row in rows]
    expected = list(range(start, start + len(rows)))
    if numbers != expected:
        raise ValueError(f"{label} operation numbers are not contiguous: {numbers} != {expected}")


def merged_snapshot(
    preflight: dict[str, Any],
    pipeline: dict[str, Any] | None,
    pipeline_start: int,
    *,
    child_status: str,
    child_exit_code: int | None,
) -> dict[str, Any]:
    preflight_rows = normalized_operations(preflight, "preflight")
    if not preflight_rows:
        raise ValueError("preflight operations are empty")
    validate_contiguous(preflight_rows, int(preflight_rows[0]["operation_no"]), "preflight")
    if int(preflight_rows[-1]["operation_no"]) + 1 != pipeline_start:
        raise ValueError("pipeline start does not immediately follow preflight")

    pipeline_rows: list[dict[str, Any]] = []
    if pipeline is not None:
        pipeline_rows = normalized_operations(pipeline, "pipeline")
        validate_contiguous(pipeline_rows, pipeline_start, "pipeline")

    combined = preflight_rows + pipeline_rows
    if len({int(row["operation_no"]) for row in combined}) != len(combined):
        raise ValueError("combined runtime contains duplicate operation numbers")

    pipeline_status = pipeline.get("status") if pipeline else None
    pipeline_failure = pipeline.get("failure") if pipeline else None
    real_counts = (
        pipeline.get("real_counts")
        if isinstance(pipeline, dict) and isinstance(pipeline.get("real_counts"), dict)
        else preflight.get("real_counts", {})
    )
    return {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "updated_at": utc_now(),
        "status": (
            pipeline_status
            if child_status == "finished" and pipeline_status
            else "PREFLIGHT_PASSED_PIPELINE_RUNTIME_STREAMING"
            if child_status == "running"
            else "PREFLIGHT_PASSED_PIPELINE_STARTING"
        ),
        "failure": pipeline_failure,
        "first_invalid_stage": (
            pipeline.get("first_invalid_stage")
            if isinstance(pipeline, dict)
            else preflight.get("first_invalid_stage")
        ),
        "operation_count": len(combined),
        "operations": combined,
        "preflight_operation_count": len(preflight_rows),
        "pipeline_operation_count": len(pipeline_rows),
        "preflight_first_operation_no": int(preflight_rows[0]["operation_no"]),
        "preflight_last_operation_no": int(preflight_rows[-1]["operation_no"]),
        "pipeline_first_operation_no": pipeline_start,
        "last_visible_operation_no": int(combined[-1]["operation_no"]),
        "pipeline_child_status": child_status,
        "pipeline_child_exit_code": child_exit_code,
        "runtime_prefix_preserved": True,
        "real_counts": real_counts,
        "single_shared_runner_only": True,
        "single_process_bounded_concurrency": True,
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-report", required=True, type=Path)
    parser.add_argument("--pipeline-runtime", required=True, type=Path)
    parser.add_argument("--web-runtime-status", required=True, type=Path)
    parser.add_argument("--pipeline-operation-start", required=True, type=int)
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        raise ValueError("pipeline command is required after --")
    if args.pipeline_operation_start < 1:
        raise ValueError("pipeline-operation-start must be positive")
    if not (0.1 <= args.poll_seconds <= 30):
        raise ValueError("poll-seconds must be between 0.1 and 30")

    preflight = load_object(args.preflight_report.resolve())
    args.pipeline_runtime = args.pipeline_runtime.resolve()
    args.web_runtime_status = args.web_runtime_status.resolve()
    args.pipeline_runtime.parent.mkdir(parents=True, exist_ok=True)
    args.web_runtime_status.parent.mkdir(parents=True, exist_ok=True)

    atomic_json(
        args.web_runtime_status,
        merged_snapshot(
            preflight,
            None,
            args.pipeline_operation_start,
            child_status="starting",
            child_exit_code=None,
        ),
    )

    proc = subprocess.Popen(args.command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    last_signature: tuple[int, int] | None = None
    while proc.poll() is None:
        if args.pipeline_runtime.is_file():
            stat = args.pipeline_runtime.stat()
            signature = (stat.st_size, stat.st_mtime_ns)
            if signature != last_signature:
                pipeline = load_object(args.pipeline_runtime)
                atomic_json(
                    args.web_runtime_status,
                    merged_snapshot(
                        preflight,
                        pipeline,
                        args.pipeline_operation_start,
                        child_status="running",
                        child_exit_code=None,
                    ),
                )
                last_signature = signature
        time.sleep(args.poll_seconds)

    stdout, stderr = proc.communicate()
    pipeline = load_object(args.pipeline_runtime) if args.pipeline_runtime.is_file() else None
    final = merged_snapshot(
        preflight,
        pipeline,
        args.pipeline_operation_start,
        child_status="finished",
        child_exit_code=proc.returncode,
    )
    final["pipeline_stdout_tail"] = stdout[-16000:]
    final["pipeline_stderr_tail"] = stderr[-16000:]
    if proc.returncode != 0 and pipeline is None:
        final["status"] = "BLOCKED_PIPELINE_EXITED_WITHOUT_RUNTIME_OUTPUT"
        final["failure"] = f"pipeline exited {proc.returncode} without runtime JSON"
    atomic_json(args.web_runtime_status, final)
    print(json.dumps({
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "operation_count": final["operation_count"],
        "last_visible_operation_no": final["last_visible_operation_no"],
        "web_runtime": str(args.web_runtime_status),
    }))
    return int(proc.returncode)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

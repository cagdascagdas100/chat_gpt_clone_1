#!/usr/bin/env python3
"""Retry the audited 037 entrypoint only for transient network/service failures.

The wrapper is sequential and runs inside the same existing shared-runner
process. It creates no task, claim, queue item, lease, heartbeat, owner, runner,
or parallel runner. Non-transient worktree, control-plane, data-contract,
identity, geometry, checksum and safety failures stop immediately.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "height_difference_3"
AUDITED_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/037_audit_control_then_run_full_pipeline.py"
PIPELINE_REL = "docs/chatgpt_status/topography/shards/height_difference_3/automation/032_run_full_pipeline_and_website_acceptance.py"

TRANSIENT_PATTERNS = (
    r"\btimeout\b",
    r"timed out",
    r"temporary failure",
    r"temporarily unavailable",
    r"name or service not known",
    r"nodename nor servname",
    r"\bdns\b",
    r"connection (?:aborted|closed|refused|reset|error)",
    r"remote end closed connection",
    r"remotedisconnected",
    r"max retries exceeded",
    r"too many requests",
    r"\bhttp(?:error)?\s*(?:429|500|502|503|504)\b",
    r"\b(?:429|500|502|503|504)\s+(?:error|service|gateway|server|unavailable)",
    r"service unavailable",
    r"bad gateway",
    r"gateway timeout",
    r"tls.{0,80}(?:temporar|handshake)",
)
NON_RETRYABLE_PATTERNS = (
    r"sha256 mismatch",
    r"md5 mismatch",
    r"blob differs",
    r"worktree.{0,120}dirty",
    r"branch mismatch",
    r"repository mismatch",
    r"outside british national grid",
    r"ambiguous",
    r"duplicate",
    r"non-contiguous",
    r"unsupported identity",
    r"invalid geometry",
    r"resolution is coarser",
    r"crs.{0,120}expected",
    r"unsafe archive",
    r"fake_data",
    r"db_write",
    r"migration",
    r"production_deploy",
)


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--initial-delay-seconds", type=float, default=2.0)
    parser.add_argument("--maximum-delay-seconds", type=float, default=8.0)
    parser.add_argument("--attempt-report", required=True, type=Path)
    parser.add_argument("--no-sleep", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("audited_command", nargs=argparse.REMAINDER)
    return parser.parse_args()


def normalized_audited(command: list[str]) -> list[str]:
    value = list(command)
    if value and value[0] == "--":
        value = value[1:]
    if len(value) < 2 or value[0] != "python" or value[1] != AUDITED_REL:
        raise ValueError("retry wrapper must explicitly invoke the approved 037 entrypoint")
    try:
        separator = value.index("--", 2)
    except ValueError as exc:
        raise ValueError("037 command must contain an explicit nested 032 separator") from exc
    nested = value[separator + 1:]
    if len(nested) < 2 or nested[0] != "python" or nested[1] != PIPELINE_REL:
        raise ValueError("037 command must explicitly invoke the approved 032 pipeline")
    value[0] = sys.executable
    return value


def output_dir_from_command(command: list[str]) -> Path:
    try:
        index = command.index("--output-dir")
        raw = command[index + 1]
    except (ValueError, IndexError) as exc:
        raise ValueError("nested 032 command must include --output-dir") from exc
    return Path(raw).resolve()


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def evidence_text(result: dict[str, Any], output_dir: Path) -> tuple[str, dict[str, Any]]:
    paths = [
        output_dir / "control_audit_then_pipeline_execution.json",
        output_dir / "control_plane_readiness_latest.json",
        output_dir / "full_pipeline_and_website_acceptance_execution.json",
        output_dir / "preflight_then_resumable_execution.json",
        output_dir / "preflight_latest.json",
        output_dir / "resumable_targeted_source_execution.json",
        output_dir / "runtime_progress_latest.json",
        output_dir / "website_acceptance_transaction_latest.json",
        output_dir / "website_acceptance_latest.json",
    ]
    artefacts: dict[str, Any] = {}
    pieces = [str(result.get("stdout_tail") or ""), str(result.get("stderr_tail") or "")]
    for path in paths:
        payload = read_json(path)
        if payload is not None:
            artefacts[path.name] = payload
            pieces.append(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return "\n".join(pieces).casefold(), artefacts


def retry_decision(result: dict[str, Any], output_dir: Path) -> tuple[bool, str, dict[str, Any]]:
    text, artefacts = evidence_text(result, output_dir)
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in NON_RETRYABLE_PATTERNS):
        return False, "NON_TRANSIENT_CONTRACT_OR_SAFETY_FAILURE", artefacts
    if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in TRANSIENT_PATTERNS):
        return True, "TRANSIENT_NETWORK_OR_SERVICE_FAILURE", artefacts
    return False, "NO_APPROVED_TRANSIENT_SIGNATURE", artefacts


def run(command: list[str]) -> dict[str, Any]:
    started = now()
    proc = subprocess.run(command, text=True, capture_output=True, check=False)
    return {
        "started_at": started,
        "finished_at": now(),
        "command": command,
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-16000:],
        "stderr_tail": proc.stderr[-16000:],
    }


def main() -> int:
    args = parse()
    if not 1 <= args.attempts <= 5:
        raise ValueError("attempts must be between 1 and 5")
    if args.initial_delay_seconds < 0 or args.maximum_delay_seconds < 0:
        raise ValueError("retry delays must be non-negative")
    if args.initial_delay_seconds > args.maximum_delay_seconds:
        raise ValueError("initial delay cannot exceed maximum delay")

    audited = normalized_audited(args.audited_command)
    output_dir = output_dir_from_command(audited)
    report_path = args.attempt_report.resolve()
    state: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "updated_at": now(),
        "status": "AUDITED_ENTRYPOINT_RETRY_WRAPPER_STARTING",
        "maximum_attempts": args.attempts,
        "attempt_count": 0,
        "attempts": [],
        "retry_policy": {
            "sequential_same_existing_runner_process_only": True,
            "approved_reason": "TRANSIENT_NETWORK_OR_SERVICE_FAILURE",
            "non_transient_failures_stop_immediately": True,
            "each_attempt_repeats_safe_sync_control_audit_and_resumable_validation": True,
            "maximum_parallel_network_stages_inside_032": 2,
        },
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
    atomic_json(report_path, state)

    for attempt_no in range(1, args.attempts + 1):
        result = run(audited)
        retryable, reason, artefacts = retry_decision(result, output_dir)
        record = {
            "attempt_no": attempt_no,
            **result,
            "retryable": retryable,
            "decision_reason": reason,
            "evidence_statuses": {
                name: payload.get("status")
                for name, payload in artefacts.items()
                if isinstance(payload, dict)
            },
        }
        state["attempt_count"] = attempt_no
        state["attempts"].append(record)
        state["updated_at"] = now()

        if result["exit_code"] == 0:
            state["status"] = "AUDITED_RESUMABLE_PIPELINE_SUCCEEDED"
            state["successful_attempt"] = attempt_no
            atomic_json(report_path, state)
            print(json.dumps({"ok": True, "status": state["status"], "attempt": attempt_no, "report": str(report_path)}))
            return 0

        if not retryable:
            state["status"] = "BLOCKED_NON_TRANSIENT_AUDITED_PIPELINE_FAILURE"
            state["final_exit_code"] = int(result["exit_code"])
            atomic_json(report_path, state)
            return int(result["exit_code"])

        if attempt_no == args.attempts:
            state["status"] = "BLOCKED_TRANSIENT_FAILURE_RETRY_BUDGET_EXHAUSTED"
            state["final_exit_code"] = int(result["exit_code"])
            atomic_json(report_path, state)
            return int(result["exit_code"])

        delay = min(args.initial_delay_seconds * (2 ** (attempt_no - 1)), args.maximum_delay_seconds)
        state["attempts"][-1]["retry_delay_seconds"] = delay
        state["status"] = "TRANSIENT_FAILURE_WAITING_FOR_RETRY"
        atomic_json(report_path, state)
        if delay and not args.no_sleep:
            time.sleep(delay)

    raise AssertionError("unreachable")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

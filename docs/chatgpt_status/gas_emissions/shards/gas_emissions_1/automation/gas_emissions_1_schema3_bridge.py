#!/usr/bin/env python3
"""Safe schema-v3 bridge for the existing gas_emissions_1 recovery task.

This script never creates a second logical task or runner. It validates the
canonical queue/task context and then invokes the already tracked V6 PowerShell
recovery carrier on the existing Windows runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID = "gas_emissions_1"
TASK_ID = "gas-emissions-1-single-pass-recovery-20260722"
CONTINUATION_KEY = "5345f564b184a0bdebe1f2233159ac30077add6d920970263ba528f1c5231e2c"
QUEUE_REL = Path("docs/chatgpt_status/aays1/queue/0020_100_gas_emissions_1_single_pass_recovery_20260722.task.json")
V6_REL = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/automation/RUN_GAS_EMISSIONS_1_SINGLE_PASS_RECOVERY_20260722_V6.ps1")
V6_BLOB_SHA1 = "dd20f6193519fc59698f5a610df55b68e37d785f"
BRIDGE_REPORT_REL = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/recovery/gas_emissions_1_schema3_bridge_latest.json")
RECOVERY_REPORT_REL = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_single_pass_recovery_latest.json")
VALIDATION_REPORT_REL = Path("docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_single_pass_recovery_validation_latest.json")
FORBIDDEN_TRUE_FLAGS = ("fake_data", "db_write", "migration", "production_deploy", "final_ready")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(text)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def validate_context(repo_root: Path) -> dict[str, Any]:
    queue_path = repo_root / QUEUE_REL
    script_path = repo_root / V6_REL
    if not queue_path.is_file():
        raise FileNotFoundError(f"missing queue manifest: {QUEUE_REL}")
    if not script_path.is_file():
        raise FileNotFoundError(f"missing V6 carrier: {V6_REL}")

    queue = read_json(queue_path)
    checks = {
        "queue_slot_id": queue.get("slot_id") == SLOT_ID,
        "queue_task_id": queue.get("task_id") == TASK_ID,
        "queue_continuation_key": queue.get("continuation_key") == CONTINUATION_KEY,
        "queue_schema_version": queue.get("schema_version") == 3,
        "queue_state_ready": str(queue.get("state", "")).upper() == "READY",
        "single_runner_only": bool(queue.get("single_runner_only", True)),
        "second_task_created_false": queue.get("second_task_created", False) is False,
        "second_runner_created_false": queue.get("second_runner_created", False) is False,
        "v6_blob_sha1_match": git_blob_sha1(script_path) == V6_BLOB_SHA1,
    }
    if not all(checks.values()):
        failed = sorted(key for key, value in checks.items() if not value)
        raise RuntimeError("preflight failed: " + ",".join(failed))
    return checks


def validate_output(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if data.get("slot_id") != SLOT_ID:
        raise RuntimeError(f"wrong slot_id in {path}")
    for flag in FORBIDDEN_TRUE_FLAGS:
        if data.get(flag) is True:
            raise RuntimeError(f"forbidden true flag {flag} in {path}")
    return data


def run_bridge(repo_root: Path, timeout_seconds: int) -> int:
    started_at = utc_now()
    report: dict[str, Any] = {
        "schema_version": 3,
        "slot_id": SLOT_ID,
        "task_id": TASK_ID,
        "continuation_key": CONTINUATION_KEY,
        "started_at": started_at,
        "state": "RUNNING_PREFLIGHT",
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    report_path = repo_root / BRIDGE_REPORT_REL
    try:
        report["preflight"] = validate_context(repo_root)
        powershell = shutil.which("powershell.exe") or shutil.which("powershell") or shutil.which("pwsh")
        if os.name != "nt" or not powershell:
            raise RuntimeError("WINDOWS_POWERSHELL_EXECUTION_HOST_REQUIRED")

        command = [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(repo_root / V6_REL),
            "-RepoRoot",
            str(repo_root),
            "-OverallTimeoutSeconds",
            "2700",
        ]
        env = os.environ.copy()
        env["AAYS_SLOT_ID"] = SLOT_ID
        env["AAYS_TASK_ID"] = TASK_ID
        completed = subprocess.run(
            command,
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        report["process"] = {
            "returncode": completed.returncode,
            "stdout_tail": completed.stdout[-4000:],
            "stderr_tail": completed.stderr[-4000:],
        }
        if completed.returncode != 0:
            raise RuntimeError(f"V6_CARRIER_NONZERO_EXIT_{completed.returncode}")

        recovery = validate_output(repo_root / RECOVERY_REPORT_REL)
        validation = validate_output(repo_root / VALIDATION_REPORT_REL)
        report["validated_outputs"] = {
            "recovery_report": str(RECOVERY_REPORT_REL),
            "validation_report": str(VALIDATION_REPORT_REL),
            "recovery_state": recovery.get("state") or recovery.get("status"),
            "validation_state": validation.get("state") or validation.get("status"),
        }
        report["state"] = "PASS_EXISTING_V6_RECOVERY_EXECUTED"
        report["finished_at"] = utc_now()
        atomic_write_json(report_path, report)
        return 0
    except subprocess.TimeoutExpired as exc:
        report["state"] = "BLOCKED_TIMEOUT"
        report["blocker"] = f"V6_CARRIER_TIMEOUT_AFTER_{timeout_seconds}_SECONDS"
        report["stdout_tail"] = (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else ""
        report["stderr_tail"] = (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else ""
    except Exception as exc:
        report["state"] = "BLOCKED_PREFLIGHT_OR_EXECUTION"
        report["blocker"] = f"{type(exc).__name__}:{exc}"
    report["finished_at"] = utc_now()
    atomic_write_json(report_path, report)
    return 2


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sample = root / "sample.txt"
        sample.write_text("abc", encoding="utf-8")
        expected = hashlib.sha1(b"blob 3\0abc").hexdigest()
        if git_blob_sha1(sample) != expected:
            raise AssertionError("git blob SHA-1 test failed")
        target = root / "nested" / "result.json"
        atomic_write_json(target, {"slot_id": SLOT_ID, "ok": True})
        if read_json(target).get("ok") is not True:
            raise AssertionError("atomic JSON test failed")
    print("SELF_TEST_PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=os.environ.get("AAYS_REPO_ROOT", os.getcwd()))
    parser.add_argument("--timeout-seconds", type=int, default=2820)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    return run_bridge(Path(args.repo_root).resolve(), args.timeout_seconds)


if __name__ == "__main__":
    sys.exit(main())

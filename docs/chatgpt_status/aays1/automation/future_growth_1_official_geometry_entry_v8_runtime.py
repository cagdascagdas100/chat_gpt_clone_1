#!/usr/bin/env python3
"""Stall-resistant guarded runtime wrapper for future_growth_1 revision 8."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
CORE_BOOTSTRAP = REPO / "docs/chatgpt_status/aays1/automation/future_growth_1_official_geometry_entry_v8_bootstrap.py"
QUEUE_VALIDATOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/030_validate_revision8_queue_request_contract_v2.py"
QUEUE_SELFTEST = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/031_selftest_revision8_queue_request_contract_v2.py"
DEPENDENCY_VALIDATOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/034_validate_revision8_predecessor_dependency_v1.py"
DEPENDENCY_SELFTEST = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/035_selftest_revision8_predecessor_dependency_v1.py"
BUNDLE_VALIDATOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/036_validate_revision8_runtime_evidence_bundle_v1.py"
BUNDLE_SELFTEST = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/037_selftest_revision8_runtime_evidence_bundle_v1.py"
STALL_VALIDATOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/040_validate_revision8_stall_state_v1.py"
STALL_SELFTEST = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/041_selftest_revision8_stall_state_v1.py"
QUEUE_MANIFEST = REPO / "docs/chatgpt_status/aays1/queue/aays1_future_growth_1_official_geometry_pipeline_v8_20260722.task.json"
SLOT_STATUS = REPO / "docs/chatgpt_status/_shared/slots_21/future_growth_1/status_latest.json"
HEARTBEAT = REPO / "docs/chatgpt_status/_shared/slots_21/future_growth_1/heartbeat_latest.json"
OWNERSHIP = REPO / "docs/chatgpt_status/_shared/slots_21/future_growth_1/ownership_latest.json"
PREDECESSOR_STATUS = REPO / "docs/chatgpt_status/_shared/slots_21/height_difference_2/status_latest.json"
STALL_OUTPUT = REPO / "england_map_web/data/aays_21_slots/future_growth_1/revision8_stall_diagnostic_latest.json"
DEPENDENCY_OUTPUT = REPO / "england_map_web/data/aays_21_slots/future_growth_1/revision8_predecessor_dependency_validation_latest.json"
OUTPUT_VALIDATOR = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/automation/022_validate_revision8_runner_output_v1.py"
RUNNER_OUTPUT = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/006_official_geometry_pipeline_v8_latest.json"
OUTPUT_VALIDATION = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/validation/036_revision8_runner_output_runtime_validation_latest.json"
BUNDLE_OUTPUT = REPO / "docs/chatgpt_status/aays1/shards/future_growth_1/validation/038_revision8_runtime_evidence_bundle_latest.json"
WEB_ACCEPTANCE = REPO / "england_map_web/data/aays_21_slots/future_growth_1/revision8_runtime_acceptance_latest.json"

WRAPPER_TIMEOUT_SECONDS = 5200
STAGE_TIMEOUTS = {"stall_selftest": 120, "stall_diagnostic": 120, "dependency_selftest": 120, "bundle_selftest": 180, "dependency_validation": 120, "core_pipeline": 4500, "runner_output_validation": 300, "bundle_validation": 600}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _terminate_process_tree(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], text=True, capture_output=True, check=False, timeout=30)
        except Exception:
            proc.kill()
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            proc.kill()


def run_bounded(command: list[str], stage: str, timeout_seconds: float, deadline: float) -> dict[str, Any]:
    started = time.monotonic()
    remaining = max(0.0, deadline - started)
    effective_timeout = min(float(timeout_seconds), remaining)
    if effective_timeout <= 0:
        return {"stage": stage, "command": command, "exit_code": 124, "timed_out": True, "timeout_seconds": 0, "stdout": "", "stderr": "global wrapper deadline exhausted", "elapsed_seconds": 0.0}
    kwargs: dict[str, Any] = {"cwd": REPO, "text": True, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    proc = subprocess.Popen(command, **kwargs)
    timed_out = False
    try:
        stdout, stderr = proc.communicate(timeout=effective_timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _terminate_process_tree(proc)
        try:
            stdout, stderr = proc.communicate(timeout=30)
        except Exception:
            stdout, stderr = "", "process tree cleanup did not return output"
    elapsed = round(time.monotonic() - started, 3)
    return {"stage": stage, "command": command, "exit_code": 124 if timed_out else int(proc.returncode or 0), "timed_out": timed_out, "timeout_seconds": round(effective_timeout, 3), "stdout": (stdout or "")[-16000:], "stderr": (stderr or "")[-16000:], "elapsed_seconds": elapsed}


def parse_json_stdout(result: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(result.get("stdout") or "")
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def blocked(status: str, detail: Any, started: float) -> int:
    write_json(WEB_ACCEPTANCE, {"schema_version": 3, "slot_id": "future_growth_1", "state": "BLOCKED", "status": status, "detail": detail, "wrapper_elapsed_seconds": round(time.monotonic() - started, 3), "runner_execution_claimed": False, "business_progress_claimed": False, "actual_business_data_rows_written": 0, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False})
    return 2


def main() -> int:
    started = time.monotonic()
    deadline = started + WRAPPER_TIMEOUT_SECONDS
    required = [CORE_BOOTSTRAP, QUEUE_VALIDATOR, QUEUE_SELFTEST, DEPENDENCY_VALIDATOR, DEPENDENCY_SELFTEST, BUNDLE_VALIDATOR, BUNDLE_SELFTEST, STALL_VALIDATOR, STALL_SELFTEST, QUEUE_MANIFEST, SLOT_STATUS, HEARTBEAT, OWNERSHIP, PREDECESSOR_STATUS, OUTPUT_VALIDATOR]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        return blocked("BLOCKED_RUNTIME_REQUIRED_FILE_MISSING", missing, started)
    stall_selftest_run = run_bounded([sys.executable, str(STALL_SELFTEST)], "stall_selftest", STAGE_TIMEOUTS["stall_selftest"], deadline)
    stall_selftest = parse_json_stdout(stall_selftest_run)
    if stall_selftest_run["exit_code"] != 0 or stall_selftest.get("result") != "12/12 PASS":
        return blocked("BLOCKED_STALL_SELFTEST", {"process": stall_selftest_run, "result": stall_selftest}, started)
    stall_run = run_bounded([sys.executable, str(STALL_VALIDATOR), str(QUEUE_MANIFEST), str(SLOT_STATUS), str(HEARTBEAT), str(OWNERSHIP), str(PREDECESSOR_STATUS), str(RUNNER_OUTPUT), "--output", str(STALL_OUTPUT)], "stall_diagnostic", STAGE_TIMEOUTS["stall_diagnostic"], deadline)
    stall = read_json(STALL_OUTPUT) if STALL_OUTPUT.is_file() else {}
    if stall_run["exit_code"] != 0 or stall.get("result") != "PASS":
        return blocked(str(stall.get("classification") or "BLOCKED_STALL_DIAGNOSTIC"), {"process": stall_run, "diagnostic": stall}, started)
    dependency_selftest_run = run_bounded([sys.executable, str(DEPENDENCY_SELFTEST)], "dependency_selftest", STAGE_TIMEOUTS["dependency_selftest"], deadline)
    dependency_selftest = parse_json_stdout(dependency_selftest_run)
    if dependency_selftest_run["exit_code"] != 0 or dependency_selftest.get("result") != "10/10 PASS":
        return blocked("BLOCKED_PREDECESSOR_DEPENDENCY_SELFTEST", {"process": dependency_selftest_run, "result": dependency_selftest}, started)
    bundle_selftest_run = run_bounded([sys.executable, str(BUNDLE_SELFTEST)], "bundle_selftest", STAGE_TIMEOUTS["bundle_selftest"], deadline)
    bundle_selftest = parse_json_stdout(bundle_selftest_run)
    if bundle_selftest_run["exit_code"] != 0 or bundle_selftest.get("result") != "13/13 PASS":
        return blocked("BLOCKED_RUNTIME_EVIDENCE_BUNDLE_SELFTEST", {"process": bundle_selftest_run, "result": bundle_selftest}, started)
    dependency_run = run_bounded([sys.executable, str(DEPENDENCY_VALIDATOR), str(QUEUE_MANIFEST), str(PREDECESSOR_STATUS), "--output", str(DEPENDENCY_OUTPUT)], "dependency_validation", STAGE_TIMEOUTS["dependency_validation"], deadline)
    dependency = read_json(DEPENDENCY_OUTPUT) if DEPENDENCY_OUTPUT.is_file() else {}
    if dependency_run["exit_code"] != 0 or dependency.get("result") != "PASS" or dependency.get("dependency_complete") is not True or dependency.get("checks_passed") != 19:
        return blocked("BLOCKED_PREDECESSOR_DEPENDENCY_NOT_COMPLETE", {"process": dependency_run, "result": dependency}, started)
    core_run = run_bounded([sys.executable, str(CORE_BOOTSTRAP)], "core_pipeline", STAGE_TIMEOUTS["core_pipeline"], deadline)
    if core_run["exit_code"] != 0:
        return blocked("BLOCKED_CORE_ENTRY_TIMEOUT" if core_run["timed_out"] else "BLOCKED_CORE_ENTRY", core_run, started)
    if not RUNNER_OUTPUT.is_file():
        return blocked("BLOCKED_RUNNER_OUTPUT_MISSING_AFTER_CORE", core_run, started)
    output_validation_run = run_bounded([sys.executable, str(OUTPUT_VALIDATOR), str(RUNNER_OUTPUT), "--output", str(OUTPUT_VALIDATION)], "runner_output_validation", STAGE_TIMEOUTS["runner_output_validation"], deadline)
    output_validation = read_json(OUTPUT_VALIDATION) if OUTPUT_VALIDATION.is_file() else {}
    if output_validation_run["exit_code"] != 0 or output_validation.get("result") != "PASS" or output_validation.get("checks_passed") != 58 or output_validation.get("checks_total") != 58:
        return blocked("BLOCKED_RUNNER_OUTPUT_ACCEPTANCE", {"process": output_validation_run, "result": output_validation}, started)
    bundle_validation_run = run_bounded([sys.executable, str(BUNDLE_VALIDATOR), str(REPO), str(QUEUE_MANIFEST), "--output", str(BUNDLE_OUTPUT)], "bundle_validation", STAGE_TIMEOUTS["bundle_validation"], deadline)
    bundle_validation = read_json(BUNDLE_OUTPUT) if BUNDLE_OUTPUT.is_file() else {}
    if bundle_validation_run["exit_code"] != 0 or bundle_validation.get("result") != "PASS" or bundle_validation.get("checks_passed") != 64 or bundle_validation.get("checks_total") != 64:
        return blocked("BLOCKED_RUNTIME_EVIDENCE_BUNDLE_ACCEPTANCE", {"process": bundle_validation_run, "result": bundle_validation}, started)
    write_json(WEB_ACCEPTANCE, {"schema_version": 3, "slot_id": "future_growth_1", "state": "COMPLETED_RUNTIME_ACCEPTANCE", "status": "COMPLETED_STALL_GUARD_BOUNDED_CORE_58_OUTPUT_AND_64_BUNDLE_GATES", "stall_diagnostic": stall, "dependency_validation": dependency, "runner_output_validation": output_validation, "runtime_evidence_bundle_validation": bundle_validation, "wrapper_elapsed_seconds": round(time.monotonic() - started, 3), "runner_execution_claimed": True, "business_progress_claimed": False, "actual_business_data_rows_written": 0, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Static fail-closed validator for the stall-resistant revision-8 runtime wrapper."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SLOT_ID = "future_growth_1"


def validate_text(text: str) -> dict:
    stall_self = text.find('run_bounded([sys.executable, str(STALL_SELFTEST)]')
    stall_run = text.find('run_bounded([sys.executable, str(STALL_VALIDATOR)')
    dep_self = text.find('run_bounded([sys.executable, str(DEPENDENCY_SELFTEST)]')
    bundle_self = text.find('run_bounded([sys.executable, str(BUNDLE_SELFTEST)]')
    dep_run = text.find('run_bounded([sys.executable, str(DEPENDENCY_VALIDATOR)')
    core_run = text.find('run_bounded([sys.executable, str(CORE_BOOTSTRAP)]')
    out_run = text.find('run_bounded([sys.executable, str(OUTPUT_VALIDATOR)')
    bundle_run = text.find('run_bounded([sys.executable, str(BUNDLE_VALIDATOR)')
    accept = text.find('"state": "COMPLETED_RUNTIME_ACCEPTANCE"')
    checks = {
        "bootstrap_path_exact": "future_growth_1_official_geometry_entry_v8_bootstrap.py" in text,
        "queue_validator_v2_exact": "030_validate_revision8_queue_request_contract_v2.py" in text,
        "queue_selftest_v2_exact": "031_selftest_revision8_queue_request_contract_v2.py" in text,
        "stall_validator_exact": "040_validate_revision8_stall_state_v1.py" in text,
        "stall_selftest_exact": "041_selftest_revision8_stall_state_v1.py" in text,
        "dependency_validator_exact": "034_validate_revision8_predecessor_dependency_v1.py" in text,
        "dependency_selftest_exact": "035_selftest_revision8_predecessor_dependency_v1.py" in text,
        "bundle_validator_exact": "036_validate_revision8_runtime_evidence_bundle_v1.py" in text,
        "bundle_selftest_exact": "037_selftest_revision8_runtime_evidence_bundle_v1.py" in text,
        "global_deadline_5200": "WRAPPER_TIMEOUT_SECONDS = 5200" in text and "deadline = started + WRAPPER_TIMEOUT_SECONDS" in text,
        "bounded_popen_used": "subprocess.Popen(command, **kwargs)" in text and "proc.communicate(timeout=effective_timeout)" in text,
        "timeout_expired_handled": "except subprocess.TimeoutExpired" in text and '"exit_code": 124 if timed_out' in text,
        "windows_tree_kill": '["taskkill", "/PID", str(proc.pid), "/T", "/F"]' in text,
        "posix_tree_kill": "os.killpg(proc.pid, signal.SIGKILL)" in text,
        "new_process_group": "subprocess.CREATE_NEW_PROCESS_GROUP" in text and 'kwargs["start_new_session"] = True' in text,
        "stall_selftest_before_stall": 0 <= stall_self < stall_run,
        "stall_before_dependency": 0 <= stall_run < dep_self < bundle_self < dep_run,
        "dependency_before_core": 0 <= dep_run < core_run,
        "core_before_output": 0 <= core_run < out_run,
        "output_before_bundle": 0 <= out_run < bundle_run,
        "bundle_before_acceptance": 0 <= bundle_run < accept,
        "core_timeout_bounded": '"core_pipeline": 4500' in text,
        "timeout_status_explicit": "BLOCKED_CORE_ENTRY_TIMEOUT" in text,
        "no_direct_network_call": all(token not in text for token in ("urlopen(", "requests.get(", "httpx.get(")),
        "no_business_or_final_claim": all(token not in text for token in ('actual_business_data_rows_written": 1', 'final_ready": True', 'business_progress_claimed": True')),
    }
    failed = [key for key, value in checks.items() if not value]
    return {"schema_version": 4, "slot_id": SLOT_ID, "validation_kind": "REVISION8_STALL_RESISTANT_BOUNDED_RUNTIME_STATIC_FAIL_CLOSED", "result": "PASS" if not failed else "FAIL", "checks_passed": sum(checks.values()), "checks_total": len(checks), "checks": checks, "failed_checks": failed, "runner_execution_claimed": False, "business_progress_claimed": False, "final_ready": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wrapper", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = validate_text(args.wrapper.read_text(encoding="utf-8"))
    except Exception as exc:
        result = {"schema_version": 4, "slot_id": SLOT_ID, "validation_kind": "REVISION8_STALL_RESISTANT_BOUNDED_RUNTIME_STATIC_FAIL_CLOSED", "result": "FAIL", "checks_passed": 0, "checks_total": 1, "checks": {"read": False}, "failed_checks": [f"{type(exc).__name__}:{exc}"], "runner_execution_claimed": False, "business_progress_claimed": False, "final_ready": False}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if result["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

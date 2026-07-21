#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
ATTEMPT_ID = "height-difference-2-20260721-020"
BRANCH = "codex/aays-single-runner-v5-20260706"
HELPER_BLOB = "b3a18bcdb1b7158d18aab33b42d5797342d23cd1"
OPERATOR_BLOB = "1632d6d7467c21d0ba0bfdd880a137afb2f905f3"
TARGET_ROWS = [30762, 46142, 61522]


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    helper_path = root / "docs/chatgpt_status/topography/shards/height_difference_2/automation/026_restart_existing_canonical_f_runner_if_stale.ps1"
    operator_path = root / "docs/chatgpt_status/topography/shards/height_difference_2/automation/030_apply_attempt_020_existing_f_runner_recovery.ps1"
    queue_path = root / "docs/chatgpt_status/aays1/queue/0000_001_height_difference_2_canonical_export_official_sampling_20260720.task.json"
    request_path = root / "docs/chatgpt_status/_shared/status/reboot_runner_start_request_20260721_height_difference_2_001.json"
    control_path = root / "docs/chatgpt_status/_shared/control/request_queue_refresh.json"

    helper = helper_path.read_text(encoding="utf-8-sig")
    operator = operator_path.read_text(encoding="utf-8-sig")
    helper_actual_blob = git_blob_sha(helper_path)
    operator_actual_blob = git_blob_sha(operator_path)
    queue: dict[str, Any] = json.loads(queue_path.read_text(encoding="utf-8-sig"))
    request: dict[str, Any] = json.loads(request_path.read_text(encoding="utf-8-sig"))
    control: dict[str, Any] = json.loads(control_path.read_text(encoding="utf-8-sig"))

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("helper_blob_actual", helper_actual_blob == HELPER_BLOB, f"actual={helper_actual_blob}")
    check("operator_blob_actual", operator_actual_blob == OPERATOR_BLOB, f"actual={operator_actual_blob}")
    check("helper_attempt_020", ATTEMPT_ID in helper and "height-difference-2-20260721-019" not in helper, "Restart receipt is bound only to attempt 020.")
    check("helper_single_architecture", "existing_single_runner_architecture_reused = $true" in helper and "new_runner_architecture_created = $false" in helper and "parallel_runner_started = $false" in helper, "Helper preserves the single-runner architecture.")
    check("helper_multiple_process_fail_closed", "BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES" in helper and "BLOCKED_MULTIPLE_PERSISTENT_DAEMONS_AFTER_START" in helper, "Multiple canonical processes fail closed.")
    check("helper_existing_daemon_preserved", "CANONICAL_PERSISTENT_DAEMON_ALREADY_ACTIVE_NO_NEW_PROCESS" in helper, "One existing daemon is preserved without a second start.")
    check("helper_exact_rows_receipt", "exact_target_rows = @(30762,46142,61522)" in helper and "nearest_row_fallback_allowed = $false" in helper, "Receipt records the exact-row gate.")
    check("operator_attempt_020", ATTEMPT_ID in operator and TASK_ID in operator, "Operator entry is tied to the same task and attempt.")
    check("operator_exact_f_root", "F:\\TerraYield_AAYS_Portable\\runner_system\\AAYS_WT\\AAYS_RUNNER_HEALTHY_20260707" in operator, "Operator entry is pinned to the canonical F repo.")
    check("operator_branch_exact", BRANCH in operator and "BLOCKED_CANONICAL_BRANCH_MISMATCH" in operator, "Branch mismatch fails closed.")
    check("operator_dirty_repo_blocked", "status --porcelain" in operator and "BLOCKED_CANONICAL_F_REPO_DIRTY" in operator, "Uncommitted local changes prevent reset.")
    check("operator_fetches_exact_branch", "fetch origin $branch --prune" in operator and 'rev-parse "origin/$branch"' in operator, "Only the exact remote branch is fetched and read.")
    check("operator_reset_only_when_needed", "$localBefore -ne $remoteHead" in operator and 'reset --hard "origin/$branch"' in operator, "Clean repo is reset only when local and remote heads differ.")
    check("operator_remote_readback", "BLOCKED_REMOTE_HEAD_NOT_APPLIED" in operator and "$localAfter -ne $remoteHead" in operator, "Local head must match remote head after synchronization.")
    check("operator_helper_blob_gate", HELPER_BLOB in operator and "BLOCKED_ATTEMPT_020_HELPER_BLOB_MISMATCH" in operator, "Exact helper blob is verified before invocation.")
    check("operator_invokes_only_helper", "-File $helper" in operator and "Start-Process" not in operator, "Operator entry delegates process decisions only to the guarded helper.")
    check("operator_receipt_path", "015_operator_recovery_preflight_latest.json" in operator, "Operator preflight writes a deterministic receipt path.")
    check("operator_safety_flags", all(token in operator for token in ["new_runner_architecture_created = $false", "parallel_runner_started = $false", "fake_data = $false", "db_write = $false", "migration = $false", "production_deploy = $false"]), "Safety flags remain false.")
    check("queue_attempt_and_helper", queue.get("task_id") == TASK_ID and queue.get("attempt_id") == ATTEMPT_ID and queue.get("restart_helper_blob_sha") == HELPER_BLOB, "Queue binds the exact task, attempt and helper blob.")
    check("queue_operator_blob", queue.get("operator_recovery_blob_sha") == OPERATOR_BLOB, "Queue binds the exact operator entry blob.")
    check("queue_exact_target_gate", queue.get("sample_rows") == TARGET_ROWS and queue.get("measurement_contract", {}).get("nearest_row_fallback_allowed") is False, "Queue requires exact target rows and no nearest fallback.")
    check("request_attempt_and_helper", request.get("task_id") == TASK_ID and request.get("attempt_id") == ATTEMPT_ID and request.get("required_restart_helper_blob_sha") == HELPER_BLOB, "Restart request binds attempt 020 and the helper blob.")
    check("request_operator_blob", request.get("required_operator_recovery_blob_sha") == OPERATOR_BLOB, "Restart request binds the operator entry blob.")
    check("control_attempt_and_helper", control.get("task_id") == TASK_ID and control.get("attempt_id") == ATTEMPT_ID and control.get("required_restart_helper_blob_sha") == HELPER_BLOB, "Queue refresh control binds attempt 020 and the helper blob.")
    check("control_operator_blob", control.get("required_operator_recovery_blob_sha") == OPERATOR_BLOB, "Queue refresh control binds the operator entry blob.")

    passed = sum(1 for item in checks if item["passed"])
    payload = {
        "schema_version": 2,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "helper_actual_blob_sha": helper_actual_blob,
        "operator_actual_blob_sha": operator_actual_blob,
        "operator_recovery_executed": False,
        "runner_restart_observed": False,
        "product_rows_promoted": 0,
        "static_contract_only": True,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": passed == len(checks), "passed": passed, "total": len(checks)}))
    return 0 if passed == len(checks) else 2


if __name__ == "__main__":
    raise SystemExit(main())

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
TASK_VERSION = "6.2-fhost-safe-ffonly-terrain50-webfloor"
HELPER_BLOB = "b3a18bcdb1b7158d18aab33b42d5797342d23cd1"
OPERATOR_BLOB = "69d19c82d6a380fdcee7423e21bf978c15406b7d"
CARRIER_BLOB = "771d8b01fbc550c8d49b480470943dbb11f3e18b"
ENTRYPOINT_BLOB = "77627e136f9a45ff1ec998fb33bc94ea2d17d794"
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
    carrier_path = root / "docs/chatgpt_status/topography/shards/height_difference_2/automation/043_height_difference_2_shared_runner_carrier.ps1"
    entrypoint_path = root / "docs/chatgpt_status/aays1/automation/height_difference_2_reconciled_candidate_then_sampling_entry.py"
    queue_path = root / "docs/chatgpt_status/aays1/queue/0000_001_height_difference_2_canonical_export_official_sampling_20260720.task.json"
    request_path = root / "docs/chatgpt_status/_shared/status/reboot_runner_start_request_20260721_height_difference_2_001.json"

    helper = helper_path.read_text(encoding="utf-8-sig")
    operator = operator_path.read_text(encoding="utf-8-sig")
    carrier = carrier_path.read_text(encoding="utf-8-sig")
    entrypoint = entrypoint_path.read_text(encoding="utf-8-sig")
    helper_actual_blob = git_blob_sha(helper_path)
    operator_actual_blob = git_blob_sha(operator_path)
    carrier_actual_blob = git_blob_sha(carrier_path)
    entrypoint_actual_blob = git_blob_sha(entrypoint_path)
    queue: dict[str, Any] = json.loads(queue_path.read_text(encoding="utf-8-sig"))
    request: dict[str, Any] = json.loads(request_path.read_text(encoding="utf-8-sig"))

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("helper_blob_actual", helper_actual_blob == HELPER_BLOB, f"actual={helper_actual_blob}")
    check("operator_blob_actual", operator_actual_blob == OPERATOR_BLOB, f"actual={operator_actual_blob}")
    check("carrier_blob_actual", carrier_actual_blob == CARRIER_BLOB, f"actual={carrier_actual_blob}")
    check("entrypoint_blob_actual", entrypoint_actual_blob == ENTRYPOINT_BLOB, f"actual={entrypoint_actual_blob}")
    check("helper_attempt_020", ATTEMPT_ID in helper and "height-difference-2-20260721-019" not in helper, "Restart receipt is bound only to attempt 020.")
    check("helper_single_architecture", "existing_single_runner_architecture_reused = $true" in helper and "new_runner_architecture_created = $false" in helper and "parallel_runner_started = $false" in helper, "Helper preserves the single-runner architecture.")
    check("helper_multiple_process_fail_closed", "BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES" in helper and "BLOCKED_MULTIPLE_PERSISTENT_DAEMONS_AFTER_START" in helper, "Multiple canonical processes fail closed.")
    check("helper_existing_daemon_preserved", "CANONICAL_PERSISTENT_DAEMON_ALREADY_ACTIVE_NO_NEW_PROCESS" in helper, "One existing daemon is preserved without a second start.")
    check("helper_exact_rows_receipt", "exact_target_rows = @(30762,46142,61522)" in helper and "nearest_row_fallback_allowed = $false" in helper, "Receipt records the exact-row gate.")
    check("operator_attempt_020", ATTEMPT_ID in operator and TASK_ID in operator, "Operator entry is tied to the same task and attempt.")
    check("operator_exact_f_root", "F:\\TerraYield_AAYS_Portable\\runner_system\\AAYS_WT\\AAYS_RUNNER_HEALTHY_20260707" in operator, "Operator entry is pinned to the canonical F repo.")
    check("operator_branch_exact", BRANCH in operator and "BLOCKED_CANONICAL_BRANCH_MISMATCH" in operator, "Branch mismatch fails closed.")
    check("operator_dirty_repo_preserved", "stash','push','--include-untracked'" in operator and "stash_auto_restore_attempted = $false" in operator and "BLOCKED_CANONICAL_REPO_NOT_CLEAN_AFTER_STASH" in operator, "Dirty and untracked state is snapshotted/stashed and never auto-popped.")
    check("operator_atomic_fetch", "fetch','--atomic','origin',$branch,'--prune'" in operator and 'rev-parse', "Atomic fetch and exact remote readback are present.")
    check("operator_hard_reset_forbidden", "reset --hard" not in operator and "hard_reset_used = $false" in operator, "Hard reset is absent and explicitly forbidden in the receipt.")
    check("operator_ff_only_gate", "merge-base','--is-ancestor'" in operator and "merge','--ff-only'" in operator and "BLOCKED_CANONICAL_NON_FF_DIVERGENCE" in operator, "Only fast-forward synchronization is allowed; divergence fails closed.")
    check("operator_remote_readback", "BLOCKED_REMOTE_HEAD_NOT_APPLIED" in operator and "$localAfter -ne $remoteHead" in operator, "Local head must exactly match remote head after synchronization.")
    check("operator_helper_blob_gate", HELPER_BLOB in operator and "BLOCKED_ATTEMPT_020_HELPER_BLOB_MISMATCH" in operator, "Exact helper blob is verified before invocation.")
    check("operator_receipt_path", "015_operator_recovery_preflight_latest.json" in operator and "016_operator_git_snapshot_latest.json" in operator, "Deterministic recovery and dirty-state receipts are present.")
    check("operator_safety_flags", all(token in operator for token in ["new_runner_architecture_created = $false", "parallel_runner_started = $false", "fake_data = $false", "db_write = $false", "migration = $false", "production_deploy = $false"]), "Safety flags remain false.")
    check("carrier_v62_web_floor", TASK_VERSION in carrier and "$expectedWebRows = 1036" in carrier and ENTRYPOINT_BLOB in carrier, "Carrier is aligned to v6.2, 1036 web floor and exact entrypoint blob.")
    check("entrypoint_v62_web_floor", TASK_VERSION in entrypoint and 'AAYS_HEIGHT_DIFFERENCE_2_EXPECTED_WEB_ROWS", "1036"' in entrypoint, "Entrypoint fallback matches the queue web floor.")
    check("queue_task_and_helper", queue.get("task_id") == TASK_ID and queue.get("attempt_id") == ATTEMPT_ID and queue.get("restart_helper_blob_sha") == HELPER_BLOB, "Queue binds the exact task, attempt and helper blob.")
    check("queue_v62_pins", queue.get("task_version") == TASK_VERSION and queue.get("operator_recovery_blob_sha") == OPERATOR_BLOB and queue.get("script_blob_sha") == CARRIER_BLOB and queue.get("python_script_blob_sha") == ENTRYPOINT_BLOB, "Queue pins v6.2 operator, carrier and entrypoint blobs.")
    check("queue_safe_sync", queue.get("hard_reset_forbidden") is True and queue.get("fast_forward_only_required") is True and "atomic_fetch_ff_only_exact_head" in queue.get("runner_contract_modes", []), "Queue requires ff-only exact-head synchronization and forbids hard reset.")
    check("queue_exact_target_gate", queue.get("sample_rows") == TARGET_ROWS and queue.get("measurement_contract", {}).get("nearest_row_fallback_allowed") is False, "Queue requires exact target rows and no nearest fallback.")
    check("queue_web_floor", int(queue.get("expected_web_operation_rows", 0)) >= 1036, "Queue requires port 8012 web floor >=1036.")
    check("request_v62_pins", request.get("task_id") == TASK_ID and request.get("attempt_id") == ATTEMPT_ID and request.get("task_version") == TASK_VERSION and request.get("required_operator_recovery_blob_sha") == OPERATOR_BLOB and request.get("required_carrier_blob_sha") == CARRIER_BLOB and request.get("required_entrypoint_blob_sha") == ENTRYPOINT_BLOB, "Slot-specific restart request pins the same v6.2 recovery chain.")
    check("request_safe_sync", request.get("hard_reset_forbidden") is True and request.get("fast_forward_only_required") is True and int(request.get("expected_web_operation_rows", 0)) >= 1036, "Restart request requires ff-only synchronization and the 1036 web floor.")

    passed = sum(1 for item in checks if item["passed"])
    payload = {
        "schema_version": 3,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "task_version": TASK_VERSION,
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "helper_actual_blob_sha": helper_actual_blob,
        "operator_actual_blob_sha": operator_actual_blob,
        "carrier_actual_blob_sha": carrier_actual_blob,
        "entrypoint_actual_blob_sha": entrypoint_actual_blob,
        "operator_recovery_executed": False,
        "runner_restart_observed": False,
        "product_rows_promoted": 0,
        "static_contract_only": True,
        "shared_global_queue_refresh_control_not_pinned": True,
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

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
TASK_VERSION = "6.3-fhost-safe-ffonly-terrain50-webacceptance"
PICKUP_REVISION = 11
HELPER_BLOB = "b3a18bcdb1b7158d18aab33b42d5797342d23cd1"
OPERATOR_BLOB = "4565641e078f7058d7946a29c3da411f87be5572"
CARRIER_BLOB = "c3d25055ae182590c382327df09040ab65b8223a"
ENTRYPOINT_BLOB = "ff6656beb3e8db7d658e03e8373185cc6e500b3b"
NUMERIC_GATE_BLOB = "c2633df7a1a0ed7cebdf27331ca44b8bcd0872b1"
WEB_VERIFIER_BLOB = "f4fd5ecdcee6fed79b2cdd42452eb8f8398abae1"
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
    automation = root / "docs/chatgpt_status/topography/shards/height_difference_2/automation"
    helper_path = automation / "026_restart_existing_canonical_f_runner_if_stale.ps1"
    operator_path = automation / "030_apply_attempt_020_existing_f_runner_recovery.ps1"
    carrier_path = automation / "043_height_difference_2_shared_runner_carrier.ps1"
    numeric_gate_path = automation / "014_run_official_numeric_gate.py"
    web_verifier_path = automation / "017_verify_height_difference_2_web_8012.py"
    entrypoint_path = root / "docs/chatgpt_status/aays1/automation/height_difference_2_reconciled_candidate_then_sampling_entry.py"
    queue_path = root / "docs/chatgpt_status/aays1/queue/0000_001_height_difference_2_canonical_export_official_sampling_20260720.task.json"
    request_path = root / "docs/chatgpt_status/_shared/status/reboot_runner_start_request_20260721_height_difference_2_001.json"

    helper = helper_path.read_text(encoding="utf-8-sig")
    operator = operator_path.read_text(encoding="utf-8-sig")
    carrier = carrier_path.read_text(encoding="utf-8-sig")
    entrypoint = entrypoint_path.read_text(encoding="utf-8-sig")
    numeric_gate = numeric_gate_path.read_text(encoding="utf-8-sig")
    web_verifier = web_verifier_path.read_text(encoding="utf-8-sig")
    actual = {
        "helper": git_blob_sha(helper_path),
        "operator": git_blob_sha(operator_path),
        "carrier": git_blob_sha(carrier_path),
        "entrypoint": git_blob_sha(entrypoint_path),
        "numeric_gate": git_blob_sha(numeric_gate_path),
        "web_verifier": git_blob_sha(web_verifier_path),
    }
    queue: dict[str, Any] = json.loads(queue_path.read_text(encoding="utf-8-sig"))
    request: dict[str, Any] = json.loads(request_path.read_text(encoding="utf-8-sig"))

    checks: list[dict[str, Any]] = []
    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    expected_blobs = {
        "helper": HELPER_BLOB,
        "operator": OPERATOR_BLOB,
        "carrier": CARRIER_BLOB,
        "entrypoint": ENTRYPOINT_BLOB,
        "numeric_gate": NUMERIC_GATE_BLOB,
        "web_verifier": WEB_VERIFIER_BLOB,
    }
    for name, expected in expected_blobs.items():
        check(f"{name}_blob_actual", actual[name] == expected, f"actual={actual[name]}")

    check("helper_attempt_020", ATTEMPT_ID in helper and "height-difference-2-20260721-019" not in helper, "Helper is bound only to attempt 020.")
    check("helper_single_runner_fail_closed", all(token in helper for token in ["existing_single_runner_architecture_reused = $true", "new_runner_architecture_created = $false", "parallel_runner_started = $false", "BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES", "CANONICAL_PERSISTENT_DAEMON_ALREADY_ACTIVE_NO_NEW_PROCESS"]), "Helper preserves the existing single runner and fails closed on ambiguity.")
    check("operator_exact_root_and_branch", BRANCH in operator and "F:\\TerraYield_AAYS_Portable\\runner_system\\AAYS_WT\\AAYS_RUNNER_HEALTHY_20260707" in operator and "BLOCKED_CANONICAL_BRANCH_MISMATCH" in operator, "Operator is pinned to the canonical F repo and branch.")
    check("operator_snapshot_race_safe", all(token in operator for token in ["snapshot_capture_phase = 'memory_before_stash_fetch_sync'", "snapshot_publication_phase = 'receipt_exit_after_sync_or_on_blocked_exit'", "function Publish-Snapshot", "Publish-Snapshot", "snapshot_required_for_clean_and_dirty = $true"]), "Git state is captured before synchronization but 016 is published only on receipt exit.")
    check("operator_dirty_state_preserved", "stash','push','--include-untracked'" in operator and "stash_auto_restore_attempted = $false" in operator, "Dirty/untracked state is stashed with no auto-pop.")
    check("operator_ff_only_no_reset", "fetch','--atomic','origin',$branch,'--prune'" in operator and "merge-base','--is-ancestor'" in operator and "merge','--ff-only'" in operator and "reset --hard" not in operator and "hard_reset_used = $false" in operator, "Synchronization is atomic-fetch + ancestry-gated ff-only; hard reset is forbidden.")
    check("operator_remote_exact_head", "BLOCKED_REMOTE_HEAD_NOT_APPLIED" in operator and "$localAfter -ne $remoteHead" in operator, "Local HEAD must equal remote after synchronization.")
    check("operator_receipts", "015_operator_recovery_preflight_latest.json" in operator and "016_operator_git_snapshot_latest.json" in operator, "015 and deterministic 016 receipts are bound.")
    check("carrier_revision_and_web_floor", TASK_VERSION in carrier and f"$pickupRequestRevision = {PICKUP_REVISION}" in carrier and "$expectedWebRows = 1036" in carrier and ENTRYPOINT_BLOB in carrier and "PORT_8012_ACCEPTANCE_REQUIRED=true" in carrier and "PORT_8012_CURRENT_CANDIDATE_SHA256_REQUIRED=true" in carrier and "PORT_8012_OPERATION_FILE_PATH_GUARD_REQUIRED=true" in carrier, "Carrier revision and current web-byte guards are aligned.")
    check("entrypoint_requires_web_pass", TASK_VERSION in entrypoint and 'numeric_payload.get("web_acceptance_passed") is True' in entrypoint and "THREE_OFFICIAL_NUMERIC_ROWS_AND_PORT_8012_ACCEPTANCE_READY_PENDING_REVIEW" in entrypoint, "Entrypoint cannot succeed on numeric rows alone.")
    check("numeric_gate_current_candidate_sha", '"--expected-candidates-sha256"' in numeric_gate and "preacceptance_candidates_sha256" in numeric_gate and 'web_payload.get("candidate_http_sha256") == expected_candidates_sha256' in numeric_gate and 'web_payload.get("current_candidate_bytes_verified") is True' in numeric_gate, "Numeric orchestrator binds the HTTP candidate bytes to the exact preacceptance file SHA256.")
    check("numeric_gate_exact_rows", "official numeric exact row set mismatch" in numeric_gate and "[30762, 46142, 61522]" in numeric_gate, "Numeric gate itself rejects a non-exact three-row set.")
    check("web_verifier_current_candidate_sha", "expected-candidates-sha256" in web_verifier and "candidate HTTP SHA256 mismatch" in web_verifier and "current_candidate_bytes_verified" in web_verifier and TASK_ID in web_verifier and ATTEMPT_ID in web_verifier, "Port8012 verifier requires current candidate bytes and exact task/attempt binding.")
    check("web_verifier_operation_path_guard", "_safe_operation_file_name" in web_verifier and "operation file escapes slot root" in web_verifier and "operation_file_path_guard_verified" in web_verifier and "duplicate file names" in web_verifier, "Operation files are constrained to unique slot-local JSON basenames.")
    check("web_verifier_exact_rows", "TARGET_ROWS = [30762, 46142, 61522]" in web_verifier and "candidate exact row set mismatch" in web_verifier and "exact_target_rows_verified" in web_verifier, "Port8012 verifier binds exact target rows.")

    check("queue_identity", queue.get("task_id") == TASK_ID and queue.get("attempt_id") == ATTEMPT_ID and queue.get("task_version") == TASK_VERSION and queue.get("pickup_request_revision") == PICKUP_REVISION, "Queue identity and pickup revision match.")
    check("queue_blobs", queue.get("restart_helper_blob_sha") == HELPER_BLOB and queue.get("operator_recovery_blob_sha") == OPERATOR_BLOB and queue.get("script_blob_sha") == CARRIER_BLOB and queue.get("python_script_blob_sha") == ENTRYPOINT_BLOB and queue.get("official_numeric_gate_blob_sha") == NUMERIC_GATE_BLOB and queue.get("web_verifier_blob_sha") == WEB_VERIFIER_BLOB, "Queue pins the exact recovery/runtime blob set.")
    check("queue_recovery_policy", queue.get("git_snapshot_always_required") is True and queue.get("snapshot_capture_before_sync_required") is True and queue.get("snapshot_publication_after_sync_or_blocked_exit_required") is True and queue.get("hard_reset_forbidden") is True and queue.get("fast_forward_only_required") is True, "Queue pins race-safe snapshot and ff-only/no-reset recovery.")
    check("queue_exact_data_and_web", queue.get("sample_rows") == TARGET_ROWS and queue.get("web_exact_target_rows_required") == TARGET_ROWS and int(queue.get("expected_web_operation_rows", 0)) >= 1036 and queue.get("web_acceptance_status_required") == "PORT_8012_WEB_ACCEPTANCE_PASSED" and queue.get("web_current_candidate_sha256_required") is True and queue.get("web_operation_file_path_guard_required") is True, "Queue binds exact targets, current candidate SHA and safe operation paths.")

    check("request_identity", request.get("task_id") == TASK_ID and request.get("attempt_id") == ATTEMPT_ID and request.get("task_version") == TASK_VERSION and request.get("request_revision") == PICKUP_REVISION and request.get("required_pickup_request_revision") == PICKUP_REVISION, "Restart request identity/revision match queue and carrier.")
    check("request_blobs", request.get("required_restart_helper_blob_sha") == HELPER_BLOB and request.get("required_operator_recovery_blob_sha") == OPERATOR_BLOB and request.get("required_carrier_blob_sha") == CARRIER_BLOB and request.get("required_entrypoint_blob_sha") == ENTRYPOINT_BLOB and request.get("required_official_numeric_gate_blob_sha") == NUMERIC_GATE_BLOB and request.get("required_web_verifier_blob_sha") == WEB_VERIFIER_BLOB, "Restart request pins the exact runtime blob set.")
    check("request_recovery_and_web", request.get("snapshot_capture_before_sync_required") is True and request.get("snapshot_publication_after_sync_or_blocked_exit_required") is True and request.get("hard_reset_forbidden") is True and request.get("fast_forward_only_required") is True and request.get("web_exact_target_rows_required") == TARGET_ROWS and request.get("web_acceptance_status_required") == "PORT_8012_WEB_ACCEPTANCE_PASSED" and request.get("web_current_candidate_sha256_required") is True and request.get("web_operation_file_path_guard_required") is True, "Restart request matches race-safe recovery and current-byte exact-row web acceptance.")

    passed = sum(1 for item in checks if item["passed"])
    payload = {
        "schema_version": 8,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "task_version": TASK_VERSION,
        "pickup_request_revision": PICKUP_REVISION,
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "actual_blob_sha": actual,
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

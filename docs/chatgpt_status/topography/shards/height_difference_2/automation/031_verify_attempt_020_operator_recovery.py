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
TASK_VERSION = "6.4-terrain50-accuracy-screening-web-integrity"
PICKUP_REVISION = 12
TARGET_ROWS = [30762, 46142, 61522]
EXPECTED = {
    "helper": "b3a18bcdb1b7158d18aab33b42d5797342d23cd1",
    "operator": "4565641e078f7058d7946a29c3da411f87be5572",
    "carrier": "69e09b9e06dc82615a79ca832bd522cf8185e399",
    "entrypoint": "842ec93f6218025d583ee720cd56bce6ef2fb462",
    "numeric_gate": "c2633df7a1a0ed7cebdf27331ca44b8bcd0872b1",
    "terrain_resolver": "90e87710cba7a63df01ab058b335d5bc570dc9f6",
    "terrain_crosschecker": "9f4a652392017c74c5dd2f8cec899e114ccdc2d6",
    "terrain_wrapper": "8ce81728c2eca74f8b14f3b3675c09ec393e06a5",
    "web_verifier": "f4fd5ecdcee6fed79b2cdd42452eb8f8398abae1",
}


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
    paths = {
        "helper": automation / "026_restart_existing_canonical_f_runner_if_stale.ps1",
        "operator": automation / "030_apply_attempt_020_existing_f_runner_recovery.ps1",
        "carrier": automation / "043_height_difference_2_shared_runner_carrier.ps1",
        "entrypoint": root / "docs/chatgpt_status/aays1/automation/height_difference_2_reconciled_candidate_then_sampling_entry.py",
        "numeric_gate": automation / "014_run_official_numeric_gate.py",
        "terrain_resolver": automation / "015_resolve_os_terrain50_downloads.py",
        "terrain_crosschecker": automation / "013_crosscheck_os_terrain50.py",
        "terrain_wrapper": automation / "016_prepare_and_crosscheck_os_terrain50.py",
        "web_verifier": automation / "017_verify_height_difference_2_web_8012.py",
    }
    text = {name: path.read_text(encoding="utf-8-sig") for name, path in paths.items()}
    actual = {name: git_blob_sha(path) for name, path in paths.items()}
    queue: dict[str, Any] = json.loads((root / "docs/chatgpt_status/aays1/queue/0000_001_height_difference_2_canonical_export_official_sampling_20260720.task.json").read_text(encoding="utf-8-sig"))
    request: dict[str, Any] = json.loads((root / "docs/chatgpt_status/_shared/status/reboot_runner_start_request_20260721_height_difference_2_001.json").read_text(encoding="utf-8-sig"))

    checks: list[dict[str, Any]] = []
    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    for name, expected in EXPECTED.items():
        check(f"{name}_blob_actual", actual[name] == expected, f"actual={actual[name]}")

    helper = text["helper"]
    operator = text["operator"]
    carrier = text["carrier"]
    entrypoint = text["entrypoint"]
    numeric_gate = text["numeric_gate"]
    wrapper = text["terrain_wrapper"]
    web_verifier = text["web_verifier"]

    check("single_runner", all(token in helper for token in ["existing_single_runner_architecture_reused = $true", "new_runner_architecture_created = $false", "parallel_runner_started = $false", "BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES"]), "Existing single-runner architecture is preserved.")
    check("operator_safe_sync", BRANCH in operator and "snapshot_capture_phase = 'memory_before_stash_fetch_sync'" in operator and "stash','push','--include-untracked'" in operator and "merge','--ff-only'" in operator and "reset --hard" not in operator, "Recovery preserves state and uses ff-only without hard reset.")
    check("carrier_v64", TASK_VERSION in carrier and f"$pickupRequestRevision = {PICKUP_REVISION}" in carrier and EXPECTED["entrypoint"] in carrier and EXPECTED["terrain_resolver"] in carrier and EXPECTED["terrain_crosschecker"] in carrier and EXPECTED["terrain_wrapper"] in carrier, "Carrier pins v6.4 entrypoint and complete Terrain50 chain.")
    check("carrier_accuracy_contract", all(token in carrier for token in ["TERRAIN50_OS_GRID_RMSE_M=4.0", "EA_DTM1M_RMSE_M=0.15", "TERRAIN50_CONSERVATIVE_ONE_RMSE_SUM_M=4.15", "TERRAIN50_CONSERVATIVE_TWO_RMSE_SUM_M=8.30", "TERRAIN50_TWO_RMSE_SCREENING_IS_NOT_CONFIDENCE_INTERVAL=true"]), "Carrier publishes the evidence-based conservative screening contract.")
    check("wrapper_accuracy_contract", all(token in wrapper for token in ["OS_TERRAIN50_GRID_RMSE_M = 4.0", "EA_LIDAR_DTM_RMSE_M = 0.15", "CONSERVATIVE_ONE_RMSE_SUM_M", "CONSERVATIVE_TWO_RMSE_SUM_M", "OUTSIDE_CONSERVATIVE_TWO_RMSE_SUM_BLOCK", "confidence_interval_claimed\": False"]), "Terrain50 wrapper blocks deltas outside the conservative two-RMSE-sum screen without claiming a confidence interval.")
    check("entrypoint_accuracy_gate", TASK_VERSION in entrypoint and 'terrain_payload.get("accuracy_screening_passed") is True' in entrypoint and "THREE_SOURCE_OFFICIAL_NUMERIC_ACCURACY_AND_WEB_GATE_EXECUTED" in entrypoint, "Entrypoint requires Terrain50 accuracy screening plus numeric and web gates.")
    check("numeric_current_web_bytes", '"--expected-candidates-sha256"' in numeric_gate and "preacceptance_candidates_sha256" in numeric_gate and 'web_payload.get("current_candidate_bytes_verified") is True' in numeric_gate, "Numeric gate binds HTTP candidates to the bytes it just wrote.")
    check("web_path_and_identity_guard", "_safe_operation_file_name" in web_verifier and "candidate payload slot/task/attempt binding mismatch" in web_verifier and "candidate HTTP SHA256 mismatch" in web_verifier and "operation_file_path_guard_verified" in web_verifier, "Web acceptance verifies current candidate bytes, identity and slot-local operation paths.")

    check("queue_identity", queue.get("task_id") == TASK_ID and queue.get("attempt_id") == ATTEMPT_ID and queue.get("task_version") == TASK_VERSION and queue.get("pickup_request_revision") == PICKUP_REVISION, "Queue identity/version/revision match.")
    check("queue_runtime_blobs", queue.get("restart_helper_blob_sha") == EXPECTED["helper"] and queue.get("operator_recovery_blob_sha") == EXPECTED["operator"] and queue.get("script_blob_sha") == EXPECTED["carrier"] and queue.get("python_script_blob_sha") == EXPECTED["entrypoint"] and queue.get("official_numeric_gate_blob_sha") == EXPECTED["numeric_gate"] and queue.get("terrain50_resolver_blob_sha") == EXPECTED["terrain_resolver"] and queue.get("terrain50_crosschecker_blob_sha") == EXPECTED["terrain_crosschecker"] and queue.get("terrain50_wrapper_blob_sha") == EXPECTED["terrain_wrapper"] and queue.get("web_verifier_blob_sha") == EXPECTED["web_verifier"], "Queue pins the complete runtime blob set.")
    check("queue_accuracy_web_contract", queue.get("sample_rows") == TARGET_ROWS and queue.get("terrain50_accuracy_screening_required") is True and float(queue.get("terrain50_conservative_two_rmse_sum_m", 0)) == 8.3 and queue.get("terrain50_two_rmse_screening_is_confidence_interval") is False and queue.get("web_current_candidate_sha256_required") is True and queue.get("web_operation_file_path_guard_required") is True and int(queue.get("expected_web_operation_rows", 0)) >= 1036, "Queue requires exact targets, accuracy screening and current-byte web acceptance.")
    check("request_identity", request.get("task_id") == TASK_ID and request.get("attempt_id") == ATTEMPT_ID and request.get("task_version") == TASK_VERSION and request.get("request_revision") == PICKUP_REVISION and request.get("required_pickup_request_revision") == PICKUP_REVISION, "Restart request revision matches queue/carrier.")
    check("request_runtime_blobs", request.get("required_carrier_blob_sha") == EXPECTED["carrier"] and request.get("required_entrypoint_blob_sha") == EXPECTED["entrypoint"] and request.get("required_official_numeric_gate_blob_sha") == EXPECTED["numeric_gate"] and request.get("required_terrain50_resolver_blob_sha") == EXPECTED["terrain_resolver"] and request.get("required_terrain50_crosschecker_blob_sha") == EXPECTED["terrain_crosschecker"] and request.get("required_terrain50_wrapper_blob_sha") == EXPECTED["terrain_wrapper"] and request.get("required_web_verifier_blob_sha") == EXPECTED["web_verifier"] and request.get("required_operator_recovery_blob_sha") == EXPECTED["operator"], "Restart request pins the same runtime chain.")
    check("request_accuracy_web_contract", request.get("terrain50_accuracy_screening_required") is True and float(request.get("terrain50_conservative_two_rmse_sum_m", 0)) == 8.3 and request.get("terrain50_two_rmse_screening_is_confidence_interval") is False and request.get("web_current_candidate_sha256_required") is True and request.get("web_operation_file_path_guard_required") is True, "Restart request matches accuracy and web-integrity safeguards.")

    passed = sum(1 for item in checks if item["passed"])
    payload = {
        "schema_version": 9,
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

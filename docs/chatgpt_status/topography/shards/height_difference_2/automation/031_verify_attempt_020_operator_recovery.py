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
TASK_VERSION = "6.6-preweb-height-metric-gate"
PICKUP_REVISION = 16
TARGET_ROWS = [30762, 46142, 61522]
EXPECTED_HMLR = {"30762": "46058185", "46142": "39866294", "61522": "62045430"}
EXPECTED_HEIGHTS = {"30762": 0.27, "46142": 0.831, "61522": 0.49}
EA_COVERAGE_ID = "13787b9a-26a4-4775-8523-806d13af58fc__Lidar_Composite_Elevation_DTM_1m"
EXPECTED = {
    "helper": "b3a18bcdb1b7158d18aab33b42d5797342d23cd1",
    "operator": "4565641e078f7058d7946a29c3da411f87be5572",
    "carrier": "72ce15f9c0fe96cc1aa7813d288d1ad4e2f14e19",
    "entrypoint": "54e301461379b1f0688d7fc651ce633420fca258",
    "numeric_gate": "5bab5fda5a25dbc67dd1aa219aae961b8acf1368",
    "metric_guard": "f9b70ef7adc1d2d3673501e0b82a992d230efc2f",
    "terrain_resolver": "90e87710cba7a63df01ab058b335d5bc570dc9f6",
    "terrain_crosschecker": "9f4a652392017c74c5dd2f8cec899e114ccdc2d6",
    "terrain_wrapper": "8ce81728c2eca74f8b14f3b3675c09ec393e06a5",
    "web_verifier": "84a560369b1c589aa1b74965f3c8c2ebc91e3caf",
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
        "metric_guard": automation / "018_verify_current_height_difference_metric.py",
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
    metric_guard = text["metric_guard"]
    numeric_gate = text["numeric_gate"]
    wrapper = text["terrain_wrapper"]
    web_verifier = text["web_verifier"]

    check("single_runner", all(token in helper for token in ["existing_single_runner_architecture_reused = $true", "new_runner_architecture_created = $false", "parallel_runner_started = $false", "BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES"]), "Existing single-runner architecture is preserved.")
    check("operator_safe_sync", BRANCH in operator and "snapshot_capture_phase = 'memory_before_stash_fetch_sync'" in operator and "stash','push','--include-untracked'" in operator and "merge','--ff-only'" in operator and "reset --hard" not in operator, "Recovery preserves state and uses ff-only without hard reset.")
    check("carrier_v66_rev16", TASK_VERSION in carrier and f"$pickupRequestRevision = {PICKUP_REVISION}" in carrier and EXPECTED["entrypoint"] in carrier and EXPECTED["metric_guard"] in carrier and EXPECTED["numeric_gate"] in carrier and EXPECTED["web_verifier"] in carrier, "Carrier pins revision16 entrypoint, metric guard, numeric and web chain.")
    check("carrier_metric_order", all(token in carrier for token in ["CURRENT_HEIGHT_DIFFERENCE_METRIC_MUST_PASS_BEFORE_TERRAIN50_AND_WEB=true", "CURRENT_CANDIDATE_HEIGHT_DIFFERENCE_FIELD=height_difference_m", "CURRENT_CANDIDATE_MEDIAN_ELEVATION_IS_DISTINCT=true", "PORT_8012_CURRENT_CANDIDATE_METRIC_BINDING_REQUIRED=true"]), "Carrier publishes pre-web metric and candidate-binding safeguards.")
    check("carrier_ea_coverage_pin", EA_COVERAGE_ID in carrier and "$env:AAYS_EA_DTM1M_COVERAGE_ID = $expectedEaCoverageId" in carrier, "Carrier pins exact EA Elevation DTM1m CoverageId.")
    check("entrypoint_preweb_metric_gate", all(token in entrypoint for token in [TASK_VERSION, "--preserved-metric-evidence", "--height-metric-tolerance-m", "height_metric_must_pass_before_terrain_and_web", "current_candidate_metric_contract_passed"]), "Entrypoint delegates metric consistency into numeric gate before Terrain50/web and checks current candidate metric contract.")
    check("metric_guard_contract", all(token in metric_guard for token in [EA_COVERAGE_ID, "max_m - min_m", "preserved_height_difference_m", "parcel_elevation_median_m_odn", "current EA parcel height-difference drift"]), "Metric guard separates parcel range from median elevation and fails closed on drift.")
    check("numeric_preweb_metric_order", all(token in numeric_gate for token in ["CURRENT_HEIGHT_DIFFERENCE_METRIC_CONSISTENCY", "SKIPPED_CURRENT_HEIGHT_METRIC_GATE_FAILED", "height_difference_m", "parcel_elevation_median_m_odn", "height_metric_consistency_passed", "current_candidate_metric_binding_verified"]), "Numeric gate runs metric guard before Terrain50/web and writes explicit range plus distinct median fields.")
    check("web_current_metric_binding", all(token in web_verifier for token in ["EXPECTED_METRIC", "current candidate metric contract mismatch", "current candidate max-minus-min self-check failed", "current_candidate_metric_binding_verified"]), "Web verifier independently binds current local candidate bytes to exact range metric and confidence.")
    check("carrier_accuracy_contract", all(token in carrier for token in ["TERRAIN50_OS_GRID_RMSE_M=4.0", "EA_DTM1M_RMSE_M=0.15", "TERRAIN50_CONSERVATIVE_ONE_RMSE_SUM_M=4.15", "TERRAIN50_CONSERVATIVE_TWO_RMSE_SUM_M=8.30", "TERRAIN50_TWO_RMSE_SCREENING_IS_NOT_CONFIDENCE_INTERVAL=true"]), "Carrier preserves conservative Terrain50 screening.")
    check("wrapper_accuracy_contract", all(token in wrapper for token in ["OS_TERRAIN50_GRID_RMSE_M = 4.0", "EA_LIDAR_DTM_RMSE_M = 0.15", "CONSERVATIVE_ONE_RMSE_SUM_M", "CONSERVATIVE_TWO_RMSE_SUM_M", "OUTSIDE_CONSERVATIVE_TWO_RMSE_SUM_BLOCK", "confidence_interval_claimed\": False"]), "Terrain50 wrapper blocks outside conservative two-RMSE-sum screen.")
    check("web_fullsite_guard", all(token in web_verifier for token in ["port8012 base host is not loopback", "expected_visible_source_rows", "expected_visible_example_rows", "EXPECTED_SITE_BINDINGS", "site_exact_measurement_binding_verified"]), "Web verifier preserves loopback/full-site exact binding guards.")

    check("queue_identity", queue.get("task_id") == TASK_ID and queue.get("attempt_id") == ATTEMPT_ID and queue.get("task_version") == TASK_VERSION and queue.get("pickup_request_revision") == PICKUP_REVISION, "Queue identity/version/revision match.")
    check("queue_runtime_blobs", queue.get("restart_helper_blob_sha") == EXPECTED["helper"] and queue.get("operator_recovery_blob_sha") == EXPECTED["operator"] and queue.get("script_blob_sha") == EXPECTED["carrier"] and queue.get("python_script_blob_sha") == EXPECTED["entrypoint"] and queue.get("official_numeric_gate_blob_sha") == EXPECTED["numeric_gate"] and queue.get("height_metric_guard_blob_sha") == EXPECTED["metric_guard"] and queue.get("terrain50_resolver_blob_sha") == EXPECTED["terrain_resolver"] and queue.get("terrain50_crosschecker_blob_sha") == EXPECTED["terrain_crosschecker"] and queue.get("terrain50_wrapper_blob_sha") == EXPECTED["terrain_wrapper"] and queue.get("web_verifier_blob_sha") == EXPECTED["web_verifier"], "Queue pins complete revision16 runtime blob set.")
    check("queue_metric_contract", queue.get("ea_dtm1m_coverage_id") == EA_COVERAGE_ID and queue.get("ea_dtm1m_coverage_id_pin_required") is True and queue.get("height_metric_consistency_required") is True and queue.get("height_metric_must_pass_before_terrain50_and_web") is True and float(queue.get("height_metric_tolerance_m", -1)) == 0.001 and queue.get("parcel_elevation_median_is_distinct_metric") is True and queue.get("current_candidate_height_difference_field") == "height_difference_m" and queue.get("current_candidate_metric_binding_required") is True, "Queue requires exact EA coverage, pre-web max-minus-min metric consistency and exact local candidate metric binding.")
    check("queue_metric_output_path", "docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs/008_official_numeric_gate_latest/current_height_metric_consistency.json" in queue.get("expected_outputs", []) and "docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs/009_current_height_metric_consistency_latest.json" not in queue.get("expected_outputs", []), "Queue expects the metric receipt owned by the numeric gate and no stale 009 receipt.")
    check("queue_accuracy_web_contract", queue.get("sample_rows") == TARGET_ROWS and queue.get("terrain50_accuracy_screening_required") is True and float(queue.get("terrain50_conservative_two_rmse_sum_m", 0)) == 8.3 and queue.get("web_loopback_only_required") is True and queue.get("web_exact_hmlr_bindings_required") == EXPECTED_HMLR and queue.get("web_exact_height_difference_bindings_m") == EXPECTED_HEIGHTS and queue.get("web_current_candidate_metric_binding_required") is True and float(queue.get("web_min_result_confidence_percent", 0)) >= 96 and int(queue.get("expected_web_operation_rows", 0)) >= 1036, "Queue retains Terrain50 and full-site/current-candidate web safeguards.")
    check("request_identity", request.get("task_id") == TASK_ID and request.get("attempt_id") == ATTEMPT_ID and request.get("task_version") == TASK_VERSION and request.get("request_revision") == PICKUP_REVISION and request.get("required_pickup_request_revision") == PICKUP_REVISION, "Restart request revision matches queue/carrier.")
    check("request_runtime_blobs", request.get("required_carrier_blob_sha") == EXPECTED["carrier"] and request.get("required_entrypoint_blob_sha") == EXPECTED["entrypoint"] and request.get("required_official_numeric_gate_blob_sha") == EXPECTED["numeric_gate"] and request.get("required_height_metric_guard_blob_sha") == EXPECTED["metric_guard"] and request.get("required_terrain50_resolver_blob_sha") == EXPECTED["terrain_resolver"] and request.get("required_terrain50_crosschecker_blob_sha") == EXPECTED["terrain_crosschecker"] and request.get("required_terrain50_wrapper_blob_sha") == EXPECTED["terrain_wrapper"] and request.get("required_web_verifier_blob_sha") == EXPECTED["web_verifier"] and request.get("required_operator_recovery_blob_sha") == EXPECTED["operator"], "Restart request pins same revision16 runtime chain.")
    check("request_metric_contract", request.get("ea_dtm1m_coverage_id") == EA_COVERAGE_ID and request.get("ea_dtm1m_coverage_id_pin_required") is True and request.get("height_metric_consistency_required") is True and request.get("height_metric_must_pass_before_terrain50_and_web") is True and float(request.get("height_metric_tolerance_m", -1)) == 0.001 and request.get("parcel_elevation_median_is_distinct_metric") is True and request.get("current_candidate_metric_binding_required") is True, "Restart request matches rev16 metric semantics and order.")

    passed = sum(1 for item in checks if item["passed"])
    payload = {"schema_version": 13, "slot_id": "height_difference_2", "task_id": TASK_ID, "attempt_id": ATTEMPT_ID, "task_version": TASK_VERSION, "pickup_request_revision": PICKUP_REVISION, "status": "PASS" if passed == len(checks) else "FAIL", "passed": passed, "total": len(checks), "checks": checks, "actual_blob_sha": actual, "ea_coverage_id_required": EA_COVERAGE_ID, "height_metric_contract": "CURRENT_EA_MAX_MINUS_MIN_EXACT_HMLR_MATCHES_PRESERVED_WITHIN_0_001M_BEFORE_TERRAIN_AND_WEB", "current_candidate_metric_binding_required": True, "operator_recovery_executed": False, "runner_restart_observed": False, "product_rows_promoted": 0, "static_contract_only": True, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": passed == len(checks), "passed": passed, "total": len(checks)}))
    return 0 if passed == len(checks) else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

script = Path(__file__).with_name("036_run_coverage_aware_inner_carrier.ps1").read_text(encoding="utf-8")
checks = {
    "slot_scope": "internet_access_2" in script and "internet_access_3" not in script,
    "base_runner": "009_probe_download_slice_join_publish_slot2.ps1" in script,
    "coverage_extractor": "030_extract_slot2_coverage_aware_candidates.py" in script,
    "coverage_selftest": "031_selftest_extract_slot2_coverage_aware_candidates.py" in script,
    "coverage_selftest_20": "tests_passed -ne 20" in script and "tests_total -ne 20" in script,
    "exact_needle": '002_extract_slot2_ofcom_2026_candidates.py' in script,
    "exact_replacement": '030_extract_slot2_coverage_aware_candidates.py' in script,
    "replacement_count_one": "$replacementCount -ne 1" in script,
    "runtime_work_root": "internet_access_2_coverage_aware_inner_runtime.ps1" in script,
    "base_sha": "base_runner_sha256" in script and "Get-FileHash" in script,
    "runtime_sha": "runtime_carrier_sha256" in script,
    "carrier_output": "internet_access_2_coverage_aware_carrier_latest.json" in script,
    "failure_propagation": "exit $innerExitCode" in script,
    "no_business_write": "actual_business_data_rows_written = 0" in script and "scores_written = 0" in script,
    "no_db_migration_deploy": "db_write = $false" in script and "migration = $false" in script and "production_deploy = $false" in script,
    "not_final": "final_ready = $false" in script,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise AssertionError(f"failed: {failed}")
print(json.dumps({
    "status": "PASS",
    "tests_passed": len(checks),
    "tests_total": len(checks),
    "test_names": list(checks),
    "actual_business_data_rows_written": 0,
    "final_ready": False,
}, sort_keys=True))

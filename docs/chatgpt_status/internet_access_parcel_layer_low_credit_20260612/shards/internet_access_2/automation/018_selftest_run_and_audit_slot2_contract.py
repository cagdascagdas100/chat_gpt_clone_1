#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

script = Path(__file__).with_name("017_run_and_audit_slot2.ps1").read_text(encoding="utf-8")
checks = {
    "slot_scope": "internet_access_2" in script and "internet_access_3" not in script,
    "inner_runner": "009_probe_download_slice_join_publish_slot2.ps1" in script,
    "bundle_verifier": "015_verify_published_runner_bundle.py" in script,
    "bundle_selftest": "016_selftest_verify_published_runner_bundle.py" in script,
    "bundle_selftest_18": "tests_passed -ne 18" in script and "tests_total -ne 18" in script,
    "provenance_verifier": "019_verify_single_run_provenance.py" in script,
    "provenance_selftest": "020_selftest_verify_single_run_provenance.py" in script,
    "provenance_selftest_20": "tests_passed -ne 20" in script and "tests_total -ne 20" in script,
    "effective_work_root": 'outputs/internet_access_2_verified_run' in script and "$effectiveWorkRoot" in script,
    "bundle_audit_output": "runner_bundle_audit_latest.json" in script,
    "provenance_audit_output": "runner_provenance_audit_latest.json" in script,
    "bundle_audit_status": "PASS_REAL_RUN_WEB_BUNDLE_AUDITED_REVIEW_ONLY" in script,
    "provenance_audit_status": "PASS_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY" in script,
    "provenance_chain_output": "provenance_chain_sha256" in script,
    "exact_rows": "$expectedRows = 30761" in script,
    "inner_failure_propagated": "exit $LASTEXITCODE" in script,
    "no_business_write": "actual_business_data_rows_written = 0" in script,
    "no_scores": "scores_written = 0" in script,
    "no_db_migration": "db_write = $false" in script and "migration = $false" in script,
    "no_deploy": "production_deploy = $false" in script,
    "not_final": "final_ready = $false" in script,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise AssertionError(f"failed: {failed}")
print(json.dumps({"status": "PASS", "tests_passed": len(checks), "tests_total": len(checks), "test_names": list(checks), "actual_business_data_rows_written": 0, "final_ready": False}, sort_keys=True))

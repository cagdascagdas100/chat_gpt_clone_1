#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
script=Path(__file__).with_name("017_run_and_audit_slot2.ps1").read_text(encoding="utf-8")
checks={
"slot_scope":"internet_access_2" in script and "internet_access_3" not in script,
"inner_runner":"009_probe_download_slice_join_publish_slot2.ps1" in script,
"bundle_verifier":"015_verify_published_runner_bundle.py" in script,
"bundle_selftest":"016_selftest_verify_published_runner_bundle.py" in script,
"bundle_selftest_23":"tests_passed -ne 23" in script and "tests_total -ne 23" in script,
"candidate_verifier":"021_verify_candidate_jsonl_integrity.py" in script,
"candidate_selftest":"022_selftest_verify_candidate_jsonl_integrity.py" in script,
"candidate_selftest_25":"tests_passed -ne 25" in script and "tests_total -ne 25" in script,
"candidate_audit_output":"candidate_jsonl_integrity_latest.json" in script,
"candidate_audit_status":"PASS_COMPLETE_CANDIDATE_JSONL_INTEGRITY_REVIEW_ONLY" in script,
"candidate_sha_output":"candidate_rows_jsonl_sha256" in script,
"postcode_resolution_verifier":"028_validate_candidate_postcode_resolution.py" in script,
"postcode_resolution_selftest":"029_selftest_validate_candidate_postcode_resolution.py" in script,
"postcode_resolution_selftest_18":"tests_passed -ne 18" in script and "tests_total -ne 18" in script,
"postcode_resolution_before_candidate":script.index("$postcodeResolutionAuditRaw") < script.index("$candidateAuditRaw"),
"provenance_verifier":"019_verify_single_run_provenance.py" in script,
"provenance_selftest":"020_selftest_verify_single_run_provenance.py" in script,
"provenance_selftest_24":"tests_passed -ne 24" in script and "tests_total -ne 24" in script,
"consistency_verifier":"024_validate_review_contract_consistency.py" in script,
"consistency_selftest":"025_selftest_validate_review_contract_consistency.py" in script,
"consistency_selftest_14":"tests_passed -ne 14" in script and "tests_total -ne 14" in script,
"consistency_audit_output":"review_contract_consistency_latest.json" in script,
"consistency_audit_status":"PASS_REVIEW_CONTRACT_CONSISTENCY_AUDITED_REVIEW_ONLY" in script,
"combined_validation_314":"$expectedCombinedValidation = 314" in script and "combined_validation_total" in script,
"consistency_before_network":script.index("$consistencyAuditRaw") < script.index("$innerArgs"),
"effective_work_root":"outputs/internet_access_2_verified_run" in script and "$effectiveWorkRoot" in script,
"bundle_audit_output":"runner_bundle_audit_latest.json" in script,
"provenance_audit_output":"runner_provenance_audit_latest.json" in script,
"bundle_audit_status":"PASS_REAL_RUN_WEB_BUNDLE_AUDITED_REVIEW_ONLY" in script,
"provenance_audit_status":"PASS_SINGLE_RUN_PROVENANCE_CHAIN_AUDITED_REVIEW_ONLY" in script,
"provenance_chain_output":"provenance_chain_sha256" in script and "provenance_artifact_count -ne 12" in script and "zip_container_audit_sha256" in script,
"exact_rows":"$expectedRows = 30761" in script,
"inner_failure_propagated":"exit $LASTEXITCODE" in script,
"candidate_before_bundle":script.index("$candidateAuditRaw") < script.index("$bundleAuditRaw"),
"no_business_write":"actual_business_data_rows_written = 0" in script,
"no_scores":"scores_written = 0" in script,
"no_db_migration":"db_write = $false" in script and "migration = $false" in script,
"no_deploy":"production_deploy = $false" in script,
"not_final":"final_ready = $false" in script,
"schema_v6":"schema_version = 6" in script,
}
failed=[name for name,ok in checks.items() if not ok]
if failed: raise AssertionError(f"failed: {failed}")
print(json.dumps({"status":"PASS","tests_passed":len(checks),"tests_total":len(checks),"test_names":list(checks),"actual_business_data_rows_written":0,"final_ready":False},sort_keys=True))

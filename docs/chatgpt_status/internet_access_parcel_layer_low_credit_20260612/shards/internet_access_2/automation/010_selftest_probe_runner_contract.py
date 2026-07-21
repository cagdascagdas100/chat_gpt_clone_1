#!/usr/bin/env python3
"""Static contract checks for the slot-2 resilient runner orchestrator."""
from __future__ import annotations
import json
from pathlib import Path

script = Path(__file__).with_name("009_probe_download_slice_join_publish_slot2.ps1").read_text(encoding="utf-8")
checks = {
    "slot_scope": "internet_access_2" in script and "internet_access_3" not in script,
    "official_https_url": "https://www.ofcom.org.uk/" in script,
    "official_v2_date": '$officialV2Date = "2026-07-07"' in script,
    "outer_zip_r1_transport_name": 'official_outer_zip_filename = "202601_fixed_broadband_coverage_and_full_fibre_take-up-r1.zip"' in script,
    "outer_zip_r1_name_not_payload_revision": "outer_zip_r1_name_is_transport_container_only = $true" in script,
    "display_size_conflict_recorded": "official_page_display_size_mb_observations = @(32.2,32.3)" in script and 'official_page_display_size_consistency = "CONFLICTING_READBACK_METADATA_ONLY"' in script,
    "display_size_not_exact_integrity_gate": "official_listed_zip_size_mb =" not in script,
    "no_published_checksum_claim": "official_checksum_published = $false" in script,
    "runtime_integrity_basis": "RUNTIME_BYTE_COUNT_ZIP_SIGNATURE_SHA256_AND_INTERNAL_V2_VALIDATION" in script and "Get-FileHash -Algorithm SHA256" in script,
    "diagnostics_schema_v6": "schema_version = 6" in script,
    "dns_gate": "Resolve-DnsName" in script and "BLOCKED_DNS" in script,
    "retry_gate": "DownloadRetries" in script and "download_attempts" in script,
    "zip_size_gate": "30000000" in script,
    "zip_signature_gate": "0x50" in script and "0x4B" in script,
    "internal_r1_rejected": "r1 postcode files found" in script,
    "r2_exact_count": "Expected $expectedR2Count corrected r2 postcode files" in script,
    "v2_validator_present": "013_validate_ofcom_v2_corrections.py" in script,
    "v2_validator_selftest": "014_selftest_validate_ofcom_v2_corrections.py" in script and "Run-JsonSelftest $v2ValidatorSelftest 43" in script,
    "v2_semantic_status": "PASS_OFFICIAL_V2_R2_CORRECTION_AND_SEMANTICS_VALIDATED" in script,
    "cw_cv_duplicate_gate": "cw_not_cv_duplicate" in script,
    "mk_me_duplicate_gate": "mk_not_me_duplicate" in script,
    "postcode_files_directory_gate": "postcode_files_directory_validated" in script,
    "postcode_premise_count_gate": "postcode_premise_count_fields_present" in script,
    "all_percentage_columns_gate": "all_percentage_columns_range_validated" in script,
    "threshold_order_gate": "coverage_speed_threshold_order_validated" in script,
    "streaming_slice": "007_stream_extract_slot2_inputs.py" in script,
    "exact_slot_count": "$expectedRows = 30761" in script,
    "strict_publisher": "005_publish_slot2_readback.py" in script and "runner_readback_latest.json" in script,
    "no_business_write": "actual_business_data_rows_written = 0" in script,
    "no_deploy": "production_deploy = $false" in script and "direct_push = $false" in script,
    "final_not_ready": "final_ready = $false" in script,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise AssertionError(f"failed: {failed}")
print(json.dumps({"status": "PASS", "tests_passed": len(checks), "tests_total": len(checks), "test_names": list(checks), "business_rows_written": 0, "final_ready": False}, sort_keys=True))

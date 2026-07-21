#!/usr/bin/env python3
"""Static contract checks for the slot-2 resilient runner orchestrator."""
from __future__ import annotations
import json
from pathlib import Path

script = Path(__file__).with_name("009_probe_download_slice_join_publish_slot2.ps1").read_text(encoding="utf-8")
checks = {
    "slot_scope": "internet_access_2" in script and "internet_access_3" not in script,
    "official_https_url": "https://www.ofcom.org.uk/" in script,
    "dns_gate": "Resolve-DnsName" in script and "BLOCKED_DNS" in script,
    "retry_gate": "DownloadRetries" in script and "download_attempts" in script,
    "zip_size_gate": "30000000" in script,
    "zip_signature_gate": "0x50" in script and "0x4B" in script,
    "r1_rejected": "r1 postcode files found" in script,
    "r2_exact_count": "Expected $expectedR2Count corrected r2 postcode files" in script,
    "streaming_slice": "007_stream_extract_slot2_inputs.py" in script,
    "exact_slot_count": "$expectedRows = 30761" in script,
    "three_selftests": all(name in script for name in ["003_selftest_slot2_extractor.py", "008_selftest_stream_extract_slot2_inputs.py", "006_selftest_publish_slot2_readback.py"]),
    "strict_publisher": "005_publish_slot2_readback.py" in script and "runner_readback_latest.json" in script,
    "no_business_write": "actual_business_data_rows_written = 0" in script,
    "no_score": "scores_written = 0" in script,
    "no_deploy": "production_deploy = $false" in script and "direct_push = $false" in script,
    "final_not_ready": "final_ready = $false" in script,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise AssertionError(f"failed: {failed}")
print(json.dumps({"status": "PASS", "tests_passed": len(checks), "tests_total": len(checks), "business_rows_written": 0}, sort_keys=True))

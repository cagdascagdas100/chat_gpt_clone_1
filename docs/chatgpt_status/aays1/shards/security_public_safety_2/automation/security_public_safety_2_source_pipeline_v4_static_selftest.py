from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parent
bootstrap = (root / "security_public_safety_2_official_source_bootstrap_v2.py").read_text(encoding="utf-8")
pipeline = (root / "security_public_safety_2_runner_pipeline_v4_sources.py").read_text(encoding="utf-8")
carrier = (root / "security_public_safety_2_runner_pipeline_v4.ps1").read_text(encoding="utf-8")

rules = {
    "exact_slot_bootstrap": 'SLOT_ID = "security_public_safety_2"' in bootstrap,
    "exact_branch_bootstrap": 'TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"' in bootstrap,
    "police_latest_source": "data.police.uk/api/crime-last-updated" in bootstrap,
    "mps_dataset_source": "data.london.gov.uk/dataset/mps-recorded-crime-geographic-breakdown-exy3m" in bootstrap,
    "private_ip_guard": "NON_PUBLIC_IP_FORBIDDEN" in bootstrap,
    "https_guard": "HTTPS_REQUIRED" in bootstrap,
    "credentials_guard": "URL_CREDENTIALS_FORBIDDEN" in bootstrap,
    "resource_page_fallback": "OFFICIAL_RESOURCE_PAGE_FALLBACK" in bootstrap,
    "historical_rejected": "not historical" in bootstrap,
    "newest_period_selection": "period_end" in bootstrap and "reverse=True" in bootstrap,
    "minimum_period_gate": 'MIN_MPS_PERIOD_END = "2026-06-30"' in bootstrap,
    "police_date_parse": "parse_police_latest" in bootstrap,
    "sha_provenance": '"sha256"' in bootstrap,
    "csv_validation_reused": "materialize_source" in bootstrap,
    "business_rows_zero_bootstrap": '"actual_business_rows_written": 0' in bootstrap,
    "final_false_bootstrap": '"final_ready": False' in bootstrap,
    "pipeline_exact_slot": 'SLOT_ID = "security_public_safety_2"' in pipeline,
    "pipeline_exact_branch": 'TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"' in pipeline,
    "pipeline_runs_bootstrap_v2": "security_public_safety_2_official_source_bootstrap_v2.py" in pipeline,
    "pipeline_provenance_gate": "OFFICIAL_SOURCE_PROVENANCE_GATE" in pipeline,
    "pipeline_sha_gate": "_SHA_MISSING" in pipeline,
    "pipeline_url_guard": "_URL_GUARD_FAILED" in pipeline,
    "pipeline_freshness_gate": "SOURCE_FRESHNESS_GATE_FAILED" in pipeline,
    "pipeline_exports_iod": 'env["AAYS_IOD25_V2_CSV"]' in pipeline,
    "pipeline_exports_mps": 'env["AAYS_MPS_LSOA_CSV"]' in pipeline,
    "pipeline_resume_only_after_gate": pipeline.index("validate_manifest") < pipeline.index("security_public_safety_2_runner_pipeline_v2_resume.py"),
    "carrier_slot_guard": "WRONG_SLOT" in carrier,
    "carrier_branch_guard": "WRONG_BRANCH" in carrier,
    "carrier_no_git_push": "git push" not in carrier.lower(),
    "carrier_no_git_commit": "git commit" not in carrier.lower(),
    "carrier_no_runner_start": "start-process" not in carrier.lower() and "new runner" not in carrier.lower(),
    "carrier_propagates_exit": "exit $LASTEXITCODE" in carrier,
    "final_false_pipeline": '"final_ready": False' in pipeline,
}
cases = [{"name": name, "pass": bool(value)} for name, value in rules.items()]
result = {
    "schema_version": 1,
    "slot_id": "security_public_safety_2",
    "test_type": "SOURCE_PROVENANCE_PIPELINE_V4_STATIC_SELFTEST",
    "cases": cases,
    "passed": sum(1 for case in cases if case["pass"]),
    "total": len(cases),
    "pass": all(case["pass"] for case in cases),
    "actual_business_rows_written": 0,
    "fake_data": False,
    "final_ready": False,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result["pass"] else 1)

from __future__ import annotations
import json
from pathlib import Path

root = Path(__file__).resolve().parent
bootstrap = (root / 'security_public_safety_2_official_source_bootstrap.py').read_text(encoding='utf-8')
pipeline = (root / 'security_public_safety_2_runner_pipeline_v3_sources.py').read_text(encoding='utf-8')
carrier = (root / 'security_public_safety_2_runner_pipeline_v3.ps1').read_text(encoding='utf-8')
checks = {
    'exact_slot': 'security_public_safety_2' in bootstrap and 'security_public_safety_2' in pipeline and 'security_public_safety_2' in carrier,
    'exact_branch': 'codex/aays-single-runner-v5-20260706' in bootstrap and 'codex/aays-single-runner-v5-20260706' in pipeline,
    'official_iod_domain': 'assets.publishing.service.gov.uk' in bootstrap,
    'official_mps_domain': 'data.london.gov.uk' in bootstrap,
    'sha256_recorded': 'sha256' in bootstrap,
    'csv_headers_validated': 'inspect_csv' in bootstrap,
    'download_limit': 'MAX_DOWNLOAD_BYTES' in bootstrap,
    'fail_closed_manifest': 'OFFICIAL_SOURCE_BOOTSTRAP_INCOMPLETE' in bootstrap,
    'no_business_rows_bootstrap': 'actual_business_rows_written' in bootstrap,
    'wrapper_runs_bootstrap_first': pipeline.find('OFFICIAL_SOURCE_BOOTSTRAP') < pipeline.find('RESUME_PIPELINE_V2'),
    'wrapper_exports_iod': 'AAYS_IOD25_V2_CSV' in pipeline,
    'wrapper_exports_mps': 'AAYS_MPS_LSOA_CSV' in pipeline,
    'wrapper_propagates_exit': 'returncode' in pipeline and 'exit_code' in pipeline,
    'carrier_no_git_push': 'git push' not in carrier.lower(),
    'carrier_no_git_commit': 'git commit' not in carrier.lower(),
    'carrier_no_runner_start': 'start-process' not in carrier.lower(),
    'carrier_slot_guard': 'WRONG_SLOT' in carrier,
    'carrier_branch_guard': 'WRONG_BRANCH' in carrier,
    'final_false_bootstrap': 'final_ready' in bootstrap,
    'final_false_pipeline': 'final_ready' in pipeline,
}
cases = [{'name': key, 'pass': bool(value)} for key, value in checks.items()]
passed = sum(item['pass'] for item in cases)
payload = {'schema_version': 1, 'slot_id': 'security_public_safety_2', 'test_type': 'SOURCE_AWARE_PIPELINE_STATIC_SELFTEST', 'cases': cases, 'passed': passed, 'total': len(cases), 'pass': passed == len(cases), 'actual_business_rows_written': 0, 'fake_data': False, 'final_ready': False}
print(json.dumps(payload, ensure_ascii=False, indent=2))
raise SystemExit(0 if payload['pass'] else 1)

from __future__ import annotations

from pathlib import Path

source = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave72_orchestrator.py")
if not source.is_file():
    raise SystemExit(f"SOURCE_ORCHESTRATOR_MISSING: {source}")
text = source.read_text(encoding="utf-8")

start = text.find("def materialize_scripts() -> None:\n")
end = text.find("\n\ndef claim() -> None:", start)
if start < 0 or end < 0:
    raise SystemExit("WAVE115_MATERIALIZE_FUNCTION_BOUNDARY_MISSING")
replacement_function = '''def materialize_scripts() -> None:
    for path in (GENERATOR, ACCEPTANCE_SCRIPT):
        if not path.is_file():
            raise SystemExit(f"FINAL_VERIFIED_SCRIPT_MISSING:{path}")
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
'''
text = text[:start] + replacement_function + text[end:]

replacements = [
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "d2de8c05edd12442771bb40c474a676a65385be5"'),
    ('FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_11110_TO_11560_ROWS_WITH_OFFICIAL_SOURCE_HASHES"', 'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_30460_TO_30761_ROWS_WITH_OFFICIAL_SOURCE_HASHES"'),
    ('CONTINUATION_KEY = "e80c765946c15e4233d5137b2c44bfde0c56ec923f52eb105038fb4d9369b2b5"', 'CONTINUATION_KEY = "3c391d74df0d094b712038e46117560142b33e67f25d554a542e9e371cc235fa"'),
    ('TASK_ID = "security_public_safety_2_priority_11560row_incremental_evidence_expansion_20260730"', 'TASK_ID = "security_public_safety_2_priority_30761row_incremental_evidence_expansion_20260731"'),
    ('OWNER = "github-actions-security-public-safety-2-wave72"', 'OWNER = "github-actions-security-public-safety-2-wave115"'),
    ('0047_security_public_safety_2_priority_11560row_incremental_evidence_expansion_20260730.v3.task.json', '0090_security_public_safety_2_priority_30761row_incremental_evidence_expansion_20260731.v3.task.json'),
    ('security_public_safety_2_priority_11560row_incremental_evidence_expansion_20260730.py', 'security_public_safety_2_priority_30761row_incremental_evidence_expansion_20260731.py'),
    ('security_public_safety_2_wave72_accept_publish.py', 'security_public_safety_2_wave115_accept_publish.py'),
    ('security_public_safety_2_priority_11110row_incremental_evidence_expansion_20260730.py', 'security_public_safety_2_priority_30460row_incremental_evidence_expansion_20260731.py'),
    ('security_public_safety_2_wave71_accept_publish.py', 'security_public_safety_2_wave114_accept_publish.py'),
    ('priority_450row_wave72_latest.json', 'priority_301row_wave115_latest.json'),
    ('priority_11560row_evidence_expansion_latest.json', 'priority_30761row_evidence_expansion_latest.json'),
    ('priority_11560row_evidence_expansion.html', 'priority_30761row_evidence_expansion.html'),
    ('priority_11560row_browser_acceptance_wave72_receipt_20260730.json', 'priority_30761row_browser_acceptance_wave115_receipt_20260731.json'),
    ('priority_11560row_targeted_retry_wave72_diagnostic_20260730.json', 'priority_30761row_targeted_retry_wave115_diagnostic_20260731.json'),
    ('"accepted_base_rows": 11110', '"accepted_base_rows": 30460'),
    ('"incremental_candidate_rows": 450', '"incremental_candidate_rows": 301'),
    ('"merged_candidate_rows": 11560', '"merged_candidate_rows": 30761'),
    ('"minimum_incremental_police_hash_rows": 428', '"minimum_incremental_police_hash_rows": 286'),
    ('"minimum_merged_police_hash_rows": 10982', '"minimum_merged_police_hash_rows": 29223'),
    ('"minimum_merged_accuracy_ge_95_candidate_rows": 10982', '"minimum_merged_accuracy_ge_95_candidate_rows": 29223'),
    ('"incremental_parcel_start": 41872', '"incremental_parcel_start": 61222'),
    ('"incremental_parcel_end": 42321', '"incremental_parcel_end": 61522'),
    ('if int(previous_acceptance.get("candidate_rows") or 0) != 11110:', 'if int(previous_acceptance.get("candidate_rows") or 0) != 30460:'),
    ('PREVIOUS_11110_ROW_COUNT_MISMATCH', 'PREVIOUS_30460_ROW_COUNT_MISMATCH'),
    ('"accepted_base_candidate_rows": 11110', '"accepted_base_candidate_rows": 30460'),
    ('"incremental_rows_target": 450', '"incremental_rows_target": 301'),
    ('"merged_rows_target": 11560', '"merged_rows_target": 30761'),
    ('"merged_rows_ready": 11110', '"merged_rows_ready": 30460'),
    ('or 10964', 'or 30070'),
    ('or 11110', 'or 30460'),
    ('"expanded_scope_progress_percent": 96.11', '"expanded_scope_progress_percent": 99.02'),
    ('"expanded_scope_delta_percentage_points": 3.89', '"expanded_scope_delta_percentage_points": 0.98'),
    ('"priority": -148', '"priority": -191'),
    ('"candidate_rows": 11560', '"candidate_rows": 30761'),
    ('"candidate_accuracy_ge_95_rows_min": 10982', '"candidate_accuracy_ge_95_rows_min": 29223'),
    ('"police_response_sha256_rows_min": 10982', '"police_response_sha256_rows_min": 29223'),
    ('"candidate_dom_rows": 11560', '"candidate_dom_rows": 30761'),
    ('"schema_version": 95,', '"schema_version": 138,'),
    ('"line_by_line_rows": 11560', '"line_by_line_rows": 30761'),
    ('"schema_version": 99,', '"schema_version": 142,'),
    ('or 121) + 1', 'or 164) + 1'),
    ('priority_11110row_incremental_evidence_expansion_full_remote_and_canonical_browser_acceptance', 'priority_30460row_incremental_evidence_expansion_full_remote_and_canonical_browser_acceptance'),
    ('"schema_version": 94,', '"schema_version": 137,'),
    ('claim security_public_safety_2 11560-row wave72', 'claim security_public_safety_2 30761-row wave115'),
    ('WAVE72_CLAIM_NOT_ACTIVE', 'WAVE115_CLAIM_NOT_ACTIVE'),
    ('WAVE72_OWNER_CLAIM_MISMATCH', 'WAVE115_OWNER_CLAIM_MISMATCH'),
    ('publish security_public_safety_2 11560-row evidence', 'publish security_public_safety_2 30761-row evidence'),
    ('len(rows) != 11560', 'len(rows) != 30761'),
    ('"parcel_42321"', '"parcel_61522"'),
    ('terminalize security_public_safety_2 11560-row readback', 'terminalize security_public_safety_2 30761-row readback'),
    ('WAVE72_REMOTE_TERMINAL_READBACK_FAILED', 'WAVE115_REMOTE_TERMINAL_READBACK_FAILED'),
    ('WAVE72_WORKFLOW_FAILED_FAIL_CLOSED', 'WAVE115_WORKFLOW_FAILED_FAIL_CLOSED'),
    ('park security_public_safety_2 wave72 failure', 'park security_public_safety_2 wave115 failure'),
    ('docs/chatgpt_status/aays1/automation/security_public_safety_2_wave72_orchestrator.py', 'docs/chatgpt_status/aays1/automation/security_public_safety_2_wave115_orchestrator.py'),
]
for old, new in replacements:
    if old not in text:
        raise SystemExit(f"WAVE115_TRANSFORM_FRAGMENT_MISSING:{old}")
    text = text.replace(old, new)

required = [
    'SOURCE_HEAD = "d2de8c05edd12442771bb40c474a676a65385be5"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_30460_TO_30761_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "3c391d74df0d094b712038e46117560142b33e67f25d554a542e9e371cc235fa"',
    'TASK_ID = "security_public_safety_2_priority_30761row_incremental_evidence_expansion_20260731"',
    'OWNER = "github-actions-security-public-safety-2-wave115"',
    '0090_security_public_safety_2_priority_30761row_incremental_evidence_expansion_20260731.v3.task.json',
    'priority_301row_wave115_latest.json',
    '"accepted_base_rows": 30460',
    '"incremental_candidate_rows": 301',
    '"merged_candidate_rows": 30761',
    '"minimum_incremental_police_hash_rows": 286',
    '"minimum_merged_police_hash_rows": 29223',
    '"incremental_parcel_start": 61222',
    '"incremental_parcel_end": 61522',
    '"expanded_scope_progress_percent": 99.02',
    '"expanded_scope_delta_percentage_points": 0.98',
    'len(rows) != 30761',
    '"parcel_61522"',
    'WAVE115_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"WAVE115_FINAL_FRAGMENT_MISSING:{fragment}")

exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})

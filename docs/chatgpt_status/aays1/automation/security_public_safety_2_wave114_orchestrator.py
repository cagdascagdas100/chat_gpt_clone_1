from __future__ import annotations

from pathlib import Path

source = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave92_orchestrator.py")
if not source.is_file():
    raise SystemExit(f"SOURCE_ORCHESTRATOR_MISSING: {source}")
text = source.read_text(encoding="utf-8")

protected = [
    ("5ff2e96dd28181341b05845a7056945a6005a74c", "__SOURCE_HEAD__"),
    ("a3efcf9d82e085183979087a1bf0d2ea905fa427d3009fdccd73ac023f01ce92", "__PREVIOUS_CONTINUATION__"),
    ("bf2a19bc6e2fb5f8bf351bea31c340b142ca6735cf144d2e326809b4ecae3f1b", "__CURRENT_CONTINUATION__"),
    ("wave91", "__PREVIOUS_WAVE__"),
    ("wave92", "__CURRENT_WAVE__"),
    ("0066_", "__PREVIOUS_QUEUE__"),
    ("0067_", "__CURRENT_QUEUE__"),
    ("19660", "__ROWS_OLD_PREVIOUS__"),
    ("20110", "__ROWS_BASE__"),
    ("20560", "__ROWS_TARGET__"),
    ("19105", "__MIN_OLD_PREVIOUS__"),
    ("19532", "__MIN_CURRENT__"),
    ("19855", "__ACCURACY_BASE__"),
    ("50422", "__PARCEL_OLD_START__"),
    ("50872", "__PARCEL_START__"),
    ("51322", "__PARCEL_END_PLUS_ONE__"),
    ("50871", "__PARCEL_OLD_END__"),
    ("51321", "__PARCEL_END__"),
    ("2.24", "__DELTA_PREVIOUS__"),
    ("2.19", "__DELTA_CURRENT__"),
]
for old, token in protected:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_TRANSFORM_FRAGMENT_MISSING: {old}")
    text = text.replace(old, token)

direct = [
    (r'''('\"schema_version\": 69', '\"schema_version\": 70'),''', r'''('\"schema_version\": 91', '\"schema_version\": 92'),'''),
    ('"schema_version": 115,', '"schema_version": 137,'),
    ('"schema_version": 119,', '"schema_version": 141,'),
    ('"schema_version": 114,', '"schema_version": 136,'),
    ('or 141) + 1', 'or 163) + 1'),
    ('"priority": -168,', '"priority": -190,'),
    ('97.81', '98.52'),
    ('WAVE92', 'WAVE114'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__SOURCE_HEAD__", "6be0bd6ca0a62dfd54f5295d85933b312888efaa"),
    ("__PREVIOUS_CONTINUATION__", "56d98350cafe88a2f19a896be15a0bf30c76ec772f992d43cb30b2ca9e905189"),
    ("__CURRENT_CONTINUATION__", "56e3e62bf3872c903c92273cf1ee0c2aa6d5e182adf9c68f3822f9629f539183"),
    ("__PREVIOUS_WAVE__", "wave113"),
    ("__CURRENT_WAVE__", "wave114"),
    ("__PREVIOUS_QUEUE__", "0088_"),
    ("__CURRENT_QUEUE__", "0089_"),
    ("__ROWS_OLD_PREVIOUS__", "29560"),
    ("__ROWS_BASE__", "30010"),
    ("__ROWS_TARGET__", "30460"),
    ("__MIN_OLD_PREVIOUS__", "28510"),
    ("__MIN_CURRENT__", "28937"),
    ("__ACCURACY_BASE__", "29629"),
    ("__PARCEL_OLD_START__", "60322"),
    ("__PARCEL_START__", "60772"),
    ("__PARCEL_END_PLUS_ONE__", "61222"),
    ("__PARCEL_OLD_END__", "60771"),
    ("__PARCEL_END__", "61221"),
    ("__DELTA_PREVIOUS__", "1.50"),
    ("__DELTA_CURRENT__", "1.48"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

wrapper_old_target = "security_public_safety_2_priority_30460row_incremental_evidence_expansion_20260730"
wrapper_new_target = "security_public_safety_2_priority_30460row_incremental_evidence_expansion_20260731"
if wrapper_old_target not in text:
    raise SystemExit(f"ORCHESTRATOR_WRAPPER_TARGET_DATE_FRAGMENT_MISSING: {wrapper_old_target}")
text = text.replace(wrapper_old_target, wrapper_new_target)

inner_marker = "\nrequired = ["
inner_injection = '''
old_target_task = "security_public_safety_2_priority_30460row_incremental_evidence_expansion_20260730"
new_target_task = "security_public_safety_2_priority_30460row_incremental_evidence_expansion_20260731"
if old_target_task in text:
    text = text.replace(old_target_task, new_target_task)
elif new_target_task not in text:
    raise SystemExit(f"ORCHESTRATOR_TARGET_DATE_FRAGMENT_MISSING: {old_target_task}")
text = text.replace("priority_30460row_browser_acceptance_wave114_receipt_20260730", "priority_30460row_browser_acceptance_wave114_receipt_20260731")
text = text.replace("priority_30460row_targeted_retry_wave114_diagnostic_20260730", "priority_30460row_targeted_retry_wave114_diagnostic_20260731")
previous_generator_old = "security_public_safety_2_priority_30010row_incremental_evidence_expansion_20260730.py"
previous_generator_new = "security_public_safety_2_priority_30010row_incremental_evidence_expansion_20260731.py"
if previous_generator_old in text:
    text = text.replace(previous_generator_old, previous_generator_new)
elif previous_generator_new not in text:
    raise SystemExit(f"PREVIOUS_GENERATOR_DATE_FRAGMENT_MISSING: {previous_generator_old}")

acceptance_marker = '        acc = acc.replace(old, new)' + chr(10) + '    for fragment in ('
acceptance_patch = chr(10).join([
    '        acc = acc.replace(old, new)',
    '    old_acceptance_task = "security_public_safety_2_priority_30460row_incremental_evidence_expansion_20260730"',
    '    new_acceptance_task = "security_public_safety_2_priority_30460row_incremental_evidence_expansion_20260731"',
    '    if old_acceptance_task in acc:',
    '        acc = acc.replace(old_acceptance_task, new_acceptance_task)',
    '    elif new_acceptance_task not in acc:',
    '        raise SystemExit(f"ACCEPTANCE_TARGET_DATE_FRAGMENT_MISSING:{old_acceptance_task}")',
    '    acc = acc.replace("priority_30460row_browser_acceptance_wave114_receipt_20260730", "priority_30460row_browser_acceptance_wave114_receipt_20260731")',
    '    acc = acc.replace("priority_30460row_targeted_retry_wave114_diagnostic_20260730", "priority_30460row_targeted_retry_wave114_diagnostic_20260731")',
    '    for fragment in (',
])
if acceptance_marker not in text:
    raise SystemExit("ORCHESTRATOR_ACCEPTANCE_MARKER_MISSING")
text = text.replace(acceptance_marker, acceptance_patch, 1)

required = ['''
if inner_marker not in text:
    raise SystemExit("ORCHESTRATOR_INNER_REQUIRED_MARKER_MISSING")
text = text.replace(inner_marker, "\n" + inner_injection, 1)

required = [
    'SOURCE_HEAD = "6be0bd6ca0a62dfd54f5295d85933b312888efaa"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_30010_TO_30460_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "56e3e62bf3872c903c92273cf1ee0c2aa6d5e182adf9c68f3822f9629f539183"',
    'TASK_ID = "security_public_safety_2_priority_30460row_incremental_evidence_expansion_20260731"',
    'OWNER = "github-actions-security-public-safety-2-wave114"',
    '0089_security_public_safety_2_priority_30460row_incremental_evidence_expansion_20260731.v3.task.json',
    'priority_450row_wave114_latest.json',
    'priority_30460row_evidence_expansion_latest.json',
    '"accepted_base_rows": 30010',
    '"merged_candidate_rows": 30460',
    '"minimum_merged_police_hash_rows": 28937',
    '"incremental_parcel_start": 60772',
    '"incremental_parcel_end": 61221',
    '"expanded_scope_progress_percent": 98.52',
    '"expanded_scope_delta_percentage_points": 1.48',
    'len(rows) != 30460',
    '"parcel_61221"',
    'WAVE114_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})

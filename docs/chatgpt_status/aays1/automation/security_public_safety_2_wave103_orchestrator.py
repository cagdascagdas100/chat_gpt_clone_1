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
    (r'''('\"schema_version\": 69', '\"schema_version\": 70'),''', r'''('\"schema_version\": 80', '\"schema_version\": 81'),'''),
    ('"schema_version": 115,', '"schema_version": 126,'),
    ('"schema_version": 119,', '"schema_version": 130,'),
    ('"schema_version": 114,', '"schema_version": 125,'),
    ('or 141) + 1', 'or 152) + 1'),
    ('"priority": -168,', '"priority": -179,'),
    ('97.81', '98.24'),
    ('WAVE92', 'WAVE103'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__SOURCE_HEAD__", "902e11dbc64023c52b6a48fcaf936e3efbc72654"),
    ("__PREVIOUS_CONTINUATION__", "1bbc08a1ccfecb4f9338a4731fac72af44effa38bb512ce9fe09108a3a228444"),
    ("__CURRENT_CONTINUATION__", "bbf5266a5005f0dd7b09e450bf9f96af840df7acf2a123d2e42652451f619568"),
    ("__PREVIOUS_WAVE__", "wave102"),
    ("__CURRENT_WAVE__", "wave103"),
    ("__PREVIOUS_QUEUE__", "0077_"),
    ("__CURRENT_QUEUE__", "0078_"),
    ("__ROWS_OLD_PREVIOUS__", "24610"),
    ("__ROWS_BASE__", "25060"),
    ("__ROWS_TARGET__", "25510"),
    ("__MIN_OLD_PREVIOUS__", "23807"),
    ("__MIN_CURRENT__", "24235"),
    ("__ACCURACY_BASE__", "24742"),
    ("__PARCEL_OLD_START__", "55372"),
    ("__PARCEL_START__", "55822"),
    ("__PARCEL_END_PLUS_ONE__", "56272"),
    ("__PARCEL_OLD_END__", "55821"),
    ("__PARCEL_END__", "56271"),
    ("__DELTA_PREVIOUS__", "1.80"),
    ("__DELTA_CURRENT__", "1.76"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

wrapper_old_target = "security_public_safety_2_priority_25510row_incremental_evidence_expansion_20260730"
wrapper_new_target = "security_public_safety_2_priority_25510row_incremental_evidence_expansion_20260731"
if wrapper_old_target not in text:
    raise SystemExit(f"ORCHESTRATOR_WRAPPER_TARGET_DATE_FRAGMENT_MISSING: {wrapper_old_target}")
text = text.replace(wrapper_old_target, wrapper_new_target)

inner_marker = "\nrequired = ["
inner_injection = '''
old_target_task = "security_public_safety_2_priority_25510row_incremental_evidence_expansion_20260730"
new_target_task = "security_public_safety_2_priority_25510row_incremental_evidence_expansion_20260731"
if old_target_task in text:
    text = text.replace(old_target_task, new_target_task)
elif new_target_task not in text:
    raise SystemExit(f"ORCHESTRATOR_TARGET_DATE_FRAGMENT_MISSING: {old_target_task}")
text = text.replace("priority_25510row_browser_acceptance_wave103_receipt_20260730", "priority_25510row_browser_acceptance_wave103_receipt_20260731")
text = text.replace("priority_25510row_targeted_retry_wave103_diagnostic_20260730", "priority_25510row_targeted_retry_wave103_diagnostic_20260731")
previous_generator_old = "security_public_safety_2_priority_25060row_incremental_evidence_expansion_20260730.py"
previous_generator_new = "security_public_safety_2_priority_25060row_incremental_evidence_expansion_20260731.py"
if previous_generator_old in text:
    text = text.replace(previous_generator_old, previous_generator_new)
elif previous_generator_new not in text:
    raise SystemExit(f"PREVIOUS_GENERATOR_DATE_FRAGMENT_MISSING: {previous_generator_old}")

acceptance_marker = '        acc = acc.replace(old, new)' + chr(10) + '    for fragment in ('
acceptance_patch = chr(10).join([
    '        acc = acc.replace(old, new)',
    '    old_acceptance_task = "security_public_safety_2_priority_25510row_incremental_evidence_expansion_20260730"',
    '    new_acceptance_task = "security_public_safety_2_priority_25510row_incremental_evidence_expansion_20260731"',
    '    if old_acceptance_task in acc:',
    '        acc = acc.replace(old_acceptance_task, new_acceptance_task)',
    '    elif new_acceptance_task not in acc:',
    '        raise SystemExit(f"ACCEPTANCE_TARGET_DATE_FRAGMENT_MISSING:{old_acceptance_task}")',
    '    acc = acc.replace("priority_25510row_browser_acceptance_wave103_receipt_20260730", "priority_25510row_browser_acceptance_wave103_receipt_20260731")',
    '    acc = acc.replace("priority_25510row_targeted_retry_wave103_diagnostic_20260730", "priority_25510row_targeted_retry_wave103_diagnostic_20260731")',
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
    'SOURCE_HEAD = "902e11dbc64023c52b6a48fcaf936e3efbc72654"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_25060_TO_25510_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "bbf5266a5005f0dd7b09e450bf9f96af840df7acf2a123d2e42652451f619568"',
    'TASK_ID = "security_public_safety_2_priority_25510row_incremental_evidence_expansion_20260731"',
    'OWNER = "github-actions-security-public-safety-2-wave103"',
    '0078_security_public_safety_2_priority_25510row_incremental_evidence_expansion_20260731.v3.task.json',
    'priority_450row_wave103_latest.json',
    'priority_25510row_evidence_expansion_latest.json',
    '"accepted_base_rows": 25060',
    '"merged_candidate_rows": 25510',
    '"minimum_merged_police_hash_rows": 24235',
    '"incremental_parcel_start": 55822',
    '"incremental_parcel_end": 56271',
    '"expanded_scope_progress_percent": 98.24',
    '"expanded_scope_delta_percentage_points": 1.76',
    'len(rows) != 25510',
    '"parcel_56271"',
    'WAVE103_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})

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
    (r'''('\"schema_version\": 69', '\"schema_version\": 70'),''', r'''('\"schema_version\": 71', '\"schema_version\": 72'),'''),
    ('"schema_version": 115,', '"schema_version": 117,'),
    ('"schema_version": 119,', '"schema_version": 121,'),
    ('"schema_version": 114,', '"schema_version": 116,'),
    ('or 141) + 1', 'or 143) + 1'),
    ('"priority": -168,', '"priority": -170,'),
    ('97.81', '97.90'),
    ('WAVE92', 'WAVE94'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__SOURCE_HEAD__", "6ee96ccbbcaeae980013e8104d7c082ba21c1479"),
    ("__PREVIOUS_CONTINUATION__", "aedff5e02bd2ea03fde7b7a30bdca3f447d5f087f7c9ef726de4a6b11ca9a136"),
    ("__CURRENT_CONTINUATION__", "09d58c6ca20d0d23243de6995f6f210244bc792c2351da58e465f45c69939ef7"),
    ("__PREVIOUS_WAVE__", "wave93"),
    ("__CURRENT_WAVE__", "wave94"),
    ("__PREVIOUS_QUEUE__", "0068_"),
    ("__CURRENT_QUEUE__", "0069_"),
    ("__ROWS_OLD_PREVIOUS__", "20560"),
    ("__ROWS_BASE__", "21010"),
    ("__ROWS_TARGET__", "21460"),
    ("__MIN_OLD_PREVIOUS__", "19960"),
    ("__MIN_CURRENT__", "20387"),
    ("__ACCURACY_BASE__", "20749"),
    ("__PARCEL_OLD_START__", "51322"),
    ("__PARCEL_START__", "51772"),
    ("__PARCEL_END_PLUS_ONE__", "52222"),
    ("__PARCEL_OLD_END__", "51771"),
    ("__PARCEL_END__", "52221"),
    ("__DELTA_PREVIOUS__", "2.14"),
    ("__DELTA_CURRENT__", "2.10"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

wrapper_old_target = "security_public_safety_2_priority_21460row_incremental_evidence_expansion_20260730"
wrapper_new_target = "security_public_safety_2_priority_21460row_incremental_evidence_expansion_20260731"
if wrapper_old_target not in text:
    raise SystemExit(f"ORCHESTRATOR_WRAPPER_TARGET_DATE_FRAGMENT_MISSING: {wrapper_old_target}")
text = text.replace(wrapper_old_target, wrapper_new_target)

inner_marker = "\nrequired = ["
inner_injection = '''
old_target_task = "security_public_safety_2_priority_21460row_incremental_evidence_expansion_20260730"
new_target_task = "security_public_safety_2_priority_21460row_incremental_evidence_expansion_20260731"
if old_target_task not in text:
    raise SystemExit(f"ORCHESTRATOR_TARGET_DATE_FRAGMENT_MISSING: {old_target_task}")
text = text.replace(old_target_task, new_target_task)
text = text.replace("priority_21460row_browser_acceptance_wave94_receipt_20260730", "priority_21460row_browser_acceptance_wave94_receipt_20260731")
text = text.replace("priority_21460row_targeted_retry_wave94_diagnostic_20260730", "priority_21460row_targeted_retry_wave94_diagnostic_20260731")

acceptance_marker = '        acc = acc.replace(old, new)' + chr(10) + '    for fragment in ('
acceptance_patch = chr(10).join([
    '        acc = acc.replace(old, new)',
    '    old_acceptance_task = "security_public_safety_2_priority_21460row_incremental_evidence_expansion_20260730"',
    '    new_acceptance_task = "security_public_safety_2_priority_21460row_incremental_evidence_expansion_20260731"',
    '    if old_acceptance_task not in acc:',
    '        raise SystemExit(f"ACCEPTANCE_TARGET_DATE_FRAGMENT_MISSING:{old_acceptance_task}")',
    '    acc = acc.replace(old_acceptance_task, new_acceptance_task)',
    '    acc = acc.replace("priority_21460row_browser_acceptance_wave94_receipt_20260730", "priority_21460row_browser_acceptance_wave94_receipt_20260731")',
    '    acc = acc.replace("priority_21460row_targeted_retry_wave94_diagnostic_20260730", "priority_21460row_targeted_retry_wave94_diagnostic_20260731")',
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
    'SOURCE_HEAD = "6ee96ccbbcaeae980013e8104d7c082ba21c1479"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_21010_TO_21460_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "09d58c6ca20d0d23243de6995f6f210244bc792c2351da58e465f45c69939ef7"',
    'TASK_ID = "security_public_safety_2_priority_21460row_incremental_evidence_expansion_20260731"',
    'OWNER = "github-actions-security-public-safety-2-wave94"',
    '0069_security_public_safety_2_priority_21460row_incremental_evidence_expansion_20260731.v3.task.json',
    'priority_450row_wave94_latest.json',
    'priority_21460row_evidence_expansion_latest.json',
    '"accepted_base_rows": 21010',
    '"merged_candidate_rows": 21460',
    '"minimum_merged_police_hash_rows": 20387',
    '"incremental_parcel_start": 51772',
    '"incremental_parcel_end": 52221',
    '"expanded_scope_progress_percent": 97.90',
    '"expanded_scope_delta_percentage_points": 2.10',
    'len(rows) != 21460',
    '"parcel_52221"',
    'WAVE94_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})

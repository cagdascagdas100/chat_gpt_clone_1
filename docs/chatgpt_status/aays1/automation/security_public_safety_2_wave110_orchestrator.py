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
    (r'''('\"schema_version\": 69', '\"schema_version\": 70'),''', r'''('\"schema_version\": 87', '\"schema_version\": 88'),'''),
    ('"schema_version": 115,', '"schema_version": 133,'),
    ('"schema_version": 119,', '"schema_version": 137,'),
    ('"schema_version": 114,', '"schema_version": 132,'),
    ('or 141) + 1', 'or 159) + 1'),
    ('"priority": -168,', '"priority": -186,'),
    ('97.81', '98.43'),
    ('WAVE92', 'WAVE110'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__SOURCE_HEAD__", "a89261e8c611712568945bf44ab9a008e99a4782"),
    ("__PREVIOUS_CONTINUATION__", "00640c873f67283da0bcaa6f31141f332247d7197d86bf8d48f7650f49290319"),
    ("__CURRENT_CONTINUATION__", "758e067a1160863ad6abd679e9870f108f7ebbbdedd011858c7064963f22910d"),
    ("__PREVIOUS_WAVE__", "wave109"),
    ("__CURRENT_WAVE__", "wave110"),
    ("__PREVIOUS_QUEUE__", "0084_"),
    ("__CURRENT_QUEUE__", "0085_"),
    ("__ROWS_OLD_PREVIOUS__", "27760"),
    ("__ROWS_BASE__", "28210"),
    ("__ROWS_TARGET__", "28660"),
    ("__MIN_OLD_PREVIOUS__", "26800"),
    ("__MIN_CURRENT__", "27227"),
    ("__ACCURACY_BASE__", "27858"),
    ("__PARCEL_OLD_START__", "58522"),
    ("__PARCEL_START__", "58972"),
    ("__PARCEL_END_PLUS_ONE__", "59422"),
    ("__PARCEL_OLD_END__", "58971"),
    ("__PARCEL_END__", "59421"),
    ("__DELTA_PREVIOUS__", "1.60"),
    ("__DELTA_CURRENT__", "1.57"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

wrapper_old_target = "security_public_safety_2_priority_28660row_incremental_evidence_expansion_20260730"
wrapper_new_target = "security_public_safety_2_priority_28660row_incremental_evidence_expansion_20260731"
if wrapper_old_target not in text:
    raise SystemExit(f"ORCHESTRATOR_WRAPPER_TARGET_DATE_FRAGMENT_MISSING: {wrapper_old_target}")
text = text.replace(wrapper_old_target, wrapper_new_target)

inner_marker = "\nrequired = ["
inner_injection = '''
old_target_task = "security_public_safety_2_priority_28660row_incremental_evidence_expansion_20260730"
new_target_task = "security_public_safety_2_priority_28660row_incremental_evidence_expansion_20260731"
if old_target_task in text:
    text = text.replace(old_target_task, new_target_task)
elif new_target_task not in text:
    raise SystemExit(f"ORCHESTRATOR_TARGET_DATE_FRAGMENT_MISSING: {old_target_task}")
text = text.replace("priority_28660row_browser_acceptance_wave110_receipt_20260730", "priority_28660row_browser_acceptance_wave110_receipt_20260731")
text = text.replace("priority_28660row_targeted_retry_wave110_diagnostic_20260730", "priority_28660row_targeted_retry_wave110_diagnostic_20260731")
previous_generator_old = "security_public_safety_2_priority_28210row_incremental_evidence_expansion_20260730.py"
previous_generator_new = "security_public_safety_2_priority_28210row_incremental_evidence_expansion_20260731.py"
if previous_generator_old in text:
    text = text.replace(previous_generator_old, previous_generator_new)
elif previous_generator_new not in text:
    raise SystemExit(f"PREVIOUS_GENERATOR_DATE_FRAGMENT_MISSING: {previous_generator_old}")

acceptance_marker = '        acc = acc.replace(old, new)' + chr(10) + '    for fragment in ('
acceptance_patch = chr(10).join([
    '        acc = acc.replace(old, new)',
    '    old_acceptance_task = "security_public_safety_2_priority_28660row_incremental_evidence_expansion_20260730"',
    '    new_acceptance_task = "security_public_safety_2_priority_28660row_incremental_evidence_expansion_20260731"',
    '    if old_acceptance_task in acc:',
    '        acc = acc.replace(old_acceptance_task, new_acceptance_task)',
    '    elif new_acceptance_task not in acc:',
    '        raise SystemExit(f"ACCEPTANCE_TARGET_DATE_FRAGMENT_MISSING:{old_acceptance_task}")',
    '    acc = acc.replace("priority_28660row_browser_acceptance_wave110_receipt_20260730", "priority_28660row_browser_acceptance_wave110_receipt_20260731")',
    '    acc = acc.replace("priority_28660row_targeted_retry_wave110_diagnostic_20260730", "priority_28660row_targeted_retry_wave110_diagnostic_20260731")',
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
    'SOURCE_HEAD = "a89261e8c611712568945bf44ab9a008e99a4782"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_28210_TO_28660_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "758e067a1160863ad6abd679e9870f108f7ebbbdedd011858c7064963f22910d"',
    'TASK_ID = "security_public_safety_2_priority_28660row_incremental_evidence_expansion_20260731"',
    'OWNER = "github-actions-security-public-safety-2-wave110"',
    '0085_security_public_safety_2_priority_28660row_incremental_evidence_expansion_20260731.v3.task.json',
    'priority_450row_wave110_latest.json',
    'priority_28660row_evidence_expansion_latest.json',
    '"accepted_base_rows": 28210',
    '"merged_candidate_rows": 28660',
    '"minimum_merged_police_hash_rows": 27227',
    '"incremental_parcel_start": 58972',
    '"incremental_parcel_end": 59421',
    '"expanded_scope_progress_percent": 98.43',
    '"expanded_scope_delta_percentage_points": 1.57',
    'len(rows) != 28660',
    '"parcel_59421"',
    'WAVE110_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})

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
    (r'''('\"schema_version\": 69', '\"schema_version\": 70'),''', r'''('\"schema_version\": 70', '\"schema_version\": 71'),'''),
    ('"schema_version": 115,', '"schema_version": 116,'),
    ('"schema_version": 119,', '"schema_version": 120,'),
    ('"schema_version": 114,', '"schema_version": 115,'),
    ('or 141) + 1', 'or 142) + 1'),
    ('"priority": -168,', '"priority": -169,'),
    ('97.81', '97.86'),
    ('WAVE92', 'WAVE93'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__SOURCE_HEAD__", "c47ab2816e8f5cc174785864d27914d1328679da"),
    ("__PREVIOUS_CONTINUATION__", "bf2a19bc6e2fb5f8bf351bea31c340b142ca6735cf144d2e326809b4ecae3f1b"),
    ("__CURRENT_CONTINUATION__", "aedff5e02bd2ea03fde7b7a30bdca3f447d5f087f7c9ef726de4a6b11ca9a136"),
    ("__PREVIOUS_WAVE__", "wave92"),
    ("__CURRENT_WAVE__", "wave93"),
    ("__PREVIOUS_QUEUE__", "0067_"),
    ("__CURRENT_QUEUE__", "0068_"),
    ("__ROWS_OLD_PREVIOUS__", "20110"),
    ("__ROWS_BASE__", "20560"),
    ("__ROWS_TARGET__", "21010"),
    ("__MIN_OLD_PREVIOUS__", "19532"),
    ("__MIN_CURRENT__", "19960"),
    ("__ACCURACY_BASE__", "20304"),
    ("__PARCEL_OLD_START__", "50872"),
    ("__PARCEL_START__", "51322"),
    ("__PARCEL_END_PLUS_ONE__", "51772"),
    ("__PARCEL_OLD_END__", "51321"),
    ("__PARCEL_END__", "51771"),
    ("__DELTA_PREVIOUS__", "2.19"),
    ("__DELTA_CURRENT__", "2.14"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "c47ab2816e8f5cc174785864d27914d1328679da"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_20560_TO_21010_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "aedff5e02bd2ea03fde7b7a30bdca3f447d5f087f7c9ef726de4a6b11ca9a136"',
    'TASK_ID = "security_public_safety_2_priority_21010row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave93"',
    '0068_security_public_safety_2_priority_21010row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave93_latest.json',
    'priority_21010row_evidence_expansion_latest.json',
    '"accepted_base_rows": 20560',
    '"merged_candidate_rows": 21010',
    '"minimum_merged_police_hash_rows": 19960',
    '"incremental_parcel_start": 51322',
    '"incremental_parcel_end": 51771',
    '"expanded_scope_progress_percent": 97.86',
    '"expanded_scope_delta_percentage_points": 2.14',
    'len(rows) != 21010',
    '"parcel_51771"',
    'WAVE93_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})

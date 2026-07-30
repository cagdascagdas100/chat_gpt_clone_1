from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave72_orchestrator.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_ORCHESTRATOR_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")

protected = [
    ("37bd2b96152653939629ac9da1daebc79fa1c68bf1127b97a6d9773e5410baf3", "__PREVIOUS_CONTINUATION__"),
    ("e80c765946c15e4233d5137b2c44bfde0c56ec923f52eb105038fb4d9369b2b5", "__CURRENT_CONTINUATION__"),
    ("wave71", "__PREVIOUS_WAVE__"),
    ("wave72", "__CURRENT_WAVE__"),
    ("0046_", "__PREVIOUS_QUEUE__"),
    ("0047_", "__CURRENT_QUEUE__"),
    ("10660", "__ROWS_OLD_PREVIOUS__"),
    ("11110", "__ROWS_BASE__"),
    ("11560", "__ROWS_TARGET__"),
    ("10555", "__MIN_OLD_PREVIOUS__"),
    ("10982", "__MIN_CURRENT__"),
    ("10964", "__ACCURACY_BASE__"),
    ("41422", "__PARCEL_OLD_START__"),
    ("41872", "__PARCEL_START__"),
    ("42322", "__PARCEL_END_PLUS_ONE__"),
    ("41871", "__PARCEL_OLD_END__"),
    ("42321", "__PARCEL_END__"),
    ("4.05", "__DELTA_PREVIOUS__"),
    ("3.89", "__DELTA_CURRENT__"),
]
for old, token in protected:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_TRANSFORM_FRAGMENT_MISSING: {old}")
    text = text.replace(old, token)

direct = [
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "5ff2e96dd28181341b05845a7056945a6005a74c"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 69', '\"schema_version\": 70'),"),
    ('"schema_version": 95,', '"schema_version": 115,'),
    ('"schema_version": 99,', '"schema_version": 119,'),
    ('"schema_version": 94,', '"schema_version": 114,'),
    ('or 121) + 1', 'or 141) + 1'),
    ('"priority": -148,', '"priority": -168,'),
    ('96.11', '97.81'),
    ('WAVE72', 'WAVE92'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "a3efcf9d82e085183979087a1bf0d2ea905fa427d3009fdccd73ac023f01ce92"),
    ("__CURRENT_CONTINUATION__", "bf2a19bc6e2fb5f8bf351bea31c340b142ca6735cf144d2e326809b4ecae3f1b"),
    ("__PREVIOUS_WAVE__", "wave91"),
    ("__CURRENT_WAVE__", "wave92"),
    ("__PREVIOUS_QUEUE__", "0066_"),
    ("__CURRENT_QUEUE__", "0067_"),
    ("__ROWS_OLD_PREVIOUS__", "19660"),
    ("__ROWS_BASE__", "20110"),
    ("__ROWS_TARGET__", "20560"),
    ("__MIN_OLD_PREVIOUS__", "19105"),
    ("__MIN_CURRENT__", "19532"),
    ("__ACCURACY_BASE__", "19855"),
    ("__PARCEL_OLD_START__", "50422"),
    ("__PARCEL_START__", "50872"),
    ("__PARCEL_END_PLUS_ONE__", "51322"),
    ("__PARCEL_OLD_END__", "50871"),
    ("__PARCEL_END__", "51321"),
    ("__DELTA_PREVIOUS__", "2.24"),
    ("__DELTA_CURRENT__", "2.19"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "5ff2e96dd28181341b05845a7056945a6005a74c"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_20110_TO_20560_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "bf2a19bc6e2fb5f8bf351bea31c340b142ca6735cf144d2e326809b4ecae3f1b"',
    'TASK_ID = "security_public_safety_2_priority_20560row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave92"',
    '0067_security_public_safety_2_priority_20560row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave92_latest.json',
    'priority_20560row_evidence_expansion_latest.json',
    '"accepted_base_rows": 20110',
    '"merged_candidate_rows": 20560',
    '"minimum_merged_police_hash_rows": 19532',
    '"incremental_parcel_start": 50872',
    '"incremental_parcel_end": 51321',
    '"expanded_scope_progress_percent": 97.81',
    '"expanded_scope_delta_percentage_points": 2.19',
    'len(rows) != 20560',
    '"parcel_51321"',
    'WAVE92_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

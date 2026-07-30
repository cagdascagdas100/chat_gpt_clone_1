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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "b74e5a77ef5f2f6ed9f8aa3564b4aa3f21621196"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 56', '\"schema_version\": 57'),"),
    ('"schema_version": 95,', '"schema_version": 102,'),
    ('"schema_version": 99,', '"schema_version": 106,'),
    ('"schema_version": 94,', '"schema_version": 101,'),
    ('or 121) + 1', 'or 128) + 1'),
    ('"priority": -148,', '"priority": -155,'),
    ('96.11', '96.94'),
    ('WAVE72', 'WAVE79'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "2cc8451e9fc6c56c340af6d0f8126f07fe327a0411de024472f8c3250a1f765d"),
    ("__CURRENT_CONTINUATION__", "38fc96b4516cf859c4b72a016e8c2b52f9cbb33d219c3fdadf8af1d011b4e484"),
    ("__PREVIOUS_WAVE__", "wave78"),
    ("__CURRENT_WAVE__", "wave79"),
    ("__PREVIOUS_QUEUE__", "0053_"),
    ("__CURRENT_QUEUE__", "0054_"),
    ("__ROWS_OLD_PREVIOUS__", "13810"),
    ("__ROWS_BASE__", "14260"),
    ("__ROWS_TARGET__", "14710"),
    ("__MIN_OLD_PREVIOUS__", "13547"),
    ("__MIN_CURRENT__", "13975"),
    ("__ACCURACY_BASE__", "14076"),
    ("__PARCEL_OLD_START__", "44572"),
    ("__PARCEL_START__", "45022"),
    ("__PARCEL_END_PLUS_ONE__", "45472"),
    ("__PARCEL_OLD_END__", "45021"),
    ("__PARCEL_END__", "45471"),
    ("__DELTA_PREVIOUS__", "3.16"),
    ("__DELTA_CURRENT__", "3.06"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "b74e5a77ef5f2f6ed9f8aa3564b4aa3f21621196"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_14260_TO_14710_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "38fc96b4516cf859c4b72a016e8c2b52f9cbb33d219c3fdadf8af1d011b4e484"',
    'TASK_ID = "security_public_safety_2_priority_14710row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave79"',
    '0054_security_public_safety_2_priority_14710row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave79_latest.json',
    'priority_14710row_evidence_expansion_latest.json',
    '"accepted_base_rows": 14260',
    '"merged_candidate_rows": 14710',
    '"minimum_merged_police_hash_rows": 13975',
    '"incremental_parcel_start": 45022',
    '"incremental_parcel_end": 45471',
    '"expanded_scope_progress_percent": 96.94',
    '"expanded_scope_delta_percentage_points": 3.06',
    'len(rows) != 14710',
    '"parcel_45471"',
    'WAVE79_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

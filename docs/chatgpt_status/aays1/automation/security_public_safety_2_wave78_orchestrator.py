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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "b08eaa35fd46dce195b934c4b4786c4ccbcc6d20"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 55', '\"schema_version\": 56'),"),
    ('"schema_version": 95,', '"schema_version": 101,'),
    ('"schema_version": 99,', '"schema_version": 105,'),
    ('"schema_version": 94,', '"schema_version": 100,'),
    ('or 121) + 1', 'or 127) + 1'),
    ('"priority": -148,', '"priority": -154,'),
    ('96.11', '96.84'),
    ('WAVE72', 'WAVE78'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "a005e9d21cc290b1e472eed6081436250a1cb344df18bc87aa7a25b2eb09db2d"),
    ("__CURRENT_CONTINUATION__", "2cc8451e9fc6c56c340af6d0f8126f07fe327a0411de024472f8c3250a1f765d"),
    ("__PREVIOUS_WAVE__", "wave77"),
    ("__CURRENT_WAVE__", "wave78"),
    ("__PREVIOUS_QUEUE__", "0052_"),
    ("__CURRENT_QUEUE__", "0053_"),
    ("__ROWS_OLD_PREVIOUS__", "13360"),
    ("__ROWS_BASE__", "13810"),
    ("__ROWS_TARGET__", "14260"),
    ("__MIN_OLD_PREVIOUS__", "13120"),
    ("__MIN_CURRENT__", "13547"),
    ("__ACCURACY_BASE__", "13631"),
    ("__PARCEL_OLD_START__", "44122"),
    ("__PARCEL_START__", "44572"),
    ("__PARCEL_END_PLUS_ONE__", "45022"),
    ("__PARCEL_OLD_END__", "44571"),
    ("__PARCEL_END__", "45021"),
    ("__DELTA_PREVIOUS__", "3.26"),
    ("__DELTA_CURRENT__", "3.16"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "b08eaa35fd46dce195b934c4b4786c4ccbcc6d20"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_13810_TO_14260_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "2cc8451e9fc6c56c340af6d0f8126f07fe327a0411de024472f8c3250a1f765d"',
    'TASK_ID = "security_public_safety_2_priority_14260row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave78"',
    '0053_security_public_safety_2_priority_14260row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave78_latest.json',
    'priority_14260row_evidence_expansion_latest.json',
    '"accepted_base_rows": 13810',
    '"merged_candidate_rows": 14260',
    '"minimum_merged_police_hash_rows": 13547',
    '"incremental_parcel_start": 44572',
    '"incremental_parcel_end": 45021',
    '"expanded_scope_progress_percent": 96.84',
    '"expanded_scope_delta_percentage_points": 3.16',
    'len(rows) != 14260',
    '"parcel_45021"',
    'WAVE78_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

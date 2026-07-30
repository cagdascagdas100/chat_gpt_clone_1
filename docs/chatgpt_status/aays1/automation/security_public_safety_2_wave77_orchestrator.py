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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "59f4a1cfba6b3fa739641a1f6531ea7c904e92c6"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 54', '\"schema_version\": 55'),"),
    ('"schema_version": 95,', '"schema_version": 100,'),
    ('"schema_version": 99,', '"schema_version": 104,'),
    ('"schema_version": 94,', '"schema_version": 99,'),
    ('or 121) + 1', 'or 126) + 1'),
    ('"priority": -148,', '"priority": -153,'),
    ('96.11', '96.74'),
    ('WAVE72', 'WAVE77'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "8ffc9b537d79f7ae2f8c1c60b6945e2b8cbe9d92cf531d3e5c5527d8f4b4960e"),
    ("__CURRENT_CONTINUATION__", "bab574342207c2f4e022ea24b4b3391753eb46eefdc125a0790e50eed5285b44"),
    ("__PREVIOUS_WAVE__", "wave76"),
    ("__CURRENT_WAVE__", "wave77"),
    ("__PREVIOUS_QUEUE__", "0051_"),
    ("__CURRENT_QUEUE__", "0052_"),
    ("__ROWS_OLD_PREVIOUS__", "12910"),
    ("__ROWS_BASE__", "13360"),
    ("__ROWS_TARGET__", "13810"),
    ("__MIN_OLD_PREVIOUS__", "12692"),
    ("__MIN_CURRENT__", "13120"),
    ("__ACCURACY_BASE__", "13187"),
    ("__PARCEL_OLD_START__", "43672"),
    ("__PARCEL_START__", "44122"),
    ("__PARCEL_END_PLUS_ONE__", "44572"),
    ("__PARCEL_OLD_END__", "44121"),
    ("__PARCEL_END__", "44571"),
    ("__DELTA_PREVIOUS__", "3.37"),
    ("__DELTA_CURRENT__", "3.26"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "59f4a1cfba6b3fa739641a1f6531ea7c904e92c6"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_13360_TO_13810_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "bab574342207c2f4e022ea24b4b3391753eb46eefdc125a0790e50eed5285b44"',
    'TASK_ID = "security_public_safety_2_priority_13810row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave77"',
    '0052_security_public_safety_2_priority_13810row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave77_latest.json',
    'priority_13810row_evidence_expansion_latest.json',
    '"accepted_base_rows": 13360',
    '"merged_candidate_rows": 13810',
    '"minimum_merged_police_hash_rows": 13120',
    '"incremental_parcel_start": 44122',
    '"incremental_parcel_end": 44571',
    '"expanded_scope_progress_percent": 96.74',
    '"expanded_scope_delta_percentage_points": 3.26',
    'len(rows) != 13810',
    '"parcel_44571"',
    'WAVE77_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

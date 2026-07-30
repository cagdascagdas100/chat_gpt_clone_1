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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "41a5ab16fb49eea0b18753b6e7778b31c2bfd974"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 66', '\"schema_version\": 67'),"),
    ('"schema_version": 95,', '"schema_version": 112,'),
    ('"schema_version": 99,', '"schema_version": 116,'),
    ('"schema_version": 94,', '"schema_version": 111,'),
    ('or 121) + 1', 'or 138) + 1'),
    ('"priority": -148,', '"priority": -165,'),
    ('96.11', '97.66'),
    ('WAVE72', 'WAVE89'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "cc4820ece5096f0f936f662886e0fb2ebf766fd5da822eab9b472eb111967a14"),
    ("__CURRENT_CONTINUATION__", "21fae46679279c6057c40339323cc9366d53ea78ea9367d64c8b748798a8ac2a"),
    ("__PREVIOUS_WAVE__", "wave88"),
    ("__CURRENT_WAVE__", "wave89"),
    ("__PREVIOUS_QUEUE__", "0063_"),
    ("__CURRENT_QUEUE__", "0064_"),
    ("__ROWS_OLD_PREVIOUS__", "18310"),
    ("__ROWS_BASE__", "18760"),
    ("__ROWS_TARGET__", "19210"),
    ("__MIN_OLD_PREVIOUS__", "17822"),
    ("__MIN_CURRENT__", "18250"),
    ("__ACCURACY_BASE__", "18518"),
    ("__PARCEL_OLD_START__", "49072"),
    ("__PARCEL_START__", "49522"),
    ("__PARCEL_END_PLUS_ONE__", "49972"),
    ("__PARCEL_OLD_END__", "49521"),
    ("__PARCEL_END__", "49971"),
    ("__DELTA_PREVIOUS__", "2.40"),
    ("__DELTA_CURRENT__", "2.34"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "41a5ab16fb49eea0b18753b6e7778b31c2bfd974"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_18760_TO_19210_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "21fae46679279c6057c40339323cc9366d53ea78ea9367d64c8b748798a8ac2a"',
    'TASK_ID = "security_public_safety_2_priority_19210row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave89"',
    '0064_security_public_safety_2_priority_19210row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave89_latest.json',
    'priority_19210row_evidence_expansion_latest.json',
    '"accepted_base_rows": 18760',
    '"merged_candidate_rows": 19210',
    '"minimum_merged_police_hash_rows": 18250',
    '"incremental_parcel_start": 49522',
    '"incremental_parcel_end": 49971',
    '"expanded_scope_progress_percent": 97.66',
    '"expanded_scope_delta_percentage_points": 2.34',
    'len(rows) != 19210',
    '"parcel_49971"',
    'WAVE89_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

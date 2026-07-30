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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "f496dfc3f7e143f0fdd9644608e75eb06f5d1624"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 65', '\"schema_version\": 66'),"),
    ('"schema_version": 95,', '"schema_version": 111,'),
    ('"schema_version": 99,', '"schema_version": 115,'),
    ('"schema_version": 94,', '"schema_version": 110,'),
    ('or 121) + 1', 'or 137) + 1'),
    ('"priority": -148,', '"priority": -164,'),
    ('96.11', '97.60'),
    ('WAVE72', 'WAVE88'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "aa12cea3d7564174185e8affd22340d50552b8abf49e22bf9608a55f8656bf11"),
    ("__CURRENT_CONTINUATION__", "cc4820ece5096f0f936f662886e0fb2ebf766fd5da822eab9b472eb111967a14"),
    ("__PREVIOUS_WAVE__", "wave87"),
    ("__CURRENT_WAVE__", "wave88"),
    ("__PREVIOUS_QUEUE__", "0062_"),
    ("__CURRENT_QUEUE__", "0063_"),
    ("__ROWS_OLD_PREVIOUS__", "17860"),
    ("__ROWS_BASE__", "18310"),
    ("__ROWS_TARGET__", "18760"),
    ("__MIN_OLD_PREVIOUS__", "17395"),
    ("__MIN_CURRENT__", "17822"),
    ("__ACCURACY_BASE__", "18079"),
    ("__PARCEL_OLD_START__", "48622"),
    ("__PARCEL_START__", "49072"),
    ("__PARCEL_END_PLUS_ONE__", "49522"),
    ("__PARCEL_OLD_END__", "49071"),
    ("__PARCEL_END__", "49521"),
    ("__DELTA_PREVIOUS__", "2.46"),
    ("__DELTA_CURRENT__", "2.40"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "f496dfc3f7e143f0fdd9644608e75eb06f5d1624"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_18310_TO_18760_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "cc4820ece5096f0f936f662886e0fb2ebf766fd5da822eab9b472eb111967a14"',
    'TASK_ID = "security_public_safety_2_priority_18760row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave88"',
    '0063_security_public_safety_2_priority_18760row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave88_latest.json',
    'priority_18760row_evidence_expansion_latest.json',
    '"accepted_base_rows": 18310',
    '"merged_candidate_rows": 18760',
    '"minimum_merged_police_hash_rows": 17822',
    '"incremental_parcel_start": 49072',
    '"incremental_parcel_end": 49521',
    '"expanded_scope_progress_percent": 97.60',
    '"expanded_scope_delta_percentage_points": 2.40',
    'len(rows) != 18760',
    '"parcel_49521"',
    'WAVE88_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

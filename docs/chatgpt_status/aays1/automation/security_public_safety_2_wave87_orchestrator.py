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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "d91d912077e741bed082ad4b583c3653eacd4fc8"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 64', '\"schema_version\": 65'),"),
    ('"schema_version": 95,', '"schema_version": 110,'),
    ('"schema_version": 99,', '"schema_version": 114,'),
    ('"schema_version": 94,', '"schema_version": 109,'),
    ('or 121) + 1', 'or 136) + 1'),
    ('"priority": -148,', '"priority": -163,'),
    ('96.11', '97.54'),
    ('WAVE72', 'WAVE87'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "8e1e55ab6a4812d1147e314a07cdf19277c46a84a4b553e205c79b50dade1da7"),
    ("__CURRENT_CONTINUATION__", "aa12cea3d7564174185e8affd22340d50552b8abf49e22bf9608a55f8656bf11"),
    ("__PREVIOUS_WAVE__", "wave86"),
    ("__CURRENT_WAVE__", "wave87"),
    ("__PREVIOUS_QUEUE__", "0061_"),
    ("__CURRENT_QUEUE__", "0062_"),
    ("__ROWS_OLD_PREVIOUS__", "17410"),
    ("__ROWS_BASE__", "17860"),
    ("__ROWS_TARGET__", "18310"),
    ("__MIN_OLD_PREVIOUS__", "16967"),
    ("__MIN_CURRENT__", "17395"),
    ("__ACCURACY_BASE__", "17639"),
    ("__PARCEL_OLD_START__", "48172"),
    ("__PARCEL_START__", "48622"),
    ("__PARCEL_END_PLUS_ONE__", "49072"),
    ("__PARCEL_OLD_END__", "48621"),
    ("__PARCEL_END__", "49071"),
    ("__DELTA_PREVIOUS__", "2.52"),
    ("__DELTA_CURRENT__", "2.46"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "d91d912077e741bed082ad4b583c3653eacd4fc8"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_17860_TO_18310_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "aa12cea3d7564174185e8affd22340d50552b8abf49e22bf9608a55f8656bf11"',
    'TASK_ID = "security_public_safety_2_priority_18310row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave87"',
    '0062_security_public_safety_2_priority_18310row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave87_latest.json',
    'priority_18310row_evidence_expansion_latest.json',
    '"accepted_base_rows": 17860',
    '"merged_candidate_rows": 18310',
    '"minimum_merged_police_hash_rows": 17395',
    '"incremental_parcel_start": 48622',
    '"incremental_parcel_end": 49071',
    '"expanded_scope_progress_percent": 97.54',
    '"expanded_scope_delta_percentage_points": 2.46',
    'len(rows) != 18310',
    '"parcel_49071"',
    'WAVE87_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

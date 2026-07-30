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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "26eb0698360d7d8c600a67a57b0f6775bcd0e8a1"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 60', '\"schema_version\": 61'),"),
    ('"schema_version": 95,', '"schema_version": 106,'),
    ('"schema_version": 99,', '"schema_version": 110,'),
    ('"schema_version": 94,', '"schema_version": 105,'),
    ('or 121) + 1', 'or 132) + 1'),
    ('"priority": -148,', '"priority": -159,'),
    ('96.11', '97.27'),
    ('WAVE72', 'WAVE83'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "d8a5ce52bb046348859f324e448bd9caefd43b5386dbb576bd8767c9305a0d0e"),
    ("__CURRENT_CONTINUATION__", "421da5bbd1900635468d505157e7d5d90dde2d4644915102b0db9b4898c5d1e6"),
    ("__PREVIOUS_WAVE__", "wave82"),
    ("__CURRENT_WAVE__", "wave83"),
    ("__PREVIOUS_QUEUE__", "0057_"),
    ("__CURRENT_QUEUE__", "0058_"),
    ("__ROWS_OLD_PREVIOUS__", "15610"),
    ("__ROWS_BASE__", "16060"),
    ("__ROWS_TARGET__", "16510"),
    ("__MIN_OLD_PREVIOUS__", "15257"),
    ("__MIN_CURRENT__", "15685"),
    ("__ACCURACY_BASE__", "15863"),
    ("__PARCEL_OLD_START__", "46372"),
    ("__PARCEL_START__", "46822"),
    ("__PARCEL_END_PLUS_ONE__", "47272"),
    ("__PARCEL_OLD_END__", "46821"),
    ("__PARCEL_END__", "47271"),
    ("__DELTA_PREVIOUS__", "2.80"),
    ("__DELTA_CURRENT__", "2.73"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "26eb0698360d7d8c600a67a57b0f6775bcd0e8a1"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_16060_TO_16510_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "421da5bbd1900635468d505157e7d5d90dde2d4644915102b0db9b4898c5d1e6"',
    'TASK_ID = "security_public_safety_2_priority_16510row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave83"',
    '0058_security_public_safety_2_priority_16510row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave83_latest.json',
    'priority_16510row_evidence_expansion_latest.json',
    '"accepted_base_rows": 16060',
    '"merged_candidate_rows": 16510',
    '"minimum_merged_police_hash_rows": 15685',
    '"incremental_parcel_start": 46822',
    '"incremental_parcel_end": 47271',
    '"expanded_scope_progress_percent": 97.27',
    '"expanded_scope_delta_percentage_points": 2.73',
    'len(rows) != 16510',
    '"parcel_47271"',
    'WAVE83_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

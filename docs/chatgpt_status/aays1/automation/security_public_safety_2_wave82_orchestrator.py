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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "06a42c30f2db74d13bde5b9437c03dfdbc68ba89"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 59', '\"schema_version\": 60'),"),
    ('"schema_version": 95,', '"schema_version": 105,'),
    ('"schema_version": 99,', '"schema_version": 109,'),
    ('"schema_version": 94,', '"schema_version": 104,'),
    ('or 121) + 1', 'or 131) + 1'),
    ('"priority": -148,', '"priority": -158,'),
    ('96.11', '97.20'),
    ('WAVE72', 'WAVE82'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "27ad2fbd199403398e4154a154394cd37034cbf17ce7f020c3b724c02b508616"),
    ("__CURRENT_CONTINUATION__", "d8a5ce52bb046348859f324e448bd9caefd43b5386dbb576bd8767c9305a0d0e"),
    ("__PREVIOUS_WAVE__", "wave81"),
    ("__CURRENT_WAVE__", "wave82"),
    ("__PREVIOUS_QUEUE__", "0056_"),
    ("__CURRENT_QUEUE__", "0057_"),
    ("__ROWS_OLD_PREVIOUS__", "15160"),
    ("__ROWS_BASE__", "15610"),
    ("__ROWS_TARGET__", "16060"),
    ("__MIN_OLD_PREVIOUS__", "14830"),
    ("__MIN_CURRENT__", "15257"),
    ("__ACCURACY_BASE__", "15415"),
    ("__PARCEL_OLD_START__", "45922"),
    ("__PARCEL_START__", "46372"),
    ("__PARCEL_END_PLUS_ONE__", "46822"),
    ("__PARCEL_OLD_END__", "46371"),
    ("__PARCEL_END__", "46821"),
    ("__DELTA_PREVIOUS__", "2.88"),
    ("__DELTA_CURRENT__", "2.80"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "06a42c30f2db74d13bde5b9437c03dfdbc68ba89"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_15610_TO_16060_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "d8a5ce52bb046348859f324e448bd9caefd43b5386dbb576bd8767c9305a0d0e"',
    'TASK_ID = "security_public_safety_2_priority_16060row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave82"',
    '0057_security_public_safety_2_priority_16060row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave82_latest.json',
    'priority_16060row_evidence_expansion_latest.json',
    '"accepted_base_rows": 15610',
    '"merged_candidate_rows": 16060',
    '"minimum_merged_police_hash_rows": 15257',
    '"incremental_parcel_start": 46372',
    '"incremental_parcel_end": 46821',
    '"expanded_scope_progress_percent": 97.20',
    '"expanded_scope_delta_percentage_points": 2.80',
    'len(rows) != 16060',
    '"parcel_46821"',
    'WAVE82_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

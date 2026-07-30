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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "398c9cb4cf159da5cba1ca7a46831a72d5f78f6e"'),
    (("'\"schema_version\": 49', '\"schema_version\": 50'"), ("'\"schema_version\": 58', '\"schema_version\": 59'")),
    ('"schema_version": 95,', '"schema_version": 104,'),
    ('"schema_version": 99,', '"schema_version": 108,'),
    ('"schema_version": 94,', '"schema_version": 103,'),
    ('or 121) + 1', 'or 130) + 1'),
    ('"priority": -148,', '"priority": -157,'),
    ('96.11', '97.12'),
    ('WAVE72', 'WAVE81'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "c2bff1ff33ef162e11fadf8e0e02284953f44d88feb0f6291018fcc9c966b50c"),
    ("__CURRENT_CONTINUATION__", "27ad2fbd199403398e4154a154394cd37034cbf17ce7f020c3b724c02b508616"),
    ("__PREVIOUS_WAVE__", "wave80"),
    ("__CURRENT_WAVE__", "wave81"),
    ("__PREVIOUS_QUEUE__", "0055_"),
    ("__CURRENT_QUEUE__", "0056_"),
    ("__ROWS_OLD_PREVIOUS__", "14710"),
    ("__ROWS_BASE__", "15160"),
    ("__ROWS_TARGET__", "15610"),
    ("__MIN_OLD_PREVIOUS__", "14402"),
    ("__MIN_CURRENT__", "14830"),
    ("__ACCURACY_BASE__", "14967"),
    ("__PARCEL_OLD_START__", "45472"),
    ("__PARCEL_START__", "45922"),
    ("__PARCEL_END_PLUS_ONE__", "46372"),
    ("__PARCEL_OLD_END__", "45921"),
    ("__PARCEL_END__", "46371"),
    ("__DELTA_PREVIOUS__", "2.97"),
    ("__DELTA_CURRENT__", "2.88"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "398c9cb4cf159da5cba1ca7a46831a72d5f78f6e"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_15160_TO_15610_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "27ad2fbd199403398e4154a154394cd37034cbf17ce7f020c3b724c02b508616"',
    'TASK_ID = "security_public_safety_2_priority_15610row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave81"',
    '0056_security_public_safety_2_priority_15610row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave81_latest.json',
    'priority_15610row_evidence_expansion_latest.json',
    '"accepted_base_rows": 15160',
    '"merged_candidate_rows": 15610',
    '"minimum_merged_police_hash_rows": 14830',
    '"incremental_parcel_start": 45922',
    '"incremental_parcel_end": 46371',
    '"expanded_scope_progress_percent": 97.12',
    '"expanded_scope_delta_percentage_points": 2.88',
    'len(rows) != 15610',
    '"parcel_46371"',
    'WAVE81_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

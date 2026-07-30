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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "f8327d06d4237a604d0ec312dd45dd68a90a7244"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 62', '\"schema_version\": 63'),"),
    ('"schema_version": 95,', '"schema_version": 108,'),
    ('"schema_version": 99,', '"schema_version": 112,'),
    ('"schema_version": 94,', '"schema_version": 107,'),
    ('or 121) + 1', 'or 134) + 1'),
    ('"priority": -148,', '"priority": -161,'),
    ('96.11', '97.42'),
    ('WAVE72', 'WAVE85'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "9a4b6de0bd303868ead980127702e351f234324d603f30023f216ec8a14bd1e0"),
    ("__CURRENT_CONTINUATION__", "199c2c4d0ca0b1d657eacd192d5d83bc5cca426c48adf2adddb7d6eff715de79"),
    ("__PREVIOUS_WAVE__", "wave84"),
    ("__CURRENT_WAVE__", "wave85"),
    ("__PREVIOUS_QUEUE__", "0059_"),
    ("__CURRENT_QUEUE__", "0060_"),
    ("__ROWS_OLD_PREVIOUS__", "16510"),
    ("__ROWS_BASE__", "16960"),
    ("__ROWS_TARGET__", "17410"),
    ("__MIN_OLD_PREVIOUS__", "16112"),
    ("__MIN_CURRENT__", "16540"),
    ("__ACCURACY_BASE__", "16756"),
    ("__PARCEL_OLD_START__", "47272"),
    ("__PARCEL_START__", "47722"),
    ("__PARCEL_END_PLUS_ONE__", "48172"),
    ("__PARCEL_OLD_END__", "47721"),
    ("__PARCEL_END__", "48171"),
    ("__DELTA_PREVIOUS__", "2.65"),
    ("__DELTA_CURRENT__", "2.58"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "f8327d06d4237a604d0ec312dd45dd68a90a7244"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_16960_TO_17410_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "199c2c4d0ca0b1d657eacd192d5d83bc5cca426c48adf2adddb7d6eff715de79"',
    'TASK_ID = "security_public_safety_2_priority_17410row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave85"',
    '0060_security_public_safety_2_priority_17410row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave85_latest.json',
    'priority_17410row_evidence_expansion_latest.json',
    '"accepted_base_rows": 16960',
    '"merged_candidate_rows": 17410',
    '"minimum_merged_police_hash_rows": 16540',
    '"incremental_parcel_start": 47722',
    '"incremental_parcel_end": 48171',
    '"expanded_scope_progress_percent": 97.42',
    '"expanded_scope_delta_percentage_points": 2.58',
    'len(rows) != 17410',
    '"parcel_48171"',
    'WAVE85_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

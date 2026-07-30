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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "07c0c6c84cdae13f3a99005cd3b885336f7f09e0"'),
    (("'\"schema_version\": 49', '\"schema_version\": 50'"), ("'\"schema_version\": 63', '\"schema_version\": 64'")),
    ('"schema_version": 95,', '"schema_version": 109,'),
    ('"schema_version": 99,', '"schema_version": 113,'),
    ('"schema_version": 94,', '"schema_version": 108,'),
    ('or 121) + 1', 'or 135) + 1'),
    ('"priority": -148,', '"priority": -162,'),
    ('96.11', '97.48'),
    ('WAVE72', 'WAVE86'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "199c2c4d0ca0b1d657eacd192d5d83bc5cca426c48adf2adddb7d6eff715de79"),
    ("__CURRENT_CONTINUATION__", "8e1e55ab6a4812d1147e314a07cdf19277c46a84a4b553e205c79b50dade1da7"),
    ("__PREVIOUS_WAVE__", "wave85"),
    ("__CURRENT_WAVE__", "wave86"),
    ("__PREVIOUS_QUEUE__", "0060_"),
    ("__CURRENT_QUEUE__", "0061_"),
    ("__ROWS_OLD_PREVIOUS__", "16960"),
    ("__ROWS_BASE__", "17410"),
    ("__ROWS_TARGET__", "17860"),
    ("__MIN_OLD_PREVIOUS__", "16540"),
    ("__MIN_CURRENT__", "16967"),
    ("__ACCURACY_BASE__", "17196"),
    ("__PARCEL_OLD_START__", "47722"),
    ("__PARCEL_START__", "48172"),
    ("__PARCEL_END_PLUS_ONE__", "48622"),
    ("__PARCEL_OLD_END__", "48171"),
    ("__PARCEL_END__", "48621"),
    ("__DELTA_PREVIOUS__", "2.58"),
    ("__DELTA_CURRENT__", "2.52"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "07c0c6c84cdae13f3a99005cd3b885336f7f09e0"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_17410_TO_17860_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "8e1e55ab6a4812d1147e314a07cdf19277c46a84a4b553e205c79b50dade1da7"',
    'TASK_ID = "security_public_safety_2_priority_17860row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave86"',
    '0061_security_public_safety_2_priority_17860row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave86_latest.json',
    'priority_17860row_evidence_expansion_latest.json',
    '"accepted_base_rows": 17410',
    '"merged_candidate_rows": 17860',
    '"minimum_merged_police_hash_rows": 16967',
    '"incremental_parcel_start": 48172',
    '"incremental_parcel_end": 48621',
    '"expanded_scope_progress_percent": 97.48',
    '"expanded_scope_delta_percentage_points": 2.52',
    'len(rows) != 17860',
    '"parcel_48621"',
    'WAVE86_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

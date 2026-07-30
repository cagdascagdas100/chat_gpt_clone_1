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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "a824569be9285b2be6dcf2a0a38d3b66ac15153e"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 51', '\"schema_version\": 52'),"),
    ('"schema_version": 95,', '"schema_version": 97,'),
    ('"schema_version": 99,', '"schema_version": 101,'),
    ('"schema_version": 94,', '"schema_version": 96,'),
    ('or 121) + 1', 'or 123) + 1'),
    ('"priority": -148,', '"priority": -150,'),
    ('96.11', '96.39'),
    ('WAVE72', 'WAVE74'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "8677308be6b7c286d15f61c097739a919387cc3219fba2649b2ffc250a319603"),
    ("__CURRENT_CONTINUATION__", "da250374a0da5cccb66c7753f87ba749f5e282ede5bb497ea9f4496d2081b460"),
    ("__PREVIOUS_WAVE__", "wave73"),
    ("__CURRENT_WAVE__", "wave74"),
    ("__PREVIOUS_QUEUE__", "0048_"),
    ("__CURRENT_QUEUE__", "0049_"),
    ("__ROWS_OLD_PREVIOUS__", "11560"),
    ("__ROWS_BASE__", "12010"),
    ("__ROWS_TARGET__", "12460"),
    ("__MIN_OLD_PREVIOUS__", "11410"),
    ("__MIN_CURRENT__", "11838"),
    ("__ACCURACY_BASE__", "11854"),
    ("__PARCEL_OLD_START__", "42322"),
    ("__PARCEL_START__", "42772"),
    ("__PARCEL_END_PLUS_ONE__", "43222"),
    ("__PARCEL_OLD_END__", "42771"),
    ("__PARCEL_END__", "43221"),
    ("__DELTA_PREVIOUS__", "3.75"),
    ("__DELTA_CURRENT__", "3.61"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "a824569be9285b2be6dcf2a0a38d3b66ac15153e"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_12010_TO_12460_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "da250374a0da5cccb66c7753f87ba749f5e282ede5bb497ea9f4496d2081b460"',
    'TASK_ID = "security_public_safety_2_priority_12460row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave74"',
    '0049_security_public_safety_2_priority_12460row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave74_latest.json',
    'priority_12460row_evidence_expansion_latest.json',
    '"accepted_base_rows": 12010',
    '"merged_candidate_rows": 12460',
    '"minimum_merged_police_hash_rows": 11838',
    '"incremental_parcel_start": 42772',
    '"incremental_parcel_end": 43221',
    '"expanded_scope_progress_percent": 96.39',
    '"expanded_scope_delta_percentage_points": 3.61',
    'len(rows) != 12460',
    '"parcel_43221"',
    'WAVE74_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

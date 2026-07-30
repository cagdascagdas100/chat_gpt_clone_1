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
    ('SOURCE_HEAD = "422bfc04d3ff4aef3d479444b186dbc353861b46"', 'SOURCE_HEAD = "31818490687aec773494242a46fffb2e4f8ed7dd"'),
    ("('\"schema_version\": 49', '\"schema_version\": 50'),", "('\"schema_version\": 68', '\"schema_version\": 69'),"),
    ('"schema_version": 95,', '"schema_version": 114,'),
    ('"schema_version": 99,', '"schema_version": 118,'),
    ('"schema_version": 94,', '"schema_version": 113,'),
    ('or 121) + 1', 'or 140) + 1'),
    ('"priority": -148,', '"priority": -167,'),
    ('96.11', '97.76'),
    ('WAVE72', 'WAVE91'),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__PREVIOUS_CONTINUATION__", "d6ea0dc34da35595b5b80548aeb7d242661d2a32b83609c4edc4c3f44b3cd1ed"),
    ("__CURRENT_CONTINUATION__", "a3efcf9d82e085183979087a1bf0d2ea905fa427d3009fdccd73ac023f01ce92"),
    ("__PREVIOUS_WAVE__", "wave90"),
    ("__CURRENT_WAVE__", "wave91"),
    ("__PREVIOUS_QUEUE__", "0065_"),
    ("__CURRENT_QUEUE__", "0066_"),
    ("__ROWS_OLD_PREVIOUS__", "19210"),
    ("__ROWS_BASE__", "19660"),
    ("__ROWS_TARGET__", "20110"),
    ("__MIN_OLD_PREVIOUS__", "18677"),
    ("__MIN_CURRENT__", "19105"),
    ("__ACCURACY_BASE__", "19409"),
    ("__PARCEL_OLD_START__", "49972"),
    ("__PARCEL_START__", "50422"),
    ("__PARCEL_END_PLUS_ONE__", "50872"),
    ("__PARCEL_OLD_END__", "50421"),
    ("__PARCEL_END__", "50871"),
    ("__DELTA_PREVIOUS__", "2.29"),
    ("__DELTA_CURRENT__", "2.24"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "31818490687aec773494242a46fffb2e4f8ed7dd"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_19660_TO_20110_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "a3efcf9d82e085183979087a1bf0d2ea905fa427d3009fdccd73ac023f01ce92"',
    'TASK_ID = "security_public_safety_2_priority_20110row_incremental_evidence_expansion_20260730"',
    'OWNER = "github-actions-security-public-safety-2-wave91"',
    '0066_security_public_safety_2_priority_20110row_incremental_evidence_expansion_20260730.v3.task.json',
    'priority_450row_wave91_latest.json',
    'priority_20110row_evidence_expansion_latest.json',
    '"accepted_base_rows": 19660',
    '"merged_candidate_rows": 20110',
    '"minimum_merged_police_hash_rows": 19105',
    '"incremental_parcel_start": 50422',
    '"incremental_parcel_end": 50871',
    '"expanded_scope_progress_percent": 97.76',
    '"expanded_scope_delta_percentage_points": 2.24',
    'len(rows) != 20110',
    '"parcel_50871"',
    'WAVE91_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

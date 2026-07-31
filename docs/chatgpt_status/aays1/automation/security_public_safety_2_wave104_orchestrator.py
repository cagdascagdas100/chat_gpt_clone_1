from __future__ import annotations

from pathlib import Path

source = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave103_orchestrator.py")
if not source.is_file():
    raise SystemExit(f"SOURCE_ORCHESTRATOR_MISSING: {source}")
text = source.read_text(encoding="utf-8")

protected = [
    ("902e11dbc64023c52b6a48fcaf936e3efbc72654", "__SOURCE_HEAD__"),
    ("1bbc08a1ccfecb4f9338a4731fac72af44effa38bb512ce9fe09108a3a228444", "__PREVIOUS_CONTINUATION__"),
    ("bbf5266a5005f0dd7b09e450bf9f96af840df7acf2a123d2e42652451f619568", "__CURRENT_CONTINUATION__"),
    ("wave102", "__PREVIOUS_WAVE__"),
    ("wave103", "__CURRENT_WAVE__"),
    ("WAVE103", "__CURRENT_WAVE_UPPER__"),
    ("0077_", "__PREVIOUS_QUEUE__"),
    ("0078_", "__CURRENT_QUEUE__"),
    ("24610", "__ROWS_OLD_PREVIOUS__"),
    ("25060", "__ROWS_BASE__"),
    ("25510", "__ROWS_TARGET__"),
    ("23807", "__MIN_OLD_PREVIOUS__"),
    ("24235", "__MIN_CURRENT__"),
    ("24742", "__ACCURACY_BASE__"),
    ("55372", "__PARCEL_OLD_START__"),
    ("55822", "__PARCEL_START__"),
    ("56272", "__PARCEL_END_PLUS_ONE__"),
    ("55821", "__PARCEL_OLD_END__"),
    ("56271", "__PARCEL_END__"),
    ("1.80", "__DELTA_PREVIOUS__"),
    ("1.76", "__DELTA_CURRENT__"),
    (r'''('\"schema_version\": 80', '\"schema_version\": 81'),''', "__EMBEDDED_SCHEMA_RULE__"),
    ('"schema_version": 126,', "__CURRENT_SCHEMA__"),
    ('"schema_version": 130,', "__OWNERSHIP_SCHEMA__"),
    ('"schema_version": 125,', "__HEARTBEAT_SCHEMA__"),
    ('or 152) + 1', "__LEASE_RULE__"),
    ('"priority": -179,', "__PRIORITY_RULE__"),
    ('98.24', "__PROGRESS_RULE__"),
]
for old, token in protected:
    if old not in text:
        raise SystemExit(f"WAVE104_TRANSFORM_FRAGMENT_MISSING: {old}")
    text = text.replace(old, token)

resolved = [
    ("__SOURCE_HEAD__", "932f0dec011c3cd3837da448ee86725150ea4fe3"),
    ("__PREVIOUS_CONTINUATION__", "bbf5266a5005f0dd7b09e450bf9f96af840df7acf2a123d2e42652451f619568"),
    ("__CURRENT_CONTINUATION__", "e744fbe6afb47dc3318636cbe2d4c07affe481c41149cf58f7cba680b5773b9a"),
    ("__PREVIOUS_WAVE__", "wave103"),
    ("__CURRENT_WAVE__", "wave104"),
    ("__CURRENT_WAVE_UPPER__", "WAVE104"),
    ("__PREVIOUS_QUEUE__", "0078_"),
    ("__CURRENT_QUEUE__", "0079_"),
    ("__ROWS_OLD_PREVIOUS__", "25060"),
    ("__ROWS_BASE__", "25510"),
    ("__ROWS_TARGET__", "25960"),
    ("__MIN_OLD_PREVIOUS__", "24235"),
    ("__MIN_CURRENT__", "24662"),
    ("__ACCURACY_BASE__", "25188"),
    ("__PARCEL_OLD_START__", "55822"),
    ("__PARCEL_START__", "56272"),
    ("__PARCEL_END_PLUS_ONE__", "56722"),
    ("__PARCEL_OLD_END__", "56271"),
    ("__PARCEL_END__", "56721"),
    ("__DELTA_PREVIOUS__", "1.76"),
    ("__DELTA_CURRENT__", "1.73"),
    ("__EMBEDDED_SCHEMA_RULE__", r'''('\"schema_version\": 81', '\"schema_version\": 82'),'''),
    ("__CURRENT_SCHEMA__", '"schema_version": 127,'),
    ("__OWNERSHIP_SCHEMA__", '"schema_version": 131,'),
    ("__HEARTBEAT_SCHEMA__", '"schema_version": 126,'),
    ("__LEASE_RULE__", 'or 153) + 1'),
    ("__PRIORITY_RULE__", '"priority": -180,'),
    ("__PROGRESS_RULE__", '98.27'),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"WAVE104_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    'SOURCE_HEAD = "932f0dec011c3cd3837da448ee86725150ea4fe3"',
    'FIRST_STEP = "EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_25510_TO_25960_ROWS_WITH_OFFICIAL_SOURCE_HASHES"',
    'CONTINUATION_KEY = "e744fbe6afb47dc3318636cbe2d4c07affe481c41149cf58f7cba680b5773b9a"',
    'TASK_ID = "security_public_safety_2_priority_25960row_incremental_evidence_expansion_20260731"',
    'OWNER = "github-actions-security-public-safety-2-wave104"',
    '0079_security_public_safety_2_priority_25960row_incremental_evidence_expansion_20260731.v3.task.json',
    'priority_450row_wave104_latest.json',
    'priority_25960row_evidence_expansion_latest.json',
    '"accepted_base_rows": 25510',
    '"merged_candidate_rows": 25960',
    '"minimum_merged_police_hash_rows": 24662',
    '"incremental_parcel_start": 56272',
    '"incremental_parcel_end": 56721',
    '"expanded_scope_progress_percent": 98.27',
    '"expanded_scope_delta_percentage_points": 1.73',
    'len(rows) != 25960',
    '"parcel_56721"',
    'WAVE104_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"WAVE104_FINAL_FRAGMENT_MISSING: {fragment}")

exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})

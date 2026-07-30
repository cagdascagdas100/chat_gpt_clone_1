from __future__ import annotations

from pathlib import Path

source = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave97_orchestrator.py")
if not source.is_file():
    raise SystemExit(f"SOURCE_ORCHESTRATOR_MISSING: {source}")
text = source.read_text(encoding="utf-8")

protected = [
    ("46d33e257cb7d824d5a677d8f762e5afa956111e", "__SOURCE_HEAD__"),
    ("1486d431576a8dcdd404cf0e8630338af66e73694ce8f9be71a6936afa272732", "__PREVIOUS_CONTINUATION__"),
    ("8c0d233f0b4e80b52f2d50fcfc8c2febd9686377a12aa148dc70960267080c8b", "__CURRENT_CONTINUATION__"),
    ("wave96", "__PREVIOUS_WAVE__"),
    ("wave97", "__CURRENT_WAVE__"),
    ("0071_", "__PREVIOUS_QUEUE__"),
    ("0072_", "__CURRENT_QUEUE__"),
    ("21910", "__ROWS_OLD_PREVIOUS__"),
    ("22360", "__ROWS_BASE__"),
    ("22810", "__ROWS_TARGET__"),
    ("21242", "__MIN_OLD_PREVIOUS__"),
    ("21670", "__MIN_CURRENT__"),
    ("22081", "__ACCURACY_BASE__"),
    ("52672", "__PARCEL_OLD_START__"),
    ("53122", "__PARCEL_START__"),
    ("53572", "__PARCEL_END_PLUS_ONE__"),
    ("53121", "__PARCEL_OLD_END__"),
    ("53571", "__PARCEL_END__"),
    ("2.01", "__DELTA_PREVIOUS__"),
    ("1.97", "__DELTA_CURRENT__"),
]
for old, token in protected:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_TRANSFORM_FRAGMENT_MISSING: {old}")
    text = text.replace(old, token)

direct = [
    ("    (r'''('\\\"schema_version\\\": 69', '\\\"schema_version\\\": 70'),''', r'''('\\\"schema_version\\\": 74', '\\\"schema_version\\\": 75'),'''),",
     "    (r'''('\\\"schema_version\\\": 69', '\\\"schema_version\\\": 70'),''', r'''('\\\"schema_version\\\": 75', '\\\"schema_version\\\": 76'),'''),"),
    ("    ('\"schema_version\": 115,', '\"schema_version\": 120,'),",
     "    ('\"schema_version\": 115,', '\"schema_version\": 121,'),"),
    ("    ('\"schema_version\": 119,', '\"schema_version\": 124,'),",
     "    ('\"schema_version\": 119,', '\"schema_version\": 125,'),"),
    ("    ('\"schema_version\": 114,', '\"schema_version\": 119,'),",
     "    ('\"schema_version\": 114,', '\"schema_version\": 120,'),"),
    ("    ('or 141) + 1', 'or 146) + 1'),", "    ('or 141) + 1', 'or 147) + 1'),"),
    ("    ('\"priority\": -168,', '\"priority\": -173,'),",
     "    ('\"priority\": -168,', '\"priority\": -174,'),"),
    ("    ('97.81', '98.03'),", "    ('97.81', '98.07'),"),
    ("    '\"expanded_scope_progress_percent\": 98.03',", "    '\"expanded_scope_progress_percent\": 98.07',"),
    ("    ('WAVE92', 'WAVE97'),", "    ('WAVE92', 'WAVE98'),"),
    ("    'WAVE97_REMOTE_TERMINAL_READBACK_FAILED',", "    'WAVE98_REMOTE_TERMINAL_READBACK_FAILED',"),
]
for old, new in direct:
    if old not in text:
        raise SystemExit(f"ORCHESTRATOR_DIRECT_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

resolved = [
    ("__SOURCE_HEAD__", "3976839fb696d3dfd0eedfd59c87f7bfdeb8a230"),
    ("__PREVIOUS_CONTINUATION__", "8c0d233f0b4e80b52f2d50fcfc8c2febd9686377a12aa148dc70960267080c8b"),
    ("__CURRENT_CONTINUATION__", "36f1b43ca5fd4ff3e2e79e5d3d960a8c479f5cbd20d4db374d9be4305030f1d3"),
    ("__PREVIOUS_WAVE__", "wave97"),
    ("__CURRENT_WAVE__", "wave98"),
    ("__PREVIOUS_QUEUE__", "0072_"),
    ("__CURRENT_QUEUE__", "0073_"),
    ("__ROWS_OLD_PREVIOUS__", "22360"),
    ("__ROWS_BASE__", "22810"),
    ("__ROWS_TARGET__", "23260"),
    ("__MIN_OLD_PREVIOUS__", "21670"),
    ("__MIN_CURRENT__", "22097"),
    ("__ACCURACY_BASE__", "22522"),
    ("__PARCEL_OLD_START__", "53122"),
    ("__PARCEL_START__", "53572"),
    ("__PARCEL_END_PLUS_ONE__", "54022"),
    ("__PARCEL_OLD_END__", "53571"),
    ("__PARCEL_END__", "54021"),
    ("__DELTA_PREVIOUS__", "1.97"),
    ("__DELTA_CURRENT__", "1.93"),
]
for token, value in resolved:
    if token not in text:
        raise SystemExit(f"ORCHESTRATOR_PLACEHOLDER_MISSING: {token}")
    text = text.replace(token, value)

required = [
    '3976839fb696d3dfd0eedfd59c87f7bfdeb8a230',
    'EXPAND_CANONICAL_BROWSER_VISIBLE_SAMPLE_FROM_22810_TO_23260_ROWS_WITH_OFFICIAL_SOURCE_HASHES',
    '36f1b43ca5fd4ff3e2e79e5d3d960a8c479f5cbd20d4db374d9be4305030f1d3',
    'security_public_safety_2_priority_23260row_incremental_evidence_expansion_20260731',
    'github-actions-security-public-safety-2-wave98',
    '0073_security_public_safety_2_priority_23260row_incremental_evidence_expansion_20260731.v3.task.json',
    'priority_450row_wave98_latest.json',
    'priority_23260row_evidence_expansion_latest.json',
    '\"accepted_base_rows\": 22810',
    '\"merged_candidate_rows\": 23260',
    '\"minimum_merged_police_hash_rows\": 22097',
    '\"incremental_parcel_start\": 53572',
    '\"incremental_parcel_end\": 54021',
    '\"expanded_scope_progress_percent\": 98.07',
    '\"expanded_scope_delta_percentage_points\": 1.93',
    'len(rows) != 23260',
    '\"parcel_54021\"',
    'WAVE98_REMOTE_TERMINAL_READBACK_FAILED',
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"ORCHESTRATOR_FINAL_FRAGMENT_MISSING: {fragment}")

exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source), "__package__": None})

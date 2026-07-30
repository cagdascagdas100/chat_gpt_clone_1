from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_5270row_incremental_evidence_expansion_20260730.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ('FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_5270row_evidence_expansion_latest.json"', 'FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_5590row_evidence_expansion_latest.json"'),
    ('WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_5270row_evidence_expansion_latest.json"', 'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_5590row_evidence_expansion_latest.json"'),
    ('INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_310row_wave56_latest.json"', 'INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_320row_wave57_latest.json"'),
    ('AAYS-TerraYield-security-public-safety-wave56-boundary-recovery/1.0', 'AAYS-TerraYield-security-public-safety-wave57-boundary-recovery/1.0'),
    ('priority_4960row_evidence_expansion_latest.json', 'priority_5270row_evidence_expansion_latest.json'),
    ('priority_310row_wave56_latest.json', 'priority_320row_wave57_latest.json'),
    ('priority_310row_wave56.html', 'priority_320row_wave57.html'),
    ('priority_5270row_evidence_expansion_latest.json', 'priority_5590row_evidence_expansion_latest.json'),
    ('priority_5270row_evidence_expansion.html', 'priority_5590row_evidence_expansion.html'),
    ('range(30762, 35722)', 'range(30762, 36032)'),
    ('range(35722, 36032)', 'range(36032, 36352)'),
    ('PREVIOUS_4960_SEQUENCE_MISMATCH', 'PREVIOUS_5270_SEQUENCE_MISMATCH'),
    ('wave56_incremental_target_310_ids_unique', 'wave57_incremental_target_320_ids_unique'),
    ('len(target_features) == 310', 'len(target_features) == 320'),
    ('wave56_incremental_valid_wgs84_points', 'wave57_incremental_valid_wgs84_points'),
    ('valid_points == 310', 'valid_points == 320'),
    ('wave56_incremental_single_ons_lsoa_matches', 'wave57_incremental_single_ons_lsoa_matches'),
    ('ons_rows == 310', 'ons_rows == 320'),
    ('wave56_incremental_police_response_hashes', 'wave57_incremental_police_response_hashes'),
    ('police_hash_rows >= 295', 'police_hash_rows >= 304'),
    ('wave56_incremental_candidate_310_rows_generated', 'wave57_incremental_candidate_320_rows_generated'),
    ('candidate_rows == 310', 'candidate_rows == 320'),
    ('IOD25_RELATIVE_SECURITY_INCREMENTAL_310_ROWS_PREPARED_NOT_PROMOTED', 'IOD25_RELATIVE_SECURITY_INCREMENTAL_320_ROWS_PREPARED_NOT_PROMOTED'),
    ('MERGE_WITH_ACCEPTED_4960_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE', 'MERGE_WITH_ACCEPTED_5270_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE'),
    ('accepted 4960-row wave', 'accepted 5270-row wave'),
    ('merge_with_accepted_4960_candidate_rows', 'merge_with_accepted_5270_candidate_rows'),
    ('Merge the 310 validated incremental rows with the accepted 4960-row artifact', 'Merge the 320 validated incremental rows with the accepted 5270-row artifact'),
    ('IoD25 310 satır artımlı kanıt dalgası', 'IoD25 320 satır artımlı kanıt dalgası'),
    ('Aday satır<br><b>{candidate_rows}/310</b>', 'Aday satır<br><b>{candidate_rows}/320</b>'),
    ('<h2>310 artımlı örnek satır</h2>', '<h2>320 artımlı örnek satır</h2>'),
    ('INCREMENTAL_310_SEQUENCE_MISMATCH', 'INCREMENTAL_320_SEQUENCE_MISMATCH'),
    ('len(set(row_ids)) != 5270', 'len(set(row_ids)) != 5590'),
    ('MERGED_5270_SEQUENCE_OR_UNIQUENESS_FAILED', 'MERGED_5590_SEQUENCE_OR_UNIQUENESS_FAILED'),
    ('accepted_4960row_base_present', 'accepted_5270row_base_present'),
    ('incremental_310_ids_unique', 'incremental_320_ids_unique'),
    ('merged_5270_ids_sequential_unique', 'merged_5590_ids_sequential_unique'),
    ('valid_wgs84_points_5270', 'valid_wgs84_points_5590'),
    ('valid_points == 5270', 'valid_points == 5590'),
    ('single_ons_lsoa_matches_5270', 'single_ons_lsoa_matches_5590'),
    ('ons_rows == 5270', 'ons_rows == 5590'),
    ('police_hash_rows >= 5007', 'police_hash_rows >= 5311'),
    ('iod25_exact_lsoa_joins_5270', 'iod25_exact_lsoa_joins_5590'),
    ('iod_join_rows == 5270', 'iod_join_rows == 5590'),
    ('candidate_rows_5270', 'candidate_rows_5590'),
    ('candidate_rows == 5270', 'candidate_rows == 5590'),
    ('candidate_accuracy_ge_95_rows_ge_5007', 'candidate_accuracy_ge_95_rows_ge_5311'),
    ('accuracy_ge_95_rows >= 5007', 'accuracy_ge_95_rows >= 5311'),
    ('"schema_version": 34', '"schema_version": 35'),
    ('IOD25_RELATIVE_SECURITY_PRIORITY_5270_ROWS_PREPARED_NOT_PROMOTED', 'IOD25_RELATIVE_SECURITY_PRIORITY_5590_ROWS_PREPARED_NOT_PROMOTED'),
    ('HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_5270_ROWS', 'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_5590_ROWS'),
    ('pending for the 5270-row artifact', 'pending for the 5590-row artifact'),
    ('on the 5270-row candidate artifact', 'on the 5590-row candidate artifact'),
    ('"base_rows": 4960', '"base_rows": 5270'),
    ('"added_rows": 310', '"added_rows": 320'),
    ('<title>security_public_safety_2 — 5270 satır</title>', '<title>security_public_safety_2 — 5590 satır</title>'),
    ('<h1>security_public_safety_2 — 5270 satır aday kanıtı</h1>', '<h1>security_public_safety_2 — 5590 satır aday kanıtı</h1>'),
    ('Aday satır<br><b>{candidate_rows}/5270</b>', 'Aday satır<br><b>{candidate_rows}/5590</b>'),
    ('<h2>5270 örnek satır</h2>', '<h2>5590 örnek satır</h2>'),
    ('aays_wave56_iod_', 'aays_wave57_iod_'),
    ('ons_rows == 5270', 'ons_rows == 5590'),
    ('iod_rows == 5270', 'iod_rows == 5590'),
    ('candidate_rows == 5270', 'candidate_rows == 5590'),
    ('accuracy_rows >= 5007', 'accuracy_rows >= 5311'),
    ('ons_rows != 5270 or iod_rows != 5270 or candidate_rows != 5270', 'ons_rows != 5590 or iod_rows != 5590 or candidate_rows != 5590'),
]

for old, new in replacements:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

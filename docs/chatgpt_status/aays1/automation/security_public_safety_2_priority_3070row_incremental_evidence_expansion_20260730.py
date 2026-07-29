from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_2840row_incremental_evidence_expansion_20260730.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ('priority_2840row_evidence_expansion_latest.json"', 'priority_3070row_evidence_expansion_latest.json"'),
    ('priority_2840row_evidence_expansion.html"', 'priority_3070row_evidence_expansion.html"'),
    ('priority_2620row_evidence_expansion_latest.json"', 'priority_2840row_evidence_expansion_latest.json"'),
    ('priority_220row_wave47_latest.json"', 'priority_230row_wave48_latest.json"'),
    ('priority_220row_wave47.html"', 'priority_230row_wave48.html"'),
    ('range(30762, 33382)', 'range(30762, 33602)'),
    ('range(33382, 33602)', 'range(33602, 33832)'),
    ('PREVIOUS_2620_SEQUENCE_MISMATCH', 'PREVIOUS_2840_SEQUENCE_MISMATCH'),
    ('wave47_incremental_target_220_ids_unique', 'wave48_incremental_target_230_ids_unique'),
    ('len(target_features) == 220', 'len(target_features) == 230'),
    ('wave47_incremental_valid_wgs84_points', 'wave48_incremental_valid_wgs84_points'),
    ('valid_points == 220', 'valid_points == 230'),
    ('wave47_incremental_single_ons_lsoa_matches', 'wave48_incremental_single_ons_lsoa_matches'),
    ('ons_rows == 220', 'ons_rows == 230'),
    ('wave47_incremental_police_response_hashes', 'wave48_incremental_police_response_hashes'),
    ('police_hash_rows >= 209', 'police_hash_rows >= 219'),
    ('wave47_incremental_candidate_220_rows_generated', 'wave48_incremental_candidate_230_rows_generated'),
    ('candidate_rows == 220', 'candidate_rows == 230'),
    ('IOD25_RELATIVE_SECURITY_INCREMENTAL_220_ROWS_PREPARED_NOT_PROMOTED', 'IOD25_RELATIVE_SECURITY_INCREMENTAL_230_ROWS_PREPARED_NOT_PROMOTED'),
    ('MERGE_WITH_ACCEPTED_2620_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE', 'MERGE_WITH_ACCEPTED_2840_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE'),
    ('accepted 2620-row wave', 'accepted 2840-row wave'),
    ('merge_with_accepted_2620_candidate_rows', 'merge_with_accepted_2840_candidate_rows'),
    ('Merge the 220 validated incremental rows with the accepted 2620-row artifact', 'Merge the 230 validated incremental rows with the accepted 2840-row artifact'),
    ('IoD25 220 satır artımlı kanıt dalgası', 'IoD25 230 satır artımlı kanıt dalgası'),
    ('Aday satır<br><b>{candidate_rows}/220</b>', 'Aday satır<br><b>{candidate_rows}/230</b>'),
    ('<h2>220 artımlı örnek satır</h2>', '<h2>230 artımlı örnek satır</h2>'),
    ('INCREMENTAL_220_SEQUENCE_MISMATCH', 'INCREMENTAL_230_SEQUENCE_MISMATCH'),
    ('len(set(row_ids)) != 2840', 'len(set(row_ids)) != 3070'),
    ('MERGED_2840_SEQUENCE_OR_UNIQUENESS_FAILED', 'MERGED_3070_SEQUENCE_OR_UNIQUENESS_FAILED'),
    ('accepted_2620row_base_present', 'accepted_2840row_base_present'),
    ('incremental_220_ids_unique', 'incremental_230_ids_unique'),
    ('merged_2840_ids_sequential_unique', 'merged_3070_ids_sequential_unique'),
    ('valid_wgs84_points_2840', 'valid_wgs84_points_3070'),
    ('valid_points == 2840', 'valid_points == 3070'),
    ('single_ons_lsoa_matches_2840', 'single_ons_lsoa_matches_3070'),
    ('ons_rows == 2840', 'ons_rows == 3070'),
    ('police_hash_rows >= 2698', 'police_hash_rows >= 2917'),
    ('iod25_exact_lsoa_joins_2840', 'iod25_exact_lsoa_joins_3070'),
    ('iod_join_rows == 2840', 'iod_join_rows == 3070'),
    ('candidate_rows_2840', 'candidate_rows_3070'),
    ('candidate_rows == 2840', 'candidate_rows == 3070'),
    ('candidate_accuracy_ge_95_rows_ge_2698', 'candidate_accuracy_ge_95_rows_ge_2917'),
    ('accuracy_ge_95_rows >= 2698', 'accuracy_ge_95_rows >= 2917'),
    ('"schema_version": 25', '"schema_version": 26'),
    ('IOD25_RELATIVE_SECURITY_PRIORITY_2840_ROWS_PREPARED_NOT_PROMOTED', 'IOD25_RELATIVE_SECURITY_PRIORITY_3070_ROWS_PREPARED_NOT_PROMOTED'),
    ('HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_2840_ROWS', 'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_3070_ROWS'),
    ('pending for the 2840-row artifact', 'pending for the 3070-row artifact'),
    ('on the 2840-row candidate artifact', 'on the 3070-row candidate artifact'),
    ('"base_rows": 2620', '"base_rows": 2840'),
    ('"added_rows": 220', '"added_rows": 230'),
    ('<title>security_public_safety_2 — 2840 satır</title>', '<title>security_public_safety_2 — 3070 satır</title>'),
    ('<h1>security_public_safety_2 — 2840 satır aday kanıtı</h1>', '<h1>security_public_safety_2 — 3070 satır aday kanıtı</h1>'),
    ('Aday satır<br><b>{candidate_rows}/2840</b>', 'Aday satır<br><b>{candidate_rows}/3070</b>'),
    ('<h2>2840 örnek satır</h2>', '<h2>3070 örnek satır</h2>'),
]

for old, new in replacements:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

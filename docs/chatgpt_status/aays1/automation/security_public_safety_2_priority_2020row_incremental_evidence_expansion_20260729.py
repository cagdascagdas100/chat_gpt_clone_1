from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_340row_incremental_evidence_expansion_20260729.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = {
    'PREVIOUS = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_320row_evidence_expansion_latest.json"':
        'PREVIOUS = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_1840row_evidence_expansion_latest.json"',
    'INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_20row_wave27_latest.json"':
        'INCREMENTAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_180row_wave43_latest.json"',
    'INCREMENTAL_WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_20row_wave27_latest.json"':
        'INCREMENTAL_WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_180row_wave43_latest.json"',
    'INCREMENTAL_WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_20row_wave27.html"':
        'INCREMENTAL_WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_180row_wave43.html"',
    'FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_340row_evidence_expansion_latest.json"':
        'FINAL_OUTPUT = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_2020row_evidence_expansion_latest.json"',
    'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_340row_evidence_expansion_latest.json"':
        'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_2020row_evidence_expansion_latest.json"',
    'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_340row_evidence_expansion.html"':
        'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_2020row_evidence_expansion.html"',
    'EXPECTED_PREVIOUS_IDS = [f"parcel_{value}" for value in range(30762, 31082)]':
        'EXPECTED_PREVIOUS_IDS = [f"parcel_{value}" for value in range(30762, 32602)]',
    'EXPECTED_INCREMENTAL_IDS = [f"parcel_{value}" for value in range(31082, 31102)]':
        'EXPECTED_INCREMENTAL_IDS = [f"parcel_{value}" for value in range(32602, 32782)]',
    'PREVIOUS_320_SEQUENCE_MISMATCH': 'PREVIOUS_1840_SEQUENCE_MISMATCH',
    'priority_320row_evidence_expansion_latest.json"': 'priority_1840row_evidence_expansion_latest.json"',
    'priority_20row_wave27_latest.json"': 'priority_180row_wave43_latest.json"',
    'priority_20row_wave27.html"': 'priority_180row_wave43.html"',
    'range(31082, 31102)': 'range(32602, 32782)',
    'ThreadPoolExecutor(max_workers=12, thread_name_prefix="security-row")':
        'ThreadPoolExecutor(max_workers=15, thread_name_prefix="security-row")',
    'wave27_incremental_target_20_ids_unique': 'wave43_incremental_target_180_ids_unique',
    'len(target_features) == 20': 'len(target_features) == 180',
    'wave27_incremental_valid_wgs84_points': 'wave43_incremental_valid_wgs84_points',
    'valid_points == 20': 'valid_points == 180',
    'wave27_incremental_single_ons_lsoa_matches': 'wave43_incremental_single_ons_lsoa_matches',
    'ons_rows == 20': 'ons_rows == 180',
    'wave27_incremental_police_response_hashes': 'wave43_incremental_police_response_hashes',
    'police_hash_rows >= 19': 'police_hash_rows >= 171',
    'wave27_incremental_candidate_20_rows_generated': 'wave43_incremental_candidate_180_rows_generated',
    'candidate_rows == 20': 'candidate_rows == 180',
    'IOD25_RELATIVE_SECURITY_INCREMENTAL_20_ROWS_PREPARED_NOT_PROMOTED':
        'IOD25_RELATIVE_SECURITY_INCREMENTAL_180_ROWS_PREPARED_NOT_PROMOTED',
    'MERGE_WITH_ACCEPTED_320_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE':
        'MERGE_WITH_ACCEPTED_1840_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE',
    'accepted 320-row wave': 'accepted 1840-row wave',
    'merge_with_accepted_320_candidate_rows': 'merge_with_accepted_1840_candidate_rows',
    'Merge the 20 validated incremental rows with the accepted 320-row artifact':
        'Merge the 180 validated incremental rows with the accepted 1840-row artifact',
    'IoD25 20 satır artımlı kanıt dalgası': 'IoD25 180 satır artımlı kanıt dalgası',
    'Aday satır<br><b>{candidate_rows}/20</b>': 'Aday satır<br><b>{candidate_rows}/180</b>',
    '<h2>20 artımlı örnek satır</h2>': '<h2>180 artımlı örnek satır</h2>',
    'INCREMENTAL_20_SEQUENCE_MISMATCH': 'INCREMENTAL_180_SEQUENCE_MISMATCH',
    'len(set(row_ids)) != 340': 'len(set(row_ids)) != 2020',
    'MERGED_340_SEQUENCE_OR_UNIQUENESS_FAILED': 'MERGED_2020_SEQUENCE_OR_UNIQUENESS_FAILED',
    'accepted_320row_base_present': 'accepted_1840row_base_present',
    'incremental_20_ids_unique': 'incremental_180_ids_unique',
    'merged_340_ids_sequential_unique': 'merged_2020_ids_sequential_unique',
    'valid_wgs84_points_340': 'valid_wgs84_points_2020',
    'valid_points == 340': 'valid_points == 2020',
    'single_ons_lsoa_matches_340': 'single_ons_lsoa_matches_2020',
    'ons_rows == 340': 'ons_rows == 2020',
    'police_hash_rows >= 323': 'police_hash_rows >= 1919',
    'iod25_exact_lsoa_joins_340': 'iod25_exact_lsoa_joins_2020',
    'iod_join_rows == 340': 'iod_join_rows == 2020',
    'candidate_rows_340': 'candidate_rows_2020',
    'candidate_rows == 340': 'candidate_rows == 2020',
    'candidate_accuracy_ge_95_rows_ge_323': 'candidate_accuracy_ge_95_rows_ge_1919',
    'accuracy_ge_95_rows >= 323': 'accuracy_ge_95_rows >= 1919',
    '"schema_version": 5': '"schema_version": 21',
    'IOD25_RELATIVE_SECURITY_PRIORITY_340_ROWS_PREPARED_NOT_PROMOTED':
        'IOD25_RELATIVE_SECURITY_PRIORITY_2020_ROWS_PREPARED_NOT_PROMOTED',
    'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_340_ROWS':
        'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_2020_ROWS',
    'pending for the 340-row artifact': 'pending for the 2020-row artifact',
    'on the 340-row candidate artifact': 'on the 2020-row candidate artifact',
    '"base_rows": 320': '"base_rows": 1840',
    '"added_rows": 20': '"added_rows": 180',
    '<title>security_public_safety_2 — 340 satır</title>':
        '<title>security_public_safety_2 — 2020 satır</title>',
    '<h1>security_public_safety_2 — 340 satır aday kanıtı</h1>':
        '<h1>security_public_safety_2 — 2020 satır aday kanıtı</h1>',
    'Aday satır<br><b>{candidate_rows}/340</b>': 'Aday satır<br><b>{candidate_rows}/2020</b>',
    '<h2>340 örnek satır</h2>': '<h2>2020 örnek satır</h2>',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

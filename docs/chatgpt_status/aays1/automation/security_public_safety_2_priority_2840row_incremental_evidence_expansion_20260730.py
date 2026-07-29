from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_2620row_incremental_evidence_expansion_20260730.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = {
    'priority_2410row_evidence_expansion_latest.json"': 'priority_2620row_evidence_expansion_latest.json"',
    'priority_210row_wave46_latest.json"': 'priority_220row_wave47_latest.json"',
    'priority_210row_wave46.html"': 'priority_220row_wave47.html"',
    'priority_2620row_evidence_expansion_latest.json"': 'priority_2840row_evidence_expansion_latest.json"',
    'priority_2620row_evidence_expansion.html"': 'priority_2840row_evidence_expansion.html"',
    'range(30762, 33172)': 'range(30762, 33382)',
    'range(33172, 33382)': 'range(33382, 33602)',
    'PREVIOUS_2410_SEQUENCE_MISMATCH': 'PREVIOUS_2620_SEQUENCE_MISMATCH',
    'wave46_incremental_target_210_ids_unique': 'wave47_incremental_target_220_ids_unique',
    'len(target_features) == 210': 'len(target_features) == 220',
    'wave46_incremental_valid_wgs84_points': 'wave47_incremental_valid_wgs84_points',
    'valid_points == 210': 'valid_points == 220',
    'wave46_incremental_single_ons_lsoa_matches': 'wave47_incremental_single_ons_lsoa_matches',
    'ons_rows == 210': 'ons_rows == 220',
    'wave46_incremental_police_response_hashes': 'wave47_incremental_police_response_hashes',
    'police_hash_rows >= 200': 'police_hash_rows >= 209',
    'wave46_incremental_candidate_210_rows_generated': 'wave47_incremental_candidate_220_rows_generated',
    'candidate_rows == 210': 'candidate_rows == 220',
    'IOD25_RELATIVE_SECURITY_INCREMENTAL_210_ROWS_PREPARED_NOT_PROMOTED': 'IOD25_RELATIVE_SECURITY_INCREMENTAL_220_ROWS_PREPARED_NOT_PROMOTED',
    'MERGE_WITH_ACCEPTED_2410_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE': 'MERGE_WITH_ACCEPTED_2620_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE',
    'accepted 2410-row wave': 'accepted 2620-row wave',
    'merge_with_accepted_2410_candidate_rows': 'merge_with_accepted_2620_candidate_rows',
    'Merge the 210 validated incremental rows with the accepted 2410-row artifact': 'Merge the 220 validated incremental rows with the accepted 2620-row artifact',
    'IoD25 210 satır artımlı kanıt dalgası': 'IoD25 220 satır artımlı kanıt dalgası',
    'Aday satır<br><b>{candidate_rows}/210</b>': 'Aday satır<br><b>{candidate_rows}/220</b>',
    '<h2>210 artımlı örnek satır</h2>': '<h2>220 artımlı örnek satır</h2>',
    'INCREMENTAL_210_SEQUENCE_MISMATCH': 'INCREMENTAL_220_SEQUENCE_MISMATCH',
    'len(set(row_ids)) != 2620': 'len(set(row_ids)) != 2840',
    'MERGED_2620_SEQUENCE_OR_UNIQUENESS_FAILED': 'MERGED_2840_SEQUENCE_OR_UNIQUENESS_FAILED',
    'accepted_2410row_base_present': 'accepted_2620row_base_present',
    'incremental_210_ids_unique': 'incremental_220_ids_unique',
    'merged_2620_ids_sequential_unique': 'merged_2840_ids_sequential_unique',
    'valid_wgs84_points_2620': 'valid_wgs84_points_2840',
    'valid_points == 2620': 'valid_points == 2840',
    'single_ons_lsoa_matches_2620': 'single_ons_lsoa_matches_2840',
    'ons_rows == 2620': 'ons_rows == 2840',
    'police_hash_rows >= 2489': 'police_hash_rows >= 2698',
    'iod25_exact_lsoa_joins_2620': 'iod25_exact_lsoa_joins_2840',
    'iod_join_rows == 2620': 'iod_join_rows == 2840',
    'candidate_rows_2620': 'candidate_rows_2840',
    'candidate_rows == 2620': 'candidate_rows == 2840',
    'candidate_accuracy_ge_95_rows_ge_2489': 'candidate_accuracy_ge_95_rows_ge_2698',
    'accuracy_ge_95_rows >= 2489': 'accuracy_ge_95_rows >= 2698',
    '"schema_version": 24': '"schema_version": 25',
    'IOD25_RELATIVE_SECURITY_PRIORITY_2620_ROWS_PREPARED_NOT_PROMOTED': 'IOD25_RELATIVE_SECURITY_PRIORITY_2840_ROWS_PREPARED_NOT_PROMOTED',
    'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_2620_ROWS': 'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_2840_ROWS',
    'pending for the 2620-row artifact': 'pending for the 2840-row artifact',
    'on the 2620-row candidate artifact': 'on the 2840-row candidate artifact',
    '"base_rows": 2410': '"base_rows": 2620',
    '"added_rows": 210': '"added_rows": 220',
    '<title>security_public_safety_2 — 2620 satır</title>': '<title>security_public_safety_2 — 2840 satır</title>',
    '<h1>security_public_safety_2 — 2620 satır aday kanıtı</h1>': '<h1>security_public_safety_2 — 2840 satır aday kanıtı</h1>',
    'Aday satır<br><b>{candidate_rows}/2620</b>': 'Aday satır<br><b>{candidate_rows}/2840</b>',
    '<h2>2620 örnek satır</h2>': '<h2>2840 örnek satır</h2>',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

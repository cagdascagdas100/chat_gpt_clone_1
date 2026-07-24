from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_iod25_relative_method_wave2_20260722.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = {
    'WAVE1_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json"':
        'WAVE1_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/source_and_sample_gate_latest.json"',
    'OUTPUT_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/iod25_relative_method_wave2_latest.json"':
        'OUTPUT_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_96row_consolidation_latest.json"',
    'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/progress_latest.json"':
        'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_96row_consolidation_latest.json"',
    'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/index.html"':
        'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_96row_consolidation.html"',
    'TARGET_IDS = [f"parcel_{value}" for value in range(30774, 30798)]':
        'TARGET_IDS = [f"parcel_{value}" for value in range(30762, 30858)]',
    'ThreadPoolExecutor(max_workers=6, thread_name_prefix="security-row")':
        'ThreadPoolExecutor(max_workers=10, thread_name_prefix="security-row")',
    'wave2_target_24_ids_unique': 'priority_target_96_ids_unique',
    'len(target_features) == 24': 'len(target_features) == 96',
    'wave2_valid_wgs84_points': 'priority_valid_wgs84_points',
    'valid_points == 24': 'valid_points == 96',
    'wave2_single_ons_lsoa_matches': 'priority_single_ons_lsoa_matches',
    'ons_rows == 24': 'ons_rows == 96',
    'wave2_police_response_hashes': 'priority_police_response_hashes',
    'police_hash_rows == 24': 'police_hash_rows == 96',
    'wave2_candidate_rows_generated': 'priority_candidate_rows_generated',
    'candidate_rows == 24': 'candidate_rows == 96',
    'IOD25_RELATIVE_SECURITY_METHOD_AND_24_ROW_WAVE2_PREPARED_NOT_PROMOTED':
        'IOD25_RELATIVE_SECURITY_PRIORITY_96_ROWS_PREPARED_NOT_PROMOTED',
    '24 örnek parsel': '96 örnek parsel',
    '24 parsel': '96 parsel',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {
    "__name__": "__main__",
    "__file__": str(SOURCE),
    "__package__": None,
}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

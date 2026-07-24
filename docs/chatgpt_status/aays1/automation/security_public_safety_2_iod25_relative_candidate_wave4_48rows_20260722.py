from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_iod25_relative_method_wave2_20260722.py"
if not SOURCE.is_file():
    raise SystemExit(f"BASE_WAVE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8-sig")
replacements = {
    'WAVE1_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json"': 'WAVE1_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/iod25_relative_method_wave2_latest.json"',
    'OUTPUT_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/iod25_relative_method_wave2_latest.json"': 'OUTPUT_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/iod25_relative_candidate_wave4_48rows_latest.json"',
    'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/progress_latest.json"': 'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/candidate_wave4_48rows_latest.json"',
    'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/index.html"': 'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/candidate_wave4_48rows.html"',
    'TARGET_IDS = [f"parcel_{value}" for value in range(30774, 30798)]': 'TARGET_IDS = [f"parcel_{value}" for value in range(30798, 30846)]',
    'USER_AGENT = "AAYS-TerraYield-security-public-safety-method-wave/3.0"': 'USER_AGENT = "AAYS-TerraYield-security-public-safety-candidate-wave/4.0"',
    'max_workers=6, thread_name_prefix="security-row"': 'max_workers=8, thread_name_prefix="security-row-wave4"',
    'len(target_features) == 24': 'len(target_features) == 48',
    'valid_points == 24': 'valid_points == 48',
    'ons_rows == 24': 'ons_rows == 48',
    'police_hash_rows == 24': 'police_hash_rows == 48',
    'candidate_rows == 24': 'candidate_rows == 48',
    '"wave2_target_24_ids_unique"': '"wave4_target_48_ids_unique"',
    '"wave2_valid_wgs84_points"': '"wave4_valid_wgs84_points"',
    '"wave2_single_ons_lsoa_matches"': '"wave4_single_ons_lsoa_matches"',
    '"wave2_police_response_hashes"': '"wave4_police_response_hashes"',
    '"wave2_candidate_rows_generated"': '"wave4_candidate_rows_generated"',
    '"IOD25_RELATIVE_SECURITY_METHOD_AND_24_ROW_WAVE2_PREPARED_NOT_PROMOTED"': '"IOD25_RELATIVE_SECURITY_48_ROW_WAVE4_PREPARED_NOT_PROMOTED"',
    '24 parsel': '48 parsel',
    '24 örnek': '48 örnek',
    '24-row': '48-row',
    '24 row': '48 row',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"BASE_WAVE_REPLACEMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {
    "__name__": "__main__",
    "__file__": str(SOURCE),
}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

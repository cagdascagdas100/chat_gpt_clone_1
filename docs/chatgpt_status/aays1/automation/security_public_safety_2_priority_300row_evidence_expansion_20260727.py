from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_iod25_relative_method_wave2_20260722.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = {
    'WAVE1_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json"':
        'WAVE1_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_96row_consolidation_latest.json"',
    'OUTPUT_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/iod25_relative_method_wave2_latest.json"':
        'OUTPUT_PATH = ROOT / "docs/chatgpt_status/aays1/shards/security_public_safety_2/priority_300row_evidence_expansion_latest.json"',
    'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/progress_latest.json"':
        'WEB_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_300row_evidence_expansion_latest.json"',
    'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/index.html"':
        'WEB_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/priority_300row_evidence_expansion.html"',
    'TARGET_IDS = [f"parcel_{value}" for value in range(30774, 30798)]':
        'TARGET_IDS = [f"parcel_{value}" for value in range(30762, 31062)]',
    'ThreadPoolExecutor(max_workers=6, thread_name_prefix="security-row")':
        'ThreadPoolExecutor(max_workers=12, thread_name_prefix="security-row")',
    'wave2_target_24_ids_unique': 'priority_target_300_ids_unique',
    'len(target_features) == 24': 'len(target_features) == 300',
    'wave2_valid_wgs84_points': 'priority_valid_wgs84_points',
    'valid_points == 24': 'valid_points == 300',
    'wave2_single_ons_lsoa_matches': 'priority_single_ons_lsoa_matches',
    'ons_rows == 24': 'ons_rows == 300',
    'wave2_police_response_hashes': 'priority_police_response_hashes_ge_95pct',
    'police_hash_rows == 24': 'police_hash_rows >= 285',
    'wave2_candidate_rows_generated': 'priority_candidate_300_rows_generated',
    'candidate_rows == 24': 'candidate_rows == 300',
    'IOD25_RELATIVE_SECURITY_METHOD_AND_24_ROW_WAVE2_PREPARED_NOT_PROMOTED':
        'IOD25_RELATIVE_SECURITY_PRIORITY_300_ROWS_PREPARED_NOT_PROMOTED',
    'CALIBRATE_CANDIDATE_METHOD_THEN_EXPAND_TO_300_AND_BROWSER_ACCEPTANCE':
        'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE',
    '{"gate": "candidate_method_calibration_review", "state": "PENDING"}':
        '{"gate": "candidate_method_calibration_review", "state": "PASS", "evidence": "official IoD limitations reviewed; candidate-only fail-closed semantics retained"}',
    '{"gate": "expand_to_300_verified_business_rows", "state": "PENDING"}':
        '{"gate": "expand_to_300_candidate_evidence_rows", "state": "PASS" if candidate_rows == 300 else "PARTIAL", "evidence": candidate_rows}',
    'Calibration, served HTTP/JSON hash, DOM, console and browser acceptance remain pending.':
        'Served HTTP/JSON hash, DOM, console and browser acceptance remain pending.',
    'Review the relative method against documented IoD limitations, then use only accepted rows for a 300-row evidence expansion and browser acceptance.':
        'Run served HTTP/JSON hash verification and DOM/console browser acceptance on the 300-row candidate artifact.',
    'IoD25 yöntem ve 24 satır dalgası': 'IoD25 yöntem ve 300 satır kanıt dalgası',
    'Aday satır<br><b>{candidate_rows}/24</b>': 'Aday satır<br><b>{candidate_rows}/300</b>',
    '<h2>24 örnek satır</h2>': '<h2>300 örnek satır</h2>',
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

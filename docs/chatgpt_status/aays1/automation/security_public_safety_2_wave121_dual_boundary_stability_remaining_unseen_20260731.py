from __future__ import annotations

import subprocess
from pathlib import Path

BASE_SCRIPT = Path("docs/chatgpt_status/aays1/automation/security_public_safety_2_wave120_dual_boundary_stability_expanded_sample_20260731.py")
EXPECTED_BASE_GIT_BLOB = "ef37945738b79aeb7339602862d731d73161ec06"

if not BASE_SCRIPT.is_file():
    raise SystemExit(f"BASE_SCRIPT_MISSING:{BASE_SCRIPT}")
actual_blob = subprocess.check_output(["git", "hash-object", str(BASE_SCRIPT)], text=True).strip()
if actual_blob != EXPECTED_BASE_GIT_BLOB:
    raise SystemExit(f"BASE_SCRIPT_BLOB_MISMATCH:{actual_blob}")

source = BASE_SCRIPT.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global source
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_ANCHOR_COUNT_MISMATCH:{count}:{old[:80]}")
    source = source.replace(old, new, 1)


replace_once(
    'TASK_ID = "security_public_safety_2_wave120_dual_boundary_stability_expanded_sample_20260731"',
    'TASK_ID = "security_public_safety_2_wave121_dual_boundary_stability_remaining_unseen_20260731"',
)
replace_once(
    'CONTINUATION_KEY = "6fd8052994e8d31f705cf7400215885ba8cbfaad40e0aae7ff0ce6226d49fe18"',
    'CONTINUATION_KEY = "6d5bcc3d1a61ed2ea8c0c0144ede18d9bd161bc72c4028f259e971d48416a865"',
)
replace_once(
    'WAVE119_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_dual_boundary_stability_sample_wave119_latest.json"\n'
    'OUTPUT_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_dual_boundary_stability_expanded_sample_wave120_latest.json"\n'
    'OUTPUT_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_dual_boundary_stability_expanded_sample_wave120.html"',
    'WAVE119_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_dual_boundary_stability_sample_wave119_latest.json"\n'
    'WAVE120_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_dual_boundary_stability_expanded_sample_wave120_latest.json"\n'
    'OUTPUT_JSON = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_dual_boundary_stability_remaining_unseen_wave121_latest.json"\n'
    'OUTPUT_HTML = ROOT / "england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_dual_boundary_stability_remaining_unseen_wave121.html"',
)
replace_once(
    'USER_AGENT = "AAYS-TerraYield-security-public-safety-wave120/1.0"',
    'USER_AGENT = "AAYS-TerraYield-security-public-safety-wave121/1.0"',
)
replace_once(
    'WAVE119_AUDITED_ROWS = 64\n'
    'WAVE119_HIGH_CONFIDENCE_ROWS = 30506\n'
    'WAVE119_ACCURACY_PERCENT = 99.171028\n'
    'SAMPLE_ROWS = 128',
    'WAVE119_AUDITED_ROWS = 64\n'
    'WAVE120_AUDITED_ROWS = 128\n'
    'WAVE119_HIGH_CONFIDENCE_ROWS = 30506\n'
    'WAVE119_ACCURACY_PERCENT = 99.171028\n'
    'PRIOR_HIGH_CONFIDENCE_ROWS = 30629\n'
    'PRIOR_ACCURACY_PERCENT = 99.570885\n'
    'SAMPLE_ROWS = 125',
)
replace_once(
    'wave118 = read_json(WAVE118_JSON)\n'
    'wave119 = read_json(WAVE119_JSON)\n'
    'wave119_result = wave119.get("result") or {}\n'
    'if int(wave119_result.get("rows_audited") or 0) != WAVE119_AUDITED_ROWS:\n'
    '    raise SystemExit("WAVE119_AUDIT_COUNT_MISMATCH")\n'
    'if int(wave119_result.get("high_confidence_support_rows_after_sample") or 0) != WAVE119_HIGH_CONFIDENCE_ROWS:\n'
    '    raise SystemExit("WAVE119_HIGH_CONFIDENCE_MISMATCH")',
    'wave118 = read_json(WAVE118_JSON)\n'
    'wave119 = read_json(WAVE119_JSON)\n'
    'wave120 = read_json(WAVE120_JSON)\n'
    'wave119_result = wave119.get("result") or {}\n'
    'wave120_result = wave120.get("result") or {}\n'
    'if int(wave119_result.get("rows_audited") or 0) != WAVE119_AUDITED_ROWS:\n'
    '    raise SystemExit("WAVE119_AUDIT_COUNT_MISMATCH")\n'
    'if int(wave119_result.get("high_confidence_support_rows_after_sample") or 0) != WAVE119_HIGH_CONFIDENCE_ROWS:\n'
    '    raise SystemExit("WAVE119_HIGH_CONFIDENCE_MISMATCH")\n'
    'if int(wave120_result.get("rows_audited") or 0) != WAVE120_AUDITED_ROWS:\n'
    '    raise SystemExit("WAVE120_AUDIT_COUNT_MISMATCH")\n'
    'if int(wave120_result.get("high_confidence_support_rows_after_sample") or 0) != PRIOR_HIGH_CONFIDENCE_ROWS:\n'
    '    raise SystemExit("WAVE120_HIGH_CONFIDENCE_MISMATCH")',
)
replace_once(
    'wave119_ids = {\n'
    '    str(row.get("parcel_id") or "")\n'
    '    for row in (wave119.get("rows") or [])\n'
    '    if isinstance(row, dict)\n'
    '}\n'
    'remaining_unseen = [\n'
    '    row for row in held_rows\n'
    '    if str(row.get("parcel_id") or "") not in wave119_ids\n'
    ']\n'
    'sample = remaining_unseen[:SAMPLE_ROWS]\n'
    'if len(sample) != SAMPLE_ROWS:\n'
    '    raise SystemExit(f"SAMPLE_SCOPE_INCOMPLETE:{len(sample)}")',
    'wave119_ids = {\n'
    '    str(row.get("parcel_id") or "")\n'
    '    for row in (wave119.get("rows") or [])\n'
    '    if isinstance(row, dict)\n'
    '}\n'
    'wave120_ids = {\n'
    '    str(row.get("parcel_id") or "")\n'
    '    for row in (wave120.get("rows") or [])\n'
    '    if isinstance(row, dict)\n'
    '}\n'
    'if len(wave119_ids) != WAVE119_AUDITED_ROWS or len(wave120_ids) != WAVE120_AUDITED_ROWS:\n'
    '    raise SystemExit("PRIOR_WAVE_ID_COUNT_MISMATCH")\n'
    'if wave119_ids & wave120_ids:\n'
    '    raise SystemExit("PRIOR_WAVE_ID_OVERLAP")\n'
    'audited_ids = wave119_ids | wave120_ids\n'
    'remaining_unseen = [\n'
    '    row for row in held_rows\n'
    '    if str(row.get("parcel_id") or "") not in audited_ids\n'
    ']\n'
    'sample = remaining_unseen\n'
    'if len(sample) != SAMPLE_ROWS:\n'
    '    raise SystemExit(f"REMAINING_UNSEEN_SCOPE_MISMATCH:{len(sample)}")',
)
replace_once('thread_name_prefix="wave120"', 'thread_name_prefix="wave121"')
replace_once(
    'high_confidence_after = WAVE119_HIGH_CONFIDENCE_ROWS + passed',
    'high_confidence_after = PRIOR_HIGH_CONFIDENCE_ROWS + passed',
)
replace_once(
    '"wave119_high_confidence_rows": WAVE119_HIGH_CONFIDENCE_ROWS,\n'
    '    "high_confidence_support_rows_after_sample": high_confidence_after,\n'
    '    "wave119_accuracy_percent": WAVE119_ACCURACY_PERCENT,',
    '"prior_high_confidence_support_rows": PRIOR_HIGH_CONFIDENCE_ROWS,\n'
    '    "high_confidence_support_rows_after_sample": high_confidence_after,\n'
    '    "prior_accuracy_percent": PRIOR_ACCURACY_PERCENT,\n'
    '    "held_scope_audit_progress_percent": 100.0,',
)
replace_once(
    '"wave119_audited_rows_excluded": WAVE119_AUDITED_ROWS,',
    '"wave119_audited_rows_excluded": WAVE119_AUDITED_ROWS,\n'
    '        "wave120_audited_rows_excluded": WAVE120_AUDITED_ROWS,\n'
    '        "prior_audited_rows_excluded_total": WAVE119_AUDITED_ROWS + WAVE120_AUDITED_ROWS,',
)
replace_once(
    '{"operation": "wave118_held_scope_gate", "status": "PASS"},',
    '{"operation": "wave118_held_and_prior_wave_exclusion_gate", "status": "PASS"},',
)
source = source.replace(
    'COMPLETED_DUAL_BOUNDARY_STABILITY_EXPANDED_SAMPLE_PUBLISHED',
    'COMPLETED_DUAL_BOUNDARY_STABILITY_REMAINING_UNSEEN_PUBLISHED',
)
source = source.replace('Wave120', 'Wave121')
source = source.replace('geniş çift sınır kararlılık örneği', 'kalan görülmemiş çift sınır kararlılık denetimi')
source = source.replace(
    "Wave119'da incelenmeyen sonraki {SAMPLE_ROWS} HELD satır",
    "Wave119 ve Wave120'de incelenmeyen kalan tüm {SAMPLE_ROWS} HELD satır",
)

exec(compile(source, str(Path(__file__)), "exec"), {"__name__": "__main__"})

from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_5270row_incremental_evidence_expansion_20260730.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

# Direct wrapper over the canonical 340-row generator via the verified wave56
# transformer. Official-source, exact-code boundary recovery and fail-closed
# semantics remain unchanged.
text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("priority_5270row_evidence_expansion_latest.json", "priority_10660row_evidence_expansion_latest.json"),
    ("priority_5270row_evidence_expansion.html", "priority_10660row_evidence_expansion.html"),
    ("priority_4960row_evidence_expansion_latest.json", "priority_10210row_evidence_expansion_latest.json"),
    ("priority_310row_wave56_latest.json", "priority_450row_wave70_latest.json"),
    ("priority_310row_wave56.html", "priority_450row_wave70.html"),
    ("AAYS-TerraYield-security-public-safety-wave56-boundary-recovery/1.0", "AAYS-TerraYield-security-public-safety-wave70-boundary-recovery/1.0"),
    ("range(30762, 35722)", "range(30762, 40972)"),
    ("range(35722, 36032)", "range(40972, 41422)"),
    ("PREVIOUS_4960_SEQUENCE_MISMATCH", "PREVIOUS_10210_SEQUENCE_MISMATCH"),
    ("wave56_incremental_target_310_ids_unique", "wave70_incremental_target_450_ids_unique"),
    ("len(target_features) == 310", "len(target_features) == 450"),
    ("wave56_incremental_valid_wgs84_points", "wave70_incremental_valid_wgs84_points"),
    ("valid_points == 310", "valid_points == 450"),
    ("wave56_incremental_single_ons_lsoa_matches", "wave70_incremental_single_ons_lsoa_matches"),
    ("ons_rows == 310", "ons_rows == 450"),
    ("wave56_incremental_police_response_hashes", "wave70_incremental_police_response_hashes"),
    ("police_hash_rows >= 295", "police_hash_rows >= 428"),
    ("wave56_incremental_candidate_310_rows_generated", "wave70_incremental_candidate_450_rows_generated"),
    ("candidate_rows == 310", "candidate_rows == 450"),
    ("IOD25_RELATIVE_SECURITY_INCREMENTAL_310_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_INCREMENTAL_450_ROWS_PREPARED_NOT_PROMOTED"),
    ("MERGE_WITH_ACCEPTED_4960_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE", "MERGE_WITH_ACCEPTED_10210_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE"),
    ("accepted 4960-row wave", "accepted 10210-row wave"),
    ("merge_with_accepted_4960_candidate_rows", "merge_with_accepted_10210_candidate_rows"),
    ("Merge the 310 validated incremental rows with the accepted 4960-row artifact", "Merge the 450 validated incremental rows with the accepted 10210-row artifact"),
    ("IoD25 310 satır artımlı kanıt dalgası", "IoD25 450 satır artımlı kanıt dalgası"),
    ("Aday satır<br><b>{candidate_rows}/310</b>", "Aday satır<br><b>{candidate_rows}/450</b>"),
    ("<h2>310 artımlı örnek satır</h2>", "<h2>450 artımlı örnek satır</h2>"),
    ("INCREMENTAL_310_SEQUENCE_MISMATCH", "INCREMENTAL_450_SEQUENCE_MISMATCH"),
    ("len(set(row_ids)) != 5270", "len(set(row_ids)) != 10660"),
    ("MERGED_5270_SEQUENCE_OR_UNIQUENESS_FAILED", "MERGED_10660_SEQUENCE_OR_UNIQUENESS_FAILED"),
    ("accepted_4960row_base_present", "accepted_10210row_base_present"),
    ("incremental_310_ids_unique", "incremental_450_ids_unique"),
    ("merged_5270_ids_sequential_unique", "merged_10660_ids_sequential_unique"),
    ("valid_wgs84_points_5270", "valid_wgs84_points_10660"),
    ("valid_points == 5270", "valid_points == 10660"),
    ("single_ons_lsoa_matches_5270", "single_ons_lsoa_matches_10660"),
    ("ons_rows == 5270", "ons_rows == 10660"),
    ("police_hash_rows >= 5007", "police_hash_rows >= 10127"),
    ("iod25_exact_lsoa_joins_5270", "iod25_exact_lsoa_joins_10660"),
    ("iod_join_rows == 5270", "iod_join_rows == 10660"),
    ("candidate_rows_5270", "candidate_rows_10660"),
    ("candidate_rows == 5270", "candidate_rows == 10660"),
    ("candidate_accuracy_ge_95_rows_ge_5007", "candidate_accuracy_ge_95_rows_ge_10127"),
    ("accuracy_ge_95_rows >= 5007", "accuracy_ge_95_rows >= 10127"),
    ('"schema_version": 34', '"schema_version": 48'),
    ("IOD25_RELATIVE_SECURITY_PRIORITY_5270_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_PRIORITY_10660_ROWS_PREPARED_NOT_PROMOTED"),
    ("HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_5270_ROWS", "HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_10660_ROWS"),
    ("pending for the 5270-row artifact", "pending for the 10660-row artifact"),
    ("on the 5270-row candidate artifact", "on the 10660-row candidate artifact"),
    ('"base_rows": 4960', '"base_rows": 10210'),
    ('"added_rows": 310', '"added_rows": 450'),
    ("<title>security_public_safety_2 — 5270 satır</title>", "<title>security_public_safety_2 — 10660 satır</title>"),
    ("<h1>security_public_safety_2 — 5270 satır aday kanıtı</h1>", "<h1>security_public_safety_2 — 10660 satır aday kanıtı</h1>"),
    ("Aday satır<br><b>{candidate_rows}/5270</b>", "Aday satır<br><b>{candidate_rows}/10660</b>"),
    ("<h2>5270 örnek satır</h2>", "<h2>10660 örnek satır</h2>"),
    ("aays_wave56_iod_", "aays_wave70_iod_"),
    ("iod_rows == 5270", "iod_rows == 10660"),
    ("accuracy_rows >= 5007", "accuracy_rows >= 10127"),
    ("ons_rows != 5270 or iod_rows != 5270 or candidate_rows != 5270", "ons_rows != 10660 or iod_rows != 10660 or candidate_rows != 10660"),
]
for old, new in replacements:
    text = text.replace(old, new)

required = [
    'SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_340row_incremental_evidence_expansion_20260729.py"',
    "priority_10660row_evidence_expansion_latest.json",
    "priority_450row_wave70_latest.json",
    "range(40972, 41422)",
    "police_hash_rows >= 428",
    "accuracy_rows >= 10127",
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"DIRECT_WRAPPER_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

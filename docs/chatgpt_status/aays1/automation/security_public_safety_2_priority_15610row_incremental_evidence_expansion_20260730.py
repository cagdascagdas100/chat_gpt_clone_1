from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_5270row_incremental_evidence_expansion_20260730.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("priority_5270row_evidence_expansion_latest.json", "priority_15610row_evidence_expansion_latest.json"),
    ("priority_5270row_evidence_expansion.html", "priority_15610row_evidence_expansion.html"),
    ("priority_4960row_evidence_expansion_latest.json", "priority_15160row_evidence_expansion_latest.json"),
    ("priority_310row_wave56_latest.json", "priority_450row_wave81_latest.json"),
    ("priority_310row_wave56.html", "priority_450row_wave81.html"),
    ("AAYS-TerraYield-security-public-safety-wave56-boundary-recovery/1.0", "AAYS-TerraYield-security-public-safety-wave81-boundary-recovery/1.0"),
    ("range(30762, 35722)", "range(30762, 45922)"),
    ("range(35722, 36032)", "range(45922, 46372)"),
    ("PREVIOUS_4960_SEQUENCE_MISMATCH", "PREVIOUS_15160_SEQUENCE_MISMATCH"),
    ("wave56_incremental_target_310_ids_unique", "wave81_incremental_target_450_ids_unique"),
    ("len(target_features) == 310", "len(target_features) == 450"),
    ("wave56_incremental_valid_wgs84_points", "wave81_incremental_valid_wgs84_points"),
    ("valid_points == 310", "valid_points == 450"),
    ("wave56_incremental_single_ons_lsoa_matches", "wave81_incremental_single_ons_lsoa_matches"),
    ("ons_rows == 310", "ons_rows == 450"),
    ("wave56_incremental_police_response_hashes", "wave81_incremental_police_response_hashes"),
    ("police_hash_rows >= 295", "police_hash_rows >= 428"),
    ("wave56_incremental_candidate_310_rows_generated", "wave81_incremental_candidate_450_rows_generated"),
    ("candidate_rows == 310", "candidate_rows == 450"),
    ("IOD25_RELATIVE_SECURITY_INCREMENTAL_310_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_INCREMENTAL_450_ROWS_PREPARED_NOT_PROMOTED"),
    ("MERGE_WITH_ACCEPTED_4960_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE", "MERGE_WITH_ACCEPTED_15160_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE"),
    ("accepted 4960-row wave", "accepted 15160-row wave"),
    ("merge_with_accepted_4960_candidate_rows", "merge_with_accepted_15160_candidate_rows"),
    ("Merge the 310 validated incremental rows with the accepted 4960-row artifact", "Merge the 450 validated incremental rows with the accepted 15160-row artifact"),
    ("IoD25 310 satır artımlı kanıt dalgası", "IoD25 450 satır artımlı kanıt dalgası"),
    ("Aday satır<br><b>{candidate_rows}/310</b>", "Aday satır<br><b>{candidate_rows}/450</b>"),
    ("<h2>310 artımlı örnek satır</h2>", "<h2>450 artımlı örnek satır</h2>"),
    ("INCREMENTAL_310_SEQUENCE_MISMATCH", "INCREMENTAL_450_SEQUENCE_MISMATCH"),
    ("len(set(row_ids)) != 5270", "len(set(row_ids)) != 15610"),
    ("MERGED_5270_SEQUENCE_OR_UNIQUENESS_FAILED", "MERGED_15610_SEQUENCE_OR_UNIQUENESS_FAILED"),
    ("accepted_4960row_base_present", "accepted_15160row_base_present"),
    ("incremental_310_ids_unique", "incremental_450_ids_unique"),
    ("merged_5270_ids_sequential_unique", "merged_15610_ids_sequential_unique"),
    ("valid_wgs84_points_5270", "valid_wgs84_points_15610"),
    ("valid_points == 5270", "valid_points == 15610"),
    ("single_ons_lsoa_matches_5270", "single_ons_lsoa_matches_15610"),
    ("ons_rows == 5270", "ons_rows == 15610"),
    ("police_hash_rows >= 5007", "police_hash_rows >= 14830"),
    ("iod25_exact_lsoa_joins_5270", "iod25_exact_lsoa_joins_15610"),
    ("iod_join_rows == 5270", "iod_join_rows == 15610"),
    ("candidate_rows_5270", "candidate_rows_15610"),
    ("candidate_rows == 5270", "candidate_rows == 15610"),
    ("candidate_accuracy_ge_95_rows_ge_5007", "candidate_accuracy_ge_95_rows_ge_14830"),
    ("accuracy_ge_95_rows >= 5007", "accuracy_ge_95_rows >= 14830"),
    ('"schema_version": 34', '"schema_version": 59'),
    ("IOD25_RELATIVE_SECURITY_PRIORITY_5270_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_PRIORITY_15610_ROWS_PREPARED_NOT_PROMOTED"),
    ("HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_5270_ROWS", "HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_15610_ROWS"),
    ("pending for the 5270-row artifact", "pending for the 15610-row artifact"),
    ("on the 5270-row candidate artifact", "on the 15610-row candidate artifact"),
    ('"base_rows": 4960', '"base_rows": 15160'),
    ('"added_rows": 310', '"added_rows": 450'),
    ("<title>security_public_safety_2 — 5270 satır</title>", "<title>security_public_safety_2 — 15610 satır</title>"),
    ("<h1>security_public_safety_2 — 5270 satır aday kanıtı</h1>", "<h1>security_public_safety_2 — 15610 satır aday kanıtı</h1>"),
    ("Aday satır<br><b>{candidate_rows}/5270</b>", "Aday satır<br><b>{candidate_rows}/15610</b>"),
    ("<h2>5270 örnek satır</h2>", "<h2>15610 örnek satır</h2>"),
    ("aays_wave56_iod_", "aays_wave81_iod_"),
    ("iod_rows == 5270", "iod_rows == 15610"),
    ("accuracy_rows >= 5007", "accuracy_rows >= 14830"),
    ("ons_rows != 5270 or iod_rows != 5270 or candidate_rows != 5270", "ons_rows != 15610 or iod_rows != 15610 or candidate_rows != 15610"),
]
for old, new in replacements:
    text = text.replace(old, new)

required = [
    'SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_340row_incremental_evidence_expansion_20260729.py"',
    "priority_15610row_evidence_expansion_latest.json",
    "priority_450row_wave81_latest.json",
    "range(45922, 46372)",
    "police_hash_rows >= 428",
    "accuracy_rows >= 14830",
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"DIRECT_WRAPPER_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

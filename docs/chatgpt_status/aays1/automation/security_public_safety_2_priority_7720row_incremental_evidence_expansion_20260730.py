from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_5270row_incremental_evidence_expansion_20260730.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

# Direct wrapper over the canonical 340-row generator via the verified wave56
# transformer. Only target values change; official-source and fail-closed
# semantics remain unchanged.
text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("priority_5270row_evidence_expansion_latest.json", "priority_7720row_evidence_expansion_latest.json"),
    ("priority_5270row_evidence_expansion.html", "priority_7720row_evidence_expansion.html"),
    ("priority_4960row_evidence_expansion_latest.json", "priority_7340row_evidence_expansion_latest.json"),
    ("priority_310row_wave56_latest.json", "priority_380row_wave63_latest.json"),
    ("priority_310row_wave56.html", "priority_380row_wave63.html"),
    ("AAYS-TerraYield-security-public-safety-wave56-boundary-recovery/1.0", "AAYS-TerraYield-security-public-safety-wave63-boundary-recovery/1.0"),
    ("range(30762, 35722)", "range(30762, 38102)"),
    ("range(35722, 36032)", "range(38102, 38482)"),
    ("PREVIOUS_4960_SEQUENCE_MISMATCH", "PREVIOUS_7340_SEQUENCE_MISMATCH"),
    ("wave56_incremental_target_310_ids_unique", "wave63_incremental_target_380_ids_unique"),
    ("len(target_features) == 310", "len(target_features) == 380"),
    ("wave56_incremental_valid_wgs84_points", "wave63_incremental_valid_wgs84_points"),
    ("valid_points == 310", "valid_points == 380"),
    ("wave56_incremental_single_ons_lsoa_matches", "wave63_incremental_single_ons_lsoa_matches"),
    ("ons_rows == 310", "ons_rows == 380"),
    ("wave56_incremental_police_response_hashes", "wave63_incremental_police_response_hashes"),
    ("police_hash_rows >= 295", "police_hash_rows >= 361"),
    ("wave56_incremental_candidate_310_rows_generated", "wave63_incremental_candidate_380_rows_generated"),
    ("candidate_rows == 310", "candidate_rows == 380"),
    ("IOD25_RELATIVE_SECURITY_INCREMENTAL_310_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_INCREMENTAL_380_ROWS_PREPARED_NOT_PROMOTED"),
    ("MERGE_WITH_ACCEPTED_4960_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE", "MERGE_WITH_ACCEPTED_7340_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE"),
    ("accepted 4960-row wave", "accepted 7340-row wave"),
    ("merge_with_accepted_4960_candidate_rows", "merge_with_accepted_7340_candidate_rows"),
    ("Merge the 310 validated incremental rows with the accepted 4960-row artifact", "Merge the 380 validated incremental rows with the accepted 7340-row artifact"),
    ("IoD25 310 satır artımlı kanıt dalgası", "IoD25 380 satır artımlı kanıt dalgası"),
    ("Aday satır<br><b>{candidate_rows}/310</b>", "Aday satır<br><b>{candidate_rows}/380</b>"),
    ("<h2>310 artımlı örnek satır</h2>", "<h2>380 artımlı örnek satır</h2>"),
    ("INCREMENTAL_310_SEQUENCE_MISMATCH", "INCREMENTAL_380_SEQUENCE_MISMATCH"),
    ("len(set(row_ids)) != 5270", "len(set(row_ids)) != 7720"),
    ("MERGED_5270_SEQUENCE_OR_UNIQUENESS_FAILED", "MERGED_7720_SEQUENCE_OR_UNIQUENESS_FAILED"),
    ("accepted_4960row_base_present", "accepted_7340row_base_present"),
    ("incremental_310_ids_unique", "incremental_380_ids_unique"),
    ("merged_5270_ids_sequential_unique", "merged_7720_ids_sequential_unique"),
    ("valid_wgs84_points_5270", "valid_wgs84_points_7720"),
    ("valid_points == 5270", "valid_points == 7720"),
    ("single_ons_lsoa_matches_5270", "single_ons_lsoa_matches_7720"),
    ("ons_rows == 5270", "ons_rows == 7720"),
    ("police_hash_rows >= 5007", "police_hash_rows >= 7334"),
    ("iod25_exact_lsoa_joins_5270", "iod25_exact_lsoa_joins_7720"),
    ("iod_join_rows == 5270", "iod_join_rows == 7720"),
    ("candidate_rows_5270", "candidate_rows_7720"),
    ("candidate_rows == 5270", "candidate_rows == 7720"),
    ("candidate_accuracy_ge_95_rows_ge_5007", "candidate_accuracy_ge_95_rows_ge_7334"),
    ("accuracy_ge_95_rows >= 5007", "accuracy_ge_95_rows >= 7334"),
    ('"schema_version": 34', '"schema_version": 41'),
    ("IOD25_RELATIVE_SECURITY_PRIORITY_5270_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_PRIORITY_7720_ROWS_PREPARED_NOT_PROMOTED"),
    ("HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_5270_ROWS", "HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_7720_ROWS"),
    ("pending for the 5270-row artifact", "pending for the 7720-row artifact"),
    ("on the 5270-row candidate artifact", "on the 7720-row candidate artifact"),
    ('"base_rows": 4960', '"base_rows": 7340'),
    ('"added_rows": 310', '"added_rows": 380'),
    ("<title>security_public_safety_2 — 5270 satır</title>", "<title>security_public_safety_2 — 7720 satır</title>"),
    ("<h1>security_public_safety_2 — 5270 satır aday kanıtı</h1>", "<h1>security_public_safety_2 — 7720 satır aday kanıtı</h1>"),
    ("Aday satır<br><b>{candidate_rows}/5270</b>", "Aday satır<br><b>{candidate_rows}/7720</b>"),
    ("<h2>5270 örnek satır</h2>", "<h2>7720 örnek satır</h2>"),
    ("aays_wave56_iod_", "aays_wave63_iod_"),
    ("iod_rows == 5270", "iod_rows == 7720"),
    ("accuracy_rows >= 5007", "accuracy_rows >= 7334"),
    ("ons_rows != 5270 or iod_rows != 5270 or candidate_rows != 5270", "ons_rows != 7720 or iod_rows != 7720 or candidate_rows != 7720"),
]
for old, new in replacements:
    text = text.replace(old, new)

required = [
    'SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_340row_incremental_evidence_expansion_20260729.py"',
    "priority_7720row_evidence_expansion_latest.json",
    "priority_380row_wave63_latest.json",
    "range(38102, 38482)",
    "police_hash_rows >= 361",
    "accuracy_rows >= 7334",
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"DIRECT_WRAPPER_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

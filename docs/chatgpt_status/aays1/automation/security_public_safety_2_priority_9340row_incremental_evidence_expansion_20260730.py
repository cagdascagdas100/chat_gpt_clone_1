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
    ("priority_5270row_evidence_expansion_latest.json", "priority_9340row_evidence_expansion_latest.json"),
    ("priority_5270row_evidence_expansion.html", "priority_9340row_evidence_expansion.html"),
    ("priority_4960row_evidence_expansion_latest.json", "priority_8920row_evidence_expansion_latest.json"),
    ("priority_310row_wave56_latest.json", "priority_420row_wave67_latest.json"),
    ("priority_310row_wave56.html", "priority_420row_wave67.html"),
    ("AAYS-TerraYield-security-public-safety-wave56-boundary-recovery/1.0", "AAYS-TerraYield-security-public-safety-wave67-boundary-recovery/1.0"),
    ("range(30762, 35722)", "range(30762, 39682)"),
    ("range(35722, 36032)", "range(39682, 40102)"),
    ("PREVIOUS_4960_SEQUENCE_MISMATCH", "PREVIOUS_8920_SEQUENCE_MISMATCH"),
    ("wave56_incremental_target_310_ids_unique", "wave67_incremental_target_420_ids_unique"),
    ("len(target_features) == 310", "len(target_features) == 420"),
    ("wave56_incremental_valid_wgs84_points", "wave67_incremental_valid_wgs84_points"),
    ("valid_points == 310", "valid_points == 420"),
    ("wave56_incremental_single_ons_lsoa_matches", "wave67_incremental_single_ons_lsoa_matches"),
    ("ons_rows == 310", "ons_rows == 420"),
    ("wave56_incremental_police_response_hashes", "wave67_incremental_police_response_hashes"),
    ("police_hash_rows >= 295", "police_hash_rows >= 399"),
    ("wave56_incremental_candidate_310_rows_generated", "wave67_incremental_candidate_420_rows_generated"),
    ("candidate_rows == 310", "candidate_rows == 420"),
    ("IOD25_RELATIVE_SECURITY_INCREMENTAL_310_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_INCREMENTAL_420_ROWS_PREPARED_NOT_PROMOTED"),
    ("MERGE_WITH_ACCEPTED_4960_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE", "MERGE_WITH_ACCEPTED_8920_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE"),
    ("accepted 4960-row wave", "accepted 8920-row wave"),
    ("merge_with_accepted_4960_candidate_rows", "merge_with_accepted_8920_candidate_rows"),
    ("Merge the 310 validated incremental rows with the accepted 4960-row artifact", "Merge the 420 validated incremental rows with the accepted 8920-row artifact"),
    ("IoD25 310 satır artımlı kanıt dalgası", "IoD25 420 satır artımlı kanıt dalgası"),
    ("Aday satır<br><b>{candidate_rows}/310</b>", "Aday satır<br><b>{candidate_rows}/420</b>"),
    ("<h2>310 artımlı örnek satır</h2>", "<h2>420 artımlı örnek satır</h2>"),
    ("INCREMENTAL_310_SEQUENCE_MISMATCH", "INCREMENTAL_420_SEQUENCE_MISMATCH"),
    ("len(set(row_ids)) != 5270", "len(set(row_ids)) != 9340"),
    ("MERGED_5270_SEQUENCE_OR_UNIQUENESS_FAILED", "MERGED_9340_SEQUENCE_OR_UNIQUENESS_FAILED"),
    ("accepted_4960row_base_present", "accepted_8920row_base_present"),
    ("incremental_310_ids_unique", "incremental_420_ids_unique"),
    ("merged_5270_ids_sequential_unique", "merged_9340_ids_sequential_unique"),
    ("valid_wgs84_points_5270", "valid_wgs84_points_9340"),
    ("valid_points == 5270", "valid_points == 9340"),
    ("single_ons_lsoa_matches_5270", "single_ons_lsoa_matches_9340"),
    ("ons_rows == 5270", "ons_rows == 9340"),
    ("police_hash_rows >= 5007", "police_hash_rows >= 8873"),
    ("iod25_exact_lsoa_joins_5270", "iod25_exact_lsoa_joins_9340"),
    ("iod_join_rows == 5270", "iod_join_rows == 9340"),
    ("candidate_rows_5270", "candidate_rows_9340"),
    ("candidate_rows == 5270", "candidate_rows == 9340"),
    ("candidate_accuracy_ge_95_rows_ge_5007", "candidate_accuracy_ge_95_rows_ge_8873"),
    ("accuracy_ge_95_rows >= 5007", "accuracy_ge_95_rows >= 8873"),
    ('"schema_version": 34', '"schema_version": 45'),
    ("IOD25_RELATIVE_SECURITY_PRIORITY_5270_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_PRIORITY_9340_ROWS_PREPARED_NOT_PROMOTED"),
    ("HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_5270_ROWS", "HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FOR_9340_ROWS"),
    ("pending for the 5270-row artifact", "pending for the 9340-row artifact"),
    ("on the 5270-row candidate artifact", "on the 9340-row candidate artifact"),
    ('"base_rows": 4960', '"base_rows": 8920'),
    ('"added_rows": 310', '"added_rows": 420'),
    ("<title>security_public_safety_2 — 5270 satır</title>", "<title>security_public_safety_2 — 9340 satır</title>"),
    ("<h1>security_public_safety_2 — 5270 satır aday kanıtı</h1>", "<h1>security_public_safety_2 — 9340 satır aday kanıtı</h1>"),
    ("Aday satır<br><b>{candidate_rows}/5270</b>", "Aday satır<br><b>{candidate_rows}/9340</b>"),
    ("<h2>5270 örnek satır</h2>", "<h2>9340 örnek satır</h2>"),
    ("aays_wave56_iod_", "aays_wave67_iod_"),
    ("iod_rows == 5270", "iod_rows == 9340"),
    ("accuracy_rows >= 5007", "accuracy_rows >= 8873"),
    ("ons_rows != 5270 or iod_rows != 5270 or candidate_rows != 5270", "ons_rows != 9340 or iod_rows != 9340 or candidate_rows != 9340"),
]
for old, new in replacements:
    text = text.replace(old, new)

required = [
    'SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_340row_incremental_evidence_expansion_20260729.py"',
    "priority_9340row_evidence_expansion_latest.json",
    "priority_420row_wave67_latest.json",
    "range(39682, 40102)",
    "police_hash_rows >= 399",
    "accuracy_rows >= 8873",
]
for fragment in required:
    if fragment not in text:
        raise SystemExit(f"DIRECT_WRAPPER_FRAGMENT_MISSING: {fragment}")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

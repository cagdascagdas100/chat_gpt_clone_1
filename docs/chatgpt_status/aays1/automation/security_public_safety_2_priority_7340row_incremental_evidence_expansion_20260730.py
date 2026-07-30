from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_6970row_incremental_evidence_expansion_20260730.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")


def replace_required(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)


# Update total scope first, then accepted base and thresholds.
replace_required("6970", "7340")
replace_required("6610", "6970")
replace_required("6622", "6973")
replace_required('"schema_version": 39', '"schema_version": 40')

increment_replacements = [
    ("priority_360row_wave61_latest.json", "priority_370row_wave62_latest.json"),
    ("priority_360row_wave61.html", "priority_370row_wave62.html"),
    ("range(37372, 37732)", "range(37732, 38102)"),
    ("wave61_incremental_target_360_ids_unique", "wave62_incremental_target_370_ids_unique"),
    ("len(target_features) == 360", "len(target_features) == 370"),
    ("wave61_incremental_valid_wgs84_points", "wave62_incremental_valid_wgs84_points"),
    ("valid_points == 360", "valid_points == 370"),
    ("wave61_incremental_single_ons_lsoa_matches", "wave62_incremental_single_ons_lsoa_matches"),
    ("ons_rows == 360", "ons_rows == 370"),
    ("wave61_incremental_police_response_hashes", "wave62_incremental_police_response_hashes"),
    ("police_hash_rows >= 342", "police_hash_rows >= 352"),
    ("wave61_incremental_candidate_360_rows_generated", "wave62_incremental_candidate_370_rows_generated"),
    ("candidate_rows == 360", "candidate_rows == 370"),
    ("IOD25_RELATIVE_SECURITY_INCREMENTAL_360_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_INCREMENTAL_370_ROWS_PREPARED_NOT_PROMOTED"),
    ("Merge the 360 validated incremental rows", "Merge the 370 validated incremental rows"),
    ("IoD25 360 satır artımlı kanıt dalgası", "IoD25 370 satır artımlı kanıt dalgası"),
    ("Aday satır<br><b>{candidate_rows}/360</b>", "Aday satır<br><b>{candidate_rows}/370</b>"),
    ("<h2>360 artımlı örnek satır</h2>", "<h2>370 artımlı örnek satır</h2>"),
    ("INCREMENTAL_360_SEQUENCE_MISMATCH", "INCREMENTAL_370_SEQUENCE_MISMATCH"),
    ("incremental_360_ids_unique", "incremental_370_ids_unique"),
    ('"added_rows": 360', '"added_rows": 370'),
]
for old, new in increment_replacements:
    replace_required(old, new)

replace_required("range(30762, 37372)", "range(30762, 37732)")
replace_required("wave61", "wave62")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_6610row_incremental_evidence_expansion_20260730.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")


def replace_required(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)


# Update total scope first, then accepted base and thresholds.
replace_required("6610", "6970")
replace_required("6260", "6610")
replace_required("6280", "6622")
replace_required('"schema_version": 38', '"schema_version": 39')

increment_replacements = [
    ("priority_350row_wave60_latest.json", "priority_360row_wave61_latest.json"),
    ("priority_350row_wave60.html", "priority_360row_wave61.html"),
    ("range(37022, 37372)", "range(37372, 37732)"),
    ("wave60_incremental_target_350_ids_unique", "wave61_incremental_target_360_ids_unique"),
    ("len(target_features) == 350", "len(target_features) == 360"),
    ("wave60_incremental_valid_wgs84_points", "wave61_incremental_valid_wgs84_points"),
    ("valid_points == 350", "valid_points == 360"),
    ("wave60_incremental_single_ons_lsoa_matches", "wave61_incremental_single_ons_lsoa_matches"),
    ("ons_rows == 350", "ons_rows == 360"),
    ("wave60_incremental_police_response_hashes", "wave61_incremental_police_response_hashes"),
    ("police_hash_rows >= 333", "police_hash_rows >= 342"),
    ("wave60_incremental_candidate_350_rows_generated", "wave61_incremental_candidate_360_rows_generated"),
    ("candidate_rows == 350", "candidate_rows == 360"),
    ("IOD25_RELATIVE_SECURITY_INCREMENTAL_350_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_INCREMENTAL_360_ROWS_PREPARED_NOT_PROMOTED"),
    ("Merge the 350 validated incremental rows", "Merge the 360 validated incremental rows"),
    ("IoD25 350 satır artımlı kanıt dalgası", "IoD25 360 satır artımlı kanıt dalgası"),
    ("Aday satır<br><b>{candidate_rows}/350</b>", "Aday satır<br><b>{candidate_rows}/360</b>"),
    ("<h2>350 artımlı örnek satır</h2>", "<h2>360 artımlı örnek satır</h2>"),
    ("INCREMENTAL_350_SEQUENCE_MISMATCH", "INCREMENTAL_360_SEQUENCE_MISMATCH"),
    ("incremental_350_ids_unique", "incremental_360_ids_unique"),
    ('"added_rows": 350', '"added_rows": 360'),
]
for old, new in increment_replacements:
    replace_required(old, new)

replace_required("range(30762, 37022)", "range(30762, 37372)")
replace_required("wave60", "wave61")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

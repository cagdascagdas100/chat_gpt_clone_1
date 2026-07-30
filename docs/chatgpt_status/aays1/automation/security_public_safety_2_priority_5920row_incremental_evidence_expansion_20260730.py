from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_priority_5270row_incremental_evidence_expansion_20260730.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")


def replace_required(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)


# Total-scope values first, then accepted-base values.
replace_required("5270", "5920")
replace_required("4960", "5590")
replace_required("5007", "5624")
replace_required('"schema_version": 34', '"schema_version": 36')

increment_replacements = [
    ("priority_310row_wave56_latest.json", "priority_330row_wave58_latest.json"),
    ("priority_310row_wave56.html", "priority_330row_wave58.html"),
    ("range(35722, 36032)", "range(36352, 36682)"),
    ("wave56_incremental_target_310_ids_unique", "wave58_incremental_target_330_ids_unique"),
    ("len(target_features) == 310", "len(target_features) == 330"),
    ("wave56_incremental_valid_wgs84_points", "wave58_incremental_valid_wgs84_points"),
    ("valid_points == 310", "valid_points == 330"),
    ("wave56_incremental_single_ons_lsoa_matches", "wave58_incremental_single_ons_lsoa_matches"),
    ("ons_rows == 310", "ons_rows == 330"),
    ("wave56_incremental_police_response_hashes", "wave58_incremental_police_response_hashes"),
    ("police_hash_rows >= 295", "police_hash_rows >= 314"),
    ("wave56_incremental_candidate_310_rows_generated", "wave58_incremental_candidate_330_rows_generated"),
    ("candidate_rows == 310", "candidate_rows == 330"),
    ("IOD25_RELATIVE_SECURITY_INCREMENTAL_310_ROWS_PREPARED_NOT_PROMOTED", "IOD25_RELATIVE_SECURITY_INCREMENTAL_330_ROWS_PREPARED_NOT_PROMOTED"),
    ("Merge the 310 validated incremental rows", "Merge the 330 validated incremental rows"),
    ("IoD25 310 satır artımlı kanıt dalgası", "IoD25 330 satır artımlı kanıt dalgası"),
    ("Aday satır<br><b>{candidate_rows}/310</b>", "Aday satır<br><b>{candidate_rows}/330</b>"),
    ("<h2>310 artımlı örnek satır</h2>", "<h2>330 artımlı örnek satır</h2>"),
    ("INCREMENTAL_310_SEQUENCE_MISMATCH", "INCREMENTAL_330_SEQUENCE_MISMATCH"),
    ("incremental_310_ids_unique", "incremental_330_ids_unique"),
    ('"added_rows": 310', '"added_rows": 330'),
]
for old, new in increment_replacements:
    replace_required(old, new)

replace_required("range(30762, 35722)", "range(30762, 36352)")
replace_required("wave56", "wave58")

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

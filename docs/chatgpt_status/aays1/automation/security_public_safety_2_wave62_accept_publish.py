from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave61_accept_publish.py"

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
replace_required("0036", "0037")
replace_required(
    "72821d58cee55269d7897425cac337a317486de2481229866b6b3caba36c51e8",
    "6caf87b26dd9c91bae533642684b4d4e4db47145de0ef5ed36a8d9a392cecd4d",
)
replace_required("wave61", "wave62")
replace_required("range(30762, 37732)", "range(30762, 38102)")
replace_required("parcel_37731", "parcel_38101")
replace_required('"progress_delta_percentage_points": 5.16', '"progress_delta_percentage_points": 5.04')
replace_required('"incremental_rows_target": 360', '"incremental_rows_target": 370')
replace_required('"incremental_rows_completed": 360', '"incremental_rows_completed": 370')

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

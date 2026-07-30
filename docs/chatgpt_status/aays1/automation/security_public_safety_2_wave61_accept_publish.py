from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave60_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")


def replace_required(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)


# Update the already-correct wave60 wrapper without touching the base script directly.
replace_required("6610", "6970")
replace_required("6260", "6610")
replace_required("6280", "6622")
replace_required("0035", "0036")
replace_required(
    "6757d62b9226dc562217fd84b23f7b9ef2f9fda4d7362c745ede1abbc8e84947",
    "72821d58cee55269d7897425cac337a317486de2481229866b6b3caba36c51e8",
)
replace_required("wave60", "wave61")
replace_required("range(30762, 37372)", "range(30762, 37732)")
replace_required("parcel_37371", "parcel_37731")
replace_required('"progress_delta_percentage_points": 5.30', '"progress_delta_percentage_points": 5.16')
replace_required('"incremental_rows_target": 350', '"incremental_rows_target": 360')
replace_required('"incremental_rows_completed": 350', '"incremental_rows_completed": 360')

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

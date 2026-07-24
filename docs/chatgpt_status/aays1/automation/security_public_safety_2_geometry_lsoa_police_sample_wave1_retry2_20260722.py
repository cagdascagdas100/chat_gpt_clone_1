from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_20260722.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = {
    '"https://use-land-property-data.service.gov.uk/datasets/inspire/download"':
        '"https://use-land-property-data.service.gov.uk/datasets/inspire"',
    '"name": "HM Land Registry INSPIRE Index Polygons download"':
        '"name": "HM Land Registry INSPIRE Index Polygons dataset"',
    '"role": "indicative_freehold_polygon_download"':
        '"role": "indicative_freehold_dataset_access_page"',
    '"gate": "hmlr_download_route_reachable"':
        '"gate": "hmlr_official_dataset_page_reachable"',
}

for old, new in replacements.items():
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {
    "__name__": "__main__",
    "__file__": str(SOURCE),
    "__package__": None,
}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)

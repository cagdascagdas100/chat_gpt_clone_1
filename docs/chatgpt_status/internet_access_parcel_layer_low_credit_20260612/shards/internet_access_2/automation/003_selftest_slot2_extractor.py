#!/usr/bin/env python3
"""Deterministic safety self-test for the internet_access_2 extractor.

Synthetic fixtures test code contracts only. They are never business evidence.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("002_extract_slot2_ofcom_2026_candidates.py")
spec = importlib.util.spec_from_file_location("internet_access_2_extractor", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import extractor: {SCRIPT}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.ROW_START = 1
module.ROW_END = 3
module.EXPECTED_ROWS = 3
module.EXPECTED_OFCOM_FILE_COUNT = 1
module.EXPECTED_OFCOM_POSTCODE_ROWS = 2

passed: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    passed.append(name)


with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    ofcom_dir = root / "ofcom"
    ofcom_dir.mkdir()

    canonical = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-0.2, 51]}, "properties": {"row_no": 1, "parcel_id": "parcel_1", "hmlr_inspire_id": "A", "hmlr_lon": -0.2, "hmlr_lat": 51, "postcode": "AA1 1AA"}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [1, 52]}, "properties": {"row_no": 2, "parcel_id": "parcel_2", "hmlr_inspire_id": "B", "hmlr_lon": 1, "hmlr_lat": 52}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [2, 53]}, "properties": {"row_no": 3, "parcel_id": "parcel_3", "hmlr_inspire_id": "C", "hmlr_lon": 2, "hmlr_lat": 53}},
        ],
    }
    canonical_path = root / "canonical.geojson"
    canonical_path.write_text(json.dumps(canonical), encoding="utf-8")

    legacy = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": None, "properties": {"row_no": 2, "parcel_id": "parcel_2", "internet_level_value": "High; postcode=BB2 2BB; gigabit=90.0%"}}
        ],
    }
    legacy_path = root / "legacy.geojson"
    legacy_path.write_text(json.dumps(legacy), encoding="utf-8")

    headers = [
        "postcode",
        "postcode_space",
        "postcode area",
        "SFBB availability (% premises)",
        "UFBB (100Mbit/s) availability (% premises)",
        "UFBB availability (% premises)",
        "Gigabit availability (% premises)",
        "% of premises unable to receive 30Mbit/s",
        "% of premises unable to receive decent broadband from fixed or FWA",
    ]
    r2_path = ofcom_dir / "202601_fixed_postcode_coverage_r2_AA.csv"
    with r2_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerow({"postcode": "AA11AA", "postcode_space": "AA1 1AA", "postcode area": "AA", "SFBB availability (% premises)": "100", "UFBB (100Mbit/s) availability (% premises)": "99", "UFBB availability (% premises)": "98", "Gigabit availability (% premises)": "97", "% of premises unable to receive 30Mbit/s": "0", "% of premises unable to receive decent broadband from fixed or FWA": "0"})
        writer.writerow({"postcode": "BB22BB", "postcode_space": "BB2 2BB", "postcode area": "BB", "SFBB availability (% premises)": "90", "UFBB (100Mbit/s) availability (% premises)": "80", "UFBB availability (% premises)": "70", "Gigabit availability (% premises)": "60", "% of premises unable to receive 30Mbit/s": "10", "% of premises unable to receive decent broadband from fixed or FWA": "5"})

    rows = module.load_canonical(canonical_path)
    check("canonical_range_and_count", len(rows) == 3 and module.row_number(rows[0]) == 1 and module.row_number(rows[-1]) == 3)
    check("canonical_ids_unique", len({module.canonical_id(row) for row in rows}) == 3)
    legacy_rows = module.load_legacy_internet(legacy_path)
    coverage, files = module.load_ofcom_postcodes(ofcom_dir)
    check("corrected_r2_contract", len(files) == 1 and len(coverage) == 2)
    output = module.build_rows(rows, legacy_rows, coverage)
    check("direct_match", output[0]["status"] == "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_REVIEW" and output[0]["internet_match_confidence"] == 0.95)
    check("legacy_match", output[1]["status"] == "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA" and output[1]["internet_match_confidence"] == 0.70)
    check("no_data", output[2]["status"] == "NO_DATA" and output[2]["internet_match_confidence"] == 0.0)
    check("no_score_emitted", all(row["internet_availability_quality_percent"] is None for row in output))
    check("negative_longitude_preserved", output[0]["parcel_centroid_lon"] == -0.2)

    r1_path = ofcom_dir / "202601_fixed_postcode_coverage_r1_AA.csv"
    r1_path.write_text("postcode\nAA11AA\n", encoding="utf-8")
    try:
        module.load_ofcom_postcodes(ofcom_dir)
    except ValueError as exc:
        check("superseded_r1_rejected", "Superseded" in str(exc))
    else:
        raise AssertionError("superseded_r1_rejected")
    r1_path.unlink()

    bad_path = ofcom_dir / "202601_fixed_postcode_coverage_r2_AA.csv"
    with bad_path.open("r", encoding="utf-8") as handle:
        rows_bad = list(csv.DictReader(handle))
    rows_bad[0]["Gigabit availability (% premises)"] = "101"
    with bad_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows_bad)
    try:
        module.load_ofcom_postcodes(ofcom_dir)
    except ValueError as exc:
        check("out_of_range_percent_rejected", "outside 0-100" in str(exc))
    else:
        raise AssertionError("out_of_range_percent_rejected")

    canonical_dup = json.loads(json.dumps(canonical))
    canonical_dup["features"][2]["properties"]["row_no"] = 2
    dup_path = root / "canonical_dup.geojson"
    dup_path.write_text(json.dumps(canonical_dup), encoding="utf-8")
    try:
        module.load_canonical(dup_path)
    except ValueError:
        check("duplicate_canonical_row_rejected", True)
    else:
        raise AssertionError("duplicate_canonical_row_rejected")

    check("business_rows_unchanged", all(row["business_row_written"] is False for row in output))

print(json.dumps({"status": "PASS", "tests_passed": len(passed), "tests_total": 12, "test_names": passed, "business_rows_written": 0, "fake_data_business": False}, sort_keys=True))

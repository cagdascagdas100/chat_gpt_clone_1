#!/usr/bin/env python3
"""Deterministic contract self-test for internet_access_3 extractor.

This test uses temporary synthetic fixtures only to verify safety gates. It never
writes product/business rows and must not be presented as parcel evidence.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("002_extract_slot3_ofcom_2026_candidates.py")
spec = importlib.util.spec_from_file_location("internet_access_3_extractor", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import extractor: {SCRIPT}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

module.ROW_START = 1
module.ROW_END = 3
module.EXPECTED_ROWS = 3
module.EXPECTED_OFCOM_FILE_COUNT = 1
module.EXPECTED_OFCOM_POSTCODE_ROWS = 2

with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    ofcom_dir = root / "ofcom"
    ofcom_dir.mkdir()

    canonical = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [0, 51]}, "properties": {"row_no": 1, "parcel_id": "parcel_1", "hmlr_inspire_id": "A", "hmlr_lon": 0, "hmlr_lat": 51, "postcode": "AA1 1AA"}},
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
    legacy_rows = module.load_legacy_internet(legacy_path)
    coverage, files = module.load_ofcom_postcodes(ofcom_dir)
    output = module.build_rows(rows, legacy_rows, coverage)

    assert len(output) == 3 and len(files) == 1
    assert output[0]["status"] == "CURRENT_R2_DIRECT_POSTCODE_READY_FOR_SCORING"
    assert output[0]["internet_match_confidence"] == 0.95
    assert output[1]["status"] == "CURRENT_R2_LEGACY_POSTCODE_MATCH_PENDING_SPATIAL_QA"
    assert output[1]["internet_match_confidence"] == 0.70
    assert output[2]["status"] == "NO_DATA"
    assert output[2]["internet_availability_quality_percent"] is None

    r1_path = ofcom_dir / "202601_fixed_postcode_coverage_r1_AA.csv"
    r1_path.write_text("postcode\nAA11AA\n", encoding="utf-8")
    try:
        module.load_ofcom_postcodes(ofcom_dir)
    except ValueError as exc:
        assert "Superseded" in str(exc)
    else:
        raise AssertionError("r1 input was not rejected")

print(json.dumps({"status": "PASS", "tests": 7, "business_rows_written": 0, "fake_data_business": False}, sort_keys=True))

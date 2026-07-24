#!/usr/bin/env python3
"""Deterministic safety-contract test for the internet_access_3 extractor.

Temporary fixtures validate code behavior only. They are never business evidence.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("002_extract_slot3_ofcom_2026_candidates.py")
spec = importlib.util.spec_from_file_location("extractor", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import {SCRIPT}")
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
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-0.2, 51.5]}, "properties": {"row_no": 1, "parcel_id": "parcel_1", "hmlr_row_id": "1", "hmlr_inspire_id": "A", "hmlr_lon": -0.2, "hmlr_lat": 51.5}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [0.1, 51.6]}, "properties": {"row_no": 2, "parcel_id": "parcel_2", "hmlr_row_id": "2", "hmlr_inspire_id": "B", "hmlr_lon": 0.1, "hmlr_lat": 51.6}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [0.2, 51.7]}, "properties": {"row_no": 3, "parcel_id": "parcel_3", "hmlr_row_id": "3", "hmlr_inspire_id": "C", "hmlr_lon": 0.2, "hmlr_lat": 51.7}}
        ]
    }
    canonical_path = root / "canonical.geojson"
    canonical_path.write_text(json.dumps(canonical), encoding="utf-8")

    legacy = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": None, "properties": {"row_no": 1, "parcel_id": "parcel_1", "hmlr_inspire_id": "A", "internet_level_value": "High; postcode=AA1 1AA; gigabit=90%"}},
            {"type": "Feature", "geometry": None, "properties": {"row_no": 2, "parcel_id": "WRONG", "hmlr_inspire_id": "B", "internet_level_value": "High; postcode=BB2 2BB"}}
        ]
    }
    legacy_path = root / "legacy.geojson"
    legacy_path.write_text(json.dumps(legacy), encoding="utf-8")

    headers = [
        "postcode", "postcode_space", "postcode area",
        "SFBB availability (% premises)",
        "UFBB (100Mbit/s) availability (% premises)",
        "UFBB availability (% premises)",
        "Gigabit availability (% premises)",
        "% of premises unable to receive 30Mbit/s",
        "% of premises unable to receive decent broadband from fixed or FWA"
    ]
    r2_path = ofcom_dir / "202601_fixed_postcode_coverage_r2_AA.csv"
    with r2_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for postcode, postcode_space, area in [("AA11AA", "AA1 1AA", "AA"), ("BB22BB", "BB2 2BB", "BB")]:
            writer.writerow({
                "postcode": postcode,
                "postcode_space": postcode_space,
                "postcode area": area,
                "SFBB availability (% premises)": "100",
                "UFBB (100Mbit/s) availability (% premises)": "99",
                "UFBB availability (% premises)": "98",
                "Gigabit availability (% premises)": "97",
                "% of premises unable to receive 30Mbit/s": "0",
                "% of premises unable to receive decent broadband from fixed or FWA": "0"
            })

    rows = module.load_canonical(canonical_path)
    legacy_rows = module.load_legacy_internet(legacy_path)
    coverage, files = module.load_ofcom_postcodes(ofcom_dir)
    output = module.build_rows(rows, legacy_rows, coverage)

    assert len(rows) == 3 and len(files) == 1
    assert output[0]["status"] == "CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW"
    assert output[0]["internet_match_confidence"] == 0.90
    assert output[0]["parcel_centroid_lon"] == -0.2
    assert output[1]["status"] == "IDENTITY_CONFLICT_NO_DATA"
    assert "gigabit_available_pct" not in output[1]
    assert output[2]["status"] == "NO_VERIFIED_POSTCODE_NO_DATA"
    assert output[2]["postcode"] is None
    assert all(row["internet_availability_quality_percent"] is None for row in output)

    r1_path = ofcom_dir / "202601_fixed_postcode_coverage_r1_AA.csv"
    r1_path.write_text("postcode\nAA11AA\n", encoding="utf-8")
    try:
        module.load_ofcom_postcodes(ofcom_dir)
    except ValueError as exc:
        assert "r1" in str(exc)
    else:
        raise AssertionError("Superseded r1 input was not rejected")

print(json.dumps({"status": "PASS", "tests": 9, "business_rows_written": 0, "scores_written": 0}, sort_keys=True))

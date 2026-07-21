#!/usr/bin/env python3
"""Deterministic tests for the bounded streaming GeoJSON slicer."""
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("005_stream_extract_slot3_inputs.py")
spec = importlib.util.spec_from_file_location("streamer", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import streamer")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROW_START = 2
module.ROW_END = 4
module.EXPECTED_CANONICAL_ROWS = 3


def feature(number: int, *, include_id: bool = True) -> dict:
    props = {"row_no": number, "hmlr_inspire_id": f"H{number}"}
    if include_id:
        props["parcel_id"] = f"parcel_{number}"
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [number / 10, 51.0]}, "properties": props}


with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    canonical_path = root / "canonical.geojson"
    legacy_path = root / "legacy.geojson"
    output_dir = root / "out"
    canonical_payload = {"type": "FeatureCollection", "metadata": {"x": 1}, "features": [feature(i) for i in range(1, 6)]}
    legacy_payload = {"type": "FeatureCollection", "features": [feature(2), feature(4), feature(5)]}
    canonical_path.write_text(json.dumps(canonical_payload, separators=(",", ":")), encoding="utf-8")
    legacy_path.write_text(json.dumps(legacy_payload, separators=(",", ":")), encoding="utf-8")

    canonical_out = output_dir / "canonical.geojson"
    legacy_out = output_dir / "legacy.geojson"
    c = module.write_filtered_geojson(canonical_path, canonical_out, require_exact_count=True, chunk_size=17)
    l = module.write_filtered_geojson(legacy_path, legacy_out, require_exact_count=False, chunk_size=13)
    c_payload = json.loads(canonical_out.read_text(encoding="utf-8"))
    l_payload = json.loads(legacy_out.read_text(encoding="utf-8"))

    checks = {
        "tiny_chunk_feature_stream": [f["properties"]["row_no"] for f in module.iter_feature_collection(canonical_path, 11)] == [1, 2, 3, 4, 5],
        "canonical_exact_count": c["rows"] == 3,
        "canonical_range": [f["properties"]["row_no"] for f in c_payload["features"]] == [2, 3, 4],
        "canonical_unique_ids": c["unique_parcel_ids"] == 3,
        "legacy_subset_count": l["rows"] == 2,
        "legacy_range": [f["properties"]["row_no"] for f in l_payload["features"]] == [2, 4],
        "canonical_hashes": len(c["source_sha256"]) == 64 and len(c["output_sha256"]) == 64,
        "legacy_hashes": len(l["source_sha256"]) == 64 and len(l["output_sha256"]) == 64,
        "no_business_fields_added": all("internet_availability_quality_percent" not in f["properties"] for f in c_payload["features"]),
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise AssertionError(f"failed: {failed}")
    print(json.dumps({"status": "PASS", "tests_passed": len(checks), "tests_total": len(checks), "business_rows_written": 0}, sort_keys=True))

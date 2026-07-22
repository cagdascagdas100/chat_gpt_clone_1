#!/usr/bin/env python3
"""Offline selftest for rows 20-24 extractor revision 2."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("extractor_v2", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("module load failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def payload() -> dict:
    features = []
    for row_no in range(1, 31):
        features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [0.1 + row_no / 10000, 51.5 + row_no / 10000]}, "properties": {"row_no": row_no, "parcel_id": f"parcel_{row_no}", "hmlr_inspire_id": str(90000000 + row_no), "hmlr_area_m2": str(100 + row_no), "london_authority": "Test Authority"}})
    return {"type": "FeatureCollection", "features": features}


def run_case(module, root: Path, name: str, value: dict, expected_pass: bool, expected_sha: str | None = None):
    path = root / f"{name}.geojson"
    data = json.dumps(value, separators=(",", ":")).encode("utf-8")
    path.write_bytes(data)
    sha = expected_sha if expected_sha is not None else git_blob_sha1(data)
    try:
        result = module.extract(path, sha)
        actual_pass = len(result["rows"]) == 5 and result["canonical_git_blob_sha1"] == git_blob_sha1(data) and len(result["canonical_sha256"]) == 64
        error = None
    except Exception as exc:
        actual_pass = False
        error = str(exc)
    return {"name": name, "expected": "PASS" if expected_pass else "FAIL", "actual": "PASS" if actual_pass else "FAIL", "error": error, "result": actual_pass == expected_pass}


def main() -> int:
    extractor_path = Path(__file__).with_name("020_extract_rows_20_24_from_canonical_stream_v2.py")
    module = load_module(extractor_path)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        base = payload()
        cases = [run_case(module, root, "exact_manifest", base, True), run_case(module, root, "wrong_git_blob_sha", base, False, "0" * 40)]
        duplicate = copy.deepcopy(base)
        duplicate["features"].append(copy.deepcopy(duplicate["features"][19]))
        cases.append(run_case(module, root, "duplicate_target_row", duplicate, False))
        missing = copy.deepcopy(base)
        missing["features"] = [feature for feature in missing["features"] if feature["properties"]["row_no"] != 22]
        cases.append(run_case(module, root, "missing_target_row", missing, False))
        wrong_parcel = copy.deepcopy(base)
        wrong_parcel["features"][20]["properties"]["parcel_id"] = "parcel_wrong"
        cases.append(run_case(module, root, "wrong_parcel_identity", wrong_parcel, False))
        duplicate_hmlr = copy.deepcopy(base)
        duplicate_hmlr["features"][23]["properties"]["hmlr_inspire_id"] = duplicate_hmlr["features"][22]["properties"]["hmlr_inspire_id"]
        cases.append(run_case(module, root, "duplicate_hmlr_identity", duplicate_hmlr, False))
    passed = sum(1 for case in cases if case["result"])
    output = {"schema_version": 1, "slot_id": "future_growth_1", "result": "PASS" if passed == len(cases) else "FAIL", "passed": passed, "total": len(cases), "cases": cases, "actual_business_data_rows_written": 0, "final_ready": False}
    print(json.dumps(output, ensure_ascii=False))
    return 0 if passed == len(cases) else 2


if __name__ == "__main__":
    raise SystemExit(main())

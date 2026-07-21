#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import py_compile
import tempfile
from pathlib import Path
from typing import Any

TASK_ID = "aays1-height-difference-2-canonical-export-official-sampling-20260720"
ATTEMPT_ID = "height-difference-2-20260721-020"
TARGET_ROWS = [30762, 46142, 61522]
EXPECTED_EXTRACTOR_BLOB = "7da8bea047b4c3fe57c74e4121cf70dd36d16c54"


def feature(
    row_no: int,
    *,
    inspire_id: str | None = None,
    parcel_id: str | None = None,
    accuracy: str = "4/4",
    lon: float = -0.1,
    lat: float = 51.5,
    area: float = 100.0,
) -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "row_no": row_no,
            "parcel_id": parcel_id or f"parcel_{row_no}",
            "hmlr_row_id": str(row_no + 100),
            "hmlr_inspire_id": inspire_id or str(70000000 + row_no),
            "hmlr_area_m2": str(area),
            "hmlr_lon": lon,
            "hmlr_lat": lat,
            "hmlr_geometry_accuracy": accuracy,
            "london_authority": "Fixture Authority",
        },
    }


def write_fixture(path: Path, features: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    extractor_path = root / "docs/chatgpt_status/topography/shards/height_difference_2/automation/007_extract_three_canonical_candidates.py"
    carrier_path = root / "docs/chatgpt_status/topography/shards/height_difference_2/automation/025_height_difference_2_shared_runner_carrier.ps1"

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    py_compile.compile(str(extractor_path), doraise=True)
    spec = importlib.util.spec_from_file_location("height_difference_2_exact_extractor", extractor_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("EXTRACTOR_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_text = extractor_path.read_text(encoding="utf-8")
    carrier_text = carrier_path.read_text(encoding="utf-8-sig")

    with tempfile.TemporaryDirectory(prefix="height_difference_2_exact_gate_") as temp_name:
        temp = Path(temp_name)
        cases = {
            "positive": [
                feature(1),
                feature(30762),
                feature(40000),
                feature(46142),
                feature(61522),
                feature(70000),
            ],
            "nearest_only": [
                feature(30761),
                feature(30763),
                feature(46141),
                feature(46143),
                feature(61521),
                feature(61523),
            ],
            "missing_middle": [feature(30762), feature(61522)],
            "duplicate_middle": [
                feature(30762),
                feature(46142, inspire_id="A"),
                feature(46142, inspire_id="B"),
                feature(61522),
            ],
            "invalid_accuracy": [
                feature(30762),
                feature(46142, accuracy="2/4"),
                feature(61522),
            ],
            "duplicate_id": [
                feature(30762, inspire_id="SAME"),
                feature(46142, inspire_id="SAME"),
                feature(61522),
            ],
        }
        payloads: dict[str, dict[str, Any]] = {}
        for name, features in cases.items():
            path = temp / f"{name}.geojson"
            write_fixture(path, features)
            payloads[name] = module.extract(path)

    positive = payloads["positive"]
    nearest = payloads["nearest_only"]
    missing = payloads["missing_middle"]
    duplicate = payloads["duplicate_middle"]
    invalid = payloads["invalid_accuracy"]
    duplicate_id = payloads["duplicate_id"]

    check("extractor_compiles", True, "py_compile passed")
    check("target_rows_exact", list(module.TARGET_ROWS) == TARGET_ROWS, "Only the immutable three row numbers are targets.")
    check("nearest_pool_removed", "KEEP_PER_TARGET" not in source_text and "_insert_candidate" not in source_text, "Nearest-row candidate pool is absent.")
    check("nearest_fallback_flag_false", "nearest_row_fallback_used" in source_text, "Output explicitly records no nearest fallback.")
    check("positive_status", positive["status"] == "THREE_EXACT_CANONICAL_CANDIDATE_SEEDS_EXTRACTED", positive["status"])
    check("positive_exact_row_set", [row["row_no"] for row in positive["candidate_seeds"]] == TARGET_ROWS, "Positive fixture returned exact rows.")
    check("positive_zero_distance", all(row["distance_from_target_rows"] == 0 for row in positive["candidate_seeds"]), "All exact rows have zero target distance.")
    check("positive_distinct_ids", positive["distinct_hmlr_inspire_ids_verified"] is True and positive["distinct_parcel_ids_verified"] is True, "Distinct parcel and HMLR IDs verified.")
    check("nearest_only_blocked", nearest["status"].startswith("BLOCKED_") and nearest["candidate_seed_count"] == 0, nearest["status"])
    check("missing_target_blocked", missing["status"].startswith("BLOCKED_") and missing["missing_target_rows"] == [46142], str(missing["missing_target_rows"]))
    check("duplicate_target_blocked", duplicate["status"].startswith("BLOCKED_") and duplicate["duplicate_target_rows"] == [46142], str(duplicate["duplicate_target_rows"]))
    check("invalid_target_blocked", invalid["status"].startswith("BLOCKED_") and invalid["invalid_target_rows"] == [46142], str(invalid["invalid_target_rows"]))
    check("duplicate_hmlr_id_blocked", duplicate_id["status"].startswith("BLOCKED_") and duplicate_id["distinct_hmlr_inspire_ids_verified"] is False, duplicate_id["status"])
    check("legacy_values_not_promoted", positive["legacy_point_topography_values_promoted"] is False, "Legacy point values remain discarded.")
    check("no_measurement_written", positive["official_polygon_measurements_written"] == 0 and all(row["measurement_eligible"] is False for row in positive["candidate_seeds"]), "Candidate extraction writes no measurements.")
    check("carrier_attempt_matches", ATTEMPT_ID in carrier_text, "Carrier uses attempt 020.")
    check("carrier_binds_extractor_blob", EXPECTED_EXTRACTOR_BLOB in carrier_text and "EXACT_ROW_EXTRACTOR_BLOB_MISMATCH" in carrier_text, "Carrier verifies the exact extractor blob.")
    check("carrier_web_floor_325", "$expectedWebRows = 325" in carrier_text and "NEAREST_ROW_FALLBACK=false" in carrier_text, "Carrier publishes the 325-row floor and no-nearest contract.")

    passed = sum(1 for item in checks if item["passed"])
    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_2",
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "status": "PASS" if passed == len(checks) else "FAIL",
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "product_rows_promoted": 0,
        "fixture_or_static_contract_only": True,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": passed == len(checks), "passed": passed, "total": len(checks)}))
    return 0 if passed == len(checks) else 2


if __name__ == "__main__":
    raise SystemExit(main())

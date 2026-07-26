#!/usr/bin/env python3
"""Validate Batch 130 strict-12 outputs before remote GitHub acceptance.

This validator is fail-closed. It cross-checks the candidate-aware PROJ gate,
measurement manifest, verified website JSON/GeoJSON, and Batch 130 acceptance
record. It only writes an acceptance evidence file; it never invents or changes
a height_difference value.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

EXPECTED_ROWS = list(range(61540, 61552))
METHOD = "EA_DTM_1M_POLYGON_P95_MINUS_P05"
ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM_HIGH"}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} is non-finite: {value!r}")
    return number


def _rows(values: list[dict[str, Any]]) -> list[int]:
    return [int(item["row_no"]) for item in values]


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict-output-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args(argv)

    root = args.strict_output_dir.resolve()
    paths = {
        "proj": root / "00_proj_ostn15_gate.json",
        "measurements": root / "measurement" / "official_measurements.json",
        "verified_json": root / "measurement" / "verified_examples.json",
        "verified_geojson": root / "measurement" / "verified_examples.geojson",
        "strict_acceptance": root / "batch130_strict12_acceptance.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing strict12 outputs: {missing}")

    proj = _load(paths["proj"])
    measurements = _load(paths["measurements"])
    verified = _load(paths["verified_json"])
    geojson = _load(paths["verified_geojson"])
    strict = _load(paths["strict_acceptance"])

    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
        if not passed:
            raise ValueError(f"acceptance check failed: {name}: {detail}")

    proj_rows = [int(value) for value in (proj.get("candidate_rows") or [])]
    check("proj_passed", proj.get("passed") is True)
    check("proj_candidate_rows_exact", proj_rows == EXPECTED_ROWS, proj_rows)
    best = proj.get("best_transformer") or {}
    check("proj_best_available", proj.get("best_available") is True)
    check("proj_uses_ostn15", best.get("uses_ostn15_grid") is True)
    check("proj_no_ballpark", best.get("contains_ballpark") is False)
    check("proj_display_delta_sanity", proj.get("all_display_deltas_within_sanity_limit") is True)

    check("strict_schema_candidate_aware", int(strict.get("schema_version") or 0) >= 2)
    strict_rows = [int(value) for value in (strict.get("prepared_and_measured_rows") or [])]
    check("strict_rows_exact", strict_rows == EXPECTED_ROWS, strict_rows)
    check("strict_verified_count_12", int(strict.get("verified_count") or 0) == 12)
    check("strict_proj_candidate_aware", strict.get("proj_gate_candidate_aware") is True)
    check("strict_numeric_publish_gate", strict.get("numeric_publish_gate_passed") is True)
    check("strict_remote_readback_required", strict.get("remote_readback_required") is True)

    results = measurements.get("results")
    measured_rows = measurements.get("measured_rows")
    check("measurement_results_list", isinstance(results, list))
    check("measurement_measured_rows_list", isinstance(measured_rows, list))
    assert isinstance(results, list)
    assert isinstance(measured_rows, list)
    check("measurement_candidate_count_12", int(measurements.get("candidate_count") or 0) == 12)
    check("measurement_promoted_count_12", int(measurements.get("promoted_measurement_count") or 0) == 12)
    check("measurement_blocked_count_0", int(measurements.get("blocked_measurement_count") or 0) == 0)
    check("measurement_method", measurements.get("height_difference_definition") == "EA_DTM_polygon_95th_percentile_minus_5th_percentile")
    check("measurement_rows_exact", _rows(measured_rows) == EXPECTED_ROWS, _rows(measured_rows))
    check("result_rows_exact", _rows(results) == EXPECTED_ROWS, _rows(results))

    result_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    for item in results:
        row_no = int(item["row_no"])
        parcel_id = str(item.get("parcel_id") or "").strip()
        check(f"result_{row_no}_parcel_id", bool(parcel_id))
        check(f"result_{row_no}_status", item.get("status") == "MEASURED_AND_CROSSCHECKED")
        check(f"result_{row_no}_promoted", item.get("measured_value_promoted") is True)
        ea = item.get("ea_dtm") or {}
        os_data = item.get("os_terrain50") or {}
        ea_sources = ea.get("source_rasters") or []
        check(f"result_{row_no}_ea_source", bool(ea_sources))
        check(f"result_{row_no}_ea_hashes", all(str(src.get("sha256") or "").strip() for src in ea_sources))
        centroid_source = os_data.get("centroid_source") or {}
        check(f"result_{row_no}_terrain50_centroid_hash", bool(str(centroid_source.get("sha256") or "").strip()))
        result_by_key[(row_no, parcel_id)] = item

    measured_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    for item in measured_rows:
        row_no = int(item["row_no"])
        parcel_id = str(item.get("parcel_id") or "").strip()
        check(f"measured_{row_no}_parcel_id", bool(parcel_id))
        check(f"measured_{row_no}_method", item.get("height_difference_method") == METHOD)
        check(f"measured_{row_no}_confidence", item.get("confidence") in ALLOWED_CONFIDENCE)
        check(f"measured_{row_no}_ea_cells", int(item.get("ea_valid_cell_count") or 0) >= 4)
        check(
            f"measured_{row_no}_cross_source",
            _finite(item.get("cross_source_absolute_difference_m"), f"row {row_no} cross_source") <= 8.0,
        )
        height_difference = _finite(item.get("height_difference_m"), f"row {row_no} height_difference")
        check(f"measured_{row_no}_height_nonnegative", height_difference >= 0.0)
        _finite(item.get("elevation_median_m"), f"row {row_no} elevation_median")
        _finite(item.get("elevation_iqr_m"), f"row {row_no} elevation_iqr")
        _finite(item.get("os_terrain50_centroid_elevation_m"), f"row {row_no} terrain50_centroid")
        check(f"measured_{row_no}_result_key", (row_no, parcel_id) in result_by_key)
        measured_by_key[(row_no, parcel_id)] = item

    published_rows = verified.get("rows")
    check("verified_rows_list", isinstance(published_rows, list))
    assert isinstance(published_rows, list)
    check("verified_count_12", int(verified.get("published_example_count") or 0) == 12)
    check("verified_rows_exact", _rows(published_rows) == EXPECTED_ROWS, _rows(published_rows))
    for item in published_rows:
        row_no = int(item["row_no"])
        parcel_id = str(item.get("parcel_id") or "").strip()
        key = (row_no, parcel_id)
        check(f"verified_{row_no}_measured_key", key in measured_by_key)
        measured = measured_by_key[key]
        check(f"verified_{row_no}_method", item.get("height_difference_method") == METHOD)
        check(f"verified_{row_no}_confidence", item.get("confidence") in ALLOWED_CONFIDENCE)
        for field in (
            "height_difference_m",
            "elevation_median_m",
            "elevation_iqr_m",
            "os_terrain50_centroid_elevation_m",
            "cross_source_absolute_difference_m",
        ):
            lhs = _finite(item.get(field), f"verified row {row_no} {field}")
            rhs = _finite(measured.get(field), f"measured row {row_no} {field}")
            check(f"verified_{row_no}_{field}_matches", math.isclose(lhs, rhs, rel_tol=0.0, abs_tol=1e-9))

    features = geojson.get("features")
    check("geojson_feature_collection", geojson.get("type") == "FeatureCollection")
    check("geojson_features_list", isinstance(features, list))
    assert isinstance(features, list)
    check("geojson_feature_count_12", len(features) == 12)
    feature_rows: list[int] = []
    feature_ids: set[str] = set()
    for feature in features:
        properties = feature.get("properties") or {}
        row_no = int(properties["row_no"])
        feature_rows.append(row_no)
        feature_id = str(feature.get("id") or "")
        check(f"geojson_{row_no}_unique_id", bool(feature_id) and feature_id not in feature_ids)
        feature_ids.add(feature_id)
        geometry = feature.get("geometry") or {}
        check(f"geojson_{row_no}_polygon", geometry.get("type") in {"Polygon", "MultiPolygon"})
    check("geojson_rows_exact", feature_rows == EXPECTED_ROWS, feature_rows)

    file_sha256 = {name: _sha256(path) for name, path in paths.items()}
    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "purpose": "STRICT12_LOCAL_OUTPUT_ACCEPTANCE_BEFORE_REMOTE_GITHUB_READBACK",
        "expected_rows": EXPECTED_ROWS,
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "file_sha256": file_sha256,
        "local_acceptance_passed": True,
        "remote_github_readback_required": True,
        "numeric_values_changed_by_validator": 0,
        "final_ready": False,
        "fake_data": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "checks": len(checks), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

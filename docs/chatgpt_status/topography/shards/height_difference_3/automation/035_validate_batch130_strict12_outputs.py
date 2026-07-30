#!/usr/bin/env python3
"""Validate Strict12 outputs and atomically seal local acceptance evidence.

All input files are hash-stable during validation. The validator cross-binds the
PROJ gate, same-point measurement contract and transactional JSON/GeoJSON website
bundle. It never changes numeric values and remote GitHub readback remains required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

EXPECTED_ROWS = list(range(61540, 61552))
METHOD = "EA_DTM_1M_POLYGON_P95_MINUS_P05"
CONTRACT = "EA_DTM_POLYGON_P95_P05_OS_T50_SAME_POINT_V2"
ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM_HIGH"}


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise ValueError(f"required input is missing or empty: {path}")
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


def _valid_sha256(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text)


def _finite(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is invalid: {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} is non-finite: {value!r}")
    return number


def _rows(values: list[dict[str, Any]]) -> list[int]:
    return [int(item["row_no"]) for item in values]


def _exact_hmlr_method(value: Any) -> bool:
    return str(value or "").startswith("EXACT_OFFICIAL_ID")


def _write_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}_", suffix=".json.tmp", dir=path.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _source_list(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        raise ValueError(f"{label} must contain exactly one source raster")
    source = value[0]
    if not _valid_sha256(source.get("sha256")):
        raise ValueError(f"{label} source raster SHA-256 is missing")
    if not str(source.get("path") or "").strip():
        raise ValueError(f"{label} source raster path is missing")
    return value


def validate(strict_output_dir: Path, output: Path) -> dict[str, Any]:
    root = strict_output_dir.resolve()
    output = output.resolve()
    paths = {
        "proj": root / "00_proj_ostn15_gate.json",
        "measurements": root / "measurement" / "official_measurements.json",
        "verified_json": root / "measurement" / "verified_examples.json",
        "verified_geojson": root / "measurement" / "verified_examples.geojson",
        "strict_acceptance": root / "batch130_strict12_acceptance.json",
    }
    if output in paths.values():
        raise ValueError("acceptance output must differ from validated inputs")
    hashes_before = {name: _sha256(path) for name, path in paths.items()}
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
    check("proj_schema_v2", int(proj.get("schema_version") or 0) >= 2)
    check("proj_passed", proj.get("passed") is True)
    check("proj_candidate_rows_exact", proj_rows == EXPECTED_ROWS, proj_rows)
    check("proj_manifest_hash", _valid_sha256(proj.get("candidate_manifest_sha256")))
    check("proj_canonical_hash", _valid_sha256(proj.get("canonical_export_sha256")))
    check("proj_input_stable", proj.get("input_stability_verified") is True)
    check("proj_network_restored", proj.get("network_restored") is True)
    check("proj_atomic_evidence", proj.get("atomic_evidence_materialization") is True)
    best = proj.get("best_transformer") or {}
    check("proj_best_available", proj.get("best_available") is True)
    check("proj_uses_ostn15", best.get("uses_ostn15_grid") is True)
    check("proj_no_ballpark", best.get("contains_ballpark") is False)
    check("proj_all_finite", proj.get("all_finite") is True)
    check("proj_gb_bounds", proj.get("all_transformed_points_within_gb_bounds") is True)
    check("proj_display_delta", proj.get("all_display_deltas_within_sanity_limit") is True)

    strict_rows = [int(value) for value in (strict.get("prepared_and_measured_rows") or [])]
    check("strict_schema", int(strict.get("schema_version") or 0) >= 2)
    check("strict_rows_exact", strict_rows == EXPECTED_ROWS, strict_rows)
    check("strict_verified_count", int(strict.get("verified_count") or 0) == 12)
    check("strict_method", strict.get("method") == METHOD)
    check("strict_proj_candidate_aware", strict.get("proj_gate_candidate_aware") is True)
    check("strict_exact_hmlr", strict.get("exact_hmlr_official_id_gate") is True)
    check("strict_nearest_fill", strict.get("nearest_fill_forbidden") is True)
    check("strict_numeric_publish", strict.get("numeric_publish_gate_passed") is True)
    check("strict_remote_required", strict.get("remote_readback_required") is True)
    check("strict_not_final", strict.get("final_ready") is False)

    results = measurements.get("results")
    measured_rows = measurements.get("measured_rows")
    check("measurement_schema_v2", int(measurements.get("schema_version") or 0) >= 2)
    check("measurement_contract", measurements.get("measurement_contract_version") == CONTRACT)
    check("measurement_target_crs", measurements.get("target_crs") == "EPSG:27700")
    check("measurement_atomic", measurements.get("atomic_output_materialization") is True)
    check("measurement_unique_ea", measurements.get("unique_ea_coverage_required") is True)
    check("measurement_unique_os", measurements.get("unique_terrain50_tile_required") is True)
    check("measurement_errors_block", measurements.get("source_errors_forbid_promotion") is True)
    check("measurement_strict_crs", measurements.get("strict_crs_resolution_gate") is True)
    check("measurement_match_hash", _valid_sha256(measurements.get("matched_manifest_sha256")))
    check("measurement_results_list", isinstance(results, list))
    check("measurement_rows_list", isinstance(measured_rows, list))
    if not isinstance(results, list) or not isinstance(measured_rows, list):
        raise ValueError("measurement arrays are invalid")
    check("measurement_candidate_count", int(measurements.get("candidate_count") or 0) == 12)
    check("measurement_promoted_count", int(measurements.get("promoted_measurement_count") or 0) == 12)
    check("measurement_blocked_count", int(measurements.get("blocked_measurement_count", -1)) == 0)
    check("measurement_definition", measurements.get("height_difference_definition") == "EA_DTM_polygon_95th_percentile_minus_5th_percentile")
    check("measurement_rows_exact", _rows(measured_rows) == EXPECTED_ROWS, _rows(measured_rows))
    check("result_rows_exact", _rows(results) == EXPECTED_ROWS, _rows(results))

    result_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    for item in results:
        row_no = int(item["row_no"])
        parcel_id = str(item.get("parcel_id") or "").strip()
        key = (row_no, parcel_id)
        check(f"result_{row_no}_unique_key", bool(parcel_id) and key not in result_by_key)
        check(f"result_{row_no}_status", item.get("status") == "MEASURED_AND_CROSSCHECKED")
        check(f"result_{row_no}_promoted", item.get("measured_value_promoted") is True)
        check(f"result_{row_no}_gate_reasons", item.get("gate_reasons") in ([], None))
        check(f"result_{row_no}_measurement_errors", item.get("measurement_errors") in ([], None))
        check(f"result_{row_no}_exact_hmlr", _exact_hmlr_method(item.get("hmlr_match_method")), item.get("hmlr_match_method"))
        check(f"result_{row_no}_no_nearest", item.get("nearest_point_fill_used") is False)
        ea = item.get("ea_dtm") or {}
        os_data = item.get("os_terrain50") or {}
        _source_list(ea.get("source_rasters"), f"row {row_no} EA")
        _source_list(os_data.get("source_rasters"), f"row {row_no} Terrain50")
        check(f"result_{row_no}_ea_errors", ea.get("errors") in ([], None))
        check(f"result_{row_no}_os_errors", os_data.get("errors") in ([], None))
        same_point = _finite(item.get("cross_source_same_point_absolute_difference_m"), f"row {row_no} same-point difference")
        threshold = _finite(item.get("crosscheck_threshold_m"), f"row {row_no} threshold")
        check(f"result_{row_no}_same_point_threshold", 0 <= same_point <= threshold <= 8.0)
        result_by_key[key] = item

    measured_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    for item in measured_rows:
        row_no = int(item["row_no"])
        parcel_id = str(item.get("parcel_id") or "").strip()
        key = (row_no, parcel_id)
        check(f"measured_{row_no}_unique_key", bool(parcel_id) and key not in measured_by_key)
        check(f"measured_{row_no}_result_key", key in result_by_key)
        check(f"measured_{row_no}_method", item.get("height_difference_method") == METHOD)
        check(f"measured_{row_no}_confidence", item.get("confidence") in ALLOWED_CONFIDENCE)
        check(f"measured_{row_no}_exact_hmlr", _exact_hmlr_method(item.get("boundary_match_method")), item.get("boundary_match_method"))
        check(f"measured_{row_no}_data_status", item.get("data_status") == "official_sources_crosschecked_same_point")
        check(f"measured_{row_no}_ea_cells", int(item.get("ea_valid_cell_count") or 0) >= 4)
        height = _finite(item.get("height_difference_m"), f"row {row_no} height")
        check(f"measured_{row_no}_height", height >= 0)
        _finite(item.get("elevation_median_m"), f"row {row_no} median")
        _finite(item.get("elevation_iqr_m"), f"row {row_no} iqr")
        ea_point = _finite(item.get("ea_sample_point_elevation_m"), f"row {row_no} EA point")
        os_point = _finite(item.get("os_terrain50_sample_point_elevation_m"), f"row {row_no} OS point")
        cross = _finite(item.get("cross_source_same_point_absolute_difference_m"), f"row {row_no} cross")
        check(f"measured_{row_no}_cross_arithmetic", math.isclose(abs(ea_point-os_point), cross, rel_tol=0, abs_tol=0.002))
        check(f"measured_{row_no}_cross_threshold", cross <= 8.0)
        measured_by_key[key] = item

    measurement_sha = hashes_before["measurements"]
    published_rows = verified.get("rows")
    check("verified_schema_v2", int(verified.get("schema_version") or 0) >= 2)
    check("verified_status", verified.get("status") == "VERIFIED_EXAMPLES_PUBLISHED")
    check("verified_atomic_bundle", verified.get("atomic_json_geojson_bundle") is True)
    check("verified_measurement_hash", verified.get("measurement_manifest_sha256") == measurement_sha)
    check("verified_rows_list", isinstance(published_rows, list))
    if not isinstance(published_rows, list):
        raise ValueError("verified rows are invalid")
    check("verified_count", int(verified.get("published_example_count") or 0) == 12)
    check("verified_rows_exact", _rows(published_rows) == EXPECTED_ROWS, _rows(published_rows))
    verified_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    compare_fields = (
        "height_difference_m", "elevation_median_m", "elevation_iqr_m",
        "ea_sample_point_elevation_m", "os_terrain50_sample_point_elevation_m",
        "cross_source_same_point_absolute_difference_m",
    )
    for item in published_rows:
        row_no = int(item["row_no"])
        parcel_id = str(item.get("parcel_id") or "").strip()
        key = (row_no, parcel_id)
        check(f"verified_{row_no}_unique_key", bool(parcel_id) and key not in verified_by_key)
        check(f"verified_{row_no}_measured_key", key in measured_by_key)
        measured = measured_by_key[key]
        check(f"verified_{row_no}_method", item.get("height_difference_method") == METHOD)
        check(f"verified_{row_no}_confidence", item.get("confidence") in ALLOWED_CONFIDENCE)
        check(f"verified_{row_no}_exact_hmlr", _exact_hmlr_method(item.get("boundary_match_method")), item.get("boundary_match_method"))
        check(f"verified_{row_no}_data_status", item.get("data_status") == "official_sources_crosschecked_same_point")
        for field in compare_fields:
            lhs = _finite(item.get(field), f"verified row {row_no} {field}")
            rhs = _finite(measured.get(field), f"measured row {row_no} {field}")
            check(f"verified_{row_no}_{field}", math.isclose(lhs, rhs, rel_tol=0, abs_tol=1e-9))
        verified_by_key[key] = item

    features = geojson.get("features")
    check("geojson_feature_collection", geojson.get("type") == "FeatureCollection")
    check("geojson_atomic_bundle", geojson.get("atomic_json_geojson_bundle") is True)
    check("geojson_measurement_hash", geojson.get("measurement_manifest_sha256") == measurement_sha)
    check("geojson_features_list", isinstance(features, list))
    if not isinstance(features, list):
        raise ValueError("GeoJSON features are invalid")
    check("geojson_feature_count", int(geojson.get("feature_count") or 0) == 12 and len(features) == 12)
    feature_rows: list[int] = []
    feature_ids: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError("GeoJSON feature is not an object")
        properties = feature.get("properties") or {}
        row_no = int(properties["row_no"])
        parcel_id = str(properties.get("parcel_id") or "").strip()
        key = (row_no, parcel_id)
        feature_rows.append(row_no)
        feature_id = str(feature.get("id") or "").strip()
        check(f"geojson_{row_no}_id", feature_id == parcel_id and feature_id not in feature_ids)
        feature_ids.add(feature_id)
        check(f"geojson_{row_no}_verified_key", key in verified_by_key)
        check(f"geojson_{row_no}_properties", properties == verified_by_key[key])
        geometry = feature.get("geometry") or {}
        check(f"geojson_{row_no}_geometry", geometry.get("type") in {"Polygon", "MultiPolygon"})
    check("geojson_rows_exact", feature_rows == EXPECTED_ROWS, feature_rows)

    hashes_after = {name: _sha256(path) for name, path in paths.items()}
    check("input_files_hash_stable", hashes_before == hashes_after)
    payload = {
        "schema_version": 3,
        "slot_id": "height_difference_3",
        "purpose": "STRICT12_LOCAL_OUTPUT_ACCEPTANCE_BEFORE_REMOTE_GITHUB_READBACK",
        "expected_rows": EXPECTED_ROWS,
        "checks_passed": len(checks),
        "checks_total": len(checks),
        "checks": checks,
        "file_sha256": hashes_after,
        "inputs_hash_stable": True,
        "measurement_contract_version": CONTRACT,
        "same_point_crosscheck_required": True,
        "exact_hmlr_official_id_required": True,
        "nearest_fill_forbidden": True,
        "atomic_acceptance_materialization": True,
        "local_acceptance_passed": True,
        "remote_github_readback_required": True,
        "numeric_values_changed_by_validator": 0,
        "final_ready": False,
        "fake_data": False,
    }
    _write_atomic(output, payload)
    return payload


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict-output-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args(argv)
    payload = validate(args.strict_output_dir, args.output)
    print(json.dumps({"ok": True, "checks": payload["checks_total"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

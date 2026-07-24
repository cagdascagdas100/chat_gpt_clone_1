#!/usr/bin/env python3
"""Validate completed height_difference_3 pipeline stages and build a fail-closed resume plan.

This module never creates a runner, queue item, lease, parcel measurement or web result.
A stage is reusable only when its files, hashes, row identities and source contracts still validate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROW_START = 61523
ROW_END = 92283
SHARD_COUNT = 30761
CANONICAL_COUNT = 92283
FIRST_ROWS = [61523, 61524, 61525]
ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM_HIGH"}


class ValidationError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise ValidationError(f"missing file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    if not path.is_file():
        raise ValidationError(f"missing file: {path}")
    digest = hashlib.md5()  # nosec - verifies an official metadata field, not authentication
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"missing JSON: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise ValidationError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValidationError(f"JSON object required: {path}")
    return payload


def resolve_recorded_path(value: Any, base: Path) -> Path:
    text = str(value or "").strip()
    if not text:
        raise ValidationError("recorded path is empty")
    path = Path(text)
    return path if path.is_absolute() else (base / path).resolve()


def require_number(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"invalid numeric {field}={value!r}") from exc
    if not math.isfinite(number):
        raise ValidationError(f"non-finite numeric {field}={value!r}")
    return number


def validate_jsonl_registry(path: Path) -> dict[str, Any]:
    count = 0
    first_rows: list[int] = []
    last_row = None
    seen_parcels: set[str] = set()
    seen_inspire: set[str] = set()
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception as exc:
                raise ValidationError(f"invalid JSONL line {line_no}: {exc}") from exc
            row_no = int(row.get("row_no"))
            expected = ROW_START + count
            if row_no != expected:
                raise ValidationError(f"non-contiguous row registry at line {line_no}: {row_no} != {expected}")
            parcel_id = str(row.get("parcel_id") or "").strip()
            inspire_id = str(row.get("hmlr_inspire_id") or "").strip()
            if not parcel_id or not inspire_id:
                raise ValidationError(f"row {row_no} lacks parcel_id or hmlr_inspire_id")
            if parcel_id in seen_parcels or inspire_id in seen_inspire:
                raise ValidationError(f"duplicate parcel or HMLR identity at row {row_no}")
            seen_parcels.add(parcel_id)
            seen_inspire.add(inspire_id)
            require_number(row.get("bng_easting"), "bng_easting")
            require_number(row.get("bng_northing"), "bng_northing")
            if len(first_rows) < 3:
                first_rows.append(row_no)
            last_row = row_no
            count += 1
    if count != SHARD_COUNT or first_rows != FIRST_ROWS or last_row != ROW_END:
        raise ValidationError(
            f"shard registry mismatch count={count} first={first_rows} last={last_row}"
        )
    return {
        "row_count": count,
        "first_rows": first_rows,
        "last_row": last_row,
        "unique_parcel_ids": len(seen_parcels),
        "unique_hmlr_ids": len(seen_inspire),
        "sha256": sha256_file(path),
    }


def candidate_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    values = payload.get("candidates")
    if not isinstance(values, list) or len(values) != 3:
        raise ValidationError("exactly three starter candidates required")
    rows = [dict(value) for value in values if isinstance(value, dict)]
    if len(rows) != 3 or [int(row.get("row_no")) for row in rows] != FIRST_ROWS:
        raise ValidationError("starter candidates must be explicit rows 61523,61524,61525")
    for row in rows:
        if not str(row.get("parcel_id") or "").strip() or not str(row.get("hmlr_inspire_id") or "").strip():
            raise ValidationError("starter candidate lacks canonical identity")
        require_number(row.get("bng_easting"), "bng_easting")
        require_number(row.get("bng_northing"), "bng_northing")
    return rows


def validate_canonical(root: Path, security_geojson: Path) -> dict[str, Any]:
    canonical = root / "canonical"
    manifest = load_json(canonical / "stream_extraction_manifest.json")
    shard = canonical / "canonical_shard_61523_92283.jsonl"
    registry = validate_jsonl_registry(shard)
    starter = load_json(canonical / "starter_three_query_manifest.json")
    candidates = candidate_rows(starter)
    if int(manifest.get("canonical_features_validated", -1)) != CANONICAL_COUNT:
        raise ValidationError("canonical feature count is not 92283")
    if int(manifest.get("shard_rows_exported", -1)) != SHARD_COUNT:
        raise ValidationError("canonical manifest shard count is not 30761")
    if list(manifest.get("first_three_explicit_rows") or []) != FIRST_ROWS:
        raise ValidationError("canonical manifest first rows mismatch")
    source_hash = sha256_file(security_geojson)
    if str(manifest.get("source_sha256") or "").lower() != source_hash.lower():
        raise ValidationError("canonical source SHA256 changed")
    return {
        "manifest": str(canonical / "stream_extraction_manifest.json"),
        "shard": str(shard),
        "starter": str(canonical / "starter_three_query_manifest.json"),
        "source_sha256": source_hash,
        "registry": registry,
        "candidate_rows": [int(row["row_no"]) for row in candidates],
    }


def validate_hmlr_sources(root: Path) -> dict[str, Any]:
    manifest_path = root / "sources" / "hmlr_source_manifest.json"
    payload = load_json(manifest_path)
    if payload.get("status") != "READY" or int(payload.get("candidate_count", -1)) != 3:
        raise ValidationError("HMLR source manifest is not READY for three candidates")
    if payload.get("blocked"):
        raise ValidationError("HMLR source manifest contains blocked authorities")
    records = payload.get("records")
    if not isinstance(records, list) or len(records) != int(payload.get("authority_count", -1)):
        raise ValidationError("HMLR authority records are incomplete")
    vector_count = 0
    for record in records:
        vectors = record.get("vectors") if isinstance(record, dict) else None
        if not isinstance(vectors, list) or not vectors:
            raise ValidationError("HMLR authority has no vector evidence")
        for vector in vectors:
            path = resolve_recorded_path(vector.get("path"), Path.cwd())
            if sha256_file(path).lower() != str(vector.get("sha256") or "").lower():
                raise ValidationError(f"HMLR vector SHA256 mismatch: {path}")
            vector_count += 1
    return {"manifest": str(manifest_path), "authority_count": len(records), "vector_count": vector_count}


def validate_terrain_areas(root: Path, starter_rows: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_path = root / "sources" / "os_terrain50_areas" / "terrain50_required_areas_manifest.json"
    payload = load_json(manifest_path)
    if payload.get("product_id") != "Terrain50" or not str(payload.get("product_version") or "").endswith("-07"):
        raise ValidationError("Terrain50 product/version contract failed")
    if int(payload.get("candidate_count", -1)) != 3 or payload.get("only_required_areas_downloaded") is not True:
        raise ValidationError("Terrain50 targeted acquisition contract failed")
    area_map = payload.get("candidate_area_map")
    if not isinstance(area_map, list) or sorted(int(value["row_no"]) for value in area_map) != FIRST_ROWS:
        raise ValidationError("Terrain50 candidate area map mismatch")
    archives = payload.get("archives")
    required = sorted(str(value) for value in (payload.get("required_100km_areas") or []))
    if not isinstance(archives, list) or sorted(str(value.get("area")) for value in archives) != required:
        raise ValidationError("Terrain50 archive area set mismatch")
    expected_rows = sorted(int(row["row_no"]) for row in starter_rows)
    if expected_rows != FIRST_ROWS:
        raise ValidationError("starter rows changed before Terrain50 validation")
    for record in archives:
        path = resolve_recorded_path(record.get("archive_path"), Path.cwd())
        if sha256_file(path).lower() != str(record.get("archive_sha256") or "").lower():
            raise ValidationError(f"Terrain50 SHA256 mismatch: {path}")
        expected_md5 = str(record.get("archive_md5") or "").lower()
        if expected_md5 and md5_file(path).lower() != expected_md5:
            raise ValidationError(f"Terrain50 MD5 mismatch: {path}")
        if int(record.get("ascii_headers_validated", 0)) <= 0:
            raise ValidationError("Terrain50 archive lacks validated ASCII headers")
    return {"manifest": str(manifest_path), "required_areas": required, "archive_count": len(archives)}


def validate_matches(root: Path) -> dict[str, Any]:
    path = root / "hmlr_matches.json"
    payload = load_json(path)
    results = payload.get("results")
    if not isinstance(results, list) or len(results) != 3:
        raise ValidationError("HMLR match result count is not three")
    rows = []
    source_hashes = []
    for result in results:
        row_no = int(result.get("row_no"))
        rows.append(row_no)
        if result.get("status") != "MATCHED" or not isinstance(result.get("match"), dict):
            raise ValidationError(f"row {row_no} is not uniquely HMLR matched")
        match = result["match"]
        if not str(match.get("geometry_wkt_epsg27700") or "").strip():
            raise ValidationError(f"row {row_no} lacks matched EPSG:27700 geometry")
        if result.get("nearest_polygon_fill_used") is not False:
            raise ValidationError("nearest polygon fill flag is not false")
    if sorted(rows) != FIRST_ROWS or int(payload.get("matched_candidate_count", -1)) != 3:
        raise ValidationError("HMLR matched row registry mismatch")
    for source in payload.get("source_files") or []:
        source_path = resolve_recorded_path(source.get("path"), Path.cwd())
        current = sha256_file(source_path)
        if current.lower() != str(source.get("sha256") or "").lower():
            raise ValidationError(f"HMLR matched source changed: {source_path}")
        source_hashes.append(current)
    return {"manifest": str(path), "rows": sorted(rows), "source_hashes": source_hashes}


def validate_ea_sources(root: Path) -> dict[str, Any]:
    ea_path = root / "sources" / "ea_dtm_source_manifest.json"
    ea = load_json(ea_path)
    if ea.get("status") != "READY" or int(ea.get("candidate_count", -1)) != 3:
        raise ValidationError("EA source manifest is not READY for three candidates")
    records = ea.get("records") or []
    if len(records) != 3:
        raise ValidationError("EA source manifest does not contain three rasters")
    for record in records:
        path = resolve_recorded_path(record.get("path"), Path.cwd())
        if sha256_file(path).lower() != str(record.get("sha256") or "").lower():
            raise ValidationError(f"EA raster SHA256 mismatch: {path}")
        if "27700" not in str(record.get("crs") or ""):
            raise ValidationError("EA raster CRS is not EPSG:27700")
        resolution = record.get("resolution_m") or []
        if len(resolution) != 2 or max(require_number(value, "EA resolution") for value in resolution) > 1.1:
            raise ValidationError("EA raster resolution gate failed")
    return {"manifest": str(ea_path), "ea_rasters": len(records)}


def validate_terrain_tiles(root: Path) -> dict[str, Any]:
    os_path = root / "sources" / "terrain50_source_manifest.json"
    terrain = load_json(os_path)
    if terrain.get("status") != "READY" or int(terrain.get("candidate_count", -1)) != 3:
        raise ValidationError("Terrain50 source manifest is not READY for three candidates")
    records = terrain.get("records") or []
    if not records:
        raise ValidationError("Terrain50 source manifest contains no exact tiles")
    for record in records:
        path = resolve_recorded_path(record.get("path"), Path.cwd())
        if sha256_file(path).lower() != str(record.get("sha256") or "").lower():
            raise ValidationError(f"Terrain50 tile SHA256 mismatch: {path}")
        header = record.get("header") or {}
        if int(header.get("ncols", -1)) != 200 or int(header.get("nrows", -1)) != 200:
            raise ValidationError("Terrain50 tile dimension gate failed")
        if abs(require_number(header.get("cellsize"), "Terrain50 cellsize") - 50.0) > 1e-9:
            raise ValidationError("Terrain50 cell-size gate failed")
    return {"manifest": str(os_path), "terrain50_tiles": len(records)}


def validate_measurements(root: Path) -> dict[str, Any]:
    path = root / "official_measurements.json"
    payload = load_json(path)
    if int(payload.get("candidate_count", -1)) != 3 or int(payload.get("promoted_measurement_count", -1)) != 3:
        raise ValidationError("three promoted official measurements required")
    rows = payload.get("measured_rows")
    if not isinstance(rows, list) or sorted(int(row["row_no"]) for row in rows) != FIRST_ROWS:
        raise ValidationError("promoted measurement row registry mismatch")
    for row in rows:
        if row.get("confidence") not in ALLOWED_CONFIDENCE:
            raise ValidationError("measurement confidence is not publishable")
        if row.get("height_difference_method") != "EA_DTM_1M_POLYGON_P95_MINUS_P05":
            raise ValidationError("measurement method mismatch")
        for field in (
            "height_difference_m", "elevation_median_m", "elevation_iqr_m",
            "os_terrain50_centroid_elevation_m", "cross_source_absolute_difference_m",
        ):
            require_number(row.get(field), field)
    return {"manifest": str(path), "rows": FIRST_ROWS, "sha256": sha256_file(path)}


def validate_publication(root: Path) -> dict[str, Any]:
    json_path = root / "verified_examples.json"
    geojson_path = root / "verified_examples.geojson"
    summary = load_json(json_path)
    geojson = load_json(geojson_path)
    if summary.get("status") != "VERIFIED_EXAMPLES_PUBLISHED" or int(summary.get("published_example_count", -1)) != 3:
        raise ValidationError("verified JSON publication is incomplete")
    rows = summary.get("rows")
    features = geojson.get("features")
    if not isinstance(rows, list) or not isinstance(features, list) or len(rows) != 3 or len(features) != 3:
        raise ValidationError("verified JSON/GeoJSON row counts are not three")
    if sorted(int(row["row_no"]) for row in rows) != FIRST_ROWS:
        raise ValidationError("published row registry mismatch")
    for feature in features:
        geometry = feature.get("geometry") if isinstance(feature, dict) else None
        if not isinstance(geometry, dict) or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValidationError("published feature lacks parcel polygon")
    return {
        "json": str(json_path),
        "geojson": str(geojson_path),
        "json_sha256": sha256_file(json_path),
        "geojson_sha256": sha256_file(geojson_path),
        "published_rows": FIRST_ROWS,
    }


@dataclass(frozen=True)
class Stage:
    name: str
    validator: Callable[[], dict[str, Any]]


def build_plan(output_dir: Path, security_geojson: Path) -> dict[str, Any]:
    root = output_dir.resolve()
    source = security_geojson.resolve()
    starter_cache: dict[str, Any] = {}

    def canonical() -> dict[str, Any]:
        evidence = validate_canonical(root, source)
        starter_cache["rows"] = candidate_rows(load_json(root / "canonical" / "starter_three_query_manifest.json"))
        return evidence

    def terrain() -> dict[str, Any]:
        rows = starter_cache.get("rows")
        if rows is None:
            rows = candidate_rows(load_json(root / "canonical" / "starter_three_query_manifest.json"))
        return validate_terrain_areas(root, rows)

    stages = [
        Stage("CANONICAL_STREAM_EXTRACT_AND_PREPARE_THREE", canonical),
        Stage("HMLR_SOURCE_PREPARATION", lambda: validate_hmlr_sources(root)),
        Stage("TERRAIN50_REQUIRED_AREA_ACQUISITION", terrain),
        Stage("HMLR_BOUNDARY_MATCH", lambda: validate_matches(root)),
        Stage("EA_DTM_WCS_PREPARATION", lambda: validate_ea_sources(root)),
        Stage("TERRAIN50_EXACT_TILE_PREPARATION", lambda: validate_terrain_tiles(root)),
        Stage("EA_DTM_AND_TERRAIN50_SAMPLE", lambda: validate_measurements(root)),
        Stage("VERIFIED_WEBSITE_PUBLICATION", lambda: validate_publication(root)),
    ]
    results = []
    first_invalid = None
    dependency_valid = True
    for stage in stages:
        if not dependency_valid:
            results.append({"stage": stage.name, "valid": False, "reusable": False, "reason": "UPSTREAM_STAGE_INVALID"})
            continue
        try:
            evidence = stage.validator()
        except Exception as exc:
            dependency_valid = False
            first_invalid = first_invalid or stage.name
            results.append({"stage": stage.name, "valid": False, "reusable": False, "reason": f"{type(exc).__name__}: {exc}"})
        else:
            results.append({"stage": stage.name, "valid": True, "reusable": True, "evidence": evidence})
    return {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "security_geojson": str(source),
        "output_dir": str(root),
        "first_invalid_stage": first_invalid,
        "all_stages_valid": first_invalid is None,
        "stages": results,
        "new_runner_created": False,
        "parallel_runner_used": False,
        "queue_submission": False,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--security-geojson", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--plan-output", type=Path)
    args = parser.parse_args()
    plan = build_plan(args.output_dir, args.security_geojson)
    output = args.plan_output or args.output_dir / "resume_validation_latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": plan["all_stages_valid"], "first_invalid_stage": plan["first_invalid_stage"], "plan": str(output)}))
    return 0 if plan["all_stages_valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

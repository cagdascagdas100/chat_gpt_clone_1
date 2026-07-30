#!/usr/bin/env python3
"""Publish only fully gated height_difference_3 rows as one atomic JSON/GeoJSON bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable

ROW_START = 61523
ROW_END = 92283
ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM_HIGH"}
ALLOWED_METHOD = "EA_DTM_1M_POLYGON_P95_MINUS_P05"


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("measurement manifest must be a JSON object")
    return payload


def _valid_number(value: Any, *, minimum: float | None = None) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite numeric value: {value!r}")
    if minimum is not None and number < minimum:
        raise ValueError(f"numeric value below minimum {minimum}: {value!r}")
    return number


def _validate_coordinates(value: Any) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError("GeoJSON coordinates must be a non-empty array")
    first = value[0]
    if isinstance(first, (int, float)):
        if len(value) < 2:
            raise ValueError("GeoJSON position lacks longitude/latitude")
        lon = _valid_number(value[0])
        lat = _valid_number(value[1])
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"GeoJSON coordinate outside WGS84 bounds: {(lon, lat)}")
        return
    for child in value:
        _validate_coordinates(child)


def _validate_geometry(geometry: Any, row_no: int) -> dict[str, Any]:
    if not isinstance(geometry, dict):
        raise ValueError(f"row {row_no} lacks display polygon geometry")
    if geometry.get("type") not in {"Polygon", "MultiPolygon"}:
        raise ValueError(f"row {row_no} has unsupported display geometry")
    _validate_coordinates(geometry.get("coordinates"))
    return geometry


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _stage_bytes(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}_", suffix=".publish.tmp", dir=path.parent
    )
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        return temp
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        temp.unlink(missing_ok=True)
        raise


def _transactional_replace_bundle(staged: list[tuple[Path, Path]]) -> None:
    destinations = [destination.resolve() for _, destination in staged]
    if len(destinations) != len(set(destinations)):
        raise ValueError("output JSON and GeoJSON paths must be distinct")
    backups: list[tuple[Path, Path]] = []
    published: list[Path] = []
    try:
        for _, destination in staged:
            if destination.exists():
                backup = destination.with_name(f".{destination.name}.publish.bak")
                if backup.exists():
                    raise FileExistsError(f"stale publication backup exists: {backup}")
                destination.replace(backup)
                backups.append((destination, backup))
        for temp, destination in staged:
            temp.replace(destination)
            published.append(destination)
    except Exception:
        for destination in reversed(published):
            destination.unlink(missing_ok=True)
        for destination, backup in reversed(backups):
            if backup.exists():
                backup.replace(destination)
        raise
    else:
        for _, backup in backups:
            backup.unlink(missing_ok=True)
    finally:
        for temp, _ in staged:
            temp.unlink(missing_ok=True)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurement-manifest", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-geojson", type=Path, required=True)
    args = parser.parse_args(argv)

    manifest_path = args.measurement_manifest.resolve()
    manifest = _load(manifest_path)
    if manifest.get("slot_id") != "height_difference_3":
        raise ValueError("measurement manifest slot_id mismatch")
    if manifest.get("measurement_contract_version") != (
        "EA_DTM_POLYGON_P95_P05_OS_T50_SAME_POINT_V2"
    ):
        raise ValueError("unsupported measurement contract version")
    measured_rows = manifest.get("measured_rows")
    results = manifest.get("results")
    if not isinstance(measured_rows, list) or not isinstance(results, list):
        raise ValueError("measurement manifest lacks measured_rows/results lists")
    if int(manifest.get("promoted_measurement_count", -1)) != len(measured_rows):
        raise ValueError("promoted_measurement_count does not match measured_rows")
    if int(manifest.get("candidate_count", -1)) != len(results):
        raise ValueError("candidate_count does not match results")

    result_by_key: dict[tuple[int, str], dict[str, Any]] = {}
    for raw in results:
        if not isinstance(raw, dict):
            raise ValueError("measurement result is not an object")
        key = (int(raw["row_no"]), str(raw["parcel_id"]).strip())
        if key in result_by_key:
            raise ValueError(f"duplicate measurement result key: {key}")
        result_by_key[key] = raw

    threshold = _valid_number(manifest["max_crosscheck_difference_m"], minimum=0.0)
    published_rows: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []
    seen_rows: set[int] = set()
    seen_parcels: set[str] = set()

    for source in measured_rows:
        if not isinstance(source, dict):
            raise ValueError("measured row is not an object")
        row = dict(source)
        row_no = int(row["row_no"])
        parcel_id = str(row["parcel_id"]).strip()
        if not parcel_id:
            raise ValueError(f"row {row_no} has empty parcel_id")
        if not ROW_START <= row_no <= ROW_END:
            raise ValueError(f"row_no {row_no} outside shard")
        if row_no in seen_rows or parcel_id in seen_parcels:
            raise ValueError("duplicate row_no or parcel_id")
        seen_rows.add(row_no)
        seen_parcels.add(parcel_id)
        if row.get("height_difference_method") != ALLOWED_METHOD:
            raise ValueError(f"unsupported method for row {row_no}")
        if row.get("confidence") not in ALLOWED_CONFIDENCE:
            raise ValueError(f"unapproved confidence for row {row_no}")

        detail = result_by_key.get((row_no, parcel_id))
        if not detail or detail.get("status") != "MEASURED_AND_CROSSCHECKED":
            raise ValueError(f"row {row_no} lacks promoted result evidence")
        if detail.get("measured_value_promoted") is not True:
            raise ValueError(f"row {row_no} detail is not explicitly promoted")
        if detail.get("gate_reasons") not in ([], None):
            raise ValueError(f"row {row_no} has non-empty gate reasons")
        if detail.get("measurement_errors") not in ([], None):
            raise ValueError(f"row {row_no} has measurement errors")
        if detail.get("confidence") != row.get("confidence"):
            raise ValueError(f"row {row_no} confidence mismatch")

        geometry = _validate_geometry(
            row.get("geometry_geojson_epsg4326_display_only"), row_no
        )
        height_difference = _valid_number(row["height_difference_m"], minimum=0.0)
        elevation_median = _valid_number(row["elevation_median_m"])
        elevation_iqr = _valid_number(row["elevation_iqr_m"], minimum=0.0)
        ea_point = _valid_number(row["ea_sample_point_elevation_m"])
        os_point = _valid_number(row["os_terrain50_sample_point_elevation_m"])
        cross_difference = _valid_number(
            row["cross_source_same_point_absolute_difference_m"], minimum=0.0
        )
        if abs(abs(ea_point - os_point) - cross_difference) > 0.002:
            raise ValueError(f"row {row_no} cross-source difference mismatch")
        if cross_difference > threshold:
            raise ValueError(f"row {row_no} exceeds cross-source threshold")
        ea_count = int(row["ea_valid_cell_count"])
        if ea_count < int(manifest.get("minimum_ea_cells", 4)):
            raise ValueError(f"row {row_no} has insufficient EA cell count")

        properties = {
            "row_no": row_no,
            "parcel_id": parcel_id,
            "height_difference_m": round(height_difference, 3),
            "height_difference_method": ALLOWED_METHOD,
            "elevation_median_m": round(elevation_median, 3),
            "elevation_iqr_m": round(elevation_iqr, 3),
            "ea_valid_cell_count": ea_count,
            "ea_sample_point_elevation_m": round(ea_point, 3),
            "os_terrain50_sample_point_elevation_m": round(os_point, 3),
            "cross_source_same_point_absolute_difference_m": round(
                cross_difference, 3
            ),
            # Compatibility aliases retained for current website readers.
            "os_terrain50_centroid_elevation_m": round(os_point, 3),
            "cross_source_absolute_difference_m": round(cross_difference, 3),
            "boundary_match_method": row.get("boundary_match_method"),
            "confidence": row["confidence"],
            "data_status": "official_sources_crosschecked_same_point",
            "final_ready": False,
        }
        published_rows.append(properties)
        features.append(
            {
                "type": "Feature",
                "id": parcel_id,
                "geometry": geometry,
                "properties": properties,
            }
        )

    status = (
        "VERIFIED_EXAMPLES_PUBLISHED"
        if published_rows
        else "BLOCKED_NO_VERIFIED_MEASUREMENTS"
    )
    manifest_sha = _sha256(manifest_path)
    summary = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "parcel_partition": {
            "start": ROW_START,
            "end": ROW_END,
            "count": ROW_END - ROW_START + 1,
        },
        "status": status,
        "published_example_count": len(published_rows),
        "rows": published_rows,
        "measurement_manifest": str(manifest_path),
        "measurement_manifest_sha256": manifest_sha,
        "measurement_contract_version": manifest.get(
            "measurement_contract_version"
        ),
        "publication_gate": {
            "official_boundary_required": True,
            "ea_polygon_sample_required": True,
            "same_point_ea_os_crosscheck_required": True,
            "source_errors_forbid_publication": True,
            "allowed_confidence": sorted(ALLOWED_CONFIDENCE),
            "nearest_fill_forbidden": True,
        },
        "atomic_json_geojson_bundle": True,
        "overall_product_final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    geojson = {
        "type": "FeatureCollection",
        "name": "height_difference_3_verified_examples",
        "crs_note": "geometry is WGS84 display-only; calculations used EPSG:27700",
        "measurement_manifest_sha256": manifest_sha,
        "feature_count": len(features),
        "features": features,
        "atomic_json_geojson_bundle": True,
        "final_ready": False,
        "fake_data": False,
    }

    json_path = args.output_json.resolve()
    geojson_path = args.output_geojson.resolve()
    staged = [
        (_stage_bytes(json_path, _json_bytes(summary)), json_path),
        (_stage_bytes(geojson_path, _json_bytes(geojson)), geojson_path),
    ]
    _transactional_replace_bundle(staged)
    print(
        json.dumps(
            {
                "ok": bool(published_rows),
                "published": len(published_rows),
                "status": status,
                "json_sha256": _sha256(json_path),
                "geojson_sha256": _sha256(geojson_path),
            }
        )
    )
    return 0 if published_rows else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}),
            file=__import__("sys").stderr,
        )
        raise

#!/usr/bin/env python3
"""Extract the canonical height_difference_3 shard from the 92,283-row program matrix.

The source is the committed program-layer security GeoJSON because it carries the
complete canonical row registry and source-backed HMLR identifiers/coordinates.
No parcel identity is inferred from feature order.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    from pyproj import Transformer
except ImportError as exc:
    raise SystemExit(f"Required dependency is missing: {exc}")

CANONICAL_COUNT = 92283
ROW_START = 61523
ROW_END = 92283
SHARD_COUNT = 30761
TARGET_CRS = "EPSG:27700"
SOURCE_CRS = "EPSG:4326"

def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _as_int(value: Any, field: str) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer {field}={value!r}") from exc

def _as_float(value: Any, field: str) -> float:
    try:
        result = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid number {field}={value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"non-finite number {field}={value!r}")
    return result

def _load_geojson(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise ValueError("source must be a GeoJSON FeatureCollection")
    if not isinstance(payload.get("features"), list):
        raise ValueError("source FeatureCollection lacks a features list")
    return payload

def _normalize_feature(
    feature: dict[str, Any],
    transformer: Transformer,
    geometry_tolerance: float,
) -> dict[str, Any]:
    properties = dict(feature.get("properties") or {})
    row_no = _as_int(properties.get("row_no"), "row_no")
    parcel_id = str(properties.get("parcel_id") or "").strip()
    inspire_id = str(properties.get("hmlr_inspire_id") or "").strip()
    authority = str(properties.get("london_authority") or "").strip()
    if not parcel_id:
        raise ValueError(f"row_no {row_no} has empty parcel_id")
    if not inspire_id:
        raise ValueError(f"row_no {row_no} has empty hmlr_inspire_id")
    if not authority:
        raise ValueError(f"row_no {row_no} has empty london_authority")

    lon = _as_float(properties.get("hmlr_lon"), "hmlr_lon")
    lat = _as_float(properties.get("hmlr_lat"), "hmlr_lat")
    if not (-8.5 <= lon <= 2.5 and 49.0 <= lat <= 61.5):
        raise ValueError(f"row_no {row_no} is outside Great Britain coordinate bounds")

    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        raise ValueError(f"row_no {row_no} must have Point geometry")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise ValueError(f"row_no {row_no} has invalid Point coordinates")
    geom_lon = _as_float(coordinates[0], "geometry.longitude")
    geom_lat = _as_float(coordinates[1], "geometry.latitude")
    if abs(geom_lon - lon) > geometry_tolerance or abs(geom_lat - lat) > geometry_tolerance:
        raise ValueError(f"row_no {row_no} geometry and HMLR coordinate fields disagree")

    easting, northing = transformer.transform(lon, lat)
    if not (0 <= easting <= 700000 and 0 <= northing <= 1300000):
        raise ValueError(f"row_no {row_no} transformed BNG coordinate is invalid")

    return {
        "row_no": row_no,
        "parcel_id": parcel_id,
        "parcel_registry_id": None,
        "hmlr_inspire_id": inspire_id,
        "national_cadastral_reference": None,
        "hmlr_row_id": str(properties.get("hmlr_row_id") or "").strip() or None,
        "hmlr_area_m2": properties.get("hmlr_area_m2"),
        "longitude": lon,
        "latitude": lat,
        "bng_easting": round(float(easting), 3),
        "bng_northing": round(float(northing), 3),
        "local_authority_name": authority,
        "geometry_geojson_epsg4326": geometry,
        "source_coordinate_fields": ["hmlr_lon", "hmlr_lat", "geometry.coordinates"],
        "bng_coordinate_method": "PYPROJ_EPSG4326_TO_EPSG27700_FROM_SOURCE_HMLR_POINT",
        "identity_method": "EXPLICIT_ROW_NO_PARCEL_ID_AND_HMLR_INSPIRE_ID",
        "data_status": "canonical_source_backed_point_pending_current_hmlr_boundary",
        "existing_verified_height_value": None,
    }

def extract_rows(
    payload: dict[str, Any],
    *,
    canonical_count: int = CANONICAL_COUNT,
    row_start: int = ROW_START,
    row_end: int = ROW_END,
    geometry_tolerance: float = 1e-7,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    features = payload["features"]
    if len(features) != canonical_count:
        raise ValueError(f"expected {canonical_count} canonical features, received {len(features)}")

    transformer = Transformer.from_crs(SOURCE_CRS, TARGET_CRS, always_xy=True)
    row_numbers: set[int] = set()
    parcel_ids: set[str] = set()
    inspire_ids: set[str] = set()
    shard: list[dict[str, Any]] = []
    identity_by_row: dict[int, tuple[str, str, float, float, str]] = {}

    for index, feature in enumerate(features, start=1):
        if not isinstance(feature, dict):
            raise ValueError(f"feature {index} is not an object")
        row = _normalize_feature(feature, transformer, geometry_tolerance)
        row_no = row["row_no"]
        if row_no in row_numbers:
            raise ValueError(f"duplicate row_no {row_no}")
        if row["parcel_id"] in parcel_ids:
            raise ValueError(f"duplicate parcel_id {row['parcel_id']}")
        if row["hmlr_inspire_id"] in inspire_ids:
            raise ValueError(f"duplicate hmlr_inspire_id {row['hmlr_inspire_id']}")
        row_numbers.add(row_no)
        parcel_ids.add(row["parcel_id"])
        inspire_ids.add(row["hmlr_inspire_id"])
        identity_by_row[row_no] = (
            row["parcel_id"],
            row["hmlr_inspire_id"],
            row["longitude"],
            row["latitude"],
            row["local_authority_name"],
        )
        if row_start <= row_no <= row_end:
            shard.append(row)

    expected_all = set(range(1, canonical_count + 1))
    if row_numbers != expected_all:
        missing = sorted(expected_all - row_numbers)[:20]
        extra = sorted(row_numbers - expected_all)[:20]
        raise ValueError(f"canonical row registry is not exactly 1..{canonical_count}; missing={missing}, extra={extra}")

    expected_shard_count = row_end - row_start + 1
    shard.sort(key=lambda row: row["row_no"])
    if len(shard) != expected_shard_count:
        raise ValueError(f"expected {expected_shard_count} shard rows, received {len(shard)}")
    if [row["row_no"] for row in shard] != list(range(row_start, row_end + 1)):
        raise ValueError("shard row registry is not contiguous and explicit")

    identity_digest = hashlib.sha256()
    for row_no in range(1, canonical_count + 1):
        parcel_id, inspire_id, lon, lat, authority = identity_by_row[row_no]
        identity_digest.update(
            f"{row_no}\t{parcel_id}\t{inspire_id}\t{lon:.8f}\t{lat:.8f}\t{authority}\n".encode("utf-8")
        )

    audit = {
        "canonical_features_validated": len(features),
        "canonical_unique_row_numbers": len(row_numbers),
        "canonical_unique_parcel_ids": len(parcel_ids),
        "canonical_unique_hmlr_inspire_ids": len(inspire_ids),
        "shard_rows_validated": len(shard),
        "shard_row_start": row_start,
        "shard_row_end": row_end,
        "row_order_inference_used": False,
        "nearest_fill_used": False,
        "canonical_identity_sha256": identity_digest.hexdigest(),
    }
    return shard, audit

def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-geojson", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--crosscheck-geojson", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--query-preparer", type=Path)
    parser.add_argument("--skip-query-preparer", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args(argv)

    source = args.source_geojson.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    payload = _load_geojson(source)
    rows, audit = extract_rows(payload)
    del payload

    crosscheck: dict[str, Any] | None = None
    if args.crosscheck_geojson:
        crosscheck_path = args.crosscheck_geojson.resolve()
        if not crosscheck_path.is_file():
            raise FileNotFoundError(crosscheck_path)
        cross_payload = _load_geojson(crosscheck_path)
        cross_rows, cross_audit = extract_rows(cross_payload)
        del cross_payload
        if cross_audit["canonical_identity_sha256"] != audit["canonical_identity_sha256"]:
            raise ValueError("crosscheck GeoJSON canonical identity digest differs from primary source")
        primary_shard_digest = hashlib.sha256(
            "\n".join(
                f"{row['row_no']}\t{row['parcel_id']}\t{row['hmlr_inspire_id']}\t{row['longitude']:.8f}\t{row['latitude']:.8f}"
                for row in rows
            ).encode("utf-8")
        ).hexdigest()
        cross_shard_digest = hashlib.sha256(
            "\n".join(
                f"{row['row_no']}\t{row['parcel_id']}\t{row['hmlr_inspire_id']}\t{row['longitude']:.8f}\t{row['latitude']:.8f}"
                for row in cross_rows
            ).encode("utf-8")
        ).hexdigest()
        if primary_shard_digest != cross_shard_digest:
            raise ValueError("crosscheck GeoJSON shard identity/coordinate digest differs from primary source")
        crosscheck = {
            "path": str(crosscheck_path),
            "size_bytes": crosscheck_path.stat().st_size,
            "sha256": _sha256(crosscheck_path),
            "canonical_identity_sha256": cross_audit["canonical_identity_sha256"],
            "shard_identity_coordinate_sha256": cross_shard_digest,
            "status": "MATCHED_PRIMARY_CANONICAL_IDENTITY_AND_COORDINATES",
        }

    output_dir = args.output_dir.resolve()
    export_path = output_dir / "canonical_shard_61523_92283.jsonl"
    _write_jsonl(export_path, rows)

    manifest_payload: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "canonical_scope": "LONDON_CANONICAL_92283_NOT_ALL_ENGLAND",
        "source_path": str(source),
        "source_size_bytes": source.stat().st_size,
        "source_sha256": _sha256(source),
        "source_manifest_path": str(args.source_manifest.resolve()) if args.source_manifest else None,
        "source_manifest_sha256": _sha256(args.source_manifest.resolve()) if args.source_manifest else None,
        "source_layer": "security",
        "source_feature_count": audit["canonical_features_validated"],
        "crosscheck_source": crosscheck,
        "source_identity_fields": ["row_no", "parcel_id", "hmlr_inspire_id"],
        "source_location_fields": ["hmlr_lon", "hmlr_lat", "geometry.coordinates"],
        "normalization": {
            "longitude": "hmlr_lon",
            "latitude": "hmlr_lat",
            "local_authority_name": "london_authority",
            "bng_coordinates": "pyproj EPSG:4326 to EPSG:27700",
        },
        "export_path": str(export_path),
        **audit,
        "first_three_explicit_rows": [row["row_no"] for row in rows[:3]],
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    manifest_path = output_dir / "canonical_export_manifest.json"
    _write_json(manifest_path, manifest_payload)

    query_result: dict[str, Any] | None = None
    if not args.skip_query_preparer:
        preparer = args.query_preparer or Path(__file__).with_name("004_prepare_three_real_sample_queries.py")
        if not preparer.is_file():
            raise FileNotFoundError(preparer)
        command = [
            sys.executable, str(preparer),
            "--input", str(export_path),
            "--output-dir", str(output_dir / "first_three_queries"),
            "--sample-size", "3",
        ]
        if args.no_network:
            command.append("--no-network")
        process = subprocess.run(command, text=True, capture_output=True, check=False)
        query_result = {
            "command": command,
            "exit_code": process.returncode,
            "stdout": process.stdout[-8000:],
            "stderr": process.stderr[-8000:],
        }
        _write_json(output_dir / "query_preparer_execution.json", query_result)
        if process.returncode != 0:
            raise RuntimeError(f"query preparer failed with exit code {process.returncode}")

    print(json.dumps({
        "ok": True,
        "canonical_rows_validated": audit["canonical_features_validated"],
        "shard_rows_exported": len(rows),
        "first_three_rows": [row["row_no"] for row in rows[:3]],
        "query_preparer_executed": query_result is not None,
    }))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

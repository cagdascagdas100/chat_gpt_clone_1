#!/usr/bin/env python3
"""Fail-closed extraction of future_growth_2 rows from canonical security.geojson.

Identity comes only from explicit row_no, parcel_id and hmlr_inspire_id fields.
Feature order and nearest-fill logic are never used as parcel identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

DEFAULT_CANONICAL_COUNT = 92283
DEFAULT_ROW_START = 30762
DEFAULT_ROW_END = 61522


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


def _normalize_feature(feature: dict[str, Any], tolerance: float) -> dict[str, Any]:
    props = dict(feature.get("properties") or {})
    row_no = _as_int(props.get("row_no"), "row_no")
    parcel_id = str(props.get("parcel_id") or "").strip()
    inspire_id = str(props.get("hmlr_inspire_id") or "").strip()
    authority = str(props.get("london_authority") or "").strip()
    if not parcel_id or not inspire_id or not authority:
        raise ValueError(f"row_no {row_no} has incomplete explicit identity")

    lon = _as_float(props.get("hmlr_lon"), "hmlr_lon")
    lat = _as_float(props.get("hmlr_lat"), "hmlr_lat")
    if not (-8.5 <= lon <= 2.5 and 49.0 <= lat <= 61.5):
        raise ValueError(f"row_no {row_no} outside Great Britain coordinate bounds")

    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        raise ValueError(f"row_no {row_no} must have Point geometry")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise ValueError(f"row_no {row_no} invalid geometry coordinates")
    geom_lon = _as_float(coordinates[0], "geometry.longitude")
    geom_lat = _as_float(coordinates[1], "geometry.latitude")
    if abs(geom_lon - lon) > tolerance or abs(geom_lat - lat) > tolerance:
        raise ValueError(f"row_no {row_no} coordinate fields disagree")

    return {
        "row_no": row_no,
        "parcel_id": parcel_id,
        "hmlr_inspire_id": inspire_id,
        "hmlr_row_id": str(props.get("hmlr_row_id") or "").strip() or None,
        "hmlr_area_m2": props.get("hmlr_area_m2"),
        "longitude": lon,
        "latitude": lat,
        "local_authority_name": authority,
        "geometry_geojson_epsg4326": geometry,
        "identity_method": "EXPLICIT_ROW_NO_PARCEL_ID_AND_HMLR_INSPIRE_ID",
        "data_status": "canonical_source_backed_point_pending_current_hmlr_polygon"
    }


def extract_rows(
    payload: dict[str, Any],
    *,
    canonical_count: int,
    row_start: int,
    row_end: int,
    geometry_tolerance: float = 1e-7,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if payload.get("type") != "FeatureCollection" or not isinstance(payload.get("features"), list):
        raise ValueError("source must be a GeoJSON FeatureCollection")
    features = payload["features"]
    if len(features) != canonical_count:
        raise ValueError(f"expected {canonical_count} features, received {len(features)}")
    if row_start < 1 or row_end < row_start or row_end > canonical_count:
        raise ValueError("invalid shard range")

    row_numbers: set[int] = set()
    parcel_ids: set[str] = set()
    inspire_ids: set[str] = set()
    identity_digest = hashlib.sha256()
    normalized_by_row: dict[int, dict[str, Any]] = {}

    for feature in features:
        if not isinstance(feature, dict):
            raise ValueError("every feature must be an object")
        row = _normalize_feature(feature, geometry_tolerance)
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
        normalized_by_row[row_no] = row

    expected_rows = set(range(1, canonical_count + 1))
    if row_numbers != expected_rows:
        missing = sorted(expected_rows - row_numbers)[:20]
        extra = sorted(row_numbers - expected_rows)[:20]
        raise ValueError(f"row registry mismatch missing={missing} extra={extra}")

    for row_no in range(1, canonical_count + 1):
        row = normalized_by_row[row_no]
        identity_digest.update(
            f"{row_no}\t{row['parcel_id']}\t{row['hmlr_inspire_id']}\t"
            f"{row['longitude']:.8f}\t{row['latitude']:.8f}\t{row['local_authority_name']}\n".encode("utf-8")
        )

    shard = [normalized_by_row[row_no] for row_no in range(row_start, row_end + 1)]
    audit = {
        "canonical_features_validated": canonical_count,
        "canonical_unique_row_numbers": len(row_numbers),
        "canonical_unique_parcel_ids": len(parcel_ids),
        "canonical_unique_hmlr_inspire_ids": len(inspire_ids),
        "shard_rows_validated": len(shard),
        "shard_row_start": row_start,
        "shard_row_end": row_end,
        "canonical_identity_sha256": identity_digest.hexdigest(),
        "row_order_inference_used": False,
        "nearest_fill_used": False
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
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--canonical-count", type=int, default=DEFAULT_CANONICAL_COUNT)
    parser.add_argument("--row-start", type=int, default=DEFAULT_ROW_START)
    parser.add_argument("--row-end", type=int, default=DEFAULT_ROW_END)
    args = parser.parse_args(argv)

    source = args.source_geojson.resolve()
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    rows, audit = extract_rows(
        payload,
        canonical_count=args.canonical_count,
        row_start=args.row_start,
        row_end=args.row_end,
    )
    out = args.output_dir.resolve()
    shard_path = out / f"canonical_shard_{args.row_start}_{args.row_end}.jsonl"
    manifest_path = out / "canonical_shard_manifest.json"
    _write_jsonl(shard_path, rows)
    _write_json(manifest_path, {
        "schema_version": 1,
        "slot_id": "future_growth_2",
        "canonical_scope": "LONDON_CANONICAL_92283_NOT_ALL_ENGLAND",
        "source_path": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_identity_fields": ["row_no", "parcel_id", "hmlr_inspire_id"],
        "source_location_fields": ["hmlr_lon", "hmlr_lat", "geometry.coordinates"],
        "export_path": str(shard_path),
        **audit,
        "future_growth_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False
    })
    print(json.dumps({"ok": True, "rows": len(rows), "manifest": str(manifest_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

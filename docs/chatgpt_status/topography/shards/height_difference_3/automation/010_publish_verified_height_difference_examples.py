#!/usr/bin/env python3
"""Publish only fully gated height_difference_3 example rows to website JSON/GeoJSON."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

ROW_START = 61523
ROW_END = 92283
ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM_HIGH"}
ALLOWED_METHOD = "EA_DTM_1M_POLYGON_P95_MINUS_P05"


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("measurement manifest must be a JSON object")
    return payload


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _valid_number(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"non-finite numeric value: {value!r}")
    return number


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--measurement-manifest", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-geojson", type=Path, required=True)
    args = parser.parse_args(argv)

    manifest = _load(args.measurement_manifest)
    measured_rows = manifest.get("measured_rows")
    results = manifest.get("results")
    if not isinstance(measured_rows, list) or not isinstance(results, list):
        raise ValueError("measurement manifest lacks measured_rows/results lists")

    result_by_key = {
        (int(row["row_no"]), str(row["parcel_id"])): row
        for row in results
        if row.get("row_no") is not None and row.get("parcel_id") is not None
    }
    published_rows: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []
    seen_rows: set[int] = set()
    seen_parcels: set[str] = set()

    for source in measured_rows:
        row = dict(source)
        row_no = int(row["row_no"])
        parcel_id = str(row["parcel_id"]).strip()
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
        geometry = row.get("geometry_geojson_epsg4326_display_only")
        if not isinstance(geometry, dict) or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"row {row_no} lacks display polygon geometry")

        height_difference = _valid_number(row["height_difference_m"])
        elevation_median = _valid_number(row["elevation_median_m"])
        elevation_iqr = _valid_number(row["elevation_iqr_m"])
        os_elevation = _valid_number(row["os_terrain50_centroid_elevation_m"])
        cross_difference = _valid_number(row["cross_source_absolute_difference_m"])
        properties = {
            "row_no": row_no,
            "parcel_id": parcel_id,
            "height_difference_m": round(height_difference, 3),
            "height_difference_method": ALLOWED_METHOD,
            "elevation_median_m": round(elevation_median, 3),
            "elevation_iqr_m": round(elevation_iqr, 3),
            "ea_valid_cell_count": int(row["ea_valid_cell_count"]),
            "os_terrain50_centroid_elevation_m": round(os_elevation, 3),
            "cross_source_absolute_difference_m": round(cross_difference, 3),
            "boundary_match_method": row.get("boundary_match_method"),
            "confidence": row["confidence"],
            "data_status": "official_sources_crosschecked",
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

    status = "VERIFIED_EXAMPLES_PUBLISHED" if published_rows else "BLOCKED_NO_VERIFIED_MEASUREMENTS"
    summary = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "parcel_partition": {"start": ROW_START, "end": ROW_END, "count": 30761},
        "status": status,
        "published_example_count": len(published_rows),
        "rows": published_rows,
        "measurement_manifest": str(args.measurement_manifest),
        "publication_gate": {
            "official_boundary_required": True,
            "ea_polygon_sample_required": True,
            "os_terrain50_crosscheck_required": True,
            "allowed_confidence": sorted(ALLOWED_CONFIDENCE),
            "nearest_fill_forbidden": True,
        },
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
        "features": features,
        "final_ready": False,
        "fake_data": False,
    }
    _write(args.output_json, summary)
    _write(args.output_geojson, geojson)
    print(json.dumps({"ok": True, "published": len(published_rows), "status": status}))
    return 0 if published_rows else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

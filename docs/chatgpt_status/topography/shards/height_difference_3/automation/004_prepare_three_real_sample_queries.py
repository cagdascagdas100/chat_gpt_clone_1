#!/usr/bin/env python3
"""Prepare the first three real height_difference_3 parcel queries.

This script does not invent parcel coordinates or elevations. It validates a
canonical shard export, selects the first three source-backed unresolved rows,
queries the official Environment Agency tile inventory, and writes execution
manifests for the existing single shared runner.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

ROW_START = 61523
ROW_END = 92283
EXPECTED_COUNT = 30761
EA_COLLECTION_BASE = (
    "https://environment.data.gov.uk/geoservices/datasets/"
    "9f0fa3fc-a860-4729-adc9-47fe53f658d0/ogc/features/v1/"
    "collections/LIDAR_Composite_1m_DTM_2022_extents/items"
)
EA_WCS_CAPABILITIES = (
    "https://environment.data.gov.uk/spatialdata/"
    "lidar-composite-digital-terrain-model-dtm-1m/wcs"
    "?request=GetCapabilities&service=WCS&version=2.0.1"
)

REQUIRED_FIELDS = (
    "row_no",
    "parcel_id",
    "longitude",
    "latitude",
    "bng_easting",
    "bng_northing",
    "local_authority_name",
    "data_status",
)
OFFICIAL_ID_FIELDS = (
    "parcel_registry_id",
    "hmlr_inspire_id",
    "national_cadastral_reference",
)


def _load_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix in {".json", ".geojson"}:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return [dict(row) for row in payload]
        if isinstance(payload, dict):
            if isinstance(payload.get("rows"), list):
                return [dict(row) for row in payload["rows"]]
            if isinstance(payload.get("features"), list):
                rows: list[dict[str, Any]] = []
                for feature in payload["features"]:
                    row = dict(feature.get("properties") or {})
                    row["geometry_geojson_epsg4326"] = feature.get("geometry")
                    rows.append(row)
                return rows
        raise ValueError("JSON must be a row list, {'rows': [...]}, or GeoJSON FeatureCollection.")
    if suffix in {".jsonl", ".ndjson"}:
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                if line.strip():
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError(f"Line {line_no} is not a JSON object.")
                    rows.append(value)
        return rows
    raise ValueError(f"Unsupported export format: {suffix}")


def _as_int(value: Any, field: str) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer for {field}: {value!r}") from exc


def _as_float(value: Any, field: str) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid number for {field}: {value!r}") from exc


def _has_official_id(row: dict[str, Any]) -> bool:
    return any(str(row.get(field, "")).strip() for field in OFFICIAL_ID_FIELDS)


def _validate_rows(rows: list[dict[str, Any]], allow_explicit_missing: bool) -> list[dict[str, Any]]:
    if not rows:
        raise ValueError("Canonical export is empty.")

    normalized: list[dict[str, Any]] = []
    row_numbers: set[int] = set()
    parcel_ids: set[str] = set()

    for index, source in enumerate(rows, start=1):
        missing_fields = [field for field in REQUIRED_FIELDS if field not in source]
        if missing_fields:
            raise ValueError(f"Input row {index} lacks required fields: {missing_fields}")

        row = dict(source)
        row_no = _as_int(row["row_no"], "row_no")
        if not ROW_START <= row_no <= ROW_END:
            raise ValueError(f"row_no {row_no} is outside {ROW_START}-{ROW_END}.")
        if row_no in row_numbers:
            raise ValueError(f"Duplicate row_no: {row_no}")
        row_numbers.add(row_no)

        parcel_id = str(row["parcel_id"]).strip()
        if not parcel_id:
            raise ValueError(f"row_no {row_no} has an empty parcel_id.")
        if parcel_id in parcel_ids:
            raise ValueError(f"Duplicate parcel_id without conflict record: {parcel_id}")
        parcel_ids.add(parcel_id)

        data_status = str(row.get("data_status", "")).strip().lower()
        explicit_missing = data_status in {"no_data", "missing", "unmatched"}
        if explicit_missing and allow_explicit_missing:
            row["_eligible_for_sample"] = False
        else:
            row["longitude"] = _as_float(row["longitude"], "longitude")
            row["latitude"] = _as_float(row["latitude"], "latitude")
            row["bng_easting"] = _as_float(row["bng_easting"], "bng_easting")
            row["bng_northing"] = _as_float(row["bng_northing"], "bng_northing")
            row["_eligible_for_sample"] = _has_official_id(row)

        row["row_no"] = row_no
        row["parcel_id"] = parcel_id
        normalized.append(row)

    if len(normalized) != EXPECTED_COUNT and not allow_explicit_missing:
        raise ValueError(
            f"Expected exactly {EXPECTED_COUNT} rows, received {len(normalized)}. "
            "Use --allow-explicit-missing only when missing row records are explicit."
        )

    return sorted(normalized, key=lambda row: row["row_no"])


def _bbox_url(lon: float, lat: float, delta: float = 0.00015) -> str:
    query = {
        "bbox": f"{lon - delta:.8f},{lat - delta:.8f},{lon + delta:.8f},{lat + delta:.8f}",
        "limit": "20",
        "f": "application/geo+json",
    }
    return f"{EA_COLLECTION_BASE}?{urllib.parse.urlencode(query)}"


def _fetch_json(url: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "TerraYield-AAYS/height_difference_3"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _fetch_wcs_coverage_ids(timeout: int) -> list[str]:
    request = urllib.request.Request(
        EA_WCS_CAPABILITIES,
        headers={"User-Agent": "TerraYield-AAYS/height_difference_3"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        root = ET.fromstring(response.read())
    ids = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] in {"CoverageId", "Identifier"} and element.text:
            value = element.text.strip()
            if value and value not in ids:
                ids.append(value)
    return ids


def _tile_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for feature in payload.get("features") or []:
        props = dict(feature.get("properties") or {})
        result.append(
            {
                "feature_id": feature.get("id"),
                "filename": props.get("filename"),
                "tilename": props.get("tilename"),
                "polygon_id": props.get("polygon_id"),
                "resolution": props.get("resolution"),
                "year": props.get("year"),
                "od_dtm_fn": props.get("od_dtm_fn"),
                "survey_start": props.get("sd_flown"),
                "survey_end": props.get("ed_flown"),
            }
        )
    return result


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="Canonical shard CSV/JSON/JSONL export.")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--sample-size", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--allow-explicit-missing", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args(argv)

    rows = _validate_rows(_load_rows(args.input), args.allow_explicit_missing)
    candidates = [
        row
        for row in rows
        if row.get("_eligible_for_sample")
        and str(row.get("existing_verified_height_value", "")).strip() in {"", "null", "None"}
    ][: args.sample_size]

    if len(candidates) < args.sample_size:
        raise ValueError(
            f"Only {len(candidates)} source-backed unresolved rows are eligible; "
            f"{args.sample_size} are required."
        )

    coverage_ids: list[str] = []
    wcs_error: str | None = None
    if not args.no_network:
        try:
            coverage_ids = _fetch_wcs_coverage_ids(args.timeout)
        except Exception as exc:
            wcs_error = f"{type(exc).__name__}: {exc}"

    output_rows = []
    for row in candidates:
        query_url = _bbox_url(float(row["longitude"]), float(row["latitude"]))
        tile_matches: list[dict[str, Any]] = []
        query_error: str | None = None
        if not args.no_network:
            try:
                tile_matches = _tile_rows(_fetch_json(query_url, args.timeout))
            except Exception as exc:
                query_error = f"{type(exc).__name__}: {exc}"

        output_rows.append(
            {
                "row_no": row["row_no"],
                "parcel_id": row["parcel_id"],
                "parcel_registry_id": row.get("parcel_registry_id"),
                "hmlr_inspire_id": row.get("hmlr_inspire_id"),
                "national_cadastral_reference": row.get("national_cadastral_reference"),
                "longitude": row["longitude"],
                "latitude": row["latitude"],
                "bng_easting": row["bng_easting"],
                "bng_northing": row["bng_northing"],
                "local_authority_name": row["local_authority_name"],
                "ea_tile_inventory_query_url": query_url,
                "ea_tile_match_count": len(tile_matches),
                "ea_tile_matches": tile_matches,
                "ea_tile_query_error": query_error,
                "hmlr_boundary_status": "pending_current_local_authority_gml_match",
                "ea_numeric_status": "pending_wcs_or_geotiff_sample",
                "os_terrain50_status": "pending_independent_10km_tile_crosscheck",
                "measured_value_promoted": False,
                "data_status": "pending_official_measurement",
            }
        )

    manifest = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "parcel_partition": {"start": ROW_START, "end": ROW_END, "count": EXPECTED_COUNT},
        "canonical_export_path": str(args.input),
        "canonical_rows_validated": len(rows),
        "starter_candidate_count": len(output_rows),
        "network_queries_enabled": not args.no_network,
        "ea_wcs_capabilities_url": EA_WCS_CAPABILITIES,
        "ea_wcs_coverage_ids": coverage_ids,
        "ea_wcs_error": wcs_error,
        "candidates": output_rows,
        "measurement_gate": {
            "real_boundary_required": True,
            "ea_dtm_sample_required": True,
            "os_terrain50_crosscheck_required": True,
            "nearest_point_fill_forbidden": True,
        },
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    _write_json(args.output_dir / "starter_three_query_manifest.json", manifest)
    _write_json(
        args.output_dir / "operation_summary.json",
        {
            "validated_rows": len(rows),
            "selected_candidates": len(output_rows),
            "ea_tile_matches_total": sum(row["ea_tile_match_count"] for row in output_rows),
            "wcs_coverage_ids_found": len(coverage_ids),
            "numeric_samples_written": 0,
            "status": "QUERY_PREPARED_NUMERIC_SAMPLING_NOT_YET_EXECUTED",
        },
    )
    print(json.dumps({"ok": True, "output_dir": str(args.output_dir), "selected": len(output_rows)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

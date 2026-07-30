#!/usr/bin/env python3
"""Prepare exact source-backed starter candidates and official EA discovery evidence.

The canonical shard must be complete and contiguous. Network-enabled mode accepts only
HTTPS responses that remain on environment.data.gov.uk; coverage or tile-query errors
fail closed. The starter and summary manifests are published as one rollback-capable
bundle and are bound to the canonical shard SHA-256.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

ROW_START = 61523
ROW_END = 92283
EXPECTED_COUNT = 30761
EA_HOST = "environment.data.gov.uk"
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
MAX_RESPONSE_BYTES = 20 * 1024 * 1024

REQUIRED_FIELDS = (
    "row_no", "parcel_id", "longitude", "latitude", "bng_easting",
    "bng_northing", "local_authority_name", "data_status",
)
OFFICIAL_ID_FIELDS = (
    "parcel_registry_id", "hmlr_inspire_id", "national_cadastral_reference",
)


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix in {".json", ".geojson"}:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, list):
            return [dict(row) for row in payload]
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            return [dict(row) for row in payload["rows"]]
        if isinstance(payload, dict) and payload.get("type") == "FeatureCollection" and isinstance(payload.get("features"), list):
            rows: list[dict[str, Any]] = []
            for feature in payload["features"]:
                if not isinstance(feature, dict):
                    raise ValueError("GeoJSON feature is not an object")
                row = dict(feature.get("properties") or {})
                row["geometry_geojson_epsg4326"] = feature.get("geometry")
                rows.append(row)
            return rows
        raise ValueError("JSON must be rows or a GeoJSON FeatureCollection")
    if suffix in {".jsonl", ".ndjson"}:
        rows = []
        with path.open("r", encoding="utf-8-sig") as handle:
            for line_no, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"line {line_no} is not a JSON object")
                rows.append(value)
        return rows
    raise ValueError(f"unsupported export format: {suffix}")


def _as_int(value: Any, field: str) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer for {field}: {value!r}") from exc


def _as_float(value: Any, field: str) -> float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid number for {field}: {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"non-finite number for {field}: {value!r}")
    return number


def _clean_id(value: Any) -> str:
    return "".join(str(value or "").split()).casefold()


def _official_ids(row: dict[str, Any]) -> set[str]:
    return {_clean_id(row.get(field)) for field in OFFICIAL_ID_FIELDS if _clean_id(row.get(field))}


def _validate_rows(rows: list[dict[str, Any]], allow_explicit_missing: bool) -> list[dict[str, Any]]:
    if len(rows) != EXPECTED_COUNT:
        raise ValueError(f"expected exactly {EXPECTED_COUNT} explicit row records, received {len(rows)}")
    normalized: list[dict[str, Any]] = []
    row_numbers: set[int] = set()
    parcel_ids: set[str] = set()
    for index, source in enumerate(rows, start=1):
        if not isinstance(source, dict):
            raise ValueError(f"input row {index} is not an object")
        missing_fields = [field for field in REQUIRED_FIELDS if field not in source]
        if missing_fields:
            raise ValueError(f"input row {index} lacks required fields: {missing_fields}")
        row = dict(source)
        row_no = _as_int(row["row_no"], "row_no")
        if not ROW_START <= row_no <= ROW_END:
            raise ValueError(f"row_no {row_no} is outside {ROW_START}-{ROW_END}")
        if row_no in row_numbers:
            raise ValueError(f"duplicate row_no: {row_no}")
        row_numbers.add(row_no)
        parcel_id = str(row["parcel_id"]).strip()
        if not parcel_id or parcel_id in parcel_ids:
            raise ValueError(f"empty or duplicate parcel_id: {parcel_id!r}")
        parcel_ids.add(parcel_id)
        data_status = str(row.get("data_status", "")).strip().casefold()
        explicit_missing = data_status in {"no_data", "missing", "unmatched"}
        row["row_no"] = row_no
        row["parcel_id"] = parcel_id
        row["longitude"] = _as_float(row["longitude"], "longitude")
        row["latitude"] = _as_float(row["latitude"], "latitude")
        row["bng_easting"] = _as_float(row["bng_easting"], "bng_easting")
        row["bng_northing"] = _as_float(row["bng_northing"], "bng_northing")
        if not (-8.5 <= row["longitude"] <= 2.5 and 49.0 <= row["latitude"] <= 61.5):
            raise ValueError(f"row_no {row_no} longitude/latitude is outside Great Britain")
        if not (0 <= row["bng_easting"] <= 700000 and 0 <= row["bng_northing"] <= 1300000):
            raise ValueError(f"row_no {row_no} BNG coordinate is outside accepted extent")
        ids = _official_ids(row)
        row["candidate_official_ids"] = sorted(ids)
        row["_eligible_for_sample"] = bool(ids) and not (explicit_missing and allow_explicit_missing)
        if explicit_missing and not allow_explicit_missing:
            raise ValueError(f"row_no {row_no} is explicitly missing; use --allow-explicit-missing")
        normalized.append(row)
    expected_rows = set(range(ROW_START, ROW_END + 1))
    if row_numbers != expected_rows:
        missing = sorted(expected_rows - row_numbers)[:20]
        extra = sorted(row_numbers - expected_rows)[:20]
        raise ValueError(f"canonical shard registry is not contiguous; missing={missing}, extra={extra}")
    return sorted(normalized, key=lambda row: row["row_no"])


def _bbox_url(lon: float, lat: float, delta: float = 0.00015) -> str:
    if not math.isfinite(delta) or delta <= 0 or delta > 0.01:
        raise ValueError("bbox delta must be finite and within (0, 0.01]")
    query = {
        "bbox": f"{lon - delta:.8f},{lat - delta:.8f},{lon + delta:.8f},{lat + delta:.8f}",
        "limit": "20",
        "f": "application/geo+json",
    }
    return f"{EA_COLLECTION_BASE}?{urllib.parse.urlencode(query)}"


def _official_ea_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme == "https" and parsed.hostname == EA_HOST


def _read_bounded(response: Any) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_RESPONSE_BYTES:
            raise ValueError("official response exceeds safety size limit")
        chunks.append(chunk)
    if total == 0:
        raise ValueError("official response is empty")
    return b"".join(chunks)


def _open_official(url: str, timeout: int) -> tuple[bytes, str, str]:
    if not _official_ea_url(url):
        raise ValueError("EA request URL is not the pinned official HTTPS host")
    request = urllib.request.Request(url, headers={"User-Agent": "TerraYield-AAYS/height_difference_3"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        if not _official_ea_url(final_url):
            raise ValueError(f"EA response redirected off official host: {final_url}")
        body = _read_bounded(response)
        content_type = str(response.headers.get("content-type", ""))
    return body, final_url, content_type


def _fetch_json(url: str, timeout: int) -> tuple[dict[str, Any], dict[str, Any]]:
    body, final_url, content_type = _open_official(url, timeout)
    try:
        payload = json.loads(body.decode("utf-8-sig"))
    except Exception as exc:
        raise ValueError(f"EA tile inventory did not return JSON: {content_type}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise ValueError("EA tile inventory JSON lacks a features list")
    return payload, {
        "resolved_url": final_url,
        "content_type": content_type,
        "sha256": hashlib.sha256(body).hexdigest(),
        "size_bytes": len(body),
    }


def _fetch_wcs_coverage_ids(timeout: int) -> tuple[list[str], dict[str, Any]]:
    body, final_url, content_type = _open_official(EA_WCS_CAPABILITIES, timeout)
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise ValueError(f"EA WCS capabilities did not return XML: {content_type}") from exc
    ids: list[str] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] in {"CoverageId", "Identifier"} and element.text:
            value = element.text.strip()
            if value and value not in ids:
                ids.append(value)
    if not ids:
        raise ValueError("EA WCS capabilities exposed no coverage identifier")
    return ids, {
        "resolved_url": final_url,
        "content_type": content_type,
        "sha256": hashlib.sha256(body).hexdigest(),
        "size_bytes": len(body),
    }


def _tile_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, feature in enumerate(payload.get("features") or [], start=1):
        if not isinstance(feature, dict):
            raise ValueError(f"EA inventory feature {index} is not an object")
        props = dict(feature.get("properties") or {})
        geometry = feature.get("geometry")
        if geometry is not None and not isinstance(geometry, dict):
            raise ValueError(f"EA inventory feature {index} has invalid geometry")
        result.append({
            "feature_id": feature.get("id"),
            "filename": props.get("filename"),
            "tilename": props.get("tilename"),
            "polygon_id": props.get("polygon_id"),
            "resolution": props.get("resolution"),
            "year": props.get("year"),
            "od_dtm_fn": props.get("od_dtm_fn"),
            "survey_start": props.get("sd_flown"),
            "survey_end": props.get("ed_flown"),
        })
    return result


def _write_json_fsync(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _publish_bundle(staged: dict[Path, Path], output_dir: Path) -> None:
    backup_dir = Path(tempfile.mkdtemp(prefix=".query_bundle_", suffix=".backup", dir=output_dir))
    moved: list[tuple[Path, Path]] = []
    published: list[Path] = []
    try:
        for target, stage in staged.items():
            if not stage.is_file() or stage.stat().st_size <= 0:
                raise ValueError(f"staged query output missing or empty: {stage}")
            if target.exists():
                backup = backup_dir / target.name
                target.replace(backup)
                moved.append((target, backup))
        try:
            for target, stage in staged.items():
                stage.replace(target)
                published.append(target)
        except Exception:
            for target in reversed(published):
                target.unlink(missing_ok=True)
            for target, backup in reversed(moved):
                if backup.exists():
                    backup.replace(target)
            raise
    finally:
        shutil.rmtree(backup_dir, ignore_errors=True)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="Canonical shard CSV/JSON/JSONL export")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--sample-size", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--allow-explicit-missing", action="store_true")
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args(argv)
    if args.sample_size < 1 or args.sample_size > 100:
        raise ValueError("sample-size must be between 1 and 100")
    if args.timeout < 1 or args.timeout > 600:
        raise ValueError("timeout must be between 1 and 600 seconds")
    input_path = args.input.resolve()
    if not input_path.is_file() or input_path.stat().st_size <= 0:
        raise ValueError("canonical input must be a non-empty file")
    input_hash_before = _sha256(input_path)
    rows = _validate_rows(_load_rows(input_path), args.allow_explicit_missing)
    input_hash_after = _sha256(input_path)
    if input_hash_before != input_hash_after:
        raise ValueError("canonical input changed during query preparation")

    candidates = [
        row for row in rows
        if row.get("_eligible_for_sample")
        and row.get("canonical_identity_status") != "authority_overlap_alias"
        and row.get("existing_verified_height_value") in (None, "", "null", "None")
    ][: args.sample_size]
    if len(candidates) < args.sample_size:
        raise ValueError(f"only {len(candidates)} unique source-backed unresolved rows are eligible; {args.sample_size} required")

    coverage_ids: list[str] = []
    wcs_provenance: dict[str, Any] | None = None
    if not args.no_network:
        coverage_ids, wcs_provenance = _fetch_wcs_coverage_ids(args.timeout)

    output_rows: list[dict[str, Any]] = []
    for row in candidates:
        query_url = _bbox_url(float(row["longitude"]), float(row["latitude"]))
        tile_matches: list[dict[str, Any]] = []
        query_provenance: dict[str, Any] | None = None
        if not args.no_network:
            payload, query_provenance = _fetch_json(query_url, args.timeout)
            tile_matches = _tile_rows(payload)
            if not tile_matches:
                raise ValueError(f"EA tile inventory returned no match for row {row['row_no']}")
        output_rows.append({
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
            "canonical_primary_row_no": row.get("canonical_primary_row_no", row["row_no"]),
            "candidate_official_ids": row["candidate_official_ids"],
            "ea_tile_inventory_query_url": query_url,
            "ea_tile_match_count": len(tile_matches),
            "ea_tile_matches": tile_matches,
            "ea_tile_query_provenance": query_provenance,
            "hmlr_boundary_status": "pending_current_local_authority_gml_match",
            "ea_numeric_status": "pending_wcs_or_geotiff_sample",
            "os_terrain50_status": "pending_independent_10km_tile_crosscheck",
            "measured_value_promoted": False,
            "data_status": "pending_official_measurement",
        })

    status = "QUERY_PREPARED_OFFICIAL_DISCOVERY_VERIFIED" if not args.no_network else "QUERY_PREPARED_NO_NETWORK_DIAGNOSTIC"
    manifest = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "status": status,
        "parcel_partition": {"start": ROW_START, "end": ROW_END, "count": EXPECTED_COUNT},
        "canonical_export_path": str(input_path),
        "canonical_export_sha256": input_hash_after,
        "canonical_rows_validated": len(rows),
        "canonical_registry_contiguous": True,
        "starter_candidate_count": len(output_rows),
        "network_queries_enabled": not args.no_network,
        "official_ea_host_only": True,
        "ea_wcs_capabilities_url": EA_WCS_CAPABILITIES,
        "ea_wcs_coverage_ids": coverage_ids,
        "ea_wcs_provenance": wcs_provenance,
        "candidates": output_rows,
        "authority_overlap_aliases_skipped": True,
        "transactional_output_bundle": True,
        "previous_valid_outputs_preserved_on_failure": True,
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
    summary = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "status": status,
        "canonical_export_sha256": input_hash_after,
        "validated_rows": len(rows),
        "selected_candidates": len(output_rows),
        "selected_row_numbers": [row["row_no"] for row in output_rows],
        "ea_tile_matches_total": sum(row["ea_tile_match_count"] for row in output_rows),
        "wcs_coverage_ids_found": len(coverage_ids),
        "numeric_samples_written": 0,
        "transactional_output_bundle": True,
    }

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stage_dir = Path(tempfile.mkdtemp(prefix=".query_prepare_", suffix=".stage", dir=output_dir))
    try:
        stage_manifest = stage_dir / "starter_three_query_manifest.json"
        stage_summary = stage_dir / "operation_summary.json"
        _write_json_fsync(stage_manifest, manifest)
        _write_json_fsync(stage_summary, summary)
        _publish_bundle({
            output_dir / stage_manifest.name: stage_manifest,
            output_dir / stage_summary.name: stage_summary,
        }, output_dir)
    finally:
        shutil.rmtree(stage_dir, ignore_errors=True)
    print(json.dumps({"ok": True, "status": status, "output_dir": str(output_dir), "selected": len(output_rows)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

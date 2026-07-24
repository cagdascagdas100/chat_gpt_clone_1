#!/usr/bin/env python3
"""Fetch bounded EA DTM 1m GeoTIFF coverages for HMLR-matched parcels.

The WCS coverage identifier and axis labels are discovered at runtime. Each
response is checked with Rasterio for CRS, finite dimensions, resolution and
intersection with the matched parcel. HTML/error responses fail closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

import requests
import rasterio
from pyproj import CRS
from shapely import wkt
from shapely.geometry import box

DEFAULT_WCS = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
TARGET_CRS = CRS.from_epsg(27700)
MAX_RESPONSE_BYTES = 500_000_000


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_matches(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    values = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(values, list) or not values:
        raise ValueError("matched manifest has no results")
    matched = [dict(value) for value in values if value.get("status") == "MATCHED" and isinstance(value.get("match"), dict)]
    if len(matched) != len(values):
        raise ValueError("all candidates must have a unique HMLR match before EA WCS download")
    return matched


def _request_xml(session: requests.Session, base: str, params: list[tuple[str, str]], timeout: int) -> tuple[ET.Element, bytes, str]:
    response = session.get(base, params=params, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    body = response.content
    if not body:
        raise ValueError("WCS XML response is empty")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise ValueError(f"WCS did not return XML: {response.headers.get('content-type')}") from exc
    return root, body, response.url


def _coverage_ids(root: ET.Element) -> list[str]:
    values = []
    for element in root.iter():
        if _local(element.tag) in {"CoverageId", "Identifier"} and element.text:
            value = element.text.strip()
            if value and value not in values:
                values.append(value)
    return values


def _select_coverage(ids: list[str]) -> str:
    if not ids:
        raise ValueError("WCS GetCapabilities exposed no coverage identifier")
    if len(ids) == 1:
        return ids[0]
    def tokens(value: str) -> set[str]:
        return set(filter(None, re.split(r"[^a-z0-9]+", value.casefold())))

    # The EA endpoint currently exposes both the numeric elevation raster and a
    # cartographic hillshade with otherwise almost identical DTM/1m names.
    # Hillshade pixel values are illumination, not metres, so never select it
    # as a height source.
    preferred = [
        value
        for value in ids
        if "dtm" in tokens(value)
        and ({"1m", "1"} & tokens(value))
        and "elevation" in tokens(value)
        and "hillshade" not in tokens(value)
    ]
    if len(preferred) == 1:
        return preferred[0]
    non_hillshade_dtm = [
        value
        for value in ids
        if "dtm" in tokens(value)
        and ({"1m", "1"} & tokens(value))
        and "hillshade" not in tokens(value)
    ]
    if len(non_hillshade_dtm) == 1:
        return non_hillshade_dtm[0]
    raise ValueError(f"WCS coverage identifier is ambiguous: {ids}")


def _axis_labels(root: ET.Element) -> tuple[str, str]:
    for element in root.iter():
        if _local(element.tag) in {"Envelope", "RectifiedGrid"}:
            labels = element.attrib.get("axisLabels")
            if labels:
                parts = labels.split()
                if len(parts) >= 2:
                    return parts[0], parts[1]
    return "E", "N"


def _stream_get(session: requests.Session, base: str, params: list[tuple[str, str]], output: Path, timeout: int) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    with session.get(base, params=params, timeout=timeout, stream=True, allow_redirects=True) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        total = 0
        with output.open("wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    raise ValueError("EA WCS response exceeds safety size limit")
                handle.write(chunk)
    head = output.read_bytes()[:512].lstrip().lower()
    if head.startswith(b"<") and (b"exception" in head or b"html" in head):
        raise ValueError("EA WCS returned XML/HTML exception instead of GeoTIFF")
    return {"resolved_url": response.url, "content_type": content_type, "size_bytes": total}


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matched-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--wcs-base", default=DEFAULT_WCS)
    parser.add_argument("--buffer-m", type=float, default=5.0)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)

    if args.buffer_m < 0 or not math.isfinite(args.buffer_m):
        raise ValueError("buffer-m must be finite and non-negative")
    matches = _load_matches(args.matched_manifest)
    session = requests.Session()
    session.headers.update({"User-Agent": "TerraYield-AAYS/height_difference_3"})

    capabilities, caps_body, caps_url = _request_xml(session, args.wcs_base, [("service", "WCS"), ("version", "2.0.1"), ("request", "GetCapabilities")], args.timeout)
    coverage_id = _select_coverage(_coverage_ids(capabilities))
    description, desc_body, desc_url = _request_xml(session, args.wcs_base, [("service", "WCS"), ("version", "2.0.1"), ("request", "DescribeCoverage"), ("coverageId", coverage_id)], args.timeout)
    axis_x, axis_y = _axis_labels(description)

    records = []
    raster_paths = []
    for row in matches:
        geometry = wkt.loads(row["match"]["geometry_wkt_epsg27700"])
        if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"row {row.get('row_no')} has invalid matched geometry")
        minx, miny, maxx, maxy = geometry.bounds
        minx -= args.buffer_m
        miny -= args.buffer_m
        maxx += args.buffer_m
        maxy += args.buffer_m
        params = [
            ("service", "WCS"), ("version", "2.0.1"), ("request", "GetCoverage"),
            ("coverageId", coverage_id), ("format", "image/tiff"),
            ("subset", f"{axis_x}({minx:.3f},{maxx:.3f})"),
            ("subset", f"{axis_y}({miny:.3f},{maxy:.3f})"),
        ]
        output = args.output_dir / "ea_dtm" / f"row_{int(row['row_no'])}_ea_dtm_1m.tif"
        meta = _stream_get(session, args.wcs_base, params, output, args.timeout)
        with rasterio.open(output) as dataset:
            if dataset.crs is None:
                raise ValueError(f"EA raster for row {row.get('row_no')} has no CRS")
            crs = CRS.from_user_input(dataset.crs)
            if crs != TARGET_CRS:
                raise ValueError(f"EA raster for row {row.get('row_no')} is {crs}, expected EPSG:27700")
            if dataset.width <= 0 or dataset.height <= 0:
                raise ValueError("EA raster has invalid dimensions")
            if not box(*dataset.bounds).intersects(geometry):
                raise ValueError("EA raster does not intersect matched parcel geometry")
            resolution = [abs(float(dataset.res[0])), abs(float(dataset.res[1]))]
            if max(resolution) > 1.1:
                raise ValueError(f"EA raster resolution is coarser than 1.1m: {resolution}")
            record = {
                "row_no": row.get("row_no"),
                "parcel_id": row.get("parcel_id"),
                "path": str(output),
                "sha256": _sha256(output),
                "size_bytes": output.stat().st_size,
                "resolved_url": meta["resolved_url"],
                "content_type": meta["content_type"],
                "crs": crs.to_string(),
                "width": dataset.width,
                "height": dataset.height,
                "resolution_m": resolution,
                "bounds": list(map(float, dataset.bounds)),
                "nodata": dataset.nodata,
            }
        records.append(record)
        raster_paths.append(str(output))

    manifest = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "status": "READY",
        "wcs_base": args.wcs_base,
        "capabilities_url": caps_url,
        "capabilities_sha256": hashlib.sha256(caps_body).hexdigest(),
        "describe_coverage_url": desc_url,
        "describe_coverage_sha256": hashlib.sha256(desc_body).hexdigest(),
        "coverage_id": coverage_id,
        "axis_labels": [axis_x, axis_y],
        "candidate_count": len(records),
        "records": records,
        "raster_paths": raster_paths,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    output_manifest = args.output_dir / "ea_dtm_source_manifest.json"
    _write(output_manifest, manifest)
    print(json.dumps({"ok": True, "manifest": str(output_manifest), "rasters": len(records)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

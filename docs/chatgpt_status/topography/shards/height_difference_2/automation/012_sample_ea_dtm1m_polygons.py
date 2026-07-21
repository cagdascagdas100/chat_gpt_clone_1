#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import requests
import rasterio
from lxml import etree
from rasterio.io import MemoryFile
from rasterio.mask import mask
from shapely.geometry import shape

DEFAULT_WCS = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
MAX_RESPONSE_BYTES = 250_000_000
NODATA_FLOOR = -1.0e30

def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()

def _load_polygons(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("status") != "THREE_HMLR_EXACT_POLYGONS_MATCHED":
        raise ValueError("HMLR exact polygon gate is not complete")
    rows = payload.get("results")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("exactly three HMLR results required")
    result = []
    for index, row in enumerate(rows, 1):
        if row.get("status") != "MATCHED_EXACT_ID_AND_POINT_INSIDE":
            raise ValueError(f"HMLR row {index} is not an exact inside match")
        match_row = row.get("match")
        if not isinstance(match_row, dict):
            raise ValueError(f"HMLR row {index} lacks match")
        geometry = match_row.get("geometry_geojson_epsg27700")
        if not isinstance(geometry, dict):
            raise ValueError(f"HMLR row {index} lacks EPSG:27700 polygon")
        geom = shape(geometry)
        if geom.is_empty or geom.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"HMLR row {index} has invalid polygon")
        result.append({
            "row_no": int(row["row_no"]),
            "parcel_id": str(row["parcel_id"]),
            "hmlr_inspire_id": str(row["hmlr_inspire_id"]),
            "geometry": geometry,
            "bounds": list(map(float, geom.bounds)),
        })
    return result

def _xml_root(content: bytes) -> etree._Element:
    parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)
    return etree.fromstring(content, parser=parser)

def _get(session: requests.Session, url: str, params: dict[str, Any], timeout: int) -> requests.Response:
    response = session.get(url, params=params, timeout=timeout, allow_redirects=True, stream=False)
    response.raise_for_status()
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("EA WCS response exceeds safety limit")
    return response

def _discover_coverage(session: requests.Session, base_url: str, timeout: int, override: str | None) -> tuple[str, dict[str, Any]]:
    capabilities = _get(session, base_url, {
        "service": "WCS", "version": "2.0.1", "request": "GetCapabilities"
    }, timeout)
    root = _xml_root(capabilities.content)
    coverage_ids = [
        (node.text or "").strip()
        for node in root.xpath("//*[local-name()='CoverageId']")
        if (node.text or "").strip()
    ]
    coverage_ids = list(dict.fromkeys(coverage_ids))
    if override:
        if override not in coverage_ids:
            raise ValueError("configured CoverageId absent from capabilities")
        selected = override
    else:
        ranked = [
            value for value in coverage_ids
            if re.search(r"dtm", value, re.I) and re.search(r"(^|[^0-9])1\s*m([^0-9]|$)|1m", value, re.I)
        ]
        if len(ranked) != 1:
            raise ValueError(f"unique DTM 1m CoverageId not found: {ranked!r}")
        selected = ranked[0]
    return selected, {
        "capabilities_url": capabilities.url,
        "capabilities_sha256": _sha256_bytes(capabilities.content),
        "coverage_ids_seen": coverage_ids,
    }

def _describe(session: requests.Session, base_url: str, timeout: int, coverage_id: str) -> dict[str, Any]:
    response = _get(session, base_url, {
        "service": "WCS", "version": "2.0.1", "request": "DescribeCoverage",
        "coverageId": coverage_id,
    }, timeout)
    root = _xml_root(response.content)
    axis_values = []
    for node in root.xpath("//*[@axisLabels]"):
        axis_values.extend(str(node.attrib.get("axisLabels", "")).split())
    axis_values = [value for value in axis_values if value]
    if len(axis_values) < 2:
        axis_values = ["E", "N"]
    return {
        "describe_url": response.url,
        "describe_sha256": _sha256_bytes(response.content),
        "axis_labels": axis_values[:2],
    }

def _download_geotiff(
    session: requests.Session,
    base_url: str,
    timeout: int,
    coverage_id: str,
    axis_labels: list[str],
    bounds: list[float],
    padding_m: float,
) -> tuple[bytes, str]:
    minx, miny, maxx, maxy = bounds
    minx -= padding_m
    miny -= padding_m
    maxx += padding_m
    maxy += padding_m
    params: list[tuple[str, str]] = [
        ("service", "WCS"),
        ("version", "2.0.1"),
        ("request", "GetCoverage"),
        ("coverageId", coverage_id),
        ("format", "image/tiff"),
        ("subsettingCrs", "http://www.opengis.net/def/crs/EPSG/0/27700"),
        ("outputCrs", "http://www.opengis.net/def/crs/EPSG/0/27700"),
        ("subset", f"{axis_labels[0]}({minx:.3f},{maxx:.3f})"),
        ("subset", f"{axis_labels[1]}({miny:.3f},{maxy:.3f})"),
    ]
    response = session.get(base_url, params=params, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    content = response.content
    if not content or len(content) > MAX_RESPONSE_BYTES:
        raise ValueError("EA WCS GetCoverage returned empty or oversized content")
    content_type = response.headers.get("content-type", "").lower()
    head = content[:512].lstrip().lower()
    if b"exceptionreport" in head or b"serviceexception" in head or head.startswith(b"<"):
        raise ValueError("EA WCS GetCoverage returned XML/error instead of raster")
    if "tiff" not in content_type and not content.startswith((b"II*\x00", b"MM\x00*")):
        raise ValueError(f"EA WCS response is not GeoTIFF: {content_type!r}")
    return content, response.url

def _sample(content: bytes, geometry: dict[str, Any]) -> dict[str, Any]:
    with MemoryFile(content) as memfile:
        with memfile.open() as dataset:
            crs = dataset.crs.to_epsg() if dataset.crs else None
            if crs != 27700:
                raise ValueError(f"EA raster CRS is not EPSG:27700: {dataset.crs}")
            data, _ = mask(dataset, [geometry], crop=True, all_touched=False, filled=False)
            band = np.ma.asarray(data[0], dtype="float64")
            values = band.compressed()
            values = values[np.isfinite(values)]
            values = values[values > NODATA_FLOOR]
            if values.size == 0:
                raise ValueError("EA DTM has no valid pixel centres inside polygon")
            q1, median, q3 = np.quantile(values, [0.25, 0.5, 0.75])
            return {
                "valid_pixel_count": int(values.size),
                "q1_m_odn": round(float(q1), 3),
                "median_m_odn": round(float(median), 3),
                "q3_m_odn": round(float(q3), 3),
                "min_m_odn": round(float(values.min()), 3),
                "max_m_odn": round(float(values.max()), 3),
                "raster_resolution_m": [abs(float(dataset.transform.a)), abs(float(dataset.transform.e))],
                "raster_width": dataset.width,
                "raster_height": dataset.height,
                "raster_nodata": dataset.nodata,
            }

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hmlr-exact-matches", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wcs-url", default=DEFAULT_WCS)
    parser.add_argument("--coverage-id")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--padding-m", type=float, default=2.0)
    parser.add_argument("--user-agent", default="TerraYield-AAYS/height_difference_2")
    args = parser.parse_args(argv)
    try:
        polygons = _load_polygons(args.hmlr_exact_matches)
        session = requests.Session()
        session.headers.update({"User-Agent": args.user_agent})
        coverage_id, capabilities_meta = _discover_coverage(
            session, args.wcs_url, args.timeout, args.coverage_id
        )
        describe_meta = _describe(session, args.wcs_url, args.timeout, coverage_id)
        rows = []
        for polygon in polygons:
            content, resolved_url = _download_geotiff(
                session, args.wcs_url, args.timeout, coverage_id,
                describe_meta["axis_labels"], polygon["bounds"], args.padding_m
            )
            sample = _sample(content, polygon["geometry"])
            rows.append({
                "row_no": polygon["row_no"],
                "parcel_id": polygon["parcel_id"],
                "hmlr_inspire_id": polygon["hmlr_inspire_id"],
                "source": "Environment Agency LiDAR Composite DTM 1m WCS",
                "coverage_id": coverage_id,
                "resolved_getcoverage_url": resolved_url,
                "geotiff_sha256": _sha256_bytes(content),
                "geometry_source": "exact HMLR INSPIRE polygon EPSG:27700",
                "centroid_fallback_used": False,
                **sample,
            })
        status = "THREE_EA_DTM1M_POLYGON_SAMPLES_READY" if len(rows) == 3 else "BLOCKED_THREE_EA_SAMPLES_NOT_READY"
        code = 0 if len(rows) == 3 else 2
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": status,
            "processing_crs": "EPSG:27700",
            "vertical_reference": "Ordnance Datum Newlyn",
            "sample_method": "valid raster pixel centres inside exact HMLR polygon",
            "coverage_id": coverage_id,
            "capabilities": capabilities_meta,
            "describe_coverage": describe_meta,
            "sample_count": len(rows),
            "samples": rows,
            "centroid_value_promotion_forbidden": True,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": "BLOCKED_EA_DTM1M_POLYGON_SAMPLER",
            "error": f"{type(exc).__name__}: {exc}",
            "sample_count": 0,
            "centroid_value_promotion_forbidden": True,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 2
    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"], "samples": payload.get("sample_count", 0)}))
    return code

if __name__ == "__main__":
    raise SystemExit(main())

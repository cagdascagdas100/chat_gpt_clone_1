#!/usr/bin/env python3
"""Fail-closed HMLR boundary + EA WCS evidence runner for height_difference_1.

This script never invents geometry or elevation. It writes a business row only when
all required official-byte, CRS, unique polygon-binding, raster, finite-pixel and
provenance gates pass. The 10 m requests are service/point QA only; the terrain
height difference is computed from a second DTM request covering the full bound
polygon.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import dataclasses
import datetime as dt
import hashlib
import html.parser
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
from typing import Any, Iterable
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

SLOT_ID = "height_difference_1"
PARTITION = {"start": 1, "end": 30761, "count": 30761}
HMLR_DOWNLOAD_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
HMLR_AUTHORITY = "London Borough of Barking and Dagenham"
DTM_ENDPOINT = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
DSM_ENDPOINT = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-surface-model-last-return-dsm-1m/wcs"
DTM_COVERAGE = "13787b9a-26a4-4775-8523-806d13af58fc__Lidar_Composite_Elevation_DTM_1m"
DSM_COVERAGE = "9ba4d5ac-d596-445a-9056-dae3ddec0178__Lidar_Composite_Elevation_LZ_DSM_1m"
USER_AGENT = "AAYS-height-difference-evidence/1.0 (+https://github.com/cagdascagdas100/chat_gpt_clone_1)"


class EvidenceError(RuntimeError):
    pass


class TableLinkParser(html.parser.HTMLParser):
    """Capture row text and links without requiring BeautifulSoup."""

    def __init__(self) -> None:
        super().__init__()
        self.in_row = False
        self.rows: list[dict[str, Any]] = []
        self._text: list[str] = []
        self._links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "tr":
            self.in_row = True
            self._text, self._links = [], []
        if self.in_row and tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self._links.append(href)

    def handle_data(self, data: str) -> None:
        if self.in_row:
            text = data.strip()
            if text:
                self._text.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "tr" and self.in_row:
            self.rows.append({"text": " ".join(self._text), "links": self._links[:]})
            self.in_row = False


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def fetch_bytes(url: str, *, timeout: int = 180, retries: int = 3) -> tuple[bytes, dict[str, str]]:
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with contextlib.closing(urlopen(req, timeout=timeout)) as response:
                status = getattr(response, "status", 200)
                if status != 200:
                    raise EvidenceError(f"HTTP_{status}: {url}")
                data = response.read()
                headers = {k.lower(): v for k, v in response.headers.items()}
            if not data:
                raise EvidenceError(f"EMPTY_RESPONSE: {url}")
            return data, headers
        except Exception as exc:  # factual retry record is emitted by caller
            last = exc
            if attempt < retries:
                time.sleep(attempt * 3)
    raise EvidenceError(f"DOWNLOAD_FAILED: {url}: {last}")


def discover_hmlr_gml_url(page_bytes: bytes) -> str:
    parser = TableLinkParser()
    parser.feed(page_bytes.decode("utf-8", errors="replace"))
    for row in parser.rows:
        if HMLR_AUTHORITY.lower() not in row["text"].lower():
            continue
        for href in row["links"]:
            full = urljoin(HMLR_DOWNLOAD_PAGE, href)
            if ".gml" in full.lower() or "inspire" in full.lower():
                return full
    # Fail closed: do not guess an opaque download URL.
    raise EvidenceError("HMLR_BARKING_DAGENHAM_GML_LINK_NOT_DISCOVERED")


def validate_xml_bytes(data: bytes) -> None:
    prefix = data[:256].lstrip().lower()
    if not (prefix.startswith(b"<?xml") or b"<" in prefix):
        raise EvidenceError("HMLR_RESPONSE_NOT_XML_OR_GML")


def validate_tiff_bytes(data: bytes, content_type: str | None) -> None:
    if data[:2] not in (b"II", b"MM"):
        raise EvidenceError("WCS_RESPONSE_NOT_TIFF_MAGIC")
    if content_type and "tiff" not in content_type.lower() and "octet-stream" not in content_type.lower():
        raise EvidenceError(f"UNEXPECTED_WCS_CONTENT_TYPE:{content_type}")


def wcs_url(endpoint: str, coverage_id: str, bbox: tuple[float, float, float, float]) -> str:
    minx, miny, maxx, maxy = bbox
    params = [
        ("service", "WCS"),
        ("version", "2.0.1"),
        ("request", "GetCoverage"),
        ("coverageId", coverage_id),
        ("format", "image/tiff"),
        ("subset", f"E({minx:.3f},{maxx:.3f})"),
        ("subset", f"N({miny:.3f},{maxy:.3f})"),
    ]
    return endpoint + "?" + urlencode(params)


def required_geo_modules() -> tuple[Any, Any, Any, Any, Any]:
    try:
        import geopandas as gpd  # type: ignore
        import numpy as np  # type: ignore
        import rasterio  # type: ignore
        from rasterio.mask import mask  # type: ignore
        from shapely.geometry import Point, mapping  # type: ignore
    except Exception as exc:
        raise EvidenceError(f"REQUIRED_GEOSPATIAL_DEPENDENCY_MISSING:{exc}") from exc
    return gpd, np, rasterio, mask, (Point, mapping)


def choose_polygon_id_column(columns: Iterable[str]) -> str:
    lowered = {str(c).lower(): str(c) for c in columns}
    for key in ("inspireid", "inspire_id", "landregistry-inspire-id", "gml_id", "gml:id", "id"):
        if key in lowered:
            return lowered[key]
    raise EvidenceError("HMLR_POLYGON_ID_COLUMN_NOT_RESOLVED")


def exact_polygon_match(gdf: Any, point: Any) -> tuple[list[int], list[int]]:
    try:
        exact_idx = list(gdf.sindex.query(point, predicate="intersects"))
        near_idx = list(gdf.sindex.query(point.buffer(15.0), predicate="intersects"))
    except Exception:
        exact_idx = list(gdf.index[gdf.geometry.intersects(point)])
        near_idx = list(gdf.index[gdf.geometry.intersects(point.buffer(15.0))])
    return [int(i) for i in exact_idx], [int(i) for i in near_idx]


def raster_measurement(tiff_path: Path, polygon: Any, rasterio: Any, np: Any, mask: Any, mapping: Any) -> dict[str, Any]:
    with rasterio.open(tiff_path) as src:
        crs_epsg = src.crs.to_epsg() if src.crs else None
        if crs_epsg != 27700:
            raise EvidenceError(f"RASTER_CRS_NOT_EPSG27700:{crs_epsg}")
        res_x, res_y = abs(float(src.res[0])), abs(float(src.res[1]))
        if not (0.75 <= res_x <= 1.25 and 0.75 <= res_y <= 1.25):
            raise EvidenceError(f"RASTER_RESOLUTION_NOT_APPROX_1M:{res_x},{res_y}")
        pminx, pminy, pmaxx, pmaxy = polygon.bounds
        b = src.bounds
        if pminx < b.left or pminy < b.bottom or pmaxx > b.right or pmaxy > b.top:
            raise EvidenceError("POLYGON_NOT_FULLY_COVERED_BY_RASTER")
        clipped, _ = mask(src, [mapping(polygon)], crop=True, filled=False)
        band = clipped[0]
        values = band.compressed() if hasattr(band, "compressed") else band[np.isfinite(band)]
        values = values[np.isfinite(values)]
        if src.nodata is not None:
            values = values[values != src.nodata]
        if values.size < 1:
            raise EvidenceError("NO_FINITE_RASTER_PIXELS_INSIDE_POLYGON")
        vmin = float(values.min())
        vmax = float(values.max())
        if not (math.isfinite(vmin) and math.isfinite(vmax) and vmax >= vmin):
            raise EvidenceError("INVALID_RASTER_MIN_MAX")
        return {
            "crs_epsg": crs_epsg,
            "resolution_m": [res_x, res_y],
            "valid_pixel_count": int(values.size),
            "min_m_aod": round(vmin, 3),
            "max_m_aod": round(vmax, 3),
            "height_difference_m": round(vmax - vmin, 3),
        }


def load_survey_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise EvidenceError("SURVEY_METADATA_JSON_MUST_BE_OBJECT")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(os.environ.get("AAYS_REPO_ROOT", Path.cwd())))
    parser.add_argument("--examples-json", type=Path)
    parser.add_argument("--probe-urls-json", type=Path)
    parser.add_argument("--hmlr-gml-url", default=os.environ.get("HMLR_BARKING_DAGENHAM_GML_URL"))
    parser.add_argument("--survey-metadata-json", type=Path, default=None)
    parser.add_argument("--runner-output", type=Path)
    parser.add_argument("--website-output", type=Path)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    examples_path = args.examples_json or repo / "england_map_web/data/aays_18_slots/height_difference_1/examples_latest.json"
    urls_path = args.probe_urls_json or repo / "england_map_web/data/aays_18_slots/height_difference_1/getcoverage_urls_latest.json"
    runner_output = args.runner_output or repo / "docs/chatgpt_status/height_difference/shards/height_difference_1/runner_outputs/official_boundary_and_wcs_latest.json"
    website_output = args.website_output or repo / "england_map_web/data/aays_18_slots/height_difference_1/verified_results_latest.json"

    result: dict[str, Any] = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "parcel_partition": PARTITION,
        "started_at": utc_now(),
        "state": "STARTED_FAIL_CLOSED",
        "business_rows": [],
        "candidate_measurements": [],
        "examples": [],
        "artifacts": {},
        "errors": [],
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }

    workdir = Path(tempfile.mkdtemp(prefix="height_difference_1_"))
    try:
        examples_doc = json.loads(examples_path.read_text(encoding="utf-8"))
        urls_doc = json.loads(urls_path.read_text(encoding="utf-8"))
        examples = examples_doc.get("examples", [])
        if len(examples) != 11 or any(not str(x.get("parcel_id", "")).startswith("parcel_") for x in examples):
            raise EvidenceError("EXPECTED_EXACTLY_11_PINNED_EXAMPLES")
        if urls_doc.get("url_count") != 22:
            raise EvidenceError("EXPECTED_22_PREPARED_WCS_URLS")

        page_bytes, page_headers = fetch_bytes(HMLR_DOWNLOAD_PAGE)
        gml_url = args.hmlr_gml_url or discover_hmlr_gml_url(page_bytes)
        gml_bytes, gml_headers = fetch_bytes(gml_url, timeout=300)
        validate_xml_bytes(gml_bytes)
        gml_path = workdir / "barking_and_dagenham_current.gml"
        gml_path.write_bytes(gml_bytes)
        result["artifacts"]["hmlr_gml"] = {
            "url": gml_url,
            "sha256": sha256_bytes(gml_bytes),
            "bytes": len(gml_bytes),
            "content_type": gml_headers.get("content-type"),
            "download_page_sha256": sha256_bytes(page_bytes),
            "download_page_content_type": page_headers.get("content-type"),
        }

        gpd, np, rasterio, mask, shape_tools = required_geo_modules()
        Point, mapping = shape_tools
        gdf = gpd.read_file(gml_path)
        if gdf.empty:
            raise EvidenceError("HMLR_GML_HAS_ZERO_FEATURES")
        if gdf.crs is None:
            raise EvidenceError("HMLR_GML_CRS_MISSING")
        source_crs = str(gdf.crs)
        if gdf.crs.to_epsg() != 27700:
            gdf = gdf.to_crs(epsg=27700)
        id_column = choose_polygon_id_column(gdf.columns)
        result["artifacts"]["hmlr_gml"].update({
            "feature_count": int(len(gdf)),
            "source_crs": source_crs,
            "working_crs": "EPSG:27700",
            "polygon_id_column": id_column,
        })

        # The 22 fixed 10 m requests are service/point QA. Download in parallel and hash every response.
        probe_requests = urls_doc["requests"]
        def get_probe(row: dict[str, Any]) -> dict[str, Any]:
            data, headers = fetch_bytes(row["getcoverage_url"], timeout=240)
            validate_tiff_bytes(data, headers.get("content-type"))
            path = workdir / f"{row['probe_id']}.tif"
            path.write_bytes(data)
            return {
                "probe_id": row["probe_id"],
                "parcel_id": row["parcel_id"],
                "product": row["product"],
                "url": row["getcoverage_url"],
                "path": str(path),
                "sha256": sha256_bytes(data),
                "bytes": len(data),
                "content_type": headers.get("content-type"),
                "state": "TIFF_BYTES_VERIFIED",
            }

        probe_receipts: list[dict[str, Any]] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.max_workers, 4))) as pool:
            futures = [pool.submit(get_probe, row) for row in probe_requests]
            for future in concurrent.futures.as_completed(futures):
                probe_receipts.append(future.result())
        probe_receipts.sort(key=lambda x: x["probe_id"])
        result["probe_receipts"] = probe_receipts

        survey_metadata = load_survey_metadata(args.survey_metadata_json)
        for ex in examples:
            parcel_id = ex["parcel_id"]
            item: dict[str, Any] = {
                "parcel_id": parcel_id,
                "point_bng": [ex["bng_easting_m"], ex["bng_northing_m"]],
                "boundary_state": "PENDING",
                "measurement_state": "NOT_RUN",
                "business_row": False,
                "errors": [],
            }
            try:
                point = Point(float(ex["bng_easting_m"]), float(ex["bng_northing_m"]))
                exact_idx, near_idx = exact_polygon_match(gdf, point)
                item["exact_polygon_candidate_count"] = len(exact_idx)
                item["within_15m_candidate_count"] = len(near_idx)
                if len(exact_idx) != 1:
                    raise EvidenceError(f"UNIQUE_EXACT_POLYGON_REQUIRED:found={len(exact_idx)}")
                row = gdf.loc[exact_idx[0]]
                polygon = row.geometry
                if polygon is None or polygon.is_empty or not polygon.is_valid:
                    raise EvidenceError("BOUND_POLYGON_INVALID_OR_EMPTY")
                polygon_id = str(row[id_column])
                item.update({
                    "boundary_state": "UNIQUE_EXACT_POINT_IN_POLYGON",
                    "polygon_id": polygon_id,
                    "polygon_bounds_bng": [round(float(v), 3) for v in polygon.bounds],
                    "polygon_area_m2": round(float(polygon.area), 3),
                })

                minx, miny, maxx, maxy = polygon.bounds
                bbox = (minx - 1.0, miny - 1.0, maxx + 1.0, maxy + 1.0)
                full_requests = {
                    "DTM_1M": (DTM_ENDPOINT, DTM_COVERAGE),
                    "DSM_LZ_1M": (DSM_ENDPOINT, DSM_COVERAGE),
                }
                full_receipts: dict[str, Any] = {}
                for product, (endpoint, coverage) in full_requests.items():
                    url = wcs_url(endpoint, coverage, bbox)
                    data, headers = fetch_bytes(url, timeout=300)
                    validate_tiff_bytes(data, headers.get("content-type"))
                    tif = workdir / f"{parcel_id}_{product}.tif"
                    tif.write_bytes(data)
                    measure = raster_measurement(tif, polygon, rasterio, np, mask, mapping)
                    full_receipts[product] = {
                        "url": url,
                        "sha256": sha256_bytes(data),
                        "bytes": len(data),
                        "content_type": headers.get("content-type"),
                        "measurement": measure,
                    }
                item["full_polygon_rasters"] = full_receipts
                dtm = full_receipts["DTM_1M"]["measurement"]
                dsm = full_receipts["DSM_LZ_1M"]["measurement"]
                item["measurement_state"] = "OFFICIAL_BYTES_AND_GEOMETRY_MEASURED"
                item["candidate_height_difference_m"] = dtm["height_difference_m"]
                item["dsm_qa_height_range_m"] = dsm["height_difference_m"]
                item["survey_metadata"] = survey_metadata.get(parcel_id)

                candidate = {
                    "parcel_id": parcel_id,
                    "polygon_id": polygon_id,
                    "polygon_hash_basis": result["artifacts"]["hmlr_gml"]["sha256"],
                    "dtm_sha256": full_receipts["DTM_1M"]["sha256"],
                    "dsm_sha256": full_receipts["DSM_LZ_1M"]["sha256"],
                    "dtm_min_m_aod": dtm["min_m_aod"],
                    "dtm_max_m_aod": dtm["max_m_aod"],
                    "height_difference_m": dtm["height_difference_m"],
                    "valid_dtm_pixel_count": dtm["valid_pixel_count"],
                    "survey_metadata": item["survey_metadata"],
                    "evidence_state": "MEASURED_OFFICIAL_BYTES",
                }
                result["candidate_measurements"].append(candidate)
                if item["survey_metadata"]:
                    business = dict(candidate)
                    business["business_row"] = True
                    business["evidence_state"] = "VERIFIED_ALL_REQUIRED_GATES"
                    result["business_rows"].append(business)
                    item["business_row"] = True
                else:
                    item["errors"].append("SURVEY_METADATA_NOT_RESOLVED_BUSINESS_ROW_WITHHELD")
            except Exception as exc:
                item["errors"].append(str(exc))
            result["examples"].append(item)

        result["state"] = "COMPLETED_FAIL_CLOSED"
    except Exception as exc:
        result["state"] = "BLOCKED_FAIL_CLOSED"
        result["errors"].append(str(exc))
    finally:
        result["finished_at"] = utc_now()
        result["counts"] = {
            "prepared_examples": 11,
            "prepared_probe_requests": 22,
            "verified_probe_tiff_receipts": len(result.get("probe_receipts", [])),
            "unique_boundary_bindings": sum(1 for x in result["examples"] if x.get("boundary_state") == "UNIQUE_EXACT_POINT_IN_POLYGON"),
            "candidate_measurements": len(result["candidate_measurements"]),
            "business_rows_written": len(result["business_rows"]),
        }
        atomic_json(runner_output, result)
        atomic_json(website_output, result)
        shutil.rmtree(workdir, ignore_errors=True)

    print(f"SLOT_ID={SLOT_ID}")
    print(f"STATE={result['state']}")
    print(f"BUSINESS_ROWS_WRITTEN={len(result['business_rows'])}")
    print("FINAL_READY=false")
    return 0 if result["state"] == "COMPLETED_FAIL_CLOSED" else 2


if __name__ == "__main__":
    sys.exit(main())

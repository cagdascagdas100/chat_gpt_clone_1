#!/usr/bin/env python3
"""Fail-closed HMLR boundary + EA WCS evidence runner for height_difference_1.

No geometry, elevation, confidence percentage or successful execution is invented.
The 10 m requests are per-parcel service QA. The terrain result is calculated only
from a second DTM request covering the complete uniquely bound HMLR polygon.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import datetime as dt
import hashlib
import html.parser
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
from typing import Any, Iterable
from urllib.parse import parse_qs, urlencode, urljoin, urlparse
from urllib.request import Request, urlopen

SLOT_ID = "height_difference_1"
SCRIPT_VERSION = "1.1-hardened-fail-closed"
PARTITION = {"start": 1, "end": 30761, "count": 30761}
EXPECTED_SOURCE_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EXPECTED_SOURCE_FEATURE_COUNT = 92283
EXPECTED_PARCELS = [f"parcel_{i}" for i in range(1, 12)]
HMLR_DOWNLOAD_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
HMLR_AUTHORITY = "London Borough of Barking and Dagenham"
DTM_ENDPOINT = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
DSM_ENDPOINT = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-surface-model-last-return-dsm-1m/wcs"
DTM_COVERAGE = "13787b9a-26a4-4775-8523-806d13af58fc__Lidar_Composite_Elevation_DTM_1m"
DSM_COVERAGE = "9ba4d5ac-d596-445a-9056-dae3ddec0178__Lidar_Composite_Elevation_LZ_DSM_1m"
USER_AGENT = "AAYS-height-difference-evidence/1.1 (+https://github.com/cagdascagdas100/chat_gpt_clone_1)"
MAX_GML_BYTES = 1_000_000_000
MAX_TIFF_BYTES = 250_000_000
MAX_FULL_POLYGON_CELLS = 4_000_000


class EvidenceError(RuntimeError):
    pass


class TableLinkParser(html.parser.HTMLParser):
    """Capture table-row text and links without third-party HTML dependencies."""

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
        if self.in_row and data.strip():
            self._text.append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "tr" and self.in_row:
            self.rows.append({"text": " ".join(self._text), "links": self._links[:]})
            self.in_row = False


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(encoded)


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def fetch_bytes(
    url: str,
    *,
    timeout: int = 180,
    retries: int = 3,
    max_bytes: int,
) -> tuple[bytes, dict[str, str]]:
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
            with contextlib.closing(urlopen(req, timeout=timeout)) as response:
                status = getattr(response, "status", 200)
                if status != 200:
                    raise EvidenceError(f"HTTP_{status}:{url}")
                headers = {k.lower(): v for k, v in response.headers.items()}
                declared = headers.get("content-length")
                if declared and int(declared) > max_bytes:
                    raise EvidenceError(f"DECLARED_RESPONSE_TOO_LARGE:{declared}>{max_bytes}")
                chunks: list[bytes] = []
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise EvidenceError(f"RESPONSE_TOO_LARGE:{total}>{max_bytes}")
                    chunks.append(chunk)
                data = b"".join(chunks)
            if not data:
                raise EvidenceError(f"EMPTY_RESPONSE:{url}")
            return data, headers
        except Exception as exc:
            last = exc
            if attempt < retries:
                time.sleep(attempt * 3)
    raise EvidenceError(f"DOWNLOAD_FAILED:{url}:{last}")


def discover_hmlr_gml_url(page_bytes: bytes) -> str:
    parser = TableLinkParser()
    parser.feed(page_bytes.decode("utf-8", errors="replace"))
    matching_rows = [row for row in parser.rows if HMLR_AUTHORITY.lower() in row["text"].lower()]
    if len(matching_rows) != 1:
        raise EvidenceError(f"HMLR_AUTHORITY_ROW_NOT_UNIQUE:found={len(matching_rows)}")
    row = matching_rows[0]
    if "download" not in row["text"].lower() or ".gml" not in row["text"].lower():
        raise EvidenceError("HMLR_AUTHORITY_ROW_NOT_GML_DOWNLOAD")
    https_links = []
    for href in row["links"]:
        full = urljoin(HMLR_DOWNLOAD_PAGE, href)
        if urlparse(full).scheme == "https":
            https_links.append(full)
    if len(https_links) != 1:
        raise EvidenceError(f"HMLR_GML_LINK_NOT_UNIQUE:found={len(https_links)}")
    return https_links[0]


def validate_xml_bytes(data: bytes) -> None:
    prefix = data[:1024].lstrip().lower()
    if prefix.startswith(b"<html") or b"<!doctype html" in prefix:
        raise EvidenceError("HMLR_RESPONSE_IS_HTML_NOT_GML")
    if not (prefix.startswith(b"<?xml") or prefix.startswith(b"<")):
        raise EvidenceError("HMLR_RESPONSE_NOT_XML_OR_GML")


def validate_tiff_bytes(data: bytes, content_type: str | None) -> None:
    if len(data) < 8 or data[:2] not in (b"II", b"MM"):
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


def validate_examples_doc(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if doc.get("slot_id") != SLOT_ID:
        raise EvidenceError("EXAMPLES_SLOT_ID_MISMATCH")
    if doc.get("source_feature_collection_blob_sha") != EXPECTED_SOURCE_BLOB_SHA:
        raise EvidenceError("CANONICAL_SOURCE_BLOB_SHA_MISMATCH")
    if doc.get("source_feature_collection_count") != EXPECTED_SOURCE_FEATURE_COUNT:
        raise EvidenceError("CANONICAL_SOURCE_FEATURE_COUNT_MISMATCH")
    examples = doc.get("examples")
    if not isinstance(examples, list) or [x.get("parcel_id") for x in examples] != EXPECTED_PARCELS:
        raise EvidenceError("EXPECTED_ORDERED_PARCEL_1_TO_11")
    for row in examples:
        easting = float(row["bng_easting_m"])
        northing = float(row["bng_northing_m"])
        if not (math.isfinite(easting) and math.isfinite(northing)):
            raise EvidenceError(f"NON_FINITE_BNG:{row['parcel_id']}")
        if not (0 <= easting <= 700_000 and 0 <= northing <= 1_300_000):
            raise EvidenceError(f"BNG_OUTSIDE_PLAUSIBLE_RANGE:{row['parcel_id']}")
        if row.get("height_difference_m") is not None or row.get("business_row") is not False:
            raise EvidenceError(f"PREPARED_EXAMPLE_MUST_BE_UNMEASURED:{row['parcel_id']}")
    return examples


def validate_probe_urls_doc(doc: dict[str, Any]) -> list[dict[str, Any]]:
    requests = doc.get("requests")
    if doc.get("slot_id") != SLOT_ID or doc.get("url_count") != 22 or not isinstance(requests, list):
        raise EvidenceError("EXPECTED_22_SLOT_SCOPED_WCS_URLS")
    expected_ids = [f"HD1-WCS-{i:03d}" for i in range(1, 23)]
    if [row.get("probe_id") for row in requests] != expected_ids:
        raise EvidenceError("WCS_PROBE_ID_SEQUENCE_MISMATCH")
    pairs: dict[str, set[str]] = {parcel: set() for parcel in EXPECTED_PARCELS}
    for row in requests:
        parcel = row.get("parcel_id")
        product = row.get("product")
        if parcel not in pairs or product not in {"DTM_1M", "DSM_LZ_1M"}:
            raise EvidenceError(f"WCS_PARCEL_OR_PRODUCT_INVALID:{parcel}:{product}")
        pairs[parcel].add(product)
        parsed = urlparse(str(row.get("getcoverage_url", "")))
        if parsed.scheme != "https" or parsed.netloc != "environment.data.gov.uk":
            raise EvidenceError(f"WCS_URL_HOST_INVALID:{row.get('probe_id')}")
        query = parse_qs(parsed.query)
        expected_coverage = DTM_COVERAGE if product == "DTM_1M" else DSM_COVERAGE
        if query.get("coverageId") != [expected_coverage]:
            raise EvidenceError(f"WCS_COVERAGE_ID_MISMATCH:{row.get('probe_id')}")
        if query.get("service") != ["WCS"] or query.get("request") != ["GetCoverage"]:
            raise EvidenceError(f"WCS_REQUEST_SEMANTICS_INVALID:{row.get('probe_id')}")
        if len(query.get("subset", [])) != 2:
            raise EvidenceError(f"WCS_SUBSET_COUNT_INVALID:{row.get('probe_id')}")
    if any(products != {"DTM_1M", "DSM_LZ_1M"} for products in pairs.values()):
        raise EvidenceError("WCS_DTM_DSM_PAIR_MISSING")
    return requests


def choose_polygon_id_column(columns: Iterable[str]) -> str:
    lowered = {str(c).lower(): str(c) for c in columns}
    for key in ("inspireid", "inspire_id", "landregistry-inspire-id", "gml_id", "gml:id", "id"):
        if key in lowered:
            return lowered[key]
    raise EvidenceError("HMLR_POLYGON_ID_COLUMN_NOT_RESOLVED")


def exact_polygon_match_positions(gdf: Any, point: Any) -> tuple[list[int], list[int]]:
    try:
        exact = [int(i) for i in gdf.sindex.query(point, predicate="intersects")]
        nearby = [int(i) for i in gdf.sindex.query(point.buffer(15.0), predicate="intersects")]
    except Exception:
        exact_mask = gdf.geometry.intersects(point).to_numpy()
        nearby_mask = gdf.geometry.intersects(point.buffer(15.0)).to_numpy()
        exact = [int(i) for i, value in enumerate(exact_mask) if bool(value)]
        nearby = [int(i) for i, value in enumerate(nearby_mask) if bool(value)]
    return exact, nearby


def validate_survey_metadata_entry(parcel_id: str, entry: Any) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise EvidenceError(f"SURVEY_METADATA_MISSING:{parcel_id}")
    source_url = str(entry.get("source_url", ""))
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.netloc != "environment.data.gov.uk":
        raise EvidenceError(f"SURVEY_METADATA_SOURCE_NOT_OFFICIAL_EA:{parcel_id}")
    survey_date = entry.get("survey_date")
    survey_year = entry.get("survey_year")
    if survey_date:
        try:
            parsed_date = dt.date.fromisoformat(str(survey_date))
        except ValueError as exc:
            raise EvidenceError(f"SURVEY_DATE_NOT_ISO:{parcel_id}") from exc
        if not (2000 <= parsed_date.year <= dt.date.today().year):
            raise EvidenceError(f"SURVEY_DATE_OUT_OF_RANGE:{parcel_id}")
    elif survey_year is not None:
        year = int(survey_year)
        if not (2000 <= year <= dt.date.today().year):
            raise EvidenceError(f"SURVEY_YEAR_OUT_OF_RANGE:{parcel_id}")
    else:
        raise EvidenceError(f"SURVEY_DATE_OR_YEAR_REQUIRED:{parcel_id}")
    if str(entry.get("resolution_state", "")).upper() not in {"RESOLVED", "OFFICIAL_METADATA_RESOLVED"}:
        raise EvidenceError(f"SURVEY_METADATA_NOT_RESOLVED:{parcel_id}")
    return dict(entry)


def raster_measurement(tiff_path: Path, polygon: Any, rasterio: Any, np: Any, mask: Any, mapping: Any) -> dict[str, Any]:
    with rasterio.open(tiff_path) as src:
        if src.count != 1:
            raise EvidenceError(f"RASTER_BAND_COUNT_NOT_ONE:{src.count}")
        crs_epsg = src.crs.to_epsg() if src.crs else None
        if crs_epsg != 27700:
            raise EvidenceError(f"RASTER_CRS_NOT_EPSG27700:{crs_epsg}")
        res_x, res_y = abs(float(src.res[0])), abs(float(src.res[1]))
        if not (0.75 <= res_x <= 1.25 and 0.75 <= res_y <= 1.25):
            raise EvidenceError(f"RASTER_RESOLUTION_NOT_APPROX_1M:{res_x},{res_y}")
        pminx, pminy, pmaxx, pmaxy = polygon.bounds
        bounds = src.bounds
        if pminx < bounds.left or pminy < bounds.bottom or pmaxx > bounds.right or pmaxy > bounds.top:
            raise EvidenceError("POLYGON_NOT_FULLY_COVERED_BY_RASTER")
        clipped, _ = mask(src, [mapping(polygon)], crop=True, filled=False, all_touched=False)
        band = clipped[0]
        values = band.compressed() if hasattr(band, "compressed") else band[np.isfinite(band)]
        values = values[np.isfinite(values)]
        if src.nodata is not None:
            values = values[values != src.nodata]
        if values.size < 1:
            raise EvidenceError("NO_FINITE_RASTER_PIXELS_INSIDE_POLYGON")
        vmin, vmax = float(values.min()), float(values.max())
        if not (math.isfinite(vmin) and math.isfinite(vmax) and vmax >= vmin):
            raise EvidenceError("INVALID_RASTER_MIN_MAX")
        p05, median, p95 = [float(x) for x in np.percentile(values, [5, 50, 95])]
        return {
            "crs_epsg": crs_epsg,
            "resolution_m": [res_x, res_y],
            "valid_pixel_count": int(values.size),
            "min_m_aod": round(vmin, 3),
            "max_m_aod": round(vmax, 3),
            "height_difference_m": round(vmax - vmin, 3),
            "p05_m_aod": round(p05, 3),
            "median_m_aod": round(median, 3),
            "p95_m_aod": round(p95, 3),
            "robust_p95_minus_p05_m": round(p95 - p05, 3),
        }


def load_survey_metadata(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise EvidenceError("SURVEY_METADATA_JSON_MUST_BE_OBJECT")
    return data


def run_self_test() -> dict[str, Any]:
    sample_html = (
        '<table><tr><td>London Borough of Barking and Dagenham</td>'
        '<td><a href="/official/file.gml">Download .gml</a></td></tr></table>'
    ).encode()
    discovered = discover_hmlr_gml_url(sample_html)
    generated = wcs_url(DTM_ENDPOINT, DTM_COVERAGE, (1.0, 2.0, 11.0, 12.0))
    validate_tiff_bytes(b"II*\x00\x00\x00\x00\x00", "image/tiff")
    validate_xml_bytes(b'<?xml version="1.0"?><gml/>')
    if discovered != "https://use-land-property-data.service.gov.uk/official/file.gml":
        raise EvidenceError("SELF_TEST_HMLR_DISCOVERY_FAILED")
    if "coverageId=" not in generated or generated.count("subset=") != 2:
        raise EvidenceError("SELF_TEST_WCS_URL_FAILED")
    return {"state": "PASS", "checks": 4, "script_version": SCRIPT_VERSION}


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
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(run_self_test(), sort_keys=True))
        return 0

    repo = args.repo_root.resolve()
    examples_path = args.examples_json or repo / "england_map_web/data/aays_18_slots/height_difference_1/examples_latest.json"
    urls_path = args.probe_urls_json or repo / "england_map_web/data/aays_18_slots/height_difference_1/getcoverage_urls_latest.json"
    runner_output = args.runner_output or repo / "docs/chatgpt_status/height_difference/shards/height_difference_1/runner_outputs/official_boundary_and_wcs_latest.json"
    website_output = args.website_output or repo / "england_map_web/data/aays_18_slots/height_difference_1/verified_results_latest.json"

    result: dict[str, Any] = {
        "schema_version": 2,
        "slot_id": SLOT_ID,
        "script_version": SCRIPT_VERSION,
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
        examples_bytes = examples_path.read_bytes()
        urls_bytes = urls_path.read_bytes()
        examples_doc = json.loads(examples_bytes)
        urls_doc = json.loads(urls_bytes)
        examples = validate_examples_doc(examples_doc)
        probe_requests = validate_probe_urls_doc(urls_doc)
        result["artifacts"]["input_examples"] = {"sha256": sha256_bytes(examples_bytes), "rows": len(examples)}
        result["artifacts"]["input_probe_urls"] = {"sha256": sha256_bytes(urls_bytes), "rows": len(probe_requests)}

        page_bytes, page_headers = fetch_bytes(
            HMLR_DOWNLOAD_PAGE, timeout=180, retries=3, max_bytes=20_000_000
        )
        gml_url = args.hmlr_gml_url or discover_hmlr_gml_url(page_bytes)
        gml_bytes, gml_headers = fetch_bytes(
            gml_url, timeout=300, retries=3, max_bytes=MAX_GML_BYTES
        )
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

        def get_probe(row: dict[str, Any]) -> dict[str, Any]:
            receipt = {
                "probe_id": row["probe_id"],
                "parcel_id": row["parcel_id"],
                "product": row["product"],
                "url": row["getcoverage_url"],
                "state": "BLOCKED_FAIL_CLOSED",
                "sha256": None,
                "bytes": 0,
                "content_type": None,
                "error": None,
            }
            try:
                data, headers = fetch_bytes(
                    row["getcoverage_url"], timeout=240, retries=3, max_bytes=MAX_TIFF_BYTES
                )
                validate_tiff_bytes(data, headers.get("content-type"))
                path = workdir / f"{row['probe_id']}.tif"
                path.write_bytes(data)
                with rasterio.open(path) as src:
                    if src.crs is None or src.crs.to_epsg() != 27700:
                        raise EvidenceError("PROBE_RASTER_CRS_NOT_EPSG27700")
                    if src.count != 1:
                        raise EvidenceError("PROBE_RASTER_BAND_COUNT_NOT_ONE")
                receipt.update({
                    "state": "TIFF_BYTES_AND_CRS_VERIFIED",
                    "sha256": sha256_bytes(data),
                    "bytes": len(data),
                    "content_type": headers.get("content-type"),
                })
            except Exception as exc:
                receipt["error"] = str(exc)
            return receipt

        workers = max(1, min(args.max_workers, 4))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            probe_receipts = list(pool.map(get_probe, probe_requests))
        result["probe_receipts"] = probe_receipts
        probe_by_parcel_product = {
            (row["parcel_id"], row["product"]): row for row in probe_receipts
        }
        survey_metadata = load_survey_metadata(args.survey_metadata_json)

        def process_example(ex: dict[str, Any]) -> dict[str, Any]:
            parcel_id = ex["parcel_id"]
            item: dict[str, Any] = {
                "parcel_id": parcel_id,
                "slot_ordinal": int(ex["slot_ordinal"]),
                "point_bng": [ex["bng_easting_m"], ex["bng_northing_m"]],
                "boundary_state": "PENDING",
                "measurement_state": "NOT_RUN",
                "business_row": False,
                "errors": [],
            }
            try:
                qa_pair = [
                    probe_by_parcel_product[(parcel_id, "DTM_1M")],
                    probe_by_parcel_product[(parcel_id, "DSM_LZ_1M")],
                ]
                item["probe_qa_states"] = [row["state"] for row in qa_pair]
                if any(row["state"] != "TIFF_BYTES_AND_CRS_VERIFIED" for row in qa_pair):
                    raise EvidenceError("PARCEL_DTM_DSM_10M_QA_PAIR_NOT_VERIFIED")

                point = Point(float(ex["bng_easting_m"]), float(ex["bng_northing_m"]))
                exact_positions, near_positions = exact_polygon_match_positions(gdf, point)
                item["exact_polygon_candidate_count"] = len(exact_positions)
                item["within_15m_candidate_count"] = len(near_positions)
                if len(exact_positions) != 1:
                    raise EvidenceError(f"UNIQUE_EXACT_POLYGON_REQUIRED:found={len(exact_positions)}")
                row = gdf.iloc[exact_positions[0]]
                polygon = row.geometry
                if polygon is None or polygon.is_empty or not polygon.is_valid:
                    raise EvidenceError("BOUND_POLYGON_INVALID_OR_EMPTY")
                polygon_id = str(row[id_column])
                polygon_wkb_sha256 = sha256_bytes(bytes(polygon.wkb))
                item.update({
                    "boundary_state": "UNIQUE_EXACT_POINT_IN_POLYGON",
                    "polygon_id": polygon_id,
                    "polygon_wkb_sha256": polygon_wkb_sha256,
                    "polygon_bounds_bng": [round(float(v), 3) for v in polygon.bounds],
                    "polygon_area_m2": round(float(polygon.area), 3),
                })

                minx, miny, maxx, maxy = polygon.bounds
                bbox = (minx - 1.0, miny - 1.0, maxx + 1.0, maxy + 1.0)
                width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
                estimated_cells = int(math.ceil(width) * math.ceil(height))
                item["full_polygon_request_estimated_cells"] = estimated_cells
                if estimated_cells < 1 or estimated_cells > MAX_FULL_POLYGON_CELLS:
                    raise EvidenceError(f"FULL_POLYGON_REQUEST_CELL_GUARD:{estimated_cells}")

                full_receipts: dict[str, Any] = {}
                for product, endpoint, coverage in (
                    ("DTM_1M", DTM_ENDPOINT, DTM_COVERAGE),
                    ("DSM_LZ_1M", DSM_ENDPOINT, DSM_COVERAGE),
                ):
                    url = wcs_url(endpoint, coverage, bbox)
                    data, headers = fetch_bytes(url, timeout=300, retries=3, max_bytes=MAX_TIFF_BYTES)
                    validate_tiff_bytes(data, headers.get("content-type"))
                    tif = workdir / f"{parcel_id}_{product}.tif"
                    tif.write_bytes(data)
                    measurement = raster_measurement(tif, polygon, rasterio, np, mask, mapping)
                    full_receipts[product] = {
                        "url": url,
                        "sha256": sha256_bytes(data),
                        "bytes": len(data),
                        "content_type": headers.get("content-type"),
                        "measurement": measurement,
                    }
                item["full_polygon_rasters"] = full_receipts
                dtm = full_receipts["DTM_1M"]["measurement"]
                dsm = full_receipts["DSM_LZ_1M"]["measurement"]
                item["measurement_state"] = "OFFICIAL_BYTES_AND_GEOMETRY_MEASURED"
                item["candidate_height_difference_m"] = dtm["height_difference_m"]
                item["dsm_qa_height_range_m"] = dsm["height_difference_m"]

                candidate = {
                    "parcel_id": parcel_id,
                    "polygon_id": polygon_id,
                    "polygon_wkb_sha256": polygon_wkb_sha256,
                    "hmlr_gml_sha256": result["artifacts"]["hmlr_gml"]["sha256"],
                    "dtm_sha256": full_receipts["DTM_1M"]["sha256"],
                    "dsm_sha256": full_receipts["DSM_LZ_1M"]["sha256"],
                    "dtm_min_m_aod": dtm["min_m_aod"],
                    "dtm_max_m_aod": dtm["max_m_aod"],
                    "height_difference_m": dtm["height_difference_m"],
                    "dtm_robust_p95_minus_p05_m": dtm["robust_p95_minus_p05_m"],
                    "valid_dtm_pixel_count": dtm["valid_pixel_count"],
                    "evidence_state": "MEASURED_OFFICIAL_BYTES_BUSINESS_ROW_WITHHELD",
                    "business_row": False,
                }
                item["candidate"] = candidate
                try:
                    metadata = validate_survey_metadata_entry(parcel_id, survey_metadata.get(parcel_id))
                    candidate["survey_metadata"] = metadata
                    candidate["survey_metadata_sha256"] = sha256_json(metadata)
                    candidate["evidence_state"] = "VERIFIED_ALL_REQUIRED_GATES"
                    candidate["business_row"] = True
                    item["business_row"] = True
                except Exception as metadata_exc:
                    item["errors"].append(str(metadata_exc))
            except Exception as exc:
                item["errors"].append(str(exc))
            return item

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            processed = list(pool.map(process_example, examples))
        processed.sort(key=lambda row: row["slot_ordinal"])
        result["examples"] = processed
        for item in processed:
            candidate = item.get("candidate")
            if candidate:
                result["candidate_measurements"].append(candidate)
                if candidate.get("business_row") is True:
                    result["business_rows"].append(candidate)

        if result["business_rows"]:
            result["state"] = "COMPLETED_VERIFIED_ROWS_AVAILABLE"
        elif result["candidate_measurements"]:
            result["state"] = "COMPLETED_MEASUREMENTS_WITHHELD"
        else:
            result["state"] = "COMPLETED_NO_VERIFIED_MEASUREMENTS"
    except Exception as exc:
        result["state"] = "BLOCKED_FAIL_CLOSED"
        result["errors"].append(str(exc))
    finally:
        result["finished_at"] = utc_now()
        result["counts"] = {
            "prepared_examples": 11,
            "prepared_probe_requests": 22,
            "verified_probe_tiff_receipts": sum(
                1 for row in result.get("probe_receipts", [])
                if row.get("state") == "TIFF_BYTES_AND_CRS_VERIFIED"
            ),
            "unique_boundary_bindings": sum(
                1 for row in result["examples"]
                if row.get("boundary_state") == "UNIQUE_EXACT_POINT_IN_POLYGON"
            ),
            "candidate_measurements": len(result["candidate_measurements"]),
            "business_rows_written": len(result["business_rows"]),
        }
        atomic_json(runner_output, result)
        atomic_json(website_output, result)
        shutil.rmtree(workdir, ignore_errors=True)

    print(f"SLOT_ID={SLOT_ID}")
    print(f"SCRIPT_VERSION={SCRIPT_VERSION}")
    print(f"STATE={result['state']}")
    print(f"BUSINESS_ROWS_WRITTEN={len(result['business_rows'])}")
    print("FINAL_READY=false")
    return 2 if result["state"] == "BLOCKED_FAIL_CLOSED" else 0


if __name__ == "__main__":
    sys.exit(main())

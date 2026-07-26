#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html.parser
import io
import json
import math
import os
import re
import shutil
import tempfile
import urllib.parse
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests

SLOT_ID = "height_difference_3"
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
CANONICAL_BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
ONS_LAD25_QUERY = (
    "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
    "Local_Authority_Districts_DEC_2025_Boundaries_UK_BFC/FeatureServer/0/query"
)
HMLR_DOWNLOAD_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
EA_ALLOWED_HOSTS = {"environment.data.gov.uk"}
MAX_HTTP_BYTES = 300 * 1024 * 1024
MAX_ARCHIVE_FILES = 100
MAX_EXTRACTED_BYTES = 800 * 1024 * 1024
TIMEOUT = (20, 180)


class GateError(RuntimeError):
    pass


def now_z() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while chunk := fh.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: str | Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise GateError(f"INPUT_NOT_FOUND:{path}") from exc
    except json.JSONDecodeError as exc:
        raise GateError(f"INPUT_JSON_INVALID:{path}") from exc
    if not isinstance(value, dict):
        raise GateError(f"INPUT_ROOT_NOT_OBJECT:{path}")
    return value


def atomic_write_json(path: str | Path, value: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, target)


def finite_number(value: Any, code: str) -> float:
    if isinstance(value, bool):
        raise GateError(code + "_NOT_NUMERIC")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise GateError(code + "_NOT_NUMERIC") from exc
    if not math.isfinite(number):
        raise GateError(code + "_NOT_FINITE")
    return number


def exact_rows(payload: dict[str, Any], field: str, code: str) -> list[dict[str, Any]]:
    rows = payload.get(field)
    if not isinstance(rows, list) or len(rows) != 3 or any(not isinstance(row, dict) for row in rows):
        raise GateError(code + "_ROW_COUNT_NOT_3")
    if [row.get("parcel_id") for row in rows] != TARGET_IDS:
        raise GateError(code + "_PARCEL_ORDER_INVALID")
    return rows


def validate_dependencies(canonical: dict[str, Any], discovery: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    canonical_rows = exact_rows(canonical, "canonical_point_rows", "CANONICAL")
    if (canonical.get("canonical_blob_sha") or canonical.get("source_blob_sha")) != CANONICAL_BLOB_SHA:
        raise GateError("CANONICAL_BLOB_SHA_MISMATCH")
    if canonical.get("feature_count") not in (None, 92283):
        raise GateError("CANONICAL_FEATURE_COUNT_MISMATCH")
    discovery_rows = exact_rows(discovery, "parcel_rows", "DISCOVERY")
    for row in discovery_rows:
        finite_number(row.get("easting"), "EASTING")
        finite_number(row.get("northing"), "NORTHING")
        evidence = json.dumps(row.get("transformation") or discovery.get("transformation") or {}, sort_keys=True).upper()
        if "OSTN15" not in evidence and "7953" not in evidence:
            raise GateError("DISCOVERY_OSTN15_NOT_PROVEN")
        if "BALLPARK" in evidence or "HELMERT" in evidence:
            raise GateError("DISCOVERY_APPROX_TRANSFORM_REJECTED")
    return canonical_rows, discovery_rows


@dataclass(frozen=True)
class DownloadRow:
    authority_name: str
    url: str


class HmlrDownloadParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_tr = False
        self.in_td = False
        self.current_cell: list[str] = []
        self.cells: list[str] = []
        self.links: list[str] = []
        self.rows: list[DownloadRow] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self.in_tr = True
            self.cells = []
            self.links = []
        elif tag == "td" and self.in_tr:
            self.in_td = True
            self.current_cell = []
        elif tag == "a" and self.in_tr:
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_data(self, data: str) -> None:
        if self.in_td:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "td" and self.in_tr:
            self.cells.append(" ".join("".join(self.current_cell).split()))
            self.in_td = False
        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            if self.cells and self.links:
                authority = self.cells[0].strip()
                gml_links = [u for u in self.links if ".gml" in u.lower()]
                if authority and len(gml_links) == 1:
                    self.rows.append(DownloadRow(authority, gml_links[0]))
                elif authority and len(gml_links) > 1:
                    raise GateError("HMLR_DUPLICATE_DOWNLOAD_LINKS_FOR_ROW")


def parse_hmlr_download_rows(html_text: str, base_url: str = HMLR_DOWNLOAD_PAGE) -> list[DownloadRow]:
    parser = HmlrDownloadParser()
    parser.feed(html_text)
    rows = [DownloadRow(r.authority_name, urllib.parse.urljoin(base_url, r.url)) for r in parser.rows]
    if not rows:
        raise GateError("HMLR_DOWNLOAD_ROWS_EMPTY")
    names = [normalise_authority_name(row.authority_name) for row in rows]
    if len(names) != len(set(names)):
        raise GateError("HMLR_NORMALISED_AUTHORITY_DUPLICATE")
    return rows


def normalise_authority_name(name: str) -> str:
    text = name.casefold().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = " ".join(text.split())
    explicit = {
        "city of london corporation": "city of london",
        "city of westminster": "westminster",
        "royal borough of greenwich": "greenwich",
        "royal borough of kensington and chelsea": "kensington and chelsea",
        "royal borough of kingston upon thames": "kingston upon thames",
        "royal borough of windsor and maidenhead": "windsor and maidenhead",
        "the north yorkshire council": "north yorkshire",
        "hull city council": "kingston upon hull city of",
    }
    if text in explicit:
        return explicit[text]
    prefixes = ["london borough of ", "royal borough of ", "city of "]
    suffixes = [
        " metropolitan borough council", " metropolitan district council", " county borough council",
        " borough council", " district council", " city council", " county council", " council district council", " council",
    ]
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    for suffix in suffixes:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return " ".join(text.split())


def match_hmlr_authority(lad_name: str, rows: list[DownloadRow]) -> DownloadRow:
    target = normalise_authority_name(lad_name)
    matches = [row for row in rows if normalise_authority_name(row.authority_name) == target]
    if len(matches) != 1:
        raise GateError(f"HMLR_AUTHORITY_MATCH_COUNT_{len(matches)}:{lad_name}")
    return matches[0]


def request_json(session: requests.Session, url: str, *, params: dict[str, Any]) -> dict[str, Any]:
    response = session.get(url, params=params, timeout=TIMEOUT, headers={"Accept": "application/json"})
    response.raise_for_status()
    if len(response.content) > 10 * 1024 * 1024:
        raise GateError("JSON_RESPONSE_TOO_LARGE")
    try:
        payload = response.json()
    except ValueError as exc:
        raise GateError("JSON_RESPONSE_INVALID") from exc
    if not isinstance(payload, dict) or payload.get("error"):
        raise GateError("JSON_RESPONSE_ERROR")
    return payload


def resolve_lad(session: requests.Session, easting: float, northing: float, endpoint: str = ONS_LAD25_QUERY) -> dict[str, str]:
    payload = request_json(
        session,
        endpoint,
        params={
            "f": "json",
            "geometry": f"{easting},{northing}",
            "geometryType": "esriGeometryPoint",
            "inSR": 27700,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "LAD25CD,LAD25NM",
            "returnGeometry": "false",
        },
    )
    features = payload.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise GateError(f"ONS_LAD_MATCH_COUNT_{0 if not isinstance(features, list) else len(features)}")
    attrs = features[0].get("attributes") if isinstance(features[0], dict) else None
    if not isinstance(attrs, dict):
        raise GateError("ONS_LAD_ATTRIBUTES_MISSING")
    code, name = attrs.get("LAD25CD"), attrs.get("LAD25NM")
    if not isinstance(code, str) or not code.startswith("E") or not isinstance(name, str) or not name.strip():
        raise GateError("ONS_LAD_NOT_ENGLAND_OR_FIELDS_INVALID")
    return {"lad25_code": code, "lad25_name": name.strip()}


def download_bounded(session: requests.Session, url: str, *, allowed_hosts: set[str] | None = None) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise GateError("DOWNLOAD_URL_NOT_HTTPS")
    if allowed_hosts is not None and parsed.hostname.casefold() not in {h.casefold() for h in allowed_hosts}:
        raise GateError("DOWNLOAD_HOST_NOT_ALLOWED")
    response = session.get(url, timeout=TIMEOUT, stream=True, allow_redirects=True)
    response.raise_for_status()
    declared = response.headers.get("Content-Length")
    if declared and int(declared) > MAX_HTTP_BYTES:
        raise GateError("DOWNLOAD_DECLARED_TOO_LARGE")
    out = bytearray()
    for chunk in response.iter_content(1024 * 1024):
        if not chunk:
            continue
        out.extend(chunk)
        if len(out) > MAX_HTTP_BYTES:
            raise GateError("DOWNLOAD_STREAM_TOO_LARGE")
    if not out:
        raise GateError("DOWNLOAD_EMPTY")
    return bytes(out)


def safe_extract_single_tiff(data: bytes, directory: str | Path) -> Path:
    root = Path(directory).resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_ARCHIVE_FILES:
            raise GateError("ARCHIVE_TOO_MANY_FILES")
        total = sum(max(0, info.file_size) for info in infos)
        if total > MAX_EXTRACTED_BYTES:
            raise GateError("ARCHIVE_UNCOMPRESSED_TOO_LARGE")
        tif_paths: list[Path] = []
        for info in infos:
            destination = (root / info.filename).resolve()
            if root != destination and root not in destination.parents:
                raise GateError("ARCHIVE_PATH_TRAVERSAL")
            if info.is_dir():
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as src, destination.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            if destination.suffix.casefold() in {".tif", ".tiff"}:
                tif_paths.append(destination)
    if len(tif_paths) != 1:
        raise GateError(f"ARCHIVE_TIFF_COUNT_{len(tif_paths)}")
    return tif_paths[0]


def property_value(properties: dict[str, Any], candidates: Iterable[str]) -> str | None:
    normalised = {re.sub(r"[^a-z0-9]", "", str(k).casefold()): v for k, v in properties.items()}
    for candidate in candidates:
        value = normalised.get(re.sub(r"[^a-z0-9]", "", candidate.casefold()))
        if value not in (None, ""):
            return str(value)
    return None


def find_unique_hmlr_polygon(gml_path: str | Path, easting: float, northing: float) -> dict[str, Any]:
    import fiona
    from shapely.geometry import Point, mapping, shape

    point = Point(easting, northing)
    matches: dict[tuple[str, str], dict[str, Any]] = {}
    with fiona.open(gml_path) as source:
        epsg = source.crs.to_epsg() if source.crs else None
        if epsg != 27700:
            raise GateError("HMLR_GML_CRS_NOT_27700")
        for feature in source:
            geometry = shape(feature.get("geometry"))
            if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
                continue
            if not geometry.is_valid:
                raise GateError("HMLR_GML_GEOMETRY_INVALID")
            if not geometry.covers(point):
                continue
            props = dict(feature.get("properties") or {})
            inspire_id = property_value(props, ["INSPIREID", "INSPIRE_ID", "inspireId"])
            if not inspire_id:
                raise GateError("HMLR_INSPIRE_ID_MISSING")
            geometry_json = mapping(geometry)
            geom_sha = sha256_bytes(json.dumps(geometry_json, sort_keys=True, separators=(",", ":")).encode("utf-8"))
            matches[(inspire_id, geom_sha)] = {
                "inspire_id": inspire_id,
                "geometry_sha256": geom_sha,
                "polygon_geojson": geometry_json,
                "point_on_edge": geometry.boundary.covers(point),
                "area_m2": round(float(geometry.area), 3),
            }
    ids = {key[0] for key in matches}
    if len(ids) != 1:
        raise GateError(f"HMLR_UNIQUE_INSPIRE_ID_COUNT_{len(ids)}")
    selected = next(iter(matches.values()))
    return selected


def selected_dtm_candidate(discovery_row: dict[str, Any]) -> dict[str, Any]:
    layers = discovery_row.get("layers")
    if not isinstance(layers, dict) or not isinstance(layers.get("dtm"), dict):
        raise GateError("DISCOVERY_DTM_LAYER_MISSING")
    dtm = layers["dtm"]
    selected = dtm.get("selected_candidate") or dtm.get("selected")
    if not isinstance(selected, dict):
        candidates = dtm.get("candidates")
        if isinstance(candidates, list) and len(candidates) == 1 and isinstance(candidates[0], dict):
            selected = candidates[0]
        else:
            raise GateError("DISCOVERY_DTM_SELECTION_NOT_UNIQUE")
    return selected


def candidate_url(candidate: dict[str, Any]) -> str:
    for key in ("download_url", "filepath", "file_path", "url"):
        value = candidate.get(key)
        if isinstance(value, str) and value.startswith("https://"):
            return value
    raise GateError("DISCOVERY_DTM_DOWNLOAD_URL_MISSING")


def validate_raster(path: str | Path, candidate: dict[str, Any], easting: float, northing: float) -> dict[str, Any]:
    import rasterio

    with rasterio.open(path) as dataset:
        if dataset.count != 1 or not dataset.crs or dataset.crs.to_epsg() != 27700:
            raise GateError("DTM_DATASET_STRUCTURE_OR_CRS_INVALID")
        if not (dataset.bounds.left <= easting <= dataset.bounds.right and dataset.bounds.bottom <= northing <= dataset.bounds.top):
            raise GateError("DTM_POINT_OUTSIDE_BOUNDS")
        xres, yres = abs(dataset.transform.a), abs(dataset.transform.e)
        if abs(xres - yres) > 1e-6 or round(xres, 6) not in {0.25, 0.5, 1.0, 2.0}:
            raise GateError("DTM_PIXEL_SIZE_UNSUPPORTED")
        transform = str(candidate.get("transform") or candidate.get("transformation") or "").upper()
        geoid = str(candidate.get("geoid") or "").upper()
        if "OSTN15" not in transform and "27700" not in transform:
            raise GateError("DTM_TRANSFORM_LINEAGE_MISSING")
        if "OSGM15" not in geoid:
            raise GateError("DTM_GEOID_NOT_OSGM15")
        survey_date = candidate.get("to_date") or candidate.get("survey_date") or candidate.get("latest_survey")
        object_id = candidate.get("OBJECTID") or candidate.get("objectid") or candidate.get("catalog_object_id")
        if not survey_date or object_id is None:
            raise GateError("DTM_SURVEY_OR_OBJECT_ID_MISSING")
        return {
            "crs_epsg": 27700,
            "vertical_datum": "ODN",
            "geoid": str(candidate.get("geoid")),
            "transform": str(candidate.get("transform") or candidate.get("transformation")),
            "resolution_m": xres,
            "survey_date": str(survey_date),
            "catalog_object_id": object_id,
            "nodata": dataset.nodata,
            "width": dataset.width,
            "height": dataset.height,
            "bounds": [dataset.bounds.left, dataset.bounds.bottom, dataset.bounds.right, dataset.bounds.top],
        }


def run(args: argparse.Namespace) -> dict[str, Any]:
    canonical = read_json(args.canonical_points)
    discovery = read_json(args.official_discovery)
    _, discovery_rows = validate_dependencies(canonical, discovery)
    session = requests.Session()
    session.headers.update({"User-Agent": "AAYS-height-difference-3/1.0"})

    page = download_bounded(session, args.hmlr_download_page, allowed_hosts={"use-land-property-data.service.gov.uk"}).decode("utf-8")
    download_rows = parse_hmlr_download_rows(page, args.hmlr_download_page)

    work_root = Path(args.work_dir)
    work_root.mkdir(parents=True, exist_ok=True)
    boundary_rows: list[dict[str, Any]] = []
    raster_rows: list[dict[str, Any]] = []
    downloaded_gmls: dict[str, tuple[Path, str, str]] = {}

    for discovery_row in discovery_rows:
        parcel_id = discovery_row["parcel_id"]
        easting = finite_number(discovery_row.get("easting"), "EASTING")
        northing = finite_number(discovery_row.get("northing"), "NORTHING")
        lad = resolve_lad(session, easting, northing, args.ons_lad_query)
        hmlr = match_hmlr_authority(lad["lad25_name"], download_rows)
        cache_key = hmlr.url
        if cache_key not in downloaded_gmls:
            gml_bytes = download_bounded(session, hmlr.url, allowed_hosts={"use-land-property-data.service.gov.uk"})
            path = work_root / (hashlib.sha1(hmlr.url.encode("utf-8")).hexdigest() + ".gml")
            path.write_bytes(gml_bytes)
            downloaded_gmls[cache_key] = (path, sha256_bytes(gml_bytes), hmlr.authority_name)
        gml_path, gml_sha, authority_name = downloaded_gmls[cache_key]
        polygon = find_unique_hmlr_polygon(gml_path, easting, northing)
        boundary_rows.append({
            "parcel_id": parcel_id,
            "lad25_code": lad["lad25_code"],
            "lad25_name": lad["lad25_name"],
            "hmlr_authority_name": authority_name,
            "source_url": hmlr.url,
            "source_file_sha256": gml_sha,
            "source_crs_epsg": 27700,
            "inspire_id": polygon["inspire_id"],
            "geometry_sha256": polygon["geometry_sha256"],
            "polygon_geojson": polygon["polygon_geojson"],
            "point_on_edge": polygon["point_on_edge"],
            "area_m2": polygon["area_m2"],
            "boundary_semantics": "GENERAL_BOUNDARY",
            "determined_boundary_evidence": None,
        })

        candidate = selected_dtm_candidate(discovery_row)
        url = candidate_url(candidate)
        raster_bytes = download_bounded(session, url, allowed_hosts=EA_ALLOWED_HOSTS)
        raster_work = work_root / parcel_id
        raster_work.mkdir(exist_ok=True)
        if raster_bytes[:4] == b"PK\x03\x04":
            tif_path = safe_extract_single_tiff(raster_bytes, raster_work)
            archive_sha = sha256_bytes(raster_bytes)
        else:
            tif_path = raster_work / "selected_dtm.tif"
            tif_path.write_bytes(raster_bytes)
            archive_sha = None
        metadata = validate_raster(tif_path, candidate, easting, northing)
        raster_rows.append({
            "parcel_id": parcel_id,
            "product": "EA_LIDAR_DTM_TIME_STAMPED",
            "download_url": url,
            "archive_sha256": archive_sha,
            "dtm_path": str(tif_path),
            "dtm_sha256": sha256_file(tif_path),
            **metadata,
        })

    release = {
        "download_page": args.hmlr_download_page,
        "page_sha256": sha256_bytes(page.encode("utf-8")),
        "published_at": args.hmlr_release_date,
        "manifest_sha256": sha256_bytes(json.dumps(boundary_rows, sort_keys=True, separators=(",", ":")).encode("utf-8")),
    }
    boundary_manifest = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "generated_at": now_z(),
        "release": release,
        "rows": boundary_rows,
        "row_count": len(boundary_rows),
        "boundary_semantics": "GENERAL_BOUNDARY_ONLY",
        "fake_data": False,
        "final_ready": False,
    }
    raster_manifest = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "generated_at": now_z(),
        "rows": raster_rows,
        "row_count": len(raster_rows),
        "fake_data": False,
        "final_ready": False,
    }
    atomic_write_json(args.boundary_manifest, boundary_manifest)
    atomic_write_json(args.raster_manifest, raster_manifest)
    return {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "task_id": "height-difference-3-official-input-manifest-v1-20260722",
        "generated_at": now_z(),
        "state": "OFFICIAL_INPUT_MANIFESTS_READY_NONFINAL",
        "boundary_rows": len(boundary_rows),
        "raster_rows": len(raster_rows),
        "boundary_manifest": args.boundary_manifest,
        "raster_manifest": args.raster_manifest,
        "actual_business_data_rows_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-points", required=True)
    parser.add_argument("--official-discovery", required=True)
    parser.add_argument("--boundary-manifest", required=True)
    parser.add_argument("--raster-manifest", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--website-report", required=True)
    parser.add_argument("--work-dir", required=True)
    parser.add_argument("--hmlr-download-page", default=HMLR_DOWNLOAD_PAGE)
    parser.add_argument("--hmlr-release-date", default="2026-07-05")
    parser.add_argument("--ons-lad-query", default=ONS_LAD25_QUERY)
    parser.add_argument("--expected-blob-sha", default=CANONICAL_BLOB_SHA)
    args = parser.parse_args()
    if args.expected_blob_sha != CANONICAL_BLOB_SHA:
        raise SystemExit("EXPECTED_BLOB_SHA_MISMATCH")
    try:
        result = run(args)
        code = 0
    except Exception as exc:
        result = {
            "schema_version": 1,
            "slot_id": SLOT_ID,
            "task_id": "height-difference-3-official-input-manifest-v1-20260722",
            "generated_at": now_z(),
            "state": "BLOCKED_FAIL_CLOSED",
            "error": type(exc).__name__ + ":" + str(exc),
            "boundary_rows": 0,
            "raster_rows": 0,
            "actual_business_data_rows_written": 0,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
            "final_ready": False,
        }
        code = 2
    atomic_write_json(args.report, result)
    atomic_write_json(args.website_report, result)
    return code


if __name__ == "__main__":
    raise SystemExit(main())

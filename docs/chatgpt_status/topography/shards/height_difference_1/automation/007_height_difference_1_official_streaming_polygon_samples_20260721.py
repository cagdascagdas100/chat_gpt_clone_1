#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import hashlib
import html
import json
import math
import os
import re
import statistics
import tempfile
import time
import urllib.parse
import zipfile
from pathlib import Path
from typing import Any, Optional
from xml.etree import ElementTree as ET

try:
    import requests
except Exception as exc:
    raise SystemExit(f"requests_required:{exc}")

try:
    import rasterio
    from rasterio.mask import mask as raster_mask
except Exception:
    rasterio = None
    raster_mask = None

try:
    from shapely.geometry import Polygon, mapping
except Exception:
    Polygon = None
    mapping = None

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
SLOT = "height_difference_1"
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
ATTEMPT_ID = "official-source-batch-004-revision-5-streaming-polygon"
CANDIDATES = [
    {"parcel_id": "parcel_2759", "parcel_ref": "52040420", "easting": 528658.656, "northing": 192535.809},
    {"parcel_id": "parcel_2758", "parcel_ref": "52213916", "easting": 528747.982, "northing": 192527.698},
    {"parcel_id": "parcel_2757", "parcel_ref": "52213412", "easting": 528723.664, "northing": 192513.392},
]
HMLR_INDEX = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
HMLR_WFS = "https://inspire.landregistry.gov.uk/inspire/ows"
EA_WCS = {
    "1m": "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs",
    "2m": "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-2m/wcs",
    "10m": "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-10m/wcs",
}
EA_SURVEY = "https://environment.data.gov.uk/survey"
OS_TERRAIN50 = (
    "https://api.os.uk/downloads/v1/products/Terrain50/downloads"
    "?area=GB&format=ASCII%20Grid%20and%20GML%20(Grid)&redirect"
)
OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/007_official_streaming_polygon_samples_latest.json"
WEB_OUT = REPO / "england_map_web/data/aays_21_slots/height_difference_1/official_streaming_polygon_samples_latest.json"
REPORT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/reports/010_height_difference_1_official_streaming_polygon_samples_result.md"
USER_AGENT = "AAYS-TerraYield/height_difference_1 official-evidence-only"
TIMEOUT = (20, 240)
MAX_HMLR_BYTES = 40 * 1024 * 1024
MAX_EA_BYTES = 80 * 1024 * 1024
MAX_OS_BYTES = 220 * 1024 * 1024
MAX_WORKERS = 3
CONFLICT_TOLERANCE_M = 8.0


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fetch_text(session: requests.Session, url: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    started = time.time()
    try:
        r = session.get(url, params=params, timeout=TIMEOUT, allow_redirects=True, headers={"User-Agent": USER_AGENT})
        return {
            "ok": r.ok,
            "status": r.status_code,
            "url": r.url,
            "text": r.text if r.ok else r.text[:4000],
            "content_type": r.headers.get("content-type", ""),
            "elapsed_s": round(time.time() - started, 3),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}:{exc}", "url": url, "elapsed_s": round(time.time() - started, 3)}


def stream_download(session: requests.Session, url: str, dest: Path, max_bytes: int, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    total = 0
    h = hashlib.sha256()
    try:
        with session.get(
            url, params=params, timeout=TIMEOUT, allow_redirects=True, stream=True,
            headers={"User-Agent": USER_AGENT}
        ) as r:
            if not r.ok:
                return {"ok": False, "status": r.status_code, "url": r.url, "error": r.text[:2000]}
            declared = r.headers.get("content-length")
            if declared and int(declared) > max_bytes:
                return {"ok": False, "status": r.status_code, "url": r.url, "error": "content_length_over_budget", "declared_bytes": int(declared), "max_bytes": max_bytes}
            with dest.open("wb") as fh:
                for chunk in r.iter_content(1024 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > max_bytes:
                        fh.close()
                        dest.unlink(missing_ok=True)
                        return {"ok": False, "status": r.status_code, "url": r.url, "error": "stream_over_budget", "bytes": total, "max_bytes": max_bytes}
                    fh.write(chunk)
                    h.update(chunk)
            return {
                "ok": True,
                "status": r.status_code,
                "url": r.url,
                "bytes": total,
                "sha256": h.hexdigest(),
                "content_type": r.headers.get("content-type", ""),
                "elapsed_s": round(time.time() - started, 3),
                "path": str(dest),
            }
    except Exception as exc:
        dest.unlink(missing_ok=True)
        return {"ok": False, "url": url, "error": f"{type(exc).__name__}:{exc}", "elapsed_s": round(time.time() - started, 3)}


def normalize_href(base: str, href: str) -> str:
    return urllib.parse.urljoin(base, html.unescape(href))


def discover_authority_links(page: str, base_url: str) -> dict[str, str]:
    wanted = {
        "barnet": "London Borough of Barnet",
        "enfield": "London Borough of Enfield",
    }
    links: dict[str, str] = {}
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page, "html.parser")
        for key, label in wanted.items():
            node = soup.find(string=lambda s: bool(s and label.lower() in s.lower()))
            if node:
                parent = node.parent
                for _ in range(5):
                    if parent is None:
                        break
                    a = parent.find("a", href=True)
                    if a:
                        links[key] = normalize_href(base_url, a["href"])
                        break
                    parent = parent.parent
    except Exception:
        pass
    for key, label in wanted.items():
        if key in links:
            continue
        idx = page.lower().find(label.lower())
        if idx >= 0:
            window = page[max(0, idx - 600): idx + 1200]
            hrefs = re.findall(r'href=["\']([^"\']+)["\']', window, flags=re.I)
            gml = next((h for h in hrefs if ".gml" in h.lower() or "download" in h.lower()), None)
            if gml:
                links[key] = normalize_href(base_url, gml)
    for href in re.findall(r'href=["\']([^"\']+)["\']', page, flags=re.I):
        low = href.lower()
        for key in wanted:
            if key not in links and key in low and (".gml" in low or "download" in low):
                links[key] = normalize_href(base_url, href)
    return links


def parse_poslist(text: str) -> list[tuple[float, float]]:
    vals = []
    for token in re.split(r"[\s,]+", (text or "").strip()):
        if not token:
            continue
        try:
            vals.append(float(token))
        except ValueError:
            return []
    if len(vals) < 6:
        return []
    if len(vals) % 2:
        vals = vals[:-1]
    return [(vals[i], vals[i + 1]) for i in range(0, len(vals), 2)]


def ring_contains(coords: list[tuple[float, float]], x: float, y: float) -> bool:
    if len(coords) < 3:
        return False
    inside = False
    j = len(coords) - 1
    for i in range(len(coords)):
        xi, yi = coords[i]
        xj, yj = coords[j]
        if ((yi > y) != (yj > y)) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-30) + xi:
            inside = not inside
        j = i
    return inside


def polygon_area(coords: list[tuple[float, float]]) -> float:
    if len(coords) < 3:
        return 0.0
    return abs(sum(coords[i][0] * coords[(i + 1) % len(coords)][1] - coords[(i + 1) % len(coords)][0] * coords[i][1] for i in range(len(coords))) / 2.0)


def extract_feature_id(elem: ET.Element) -> Optional[str]:
    for node in elem.iter():
        name = local_name(node.tag)
        if "inspireid" in name or name in {"localid", "nationalcadastralreference", "label"}:
            text = (node.text or "").strip()
            if text:
                return text
        for k, v in node.attrib.items():
            if "id" in local_name(k) and v:
                return v
    return None


def parse_gml_matches(path: Path) -> dict[str, Any]:
    matches = {c["parcel_id"]: None for c in CANDIDATES}
    features_scanned = 0
    rings_scanned = 0
    try:
        context = ET.iterparse(path, events=("end",))
        for _, elem in context:
            lname = local_name(elem.tag)
            if lname not in {"featuremember", "member", "cadastralparcel"}:
                continue
            rings: list[list[tuple[float, float]]] = []
            for node in elem.iter():
                if local_name(node.tag) in {"poslist", "coordinates"}:
                    ring = parse_poslist(node.text or "")
                    if len(ring) >= 3:
                        rings.append(ring)
            if not rings:
                elem.clear()
                continue
            features_scanned += 1
            rings_scanned += len(rings)
            feature_id = extract_feature_id(elem)
            for c in CANDIDATES:
                if matches[c["parcel_id"]] is not None:
                    continue
                for ring in rings:
                    if ring_contains(ring, c["easting"], c["northing"]):
                        xs = [p[0] for p in ring]
                        ys = [p[1] for p in ring]
                        matches[c["parcel_id"]] = {
                            "match": True,
                            "source": "HMLR_INSPIRE_GML",
                            "inspire_id": feature_id,
                            "ring": [[round(x, 3), round(y, 3)] for x, y in ring],
                            "ring_points": len(ring),
                            "area_m2": round(polygon_area(ring), 3),
                            "bbox": [min(xs), min(ys), max(xs), max(ys)],
                        }
                        break
            elem.clear()
            if all(matches.values()):
                break
        return {"ok": True, "matches": matches, "features_scanned": features_scanned, "rings_scanned": rings_scanned}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}:{exc}", "matches": matches, "features_scanned": features_scanned, "rings_scanned": rings_scanned}


def hmlr_bulk_job(tmp: Path) -> dict[str, Any]:
    session = requests.Session()
    page = fetch_text(session, HMLR_INDEX)
    result: dict[str, Any] = {"index": {k: v for k, v in page.items() if k != "text"}, "authorities": {}, "matches": {c["parcel_id"]: None for c in CANDIDATES}}
    if not page.get("ok"):
        result["error"] = "hmlr_index_fetch_failed"
        return result
    links = discover_authority_links(page["text"], page["url"])
    result["discovered_links"] = links
    for authority in ("barnet", "enfield"):
        url = links.get(authority)
        if not url:
            result["authorities"][authority] = {"ok": False, "error": "authority_link_not_discovered"}
            continue
        dest = tmp / f"hmlr_{authority}.gml"
        dl = stream_download(session, url, dest, MAX_HMLR_BYTES)
        if dl.get("ok"):
            parsed = parse_gml_matches(dest)
            dl["parse"] = {k: v for k, v in parsed.items() if k != "matches"}
            for pid, match in parsed["matches"].items():
                if match and result["matches"][pid] is None:
                    match["authority"] = authority
                    match["source_sha256"] = dl["sha256"]
                    result["matches"][pid] = match
        result["authorities"][authority] = dl
    result["ok"] = any(result["matches"].values())
    return result


def parse_wfs_bytes(data: bytes, dest: Path) -> dict[str, Any]:
    dest.write_bytes(data)
    return parse_gml_matches(dest)


def hmlr_wfs_job(tmp: Path) -> dict[str, Any]:
    session = requests.Session()
    minx = min(c["easting"] for c in CANDIDATES) - 40
    maxx = max(c["easting"] for c in CANDIDATES) + 40
    miny = min(c["northing"] for c in CANDIDATES) - 40
    maxy = max(c["northing"] for c in CANDIDATES) + 40
    attempts = []
    merged = {c["parcel_id"]: None for c in CANDIDATES}
    for version in ("2.0.0", "1.1.0", "1.0.0"):
        for typename in ("inspire:CP.CadastralParcel", "CP.CadastralParcel", "inspire:CadastralParcel"):
            params = {
                "service": "WFS", "version": version, "request": "GetFeature",
                "typeNames" if version == "2.0.0" else "typeName": typename,
                "srsName": "EPSG:27700",
                "bbox": f"{minx},{miny},{maxx},{maxy},EPSG:27700",
                "count" if version == "2.0.0" else "maxFeatures": "500",
            }
            try:
                r = session.get(HMLR_WFS, params=params, timeout=TIMEOUT, allow_redirects=True, headers={"User-Agent": USER_AGENT})
                att = {"version": version, "typename": typename, "status": r.status_code, "url": r.url, "bytes": len(r.content), "content_type": r.headers.get("content-type", "")}
                if r.ok and b"<" in r.content[:200]:
                    parsed = parse_wfs_bytes(r.content, tmp / f"wfs_{version.replace('.','_')}_{typename.replace(':','_').replace('.','_')}.gml")
                    att["parse"] = {k: v for k, v in parsed.items() if k != "matches"}
                    for pid, match in parsed["matches"].items():
                        if match and merged[pid] is None:
                            match["source"] = "HMLR_INSPIRE_WFS"
                            match["response_sha256"] = hashlib.sha256(r.content).hexdigest()
                            merged[pid] = match
                attempts.append(att)
                if all(merged.values()):
                    return {"ok": True, "matches": merged, "attempts": attempts}
            except Exception as exc:
                attempts.append({"version": version, "typename": typename, "error": f"{type(exc).__name__}:{exc}"})
    return {"ok": any(merged.values()), "matches": merged, "attempts": attempts}


def coverage_ids(xml_text: str) -> list[str]:
    ids: list[str] = []
    try:
        root = ET.fromstring(xml_text)
        for node in root.iter():
            if local_name(node.tag) in {"coverageid", "identifier", "name"}:
                text = (node.text or "").strip()
                if text and text not in ids and len(text) < 300:
                    ids.append(text)
    except Exception:
        pass
    return ids[:30]


def wcs_download_resolution(label: str, url: str, tmp: Path) -> dict[str, Any]:
    session = requests.Session()
    cap = fetch_text(session, url, {"service": "WCS", "request": "GetCapabilities", "version": "2.0.1"})
    result = {"resolution": label, "capabilities": {k: v for k, v in cap.items() if k != "text"}, "attempts": []}
    if not cap.get("ok"):
        result["ok"] = False
        return result
    ids = coverage_ids(cap["text"])
    result["coverage_ids"] = ids
    if not ids:
        result["ok"] = False
        result["error"] = "coverage_id_missing"
        return result
    minx = min(c["easting"] for c in CANDIDATES) - 30
    maxx = max(c["easting"] for c in CANDIDATES) + 30
    miny = min(c["northing"] for c in CANDIDATES) - 30
    maxy = max(c["northing"] for c in CANDIDATES) + 30
    axes = [("E", "N"), ("easting", "northing"), ("x", "y"), ("X", "Y")]
    for cid in ids[:8]:
        for ax, ay in axes:
            params = [
                ("service", "WCS"), ("version", "2.0.1"), ("request", "GetCoverage"),
                ("coverageId", cid), ("format", "image/tiff"),
                ("subset", f"{ax}({minx},{maxx})"), ("subset", f"{ay}({miny},{maxy})"),
            ]
            dest = tmp / f"ea_{label}_{len(result['attempts'])}.tif"
            dl = stream_download(session, url, dest, MAX_EA_BYTES, params=params)
            result["attempts"].append({"coverage_id": cid, "axes": [ax, ay], **dl})
            if dl.get("ok") and dl.get("bytes", 0) > 1000:
                magic = dest.read_bytes()[:4]
                if magic not in (b"II*\x00", b"MM\x00*"):
                    result["attempts"][-1]["error"] = "response_not_tiff"
                    dest.unlink(missing_ok=True)
                    continue
                result["ok"] = True
                result["selected_path"] = str(dest)
                result["selected_sha256"] = dl["sha256"]
                result["selected_coverage_id"] = cid
                result["selected_axes"] = [ax, ay]
                return result
    result["ok"] = False
    return result


def survey_tile_job(tmp: Path) -> dict[str, Any]:
    session = requests.Session()
    attempts = []
    candidates = [
        (EA_SURVEY, {"gridRef": "TQ29SE"}),
        (EA_SURVEY, {"gridref": "TQ29SE"}),
        (EA_SURVEY, {"search": "TQ29SE DTM 1m"}),
        (EA_SURVEY + "/download", {"gridRef": "TQ29SE", "product": "DTM", "resolution": "1m"}),
    ]
    links: list[str] = []
    for url, params in candidates:
        page = fetch_text(session, url, params)
        attempts.append({k: v for k, v in page.items() if k != "text"})
        if not page.get("ok"):
            continue
        for href in re.findall(r'href=["\']([^"\']+)["\']', page["text"], flags=re.I):
            full = normalize_href(page["url"], href)
            low = full.lower()
            if "tq29se" in low and any(ext in low for ext in (".tif", ".tiff", ".zip")):
                links.append(full)
    links = list(dict.fromkeys(links))
    for i, link in enumerate(links[:10]):
        dest = tmp / f"ea_survey_tq29se_{i}{'.zip' if '.zip' in link.lower() else '.tif'}"
        dl = stream_download(session, link, dest, MAX_EA_BYTES)
        if dl.get("ok"):
            selected = dest
            if zipfile.is_zipfile(dest):
                with zipfile.ZipFile(dest) as zf:
                    tif_names = [n for n in zf.namelist() if n.lower().endswith((".tif", ".tiff")) and "tq29se" in n.lower()]
                    if not tif_names:
                        tif_names = [n for n in zf.namelist() if n.lower().endswith((".tif", ".tiff"))]
                    if not tif_names:
                        continue
                    member = sorted(tif_names, key=len)[0]
                    selected = tmp / "ea_survey_tq29se_1m.tif"
                    with zf.open(member) as src, selected.open("wb") as dst:
                        while True:
                            block = src.read(1024 * 1024)
                            if not block:
                                break
                            dst.write(block)
            return {
                "ok": True,
                "attempts": attempts,
                "discovered_links": links,
                "download": dl,
                "selected_path": str(selected),
                "selected_sha256": sha256_path(selected),
            }
    return {"ok": False, "attempts": attempts, "discovered_links": links}


def os_job(tmp: Path) -> dict[str, Any]:
    session = requests.Session()
    archive = tmp / "os_terrain50_gb.zip"
    dl = stream_download(session, OS_TERRAIN50, archive, MAX_OS_BYTES)
    result: dict[str, Any] = {"download": dl}
    if not dl.get("ok"):
        result["ok"] = False
        return result
    try:
        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
            candidates = [n for n in names if Path(n).name.lower() == "tq29.asc"]
            if not candidates:
                candidates = [n for n in names if "tq29" in Path(n).name.lower() and n.lower().endswith(".asc")]
            if not candidates:
                result.update({"ok": False, "error": "TQ29_ASC_NOT_FOUND", "archive_members": len(names)})
                return result
            member = sorted(candidates, key=len)[0]
            asc = tmp / "tq29.asc"
            with zf.open(member) as src, asc.open("wb") as dst:
                while True:
                    block = src.read(1024 * 1024)
                    if not block:
                        break
                    dst.write(block)
            samples, header = sample_ascii_grid(asc)
            result.update({
                "ok": all(v.get("ok") for v in samples.values()),
                "member": member,
                "archive_members": len(names),
                "ascii_sha256": sha256_path(asc),
                "header": header,
                "samples": samples,
            })
            return result
    except Exception as exc:
        result.update({"ok": False, "error": f"{type(exc).__name__}:{exc}"})
        return result


def sample_ascii_grid(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        header: dict[str, float] = {}
        for _ in range(6):
            parts = fh.readline().strip().split()
            if len(parts) >= 2:
                header[parts[0].lower()] = float(parts[1])
        ncols = int(header["ncols"])
        nrows = int(header["nrows"])
        xll = header.get("xllcorner", header.get("xllcenter"))
        yll = header.get("yllcorner", header.get("yllcenter"))
        cell = header["cellsize"]
        rows = []
        for _ in range(nrows):
            vals = [float(v) for v in fh.readline().split()]
            if len(vals) != ncols:
                raise ValueError("ascii_grid_row_length_mismatch")
            rows.append(vals)
    out: dict[str, Any] = {}
    for c in CANDIDATES:
        col = int(math.floor((c["easting"] - xll) / cell))
        bottom_row = int(math.floor((c["northing"] - yll) / cell))
        row = nrows - 1 - bottom_row
        if 0 <= row < nrows and 0 <= col < ncols:
            value = rows[row][col]
            out[c["parcel_id"]] = {"ok": True, "elevation_m": value, "row": row, "col": col}
        else:
            out[c["parcel_id"]] = {"ok": False, "error": "coordinate_outside_ascii_grid", "row": row, "col": col}
    return out, header


def raster_stats(path: Path, boundaries: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if rasterio is None or Polygon is None or raster_mask is None:
        return {c["parcel_id"]: {"ok": False, "error": "rasterio_or_shapely_missing"} for c in CANDIDATES}
    try:
        with rasterio.open(path) as ds:
            for c in CANDIDATES:
                boundary = boundaries.get(c["parcel_id"])
                if not boundary or not boundary.get("match") or not boundary.get("ring"):
                    out[c["parcel_id"]] = {"ok": False, "error": "real_hmlr_polygon_missing"}
                    continue
                poly = Polygon(boundary["ring"])
                try:
                    arr, _ = raster_mask(ds, [mapping(poly)], crop=True, filled=False)
                    values = arr[0].compressed().tolist()
                    values = [float(v) for v in values if math.isfinite(float(v))]
                except Exception as exc:
                    out[c["parcel_id"]] = {"ok": False, "error": f"polygon_mask_failed:{type(exc).__name__}:{exc}"}
                    continue
                if not values:
                    out[c["parcel_id"]] = {"ok": False, "error": "no_valid_pixels_in_polygon"}
                    continue
                ordered = sorted(values)
                q1 = ordered[max(0, int((len(ordered) - 1) * 0.25))]
                q3 = ordered[max(0, int((len(ordered) - 1) * 0.75))]
                out[c["parcel_id"]] = {
                    "ok": True,
                    "pixel_count": len(values),
                    "median_m": round(statistics.median(values), 3),
                    "min_m": round(min(values), 3),
                    "max_m": round(max(values), 3),
                    "iqr_m": round(q3 - q1, 3),
                    "crs": str(ds.crs),
                    "resolution": [abs(ds.transform.a), abs(ds.transform.e)],
                }
        return out
    except Exception as exc:
        return {c["parcel_id"]: {"ok": False, "error": f"raster_open_failed:{type(exc).__name__}:{exc}"} for c in CANDIDATES}


def combine_boundaries(bulk: dict[str, Any], wfs: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for c in CANDIDATES:
        pid = c["parcel_id"]
        out[pid] = bulk.get("matches", {}).get(pid) or wfs.get("matches", {}).get(pid)
    return out


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    WEB_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="aays_hd1_rev5_") as td:
        tmp = Path(td)
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            hmlr_bulk_f = ex.submit(hmlr_bulk_job, tmp)
            hmlr_wfs_f = ex.submit(hmlr_wfs_job, tmp)
            os_f = ex.submit(os_job, tmp)
            hmlr_bulk = hmlr_bulk_f.result()
            hmlr_wfs = hmlr_wfs_f.result()
            os_result = os_f.result()

        boundaries = combine_boundaries(hmlr_bulk, hmlr_wfs)
        ea_results = {}
        for label, url in EA_WCS.items():
            ea_results[label] = wcs_download_resolution(label, url, tmp)
        if not ea_results["1m"].get("ok"):
            survey = survey_tile_job(tmp)
            ea_results["survey_TQ29SE"] = survey
            if survey.get("ok") and survey.get("selected_path"):
                ea_results["1m"]["ok"] = True
                ea_results["1m"]["fallback_source"] = "EA_SURVEY_TQ29SE_5KM_GEOTIFF"
                ea_results["1m"]["selected_path"] = survey["selected_path"]
                ea_results["1m"]["selected_sha256"] = survey.get("selected_sha256")

        ea_stats = {}
        for label in ("1m", "2m", "10m"):
            selected = ea_results[label].get("selected_path")
            ea_stats[label] = raster_stats(Path(selected), boundaries) if selected else {
                c["parcel_id"]: {"ok": False, "error": "official_raster_not_downloaded"} for c in CANDIDATES
            }

        rows = []
        measured = 0
        boundary_count = 0
        ea_count = 0
        os_count = 0
        for c in CANDIDATES:
            pid = c["parcel_id"]
            boundary = boundaries.get(pid)
            ea1 = ea_stats["1m"].get(pid, {})
            os_sample = os_result.get("samples", {}).get(pid, {})
            boundary_ok = bool(boundary and boundary.get("match"))
            ea_ok = bool(ea1.get("ok"))
            os_ok = bool(os_sample.get("ok"))
            boundary_count += int(boundary_ok)
            ea_count += int(ea_ok)
            os_count += int(os_ok)
            diff = None
            conflict = False
            if ea_ok and os_ok:
                diff = round(abs(float(ea1["median_m"]) - float(os_sample["elevation_m"])), 3)
                conflict = diff > CONFLICT_TOLERANCE_M
            accepted = boundary_ok and ea_ok and os_ok and not conflict
            if accepted:
                measured += 1
                semantics = "MEASURED_OFFICIAL_THREE_SOURCE"
                accuracy = "3.5/4"
            elif boundary_ok and ea_ok and not os_ok:
                semantics = "CANDIDATE_OFFICIAL_PRIMARY_NOT_INDEPENDENT_TWO_SOURCE"
                accuracy = "3.0/4 provisional_not_measured"
            elif conflict:
                semantics = "HUMAN_REVIEW_SOURCE_CONFLICT"
                accuracy = "2.5/4 not_measured"
            else:
                semantics = "NO_DATA_NOT_INFERRED"
                accuracy = "2.5/4 fallback"
            rows.append({
                **c,
                "boundary": boundary or {"match": False, "error": "real_hmlr_polygon_missing"},
                "ea_dtm_1m_polygon": ea1,
                "ea_dtm_2m_polygon": ea_stats["2m"].get(pid, {}),
                "ea_dtm_10m_polygon": ea_stats["10m"].get(pid, {}),
                "os_terrain50": os_sample,
                "ea_vs_os_abs_difference_m": diff,
                "human_review_required": conflict,
                "accepted_measured_row": accepted,
                "output_semantics": semantics,
                "accuracy_score_4": accuracy,
            })

        result = {
            "schema_version": 5,
            "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
            "slot_id": SLOT,
            "task_id": TASK_ID,
            "attempt_id": ATTEMPT_ID,
            "payload_revision": 5,
            "status": "MEASURED_OFFICIAL_ROWS_AVAILABLE" if measured else "NO_DATA_NOT_INFERRED",
            "source_contracts": {
                "hmlr": {"monthly_gml_average_size_mb": 13.66, "api_available": False, "publication_date": "2026-07-05"},
                "ea": {"dtm_1m_coverage": "approximately_99_percent_england", "persistent_wcs": True, "shared_fallback_tile": "TQ29SE"},
                "os": {"version_date": "2026-07", "tile": "TQ29", "grid_cells": [200, 200], "cellsize_m": 50, "height_precision_m": 0.1, "stream_budget_bytes": MAX_OS_BYTES},
            },
            "execution": {
                "max_concurrent_source_families": MAX_WORKERS,
                "downloads_streamed_to_disk": True,
                "elapsed_s": round(time.time() - started, 3),
            },
            "source_results": {
                "hmlr_bulk": hmlr_bulk,
                "hmlr_wfs": hmlr_wfs,
                "ea": ea_results,
                "os_terrain50": os_result,
            },
            "counts": {
                "candidate_rows": len(CANDIDATES),
                "real_boundary_matches": boundary_count,
                "ea_1m_polygon_numeric_rows": ea_count,
                "os_terrain50_numeric_rows": os_count,
                "official_three_source_measured_rows": measured,
            },
            "rows": rows,
            "acceptance": {
                "requires_real_hmlr_polygon": True,
                "requires_ea_1m_polygon_numeric": True,
                "requires_independent_os_terrain50_numeric": True,
                "ea_vs_os_tolerance_m": CONFLICT_TOLERANCE_M,
                "centroid_only_promotion_forbidden": True,
                "no_data_policy": "NO_DATA_NOT_INFERRED",
            },
            "final_ready": False,
            "product_final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        text = json.dumps(result, ensure_ascii=False, indent=2)
        OUT.write_text(text, encoding="utf-8")
        WEB_OUT.write_text(text, encoding="utf-8")
        REPORT.write_text(
            "# Height Difference 1 revision 5 official streaming polygon result\n\n"
            f"- Status: `{result['status']}`\n"
            f"- Candidates: `{len(CANDIDATES)}`\n"
            f"- Real HMLR boundary matches: `{boundary_count}`\n"
            f"- EA 1m polygon numeric rows: `{ea_count}`\n"
            f"- OS Terrain 50 numeric rows: `{os_count}`\n"
            f"- Accepted official three-source measured rows: `{measured}`\n"
            "- `final_ready=false`\n"
            "- No centroid-only or inferred parcel value is promoted.\n",
            encoding="utf-8",
        )
    print(json.dumps({"status": result["status"], "counts": result["counts"], "output": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
import requests
from shapely.geometry import Point, shape

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
SLOT = "height_difference_1"
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
PAYLOAD_REVISION = 13
ATTEMPT_ID = "official-source-batch-004-revision-13-direct-os-terrain50-crosscheck"
IDEMPOTENCY_KEY = "height_difference_1-004-20260720"
SCRIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_1/automation/038_height_difference_1_revision_13_direct_os_terrain50_crosscheck_20260721.py"
REV12_ENTRY = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/035_height_difference_1_revision_12_direct_ea_pixel_center_resample_20260721.py"
REV12_OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/014_revision_12_direct_ea_pixel_center_resample_latest.json"
REV10_MODULE = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/027_height_difference_1_revision_10_explicit_identity_evidence_gate_20260721.py"
REV11_MODULE = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/automation/032_height_difference_1_revision_11_pixel_center_sampling_provenance_20260721.py"
OUT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/015_revision_13_direct_os_terrain50_crosscheck_latest.json"
WEB_OUT = REPO / "england_map_web/data/aays_21_slots/height_difference_1/revision_13_direct_os_terrain50_crosscheck_latest.json"
SNAPSHOT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/015_revision_13_direct_os_terrain50_crosscheck_manifest_latest.json"
REPORT = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/reports/020_height_difference_1_revision_13_direct_os_terrain50_crosscheck_result.md"
WORK = REPO / "docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/015_revision_13_os_work"
API_BASE = os.environ.get("AAYS_OS_DOWNLOADS_API_BASE", "https://api.os.uk/downloads/v1").rstrip("/")
MAX_DOWNLOAD_BYTES = 2_500_000_000
MAX_MEMBER_BYTES = 20_000_000
MAX_EXTRACTED_BYTES = 600_000_000
PRODUCT_RE = re.compile(r"\bos\s*terrain\s*50\b", re.I)
GRID_LETTERS = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
ALLOWED_SUFFIXES = {".asc", ".txt", ".gml", ".prj", ".xml"}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"MODULE_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def script_sha256() -> str:
    return sha256_file(Path(__file__))


def grid_100km_letters(easting: float, northing: float) -> str:
    e100k = int(math.floor(easting / 100000))
    n100k = int(math.floor(northing / 100000))
    if not (0 <= e100k <= 6 and 0 <= n100k <= 12):
        raise ValueError("POINT_OUTSIDE_BRITISH_NATIONAL_GRID")
    l1 = (19 - n100k) - ((19 - n100k) % 5) + ((e100k + 10) // 5)
    l2 = ((19 - n100k) * 5) % 25 + (e100k % 5)
    if not (0 <= l1 < 25 and 0 <= l2 < 25):
        raise ValueError("INVALID_OS_GRID_LETTER_INDEX")
    return GRID_LETTERS[l1] + GRID_LETTERS[l2]


def tile_10km(easting: float, northing: float) -> str:
    return f"{grid_100km_letters(easting, northing)}{int((easting % 100000)//10000)}{int((northing % 100000)//10000)}".lower()


def headers() -> dict[str, str]:
    result = {"User-Agent": "TerraYield-AAYS/height_difference_1-revision-13"}
    token = os.environ.get("OS_DATA_HUB_BEARER_TOKEN", "").strip()
    if token:
        result["Authorization"] = f"Bearer {token}"
    return result


def params(extra: dict[str, str] | None = None) -> dict[str, str]:
    result = dict(extra or {})
    key = os.environ.get("OS_DATA_HUB_API_KEY", "").strip()
    if key:
        result["key"] = key
    return result


def get_json_with_hash(session: requests.Session, url: str, query: dict[str, str], timeout: int) -> tuple[Any, dict[str, Any]]:
    response = session.get(url, params=params(query), headers=headers(), timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    content = response.content
    return response.json(), {"resolved_url": response.url, "sha256": sha256_bytes(content), "content_type": response.headers.get("content-type", "")}


def choose_product(products: Any) -> dict[str, Any]:
    if not isinstance(products, list):
        raise ValueError("OS_PRODUCTS_RESPONSE_NOT_LIST")
    matches = [dict(item) for item in products if isinstance(item, dict) and PRODUCT_RE.search(" ".join(str(item.get(k) or "") for k in ("name","title","description","id")))]
    exact = [item for item in matches if re.sub(r"[^a-z0-9]+", "", str(item.get("name") or item.get("title") or "").casefold()) in {"osterrain50","terrain50"}]
    chosen = exact or matches
    if len(chosen) != 1 or not chosen[0].get("id"):
        raise ValueError(f"OS_TERRAIN50_PRODUCT_NOT_UNIQUE:{len(chosen)}")
    return chosen[0]


def choose_download(downloads: Any, area: str, product_id: str) -> dict[str, Any]:
    if not isinstance(downloads, list):
        raise ValueError("OS_DOWNLOADS_RESPONSE_NOT_LIST")
    candidates: list[dict[str, Any]] = []
    for raw in downloads:
        if not isinstance(raw, dict):
            continue
        label = " ".join(str(raw.get(k) or "") for k in ("fileName","filename","format","subformat","area","name","description")).casefold()
        raw_area = str(raw.get("area") or "").upper()
        if raw_area and raw_area not in {area, "GB"}:
            continue
        if "ascii" not in label and "grid" not in label and ".zip" not in label:
            continue
        url = next((raw.get(k) for k in ("url","downloadUrl","downloadURL","href") if isinstance(raw.get(k), str) and str(raw.get(k)).startswith("http")), None)
        if not url:
            name = raw.get("fileName") or raw.get("filename")
            if name:
                url = f"{API_BASE}/products/{product_id}/downloads?fileName={requests.utils.quote(str(name))}&redirect=true"
        if url:
            item = dict(raw)
            item["resolved_request_url"] = str(url)
            candidates.append(item)
    area_specific = [item for item in candidates if str(item.get("area") or "").upper() == area]
    chosen = area_specific or [item for item in candidates if str(item.get("area") or "").upper() == "GB"] or candidates
    unique = {item["resolved_request_url"]: item for item in chosen}
    if len(unique) != 1:
        raise ValueError(f"OS_TERRAIN50_ASCII_DOWNLOAD_NOT_UNIQUE:{area}:{len(unique)}")
    return next(iter(unique.values()))


def stream_download(session: requests.Session, url: str, target: Path, timeout: int) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, params=params(), headers=headers(), timeout=timeout, stream=True, allow_redirects=True) as response:
        response.raise_for_status()
        total = 0
        with target.open("wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError("OS_TERRAIN50_DOWNLOAD_EXCEEDS_LIMIT")
                handle.write(chunk)
        final_url = response.url
        content_type = response.headers.get("content-type", "")
    if total <= 0 or not zipfile.is_zipfile(target):
        raise ValueError("OS_TERRAIN50_DOWNLOAD_NOT_ZIP")
    return {"path": str(target), "size_bytes": total, "sha256": sha256_file(target), "resolved_url": final_url, "content_type": content_type}


def member_tile(name: str) -> str | None:
    matches = re.findall(r"(?<![a-z])([a-z]{2}\d{2})(?!\d)", Path(name).stem.casefold())
    return matches[-1] if matches else None


def extract_tile_bundle(archive: Path, needed_tile: str, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    total_extracted = 0
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            source_name = Path(info.filename)
            if source_name.is_absolute() or ".." in source_name.parts:
                raise ValueError("UNSAFE_OS_ARCHIVE_MEMBER")
            suffix = source_name.suffix.casefold()
            if suffix not in ALLOWED_SUFFIXES or info.file_size <= 0 or info.file_size > MAX_MEMBER_BYTES:
                continue
            total_extracted += info.file_size
            if total_extracted > MAX_EXTRACTED_BYTES:
                raise ValueError("OS_TERRAIN50_EXTRACTION_EXCEEDS_LIMIT")
            tile = member_tile(source_name.name)
            lower = source_name.name.casefold()
            if tile != needed_tile and "metadata" not in lower:
                continue
            target = output_dir / source_name.name
            with zf.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
            written.append(target)
    grids = [p for p in written if p.suffix.casefold() in {".asc", ".txt"} and member_tile(p.name) == needed_tile]
    if len(grids) != 1:
        raise ValueError(f"OS_TERRAIN50_TILE_GRID_NOT_UNIQUE:{needed_tile}:{len(grids)}")
    sidecars = [p for p in written if p != grids[0]]
    if not sidecars:
        raise ValueError("OS_TERRAIN50_VERTICAL_METADATA_SIDECAR_MISSING")
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")[:2_000_000] for p in sidecars if p.suffix.casefold() in {".gml",".prj",".xml"})
    upper = text.upper()
    if "27700" not in upper:
        raise ValueError("OS_TERRAIN50_SIDECAR_EPSG27700_MISSING")
    if not any(token in upper for token in ("NEWLYN", "EPSG::5701", "EPSG:5701", ">5701<", " ODN")):
        raise ValueError("OS_TERRAIN50_SIDECAR_ODN_MISSING")
    return {"grid_path": grids[0], "grid_sha256": sha256_file(grids[0]), "sidecars": [{"path": str(p), "sha256": sha256_file(p)} for p in sidecars], "vertical_metadata_sha256": sha256_bytes(text.encode("utf-8"))}


def representative_point_from_row(row: dict[str, Any], rev12: Any) -> tuple[dict[str, Any], Point]:
    geometry = rev12.extract_boundary_geometry(row)
    polygon = shape(geometry)
    if polygon.is_empty or not polygon.is_valid:
        raise ValueError("OFFICIAL_HMLR_POLYGON_INVALID_FOR_OS_CROSSCHECK")
    point = polygon.representative_point()
    if not polygon.covers(point):
        raise ValueError("REPRESENTATIVE_POINT_NOT_INSIDE_OFFICIAL_POLYGON")
    return geometry, point


def sample_grid_cell(grid_path: Path, point: Point) -> dict[str, Any]:
    with rasterio.open(grid_path) as dataset:
        epsg = dataset.crs.to_epsg() if dataset.crs else None
        if epsg != 27700:
            raise ValueError(f"OS_TERRAIN50_CRS_NOT_EPSG27700:{dataset.crs}")
        if dataset.width != 200 or dataset.height != 200:
            raise ValueError(f"OS_TERRAIN50_HEADER_NOT_200_BY_200:{dataset.width}x{dataset.height}")
        rx, ry = abs(float(dataset.transform.a)), abs(float(dataset.transform.e))
        if abs(rx - 50.0) > 1e-9 or abs(ry - 50.0) > 1e-9:
            raise ValueError(f"OS_TERRAIN50_CELLSIZE_NOT_50M:{rx},{ry}")
        row_idx, col_idx = dataset.index(point.x, point.y)
        if not (0 <= row_idx < dataset.height and 0 <= col_idx < dataset.width):
            raise ValueError("OS_TERRAIN50_POINT_OUTSIDE_TILE")
        value = float(dataset.read(1, window=((row_idx,row_idx+1),(col_idx,col_idx+1)))[0,0])
        if not math.isfinite(value) or (dataset.nodata is not None and value == float(dataset.nodata)):
            raise ValueError("OS_TERRAIN50_SELECTED_CELL_NODATA")
        center_x, center_y = rasterio.transform.xy(dataset.transform, row_idx, col_idx, offset="center")
        distance = math.hypot(float(center_x)-point.x, float(center_y)-point.y)
        if distance > math.sqrt(2.0)*25.0 + 1e-6:
            raise ValueError("OS_TERRAIN50_SELECTED_CENTER_DISTANCE_INVALID")
        return {"ok": True, "elevation_m": round(value, 3), "horizontal_crs": "EPSG:27700", "vertical_crs": "EPSG:5701", "vertical_reference": "Ordnance Datum Newlyn", "header": {"ncols": 200, "nrows": 200, "cellsize": 50.0, "nodata": dataset.nodata}, "row": int(row_idx), "col": int(col_idx), "selected_cell_center_bng": {"easting": round(float(center_x), 3), "northing": round(float(center_y), 3)}, "representative_point_bng": {"easting": round(point.x, 3), "northing": round(point.y, 3)}, "representative_to_cell_center_distance_m": round(distance, 3), "nodata": False, "role": "independent_absolute_elevation_and_datum_crosscheck_not_parcel_range"}


def main() -> int:
    timeout = int(os.environ.get("AAYS_OS_DOWNLOADS_TIMEOUT_SECONDS", "120"))
    if not REV12_ENTRY.is_file():
        raise SystemExit(f"revision_12_entry_missing:{REV12_ENTRY}")
    completed = subprocess.run([sys.executable, str(REV12_ENTRY)], cwd=str(REPO), check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    if not REV12_OUT.is_file():
        raise SystemExit(f"revision_12_output_missing:{REV12_OUT}")
    result = json.loads(REV12_OUT.read_text(encoding="utf-8-sig"))
    rows = result.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("revision_12_rows_not_list")
    rev10 = load_module(REV10_MODULE, "height_difference_1_rev10_for_rev13")
    rev11 = load_module(REV11_MODULE, "height_difference_1_rev11_for_rev13")
    rev12 = load_module(REV12_ENTRY, "height_difference_1_rev12_for_rev13")
    session = requests.Session()
    products, products_meta = get_json_with_hash(session, f"{API_BASE}/products", {"expanded":"true"}, timeout)
    product = choose_product(products)
    product_id = str(product["id"])
    row_points: list[tuple[dict[str, Any], Point, str, str]] = []
    areas: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        _, point = representative_point_from_row(row, rev12)
        area = grid_100km_letters(point.x, point.y)
        tile = tile_10km(point.x, point.y)
        row_points.append((row, point, area, tile))
        areas.add(area)
    archive_records: dict[str, dict[str, Any]] = {}
    for area in sorted(areas):
        downloads, downloads_meta = get_json_with_hash(session, f"{API_BASE}/products/{product_id}/downloads", {"area":area}, timeout)
        selected = choose_download(downloads, area, product_id)
        archive_path = WORK / "downloads" / f"os_terrain50_{area.lower()}.zip"
        download = stream_download(session, selected["resolved_request_url"], archive_path, timeout)
        archive_records[area] = {"downloads_response": downloads_meta, "selected_download": selected, "download": download}
    direct_rows = 0
    error_rows = 0
    errors: list[dict[str, Any]] = []
    for row, point, area, tile in row_points:
        try:
            archive = Path(archive_records[area]["download"]["path"])
            bundle = extract_tile_bundle(archive, tile, WORK / "tiles" / tile)
            sample = sample_grid_cell(Path(bundle["grid_path"]), point)
            sample.update({"source": "OS Terrain 50 July 2026 ASCII Grid via OS Downloads API", "product_id": product_id, "product_version": str(product.get("version") or product.get("versionDate") or product.get("releaseDate") or "July 2026"), "required_100km_area": area, "required_10km_tile": tile.upper(), "source_archive_sha256": archive_records[area]["download"]["sha256"], "source_grid_sha256": bundle["grid_sha256"], "vertical_metadata_sha256": bundle["vertical_metadata_sha256"], "sidecars": bundle["sidecars"], "products_response_sha256": products_meta["sha256"], "downloads_response_sha256": archive_records[area]["downloads_response"]["sha256"], "direct_download_resolved_url": archive_records[area]["download"]["resolved_url"]})
            row["os_terrain50"] = sample
            row["revision_13_direct_os_terrain50"] = {"ok": True, "error": None}
            direct_rows += 1
        except Exception as exc:
            row["os_terrain50"] = {"ok": False, "error": f"{type(exc).__name__}:{exc}"}
            row["revision_13_direct_os_terrain50"] = {"ok": False, "error": f"{type(exc).__name__}:{exc}"}
            row["accepted_measured_row"] = False
            row["output_semantics"] = "NO_DATA_NOT_INFERRED_DIRECT_OS_TERRAIN50_FAILED"
            error_rows += 1
            errors.append({"parcel_id": str(row.get("parcel_id") or row.get("parcel_ref") or ""), "error": f"{type(exc).__name__}:{exc}"})
    result = rev10.apply_gate(result)
    result = rev11.apply_gate(result)
    counts = result.setdefault("counts", {})
    counts["revision_13_direct_os_terrain50_rows"] = direct_rows
    counts["revision_13_direct_os_terrain50_error_rows"] = error_rows
    digest = script_sha256()
    result.update({"schema_version": max(int(result.get("schema_version", 0) or 0), 13), "slot_id": SLOT, "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "attempt_id": ATTEMPT_ID, "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL, "script_sha256": digest, "os_terrain50_source_contract": {"api_base": API_BASE, "product_id": product_id, "product": product, "products_response_url": products_meta["resolved_url"], "products_response_sha256": products_meta["sha256"], "version_date_expected": "July 2026", "grid_width": 200, "grid_height": 200, "cellsize_m": 50, "height_location": "pixel_center", "horizontal_crs": "EPSG:27700", "vertical_crs": "EPSG:5701", "vertical_reference": "Ordnance Datum Newlyn", "role": "independent_absolute_elevation_and_datum_crosscheck_not_parcel_range"}, "direct_os_terrain50_errors": errors, "direct_os_contract": {"official_os_downloads_api_required": True, "archive_grid_and_vertical_metadata_sha256_required": True, "official_hmlr_representative_point_required": True, "representative_point_inside_polygon_required": True, "exact_10km_tile_required": True, "grid_200_by_200_required": True, "cellsize_50m_required": True, "nodata_rejected": True, "parcel_range_promotion_forbidden": True}, "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False})
    accepted = int(counts.get("official_three_source_height_difference_rows", 0) or 0)
    result["status"] = "BLOCKED_DIRECT_OS_TERRAIN50_CROSSCHECK" if error_rows else ("MEASURED_OFFICIAL_HEIGHT_DIFFERENCE_ROWS_AVAILABLE" if accepted else "NO_DATA_NOT_INFERRED")
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    for path in (OUT, WEB_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    output_sha = sha256_bytes(text.encode("utf-8"))
    snapshot = {"schema_version": 1, "slot_id": SLOT, "task_id": TASK_ID, "payload_revision": PAYLOAD_REVISION, "attempt_id": ATTEMPT_ID, "idempotency_key": IDEMPOTENCY_KEY, "script_path": SCRIPT_REL, "script_sha256": digest, "runner_web_output_sha256": output_sha, "candidate_rows": counts.get("candidate_rows", 0), "direct_ea_resample_rows": counts.get("revision_12_direct_ea_resample_rows", 0), "direct_os_terrain50_rows": direct_rows, "direct_os_terrain50_error_rows": error_rows, "accepted_official_height_difference_rows": accepted, "os_terrain50_source_contract": result["os_terrain50_source_contract"], "final_ready": False, "product_final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("# Height Difference 1 revision 13 direct OS Terrain 50 crosscheck\n\n" f"- Candidate rows: `{snapshot['candidate_rows']}`\n" f"- Direct EA rows: `{snapshot['direct_ea_resample_rows']}`\n" f"- Direct OS Terrain 50 rows: `{snapshot['direct_os_terrain50_rows']}`\n" f"- Accepted official height-difference rows: `{snapshot['accepted_official_height_difference_rows']}`\n" "- OS Terrain 50 is used only for independent absolute elevation and ODN consistency, never parcel range.\n" "- `final_ready=false`\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": counts, "output": str(OUT)}))
    return 0 if not error_rows else 2


if __name__ == "__main__":
    raise SystemExit(main())

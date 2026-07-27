#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import re
import zipfile
from pathlib import Path
from typing import Any, Iterable

import requests
from shapely.geometry import shape

API_BASE = "https://api.os.uk/downloads/v1"
TERRAIN50_ASCII_FORMAT = "ASCII Grid and GML (Grid)"
MAX_DOWNLOAD_BYTES = 2_500_000_000
MAX_NESTED_ARCHIVE_BYTES = 50_000_000
MAX_NESTING_DEPTH = 2
PRODUCT_NAME_RE = re.compile(r"\bos\s*terrain\s*50\b", re.I)


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid_100km_letters(easting: float, northing: float) -> str:
    letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    e100k = int(math.floor(easting / 100000))
    n100k = int(math.floor(northing / 100000))
    if not (0 <= e100k <= 6 and 0 <= n100k <= 12):
        raise ValueError("coordinate outside British National Grid")
    l1 = (19 - n100k) - ((19 - n100k) % 5) + ((e100k + 10) // 5)
    l2 = ((19 - n100k) * 5) % 25 + (e100k % 5)
    if not (0 <= l1 < 25 and 0 <= l2 < 25):
        raise ValueError("invalid OS grid letter index")
    return letters[l1] + letters[l2]


def _required_areas(hmlr_path: Path) -> tuple[list[str], list[int]]:
    payload = json.loads(hmlr_path.read_text(encoding="utf-8-sig"))
    if payload.get("status") != "THREE_HMLR_EXACT_POLYGONS_MATCHED":
        raise ValueError("HMLR exact polygon gate incomplete")
    areas: set[str] = set()
    rows: list[int] = []
    for row in payload.get("results", []):
        if row.get("status") != "MATCHED_EXACT_ID_AND_POINT_INSIDE":
            continue
        geometry = (row.get("match") or {}).get("geometry_geojson_epsg27700")
        if not isinstance(geometry, dict):
            raise ValueError("HMLR match lacks EPSG:27700 geometry")
        minx, miny, maxx, maxy = map(float, shape(geometry).bounds)
        for easting in (minx, maxx - 1e-9):
            for northing in (miny, maxy - 1e-9):
                areas.add(_grid_100km_letters(easting, northing))
        rows.append(int(row["row_no"]))
    if len(rows) != 3:
        raise ValueError("exactly three matched HMLR rows required")
    return sorted(areas), sorted(rows)


def _headers() -> dict[str, str]:
    headers = {"User-Agent": "TerraYield-AAYS/height_difference_2"}
    token = os.environ.get("OS_DATA_HUB_BEARER_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _params(extra: dict[str, str] | None = None) -> dict[str, str]:
    params = dict(extra or {})
    key = os.environ.get("OS_DATA_HUB_API_KEY", "").strip()
    if key:
        params["key"] = key
    return params


def _get_json(session: requests.Session, url: str, *, params: dict[str, str] | None, timeout: int) -> Any:
    response = session.get(url, params=_params(params), headers=_headers(), timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    return response.json()


def _product_label(product: dict[str, Any]) -> str:
    values = [product.get(key) for key in ("name", "title", "description", "id")]
    return " ".join(str(value) for value in values if value)


def _choose_product(products: Any) -> dict[str, Any]:
    if not isinstance(products, list):
        raise ValueError("OS products response is not a list")
    matches = [dict(product) for product in products if isinstance(product, dict) and PRODUCT_NAME_RE.search(_product_label(product))]
    exact = [product for product in matches if re.sub(r"[^a-z0-9]+", "", str(product.get("name") or product.get("title") or "").casefold()) in {"osterrain50", "terrain50"}]
    chosen = exact or matches
    if len(chosen) != 1:
        raise ValueError(f"OS Terrain 50 product match is not unique: {len(chosen)}")
    if not chosen[0].get("id"):
        raise ValueError("OS Terrain 50 product lacks id")
    return chosen[0]


def _download_label(item: dict[str, Any]) -> str:
    return " ".join(str(item.get(key) or "") for key in ("fileName", "filename", "format", "subformat", "area", "name", "description"))


def _download_url(item: dict[str, Any], api_base: str, product_id: str) -> str | None:
    for key in ("url", "downloadUrl", "downloadURL", "href"):
        value = item.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    file_name = item.get("fileName") or item.get("filename")
    if file_name:
        return f"{api_base.rstrip('/')}/products/{product_id}/downloads?fileName={requests.utils.quote(str(file_name))}&redirect=true"
    return None


def _choose_download(downloads: Any, area: str, api_base: str, product_id: str) -> dict[str, Any]:
    if not isinstance(downloads, list):
        raise ValueError(f"OS downloads response for {area} is not a list")
    candidates: list[dict[str, Any]] = []
    for raw in downloads:
        if not isinstance(raw, dict):
            continue
        label = _download_label(raw).casefold()
        raw_area = str(raw.get("area") or "").upper()
        if raw_area and raw_area not in {area, "GB"}:
            continue
        if "ascii" not in label and "grid" not in label and not re.search(r"\.zip\b", label):
            continue
        url = _download_url(raw, api_base, product_id)
        if url:
            item = dict(raw)
            item["resolved_request_url"] = url
            candidates.append(item)
    area_specific = [item for item in candidates if str(item.get("area") or "").upper() == area]
    chosen = area_specific or [item for item in candidates if str(item.get("area") or "").upper() == "GB"] or candidates
    unique: dict[str, dict[str, Any]] = {str(item["resolved_request_url"]): item for item in chosen}
    if len(unique) != 1:
        raise ValueError(f"Terrain50 ASCII/Grid download for area {area} is not unique: {len(unique)}")
    return next(iter(unique.values()))


def _archive_contains_ascii_grid(zf: zipfile.ZipFile, *, depth: int = 0) -> bool:
    for info in zf.infolist():
        if info.is_dir():
            continue
        path = Path(info.filename)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Terrain50 ZIP contains unsafe member path")
        suffix = path.suffix.casefold()
        if suffix in {".asc", ".txt"}:
            return True
        if suffix != ".zip":
            continue
        if depth >= MAX_NESTING_DEPTH:
            continue
        if info.file_size <= 0 or info.file_size > MAX_NESTED_ARCHIVE_BYTES:
            raise ValueError(f"Terrain50 nested archive size invalid: {info.filename}")
        with zf.open(info) as source:
            payload = source.read(MAX_NESTED_ARCHIVE_BYTES + 1)
        if len(payload) != info.file_size or len(payload) > MAX_NESTED_ARCHIVE_BYTES:
            raise ValueError(f"Terrain50 nested archive read invalid: {info.filename}")
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as nested:
                if _archive_contains_ascii_grid(nested, depth=depth + 1):
                    return True
        except zipfile.BadZipFile as exc:
            raise ValueError(f"Terrain50 nested archive invalid: {info.filename}") from exc
    return False


def _stream_download(session: requests.Session, url: str, target: Path, timeout: int) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, params=_params(), headers=_headers(), timeout=timeout, stream=True, allow_redirects=True) as response:
        response.raise_for_status()
        total = 0
        with target.open("wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError("Terrain50 download exceeds safety limit")
                handle.write(chunk)
        final_url = response.url
        content_type = response.headers.get("content-type", "")
    if total <= 0 or not zipfile.is_zipfile(target):
        raise ValueError("Terrain50 download is empty or not ZIP")
    with zipfile.ZipFile(target) as zf:
        if not _archive_contains_ascii_grid(zf):
            raise ValueError("Terrain50 ZIP contains no ASCII grid members, directly or in nested tile ZIPs")
    return {"path": str(target), "size_bytes": total, "sha256": _sha256(target), "resolved_url": final_url, "content_type": content_type}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hmlr-exact-matches", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-base", default=API_BASE)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--no-download", action="store_true")
    args = parser.parse_args(argv)
    try:
        areas, rows = _required_areas(args.hmlr_exact_matches)
        session = requests.Session()
        products = _get_json(session, f"{args.api_base.rstrip('/')}/products", params={"expanded": "true"}, timeout=args.timeout)
        product = _choose_product(products)
        product_id = str(product["id"])
        records = []
        for area in areas:
            endpoint = f"{args.api_base.rstrip('/')}/products/{product_id}/downloads"
            exact_downloads = _get_json(session, endpoint, params={"area": area, "format": TERRAIN50_ASCII_FORMAT}, timeout=args.timeout)
            query_mode = "area_plus_exact_format"
            downloads = exact_downloads
            if isinstance(exact_downloads, list) and not exact_downloads:
                downloads = _get_json(session, endpoint, params={"area": area}, timeout=args.timeout)
                query_mode = "area_only_fallback_after_empty_exact_format"
            selected = _choose_download(downloads, area, args.api_base, product_id)
            record = {"area": area, "query_mode": query_mode, "requested_format": TERRAIN50_ASCII_FORMAT, "selected": selected}
            if not args.no_download:
                target = args.output_dir / f"os_terrain50_{area.lower()}.zip"
                record["download"] = _stream_download(session, selected["resolved_request_url"], target, args.timeout)
            records.append(record)
        status = "TERRAIN50_REQUIRED_AREA_ARCHIVES_READY" if not args.no_download else "TERRAIN50_DOWNLOADS_RESOLVED"
        payload = {"schema_version": 2, "slot_id": "height_difference_2", "status": status, "api_base": args.api_base, "product": product, "required_100km_areas": areas, "candidate_row_numbers": rows, "records": records, "archive_paths": [record["download"]["path"] for record in records if "download" in record], "exact_format_requested_first": True, "nested_zip_validation_supported": True, "nearest_or_unverified_download_used": False, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
        code = 0
    except Exception as exc:
        payload = {"schema_version": 2, "slot_id": "height_difference_2", "status": "BLOCKED_TERRAIN50_DOWNLOAD_RESOLUTION", "error": f"{type(exc).__name__}: {exc}", "archive_paths": [], "exact_format_requested_first": True, "nested_zip_validation_supported": True, "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}
        code = 2
    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"], "archives": len(payload.get("archive_paths", []))}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

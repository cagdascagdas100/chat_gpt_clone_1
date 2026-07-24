#!/usr/bin/env python3
"""Download only OS Terrain 50 100 km area packages required by starter candidates.

The official OS Downloads API is queried without guessed static URLs. Candidate
areas come only from source-backed EPSG:27700 coordinates in the starter
manifest. Every archive is checksum-verified and its ASCII grid headers are
validated before use. This script writes no parcel measurement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

PRODUCT_ID = "Terrain50"
API_BASE = "https://api.os.uk/downloads/v1"
MAX_AREA_ARCHIVE_BYTES = 80 * 1024 * 1024
VERSION_RE = re.compile(r"^\d{4}-\d{2}$")


def _grid_letters(easting: float, northing: float) -> str:
    if not (math.isfinite(easting) and math.isfinite(northing)):
        raise ValueError("non-finite British National Grid coordinate")
    e100k = int(easting) // 100000
    n100k = int(northing) // 100000
    if not (0 <= e100k <= 6 and 0 <= n100k <= 12):
        raise ValueError("coordinate outside British National Grid extent")
    l1 = (19 - n100k) - (19 - n100k) % 5 + (e100k + 10) // 5
    l2 = (19 - n100k) * 5 % 25 + e100k % 5
    if l1 > 7:
        l1 += 1
    if l2 > 7:
        l2 += 1
    return chr(l1 + 65) + chr(l2 + 65)


def _load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    candidates = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("starter manifest has no candidates")
    rows: list[dict[str, Any]] = []
    seen: set[int] = set()
    for raw in candidates:
        if not isinstance(raw, dict):
            raise ValueError("starter candidate is not an object")
        row_no = int(raw["row_no"])
        if row_no in seen:
            raise ValueError(f"duplicate candidate row_no {row_no}")
        seen.add(row_no)
        easting = float(raw["bng_easting"])
        northing = float(raw["bng_northing"])
        rows.append({**raw, "row_no": row_no, "bng_easting": easting, "bng_northing": northing, "os_100km_area": _grid_letters(easting, northing)})
    return rows


def _request_json(url: str, timeout: int) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "TerraYield-AAYS/height_difference_3", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _product_url() -> str:
    return f"{API_BASE}/products/{PRODUCT_ID}"


def _downloads_url() -> str:
    return f"{API_BASE}/products/{PRODUCT_ID}/downloads"


def _format_text(item: dict[str, Any]) -> str:
    return " ".join(str(item.get(key) or "") for key in ("format", "subformat", "fileName")).casefold()


def _select_downloads(items: Any, required_areas: list[str]) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        raise ValueError("OS Downloads API response must be a list")
    selected: dict[str, dict[str, Any]] = {}
    for area in required_areas:
        matches = []
        for raw in items:
            if not isinstance(raw, dict) or str(raw.get("area") or "").upper() != area:
                continue
            text = _format_text(raw)
            if "ascii" in text and "grid" in text:
                url = raw.get("url")
                if isinstance(url, str) and url.startswith("https://"):
                    matches.append(dict(raw))
        if len(matches) != 1:
            raise ValueError(f"expected exactly one official Terrain50 ASCII Grid download for area {area}; found {len(matches)}")
        selected[area] = matches[0]
    return selected


def _md5(path: Path) -> str:
    digest = hashlib.md5()  # nosec - official source integrity field, not security auth
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_names(archive: zipfile.ZipFile) -> list[str]:
    names: list[str] = []
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        parts = [part for part in name.split("/") if part]
        if name.startswith("/") or ".." in parts:
            raise ValueError(f"unsafe archive path: {info.filename}")
        if info.file_size < 0 or info.file_size > 50 * 1024 * 1024:
            raise ValueError(f"unsafe archive member size: {info.filename}")
        names.append(name)
    return names


def _ascii_header(archive: zipfile.ZipFile, name: str) -> dict[str, float]:
    with archive.open(name) as handle:
        lines = [handle.readline().decode("ascii", errors="strict").strip() for _ in range(6)]
    header: dict[str, float] = {}
    for line in lines:
        parts = line.split()
        if len(parts) != 2:
            raise ValueError(f"invalid ASCII header line in {name}: {line!r}")
        header[parts[0].casefold()] = float(parts[1])
    if int(header.get("ncols", -1)) != 200 or int(header.get("nrows", -1)) != 200 or abs(header.get("cellsize", -1) - 50.0) > 1e-9:
        raise ValueError(f"Terrain50 grid schema mismatch in {name}: {header}")
    if not ({"xllcorner", "xllcenter"} & set(header)) or not ({"yllcorner", "yllcenter"} & set(header)):
        raise ValueError(f"Terrain50 grid lacks southwest origin: {name}")
    return header


def _validate_archive(path: Path, area: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size < 1024:
        raise ValueError(f"Terrain50 archive missing or too small: {path}")
    with path.open("rb") as handle:
        if handle.read(4) not in {b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"}:
            raise ValueError(f"Terrain50 archive lacks ZIP signature: {path}")
    with zipfile.ZipFile(path) as archive:
        names = _safe_names(archive)
        asc = sorted(name for name in names if name.casefold().endswith(".asc"))
        gml = sorted(name for name in names if name.casefold().endswith(".gml"))
        prj = sorted(name for name in names if name.casefold().endswith(".prj"))
        if not asc:
            raise ValueError(f"no ASCII grids in Terrain50 area archive {area}")
        wrong_area = [name for name in asc if not Path(name).stem.upper().startswith(area)]
        if wrong_area:
            raise ValueError(f"Terrain50 archive {area} contains grids outside area: {wrong_area[:5]}")
        headers = {name: _ascii_header(archive, name) for name in asc}
        if not gml or not prj:
            raise ValueError(f"Terrain50 area archive {area} lacks required GML or PRJ companions")
    return {
        "archive_entries": len(names),
        "ascii_tile_count": len(asc),
        "gml_count": len(gml),
        "prj_count": len(prj),
        "ascii_headers_validated": len(headers),
        "tile_names": [Path(name).stem.upper() for name in asc],
    }


def _download(url: str, destination: Path, timeout: int, attempts: int = 3) -> tuple[str, dict[str, str]]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        fd, temp_name = tempfile.mkstemp(prefix=destination.stem + "_", suffix=".tmp", dir=destination.parent)
        os.close(fd)
        temp = Path(temp_name)
        total = 0
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "TerraYield-AAYS/height_difference_3", "Accept": "application/zip, */*"})
            with urllib.request.urlopen(request, timeout=timeout) as response, temp.open("wb") as handle:
                final_url = response.geturl()
                headers = {key.casefold(): value for key, value in response.headers.items()}
                if "text/html" in headers.get("content-type", "").casefold():
                    raise ValueError("official download returned HTML")
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_AREA_ARCHIVE_BYTES:
                        raise ValueError(f"area archive exceeds {MAX_AREA_ARCHIVE_BYTES} bytes")
                    handle.write(chunk)
            temp.replace(destination)
            return final_url, headers
        except Exception as exc:
            last_error = exc
            temp.unlink(missing_ok=True)
            if attempt < attempts:
                time.sleep(min(2 ** (attempt - 1), 4))
    assert last_error is not None
    raise last_error


def _load_json_or_fetch(path: Path | None, url: str, timeout: int) -> Any:
    if path:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return _request_json(url, timeout)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starter-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--product-json", type=Path, help="Offline/test product details JSON")
    parser.add_argument("--downloads-json", type=Path, help="Offline/test downloads list JSON")
    parser.add_argument("--archive-map-json", type=Path, help="Offline/test map from area code to local archive path")
    args = parser.parse_args()

    candidates = _load_candidates(args.starter_manifest.resolve())
    required_areas = sorted({row["os_100km_area"] for row in candidates})
    product = _load_json_or_fetch(args.product_json, _product_url(), args.timeout)
    if not isinstance(product, dict) or product.get("id") != PRODUCT_ID:
        raise ValueError("official product details do not identify Terrain50")
    version = str(product.get("version") or "")
    if not VERSION_RE.fullmatch(version) or not version.endswith("-07"):
        raise ValueError(f"Terrain50 product version is not an annual July release: {version!r}")
    downloads = _load_json_or_fetch(args.downloads_json, _downloads_url(), args.timeout)
    selected = _select_downloads(downloads, required_areas)

    archive_map: dict[str, str] = {}
    if args.archive_map_json:
        raw_map = json.loads(args.archive_map_json.read_text(encoding="utf-8-sig"))
        if not isinstance(raw_map, dict):
            raise ValueError("archive map must be an object")
        archive_map = {str(key).upper(): str(value) for key, value in raw_map.items()}

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for area in required_areas:
        metadata = selected[area]
        expected_name = str(metadata.get("fileName") or f"OS_Terrain50_{area}.zip")
        destination = Path(archive_map[area]).resolve() if area in archive_map else out / expected_name
        if area in archive_map:
            final_url = str(destination)
            response_headers: dict[str, str] = {}
        else:
            final_url, response_headers = _download(str(metadata["url"]), destination, args.timeout)
        actual_md5 = _md5(destination)
        expected_md5 = str(metadata.get("md5") or "").casefold()
        if expected_md5 and actual_md5.casefold() != expected_md5:
            raise ValueError(f"MD5 mismatch for Terrain50 area {area}: {actual_md5} != {expected_md5}")
        validation = _validate_archive(destination, area)
        records.append({
            "area": area,
            "product_version": version,
            "download_metadata": metadata,
            "resolved_download_url": final_url,
            "response_headers": response_headers,
            "archive_path": str(destination),
            "archive_size_bytes": destination.stat().st_size,
            "archive_md5": actual_md5,
            "archive_sha256": _sha256(destination),
            **validation,
        })

    manifest = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "product_id": PRODUCT_ID,
        "product_version": version,
        "official_product_url": _product_url(),
        "official_downloads_url": _downloads_url(),
        "candidate_count": len(candidates),
        "required_100km_areas": required_areas,
        "candidate_area_map": [{"row_no": row["row_no"], "parcel_id": row.get("parcel_id"), "area": row["os_100km_area"]} for row in candidates],
        "archives": records,
        "full_gb_archive_downloaded": False,
        "only_required_areas_downloaded": True,
        "nearest_or_neighbour_area_substitution_used": False,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    output = out / "terrain50_required_areas_manifest.json"
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "areas": required_areas, "archives": len(records), "manifest": str(output)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

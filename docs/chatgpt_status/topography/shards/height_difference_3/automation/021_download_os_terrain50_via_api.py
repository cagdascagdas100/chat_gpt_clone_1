#!/usr/bin/env python3
"""Download and validate the current OS Terrain 50 GB ASCII Grid package via OS Downloads API.

Uses only the official OpenData endpoint. No guessed static URL or browser HAR is required.
No parcel measurement is written by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

PRODUCT_ID = "Terrain50"
FORMAT = "ASCII Grid and GML (Grid)"
AREA = "GB"
API_BASE = "https://api.os.uk/downloads/v1"
MAX_BYTES = 350 * 1024 * 1024
MIN_ASC_TILES = 2500


def request(url: str, timeout: int, api_key: str | None = None):
    headers = {"User-Agent": "TerraYield-AAYS/height_difference_3", "Accept": "application/json, application/zip, */*"}
    if api_key:
        headers["key"] = api_key
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout)


def catalog_url(api_key: str | None = None) -> str:
    query = [("area", AREA), ("format", FORMAT)]
    if api_key:
        query.append(("key", api_key))
    return f"{API_BASE}/products/{PRODUCT_ID}/downloads?{urllib.parse.urlencode(query)}"


def redirect_url(api_key: str | None = None) -> str:
    return catalog_url(api_key) + "&redirect"


def flatten_downloads(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(v) for v in payload if isinstance(v, dict)]
    if isinstance(payload, dict):
        for key in ("downloads", "items", "results"):
            if isinstance(payload.get(key), list):
                return [dict(v) for v in payload[key] if isinstance(v, dict)]
    raise ValueError("OS Downloads API response does not contain a download list")


def choose_candidate(items: list[dict[str, Any]]) -> dict[str, Any]:
    scored: list[tuple[int, dict[str, Any]]] = []
    for item in items:
        text = json.dumps(item, ensure_ascii=False).lower()
        score = 0
        if "terrain50" in text or "terrain 50" in text:
            score += 5
        if "ascii" in text:
            score += 4
        if "grid" in text:
            score += 3
        if '"gb"' in text or "great britain" in text:
            score += 2
        if "july 2026" in text or "2026-07" in text:
            score += 2
        if ".zip" in text:
            score += 1
        if score >= 9:
            scored.append((score, item))
    if not scored:
        raise ValueError("no Terrain50 GB ASCII Grid candidate returned by OS Downloads API")
    scored.sort(key=lambda pair: (-pair[0], json.dumps(pair[1], sort_keys=True)))
    best_score = scored[0][0]
    best = [item for score, item in scored if score == best_score]
    if len(best) > 1:
        serialized = {json.dumps(item, sort_keys=True) for item in best}
        if len(serialized) > 1:
            raise ValueError(f"ambiguous OS Terrain50 candidates at score {best_score}: {len(best)}")
    return best[0]


def candidate_url(item: dict[str, Any]) -> str | None:
    for key in ("url", "downloadUrl", "downloadURL", "href", "fileUrl", "fileURL"):
        value = item.get(key)
        if isinstance(value, str) and value.startswith("https://"):
            return value
    links = item.get("links")
    if isinstance(links, list):
        for link in links:
            if isinstance(link, dict):
                value = link.get("href")
                if isinstance(value, str) and value.startswith("https://"):
                    return value
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_names(archive: zipfile.ZipFile) -> list[str]:
    names = []
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        parts = [p for p in name.split("/") if p]
        if name.startswith("/") or ".." in parts:
            raise ValueError(f"unsafe archive path: {info.filename}")
        if info.file_size < 0 or info.file_size > 50 * 1024 * 1024:
            raise ValueError(f"unsafe member size: {info.filename}")
        names.append(name)
    return names


def validate_ascii_header(archive: zipfile.ZipFile, name: str) -> dict[str, float]:
    with archive.open(name) as handle:
        lines = [handle.readline().decode("ascii", errors="strict").strip() for _ in range(8)]
    header: dict[str, float] = {}
    recognized = {"ncols", "nrows", "xllcorner", "xllcenter", "yllcorner", "yllcenter", "cellsize", "nodata_value"}
    for line in lines:
        parts = line.split()
        if len(parts) < 2 or parts[0].lower() not in recognized:
            break
        header[parts[0].lower()] = float(parts[1])
    required = {"ncols", "nrows", "cellsize"}
    if not required.issubset(header):
        raise ValueError(f"ASCII header missing {sorted(required - set(header))}: {name}")
    if not ({"xllcorner", "xllcenter"} & set(header)) or not ({"yllcorner", "yllcenter"} & set(header)):
        raise ValueError(f"ASCII header lacks southwest origin: {name}")
    if int(header["ncols"]) != 200 or int(header["nrows"]) != 200 or abs(header["cellsize"] - 50.0) > 1e-9:
        raise ValueError(f"Terrain50 grid dimensions are not 200x200 at 50m: {name}")
    return header


def validate_zip(path: Path, min_tiles: int = MIN_ASC_TILES) -> dict[str, Any]:
    if path.stat().st_size < 1024:
        raise ValueError("download is too small to be a Terrain50 package")
    with path.open("rb") as handle:
        if handle.read(4) not in {b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"}:
            raise ValueError("download does not have a ZIP signature")
    with zipfile.ZipFile(path) as archive:
        names = safe_names(archive)
        asc = sorted(name for name in names if name.lower().endswith(".asc"))
        gml = sorted(name for name in names if name.lower().endswith(".gml"))
        prj = sorted(name for name in names if name.lower().endswith(".prj"))
        nested = sorted(name for name in names if name.lower().endswith(".zip"))
        if len(asc) >= min_tiles:
            samples = sorted(set([asc[0], asc[len(asc) // 2], asc[-1]]))
            headers = {name: validate_ascii_header(archive, name) for name in samples}
            tile_count = len(asc)
            packaging = "direct_ascii_members"
        else:
            # Current official Terrain 50 packages contain one safe per-tile
            # ZIP (ASC/GML/PRJ) inside the GB ZIP. Validate the package shape
            # and three representative inner ASCII headers without extracting
            # the full national archive.
            if len(nested) < min_tiles:
                raise ValueError(
                    f"expected at least {min_tiles} direct ASCII tiles or nested tile ZIPs, "
                    f"found asc={len(asc)} nested_zip={len(nested)}"
                )
            sample_zips = sorted(set([nested[0], nested[len(nested) // 2], nested[-1]]))
            headers = {}
            for nested_name in sample_zips:
                with archive.open(nested_name) as handle:
                    payload = handle.read()
                with zipfile.ZipFile(io.BytesIO(payload)) as inner:
                    inner_names = safe_names(inner)
                    inner_asc = sorted(name for name in inner_names if name.lower().endswith(".asc"))
                    if len(inner_asc) != 1:
                        raise ValueError(f"nested Terrain50 tile must contain exactly one ASCII grid: {nested_name}")
                    headers[f"{nested_name}!{inner_asc[0]}"] = validate_ascii_header(inner, inner_asc[0])
            tile_count = len(nested)
            packaging = "nested_per_tile_zip"
    return {
        "archive_entries": len(names),
        "ascii_tile_count": tile_count,
        "direct_ascii_count": len(asc),
        "nested_tile_zip_count": len(nested),
        "gml_count": len(gml),
        "prj_count": len(prj),
        "packaging": packaging,
        "sample_headers": headers,
    }


def download_to(url: str, output: Path, timeout: int, api_key: str | None) -> tuple[str, dict[str, str]]:
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="terrain50_", suffix=".zip.tmp", dir=output.parent)
    os.close(fd)
    temp = Path(temp_name)
    total = 0
    try:
        with request(url, timeout, api_key) as response, temp.open("wb") as handle:
            final_url = response.geturl()
            headers = {k.lower(): v for k, v in response.headers.items()}
            content_type = headers.get("content-type", "").lower()
            if "text/html" in content_type:
                raise ValueError("OS download endpoint returned HTML")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError(f"Terrain50 download exceeds {MAX_BYTES} bytes")
                handle.write(chunk)
        temp.replace(output)
        return final_url, headers
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--api-key", default=os.environ.get("OS_DATA_HUB_API_KEY"))
    parser.add_argument("--archive", type=Path, help="Validate an already downloaded official archive instead of downloading.")
    parser.add_argument("--min-ascii-tiles", type=int, default=MIN_ASC_TILES)
    parser.add_argument("--max-cache-age-hours", type=float, default=24.0)
    args = parser.parse_args()

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    archive = args.archive.resolve() if args.archive else out / "OS_Terrain50_July_2026_GB_ASCII_Grid.zip"
    catalog = None
    selected = None
    response_headers: dict[str, str] = {}
    cache_reused = (
        not args.archive
        and archive.is_file()
        and args.max_cache_age_hours > 0
        and time.time() - archive.stat().st_mtime <= args.max_cache_age_hours * 3600
    )
    if cache_reused:
        previous = out / "terrain50_official_api_provenance.json"
        previous_manifest = json.loads(previous.read_text(encoding="utf-8")) if previous.is_file() else {}
        selected = {"cache_reused": True, "max_cache_age_hours": args.max_cache_age_hours}
        final_url = str(previous_manifest.get("resolved_download_url") or archive)
    elif not args.archive:
        with request(catalog_url(args.api_key), args.timeout, args.api_key) as response:
            catalog = json.load(response)
        selected = choose_candidate(flatten_downloads(catalog))
        source_url = candidate_url(selected) or redirect_url(args.api_key)
        final_url, response_headers = download_to(source_url, archive, args.timeout, args.api_key)
    else:
        final_url = str(archive)

    validation = validate_zip(archive, args.min_ascii_tiles)
    manifest = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "product_id": PRODUCT_ID,
        "area": AREA,
        "format": FORMAT,
        "official_catalog_url": catalog_url(None),
        "official_redirect_url": redirect_url(None),
        "selected_download_metadata": selected,
        "resolved_download_url": final_url,
        "response_headers": response_headers,
        "cache_reused": cache_reused,
        "archive_path": str(archive),
        "archive_size_bytes": archive.stat().st_size,
        "archive_sha256": sha256_file(archive),
        **validation,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    (out / "terrain50_official_api_provenance.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "ascii_tiles": validation["ascii_tile_count"], "archive_sha256": manifest["archive_sha256"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise


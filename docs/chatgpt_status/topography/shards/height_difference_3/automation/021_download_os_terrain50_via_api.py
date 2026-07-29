#!/usr/bin/env python3
"""Download and validate the current OS Terrain 50 GB ASCII Grid package via OS Downloads API.

Uses only the official OpenData catalog endpoint. Cached national archives are
reused only when a prior official-catalog provenance record binds the exact
archive hash and size. No guessed static URL or unproven recent cache is
accepted. No parcel measurement is written by this script.
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
OFFICIAL_GB_GRID_TILE_COUNT = 2858
OFFICIAL_PRODUCT_SUPPLY_URL = (
    "https://docs.os.uk/os-downloads/products/land-and-terrain-portfolio/"
    "os-terrain-50/os-terrain-50-overview/product-supply"
)


def request(url: str, timeout: int, api_key: str | None = None):
    headers = {
        "User-Agent": "TerraYield-AAYS/height_difference_3",
        "Accept": "application/json, application/zip, */*",
    }
    if api_key:
        headers["key"] = api_key
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=headers),
        timeout=timeout,
    )


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
            raise ValueError(
                f"ambiguous OS Terrain50 candidates at score {best_score}: {len(best)}"
            )
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


def sha256_json(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def safe_names(archive: zipfile.ZipFile) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        parts = [p for p in name.split("/") if p]
        if name.startswith("/") or ".." in parts:
            raise ValueError(f"unsafe archive path: {info.filename}")
        if info.file_size < 0 or info.file_size > 50 * 1024 * 1024:
            raise ValueError(f"unsafe member size: {info.filename}")
        folded = name.casefold()
        if folded in seen:
            raise ValueError(f"duplicate archive member path: {info.filename}")
        seen.add(folded)
        names.append(name)
    return names


def validate_ascii_header(
    archive: zipfile.ZipFile,
    name: str,
) -> dict[str, float]:
    with archive.open(name) as handle:
        lines = [
            handle.readline().decode("ascii", errors="strict").strip()
            for _ in range(8)
        ]
    header: dict[str, float] = {}
    recognized = {
        "ncols",
        "nrows",
        "xllcorner",
        "xllcenter",
        "yllcorner",
        "yllcenter",
        "cellsize",
        "nodata_value",
    }
    for line in lines:
        parts = line.split()
        if len(parts) < 2 or parts[0].lower() not in recognized:
            break
        header[parts[0].lower()] = float(parts[1])
    required = {"ncols", "nrows", "cellsize"}
    if not required.issubset(header):
        raise ValueError(
            f"ASCII header missing {sorted(required - set(header))}: {name}"
        )
    if not ({"xllcorner", "xllcenter"} & set(header)) or not (
        {"yllcorner", "yllcenter"} & set(header)
    ):
        raise ValueError(f"ASCII header lacks southwest origin: {name}")
    if (
        int(header["ncols"]) != 200
        or int(header["nrows"]) != 200
        or abs(header["cellsize"] - 50.0) > 1e-9
    ):
        raise ValueError(
            f"Terrain50 grid dimensions are not 200x200 at 50m: {name}"
        )
    return header


def validate_zip(
    path: Path,
    expected_tiles: int = OFFICIAL_GB_GRID_TILE_COUNT,
) -> dict[str, Any]:
    if expected_tiles < 1:
        raise ValueError("expected Terrain50 tile count must be positive")
    if path.stat().st_size < 1024:
        raise ValueError("download is too small to be a Terrain50 package")
    with path.open("rb") as handle:
        if handle.read(4) not in {
            b"PK\x03\x04",
            b"PK\x05\x06",
            b"PK\x07\x08",
        }:
            raise ValueError("download does not have a ZIP signature")

    with zipfile.ZipFile(path) as archive:
        names = safe_names(archive)
        asc = sorted(name for name in names if name.lower().endswith(".asc"))
        gml = sorted(name for name in names if name.lower().endswith(".gml"))
        prj = sorted(name for name in names if name.lower().endswith(".prj"))
        nested = sorted(name for name in names if name.lower().endswith(".zip"))

        if asc and nested:
            raise ValueError(
                "ambiguous Terrain50 package mixes direct ASCII members and nested tile ZIPs"
            )
        if asc:
            tile_count = len(asc)
            packaging = "direct_ascii_members"
            samples = sorted({asc[0], asc[len(asc) // 2], asc[-1]})
            headers = {
                name: validate_ascii_header(archive, name)
                for name in samples
            }
        elif nested:
            tile_count = len(nested)
            packaging = "nested_per_tile_zip"
            sample_zips = sorted(
                {nested[0], nested[len(nested) // 2], nested[-1]}
            )
            headers: dict[str, dict[str, float]] = {}
            for nested_name in sample_zips:
                with archive.open(nested_name) as handle:
                    payload = handle.read()
                with zipfile.ZipFile(io.BytesIO(payload)) as inner:
                    inner_names = safe_names(inner)
                    inner_asc = sorted(
                        name
                        for name in inner_names
                        if name.lower().endswith(".asc")
                    )
                    if len(inner_asc) != 1:
                        raise ValueError(
                            "nested Terrain50 tile must contain exactly one "
                            f"ASCII grid: {nested_name}"
                        )
                    headers[
                        f"{nested_name}!{inner_asc[0]}"
                    ] = validate_ascii_header(inner, inner_asc[0])
        else:
            raise ValueError(
                "Terrain50 package contains neither direct ASCII tiles nor nested tile ZIPs"
            )

        if tile_count != expected_tiles:
            raise ValueError(
                "Terrain50 national grid tile count mismatch: "
                f"expected={expected_tiles} actual={tile_count} packaging={packaging}"
            )

    return {
        "archive_entries": len(names),
        "ascii_tile_count": tile_count,
        "expected_national_tile_count": expected_tiles,
        "national_tile_count_exact_match": tile_count == expected_tiles,
        "direct_ascii_count": len(asc),
        "nested_tile_zip_count": len(nested),
        "gml_count": len(gml),
        "prj_count": len(prj),
        "packaging": packaging,
        "sample_headers": headers,
    }


def download_to(
    url: str,
    output: Path,
    timeout: int,
    api_key: str | None,
) -> tuple[str, dict[str, str]]:
    if not url.startswith("https://"):
        raise ValueError("OS download URL must use HTTPS")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix="terrain50_",
        suffix=".zip.tmp",
        dir=output.parent,
    )
    os.close(fd)
    temp = Path(temp_name)
    total = 0
    try:
        with request(url, timeout, api_key) as response, temp.open("wb") as handle:
            final_url = response.geturl()
            if not str(final_url).startswith("https://"):
                raise ValueError(
                    f"OS download resolved to non-HTTPS URL: {final_url}"
                )
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
                    raise ValueError(
                        f"Terrain50 download exceeds {MAX_BYTES} bytes"
                    )
                handle.write(chunk)
        if total == 0:
            raise ValueError("Terrain50 download is empty")
        temp.replace(output)
        return final_url, headers
    except Exception:
        temp.unlink(missing_ok=True)
        raise


def _load_previous(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _cache_provenance_ok(
    previous: dict[str, Any],
    archive: Path,
    archive_sha256: str,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if previous.get("official_catalog_verified") is not True:
        reasons.append("previous_official_catalog_verified_missing")
    if previous.get("product_id") != PRODUCT_ID:
        reasons.append("previous_product_id_mismatch")
    if previous.get("area") != AREA:
        reasons.append("previous_area_mismatch")
    if previous.get("format") != FORMAT:
        reasons.append("previous_format_mismatch")
    if (
        str(previous.get("archive_sha256") or "").lower()
        != archive_sha256.lower()
    ):
        reasons.append("previous_archive_sha256_mismatch")
    if int(previous.get("archive_size_bytes") or -1) != archive.stat().st_size:
        reasons.append("previous_archive_size_mismatch")
    if not str(previous.get("catalog_sha256") or "").strip():
        reasons.append("previous_catalog_sha256_missing")
    resolved = str(previous.get("resolved_download_url") or "")
    if not resolved.startswith("https://"):
        reasons.append("previous_resolved_download_url_not_https")
    return not reasons, reasons


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OS_DATA_HUB_API_KEY"),
    )
    parser.add_argument(
        "--archive",
        type=Path,
        help=(
            "Validate an already downloaded official archive instead of downloading."
        ),
    )
    parser.add_argument(
        "--expected-ascii-tiles",
        "--min-ascii-tiles",
        dest="expected_ascii_tiles",
        type=int,
        default=OFFICIAL_GB_GRID_TILE_COUNT,
        help=(
            "Exact national grid tile count. The legacy --min-ascii-tiles alias "
            "is retained for compatibility but is now enforced as an exact count."
        ),
    )
    parser.add_argument("--max-cache-age-hours", type=float, default=24.0)
    args = parser.parse_args()

    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    archive = (
        args.archive.resolve()
        if args.archive
        else out / "OS_Terrain50_July_2026_GB_ASCII_Grid.zip"
    )
    provenance_path = out / "terrain50_official_api_provenance.json"
    catalog = None
    catalog_hash = None
    selected = None
    response_headers: dict[str, str] = {}
    previous_manifest = _load_previous(provenance_path)
    candidate_cache = (
        not args.archive
        and archive.is_file()
        and args.max_cache_age_hours > 0
        and time.time() - archive.stat().st_mtime
        <= args.max_cache_age_hours * 3600
    )
    precomputed_archive_sha = (
        sha256_file(archive) if candidate_cache else None
    )
    cache_reused = False
    cache_reuse_reasons: list[str] = []
    if candidate_cache and precomputed_archive_sha:
        cache_reused, cache_reuse_reasons = _cache_provenance_ok(
            previous_manifest,
            archive,
            precomputed_archive_sha,
        )

    if cache_reused:
        selected = {
            "cache_reused": True,
            "max_cache_age_hours": args.max_cache_age_hours,
            "prior_selected_download_metadata": previous_manifest.get(
                "selected_download_metadata"
            ),
        }
        final_url = str(previous_manifest["resolved_download_url"])
        catalog_hash = str(previous_manifest["catalog_sha256"])
        official_catalog_verified = True
    elif not args.archive:
        with request(
            catalog_url(args.api_key),
            args.timeout,
            args.api_key,
        ) as response:
            final_catalog_url = response.geturl()
            if not str(final_catalog_url).startswith("https://api.os.uk/"):
                raise ValueError(
                    "OS catalog resolved off official API host: "
                    f"{final_catalog_url}"
                )
            catalog = json.load(response)
        catalog_hash = sha256_json(catalog)
        selected = choose_candidate(flatten_downloads(catalog))
        source_url = candidate_url(selected) or redirect_url(args.api_key)
        final_url, response_headers = download_to(
            source_url,
            archive,
            args.timeout,
            args.api_key,
        )
        precomputed_archive_sha = None
        official_catalog_verified = True
    else:
        final_url = str(archive)
        official_catalog_verified = False
        selected = {"archive_argument": True}

    validation = validate_zip(archive, args.expected_ascii_tiles)
    archive_hash = precomputed_archive_sha or sha256_file(archive)
    if (
        cache_reused
        and archive_hash.lower()
        != str(previous_manifest.get("archive_sha256") or "").lower()
    ):
        raise ValueError(
            "Terrain50 cache hash changed after provenance validation"
        )

    manifest = {
        "schema_version": 3,
        "slot_id": "height_difference_3",
        "product_id": PRODUCT_ID,
        "area": AREA,
        "format": FORMAT,
        "official_catalog_url": catalog_url(None),
        "official_redirect_url": redirect_url(None),
        "official_product_supply_url": OFFICIAL_PRODUCT_SUPPLY_URL,
        "official_catalog_verified": official_catalog_verified,
        "catalog_sha256": catalog_hash,
        "selected_download_metadata": selected,
        "resolved_download_url": final_url,
        "response_headers": response_headers,
        "cache_candidate_recent": candidate_cache,
        "cache_reused": cache_reused,
        "cache_provenance_verified": cache_reused,
        "cache_reuse_rejection_reasons": (
            [] if cache_reused else cache_reuse_reasons
        ),
        "archive_path": str(archive),
        "archive_size_bytes": archive.stat().st_size,
        "archive_sha256": archive_hash,
        **validation,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    provenance_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": True,
                "ascii_tiles": validation["ascii_tile_count"],
                "expected_ascii_tiles": validation[
                    "expected_national_tile_count"
                ],
                "national_tile_count_exact_match": validation[
                    "national_tile_count_exact_match"
                ],
                "archive_sha256": manifest["archive_sha256"],
                "cache_reused": cache_reused,
                "official_catalog_verified": official_catalog_verified,
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            ),
            file=sys.stderr,
        )
        raise

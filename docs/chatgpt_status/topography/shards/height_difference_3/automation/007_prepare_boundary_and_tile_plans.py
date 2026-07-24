#!/usr/bin/env python3
"""Prepare HMLR, EA and OS Terrain 50 plans for three real candidates.

The script creates deterministic URLs/tile keys only. It does not download
heavy rasters and does not write elevation measurements.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

HMLR_DOWNLOAD_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
EA_ARCGIS_LAYER = (
    "https://services-eu1.arcgis.com/KB6uNVj5ZcJr7jUP/ArcGIS/rest/services/"
    "LIDAR_Composite_Catalogues/FeatureServer/2/query"
)


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((" ".join(self._text).strip(), self._href))
            self._href = None
            self._text = []


def _normal_name(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()
    for prefix in ("city of ", "the "):
        if text.startswith(prefix):
            text = text[len(prefix):]
    return " ".join(text.split())


def _grid_letters(easting: float, northing: float) -> str:
    e100k = int(easting) // 100000
    n100k = int(northing) // 100000
    if not (0 <= e100k <= 6 and 0 <= n100k <= 12):
        raise ValueError("coordinate outside British National Grid letter extent")
    l1 = (19 - n100k) - (19 - n100k) % 5 + (e100k + 10) // 5
    l2 = (19 - n100k) * 5 % 25 + e100k % 5
    if l1 > 7:
        l1 += 1
    if l2 > 7:
        l2 += 1
    return chr(l1 + 65) + chr(l2 + 65)


def _terrain50_tile(easting: float, northing: float) -> dict[str, Any]:
    letters = _grid_letters(easting, northing)
    e10 = (int(easting) % 100000) // 10000
    n10 = (int(northing) % 100000) // 10000
    sw_e = (int(easting) // 10000) * 10000
    sw_n = (int(northing) // 10000) * 10000
    key = f"{letters}{e10}{n10}"
    return {
        "tile_key": key,
        "tile_key_lower": key.lower(),
        "bbox_epsg27700": [sw_e, sw_n, sw_e + 10000, sw_n + 10000],
        "local_search_patterns": [
            f"**/{key.lower()}*.asc",
            f"**/{key.lower()}*.gml",
            f"**/{key.lower()}*.zip",
        ],
    }


def _ea_arcgis_query(easting: float, northing: float) -> str:
    query = {
        "f": "json",
        "geometry": f"{easting:.3f},{northing:.3f}",
        "geometryType": "esriGeometryPoint",
        "inSR": "27700",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FILENAME,TILENAME,POLYGON_ID,RESOLUTION,YEAR,OD_DTM_FN,SD_FLOWN,ED_FLOWN",
        "returnGeometry": "false",
    }
    return f"{EA_ARCGIS_LAYER}?{urllib.parse.urlencode(query)}"


def _load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    candidates = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("starter manifest has no candidates")
    return [dict(value) for value in candidates]


def _fetch_hmlr_links(timeout: int) -> tuple[list[tuple[str, str]], str]:
    request = urllib.request.Request(
        HMLR_DOWNLOAD_PAGE,
        headers={"User-Agent": "TerraYield-AAYS/height_difference_3"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
    parser = LinkParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    return parser.links, hashlib.sha256(body).hexdigest()


def _match_authority(authority: str, links: list[tuple[str, str]]) -> dict[str, Any]:
    target = _normal_name(authority)
    matches = []
    for text, href in links:
        normal = _normal_name(text)
        if normal == target and href:
            matches.append(
                {
                    "link_text": text,
                    "url": urllib.parse.urljoin(HMLR_DOWNLOAD_PAGE, href),
                }
            )
    return {
        "authority": authority,
        "normalized_authority": target,
        "exact_normalized_match_count": len(matches),
        "matches": matches,
        "status": "EXACT_LINK_RESOLVED" if len(matches) == 1 else "NO_UNIQUE_EXACT_LINK",
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starter-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args(argv)

    candidates = _load_candidates(args.starter_manifest)
    links: list[tuple[str, str]] = []
    page_sha256 = None
    hmlr_error = None
    if not args.no_network:
        try:
            links, page_sha256 = _fetch_hmlr_links(args.timeout)
        except Exception as exc:
            hmlr_error = f"{type(exc).__name__}: {exc}"

    plans = []
    for row in candidates:
        easting = float(row["bng_easting"])
        northing = float(row["bng_northing"])
        authority = str(row.get("local_authority_name", "")).strip()
        plans.append(
            {
                "row_no": row.get("row_no"),
                "parcel_id": row.get("parcel_id"),
                "hmlr_authority_plan": (
                    _match_authority(authority, links)
                    if links
                    else {
                        "authority": authority,
                        "status": "NETWORK_NOT_QUERIED" if args.no_network else "HMLR_PAGE_QUERY_FAILED",
                        "matches": [],
                    }
                ),
                "ea_arcgis_dtm_extent_query_url": _ea_arcgis_query(easting, northing),
                "os_terrain50": _terrain50_tile(easting, northing),
                "measurement_status": "NOT_SAMPLED",
                "measured_value_promoted": False,
            }
        )

    output = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "candidate_count": len(plans),
        "hmlr_download_page": HMLR_DOWNLOAD_PAGE,
        "hmlr_page_sha256": page_sha256,
        "hmlr_error": hmlr_error,
        "plans": plans,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    _write_json(args.output, output)
    print(json.dumps({"ok": True, "plans": len(plans), "hmlr_links": len(links)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

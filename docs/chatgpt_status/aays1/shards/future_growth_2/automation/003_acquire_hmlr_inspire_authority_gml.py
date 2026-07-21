#!/usr/bin/env python3
"""Acquire current HM Land Registry INSPIRE GML files for future_growth_2 authorities.

The official download page is parsed at runtime. Only exact local-authority rows are
accepted. Every downloaded file is validated as non-empty XML/GML and hashed.
No parcel match or product score is produced by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

DEFAULT_DOWNLOAD_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
OFFICIAL_HOST = "use-land-property-data.service.gov.uk"

def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", html.unescape(text).lower()).strip()

class _RowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_row = False
        self.row_text: list[str] = []
        self.row_links: list[str] = []
        self.rows: list[tuple[str, list[str]]] = []
        self._anchor_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self.in_row = True
            self.row_text = []
            self.row_links = []
        if self.in_row and tag == "a":
            self._anchor_href = dict(attrs).get("href")
            if self._anchor_href:
                self.row_links.append(self._anchor_href)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a":
            self._anchor_href = None
        if tag == "tr" and self.in_row:
            self.rows.append((" ".join(self.row_text), list(self.row_links)))
            self.in_row = False

    def handle_data(self, data: str) -> None:
        if self.in_row and data.strip():
            self.row_text.append(data.strip())

def parse_authority_links(page_html: str, page_url: str = DEFAULT_DOWNLOAD_PAGE) -> dict[str, str]:
    parser = _RowParser()
    parser.feed(page_html)
    out: dict[str, str] = {}
    for row_text, links in parser.rows:
        for href in links:
            absolute = urljoin(page_url, href)
            parsed = urlparse(absolute)
            if parsed.netloc.lower() != OFFICIAL_HOST:
                continue
            if not (parsed.path.lower().endswith(".gml") or ".gml" in parsed.path.lower()):
                continue
            authority = re.sub(r"\bdownload\b|\bgml\b", " ", row_text, flags=re.I)
            authority = re.sub(r"\s+", " ", authority).strip(" .|")
            if authority:
                out[norm(authority)] = absolute
    return out

def candidate_authorities(payload: dict[str, Any]) -> list[str]:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("candidate payload lacks candidates array")
    authorities: set[str] = set()
    for row in candidates:
        if not isinstance(row, dict):
            continue
        name = str(row.get("local_authority") or "").strip()
        if not name:
            continue
        if name.startswith("London Borough of ") or name.startswith("Royal Borough of ") or name in {
            "City of London Corporation", "City of Westminster"
        }:
            authorities.add(name)
    if not authorities:
        raise ValueError("no HMLR local-authority names found in candidate payload")
    return sorted(authorities)

def validate_gml_bytes(data: bytes, *, min_bytes: int = 256) -> None:
    if len(data) < min_bytes:
        raise ValueError(f"GML payload too small: {len(data)} bytes")
    head = data[:8192].lstrip()
    lowered = head.lower()
    if not (head.startswith(b"<?xml") or b"<gml:" in lowered or b"featurecollection" in lowered):
        raise ValueError("payload does not look like XML/GML")

def fetch_bytes(url: str, timeout: int) -> tuple[bytes, str | None]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AAYS-future-growth-2/1.0 official-source-verifier"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--download-page-url", default=DEFAULT_DOWNLOAD_PAGE)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    payload = json.loads(args.candidate_json.read_text(encoding="utf-8"))
    authorities = candidate_authorities(payload)

    page_bytes, page_content_type = fetch_bytes(args.download_page_url, args.timeout)
    page_text = page_bytes.decode("utf-8", errors="replace")
    authority_links = parse_authority_links(page_text, args.download_page_url)

    missing = [a for a in authorities if norm(a) not in authority_links]
    if missing:
        raise RuntimeError(f"official HMLR page lacks exact authority rows: {missing}")

    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    downloads: list[dict[str, Any]] = []
    for authority in authorities:
        url = authority_links[norm(authority)]
        data, content_type = fetch_bytes(url, args.timeout)
        validate_gml_bytes(data)
        filename = re.sub(r"[^A-Za-z0-9]+", "_", authority).strip("_") + ".gml"
        path = out_dir / filename
        path.write_bytes(data)
        downloads.append({
            "authority": authority,
            "source_url": url,
            "content_type": content_type,
            "path": str(path),
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "validation": "PASS_XML_GML_SIGNATURE",
        })

    manifest = {
        "schema_version": 1,
        "slot_id": "future_growth_2",
        "source": "HM Land Registry INSPIRE Index Polygons",
        "official_download_page": args.download_page_url,
        "page_content_type": page_content_type,
        "requested_authority_count": len(authorities),
        "downloaded_authority_count": len(downloads),
        "downloads": downloads,
        "parcel_matches_written": 0,
        "future_growth_scores_written": 0,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "final_ready": False,
    }
    manifest_path = out_dir / "hmlr_inspire_download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "authorities": len(downloads), "manifest": str(manifest_path)}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

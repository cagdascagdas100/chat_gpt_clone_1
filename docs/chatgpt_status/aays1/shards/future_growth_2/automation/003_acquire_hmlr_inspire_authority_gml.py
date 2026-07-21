#!/usr/bin/env python3
"""Acquire current HM Land Registry INSPIRE GML files for future_growth_2 authorities.

The official download page is parsed at runtime. The service labels links as GML but
currently serves authority-specific ZIP archives. Exact official-host rows are required,
ZIP members are extracted in memory with zip-slip/zip-bomb guards, and the resulting GML
is signature-checked and hashed. No parcel match or product score is produced.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import urllib.request
import zipfile
from http.cookiejar import CookieJar
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urljoin, urlparse

DEFAULT_DOWNLOAD_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
OFFICIAL_HOST = "use-land-property-data.service.gov.uk"
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_GML_BYTES = 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250.0


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", html.unescape(text).lower()).strip()


class _RowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_row = False
        self.row_text: list[str] = []
        self.row_links: list[str] = []
        self.rows: list[tuple[str, list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self.in_row = True
            self.row_text = []
            self.row_links = []
        elif self.in_row and tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.row_links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "tr" and self.in_row:
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
            path = parsed.path.lower()
            if not (path.endswith(".zip") or path.endswith(".gml") or path.endswith(".xml")):
                continue
            authority = re.sub(r"\bdownload\b|\bgml\b|\bzip\b", " ", row_text, flags=re.I)
            authority = re.sub(r"\s+", " ", authority).strip(" .|")
            if authority:
                key = norm(authority)
                if key in out and out[key] != absolute:
                    raise ValueError(f"duplicate official HMLR links for authority {authority!r}")
                out[key] = absolute
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


def validate_gml_bytes(data: bytes, *, min_bytes: int = 128) -> None:
    if len(data) < min_bytes:
        raise ValueError(f"GML payload too small: {len(data)} bytes")
    if len(data) > MAX_GML_BYTES:
        raise ValueError(f"GML payload exceeds safety limit: {len(data)} bytes")
    head = data[:16384].lstrip().lower()
    if not (head.startswith(b"<?xml") or b"<gml:" in head or b"featurecollection" in head):
        raise ValueError("payload does not look like XML/GML")


def _safe_member_name(name: str) -> None:
    path = PurePosixPath(name.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe ZIP member path: {name!r}")


def extract_gml_payload(data: bytes, source_url: str) -> tuple[bytes, str | None, str]:
    path = urlparse(source_url).path.lower()
    looks_zip = data.startswith(b"PK\x03\x04") or path.endswith(".zip")
    if not looks_zip:
        validate_gml_bytes(data)
        return data, None, "RAW_GML"
    if len(data) > MAX_ARCHIVE_BYTES:
        raise ValueError(f"HMLR ZIP exceeds safety limit: {len(data)} bytes")
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise ValueError("HMLR payload is not a valid ZIP archive") from exc
    members = []
    for info in archive.infolist():
        _safe_member_name(info.filename)
        if info.is_dir():
            continue
        if info.filename.lower().endswith((".gml", ".xml")):
            if info.file_size <= 0 or info.file_size > MAX_GML_BYTES:
                raise ValueError(f"invalid GML member size: {info.file_size}")
            compressed = max(1, info.compress_size)
            if info.file_size / compressed > MAX_COMPRESSION_RATIO:
                raise ValueError("GML ZIP member compression ratio exceeds safety limit")
            members.append(info)
    if len(members) != 1:
        raise ValueError(f"expected exactly one GML/XML member, found {len(members)}")
    info = members[0]
    gml = archive.read(info)
    validate_gml_bytes(gml)
    return gml, info.filename, "ZIP_GML"


def build_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))


def fetch_bytes(opener: urllib.request.OpenerDirector, url: str, timeout: int, accept: str) -> tuple[bytes, str | None, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 AAYS-future-growth-2/2.0 official-source-verifier",
            "Accept": accept,
        },
    )
    with opener.open(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type"), response.geturl()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--download-page-url", default=DEFAULT_DOWNLOAD_PAGE)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    payload = json.loads(args.candidate_json.read_text(encoding="utf-8"))
    if payload.get("slot_id") != "future_growth_2":
        raise ValueError("wrong slot_id")
    authorities = candidate_authorities(payload)
    opener = build_opener()

    page_bytes, page_content_type, page_final_url = fetch_bytes(
        opener, args.download_page_url, args.timeout, "text/html,application/xhtml+xml"
    )
    page_text = page_bytes.decode("utf-8", errors="replace")
    authority_links = parse_authority_links(page_text, args.download_page_url)

    missing = [a for a in authorities if norm(a) not in authority_links]
    if missing:
        raise RuntimeError(f"official HMLR page lacks exact authority rows: {missing}")

    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    downloads: list[dict[str, Any]] = []
    for authority in authorities:
        archive_url = authority_links[norm(authority)]
        archive_data, content_type, final_url = fetch_bytes(
            opener, archive_url, args.timeout, "application/zip,application/gml+xml,application/xml,*/*"
        )
        gml_data, member_name, transport = extract_gml_payload(archive_data, archive_url)
        filename = re.sub(r"[^A-Za-z0-9]+", "_", authority).strip("_") + ".gml"
        path = out_dir / filename
        path.write_bytes(gml_data)
        downloads.append({
            "authority": authority,
            "source_archive_url": archive_url,
            "resolved_download_url": final_url,
            "content_type": content_type,
            "transport": transport,
            "archive_size_bytes": len(archive_data),
            "archive_sha256": hashlib.sha256(archive_data).hexdigest(),
            "gml_member": member_name,
            "path": str(path),
            "size_bytes": len(gml_data),
            "sha256": hashlib.sha256(gml_data).hexdigest(),
            "validation": "PASS_EXACT_OFFICIAL_ROW_AND_XML_GML_SIGNATURE",
        })

    manifest = {
        "schema_version": 2,
        "slot_id": "future_growth_2",
        "source": "HM Land Registry INSPIRE Index Polygons",
        "official_download_page": args.download_page_url,
        "download_page_final_url": page_final_url,
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

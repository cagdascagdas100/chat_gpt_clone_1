#!/usr/bin/env python3
"""Download current HMLR INSPIRE files for validated starter candidates.

Only a unique normalized local-authority match is accepted. Downloads are
hashed and inspected; ambiguous links, HTML error pages and unsafe archives
fail closed. No parcel measurement is produced here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin

import requests

DEFAULT_PAGE = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
MAX_DOWNLOAD_BYTES = 1_500_000_000
MAX_EXTRACTED_BYTES = 2_000_000_000


class AnchorParser(HTMLParser):
    """Capture links with conservative table/list-row context."""

    BLOCK_TAGS = {"tr", "li"}

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str, str]] = []
        self._href: str | None = None
        self._anchor_text: list[str] = []
        self._block_tag: str | None = None
        self._block_text: list[str] = []
        self._block_links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lower = tag.lower()
        if lower in self.BLOCK_TAGS and self._block_tag is None:
            self._block_tag = lower
            self._block_text = []
            self._block_links = []
        if lower == "a":
            self._href = dict(attrs).get("href")
            self._anchor_text = []

    def handle_data(self, data: str) -> None:
        if self._block_tag is not None:
            self._block_text.append(data)
        if self._href is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower == "a" and self._href is not None:
            anchor = " ".join(self._anchor_text).strip()
            if self._block_tag is not None:
                self._block_links.append((anchor, self._href))
            else:
                self.links.append((anchor, self._href, anchor))
            self._href = None
            self._anchor_text = []
        if self._block_tag == lower:
            context = " ".join(self._block_text).strip()
            for anchor, href in self._block_links:
                self.links.append((context, href, anchor))
            self._block_tag = None
            self._block_text = []
            self._block_links = []


def _normal_authority(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()
    prefixes = ("the ", "city of ")
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]
    return " ".join(text.split())


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "authority"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    values = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(values, list) or not values:
        raise ValueError("starter manifest has no candidates")
    result = []
    for index, value in enumerate(values, 1):
        row = dict(value)
        authority = str(row.get("local_authority_name", "")).strip()
        if not authority:
            raise ValueError(f"candidate {index} lacks local_authority_name")
        if "row_no" not in row or "parcel_id" not in row:
            raise ValueError(f"candidate {index} lacks row_no or parcel_id")
        result.append(row)
    return result


def _stream_download(session: requests.Session, url: str, output: Path, timeout: int) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, timeout=timeout, stream=True, allow_redirects=True) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        total = 0
        with output.open("wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError("HMLR download exceeds safety size limit")
                handle.write(chunk)
    if total == 0:
        raise ValueError("HMLR download is empty")
    return {"resolved_url": response.url, "content_type": content_type, "size_bytes": total}


def _safe_extract_gml(archive: Path, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    total = 0
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.is_dir() or Path(info.filename).suffix.lower() not in {".gml", ".xml"}:
                continue
            total += info.file_size
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError("HMLR archive exceeds extracted-size safety limit")
            name = Path(info.filename).name
            target = output_dir / name
            with zf.open(info) as source, target.open("wb") as destination:
                while chunk := source.read(1024 * 1024):
                    destination.write(chunk)
            extracted.append(target)
    if not extracted:
        raise ValueError("HMLR archive contains no GML/XML file")
    return extracted


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starter-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--download-page", default=DEFAULT_PAGE)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--user-agent", default="TerraYield-AAYS/height_difference_3")
    args = parser.parse_args(argv)

    candidates = _load_candidates(args.starter_manifest)
    authorities = sorted({str(row["local_authority_name"]).strip() for row in candidates})
    session = requests.Session()
    session.headers.update({"User-Agent": args.user_agent})
    page_response = session.get(args.download_page, timeout=args.timeout, allow_redirects=True)
    page_response.raise_for_status()
    page_body = page_response.content
    parser_html = AnchorParser()
    parser_html.feed(page_body.decode("utf-8", errors="replace"))

    records = []
    vector_paths: list[str] = []
    blocked = []
    for authority in authorities:
        target = _normal_authority(authority)
        matches = []
        for context, href, anchor_text in parser_html.links:
            if not href:
                continue
            combined = _normal_authority(context)
            href_name = _normal_authority(Path(href.split("?", 1)[0]).stem)
            if (
                target in {combined, href_name}
                or (target and target in href_name)
                or (target and target in combined and "download" in combined)
            ):
                matches.append({"context": context, "anchor_text": anchor_text, "url": urljoin(page_response.url, href)})
        unique = {item["url"]: item for item in matches}
        matches = list(unique.values())
        if len(matches) != 1:
            blocked.append({"authority": authority, "status": "NO_UNIQUE_EXACT_DOWNLOAD_LINK", "matches": matches})
            continue

        match = matches[0]
        authority_dir = args.output_dir / "hmlr" / _slug(authority)
        raw_path = authority_dir / "source_download"
        meta = _stream_download(session, match["url"], raw_path, args.timeout)
        head = raw_path.read_bytes()[:512].lstrip().lower()
        if head.startswith(b"<html") or b"<!doctype html" in head:
            raise ValueError(f"HMLR source for {authority} returned HTML instead of GML/archive")

        if zipfile.is_zipfile(raw_path):
            vectors = _safe_extract_gml(raw_path, authority_dir / "extracted")
            container_type = "zip"
        else:
            suffix = Path(match["url"].split("?", 1)[0]).suffix.lower()
            final_path = authority_dir / ("source.gml" if suffix not in {".gml", ".xml"} else f"source{suffix}")
            raw_path.replace(final_path)
            vectors = [final_path]
            container_type = "direct"

        vector_info = []
        for vector in vectors:
            info = {"path": str(vector), "size_bytes": vector.stat().st_size, "sha256": _sha256(vector)}
            vector_info.append(info)
            vector_paths.append(str(vector))
        records.append(
            {
                "authority": authority,
                "normalized_authority": target,
                "download_link": match,
                "resolved_url": meta["resolved_url"],
                "content_type": meta["content_type"],
                "container_type": container_type,
                "vectors": vector_info,
            }
        )

    status = "READY" if len(records) == len(authorities) and not blocked else "BLOCKED_HMLR_SOURCE_PREPARATION"
    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "status": status,
        "download_page": args.download_page,
        "download_page_resolved_url": page_response.url,
        "download_page_sha256": hashlib.sha256(page_body).hexdigest(),
        "candidate_count": len(candidates),
        "authority_count": len(authorities),
        "prepared_authority_count": len(records),
        "records": records,
        "blocked": blocked,
        "vector_paths": vector_paths,
        "nearest_or_fuzzy_authority_match_used": False,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    output = args.output_dir / "hmlr_source_manifest.json"
    _write(output, payload)
    print(json.dumps({"ok": status == "READY", "status": status, "manifest": str(output)}))
    return 0 if status == "READY" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

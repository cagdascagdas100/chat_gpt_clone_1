#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import re
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
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str, str]] = []
        self.href: str | None = None
        self.anchor: list[str] = []
        self.context: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"tr", "li"}:
            self.depth += 1
            self.context = []
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.anchor = []

    def handle_data(self, data: str) -> None:
        if self.depth:
            self.context.append(data)
        if self.href is not None:
            self.anchor.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.href is not None:
            self.links.append((" ".join(self.context).strip(), " ".join(self.anchor).strip(), self.href))
            self.href = None
            self.anchor = []
        if tag in {"tr", "li"} and self.depth:
            self.depth -= 1


def _normal(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()
    for prefix in ("the ", "city of "):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return " ".join(text.split())


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "authority"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("starter manifest must contain exactly three candidates")
    return [dict(row) for row in rows]


def _resolve(page_html: str, page_url: str, authorities: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parser = AnchorParser()
    parser.feed(page_html)
    records: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for authority in authorities:
        target = _normal(authority)
        matches: list[dict[str, Any]] = []
        for context, anchor, href in parser.links:
            if not href:
                continue
            combined = _normal(context)
            href_stem = _normal(Path(href.split("?", 1)[0]).stem)
            if target in {combined, href_stem} or (target and target in href_stem) or (target and target in combined and "download" in combined):
                matches.append({"context": context, "anchor_text": anchor, "url": urljoin(page_url, href)})
        matches = list({item["url"]: item for item in matches}.values())
        if len(matches) != 1:
            blocked.append({"authority": authority, "status": "NO_UNIQUE_EXACT_DOWNLOAD_LINK", "matches": matches})
        else:
            records.append({"authority": authority, "normalized_authority": target, "download_link": matches[0]})
    return records, blocked


def _download(session: requests.Session, url: str, target: Path, timeout: int) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with session.get(url, timeout=timeout, stream=True, allow_redirects=True) as response:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        with target.open("wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise ValueError("download exceeds safety limit")
                handle.write(chunk)
        resolved_url = response.url
    if total == 0:
        raise ValueError("empty HMLR download")
    return {"resolved_url": resolved_url, "content_type": content_type, "size_bytes": total}


def _extract(raw: Path, output_dir: Path) -> list[Path]:
    head = raw.read_bytes()[:512].lstrip().lower()
    if head.startswith(b"<html") or b"<!doctype html" in head:
        raise ValueError("HMLR returned HTML")
    if not zipfile.is_zipfile(raw):
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / "source.gml"
        raw.replace(destination)
        return [destination]
    output_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    paths: list[Path] = []
    with zipfile.ZipFile(raw) as archive:
        for info in archive.infolist():
            if info.is_dir() or Path(info.filename).suffix.lower() not in {".gml", ".xml"}:
                continue
            if Path(info.filename).is_absolute() or ".." in Path(info.filename).parts:
                raise ValueError("unsafe archive path")
            total += info.file_size
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError("extracted size limit exceeded")
            destination = output_dir / Path(info.filename).name
            with archive.open(info) as source, destination.open("wb") as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
            paths.append(destination)
    if not paths:
        raise ValueError("archive contains no GML/XML")
    return paths


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starter-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--download-page", default=DEFAULT_PAGE)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--resolve-only", action="store_true")
    parser.add_argument("--page-html", type=Path)
    args = parser.parse_args(argv)
    try:
        candidates = _load_candidates(args.starter_manifest)
        authorities = sorted({str(row["local_authority_name"]).strip() for row in candidates})
        session = requests.Session()
        session.headers["User-Agent"] = "TerraYield-AAYS/height_difference_2"
        if args.page_html:
            page_body = args.page_html.read_bytes()
            resolved_page = args.download_page
        else:
            response = session.get(args.download_page, timeout=args.timeout, allow_redirects=True)
            response.raise_for_status()
            page_body = response.content
            resolved_page = response.url
        records, blocked = _resolve(page_body.decode("utf-8", errors="replace"), resolved_page, authorities)
        vector_paths: list[str] = []
        if not args.resolve_only:
            for record in records:
                authority_dir = args.output_dir / "hmlr" / _slug(record["authority"])
                raw_path = authority_dir / "source_download"
                metadata = _download(session, record["download_link"]["url"], raw_path, args.timeout)
                vectors = _extract(raw_path, authority_dir / "extracted")
                record.update(metadata)
                record["vectors"] = [
                    {"path": str(path), "size_bytes": path.stat().st_size, "sha256": _sha256(path)} for path in vectors
                ]
                vector_paths.extend(str(path) for path in vectors)
        if args.resolve_only and len(records) == len(authorities) and not blocked:
            status = "READY_HMLR_URLS_RESOLVED"
        elif not args.resolve_only and len(records) == len(authorities) and not blocked:
            status = "READY_HMLR_GML_DOWNLOADED"
        else:
            status = "BLOCKED_HMLR_SOURCE_PREPARATION"
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": status,
            "download_page": args.download_page,
            "download_page_resolved_url": resolved_page,
            "download_page_sha256": hashlib.sha256(page_body).hexdigest(),
            "candidate_count": len(candidates),
            "authority_count": len(authorities),
            "prepared_authority_count": len(records),
            "resolve_only": args.resolve_only,
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
        code = 0 if status.startswith("READY") else 2
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": "BLOCKED_HMLR_SOURCE_PREPARATION",
            "error": f"{type(exc).__name__}: {exc}",
            "measurement_values_written": 0,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 2
    _write(args.output_dir / "hmlr_source_manifest.json", payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"]}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

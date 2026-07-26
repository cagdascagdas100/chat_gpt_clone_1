#!/usr/bin/env python3
"""Collect canonical ONS/Home Office release artifacts after official publication.

Stdlib-only, idempotent and fail-closed. It never writes project scores or parcel values.
Before publication it emits RELEASE_PENDING with zero accepted artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

ONS_RELEASE = "https://www.ons.gov.uk/releases/crimeinenglandandwalesyearendingmarch2026"
HO_ANNOUNCEMENT = "https://www.gov.uk/government/statistics/announcements/crime-outcomes-in-england-and-wales-2025-to-2026"
ALLOWED_HOSTS = {"www.ons.gov.uk", "ons.gov.uk", "www.gov.uk", "gov.uk"}
EXPECTED_TITLE = "Crime in England and Wales: year ending March 2026"
MAX_BYTES = 80 * 1024 * 1024


@dataclass(frozen=True)
class Link:
    text: str
    url: str


@dataclass
class ArtifactReceipt:
    row: int
    source: str
    link_text: str
    requested_url: str
    final_url: str | None
    host_allowed: bool
    http_status: int | None
    content_type: str | None
    byte_size: int | None
    sha256: str | None
    extension: str | None
    accepted: bool
    reason: str


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._href: str | None = None
        self._parts: list[str] = []
        self.links: list[Link] = []
        self.title_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._parts = []
        elif tag == "title":
            self._in_title = True

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)
        if self._in_title:
            self.title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            text = re.sub(r"\s+", " ", "".join(self._parts)).strip()
            self.links.append(Link(text=text, url=self._href))
            self._href = None
            self._parts = []
        elif tag == "title":
            self._in_title = False


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        if not host_allowed(newurl):
            raise URLError(f"redirect host is not allowed: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def host_allowed(url: str) -> bool:
    return (urlparse(url).hostname or "").lower() in ALLOWED_HOSTS


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch(url: str, timeout: int, max_bytes: int = MAX_BYTES) -> tuple[int, str, dict[str, str], bytes]:
    if not host_allowed(url):
        raise ValueError(f"host not allowed: {url}")
    req = Request(url, headers={"User-Agent": "AAYS-security-public-safety-release-collector/1.0"})
    opener = build_opener(SafeRedirect())
    with opener.open(req, timeout=timeout) as response:
        status = int(getattr(response, "status", 200))
        final_url = response.geturl()
        if not host_allowed(final_url):
            raise ValueError(f"final host not allowed: {final_url}")
        headers = {k.lower(): v for k, v in response.headers.items()}
        declared = headers.get("content-length")
        if declared and int(declared) > max_bytes:
            raise ValueError(f"declared content-length exceeds {max_bytes}")
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(f"response exceeds {max_bytes} bytes")
        return status, final_url, headers, data


def decode_html(data: bytes, content_type: str | None) -> str:
    charset = "utf-8"
    if content_type:
        match = re.search(r"charset=([^;\s]+)", content_type, flags=re.I)
        if match:
            charset = match.group(1).strip('"\'')
    return data.decode(charset, errors="replace")


def parse_links(base_url: str, html: str) -> tuple[str, list[Link]]:
    parser = LinkParser()
    parser.feed(html)
    title = re.sub(r"\s+", " ", "".join(parser.title_parts)).strip()
    links: list[Link] = []
    seen: set[str] = set()
    for link in parser.links:
        absolute = urljoin(base_url, link.url)
        if not host_allowed(absolute) or absolute in seen:
            continue
        seen.add(absolute)
        links.append(Link(link.text, absolute))
    return title, links


def is_release_published(html: str) -> bool:
    lowered = re.sub(r"\s+", " ", html).lower()
    if "this release is not yet published" in lowered:
        return False
    return "released:" in lowered or "publications" in lowered or "download" in lowered


def artifact_candidate(link: Link) -> bool:
    text = link.text.lower()
    path = urlparse(link.url).path.lower()
    keywords = (
        "crime in england and wales",
        "appendix",
        "police force area",
        "personal crime prevalence",
        "household crime prevalence",
        "crime outcomes",
        "data table",
        "open data",
    )
    extensions = (".xlsx", ".xls", ".ods", ".csv", ".zip", ".pdf")
    return any(k in text for k in keywords) or path.endswith(extensions)


def inspect_artifact(row: int, source: str, link: Link, timeout: int) -> ArtifactReceipt:
    try:
        status, final_url, headers, data = fetch(link.url, timeout)
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower() or None
        extension = Path(urlparse(final_url).path).suffix.lower() or None
        html_like = data[:256].lstrip().lower().startswith((b"<!doctype html", b"<html"))
        downloadable = extension in {".xlsx", ".xls", ".ods", ".csv", ".zip", ".pdf"}
        accepted = status == 200 and len(data) > 0 and (downloadable or not html_like)
        reason = "PASS_RAW_ARTIFACT" if accepted else "REJECT_NON_ARTIFACT_OR_EMPTY"
        return ArtifactReceipt(
            row=row,
            source=source,
            link_text=link.text,
            requested_url=link.url,
            final_url=final_url,
            host_allowed=True,
            http_status=status,
            content_type=content_type,
            byte_size=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            extension=extension or mimetypes.guess_extension(content_type or ""),
            accepted=accepted,
            reason=reason,
        )
    except (HTTPError, URLError, ValueError, TimeoutError) as exc:
        return ArtifactReceipt(
            row=row,
            source=source,
            link_text=link.text,
            requested_url=link.url,
            final_url=None,
            host_allowed=host_allowed(link.url),
            http_status=getattr(exc, "code", None),
            content_type=None,
            byte_size=None,
            sha256=None,
            extension=Path(urlparse(link.url).path).suffix.lower() or None,
            accepted=False,
            reason=f"FETCH_FAILED:{type(exc).__name__}:{exc}",
        )


def collect(timeout: int, max_artifacts: int) -> dict[str, object]:
    checked_at = utc_now()
    pages: list[dict[str, object]] = []
    candidates: list[tuple[str, Link]] = []
    release_published = False

    for source, url in (("ONS", ONS_RELEASE), ("HOME_OFFICE", HO_ANNOUNCEMENT)):
        try:
            status, final_url, headers, data = fetch(url, timeout, max_bytes=5 * 1024 * 1024)
            html = decode_html(data, headers.get("content-type"))
            title, links = parse_links(final_url, html)
            published = is_release_published(html) if source == "ONS" else "release date" not in html.lower() or "published" in html.lower()
            if source == "ONS":
                release_published = published and EXPECTED_TITLE.lower() in (title + " " + html[:8000]).lower()
            pages.append({
                "source": source,
                "requested_url": url,
                "final_url": final_url,
                "http_status": status,
                "content_type": headers.get("content-type"),
                "byte_size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "title": title,
                "published": published,
                "link_count": len(links),
            })
            candidates.extend((source, link) for link in links if artifact_candidate(link))
        except (HTTPError, URLError, ValueError, TimeoutError) as exc:
            pages.append({"source": source, "requested_url": url, "published": False, "error": f"{type(exc).__name__}:{exc}"})

    unique: list[tuple[str, Link]] = []
    seen: set[str] = set()
    for source, link in candidates:
        if link.url in seen:
            continue
        seen.add(link.url)
        unique.append((source, link))
    unique = unique[:max_artifacts]

    receipts: list[ArtifactReceipt] = []
    if release_published:
        for idx, (source, link) in enumerate(unique, start=1):
            receipts.append(inspect_artifact(idx, source, link, timeout))
            time.sleep(0.15)

    accepted = sum(1 for item in receipts if item.accepted)
    state = "RELEASE_PUBLISHED_ARTIFACTS_COLLECTED" if release_published else "RELEASE_PENDING_NO_ARTIFACTS_ACCEPTED"
    return {
        "schema_version": 1,
        "slot_id": "security_public_safety_1",
        "task_id": "aays1-security-public-safety-1-canonical-acceptance-v17-20260722",
        "checked_at": checked_at,
        "state": state,
        "release_published": release_published,
        "pages": pages,
        "candidate_links_found": len(unique),
        "artifact_receipts": [asdict(item) for item in receipts],
        "summary": {
            "artifacts_inspected": len(receipts),
            "artifacts_accepted": accepted,
            "figures_ingested": 0,
            "stored_values_modified": False,
            "direct_score_inputs_accepted": 0,
        },
        "quality_guards": [
            "Official ONS page state is authoritative; search snippets are not.",
            "Only ons.gov.uk and gov.uk hosts are allowed, including redirects.",
            "Raw bytes, content type, exact size and SHA-256 are recorded.",
            "No project score, parcel value or database write occurs.",
        ],
        "output_semantics": "AREA_LEVEL_PROXY",
        "parcel_measurement": False,
        "fake_data": False,
        "final_ready": False,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--max-artifacts", type=int, default=30)
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.timeout < 5 or args.timeout > 120:
        parser.error("--timeout must be between 5 and 120 seconds")
    if args.max_artifacts < 1 or args.max_artifacts > 100:
        parser.error("--max-artifacts must be between 1 and 100")
    result = collect(args.timeout, args.max_artifacts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

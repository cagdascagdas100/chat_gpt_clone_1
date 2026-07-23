#!/usr/bin/env python3
"""Collect ONS/Home Office release artifacts after verified publication.

Stdlib-only, idempotent and fail-closed. Publication is verified independently
for ONS and Home Office. Downloadable artifacts require type-compatible magic
bytes; official HTML products require an expected product identity. The script
never writes project scores, parcel values or databases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import re
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

ONS_RELEASE = "https://www.ons.gov.uk/releases/crimeinenglandandwalesyearendingmarch2026"
HO_ANNOUNCEMENT = "https://www.gov.uk/government/statistics/announcements/crime-outcomes-in-england-and-wales-2025-to-2026"
ALLOWED_HOSTS = {"www.ons.gov.uk", "ons.gov.uk", "www.gov.uk", "gov.uk"}
EXPECTED_ONS_TITLE = "crime in england and wales: year ending march 2026"
EXPECTED_HO_TITLE = "crime outcomes in england and wales 2025 to 2026"
MAX_BYTES = 80 * 1024 * 1024
PAGE_MAX_BYTES = 5 * 1024 * 1024
TRANSIENT_HTTP = {429, 500, 502, 503, 504}
TRACKING_KEYS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}


@dataclass(frozen=True)
class Link:
    text: str
    url: str


@dataclass
class ArtifactReceipt:
    row: int
    source: str
    artifact_class: str
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


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._href: str | None = None
        self._link_parts: list[str] = []
        self._in_title = False
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[Link] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._link_parts = []
        elif tag == "title":
            self._in_title = True

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)
        if self._href is not None:
            self._link_parts.append(data)
        if self._in_title:
            self.title_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            text = normalize_text("".join(self._link_parts))
            self.links.append(Link(text=text, url=self._href))
            self._href = None
            self._link_parts = []
        elif tag == "title":
            self._in_title = False


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        if not host_allowed(newurl):
            raise URLError(f"redirect target is not allowed: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def host_allowed(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme.lower() == "https" and (parsed.hostname or "").lower() in ALLOWED_HOSTS


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k.lower() not in TRACKING_KEYS]
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.params, urlencode(query), ""))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch(url: str, timeout: int, max_bytes: int = MAX_BYTES) -> tuple[int, str, dict[str, str], bytes]:
    if not host_allowed(url):
        raise ValueError(f"host or scheme not allowed: {url}")
    req = Request(url, headers={"User-Agent": "AAYS-security-public-safety-release-collector/2.0"})
    opener = build_opener(SafeRedirect())
    with opener.open(req, timeout=timeout) as response:
        status = int(getattr(response, "status", 200))
        final_url = canonicalize_url(response.geturl())
        if not host_allowed(final_url):
            raise ValueError(f"final host or scheme not allowed: {final_url}")
        headers = {k.lower(): v for k, v in response.headers.items()}
        declared = headers.get("content-length")
        if declared:
            try:
                declared_size = int(declared)
            except ValueError as exc:
                raise ValueError("invalid content-length") from exc
            if declared_size < 0 or declared_size > max_bytes:
                raise ValueError(f"declared content-length outside 0..{max_bytes}")
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(f"response exceeds {max_bytes} bytes")
        return status, final_url, headers, data


def fetch_with_retry(url: str, timeout: int, max_bytes: int) -> tuple[int, str, dict[str, str], bytes]:
    last: Exception | None = None
    for attempt in range(2):
        try:
            return fetch(url, timeout, max_bytes)
        except HTTPError as exc:
            last = exc
            if exc.code not in TRANSIENT_HTTP or attempt == 1:
                raise
        except (URLError, TimeoutError) as exc:
            last = exc
            if attempt == 1:
                raise
        time.sleep(1.0)
    assert last is not None
    raise last


def decode_html(data: bytes, content_type: str | None) -> str:
    charset = "utf-8"
    if content_type:
        match = re.search(r"charset=([^;\s]+)", content_type, flags=re.I)
        if match:
            charset = match.group(1).strip('"\'')
    return data.decode(charset, errors="replace")


def parse_page(base_url: str, html: str) -> tuple[str, str, list[Link]]:
    parser = PageParser()
    parser.feed(html)
    title = normalize_text("".join(parser.title_parts))
    visible_text = normalize_text(" ".join(parser.text_parts))
    links: list[Link] = []
    seen: set[str] = set()
    for link in parser.links:
        absolute = canonicalize_url(urljoin(base_url, link.url))
        if not host_allowed(absolute) or absolute in seen:
            continue
        seen.add(absolute)
        links.append(Link(link.text, absolute))
    return title, visible_text, links


def ons_release_published(title: str, visible_text: str) -> bool:
    lowered = f"{title} {visible_text}".lower()
    if "this release is not yet published" in lowered or "nid yw'r datganiad hwn wedi'i gyhoeddi eto" in lowered:
        return False
    title_ok = EXPECTED_ONS_TITLE in lowered
    released_marker = re.search(r"\breleased:\s*23\s+july\s+2026\b", lowered) is not None
    products_marker = "publications" in lowered and "data" in lowered
    return title_ok and released_marker and products_marker


def home_office_release_published(final_url: str, title: str, visible_text: str) -> bool:
    lowered = f"{title} {visible_text}".lower()
    path = urlparse(final_url).path.lower()
    if "/announcements/" in path or "official statistics announcement" in lowered:
        return False
    return EXPECTED_HO_TITLE in lowered and "documents" in lowered and "published" in lowered


def classify_link(link: Link) -> str:
    text = link.text.lower()
    path = urlparse(link.url).path.lower()
    combined = f"{text} {path}"
    if "pre-release" in combined or "prerelease" in combined:
        return "EXCLUDED_PRERELEASE"
    if "technical annex" in combined:
        return "HOME_OFFICE_TECHNICAL_ANNEX"
    if "crime outcomes" in combined and ("data table" in combined or path.endswith((".ods", ".xlsx", ".csv"))):
        return "HOME_OFFICE_OUTCOMES_TABLES"
    if "crime outcomes" in combined:
        return "HOME_OFFICE_OUTCOMES_PUBLICATION"
    if "police force area" in combined:
        return "ONS_PFA_TABLES"
    if "personal crime prevalence" in combined:
        return "ONS_CSEW_PERSONAL"
    if "household crime prevalence" in combined:
        return "ONS_CSEW_HOUSEHOLD"
    if "appendix" in combined:
        return "ONS_APPENDIX"
    if EXPECTED_ONS_TITLE in combined or "crime in england and wales" in combined:
        return "ONS_BULLETIN"
    if path.endswith((".xlsx", ".xls", ".ods", ".csv", ".zip", ".pdf")):
        return "OTHER_DOWNLOAD"
    return "NOT_ARTIFACT"


def artifact_candidate(link: Link) -> bool:
    return classify_link(link) not in {"NOT_ARTIFACT", "EXCLUDED_PRERELEASE"}


def extension_from_headers(final_url: str, headers: dict[str, str]) -> str | None:
    extension = Path(urlparse(final_url).path).suffix.lower()
    if extension:
        return extension
    disposition = headers.get("content-disposition", "")
    match = re.search(r"filename\*?=(?:UTF-8''|\")?([^\";]+)", disposition, flags=re.I)
    if match:
        return Path(match.group(1).strip()).suffix.lower() or None
    content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
    return mimetypes.guess_extension(content_type) if content_type else None


def html_error_like(data: bytes, visible_text: str = "") -> bool:
    prefix = data[:512].lstrip().lower()
    text = visible_text.lower()
    return prefix.startswith((b"<!doctype html", b"<html")) and any(
        marker in text for marker in ("page not found", "access denied", "service unavailable", "internal server error")
    )


def validate_download(extension: str | None, content_type: str | None, data: bytes) -> tuple[bool, str]:
    if not data:
        return False, "REJECT_EMPTY"
    ext = (extension or "").lower()
    ctype = (content_type or "").lower()
    prefix = data[:16]
    if ext in {".xlsx", ".ods", ".zip"}:
        return (prefix.startswith(b"PK\x03\x04"), "PASS_ZIP_CONTAINER" if prefix.startswith(b"PK\x03\x04") else "REJECT_BAD_ZIP_MAGIC")
    if ext == ".xls":
        ok = prefix.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
        return ok, "PASS_OLE_XLS" if ok else "REJECT_BAD_XLS_MAGIC"
    if ext == ".pdf":
        ok = data.startswith(b"%PDF-")
        return ok, "PASS_PDF" if ok else "REJECT_BAD_PDF_MAGIC"
    if ext == ".csv" or "text/csv" in ctype:
        head = data[:4096].lstrip().lower()
        if head.startswith((b"<!doctype html", b"<html")):
            return False, "REJECT_HTML_MASQUERADE"
        sample = data[:4096].decode("utf-8-sig", errors="replace")
        ok = "\n" in sample and any(delim in sample for delim in (",", ";", "\t"))
        return ok, "PASS_CSV_TEXT" if ok else "REJECT_INVALID_CSV"
    return False, "REJECT_UNSUPPORTED_DOWNLOAD_TYPE"


def inspect_artifact(row: int, source: str, link: Link, timeout: int) -> ArtifactReceipt:
    artifact_class = classify_link(link)
    try:
        status, final_url, headers, data = fetch_with_retry(link.url, timeout, MAX_BYTES)
        content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower() or None
        extension = extension_from_headers(final_url, headers)
        accepted = False
        reason = "REJECT_UNSUPPORTED"
        if content_type == "text/html" or data[:256].lstrip().lower().startswith((b"<!doctype html", b"<html")):
            html = decode_html(data, headers.get("content-type"))
            title, visible_text, _ = parse_page(final_url, html)
            if html_error_like(data, visible_text):
                reason = "REJECT_HTML_ERROR_PAGE"
            elif artifact_class == "ONS_BULLETIN" and EXPECTED_ONS_TITLE in f"{title} {visible_text}".lower():
                accepted, reason = True, "PASS_OFFICIAL_ONS_HTML_PRODUCT"
            elif artifact_class in {"HOME_OFFICE_OUTCOMES_PUBLICATION", "HOME_OFFICE_TECHNICAL_ANNEX"} and "crime outcomes" in f"{title} {visible_text}".lower():
                accepted, reason = True, "PASS_OFFICIAL_HOME_OFFICE_HTML_PRODUCT"
            else:
                reason = "REJECT_UNEXPECTED_HTML_PRODUCT"
        else:
            accepted, reason = validate_download(extension, content_type, data)
        accepted = accepted and status == 200 and host_allowed(final_url)
        return ArtifactReceipt(
            row=row,
            source=source,
            artifact_class=artifact_class,
            link_text=link.text,
            requested_url=link.url,
            final_url=final_url,
            host_allowed=host_allowed(final_url),
            http_status=status,
            content_type=content_type,
            byte_size=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
            extension=extension,
            accepted=accepted,
            reason=reason,
        )
    except (HTTPError, URLError, ValueError, TimeoutError) as exc:
        return ArtifactReceipt(
            row=row,
            source=source,
            artifact_class=artifact_class,
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
    published_by_source = {"ONS": False, "HOME_OFFICE": False}
    links_by_source: dict[str, list[Link]] = {"ONS": [], "HOME_OFFICE": []}

    for source, url in (("ONS", ONS_RELEASE), ("HOME_OFFICE", HO_ANNOUNCEMENT)):
        try:
            status, final_url, headers, data = fetch_with_retry(url, timeout, PAGE_MAX_BYTES)
            html = decode_html(data, headers.get("content-type"))
            title, visible_text, links = parse_page(final_url, html)
            published = ons_release_published(title, visible_text) if source == "ONS" else home_office_release_published(final_url, title, visible_text)
            published_by_source[source] = published
            links_by_source[source] = links
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
        except (HTTPError, URLError, ValueError, TimeoutError) as exc:
            pages.append({"source": source, "requested_url": url, "published": False, "error": f"{type(exc).__name__}:{exc}"})

    candidates: list[tuple[str, Link]] = []
    seen: set[str] = set()
    for source in ("ONS", "HOME_OFFICE"):
        if not published_by_source[source]:
            continue
        for link in links_by_source[source]:
            if not artifact_candidate(link):
                continue
            canonical = canonicalize_url(link.url)
            if canonical in seen:
                continue
            seen.add(canonical)
            candidates.append((source, Link(link.text, canonical)))
    candidates = candidates[:max_artifacts]

    receipts: list[ArtifactReceipt] = []
    for idx, (source, link) in enumerate(candidates, start=1):
        receipts.append(inspect_artifact(idx, source, link, timeout))
        time.sleep(0.15)

    accepted = sum(1 for item in receipts if item.accepted)
    release_published = published_by_source["ONS"]
    state = "RELEASE_PUBLISHED_ARTIFACTS_COLLECTED" if release_published else "RELEASE_PENDING_NO_ARTIFACTS_ACCEPTED"
    return {
        "schema_version": 2,
        "slot_id": "security_public_safety_1",
        "task_id": "aays1-security-public-safety-1-canonical-acceptance-v17-20260722",
        "checked_at": checked_at,
        "state": state,
        "release_published": release_published,
        "published_by_source": published_by_source,
        "pages": pages,
        "candidate_links_found": len(candidates),
        "artifact_receipts": [asdict(item) for item in receipts],
        "summary": {
            "artifacts_inspected": len(receipts),
            "artifacts_accepted": accepted,
            "figures_ingested": 0,
            "stored_values_modified": False,
            "direct_score_inputs_accepted": 0,
        },
        "quality_guards": [
            "ONS and Home Office publication states are verified independently.",
            "Announcement metadata does not count as a published Home Office release.",
            "Only HTTPS ONS and GOV.UK hosts are allowed, including redirects.",
            "Downloadable artifacts require extension-compatible magic bytes.",
            "Raw bytes, content type, exact size and SHA-256 are recorded.",
            "No project score, parcel value or database write occurs.",
        ],
        "output_semantics": "AREA_LEVEL_PROXY",
        "parcel_measurement": False,
        "fake_data": False,
        "final_ready": False,
    }


def atomic_write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


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
    atomic_write_json(args.output, result)
    print(json.dumps(result["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

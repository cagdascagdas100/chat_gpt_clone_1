#!/usr/bin/env python3
"""Fail-closed publication transition and link-diff monitor for official ONS/GOV.UK pages."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

ONS_URL = "https://www.ons.gov.uk/releases/crimeinenglandandwalesyearendingmarch2026"
HO_URL = "https://www.gov.uk/government/statistics/announcements/crime-outcomes-in-england-and-wales-2025-to-2026"
ALLOWED_HOSTS = {"ons.gov.uk", "www.ons.gov.uk", "gov.uk", "www.gov.uk"}
MAX_PAGE_BYTES = 5 * 1024 * 1024
EXPECTED_ONS_TITLE = "crime in england and wales: year ending march 2026"
EXPECTED_HO_TITLE = "crime outcomes in england and wales 2025 to 2026"

@dataclass(frozen=True)
class PageSnapshot:
    source: str
    requested_url: str
    final_url: str
    http_status: int
    content_type: str
    byte_size: int
    raw_sha256: str
    normalized_sha256: str
    title: str
    publication_state: str
    published: bool
    links: list[str]

class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.links: list[str] = []
        self._in_title = False
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title": self._in_title = True
        elif tag == "a":
            href = dict(attrs).get("href")
            if href: self.links.append(href)
    def handle_endtag(self, tag: str) -> None:
        if tag == "title": self._in_title = False
    def handle_data(self, data: str) -> None:
        if self._in_title: self.title_parts.append(data)

class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not url_allowed(newurl):
            raise URLError(f"redirect URL forbidden: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def url_allowed(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in ALLOWED_HOSTS

def canonical_url(base_url: str, href: str) -> str | None:
    absolute = urljoin(base_url, href)
    if not url_allowed(absolute): return None
    parsed = urlparse(absolute)
    query = "&".join(part for part in parsed.query.split("&") if part and not part.lower().startswith(("utm_", "source=", "campaign=")))
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, "", query, ""))

def normalize_html(html: str) -> str:
    text = html.lower()
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.S)
    text = re.sub(r"\b(?:nonce|data-token|csrf-token)=[\"'][^\"']+[\"']", "", text)
    text = re.sub(r"\b\d{10,13}\b", "<epoch>", text)
    return re.sub(r"\s+", " ", text).strip()

def publication_state(source: str, title: str, html: str) -> tuple[str, bool]:
    normalized = normalize_html(html)
    title_l = title.lower()
    if source == "ONS":
        if "this release is not yet published" in normalized:
            return "NOT_YET_PUBLISHED", False
        expected = EXPECTED_ONS_TITLE in (title_l + " " + normalized[:12000])
        markers = "released:" in normalized and "publications" in normalized and "data" in normalized
        return ("PUBLISHED" if expected and markers else "UNKNOWN"), bool(expected and markers)
    if source == "HOME_OFFICE":
        expected = EXPECTED_HO_TITLE in (title_l + " " + normalized[:12000])
        announcement_only = "official statistics announcement" in normalized or "will be released" in normalized
        documents = "documents" in normalized and "published:" in normalized
        published = expected and documents and not announcement_only
        return ("PUBLISHED" if published else ("ANNOUNCEMENT" if announcement_only else "UNKNOWN")), bool(published)
    raise ValueError(f"unknown source: {source}")

def parse_page(source: str, requested_url: str, final_url: str, status: int, headers: dict[str, str], data: bytes) -> PageSnapshot:
    content_type = headers.get("content-type", "").lower()
    if status != 200: raise ValueError(f"{source} HTTP {status}")
    if "html" not in content_type: raise ValueError(f"{source} non-HTML page: {content_type}")
    html = data.decode("utf-8", errors="replace")
    parser = Parser(); parser.feed(html)
    title = re.sub(r"\s+", " ", "".join(parser.title_parts)).strip()
    links = sorted({u for href in parser.links if (u := canonical_url(final_url, href))})
    state, published = publication_state(source, title, html)
    normalized = normalize_html(html)
    return PageSnapshot(source, requested_url, final_url, status, content_type, len(data), hashlib.sha256(data).hexdigest(), hashlib.sha256(normalized.encode()).hexdigest(), title, state, published, links)

def fetch(url: str, timeout: int, retries: int = 2) -> tuple[int, str, dict[str, str], bytes]:
    if not url_allowed(url): raise ValueError(f"URL forbidden: {url}")
    opener = build_opener(SafeRedirect()); last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = Request(url, headers={"User-Agent": "AAYS-publication-diff-monitor/1.0"})
            with opener.open(req, timeout=timeout) as response:
                final_url = response.geturl()
                if not url_allowed(final_url): raise ValueError(f"final URL forbidden: {final_url}")
                headers = {k.lower(): v for k, v in response.headers.items()}
                declared = headers.get("content-length")
                if declared and int(declared) > MAX_PAGE_BYTES: raise ValueError("declared page size exceeds limit")
                data = response.read(MAX_PAGE_BYTES + 1)
                if len(data) > MAX_PAGE_BYTES: raise ValueError("page size exceeds limit")
                return int(getattr(response, "status", 200)), final_url, headers, data
        except (HTTPError, URLError, TimeoutError) as exc:
            last = exc
            if attempt < retries: time.sleep(0.25 * (2 ** attempt))
    assert last is not None
    raise last

def load_previous(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.exists(): return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "pages" not in data: raise ValueError("previous snapshot schema invalid")
    return data

def previous_map(previous: dict[str, object] | None) -> dict[str, dict[str, object]]:
    if not previous: return {}
    pages = previous.get("pages", [])
    if not isinstance(pages, list): raise ValueError("previous pages invalid")
    return {str(page["source"]): page for page in pages if isinstance(page, dict) and isinstance(page.get("source"), str)}

def compare_page(current: PageSnapshot, old: dict[str, object] | None) -> dict[str, object]:
    old_links = set(old.get("links", [])) if old else set()
    old_published = bool(old.get("published", False)) if old else False
    old_norm = old.get("normalized_sha256") if old else None
    current_links = set(current.links)
    return {"source": current.source, "first_snapshot": old is None, "page_changed": old_norm is not None and old_norm != current.normalized_sha256, "publication_transition": (not old_published) and current.published, "publication_regression": old_published and (not current.published), "added_links": sorted(current_links - old_links), "removed_links": sorted(old_links - current_links), "published": current.published, "publication_state": current.publication_state}

def atomic_write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

def collect(timeout: int, previous: dict[str, object] | None = None) -> dict[str, object]:
    pages: list[PageSnapshot] = []; errors: list[dict[str, str]] = []
    for source, url in (("ONS", ONS_URL), ("HOME_OFFICE", HO_URL)):
        try:
            status, final_url, headers, data = fetch(url, timeout)
            pages.append(parse_page(source, url, final_url, status, headers, data))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            errors.append({"source": source, "error": f"{type(exc).__name__}:{exc}"})
    old_map = previous_map(previous)
    diffs = [compare_page(page, old_map.get(page.source)) for page in pages]
    transition = any(bool(item["publication_transition"]) for item in diffs)
    regression = any(bool(item["publication_regression"]) for item in diffs)
    state = "PUBLICATION_TRANSITION_OBSERVED" if transition else "PUBLICATION_REGRESSION_BLOCKED" if regression else "NO_PUBLICATION_TRANSITION"
    return {"schema_version": 1, "slot_id": "security_public_safety_1", "task_id": "aays1-security-public-safety-1-canonical-acceptance-v17-20260722", "checked_at": utc_now(), "state": state, "pages": [asdict(page) for page in pages], "diffs": diffs, "errors": errors, "summary": {"pages_expected": 2, "pages_fetched": len(pages), "errors": len(errors), "publication_transitions": sum(bool(x["publication_transition"]) for x in diffs), "publication_regressions": sum(bool(x["publication_regression"]) for x in diffs), "added_links": sum(len(x["added_links"]) for x in diffs), "removed_links": sum(len(x["removed_links"]) for x in diffs), "figures_ingested": 0, "stored_values_modified": False, "direct_score_inputs_accepted": 0}, "quality_guards": ["Only direct HTTPS ONS and GOV.UK page states are authoritative.", "Normalized and raw SHA-256 values are recorded separately.", "Publication transition requires source-specific markers.", "Publication regression blocks adoption.", "No score, parcel or database write occurs."], "output_semantics": "AREA_LEVEL_PROXY", "parcel_measurement": False, "fake_data": False, "final_ready": False}

def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True, type=Path); parser.add_argument("--previous", type=Path); parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not 5 <= args.timeout <= 120: parser.error("--timeout must be between 5 and 120")
    atomic_write(args.output, collect(args.timeout, load_previous(args.previous)))
    return 0

if __name__ == "__main__": sys.exit(main())

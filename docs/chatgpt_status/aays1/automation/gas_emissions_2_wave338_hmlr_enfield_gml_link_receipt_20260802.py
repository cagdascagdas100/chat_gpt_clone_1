#!/usr/bin/env python3
"""Wave338: resolve the current HMLR INSPIRE Enfield GML link target without downloading the full GML."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

DOWNLOAD_PAGE_URL = "https://use-land-property-data.service.gov.uk/datasets/inspire/download"
LICENSE_URL = "https://use-land-property-data.service.gov.uk/datasets/inspire/#conditions"
AUTHORITY = "London Borough of Enfield"
MAX_PAGE_BYTES = 1_500_000
MAX_TARGET_PREFIX_BYTES = 65_536
USER_AGENT = "AAYS-gas-emissions-2-wave338/1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class AnchorContextParser(HTMLParser):
    """Collect anchors with nearby visible text so repeated 'Download .gml' labels can be disambiguated."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._recent_text: deque[str] = deque(maxlen=30)
        self._active_href: str | None = None
        self._active_text: list[str] = []
        self.anchors: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        self._active_href = next((value for key, value in attrs if key.lower() == "href" and value), None)
        self._active_text = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        if self._active_href is not None:
            self._active_text.append(text)
        self._recent_text.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._active_href is None:
            return
        self.anchors.append(
            {
                "href": self._active_href,
                "text": " ".join(self._active_text).strip(),
                "preceding_context": " ".join(self._recent_text),
            }
        )
        self._active_href = None
        self._active_text = []


def bounded_get(url: str, timeout: int, limit: int, *, range_prefix: bool = False) -> tuple[int, bytes, dict[str, str], str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xml,text/xml,*/*;q=0.5"}
    if range_prefix:
        headers["Range"] = f"bytes=0-{limit - 1}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = int(getattr(response, "status", response.getcode()))
        body = response.read(limit + 1)
        if len(body) > limit:
            body = body[:limit]
        response_headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
        return status, body, response_headers, str(response.geturl())


def find_enfield_anchor(page_body: bytes) -> dict[str, str] | None:
    try:
        html = page_body.decode("utf-8")
    except UnicodeDecodeError:
        html = page_body.decode("utf-8", errors="replace")
    parser = AnchorContextParser()
    parser.feed(html)
    authority_lower = AUTHORITY.lower()
    candidates: list[dict[str, str]] = []
    for anchor in parser.anchors:
        combined = f"{anchor['preceding_context']} {anchor['text']}".lower()
        if authority_lower in combined and ("gml" in anchor["text"].lower() or "gml" in anchor["href"].lower()):
            candidates.append(anchor)
    if not candidates:
        return None
    return candidates[-1]


def target_looks_like_gml(href: str, final_url: str, headers: dict[str, str]) -> bool:
    disposition = headers.get("content-disposition", "").lower()
    content_type = headers.get("content-type", "").lower()
    joined = " ".join((href.lower(), final_url.lower(), disposition, content_type))
    return ".gml" in joined or "application/gml" in joined or "application/xml" in joined or "text/xml" in joined


def build_receipt(
    *,
    accessed_at: str,
    page_status: int | None,
    page_body: bytes | None,
    page_final_url: str | None,
    anchor: dict[str, str] | None,
    resolved_href: str | None,
    target_status: int | None,
    target_prefix: bytes | None,
    target_headers: dict[str, str] | None,
    target_final_url: str | None,
    error: str | None,
) -> dict[str, Any]:
    page_bytes = page_body or b""
    target_bytes = target_prefix or b""
    headers = target_headers or {}
    acquired = (
        error is None
        and page_status == 200
        and anchor is not None
        and resolved_href is not None
        and target_status in (200, 206)
        and target_final_url is not None
        and target_looks_like_gml(resolved_href, target_final_url, headers)
    )
    state = "PUBLISHED" if acquired else "NO_DATA_CONTINUE"
    decision = (
        "CURRENT_ENFIELD_INSPIRE_GML_LINK_TARGET_RECEIPT_ACQUIRED"
        if acquired
        else "CURRENT_ENFIELD_INSPIRE_GML_LINK_TARGET_NOT_ACQUIRED"
    )
    blocker = None
    first_unverified_step = "DOWNLOAD_BOUNDED_CURRENT_ENFIELD_GML_AND_VALIDATE_3_INSPIRE_IDS_OR_NO_DATA_CONTINUE"
    if not acquired:
        blocker = (
            "CURRENT_ENFIELD_INSPIRE_DOWNLOAD_PAGE_OR_LINK_TARGET_UNRESOLVED;"
            "CURRENT_ENFIELD_GML_BYTES_NOT_ACQUIRED;"
            "THREE_INSPIRE_IDS_NOT_VALIDATED_AGAINST_CURRENT_POLYGON_GEOMETRY;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        )
        first_unverified_step = "USE_NEXT_OFFICIAL_OPEN_IDENTIFIER_OR_BINDING_SOURCE_WITHOUT_GUESSING"
    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 338,
        "accessed_at": accessed_at,
        "state": state,
        "decision": decision,
        "blocker": blocker,
        "first_unverified_step": first_unverified_step,
        "download_page_url": DOWNLOAD_PAGE_URL,
        "license_or_terms_url": LICENSE_URL,
        "authority": AUTHORITY,
        "page_http_status": page_status,
        "page_final_url": page_final_url,
        "page_content_sha256": sha256_bytes(page_bytes),
        "page_bytes_read": len(page_bytes),
        "anchor_text": None if anchor is None else anchor.get("text"),
        "anchor_preceding_context": None if anchor is None else anchor.get("preceding_context", "")[-1000:],
        "anchor_href": None if anchor is None else anchor.get("href"),
        "resolved_href": resolved_href,
        "target_http_status": target_status,
        "target_final_url": target_final_url,
        "target_content_type": headers.get("content-type"),
        "target_content_disposition": headers.get("content-disposition"),
        "target_content_length": headers.get("content-length"),
        "target_accept_ranges": headers.get("accept-ranges"),
        "target_prefix_sha256": sha256_bytes(target_bytes),
        "target_prefix_bytes_read": len(target_bytes),
        "full_gml_downloaded": False,
        "network_or_validation_error": error,
        "canonical_sample_rows_in_scope": 3,
        "hmlr_inspire_ids_in_scope": ["46058185", "46037757", "45981756"],
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "fake_data": False,
        "final_ready": False,
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def self_test() -> None:
    html = b"""
    <html><body><div class="dataset-row">
      <span>London Borough of Enfield</span>
      <a href="/media/inspire/Enfield_2026_07.gml">Download .gml</a>
    </div></body></html>
    """
    anchor = find_enfield_anchor(html)
    assert anchor is not None
    assert anchor["href"] == "/media/inspire/Enfield_2026_07.gml"
    resolved = urllib.parse.urljoin(DOWNLOAD_PAGE_URL, anchor["href"])
    receipt = build_receipt(
        accessed_at="2026-08-02T11:58:00Z",
        page_status=200,
        page_body=html,
        page_final_url=DOWNLOAD_PAGE_URL,
        anchor=anchor,
        resolved_href=resolved,
        target_status=206,
        target_prefix=b"<?xml version='1.0'?><FeatureCollection/>",
        target_headers={"content-type": "application/gml+xml", "content-disposition": 'attachment; filename="Enfield.gml"'},
        target_final_url="https://example.invalid/Enfield.gml",
        error=None,
    )
    assert receipt["state"] == "PUBLISHED"
    assert receipt["full_gml_downloaded"] is False
    failed = build_receipt(
        accessed_at="2026-08-02T11:58:00Z",
        page_status=None,
        page_body=None,
        page_final_url=None,
        anchor=None,
        resolved_href=None,
        target_status=None,
        target_prefix=None,
        target_headers=None,
        target_final_url=None,
        error="URLError:temporary failure",
    )
    assert failed["state"] == "NO_DATA_CONTINUE"
    assert failed["business_rows_produced"] == 0
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=(
            "england_map_web/data/aays_21_slots/gas_emissions_2/"
            "wave338_hmlr_enfield_gml_link_receipt_20260802.json"
        ),
    )
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    accessed_at = utc_now()
    page_status = None
    page_body = None
    page_final_url = None
    anchor = None
    resolved_href = None
    target_status = None
    target_prefix = None
    target_headers = None
    target_final_url = None
    error = None
    try:
        page_status, page_body, _, page_final_url = bounded_get(
            DOWNLOAD_PAGE_URL, args.timeout, MAX_PAGE_BYTES
        )
        anchor = find_enfield_anchor(page_body)
        if anchor is None:
            raise ValueError("enfield_gml_anchor_not_found")
        resolved_href = urllib.parse.urljoin(page_final_url or DOWNLOAD_PAGE_URL, anchor["href"])
        target_status, target_prefix, target_headers, target_final_url = bounded_get(
            resolved_href, args.timeout, MAX_TARGET_PREFIX_BYTES, range_prefix=True
        )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError) as exc:
        error = f"{type(exc).__name__}:{exc}"

    receipt = build_receipt(
        accessed_at=accessed_at,
        page_status=page_status,
        page_body=page_body,
        page_final_url=page_final_url,
        anchor=anchor,
        resolved_href=resolved_href,
        target_status=target_status,
        target_prefix=target_prefix,
        target_headers=target_headers,
        target_final_url=target_final_url,
        error=error,
    )
    atomic_write_json(Path(args.output), receipt)
    print("DECISION=" + str(receipt["decision"]))
    print("PAGE_STATUS=" + str(receipt["page_http_status"]))
    print("TARGET_STATUS=" + str(receipt["target_http_status"]))
    print("FULL_GML_DOWNLOADED=false")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Prepare one fail-closed official-source manifest for gas_emissions_2 Wave316."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Iterable

SLOT_WRITE_ROOT = PurePosixPath("england_map_web/data/aays_21_slots/gas_emissions_2")
DEFAULT_SUPPORTS_FIELDS = [
    "publication_title",
    "publication_updated_date",
    "uk_carbon_footprint_mtco2e_2023",
    "uk_carbon_footprint_mtco2e_2007_peak",
    "uk_carbon_footprint_mtco2e_1996",
    "method_scope_consumption_based",
    "revision_notice",
]


def normalize_text(raw: str) -> str:
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


def validate_relative_output(path_text: str) -> Path:
    posix = PurePosixPath(path_text)
    if posix.is_absolute() or ".." in posix.parts:
        raise ValueError("output must be a safe relative repository path")
    if not posix.is_relative_to(SLOT_WRITE_ROOT):
        raise ValueError(f"output must stay under {SLOT_WRITE_ROOT}")
    return Path(*posix.parts)


def require_phrases(text: str, phrases: Iterable[str]) -> None:
    missing = [phrase for phrase in phrases if phrase.casefold() not in text.casefold()]
    if missing:
        raise ValueError(f"required source phrases missing: {missing}")


def fetch_source(url: str, timeout: int) -> tuple[int, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-gas-emissions-source-preflight/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
        return int(response.status), response.geturl(), payload


def build_manifest(*, source_url: str, accessed_at: str, license_url: str,
                   normalized: str, excerpt: str, http_status: int,
                   final_url: str) -> dict:
    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 316,
        "state": "SOURCE_PREFLIGHT_READY",
        "source_url": source_url,
        "final_url": final_url,
        "accessed_at": accessed_at,
        "content_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "excerpt_sha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        "supports_fields": DEFAULT_SUPPORTS_FIELDS,
        "relevant_record_ids_or_excerpt": excerpt,
        "license_or_terms_url": license_url,
        "http_status": http_status,
        "source_scope": "official_gov_uk_html_visible_text_only",
        "business_rows_produced": 0,
        "dedup_required_before_business_write": True,
        "linked_spreadsheet_values_used": False,
        "pdf_content_used": False,
        "fake_data": False,
        "final_ready": False,
    }


def self_test() -> None:
    fixture = """
    <html><head><title>Carbon footprint for the UK and England to 2023</title></head>
    <body><p>Updated 24 July 2026</p><p>The UK carbon footprint fell by 4% between 2022 and 2023
    to an estimated 699 million tonnes carbon dioxide equivalent. The 2007 peak was 984 MtCO2e
    and 826 MtCO2e was reported in 1996.</p><p>Open Government Licence v3.0</p></body></html>
    """
    normalized = normalize_text(fixture)
    require_phrases(normalized, ["Carbon footprint for the UK and England to 2023", "699", "984", "826"])
    out = validate_relative_output(
        "england_map_web/data/aays_21_slots/gas_emissions_2/official_source_manifest_wave316_preflight.json"
    )
    manifest = build_manifest(
        source_url="https://example.invalid/source",
        accessed_at="2026-08-01T14:04:00Z",
        license_url="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
        normalized=normalized,
        excerpt="Carbon footprint for the UK and England to 2023 | 699 | 984 | 826",
        http_status=200,
        final_url="https://example.invalid/source",
    )
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / out
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        loaded = json.loads(target.read_text(encoding="utf-8"))
        assert loaded["slot_id"] == "gas_emissions_2"
        assert len(loaded["content_sha256"]) == 64
        assert loaded["business_rows_produced"] == 0
    print("SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-url")
    parser.add_argument("--accessed-at")
    parser.add_argument("--license-url")
    parser.add_argument("--output")
    parser.add_argument("--fixture-file")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    required = [args.source_url, args.accessed_at, args.license_url, args.output]
    if not all(required):
        parser.error("source-url, accessed-at, license-url and output are required")

    output = validate_relative_output(args.output)
    if args.fixture_file:
        raw = Path(args.fixture_file).read_text(encoding="utf-8")
        status, final_url = 200, args.source_url
    else:
        status, final_url, raw = fetch_source(args.source_url, args.timeout)
    normalized = normalize_text(raw)
    required_phrases = [
        "Carbon footprint for the UK and England to 2023",
        "Updated 24 July 2026",
        "699 million tonnes carbon dioxide equivalent",
        "984 MtCO2e",
        "826 MtCO2e",
    ]
    require_phrases(normalized, required_phrases)
    excerpt = " | ".join(required_phrases)
    manifest = build_manifest(
        source_url=args.source_url,
        accessed_at=args.accessed_at,
        license_url=args.license_url,
        normalized=normalized,
        excerpt=excerpt,
        http_status=status,
        final_url=final_url,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)

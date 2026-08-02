#!/usr/bin/env python3
"""Wave336: acquire a bounded live OS OpenUPRN metadata receipt, fail closed, and write compact evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRODUCT_URL = "https://api.os.uk/downloads/v1/products/OpenUPRN"
DOWNLOADS_URL = "https://api.os.uk/downloads/v1/products/OpenUPRN/downloads"
LICENSE_URL = "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
MAX_RESPONSE_BYTES = 2_000_000
REQUIRED_FIELDS = ("fileName", "size", "md5", "url")
USER_AGENT = "AAYS-gas-emissions-2-wave336/1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def bounded_get(url: str, timeout: int) -> tuple[int, bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = int(getattr(response, "status", response.getcode()))
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError(f"response_too_large:{url}")
        headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
        return status, body, headers


def parse_json_bytes(body: bytes, label: str) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid_json:{label}:{exc}") from exc


def normalized_excerpt(value: Any, limit: int = 1000) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return text[:limit]


def select_csv_gb_records(downloads: Any) -> list[dict[str, Any]]:
    if not isinstance(downloads, list):
        raise ValueError("downloads_response_not_list")
    selected: list[dict[str, Any]] = []
    for item in downloads:
        if not isinstance(item, dict):
            continue
        area = str(item.get("area", "")).upper()
        fmt = str(item.get("format", "")).upper()
        if area == "GB" and "CSV" in fmt:
            selected.append(item)
    return selected


def compact_record(item: dict[str, Any]) -> dict[str, Any]:
    allowed = ("fileName", "format", "subformat", "area", "size", "md5", "url")
    return {key: item.get(key) for key in allowed if key in item}


def build_receipt(
    *,
    accessed_at: str,
    product_status: int | None,
    product_body: bytes | None,
    downloads_status: int | None,
    downloads_body: bytes | None,
    network_error: str | None,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 336,
        "accessed_at": accessed_at,
        "source_urls": [PRODUCT_URL, DOWNLOADS_URL],
        "license_or_terms_url": LICENSE_URL,
        "fake_data": False,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
    }
    if network_error is not None:
        base.update(
            {
                "state": "NO_DATA_CONTINUE",
                "decision": "LIVE_OPENUPRN_METADATA_RECEIPT_NOT_ACQUIRED",
                "network_error": network_error,
                "product_http_status": product_status,
                "downloads_http_status": downloads_status,
                "product_content_sha256": sha256_bytes(product_body or b""),
                "downloads_content_sha256": sha256_bytes(downloads_body or b""),
                "selected_record_count": 0,
                "metadata_complete_record_count": 0,
                "missing_required_fields": list(REQUIRED_FIELDS),
                "first_unverified_step": (
                    "USE_NEXT_OFFICIAL_OPEN_IDENTIFIER_OR_CANONICAL_BINDING_SOURCE_WITHOUT_GUESSING"
                ),
            }
        )
        return base

    assert product_body is not None and downloads_body is not None
    product = parse_json_bytes(product_body, "product")
    downloads = parse_json_bytes(downloads_body, "downloads")
    selected = select_csv_gb_records(downloads)
    compact = [compact_record(item) for item in selected[:10]]
    complete = [item for item in compact if all(item.get(field) not in (None, "") for field in REQUIRED_FIELDS)]
    missing = sorted(
        {
            field
            for item in compact
            for field in REQUIRED_FIELDS
            if item.get(field) in (None, "")
        }
    )
    acquired = product_status == 200 and downloads_status == 200 and bool(complete)
    base.update(
        {
            "state": "PUBLISHED" if acquired else "NO_DATA_CONTINUE",
            "decision": (
                "LIVE_OPENUPRN_METADATA_RECEIPT_ACQUIRED"
                if acquired
                else "LIVE_OPENUPRN_METADATA_RESPONSE_INCOMPLETE_NO_DATA_CONTINUE"
            ),
            "product_http_status": product_status,
            "downloads_http_status": downloads_status,
            "product_content_sha256": sha256_bytes(product_body),
            "downloads_content_sha256": sha256_bytes(downloads_body),
            "product_relevant_record_ids_or_excerpt": normalized_excerpt(product),
            "download_records": compact,
            "selected_record_count": len(selected),
            "metadata_complete_record_count": len(complete),
            "missing_required_fields": missing,
            "supports_fields": [
                "product id",
                "product name",
                "product version",
                "download fileName",
                "download format",
                "download area",
                "download size",
                "download md5",
                "download url",
            ],
            "first_unverified_step": (
                "ACQUIRE_AUTHORITATIVE_ENFIELD_OPENUPRN_SUBSET_AND_RUN_COORDINATE_COLLISION_AUDIT"
                if acquired
                else "USE_NEXT_OFFICIAL_OPEN_IDENTIFIER_OR_CANONICAL_BINDING_SOURCE_WITHOUT_GUESSING"
            ),
        }
    )
    return base


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def self_test() -> None:
    product = {"id": "OpenUPRN", "name": "OS Open UPRN", "version": "test"}
    downloads = [
        {
            "fileName": "osopenuprn_test.csv.zip",
            "format": "CSV",
            "area": "GB",
            "size": 123,
            "md5": "0123456789abcdef0123456789abcdef",
            "url": "https://example.invalid/osopenuprn_test.csv.zip",
        },
        {"fileName": "other.gpkg", "format": "GeoPackage", "area": "GB"},
    ]
    receipt = build_receipt(
        accessed_at="2026-08-02T09:54:00Z",
        product_status=200,
        product_body=json.dumps(product).encode(),
        downloads_status=200,
        downloads_body=json.dumps(downloads).encode(),
        network_error=None,
    )
    assert receipt["decision"] == "LIVE_OPENUPRN_METADATA_RECEIPT_ACQUIRED"
    assert receipt["metadata_complete_record_count"] == 1
    assert receipt["selected_record_count"] == 1
    assert receipt["fake_data"] is False

    failed = build_receipt(
        accessed_at="2026-08-02T09:54:00Z",
        product_status=None,
        product_body=None,
        downloads_status=None,
        downloads_body=None,
        network_error="URLError:temporary failure",
    )
    assert failed["state"] == "NO_DATA_CONTINUE"
    assert failed["selected_record_count"] == 0
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=(
            "england_map_web/data/aays_21_slots/gas_emissions_2/"
            "wave336_os_open_uprn_live_metadata_receipt_20260802.json"
        ),
    )
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return

    accessed_at = utc_now()
    product_status = None
    downloads_status = None
    product_body = None
    downloads_body = None
    network_error = None
    try:
        product_status, product_body, _ = bounded_get(PRODUCT_URL, args.timeout)
        downloads_status, downloads_body, _ = bounded_get(DOWNLOADS_URL, args.timeout)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        network_error = f"{type(exc).__name__}:{exc}"

    receipt = build_receipt(
        accessed_at=accessed_at,
        product_status=product_status,
        product_body=product_body,
        downloads_status=downloads_status,
        downloads_body=downloads_body,
        network_error=network_error,
    )
    atomic_write_json(Path(args.output), receipt)
    print("DECISION=" + str(receipt["decision"]))
    print("SELECTED_RECORDS=" + str(receipt["selected_record_count"]))
    print("COMPLETE_METADATA_RECORDS=" + str(receipt["metadata_complete_record_count"]))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Bounded validation of one official HMLR INSPIRE ZIP locator.

The script never persists the ZIP/GML body. It verifies HTTP/ZIP/archive-entry
facts only when all checks pass; network or content failures produce a bounded
NO_DATA_CONTINUE record.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OFFICIAL_HOST = "use-land-property-data.service.gov.uk"
EXPECTED_ENTRY = "Land_Registry_Cadastral_Parcels.gml"
DEFAULT_MAX_BYTES = 32 * 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def classify_http_zip(status: int, content_type: str, payload: bytes, expected_entry: str) -> dict[str, Any]:
    media = content_type.split(";", 1)[0].strip().lower()
    http_ok = status in (200, 206)
    signature_ok = payload.startswith(b"PK\x03\x04")
    type_ok = media in {"application/zip", "application/octet-stream", "binary/octet-stream"}
    entry_found = False
    entries: list[str] = []
    zip_error = None
    if http_ok and signature_ok:
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                entries = archive.namelist()
                entry_found = any(Path(name).name == expected_entry for name in entries)
        except (zipfile.BadZipFile, OSError) as exc:
            zip_error = f"{type(exc).__name__}:{exc}"
    verified = bool(http_ok and signature_ok and type_ok and entry_found and zip_error is None)
    return {
        "http_status": status,
        "content_type": media,
        "http_response_verified": http_ok,
        "zip_signature_verified": signature_ok,
        "zip_content_type_verified": type_ok,
        "archive_entry_verified": entry_found,
        "archive_entry_count": len(entries),
        "zip_error": zip_error,
        "verified": verified,
    }


def fetch_bounded(url: str, timeout_seconds: int, max_bytes: int) -> tuple[int, str, bytes, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-future-growth-2/1.0", "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status = int(getattr(response, "status", response.getcode()))
            content_type = response.headers.get("Content-Type", "")
            payload = response.read(max_bytes + 1)
            if len(payload) > max_bytes:
                return status, content_type, b"", f"RESPONSE_EXCEEDS_MAX_BYTES:{max_bytes}"
            return status, content_type, payload, None
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.headers.get("Content-Type", "") if exc.headers else "", b"", f"HTTPError:{exc.code}"
    except Exception as exc:
        return 0, "", b"", f"{type(exc).__name__}:{exc}"


def self_test() -> dict[str, Any]:
    tests: list[dict[str, Any]] = []
    fixture = io.BytesIO()
    with zipfile.ZipFile(fixture, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(EXPECTED_ENTRY, "<gml/>")
    valid = classify_http_zip(200, "application/zip", fixture.getvalue(), EXPECTED_ENTRY)
    tests.append({"name": "valid_zip_entry", "passed": valid["verified"] is True})
    wrong_entry = classify_http_zip(200, "application/zip", fixture.getvalue(), "missing.gml")
    tests.append({"name": "missing_entry_rejected", "passed": wrong_entry["verified"] is False and wrong_entry["archive_entry_verified"] is False})
    bad_signature = classify_http_zip(200, "application/zip", b"not-a-zip", EXPECTED_ENTRY)
    tests.append({"name": "bad_signature_rejected", "passed": bad_signature["verified"] is False})
    bad_type = classify_http_zip(200, "text/html", fixture.getvalue(), EXPECTED_ENTRY)
    tests.append({"name": "html_content_type_rejected", "passed": bad_type["verified"] is False})
    redirect = classify_http_zip(302, "text/html", b"", EXPECTED_ENTRY)
    tests.append({"name": "redirect_not_verified", "passed": redirect["verified"] is False and redirect["http_response_verified"] is False})
    passed = sum(1 for test in tests if test["passed"])
    return {"tests": tests, "passed": passed, "target": len(tests), "result": f"PASS_{passed}_OF_{len(tests)}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--locator-input", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--task-continuation-key")
    parser.add_argument("--timeout-seconds", type=int, default=30)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    if not all((args.locator_input, args.manifest, args.output, args.task_continuation_key)):
        parser.error("locator-input, manifest, output and task-continuation-key are required")

    locator = json.loads(args.locator_input.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    candidate = locator.get("candidate") or {}
    url = candidate.get("exact_official_gml_zip_url")
    if not isinstance(url, str) or __import__("urllib.parse").parse.urlparse(url).hostname != OFFICIAL_HOST:
        raise SystemExit("official locator missing or host mismatch")

    status, content_type, payload, fetch_error = fetch_bounded(url, args.timeout_seconds, args.max_bytes)
    classification = classify_http_zip(status, content_type, payload, EXPECTED_ENTRY) if fetch_error is None else {
        "http_status": status,
        "content_type": content_type,
        "http_response_verified": False,
        "zip_signature_verified": False,
        "zip_content_type_verified": False,
        "archive_entry_verified": False,
        "archive_entry_count": 0,
        "zip_error": None,
        "verified": False,
    }
    verified = bool(classification["verified"])
    error = fetch_error or classification.get("zip_error")
    blocker = None if verified else (
        "OFFICIAL_HMLR_GML_ZIP_DNS_RESOLUTION_FAILED" if error and "name resolution" in error.lower() else
        "OFFICIAL_HMLR_GML_ZIP_REDIRECT_OR_HTTP_UNVERIFIED" if (status in {0, 301, 302, 303, 307, 308} or (error and "redirect" in error.lower())) else
        "OFFICIAL_HMLR_GML_ZIP_ARCHIVE_ENTRY_UNVERIFIED"
    )
    output = {
        "architecture_version": 3,
        "schema_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_2",
        "task_continuation_key": args.task_continuation_key,
        "generated_at": utc_now(),
        "state": "PUBLISHED" if verified else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": len(manifest.get("sources", [])),
        "target_count": len(manifest.get("sources", [])),
        "progress_percent": 100.0 if manifest.get("sources") else 0.0,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "produced_business_rows": 0,
        "exact_official_gml_zip_url": url,
        "expected_archive_entry": EXPECTED_ENTRY,
        "current_http_response_verified": classification["http_response_verified"],
        "zip_signature_verified": classification["zip_signature_verified"],
        "zip_content_type_verified": classification["zip_content_type_verified"],
        "archive_entry_verified": classification["archive_entry_verified"],
        "archive_entry_count": classification["archive_entry_count"],
        "http_status": classification["http_status"],
        "content_type": classification["content_type"],
        "fetch_error": error,
        "blocker": blocker,
        "next_unverified_step": "DISCOVER_OFFICIAL_ALTERNATE_DOWNLOAD_ROUTE_OR_VALIDATE_FROM_NETWORK_ENABLED_RUNNER" if not verified else "PARSE_ONE_BOUNDED_GML_FEATURE_SCHEMA",
        "archive_body_copied": False,
        "gml_body_copied": False,
        "geometry_copied": False,
        "authority_membership_inferred": False,
        "score_written": False,
        "fake_data": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

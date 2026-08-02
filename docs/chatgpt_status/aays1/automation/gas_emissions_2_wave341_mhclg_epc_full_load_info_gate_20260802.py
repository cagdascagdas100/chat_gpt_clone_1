#!/usr/bin/env python3
"""Wave341: bounded anonymous MHCLG domestic full-load info metadata gate."""
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

CSV_INFO_URL = "https://api.get-energy-performance-data.communities.gov.uk/api/files/domestic/csv/info"
JSON_INFO_URL = "https://api.get-energy-performance-data.communities.gov.uk/api/files/domestic/json/info"
LICENSE_URL = "https://get-energy-performance-data.communities.gov.uk/guidance/licensing-restrictions"
MAX_BYTES = 65536
USER_AGENT = "AAYS-gas-emissions-2-wave341/1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def bounded_get(url: str, timeout: int) -> tuple[int | None, bytes, dict[str, str], str | None, str | None]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_BYTES + 1)[:MAX_BYTES]
            headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
            return int(getattr(response, "status", response.getcode())), body, headers, str(response.geturl()), None
    except urllib.error.HTTPError as exc:
        body = exc.read(MAX_BYTES + 1)[:MAX_BYTES]
        headers = {str(k).lower(): str(v) for k, v in exc.headers.items()}
        return int(exc.code), body, headers, str(exc.geturl()), None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, b"", {}, None, f"{type(exc).__name__}:{exc}"


def parse_metadata(body: bytes) -> dict[str, Any] | None:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return None
    file_size = data.get("fileSize")
    last_updated = data.get("lastUpdated")
    if not isinstance(file_size, int) or file_size < 0 or not isinstance(last_updated, str) or not last_updated:
        return None
    return {"fileSize": file_size, "lastUpdated": last_updated}


def build_receipt(
    *,
    accessed_at: str,
    fixture: dict[str, Any],
    csv_result: tuple[int | None, bytes, dict[str, str], str | None, str | None],
    json_result: tuple[int | None, bytes, dict[str, str], str | None, str | None],
) -> dict[str, Any]:
    endpoints: dict[str, Any] = {}
    metadata_count = 0
    auth_denied_count = 0
    errors: list[str] = []
    for name, url, result in (
        ("csv_info", CSV_INFO_URL, csv_result),
        ("json_info", JSON_INFO_URL, json_result),
    ):
        status, body, headers, final_url, error = result
        metadata = parse_metadata(body) if status == 200 else None
        if metadata is not None:
            metadata_count += 1
        if status in (401, 403):
            auth_denied_count += 1
        if error:
            errors.append(f"{name}:{error}")
        endpoints[name] = {
            "source_url": url,
            "http_status": status,
            "final_url": final_url,
            "content_type": headers.get("content-type"),
            "www_authenticate": headers.get("www-authenticate"),
            "bytes_read": len(body),
            "content_sha256": sha256_bytes(body),
            "metadata": metadata,
            "network_or_validation_error": error,
        }

    if metadata_count == 2:
        decision = "MHCLG_DOMESTIC_FULL_LOAD_INFO_ANONYMOUS_METADATA_ACQUIRED"
        blocker = (
            "THREE_EXACT_UPRNS_NOT_ACQUIRED;"
            "FULL_LOAD_ARCHIVE_NOT_DOWNLOADED;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        )
        first_unverified = "ASSESS_MHCLG_EPC_FULL_LOAD_ARCHIVE_SCHEMA_WITHOUT_DOWNLOADING_ARCHIVE_OR_NO_DATA_CONTINUE"
    elif auth_denied_count >= 1:
        decision = "MHCLG_DOMESTIC_FULL_LOAD_INFO_BEARER_TOKEN_GATE_CONFIRMED"
        blocker = (
            "MHCLG_DOMESTIC_FULL_LOAD_INFO_REQUIRES_BEARER_TOKEN;"
            "BEARER_TOKEN_NOT_AVAILABLE;"
            "THREE_EXACT_UPRNS_NOT_ACQUIRED;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        )
        first_unverified = "ASSESS_MHCLG_EPC_OPENAPI_PUBLIC_SCHEMA_OR_NO_DATA_CONTINUE"
    else:
        decision = "MHCLG_DOMESTIC_FULL_LOAD_INFO_METADATA_NOT_ACQUIRED"
        blocker = (
            "LIVE_MHCLG_DOMESTIC_FULL_LOAD_INFO_ENDPOINTS_NOT_ACQUIRED;"
            "ANONYMOUS_METADATA_ACCESS_NOT_CONFIRMED;"
            "BEARER_TOKEN_NOT_AVAILABLE;"
            "THREE_EXACT_UPRNS_NOT_ACQUIRED;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        )
        first_unverified = "ASSESS_MHCLG_EPC_OPENAPI_PUBLIC_SCHEMA_OR_NO_DATA_CONTINUE"

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 341,
        "accessed_at": accessed_at,
        "state": "NO_DATA_CONTINUE",
        "decision": decision,
        "blocker": blocker,
        "first_unverified_step": first_unverified,
        "bearer_token_used": False,
        "authorization_header_sent": False,
        "full_load_archive_downloaded": False,
        "metadata_endpoints_acquired": metadata_count,
        "authentication_denied_endpoints": auth_denied_count,
        "endpoints": endpoints,
        "network_or_validation_errors": errors,
        "official_source_evidence_count": int(fixture.get("official_source_evidence_count", 0)),
        "source_evidence_manifest": fixture.get("source_evidence_manifest", []),
        "canonical_sample_rows_in_scope": 3,
        "hmlr_inspire_ids_in_scope": ["46058185", "46037757", "45981756"],
        "exact_uprns_acquired": 0,
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
    fixture = {"official_source_evidence_count": 4, "source_evidence_manifest": []}
    ok_body = json.dumps({"data": {"fileSize": 123, "lastUpdated": "2026-08-01T00:00:00Z"}}).encode()
    acquired = build_receipt(
        accessed_at="2026-08-02T13:36:00Z",
        fixture=fixture,
        csv_result=(200, ok_body, {"content-type": "application/json"}, CSV_INFO_URL, None),
        json_result=(200, ok_body, {"content-type": "application/json"}, JSON_INFO_URL, None),
    )
    assert acquired["metadata_endpoints_acquired"] == 2
    assert acquired["authorization_header_sent"] is False
    denied = build_receipt(
        accessed_at="2026-08-02T13:36:00Z",
        fixture=fixture,
        csv_result=(401, b'{"error":"Unauthorized"}', {"www-authenticate": "Bearer"}, CSV_INFO_URL, None),
        json_result=(403, b"", {}, JSON_INFO_URL, None),
    )
    assert denied["authentication_denied_endpoints"] == 2
    assert denied["state"] == "NO_DATA_CONTINUE"
    failed = build_receipt(
        accessed_at="2026-08-02T13:36:00Z",
        fixture=fixture,
        csv_result=(None, b"", {}, None, "URLError:dns"),
        json_result=(None, b"", {}, None, "URLError:dns"),
    )
    assert len(failed["network_or_validation_errors"]) == 2
    assert failed["business_rows_produced"] == 0
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument(
        "--output",
        default="england_map_web/data/aays_21_slots/gas_emissions_2/wave341_mhclg_epc_full_load_info_gate_20260802.json",
    )
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    receipt = build_receipt(
        accessed_at=utc_now(),
        fixture=fixture,
        csv_result=bounded_get(CSV_INFO_URL, args.timeout),
        json_result=bounded_get(JSON_INFO_URL, args.timeout),
    )
    atomic_write_json(Path(args.output), receipt)
    print("DECISION=" + str(receipt["decision"]))
    print("CSV_STATUS=" + str(receipt["endpoints"]["csv_info"]["http_status"]))
    print("JSON_STATUS=" + str(receipt["endpoints"]["json_info"]["http_status"]))
    print("AUTHORIZATION_HEADER_SENT=false")
    print("FULL_LOAD_ARCHIVE_DOWNLOADED=false")


if __name__ == "__main__":
    main()

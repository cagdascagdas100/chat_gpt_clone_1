#!/usr/bin/env python3
"""Wave340: validate MHCLG EPC UPRN access contract and anonymous API gate."""
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

DOC_URLS = {
    "service": "https://get-energy-performance-data.communities.gov.uk/",
    "api_guidance": "https://get-energy-performance-data.communities.gov.uk/guidance/energy-certificate-data-apis",
    "making_request": "https://get-energy-performance-data.communities.gov.uk/api-technical-documentation/making-a-request",
    "domestic_search": "https://get-energy-performance-data.communities.gov.uk/api-technical-documentation/search-certificates/domestic",
    "licensing": "https://get-energy-performance-data.communities.gov.uk/guidance/licensing-restrictions",
}
API_PROBE_URL = "https://api.get-energy-performance-data.communities.gov.uk/api/domestic/search"
MAX_DOC_BYTES = 1_500_000
MAX_API_BYTES = 65_536
USER_AGENT = "AAYS-gas-emissions-2-wave340/1.0"

REQUIRED_MARKERS = {
    "service": ["developer api", "gov.uk one login"],
    "api_guidance": ["bearer token", "openapi specification"],
    "making_request": ["https://api.get-energy-performance-data.communities.gov.uk", "must include an authorisation header"],
    "domestic_search": ["get /api/domestic/search", "uprn", "12-digit unique property reference number"],
    "licensing": ["open government licence v3.0", "includes ordnance survey uprns"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def bounded_get(url: str, timeout: int, limit: int, *, accept: str) -> tuple[int, bytes, dict[str, str], str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": accept},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(getattr(response, "status", response.getcode()))
            body = response.read(limit + 1)[:limit]
            headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
            return status, body, headers, str(response.geturl())
    except urllib.error.HTTPError as exc:
        body = exc.read(limit + 1)[:limit]
        headers = {str(k).lower(): str(v) for k, v in exc.headers.items()}
        return int(exc.code), body, headers, str(exc.geturl())


def validate_fixture(payload: dict[str, Any]) -> None:
    manifest = payload.get("source_evidence_manifest")
    assert isinstance(manifest, list) and len(manifest) == 5
    for record in manifest:
        required = {
            "source_id", "publisher", "source_url", "accessed_at", "content_sha256",
            "hash_scope", "record_scope", "relevant_record_ids_or_excerpt",
            "supports_fields", "license_or_terms_url",
        }
        assert required.issubset(record)
        normalized = " ".join(str(record["relevant_record_ids_or_excerpt"]).split()).encode("utf-8")
        assert sha256_bytes(normalized) == record["content_sha256"]
    contract = payload["required_contract"]
    assert contract["domestic_search_path"] == "/api/domestic/search"
    assert contract["uprn_parameter"] == "uprn"
    assert contract["authorization"] == "Bearer token required"
    assert "Open Government Licence" in contract["uprn_license"]


def markers_present(body: bytes, markers: list[str]) -> bool:
    text = body.decode("utf-8", errors="replace").lower()
    return all(marker in text for marker in markers)


def build_receipt(
    *,
    fixture: dict[str, Any],
    accessed_at: str,
    docs: dict[str, dict[str, Any]],
    api_probe: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    fixture_contract_complete = True
    live_docs_complete = all(item.get("markers_present") is True for item in docs.values())
    api_status = api_probe.get("http_status")
    anonymous_access_denied = api_status in (401, 403)
    bearer_token_used = False

    decision = "MHCLG_EPC_UPRN_ACCESS_REQUIRES_BEARER_TOKEN_NO_TOKEN_AVAILABLE"
    blocker_parts = []
    if errors:
        blocker_parts.append("LIVE_MHCLG_EPC_DOCS_OR_API_PROBE_NOT_FULLY_ACQUIRED")
    if not anonymous_access_denied:
        blocker_parts.append("ANONYMOUS_API_TOKEN_GATE_NOT_LIVE_CONFIRMED")
    blocker_parts.extend([
        "MHCLG_EPC_API_BEARER_TOKEN_REQUIRED_AND_NOT_AVAILABLE",
        "THREE_EXACT_UPRNS_NOT_ACQUIRED",
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE",
    ])

    return {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 340,
        "accessed_at": accessed_at,
        "state": "NO_DATA_CONTINUE",
        "decision": decision,
        "blocker": ";".join(blocker_parts),
        "first_unverified_step": "ASSESS_MHCLG_EPC_DOMESTIC_FULL_LOAD_INFO_METADATA_ACCESS_WITHOUT_BEARER_TOKEN_OR_NO_DATA_CONTINUE",
        "fixture_contract_complete": fixture_contract_complete,
        "live_docs_complete": live_docs_complete,
        "bearer_token_used": bearer_token_used,
        "anonymous_access_denied": anonymous_access_denied,
        "api_probe_url": API_PROBE_URL,
        "api_probe_http_status": api_status,
        "api_probe_final_url": api_probe.get("final_url"),
        "api_probe_content_type": api_probe.get("content_type"),
        "api_probe_bytes_read": api_probe.get("bytes_read", 0),
        "api_probe_content_sha256": api_probe.get("content_sha256", sha256_bytes(b"")),
        "docs": docs,
        "network_or_validation_errors": errors,
        "official_source_evidence_count": len(fixture["source_evidence_manifest"]),
        "source_evidence_manifest": fixture["source_evidence_manifest"],
        "canonical_sample_rows_in_scope": fixture["canonical_sample_rows_in_scope"],
        "hmlr_inspire_ids_in_scope": fixture["hmlr_inspire_ids_in_scope"],
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
    fixture = {
        "source_evidence_manifest": [
            {
                "source_id": str(i), "publisher": "MHCLG", "source_url": "https://example.invalid",
                "accessed_at": "2026-08-02T13:12:00Z",
                "content_sha256": sha256_bytes(f"evidence {i}".encode()),
                "hash_scope": "normalized_official_excerpt_utf8",
                "record_scope": "test",
                "relevant_record_ids_or_excerpt": f"evidence {i}",
                "supports_fields": ["test"],
                "license_or_terms_url": "https://example.invalid/license",
            } for i in range(5)
        ],
        "required_contract": {
            "domestic_search_path": "/api/domestic/search",
            "uprn_parameter": "uprn",
            "authorization": "Bearer token required",
            "uprn_license": "Open Government Licence v3.0",
        },
        "canonical_sample_rows_in_scope": 3,
        "hmlr_inspire_ids_in_scope": ["1", "2", "3"],
    }
    validate_fixture(fixture)
    docs = {
        key: {"http_status": 200, "markers_present": True, "bytes_read": 10, "content_sha256": sha256_bytes(b"x")}
        for key in DOC_URLS
    }
    receipt = build_receipt(
        fixture=fixture,
        accessed_at="2026-08-02T13:12:00Z",
        docs=docs,
        api_probe={"http_status": 401, "bytes_read": 0, "content_sha256": sha256_bytes(b"")},
        errors=[],
    )
    assert receipt["state"] == "NO_DATA_CONTINUE"
    assert receipt["anonymous_access_denied"] is True
    assert receipt["bearer_token_used"] is False
    assert receipt["business_rows_produced"] == 0
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=False)
    parser.add_argument(
        "--output",
        default="england_map_web/data/aays_21_slots/gas_emissions_2/wave340_mhclg_epc_uprn_access_gate_20260802.json",
    )
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.fixture:
        raise SystemExit("--fixture is required")

    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    validate_fixture(fixture)

    accessed_at = utc_now()
    docs: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for key, url in DOC_URLS.items():
        try:
            status, body, headers, final_url = bounded_get(url, args.timeout, MAX_DOC_BYTES, accept="text/html,*/*;q=0.5")
            docs[key] = {
                "source_url": url,
                "http_status": status,
                "final_url": final_url,
                "content_type": headers.get("content-type"),
                "bytes_read": len(body),
                "content_sha256": sha256_bytes(body),
                "markers_present": markers_present(body, REQUIRED_MARKERS[key]),
            }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append(f"{key}:{type(exc).__name__}:{exc}")
            docs[key] = {
                "source_url": url,
                "http_status": None,
                "final_url": None,
                "content_type": None,
                "bytes_read": 0,
                "content_sha256": sha256_bytes(b""),
                "markers_present": False,
            }

    api_probe: dict[str, Any]
    try:
        status, body, headers, final_url = bounded_get(
            API_PROBE_URL, args.timeout, MAX_API_BYTES, accept="application/json"
        )
        api_probe = {
            "http_status": status,
            "final_url": final_url,
            "content_type": headers.get("content-type"),
            "bytes_read": len(body),
            "content_sha256": sha256_bytes(body),
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        errors.append(f"api_probe:{type(exc).__name__}:{exc}")
        api_probe = {
            "http_status": None,
            "final_url": None,
            "content_type": None,
            "bytes_read": 0,
            "content_sha256": sha256_bytes(b""),
        }

    receipt = build_receipt(
        fixture=fixture,
        accessed_at=accessed_at,
        docs=docs,
        api_probe=api_probe,
        errors=errors,
    )
    atomic_write_json(Path(args.output), receipt)
    print("DECISION=" + receipt["decision"])
    print("API_PROBE_STATUS=" + str(receipt["api_probe_http_status"]))
    print("BEARER_TOKEN_USED=false")
    print("EXACT_UPRNS_ACQUIRED=0")


if __name__ == "__main__":
    main()

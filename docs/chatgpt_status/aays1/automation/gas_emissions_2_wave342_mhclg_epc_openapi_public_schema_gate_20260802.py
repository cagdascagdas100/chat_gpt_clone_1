#!/usr/bin/env python3
"""Wave342: bounded public MHCLG EPC OpenAPI schema gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

INDEX_URL = "https://get-energy-performance-data.communities.gov.uk/api-documentation/index.html"
INITIALIZER_URL = "https://get-energy-performance-data.communities.gov.uk/api-documentation/swagger-initializer.js"
BASE = "https://get-energy-performance-data.communities.gov.uk/api-documentation/"
CANDIDATES = [
    INDEX_URL,
    INITIALIZER_URL,
    urllib.parse.urljoin(BASE, "openapi.json"),
    urllib.parse.urljoin(BASE, "openapi.yaml"),
    urllib.parse.urljoin(BASE, "openapi.yml"),
    urllib.parse.urljoin(BASE, "swagger.json"),
    urllib.parse.urljoin(BASE, "api-docs"),
    urllib.parse.urljoin(BASE, "v3/api-docs"),
]
MAX_BYTES_PER_URL = 1_000_000
MAX_TOTAL_BYTES = 3_000_000


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        tmp.write("\n")
        name = tmp.name
    os.replace(name, path)


def bounded_fetch(url: str, timeout: int, remaining: int) -> dict[str, Any]:
    limit = max(0, min(MAX_BYTES_PER_URL, remaining))
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json, application/yaml, text/yaml, text/plain, text/html, */*", "User-Agent": "AAYS-wave342/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(limit + 1)
            truncated = len(data) > limit
            data = data[:limit]
            return {
                "source_url": url,
                "final_url": response.geturl(),
                "http_status": response.status,
                "content_type": response.headers.get("Content-Type"),
                "bytes_read": len(data),
                "content_sha256": sha256_bytes(data),
                "truncated": truncated,
                "body_text": data.decode("utf-8", errors="replace"),
                "network_or_validation_error": None,
            }
    except Exception as exc:  # fail closed with evidence
        return {
            "source_url": url,
            "final_url": None,
            "http_status": getattr(exc, "code", None),
            "content_type": None,
            "bytes_read": 0,
            "content_sha256": sha256_bytes(b""),
            "truncated": False,
            "body_text": "",
            "network_or_validation_error": f"{type(exc).__name__}:{exc}",
        }


def initializer_urls(text: str) -> list[str]:
    found: list[str] = []
    for pattern in [r"\burl\s*:\s*['\"]([^'\"]+)['\"]", r"\burls\s*:\s*\[([^\]]+)\]"]:
        for match in re.finditer(pattern, text, flags=re.I | re.S):
            if pattern.startswith("\\burls"):
                found.extend(re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)))
            else:
                found.append(match.group(1))
    return [urllib.parse.urljoin(INDEX_URL, item) for item in found]


def schema_markers(text: str) -> dict[str, bool]:
    lower = text.lower()
    return {
        "openapi_v3": bool(re.search(r"(?:\"openapi\"\s*:\s*\"3\.|\bopenapi\s*:\s*['\"]?3\.)", text, flags=re.I)),
        "domestic_search_path": "/api/domestic/search" in lower,
        "uprn_marker": bool(re.search(r"\buprn\b", lower)),
    }


def self_test() -> None:
    init = "const ui = SwaggerUIBundle({ url: './openapi.json' })"
    urls = initializer_urls(init)
    assert urls and urls[0].endswith("/api-documentation/openapi.json")
    sample = '{"openapi":"3.0.3","paths":{"/api/domestic/search":{}},"components":{"schemas":{"uprn":{"type":"string"}}}}'
    markers = schema_markers(sample)
    assert all(markers.values())
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.fixture or not args.output:
        parser.error("--fixture and --output are required unless --self-test is used")

    fixture_bytes = args.fixture.read_bytes()
    fixture = json.loads(fixture_bytes)
    manifest = fixture.get("source_evidence_manifest", [])
    if len(manifest) != 4:
        raise SystemExit("fixture must contain exactly 4 official evidence records")

    probes: list[dict[str, Any]] = []
    candidates = list(CANDIDATES)
    seen: set[str] = set()
    total = 0
    i = 0
    while i < len(candidates) and total < MAX_TOTAL_BYTES:
        url = candidates[i]
        i += 1
        if url in seen:
            continue
        seen.add(url)
        probe = bounded_fetch(url, args.timeout, MAX_TOTAL_BYTES - total)
        total += probe["bytes_read"]
        body = probe.pop("body_text")
        probe["markers"] = schema_markers(body)
        if url == INITIALIZER_URL or "swagger" in body.lower():
            for discovered in initializer_urls(body):
                if discovered not in seen and discovered not in candidates:
                    candidates.append(discovered)
        probes.append(probe)

    validated = [p for p in probes if p["http_status"] == 200 and all(p["markers"].values())]
    network_errors = [f"{p['source_url']}:{p['network_or_validation_error']}" for p in probes if p["network_or_validation_error"]]
    state = "PUBLISHED" if validated else "NO_DATA_CONTINUE"
    decision = "PUBLIC_MHCLG_OPENAPI_3_SCHEMA_VALIDATED" if validated else "PUBLIC_MHCLG_OPENAPI_3_SCHEMA_NOT_ACQUIRED"
    blocker = None if validated else "PUBLIC_MHCLG_OPENAPI_SCHEMA_NOT_ACQUIRED;OPENAPI_3_DOMESTIC_SEARCH_UPRN_CONTRACT_NOT_LIVE_VALIDATED;BEARER_TOKEN_NOT_AVAILABLE;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    next_step = "USE_VALIDATED_OPENAPI_SCHEMA_FOR_TOKENED_UPRN_QUERY_PLANNING" if validated else "ASSESS_FIND_ENERGY_CERTIFICATE_PUBLIC_REGISTER_IDENTIFIER_ACCESS_OR_NO_DATA_CONTINUE"

    payload = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2",
        "wave": 342,
        "accessed_at": utc_now(),
        "state": state,
        "decision": decision,
        "blocker": blocker,
        "first_unverified_step": next_step,
        "fake_data": False,
        "final_ready": False,
        "canonical_sample_rows_in_scope": 3,
        "hmlr_inspire_ids_in_scope": ["46058185", "46037757", "45981756"],
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "fixture_sha256": sha256_bytes(fixture_bytes),
        "official_source_evidence_count": len(manifest),
        "source_evidence_manifest": manifest,
        "candidate_url_count": len(seen),
        "probe_count": len(probes),
        "total_bytes_read": total,
        "max_total_bytes": MAX_TOTAL_BYTES,
        "validated_schema_count": len(validated),
        "validated_schema_urls": [p["final_url"] or p["source_url"] for p in validated],
        "probes": probes,
        "network_or_validation_errors": network_errors,
        "authorization_header_sent": False,
        "bearer_token_used": False,
        "archive_downloaded": False,
    }
    atomic_json(args.output, payload)


if __name__ == "__main__":
    main()

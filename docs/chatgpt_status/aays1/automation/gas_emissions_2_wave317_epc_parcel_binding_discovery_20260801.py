#!/usr/bin/env python3
"""Fail-closed EPC/UPRN parcel-binding source discovery for gas_emissions_2."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

EXPECTED = {
    "landing": {
        "url": "https://get-energy-performance-data.communities.gov.uk/",
        "phrases": ["download bulk certificate data in CSV format", "developer API", "GOV.UK One Login"],
    },
    "api_guidance": {
        "url": "https://get-energy-performance-data.communities.gov.uk/guidance/energy-certificate-data-apis",
        "phrases": ["bearer token", "GOV.UK One Login"],
    },
    "making_request": {
        "url": "https://get-energy-performance-data.communities.gov.uk/api-technical-documentation/making-a-request",
        "phrases": ["https://api.get-energy-performance-data.communities.gov.uk", "Authorization", "Bearer"],
    },
    "domestic_search": {
        "url": "https://get-energy-performance-data.communities.gov.uk/api-technical-documentation/search-certificates/domestic",
        "phrases": ["GET /api/domestic/search", "uprn", "12-digit unique property reference number"],
    },
    "licensing": {
        "url": "https://get-energy-performance-data.communities.gov.uk/guidance/licensing-restrictions",
        "phrases": ["Open Government Licence v3.0", "Ordnance Survey UPRNs"],
    },
    "official_release": {
        "url": "https://www.gov.uk/government/statistics/energy-performance-of-building-certificates-in-england-and-wales-january-to-march-2026/energy-performance-of-buildings-certificates-statistical-release-january-to-march-2026-england-and-wales",
        "phrases": ["address level", "Unique Property Reference Numbers", "carbon dioxide emissions"],
    },
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_fixture(payload: dict) -> list[dict]:
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise ValueError("SOURCES_LIST_REQUIRED")
    indexed = {row.get("source_id"): row for row in sources if isinstance(row, dict)}
    validated: list[dict] = []
    for source_id, expected in EXPECTED.items():
        row = indexed.get(source_id)
        if not row:
            raise ValueError(f"MISSING_SOURCE:{source_id}")
        if row.get("source_url") != expected["url"]:
            raise ValueError(f"URL_MISMATCH:{source_id}")
        excerpt = str(row.get("relevant_excerpt") or "")
        missing = [phrase for phrase in expected["phrases"] if phrase.lower() not in excerpt.lower()]
        if missing:
            raise ValueError(f"MISSING_PHRASES:{source_id}:{missing}")
        declared = row.get("excerpt_sha256")
        actual = sha256_text(excerpt)
        if declared != actual:
            raise ValueError(f"SHA_MISMATCH:{source_id}")
        validated.append({**row, "validated": True})
    return validated


def run(fixture: Path, output: Path, parcel_uprn_map: Path | None) -> dict:
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    sources = validate_fixture(payload)
    map_present = bool(parcel_uprn_map and parcel_uprn_map.is_file())
    result = {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 317,
        "state": "NO_DATA_CONTINUE" if not map_present else "SOURCE_READY_FOR_BINDING",
        "decision": "NO_DATA_CONTINUE" if not map_present else "CONTINUE_WITH_STRICT_BINDING",
        "decision_reason": (
            "Official EPC sources prove UPRN-addressable certificate access and CO2-related fields, "
            "but bearer-token access is required and no canonical parcel-to-UPRN mapping input was supplied."
            if not map_present
            else "A parcel-to-UPRN map was supplied; downstream binding must still validate one-to-one identity."
        ),
        "source_evidence_manifest": sources,
        "source_count": len(sources),
        "official_source_discovery": "PASS",
        "api_authentication_requirement": "BEARER_TOKEN_REQUIRED",
        "parcel_uprn_map_present": map_present,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "fake_data": False,
        "final_ready": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return result


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sources = []
        for source_id, expected in EXPECTED.items():
            excerpt = " | ".join(expected["phrases"])
            sources.append({
                "source_id": source_id,
                "source_url": expected["url"],
                "accessed_at": "2026-08-01T15:19:00Z",
                "relevant_excerpt": excerpt,
                "excerpt_sha256": sha256_text(excerpt),
                "supports_fields": ["test"],
            })
        fixture = root / "fixture.json"
        output = root / "out.json"
        fixture.write_text(json.dumps({"sources": sources}), encoding="utf-8")
        result = run(fixture, output, None)
        assert result["decision"] == "NO_DATA_CONTINUE"
        assert result["source_count"] == len(EXPECTED)
        assert output.is_file()
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--parcel-uprn-map", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.fixture or not args.output:
        parser.error("--fixture and --output are required")
    result = run(args.fixture, args.output, args.parcel_uprn_map)
    print(json.dumps({"state": result["state"], "sources": result["source_count"], "rows": 0}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Wave344: validate official Find an Energy Certificate public route metadata."""
from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_REPO = "communitiesuk/epb-frontend"
EXPECTED_COMMIT = "90874a0177482b1be942674391b335c020efe7e7"
REQUIRED_ROUTE_KEYS = {
    ("GET", "/find-a-certificate/type-of-property"),
    ("POST", "/find-a-certificate/type-of-property"),
    ("GET", "/find-a-certificate/search-by-postcode"),
    ("GET", "/find-a-certificate/search-by-reference-number"),
    ("GET", "/find-a-certificate/search-by-street-name-and-town"),
    ("GET", "/find-a-non-domestic-certificate/search-by-postcode"),
}
REQUIRED_FIELDS = {"property_type", "postcode", "reference_number", "street_name", "town"}
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()

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

def validate_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    manifest = fixture.get("source_evidence_manifest", [])
    if len(manifest) != 4:
        raise ValueError("exactly four official source evidence records are required")
    if fixture.get("official_source_repo") != EXPECTED_REPO:
        raise ValueError("unexpected official source repository")
    if fixture.get("official_source_commit") != EXPECTED_COMMIT:
        raise ValueError("unexpected official source commit")
    for record in manifest:
        if record.get("source_repo") != EXPECTED_REPO or record.get("source_commit") != EXPECTED_COMMIT:
            raise ValueError("source record repository/commit mismatch")
        if len(record.get("content_sha256", "")) != 64:
            raise ValueError("invalid source evidence SHA-256")
        if not record.get("source_blob_sha") or not record.get("record_scope") or not record.get("supports_fields"):
            raise ValueError("incomplete source evidence record")
    routes = fixture.get("expected_routes", [])
    route_keys = {(r.get("method"), r.get("path")) for r in routes}
    fields = {field for r in routes for field in r.get("query_fields", [])}
    unsupported = set(fixture.get("unsupported_search_identifiers", []))
    return {
        "manifest_count": len(manifest),
        "route_count": len(routes),
        "required_routes_present": REQUIRED_ROUTE_KEYS.issubset(route_keys),
        "required_query_fields_present": REQUIRED_FIELDS.issubset(fields),
        "uprn_route_present": "uprn" in fields,
        "hmlr_inspire_id_route_present": "hmlr_inspire_id" in fields,
        "unsupported_identifiers_declared": {"uprn", "hmlr_inspire_id"}.issubset(unsupported),
        "route_inventory": routes,
        "query_fields": sorted(fields),
    }

def self_test() -> None:
    sample = {
        "official_source_repo": EXPECTED_REPO,
        "official_source_commit": EXPECTED_COMMIT,
        "source_evidence_manifest": [
            {"source_repo": EXPECTED_REPO, "source_commit": EXPECTED_COMMIT, "content_sha256": EMPTY_SHA256,
             "source_blob_sha": "abc", "record_scope": "x", "supports_fields": ["x"]}
            for _ in range(4)
        ],
        "expected_routes": [
            {"method": method, "path": path, "query_fields": []}
            for method, path in sorted(REQUIRED_ROUTE_KEYS)
        ] + [{"method": "GET", "path": "/fields", "query_fields": sorted(REQUIRED_FIELDS)}],
        "unsupported_search_identifiers": ["uprn", "hmlr_inspire_id"],
    }
    result = validate_fixture(sample)
    assert result["required_routes_present"]
    assert result["required_query_fields_present"]
    assert not result["uprn_route_present"]
    assert not result["hmlr_inspire_id_route_present"]
    print("SELF_TEST_PASS")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test(); return
    if not args.fixture or not args.output:
        parser.error("--fixture and --output are required unless --self-test is used")
    fixture_bytes = args.fixture.read_bytes()
    fixture = json.loads(fixture_bytes)
    validation = validate_fixture(fixture)
    validated = (
        validation["required_routes_present"]
        and validation["required_query_fields_present"]
        and validation["unsupported_identifiers_declared"]
        and not validation["uprn_route_present"]
        and not validation["hmlr_inspire_id_route_present"]
    )
    if not validated:
        raise SystemExit("official public route metadata validation failed")
    blocker = (
        "PUBLIC_ROUTE_METADATA_VALIDATED_BUT_THREE_CANONICAL_SAMPLE_ADDRESSES_OR_POSTCODES_NOT_ACQUIRED;"
        "THREE_EXACT_UPRNS_NOT_ACQUIRED;"
        "PUBLIC_FRONTEND_HAS_NO_UPRN_OR_HMLR_INSPIRE_ID_SEARCH_ROUTE;"
        "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    )
    payload = {
        "schema_version": 1, "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": "gas_emissions_2", "wave": 344,
        "accessed_at": utc_now(), "state": "NO_DATA_CONTINUE",
        "decision": "OFFICIAL_PUBLIC_ROUTE_METADATA_VALIDATED_NO_QUERY_INPUTS",
        "blocker": blocker,
        "first_unverified_step": "ASSESS_CANONICAL_SAMPLE_ADDRESS_OR_POSTCODE_SOURCE_FOR_PUBLIC_EPC_REGISTER_LOOKUP_OR_NO_DATA_CONTINUE",
        "fake_data": False, "final_ready": False,
        "canonical_sample_rows_in_scope": 3,
        "hmlr_inspire_ids_in_scope": ["46058185", "46037757", "45981756"],
        "business_rows_produced": 0, "parcel_rows_bound": 0,
        "completed_count": 0, "target_count": 30761,
        "previous_percent": 0.0, "current_percent": 0.0, "percent_increase": 0.0,
        "fixture_sha256": sha256_bytes(fixture_bytes),
        "official_source_repo": EXPECTED_REPO, "official_source_commit": EXPECTED_COMMIT,
        "official_source_evidence_count": validation["manifest_count"],
        "source_evidence_manifest": fixture["source_evidence_manifest"],
        "public_route_metadata_validated": True,
        "route_count": validation["route_count"],
        "route_inventory": validation["route_inventory"],
        "query_fields": validation["query_fields"],
        "uprn_search_route_present": False,
        "hmlr_inspire_id_search_route_present": False,
        "network_request_performed": False,
        "form_submitted": False,
        "personal_data_submitted": False,
        "certificate_downloaded": False,
    }
    atomic_json(args.output, payload)

if __name__ == "__main__":
    main()

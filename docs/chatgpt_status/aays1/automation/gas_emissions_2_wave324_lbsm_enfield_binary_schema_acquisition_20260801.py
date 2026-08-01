#!/usr/bin/env python3
"""Wave324 fail-closed LBSM2 Enfield binary/schema acquisition gate."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

SOURCE_IDS = {
    "canonical_wave323",
    "gla_lbsm2_dataset_listing",
    "data_gov_lbsm2_dataset_listing",
    "data_gov_enfield_resource_endpoint",
    "data_gov_dictionary_resource_metadata",
    "gla_lbsm2_blog",
}
RESOURCE_KEYS = {"enfield_resource", "data_dictionary", "api_on_request"}

def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture object required")
    return value

def validate(value: dict[str, Any]):
    if (value.get("slot_id"), value.get("wave")) != ("gas_emissions_2", 324):
        raise ValueError("slot/wave mismatch")
    ctx = value.get("canonical_context")
    resources = value.get("resource_assessment")
    manifest = value.get("source_evidence_manifest")
    if not isinstance(ctx, dict) or not isinstance(resources, dict) or not isinstance(manifest, list):
        raise ValueError("sections missing")
    if ctx.get("wave323_remote_readback") != "PASS":
        raise ValueError("Wave323 readback missing")
    if ctx.get("slot_partition") != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("partition mismatch")
    for key in ("canonical_uprn_binding_present", "canonical_toid_binding_present", "canonical_address_binding_present"):
        if ctx.get(key) is not False:
            raise ValueError(f"{key} unexpectedly present")
    if set(resources) != RESOURCE_KEYS:
        raise ValueError("resource set mismatch")
    enfield = resources["enfield_resource"]
    dictionary = resources["data_dictionary"]
    api = resources["api_on_request"]
    if enfield.get("resource_uuid") != "2359ab8c-19ed-4eeb-8429-4ea27f389d33":
        raise ValueError("Enfield resource UUID mismatch")
    if dictionary.get("resource_uuid") != "bdbaed62-2c12-46c3-9042-88c149bf4345":
        raise ValueError("dictionary resource UUID mismatch")
    if dictionary.get("package_uuid") != "e03aa07a-ee8a-4b1a-a04c-cc6e23133340":
        raise ValueError("package UUID mismatch")
    for item in (enfield, dictionary, api):
        if item.get("parcel_bindable") is not False:
            raise ValueError("resource unexpectedly parcel-bindable")
    if enfield.get("binary_bytes_acquired") is not False or enfield.get("schema_header_verified") is not False:
        raise ValueError("Enfield acquisition state mismatch")
    if dictionary.get("binary_bytes_acquired") is not False or dictionary.get("download_url_resolved") is not False:
        raise ValueError("dictionary acquisition state mismatch")
    by = {}
    for item in manifest:
        sid = item.get("source_id")
        excerpt = item.get("relevant_excerpt")
        if not isinstance(sid, str) or not isinstance(excerpt, str) or not excerpt:
            raise ValueError("source identity/excerpt missing")
        if item.get("excerpt_sha256") != digest(excerpt):
            raise ValueError(f"{sid}: excerpt sha mismatch")
        for key in ("publisher", "source_url", "accessed_at", "hash_scope", "supports_fields", "license_or_terms_url"):
            if not item.get(key):
                raise ValueError(f"{sid}: {key} missing")
        by[sid] = item
    if set(by) != SOURCE_IDS:
        raise ValueError("source set mismatch")
    return [by[k] for k in sorted(by)], ctx, resources

def build(value: dict[str, Any]) -> dict[str, Any]:
    manifest, ctx, resources = validate(value)
    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 324,
        "state": "NO_DATA_CONTINUE",
        "decision": "LBSM2_ENFIELD_BINARY_SCHEMA_ACQUISITION_NO_DATA_CONTINUE",
        "decision_reason": (
            "The official Enfield resource UUID and the data-dictionary resource UUID were resolved. "
            "The Enfield resource endpoint returned a cache miss and exposed no download URL or bytes; "
            "the dictionary resource metadata reports format unknown and no views and exposed no spreadsheet bytes. "
            "Therefore no CSV header, schema fields, content SHA-256 or deterministic canonical parcel binding can be verified. "
            "No modelled value is promoted as actual gas-meter data and no spatial guessing is used."
        ),
        "canonical_context": ctx,
        "resource_assessment": resources,
        "source_count": len(manifest),
        "source_evidence_manifest": manifest,
        "resolved_blockers": [
            "LBSM2_ENFIELD_RESOURCE_UUID_UNKNOWN",
            "LBSM2_DATA_DICTIONARY_RESOURCE_UUID_UNKNOWN",
            "LBSM2_ENFIELD_LISTED_FILE_SIZE_UNVERIFIED",
        ],
        "remaining_blocker": (
            "LBSM2_ENFIELD_RESOURCE_ENDPOINT_CACHE_MISS;"
            "LBSM2_ENFIELD_DOWNLOAD_URL_NOT_RESOLVED_FROM_PUBLIC_RESOURCE_METADATA;"
            "LBSM2_ENFIELD_BINARY_BYTES_NOT_ACQUIRED;"
            "LBSM2_DATA_DICTIONARY_DOWNLOAD_URL_NOT_RESOLVED;"
            "LBSM2_DATA_DICTIONARY_BYTES_NOT_ACQUIRED;"
            "LBSM2_SCHEMA_HEADER_NOT_VERIFIED;"
            "CANONICAL_PARCEL_UPRN_TOID_OR_ADDRESS_BINDING_ABSENT;"
            "LBSM2_VALUES_ARE_MODELLED_THEORETICAL_NOT_ACTUAL_GAS_METER_DATA;"
            "POINT_TO_BUILDING_SPATIAL_GUESSING_FORBIDDEN;"
            "PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": "LBSM2_ENFIELD_DOWNLOAD_URL_OR_API_ON_REQUEST_AUTHORISED_ACQUISITION_OR_NO_DATA_CONTINUE",
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

def self_test() -> None:
    excerpt = "x"
    manifest = [
        {
            "source_id": sid,
            "publisher": "x",
            "source_url": "https://example.invalid",
            "accessed_at": "x",
            "hash_scope": "x",
            "relevant_excerpt": excerpt,
            "excerpt_sha256": digest(excerpt),
            "supports_fields": ["x"],
            "license_or_terms_url": "https://example.invalid",
        }
        for sid in SOURCE_IDS
    ]
    resources = {
        "enfield_resource": {
            "resource_uuid": "2359ab8c-19ed-4eeb-8429-4ea27f389d33",
            "binary_bytes_acquired": False,
            "schema_header_verified": False,
            "parcel_bindable": False,
        },
        "data_dictionary": {
            "resource_uuid": "bdbaed62-2c12-46c3-9042-88c149bf4345",
            "package_uuid": "e03aa07a-ee8a-4b1a-a04c-cc6e23133340",
            "download_url_resolved": False,
            "binary_bytes_acquired": False,
            "parcel_bindable": False,
        },
        "api_on_request": {
            "parcel_bindable": False,
        },
    }
    fixture = {
        "slot_id": "gas_emissions_2",
        "wave": 324,
        "canonical_context": {
            "wave323_remote_readback": "PASS",
            "slot_partition": {"start": 30762, "end": 61522, "count": 30761},
            "canonical_uprn_binding_present": False,
            "canonical_toid_binding_present": False,
            "canonical_address_binding_present": False,
        },
        "resource_assessment": resources,
        "source_evidence_manifest": manifest,
    }
    out = build(fixture)
    assert out["source_count"] == 6 and out["parcel_rows_bound"] == 0
    print("SELF_TEST_PASS")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.fixture is None or args.output is None:
        parser.error("--fixture and --output required")
    out = build(load(args.fixture))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    print("DECISION=" + out["decision"])
    print("BUSINESS_ROWS_PRODUCED=0")
    print("PARCEL_ROWS_BOUND=0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

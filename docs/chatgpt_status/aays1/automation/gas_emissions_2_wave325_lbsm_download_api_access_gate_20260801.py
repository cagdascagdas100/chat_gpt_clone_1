#!/usr/bin/env python3
"""Wave325 fail-closed LBSM2 download/API access gate."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

SOURCE_IDS = {
    "canonical_wave324",
    "gla_lbsm2_blog",
    "gla_lbsm2_dataset_listing",
    "data_gov_api_documentation",
    "data_gov_enfield_resource_endpoint",
    "data_gov_dictionary_resource_metadata",
}
ACCESS_KEYS = {"public_directory_api", "lbsm2_api_on_request", "enfield_download", "data_dictionary_download"}

def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture object required")
    return value

def validate(value: dict[str, Any]):
    if (value.get("slot_id"), value.get("wave")) != ("gas_emissions_2", 325):
        raise ValueError("slot/wave mismatch")
    ctx = value.get("canonical_context")
    access = value.get("access_assessment")
    manifest = value.get("source_evidence_manifest")
    if not isinstance(ctx, dict) or not isinstance(access, dict) or not isinstance(manifest, list):
        raise ValueError("sections missing")
    if ctx.get("wave324_remote_readback") != "PASS":
        raise ValueError("Wave324 readback missing")
    if ctx.get("slot_partition") != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("partition mismatch")
    if set(access) != ACCESS_KEYS:
        raise ValueError("access set mismatch")
    if access["public_directory_api"].get("api_key_required") is not False:
        raise ValueError("directory API key gate mismatch")
    if access["lbsm2_api_on_request"].get("access_mode") != "AVAILABLE_ON_REQUEST":
        raise ValueError("LBSM2 API mode mismatch")
    if access["lbsm2_api_on_request"].get("authorised_access_receipt_present") is not False:
        raise ValueError("unexpected authorised receipt")
    for key in ("enfield_download", "data_dictionary_download"):
        if access[key].get("download_url_resolved") is not False or access[key].get("binary_bytes_acquired") is not False:
            raise ValueError(f"{key} acquisition state mismatch")
        if access[key].get("parcel_bindable") is not False:
            raise ValueError(f"{key} unexpectedly parcel-bindable")
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
    return [by[k] for k in sorted(by)], ctx, access

def build(value: dict[str, Any]) -> dict[str, Any]:
    manifest, ctx, access = validate(value)
    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 325,
        "state": "NO_DATA_CONTINUE",
        "decision": "LBSM2_DOWNLOAD_API_ACCESS_GATE_NO_DATA_CONTINUE",
        "decision_reason": (
            "Official data.gov.uk guidance confirms that the public directory API needs no API key and states no rate limits, "
            "but the GLA LBSM2 building-level API is available only on request and no authorised access receipt is present in the canonical inputs. "
            "The official Enfield resource endpoint still returns a cache miss, and neither the Enfield CSV nor the data dictionary exposes a resolved "
            "download URL or acquired bytes in this execution. No schema, content hash, actual gas-meter value, or deterministic parcel binding can be promoted."
        ),
        "canonical_context": ctx,
        "access_assessment": access,
        "source_count": len(manifest),
        "source_evidence_manifest": manifest,
        "resolved_blockers": [
            "PUBLIC_DIRECTORY_API_AUTHENTICATION_REQUIREMENT_UNKNOWN",
            "LBSM2_API_ACCESS_MODE_UNKNOWN",
        ],
        "remaining_blocker": (
            "LBSM2_API_AVAILABLE_ON_REQUEST_BUT_AUTHORISED_ACCESS_RECEIPT_ABSENT;"
            "LBSM2_ENFIELD_RESOURCE_ENDPOINT_CACHE_MISS;"
            "LBSM2_ENFIELD_DOWNLOAD_URL_UNRESOLVED;"
            "LBSM2_ENFIELD_BINARY_BYTES_NOT_ACQUIRED;"
            "LBSM2_DATA_DICTIONARY_DOWNLOAD_URL_UNRESOLVED;"
            "LBSM2_DATA_DICTIONARY_BYTES_NOT_ACQUIRED;"
            "LBSM2_SCHEMA_HEADER_NOT_VERIFIED;"
            "CANONICAL_PARCEL_UPRN_TOID_OR_ADDRESS_BINDING_ABSENT;"
            "LBSM2_VALUES_ARE_MODELLED_THEORETICAL_NOT_ACTUAL_GAS_METER_DATA;"
            "PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": "OPEN_UPRN_TOID_OR_ADDRESS_IDENTIFIER_BRIDGE_DISCOVERY_OR_NO_DATA_CONTINUE",
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
    manifest = [{
        "source_id": sid, "publisher": "x", "source_url": "https://example.invalid", "accessed_at": "x",
        "hash_scope": "x", "relevant_excerpt": excerpt, "excerpt_sha256": digest(excerpt),
        "supports_fields": ["x"], "license_or_terms_url": "https://example.invalid",
    } for sid in SOURCE_IDS]
    access = {
        "public_directory_api": {"api_key_required": False},
        "lbsm2_api_on_request": {"access_mode": "AVAILABLE_ON_REQUEST", "authorised_access_receipt_present": False},
        "enfield_download": {"download_url_resolved": False, "binary_bytes_acquired": False, "parcel_bindable": False},
        "data_dictionary_download": {"download_url_resolved": False, "binary_bytes_acquired": False, "parcel_bindable": False},
    }
    fixture = {
        "slot_id": "gas_emissions_2", "wave": 325,
        "canonical_context": {"wave324_remote_readback": "PASS", "slot_partition": {"start": 30762, "end": 61522, "count": 30761}},
        "access_assessment": access, "source_evidence_manifest": manifest,
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
        self_test(); return 0
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

#!/usr/bin/env python3
"""Wave327 fail-closed OS Open UPRN Enfield acquisition and collision-audit gate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_IDS = {
    "canonical_wave326",
    "canonical_parcel_sample",
    "os_open_uprn_data_hub",
    "os_open_uprn_product_supply",
    "os_downloads_api_technical_spec",
    "os_download_open_product_endpoint",
    "os_open_uprn_schema",
    "runtime_endpoint_fetch_attempt",
}
REQUIRED_SAMPLE_IDS = {"parcel_30762", "parcel_30763", "parcel_30764"}

def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture object required")
    return value

def validate(value: dict[str, Any]):
    if (value.get("slot_id"), value.get("wave")) != ("gas_emissions_2", 327):
        raise ValueError("slot/wave mismatch")
    ctx = value.get("canonical_context")
    acquisition = value.get("acquisition_assessment")
    samples = value.get("canonical_samples")
    manifest = value.get("source_evidence_manifest")
    if not isinstance(ctx, dict) or not isinstance(acquisition, dict) or not isinstance(samples, list) or not isinstance(manifest, list):
        raise ValueError("required sections missing")
    if ctx.get("wave326_remote_readback") != "PASS":
        raise ValueError("Wave326 readback missing")
    if ctx.get("slot_partition") != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("partition mismatch")
    if {item.get("parcel_id") for item in samples} != REQUIRED_SAMPLE_IDS:
        raise ValueError("canonical sample mismatch")
    for item in samples:
        if item.get("geometry_type") != "Point" or item.get("uprn") is not None:
            raise ValueError("canonical sample identity mismatch")
    required = {
        "product_version", "product_coverage", "formats", "open_data_api_key_required",
        "full_supply_only", "aoi_available", "direct_download_endpoint_resolved",
        "endpoint_fetch_attempted", "endpoint_fetch_result", "metadata_bytes_acquired",
        "binary_bytes_acquired", "enfield_subset_acquired", "collision_audit_performed",
    }
    if set(acquisition) != required:
        raise ValueError("acquisition field set mismatch")
    if acquisition["product_version"] != "June 2026" or acquisition["product_coverage"] != "Great Britain":
        raise ValueError("product metadata mismatch")
    if acquisition["formats"] != ["CSV", "GeoPackage"]:
        raise ValueError("format mismatch")
    if acquisition["open_data_api_key_required"] is not False:
        raise ValueError("OpenData authentication mismatch")
    if acquisition["full_supply_only"] is not True or acquisition["aoi_available"] is not False:
        raise ValueError("supply scope mismatch")
    if acquisition["direct_download_endpoint_resolved"] is not True or acquisition["endpoint_fetch_attempted"] is not True:
        raise ValueError("endpoint gate mismatch")
    if acquisition["endpoint_fetch_result"] != "DNS_RESOLUTION_FAILURE":
        raise ValueError("fetch result mismatch")
    for key in ("metadata_bytes_acquired", "binary_bytes_acquired", "enfield_subset_acquired", "collision_audit_performed"):
        if acquisition[key] is not False:
            raise ValueError(f"{key} must be false")
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
    return [by[k] for k in sorted(by)], ctx, acquisition, samples

def build(value: dict[str, Any]) -> dict[str, Any]:
    manifest, ctx, acquisition, samples = validate(value)
    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 327,
        "state": "NO_DATA_CONTINUE",
        "decision": "OS_OPEN_UPRN_ENFIELD_SUBSET_ACQUISITION_NO_DATA_CONTINUE",
        "decision_reason": (
            "The June 2026 OS Open UPRN product and its no-key OpenData download endpoint were resolved from official sources. "
            "OS supplies this product only as a full Great Britain CSV or GeoPackage; no AOI/Enfield order is available. "
            "The execution environment attempted the official CSV endpoint but DNS resolution failed before metadata or binary bytes were acquired. "
            "Consequently no Enfield subset or exact-coordinate collision audit could be performed. The canonical carrier remains HMLR point previews "
            "with no declared UPRN identity, so no coordinate equality or parcel binding is promoted."
        ),
        "canonical_context": ctx,
        "canonical_samples": samples,
        "acquisition_assessment": acquisition,
        "source_count": len(manifest),
        "source_evidence_manifest": manifest,
        "resolved_blockers": [
            "OS_OPEN_UPRN_DIRECT_DOWNLOAD_ENDPOINT_UNKNOWN",
            "OS_OPEN_UPRN_ACCESS_AUTHENTICATION_UNKNOWN",
            "OS_OPEN_UPRN_SUPPLY_SCOPE_UNKNOWN",
            "OS_OPEN_UPRN_CURRENT_VERSION_UNKNOWN",
        ],
        "remaining_blocker": (
            "OS_OPEN_UPRN_DIRECT_DOWNLOAD_ENDPOINT_DNS_UNRESOLVED_IN_EXECUTION_ENVIRONMENT;"
            "OS_OPEN_UPRN_FULL_GB_BINARY_NOT_ACQUIRED;"
            "OS_OPEN_UPRN_AOI_NOT_AVAILABLE;"
            "OS_OPEN_UPRN_ENFIELD_SUBSET_NOT_ACQUIRED;"
            "OS_OPEN_UPRN_COORDINATE_COLLISION_AUDIT_NOT_PERFORMED;"
            "CANONICAL_HMLR_POINT_NOT_DECLARED_AS_OS_ADDRESS_POINT;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": "OS_OPEN_UPRN_DIRECT_DOWNLOAD_NETWORK_RECOVERY_AND_BOUNDED_HEADER_ACQUISITION_OR_NO_DATA_CONTINUE",
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
        "source_id": sid, "publisher": "x", "source_url": "https://example.invalid",
        "accessed_at": "x", "hash_scope": "x", "relevant_excerpt": excerpt,
        "excerpt_sha256": digest(excerpt), "supports_fields": ["x"],
        "license_or_terms_url": "https://example.invalid",
    } for sid in SOURCE_IDS]
    fixture = {
        "slot_id": "gas_emissions_2",
        "wave": 327,
        "canonical_context": {
            "wave326_remote_readback": "PASS",
            "slot_partition": {"start": 30762, "end": 61522, "count": 30761},
        },
        "canonical_samples": [
            {"parcel_id": "parcel_30762", "geometry_type": "Point", "uprn": None},
            {"parcel_id": "parcel_30763", "geometry_type": "Point", "uprn": None},
            {"parcel_id": "parcel_30764", "geometry_type": "Point", "uprn": None},
        ],
        "acquisition_assessment": {
            "product_version": "June 2026",
            "product_coverage": "Great Britain",
            "formats": ["CSV", "GeoPackage"],
            "open_data_api_key_required": False,
            "full_supply_only": True,
            "aoi_available": False,
            "direct_download_endpoint_resolved": True,
            "endpoint_fetch_attempted": True,
            "endpoint_fetch_result": "DNS_RESOLUTION_FAILURE",
            "metadata_bytes_acquired": False,
            "binary_bytes_acquired": False,
            "enfield_subset_acquired": False,
            "collision_audit_performed": False,
        },
        "source_evidence_manifest": manifest,
    }
    out = build(fixture)
    assert out["source_count"] == 8
    assert out["parcel_rows_bound"] == 0
    assert out["first_unverified_step"].startswith("OS_OPEN_UPRN_DIRECT_DOWNLOAD")
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

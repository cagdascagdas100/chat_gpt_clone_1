#!/usr/bin/env python3
"""Wave326 fail-closed open identifier bridge discovery gate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SOURCE_IDS = {
    "canonical_wave325",
    "canonical_parcel_sample",
    "os_open_uprn",
    "os_open_linked_identifiers",
    "os_open_toid",
    "hmlr_inspire",
    "hmlr_national_polygon_service",
    "govuk_property_identifier_standard",
}
BRIDGE_KEYS = {
    "os_open_uprn_coordinate_bridge",
    "os_open_linked_uprn_toid",
    "os_open_toid_generalised_point",
    "hmlr_inspire_open_polygon",
    "hmlr_title_uprn_lookup_nps",
    "complete_address_or_classification",
}


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture object required")
    return value


def validate(value: dict[str, Any]):
    if (value.get("slot_id"), value.get("wave")) != ("gas_emissions_2", 326):
        raise ValueError("slot/wave mismatch")
    ctx = value.get("canonical_context")
    bridges = value.get("bridge_assessment")
    manifest = value.get("source_evidence_manifest")
    if not isinstance(ctx, dict) or not isinstance(bridges, dict) or not isinstance(manifest, list):
        raise ValueError("sections missing")
    if ctx.get("wave325_remote_readback") != "PASS":
        raise ValueError("Wave325 readback missing")
    if ctx.get("slot_partition") != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("partition mismatch")
    if ctx.get("canonical_carrier_geometry") != "Point":
        raise ValueError("canonical carrier geometry mismatch")
    if ctx.get("canonical_identifier_fields") != ["parcel_id", "hmlr_inspire_id"]:
        raise ValueError("canonical identifier fields mismatch")
    if set(bridges) != BRIDGE_KEYS:
        raise ValueError("bridge set mismatch")
    for item in bridges.values():
        if item.get("exact_open_canonical_bridge") is not False:
            raise ValueError("bridge unexpectedly exact/open/canonical")
        if item.get("parcel_bindable") is not False:
            raise ValueError("bridge unexpectedly parcel-bindable")
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
    return [by[k] for k in sorted(by)], ctx, bridges


def build(value: dict[str, Any]) -> dict[str, Any]:
    manifest, ctx, bridges = validate(value)
    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 326,
        "state": "NO_DATA_CONTINUE",
        "decision": "OPEN_IDENTIFIER_BRIDGE_DISCOVERY_NO_DATA_CONTINUE",
        "decision_reason": (
            "The canonical carrier exposes parcel_id and HMLR INSPIRE ID on Point preview geometry, but no UPRN, TOID, address, title number, or exact title polygon. "
            "OS Open UPRN supplies UPRN and point coordinates; OS Open Linked Identifiers supplies UPRN-to-TOID relationships without HMLR keys or geometry; "
            "OS Open TOID supplies generalised point locations rather than source polygons. HMLR INSPIRE supplies open indicative freehold polygons and INSPIRE IDs but no UPRN/TOID crosswalk. "
            "HMLR's authoritative Title Number and UPRN Look Up exists only inside the licensed, chargeable National Polygon Service and is not a canonical input. "
            "Government guidance also warns that multiple UPRNs can share one grid reference, so coordinate equality alone is not a unique authoritative parcel bridge."
        ),
        "canonical_context": ctx,
        "bridge_assessment": bridges,
        "source_count": len(manifest),
        "source_evidence_manifest": manifest,
        "resolved_blockers": [
            "OPEN_IDENTIFIER_BRIDGE_CANDIDATE_CLASSES_UNASSESSED",
            "HMLR_TITLE_TO_UPRN_BRIDGE_EXISTENCE_UNKNOWN",
            "OPEN_UPRN_COORDINATE_UNIQUENESS_UNKNOWN",
        ],
        "remaining_blocker": (
            "HMLR_TITLE_NUMBER_TO_UPRN_LOOKUP_IS_CHARGEABLE_AND_NOT_CANONICAL_INPUT;"
            "OPEN_INSPIRE_ID_TO_UPRN_OR_TOID_CROSSWALK_ABSENT;"
            "OS_OPEN_LINKED_IDENTIFIERS_HAS_NO_HMLR_INSPIRE_OR_TITLE_KEY;"
            "OS_OPEN_UPRN_HAS_POINT_COORDINATES_ONLY_AND_GRID_REFERENCE_MAY_MAP_MULTIPLE_UPRNS;"
            "OS_OPEN_TOID_LOCATION_IS_GENERALISED_POINT_NOT_SOURCE_POLYGON;"
            "CANONICAL_PARCEL_CARRIER_IS_HMLR_POINT_PREVIEW_WITH_NO_UPRN_TOID_ADDRESS;"
            "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": "OS_OPEN_UPRN_ENFIELD_SUBSET_ACQUISITION_AND_EXACT_COORDINATE_COLLISION_AUDIT_OR_NO_DATA_CONTINUE",
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
        "source_id": sid,
        "publisher": "x",
        "source_url": "https://example.invalid",
        "accessed_at": "x",
        "hash_scope": "x",
        "relevant_excerpt": excerpt,
        "excerpt_sha256": digest(excerpt),
        "supports_fields": ["x"],
        "license_or_terms_url": "https://example.invalid",
    } for sid in SOURCE_IDS]
    bridges = {key: {"exact_open_canonical_bridge": False, "parcel_bindable": False} for key in BRIDGE_KEYS}
    fixture = {
        "slot_id": "gas_emissions_2",
        "wave": 326,
        "canonical_context": {
            "wave325_remote_readback": "PASS",
            "slot_partition": {"start": 30762, "end": 61522, "count": 30761},
            "canonical_carrier_geometry": "Point",
            "canonical_identifier_fields": ["parcel_id", "hmlr_inspire_id"],
        },
        "bridge_assessment": bridges,
        "source_evidence_manifest": manifest,
    }
    out = build(fixture)
    assert out["source_count"] == 8 and out["parcel_rows_bound"] == 0
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

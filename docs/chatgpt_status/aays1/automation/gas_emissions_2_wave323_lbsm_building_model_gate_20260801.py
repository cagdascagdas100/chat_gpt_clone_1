#!/usr/bin/env python3
"""Wave323 fail-closed LBSM building-model discovery and binding gate."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

SOURCE_IDS = {
    "canonical_wave322",
    "gla_lbsm2_dataset",
    "gla_lbsm2_blog",
    "govuk_lbsm2_transparency",
    "gla_lbsm2_map_terms",
    "gla_lbsm_v1_dataset",
}
CANDIDATES = {"lbsm2_enfield_extract", "lbsm2_api_on_request", "lbsm_v1_enfield_extract"}

def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture object required")
    return value

def validate(value: dict[str, Any]):
    if (value.get("slot_id"), value.get("wave")) != ("gas_emissions_2", 323):
        raise ValueError("slot/wave mismatch")
    ctx = value.get("canonical_context")
    candidates = value.get("candidate_assessment")
    manifest = value.get("source_evidence_manifest")
    if not isinstance(ctx, dict) or not isinstance(candidates, dict) or not isinstance(manifest, list):
        raise ValueError("sections missing")
    if ctx.get("wave322_remote_readback") != "PASS":
        raise ValueError("Wave322 readback missing")
    if ctx.get("slot_partition") != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("partition mismatch")
    for key in ("canonical_uprn_binding_present", "canonical_toid_binding_present", "canonical_address_binding_present"):
        if ctx.get(key) is not False:
            raise ValueError(f"{key} unexpectedly present")
    if set(candidates) != CANDIDATES:
        raise ValueError("candidate set mismatch")
    if any(item.get("parcel_bindable") is not False for item in candidates.values()):
        raise ValueError("candidate unexpectedly parcel-bindable")
    if candidates["lbsm2_enfield_extract"].get("official_building_model_found") is not True:
        raise ValueError("official building model not found")
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
    return [by[k] for k in sorted(by)], ctx, candidates

def build(value: dict[str, Any]) -> dict[str, Any]:
    manifest, ctx, candidates = validate(value)
    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 323,
        "state": "NO_DATA_CONTINUE",
        "decision": "LBSM_BUILDING_MODEL_BINDING_GATE_NO_DATA_CONTINUE",
        "decision_reason": (
            "Official GLA sources prove that LBSM2 is a non-personal property/building-level model with an Enfield extract, "
            "modelled energy-consumption variables, UPRN-linked property records and TOID building views. The canonical parcel "
            "carrier declares no UPRN, TOID or address binding, and point-to-building spatial guessing is forbidden. The Enfield "
            "resource bytes and schema header were not read in this execution and the API is available only on request. No exact "
            "canonical parcel binding or actual gas-meter value can be promoted."
        ),
        "canonical_context": ctx,
        "candidate_assessment": candidates,
        "source_count": len(manifest),
        "source_evidence_manifest": manifest,
        "resolved_blockers": [
            "NON_PERSONAL_BUILDING_LEVEL_MODEL_NOT_IDENTIFIED",
            "LBSM2_ENFIELD_OPEN_EXTRACT_EXISTENCE_UNVERIFIED",
        ],
        "remaining_blocker": (
            "CANONICAL_PARCEL_UPRN_TOID_OR_ADDRESS_BINDING_ABSENT;"
            "LBSM2_ENFIELD_RESOURCE_BYTES_AND_HEADER_NOT_READ;"
            "LBSM2_API_AVAILABLE_ON_REQUEST_NOT_CANONICAL_INPUT;"
            "LBSM2_VALUES_INCLUDE_MODELLED_THEORETICAL_ENERGY_NOT_ACTUAL_GAS_METER_DATA;"
            "POINT_TO_BUILDING_SPATIAL_GUESSING_FORBIDDEN;"
            "PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": "LBSM2_ENFIELD_BINARY_AND_SCHEMA_ACQUISITION_OR_NO_DATA_CONTINUE",
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
    candidates = {name: {"parcel_bindable": False} for name in CANDIDATES}
    candidates["lbsm2_enfield_extract"]["official_building_model_found"] = True
    fixture = {
        "slot_id": "gas_emissions_2",
        "wave": 323,
        "canonical_context": {
            "wave322_remote_readback": "PASS",
            "slot_partition": {"start": 30762, "end": 61522, "count": 30761},
            "canonical_uprn_binding_present": False,
            "canonical_toid_binding_present": False,
            "canonical_address_binding_present": False,
        },
        "candidate_assessment": candidates,
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

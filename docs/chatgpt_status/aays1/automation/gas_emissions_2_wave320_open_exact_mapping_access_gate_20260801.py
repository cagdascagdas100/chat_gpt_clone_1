#!/usr/bin/env python3
"""Fail-closed exact parcel-to-UPRN/TOID access-gate discovery for gas_emissions_2."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

REQUIRED_SOURCE_IDS = {
    "hmlr_inspire_open",
    "nps_service_access",
    "title_uprn_spec",
    "national_polygon_spec",
    "hmlr_api_auth",
    "hmlr_2026_business_plan",
}
EXPECTED_PHRASES = {
    "hmlr_inspire_open": ["Land Registry-INSPIRE ID", "registered title", "Open Government Licence"],
    "nps_service_access": ["Title Number and UPRN Look Up dataset", "£20,000", "API key"],
    "title_uprn_spec": ["Title_No", "UPRN", "chargeable"],
    "national_polygon_spec": ["Poly_ID", "Title_No", "simpler attributes"],
    "hmlr_api_auth": ["403", "API key", "paid dataset"],
    "hmlr_2026_business_plan": ["expand the use of UPRNs", "future-plan evidence"],
}

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("fixture must be a JSON object")
    return value

def validate_fixture(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if payload.get("slot_id") != "gas_emissions_2" or payload.get("wave") != 320:
        raise ValueError("slot/wave mismatch")
    context = payload.get("canonical_context")
    if not isinstance(context, dict):
        raise ValueError("canonical_context missing")
    if context.get("canonical_identifier_format") != "parcel_<row_no>":
        raise ValueError("canonical identifier contract missing")
    partition = context.get("slot_partition")
    if partition != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("slot partition mismatch")
    if context.get("contract_evidence_rows") != 3:
        raise ValueError("Wave319 contract evidence missing")

    manifest = payload.get("source_evidence_manifest")
    if not isinstance(manifest, list):
        raise ValueError("source manifest missing")
    by_id: dict[str, dict[str, Any]] = {}
    for item in manifest:
        if not isinstance(item, dict):
            raise ValueError("source entry not object")
        source_id = item.get("source_id")
        if not isinstance(source_id, str):
            raise ValueError("source_id missing")
        excerpt = item.get("relevant_excerpt")
        if not isinstance(excerpt, str) or not excerpt:
            raise ValueError(f"{source_id}: excerpt missing")
        if item.get("excerpt_sha256") != sha256_text(excerpt):
            raise ValueError(f"{source_id}: excerpt sha mismatch")
        for phrase in EXPECTED_PHRASES.get(source_id, []):
            if phrase not in excerpt:
                raise ValueError(f"{source_id}: expected phrase missing: {phrase}")
        for key in ("publisher", "source_url", "accessed_at", "hash_scope", "supports_fields", "license_or_terms_url"):
            if not item.get(key):
                raise ValueError(f"{source_id}: {key} missing")
        by_id[source_id] = item
    if set(by_id) != REQUIRED_SOURCE_IDS:
        raise ValueError(f"source set mismatch: {sorted(by_id)}")
    return [by_id[key] for key in sorted(by_id)], context

def build_output(payload: dict[str, Any]) -> dict[str, Any]:
    manifest, context = validate_fixture(payload)
    open_bridge = bool(context.get("current_open_exact_title_to_uprn_input_present"))
    inspire_title_bridge = bool(context.get("current_open_inspire_id_to_title_number_input_present"))
    exact_polygon = bool(context.get("current_open_exact_polygon_input_present"))
    epc_token = bool(context.get("epc_bearer_token_present"))
    exact_binding_available = open_bridge and inspire_title_bridge and exact_polygon and epc_token
    if exact_binding_available:
        raise ValueError("fixture unexpectedly proves exact binding; fail closed for manual review")
    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 320,
        "state": "NO_DATA_CONTINUE",
        "decision": "OPEN_EXACT_MAPPING_ACCESS_GATE_NO_DATA_CONTINUE",
        "decision_reason": (
            "Official HM Land Registry documentation proves the deterministic bridge "
            "INSPIRE polygon -> title number -> UPRN exists only in the licensed, chargeable "
            "National Polygon Service. The current open INSPIRE dataset exposes an INSPIRE ID "
            "and indicative geometry but not the title-number/UPRN bridge. No exact open "
            "parcel-to-UPRN/TOID input, exact polygon input, or EPC bearer token is present."
        ),
        "canonical_context": context,
        "source_count": len(manifest),
        "source_evidence_manifest": manifest,
        "authoritative_bridge_contract": {
            "step_1": "INSPIRE_OR_POLYGON_TO_TITLE_NUMBER",
            "step_2": "TITLE_NUMBER_TO_UPRN",
            "official_dataset": "National Polygon Service plus Title Number and UPRN Look Up dataset",
            "current_access": "LICENSED_CHARGEABLE",
            "open_equivalent_found": False,
            "sample_scope": "Bristol 5km2 sample only; not proven to cover gas_emissions_2 Enfield partition rows",
        },
        "resolved_blockers": [
            "CANONICAL_PARCEL_IDENTIFIER_TYPE_NOT_DECLARED",
            "CANONICAL_PARCEL_GEOMETRY_INPUT_NOT_FOUND",
            "AUTHORITATIVE_MAPPING_CHAIN_UNDEFINED",
        ],
        "remaining_blocker": (
            "OPEN_EXACT_INSPIRE_ID_TO_TITLE_NUMBER_TO_UPRN_MAP_NOT_AVAILABLE;"
            "NATIONAL_POLYGON_SERVICE_LICENSE_AND_PAYMENT_REQUIRED;"
            "CANONICAL_CARRIER_GEOMETRY_IS_POINT_NOT_EXACT_POLYGON;"
            "EPC_API_BEARER_TOKEN_REQUIRED;"
            "PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": "OPEN_OR_AUTHORISED_EXACT_MAPPING_INPUT_DISCOVERY_OR_NO_DATA_CONTINUE",
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "completed_count": 0,
        "target_count": 30761,
        "previous_percent": 0.0,
        "current_percent": 0.0,
        "percent_increase": 0.0,
        "exact_binding_available": False,
        "fake_data": False,
        "final_ready": False,
    }

def self_test() -> None:
    fixture = {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 320,
        "canonical_context": {
            "continuation_key": "test",
            "task_id": "test",
            "canonical_carrier_path": "england_map_web/data/program_layer_matrix/security.geojson",
            "canonical_carrier_blob_sha": "8afd1d2bac414cf0f6b9484014e7878a4ceff877",
            "canonical_identifier_format": "parcel_<row_no>",
            "slot_partition": {"start": 30762, "end": 61522, "count": 30761},
            "contract_evidence_rows": 3,
            "current_open_exact_title_to_uprn_input_present": False,
            "current_open_inspire_id_to_title_number_input_present": False,
            "current_open_exact_polygon_input_present": False,
            "epc_bearer_token_present": False,
        },
        "source_evidence_manifest": [],
    }
    sample_excerpts = {
        "hmlr_inspire_open": "Land Registry-INSPIRE ID relates to a registered title under the Open Government Licence",
        "nps_service_access": "Title Number and UPRN Look Up dataset costs £20,000 and needs an API key",
        "title_uprn_spec": "Title_No and UPRN fields; access is chargeable",
        "national_polygon_spec": "Poly_ID and Title_No; INSPIRE has simpler attributes",
        "hmlr_api_auth": "403 without API key or access to a paid dataset",
        "hmlr_2026_business_plan": "expand the use of UPRNs; future-plan evidence",
    }
    for source_id in sorted(REQUIRED_SOURCE_IDS):
        excerpt = sample_excerpts[source_id]
        fixture["source_evidence_manifest"].append({
            "source_id": source_id,
            "publisher": "official",
            "source_url": "https://example.invalid/" + source_id,
            "accessed_at": "2026-08-01T16:33:00Z",
            "hash_scope": "normalized_visible_excerpt",
            "relevant_excerpt": excerpt,
            "excerpt_sha256": sha256_text(excerpt),
            "supports_fields": ["test"],
            "license_or_terms_url": "https://example.invalid/terms",
        })
    result = build_output(fixture)
    assert result["decision"] == "OPEN_EXACT_MAPPING_ACCESS_GATE_NO_DATA_CONTINUE"
    assert result["source_count"] == 6
    assert result["parcel_rows_bound"] == 0
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
        parser.error("--fixture and --output are required unless --self-test is used")
    payload = load_json(args.fixture)
    output = build_output(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    print("DECISION=" + output["decision"])
    print("BUSINESS_ROWS_PRODUCED=0")
    print("PARCEL_ROWS_BOUND=0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-closed OS linked-identifier contract discovery for gas_emissions_2."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

EXPECTED = {
    "linked_identifiers": {
        "phrases": [
            "authoritative relationship between Unique Property Reference Numbers",
            "TopographicArea",
            "Geometry is not included",
        ]
    },
    "linked_structure": {
        "phrases": [
            "BLPU_UPRN_TopographicArea_TOID_5",
            "BLPU <-> TopographicArea",
            "CSV",
        ]
    },
    "open_uprn": {
        "phrases": [
            "point geometry",
            "UPRN",
            "X_COORDINATE",
            "Y_COORDINATE",
        ]
    },
    "open_toid": {
        "phrases": [
            "generalised location",
            "TOID geometry always lies within the polygon",
            "point",
        ]
    },
    "hmlr_inspire": {
        "phrases": [
            "indicative extent and position of registered freehold properties",
            "download polygons by local authority",
            "OGL",
        ]
    },
}


def norm(text: str) -> str:
    return " ".join(text.split())


def sha256_text(text: str) -> str:
    return hashlib.sha256(norm(text).encode("utf-8")).hexdigest()


def validate_fixture(payload: dict[str, Any]) -> dict[str, Any]:
    sources = payload.get("sources")
    contract = payload.get("canonical_parcel_contract")
    if not isinstance(sources, list) or not isinstance(contract, dict):
        raise ValueError("INVALID_FIXTURE_SHAPE")
    by_id = {str(row.get("source_id")): row for row in sources if isinstance(row, dict)}
    if set(by_id) != set(EXPECTED):
        raise ValueError("SOURCE_SET_MISMATCH")

    evidence = []
    for source_id, spec in EXPECTED.items():
        row = by_id[source_id]
        excerpt = norm(str(row.get("relevant_excerpt") or ""))
        missing = [phrase for phrase in spec["phrases"] if phrase.lower() not in excerpt.lower()]
        if missing:
            raise ValueError(f"MISSING_REQUIRED_PHRASES:{source_id}:{missing}")
        evidence.append(
            {
                "source_id": source_id,
                "source_url": row["source_url"],
                "accessed_at": row["accessed_at"],
                "publisher": row["publisher"],
                "hash_scope": "normalized_visible_excerpt",
                "relevant_excerpt": excerpt,
                "excerpt_sha256": sha256_text(excerpt),
                "supports_fields": row["supports_fields"],
                "license_or_terms_url": row.get("license_or_terms_url"),
                "validated": True,
            }
        )

    required_contract = {
        "partition_start": 30762,
        "partition_end": 61522,
        "partition_count": 30761,
        "parcel_identifier_type_declared": False,
        "parcel_to_toid_input_present": False,
        "parcel_geometry_input_present": False,
    }
    for key, expected in required_contract.items():
        if contract.get(key) != expected:
            raise ValueError(f"CANONICAL_CONTRACT_MISMATCH:{key}")

    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 318,
        "state": "NO_DATA_CONTINUE",
        "decision": "NO_DATA_CONTINUE",
        "decision_reason": (
            "OS Open Linked Identifiers provides an authoritative UPRN-to-TopographicArea TOID "
            "relationship, but the canonical gas_emissions_2 parcel partition does not declare its "
            "identifier type and supplies neither parcel-to-TOID nor parcel geometry input. HMLR "
            "INSPIRE polygons do not document an authoritative UPRN/TOID key, so exact parcel binding "
            "cannot be promoted without a derived spatial guess."
        ),
        "source_evidence_manifest": evidence,
        "source_count": len(evidence),
        "official_source_discovery": "PASS",
        "uprn_to_topographicarea_toid_relationship": "AUTHORITATIVE_SOURCE_CONFIRMED",
        "canonical_parcel_contract": contract,
        "exact_binding_available": False,
        "derived_spatial_join_forbidden": True,
        "business_rows_produced": 0,
        "parcel_rows_bound": 0,
        "fake_data": False,
        "final_ready": False,
    }


def self_test() -> None:
    fixture = {
        "sources": [
            {
                "source_id": source_id,
                "source_url": f"https://example.invalid/{source_id}",
                "accessed_at": "2026-08-01T15:44:00Z",
                "publisher": "official",
                "relevant_excerpt": " | ".join(spec["phrases"]),
                "supports_fields": [source_id],
            }
            for source_id, spec in EXPECTED.items()
        ],
        "canonical_parcel_contract": {
            "partition_start": 30762,
            "partition_end": 61522,
            "partition_count": 30761,
            "parcel_identifier_type_declared": False,
            "parcel_to_toid_input_present": False,
            "parcel_geometry_input_present": False,
        },
    }
    result = validate_fixture(fixture)
    assert result["source_count"] == 5
    assert result["decision"] == "NO_DATA_CONTINUE"
    assert result["derived_spatial_join_forbidden"] is True
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "out.json"
        path.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
        assert json.loads(path.read_text(encoding="utf-8"))["parcel_rows_bound"] == 0
    print("SELF_TEST_PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.fixture or not args.output:
        parser.error("--fixture and --output are required")
    payload = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    result = validate_fixture(payload)
    Path(args.output).write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    print("NO_DATA_CONTINUE")


if __name__ == "__main__":
    main()

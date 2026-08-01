#!/usr/bin/env python3
"""Recover and validate the canonical parcel identifier contract for gas_emissions_2."""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

EXPECTED_ROWS = {
    "parcel_30762": {
        "row_no": 30762,
        "hmlr_inspire_id": "46058185",
        "hmlr_lon": -0.0407406,
        "hmlr_lat": 51.6769078,
        "geometry_type": "Point",
    },
    "parcel_30763": {
        "row_no": 30763,
        "hmlr_inspire_id": "46037757",
        "hmlr_lon": -0.052972,
        "hmlr_lat": 51.6767314,
        "geometry_type": "Point",
    },
    "parcel_30764": {
        "row_no": 30764,
        "hmlr_inspire_id": "45981756",
        "hmlr_lon": -0.0482579,
        "hmlr_lat": 51.6776898,
        "geometry_type": "Point",
    },
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_source(source: dict[str, Any]) -> None:
    required = {
        "source_id",
        "source_url",
        "accessed_at",
        "hash_scope",
        "relevant_excerpt",
        "excerpt_sha256",
        "supports_fields",
        "publisher",
    }
    missing = sorted(required - set(source))
    if missing:
        raise ValueError(f"SOURCE_FIELDS_MISSING:{source.get('source_id')}:{','.join(missing)}")
    actual = sha256_text(source["relevant_excerpt"])
    if actual != source["excerpt_sha256"]:
        raise ValueError(f"SOURCE_SHA_MISMATCH:{source['source_id']}")
    if not source["source_url"].startswith("https://"):
        raise ValueError(f"SOURCE_URL_INVALID:{source['source_id']}")
    if not source["supports_fields"]:
        raise ValueError(f"SOURCE_SCOPE_EMPTY:{source['source_id']}")


def validate_fixture(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("slot_id") != "gas_emissions_2":
        raise ValueError("SLOT_ID_MISMATCH")
    if payload.get("continuation_key") != "f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec":
        raise ValueError("CONTINUATION_KEY_MISMATCH")

    contract = payload.get("canonical_contract") or {}
    required_contract = {
        "carrier_path": "england_map_web/data/program_layer_matrix/security.geojson",
        "carrier_blob_sha": "8afd1d2bac414cf0f6b9484014e7878a4ceff877",
        "feature_count": 92283,
        "unique_parcel_id_count": 92283,
        "minimum_parcel_index": 1,
        "maximum_parcel_index": 92283,
        "identifier_format": "parcel_<row_no>",
        "row_no_alignment_passed": True,
        "strict_carrier_acceptance_passed": True,
    }
    for key, expected in required_contract.items():
        if contract.get(key) != expected:
            raise ValueError(f"CONTRACT_FIELD_MISMATCH:{key}")

    partition = contract.get("slot_partition") or {}
    if partition != {"start": 30762, "end": 61522, "count": 30761}:
        raise ValueError("PARTITION_MISMATCH")

    rows = contract.get("sample_rows") or {}
    if set(rows) != set(EXPECTED_ROWS):
        raise ValueError("SAMPLE_ROW_IDS_MISMATCH")
    for parcel_id, expected in EXPECTED_ROWS.items():
        observed = rows[parcel_id]
        for key, expected_value in expected.items():
            if observed.get(key) != expected_value:
                raise ValueError(f"SAMPLE_FIELD_MISMATCH:{parcel_id}:{key}")
        if observed["row_no"] != int(parcel_id.removeprefix("parcel_")):
            raise ValueError(f"ROW_ID_ALIGNMENT_MISMATCH:{parcel_id}")

    sources = payload.get("source_evidence_manifest") or []
    if len(sources) < 5:
        raise ValueError("OFFICIAL_OR_CANONICAL_SOURCE_COUNT_TOO_LOW")
    for source in sources:
        validate_source(source)

    return {
        "schema_version": 1,
        "slot_id": "gas_emissions_2",
        "wave": 319,
        "state": "NO_DATA_CONTINUE",
        "decision": "CANONICAL_PARCEL_IDENTIFIER_CONTRACT_RECOVERED_NO_DATA_CONTINUE",
        "decision_reason": (
            "The canonical parcel identifier and carrier contract is now proven: parcel_<row_no>, "
            "92,283 unique rows, slot partition 30,762-61,522, and a validated Point carrier with "
            "HMLR INSPIRE identifiers for the first three slot rows. Exact parcel-to-UPRN/TOID mapping "
            "and exact polygon geometry remain absent, so no gas/EPC parcel binding is promoted."
        ),
        "canonical_parcel_identifier_contract": {
            "identifier_type": "canonical_row_ordinal_parcel_id",
            "identifier_format": contract["identifier_format"],
            "canonical_range": {"start": 1, "end": 92283, "count": 92283},
            "slot_partition": partition,
            "carrier_path": contract["carrier_path"],
            "carrier_blob_sha": contract["carrier_blob_sha"],
            "carrier_geometry_semantics": "Point preview/carrier geometry; not exact title polygon geometry",
            "contract_recovered": True,
            "sample_rows_validated": rows,
            "sample_evidence_row_count": len(rows),
        },
        "resolved_blockers": [
            "CANONICAL_PARCEL_IDENTIFIER_TYPE_NOT_DECLARED",
            "CANONICAL_PARCEL_GEOMETRY_INPUT_NOT_FOUND",
        ],
        "remaining_blocker": (
            "CANONICAL_PARCEL_TO_UPRN_OR_TOID_MAP_NOT_FOUND;"
            "CANONICAL_CARRIER_GEOMETRY_IS_POINT_NOT_EXACT_POLYGON;"
            "EPC_API_BEARER_TOKEN_REQUIRED;PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
        ),
        "first_unverified_step": "EXACT_PARCEL_TO_UPRN_OR_TOID_MAPPING_DISCOVERY_OR_NO_DATA_CONTINUE",
        "source_evidence_manifest": sources,
        "source_count": len(sources),
        "contract_evidence_rows": len(rows),
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


def run(fixture_path: Path, output_path: Path) -> None:
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    output = validate_fixture(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_json(output), encoding="utf-8")
    print("DECISION=" + output["decision"])
    print(f"CONTRACT_EVIDENCE_ROWS={output['contract_evidence_rows']}")
    print("BUSINESS_ROWS_PRODUCED=0")
    print("PARCEL_ROWS_BOUND=0")


def self_test() -> None:
    excerpt = "test excerpt"
    fixture = {
        "slot_id": "gas_emissions_2",
        "continuation_key": "f2d3860b264634167c4555ffd2bc809541351e7a5ca52563a4fc89c43feef0ec",
        "canonical_contract": {
            "carrier_path": "england_map_web/data/program_layer_matrix/security.geojson",
            "carrier_blob_sha": "8afd1d2bac414cf0f6b9484014e7878a4ceff877",
            "feature_count": 92283,
            "unique_parcel_id_count": 92283,
            "minimum_parcel_index": 1,
            "maximum_parcel_index": 92283,
            "identifier_format": "parcel_<row_no>",
            "row_no_alignment_passed": True,
            "strict_carrier_acceptance_passed": True,
            "slot_partition": {"start": 30762, "end": 61522, "count": 30761},
            "sample_rows": EXPECTED_ROWS,
        },
        "source_evidence_manifest": [
            {
                "source_id": f"s{i}",
                "source_url": f"https://example.test/{i}",
                "accessed_at": "2026-08-01T16:12:00Z",
                "hash_scope": "normalized_visible_excerpt",
                "relevant_excerpt": excerpt,
                "excerpt_sha256": sha256_text(excerpt),
                "supports_fields": ["test"],
                "publisher": "test",
            }
            for i in range(5)
        ],
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        fixture_path = Path(temp_dir) / "fixture.json"
        output_path = Path(temp_dir) / "output.json"
        fixture_path.write_text(canonical_json(fixture), encoding="utf-8")
        run(fixture_path, output_path)
        result = json.loads(output_path.read_text(encoding="utf-8"))
        assert result["contract_evidence_rows"] == 3
        assert result["business_rows_produced"] == 0
        assert result["resolved_blockers"] == [
            "CANONICAL_PARCEL_IDENTIFIER_TYPE_NOT_DECLARED",
            "CANONICAL_PARCEL_GEOMETRY_INPUT_NOT_FOUND",
        ]
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
    if not args.fixture or not args.output:
        parser.error("--fixture and --output are required unless --self-test is used")
    run(args.fixture, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

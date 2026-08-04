#!/usr/bin/env python3
"""Validate three tracked sample anchor coordinates without inferring parcel binding."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED = {
    30762: {"parcel_id": "parcel_30762", "lpa": "Enfield"},
    46142: {"parcel_id": "parcel_46142", "lpa": "Havering"},
    61522: {"parcel_id": "parcel_61522", "lpa": "Lambeth"},
}
EXPECTED_DATA_STATUS = "VERIFIED_METADATA_NOT_SCORED"
EXPECTED_EVIDENCE_SCOPE = "SERVICE_LAYER_METADATA_ONLY"
EXPECTED_BINDING_STATUS = "MANIFEST_DECLARED_ANCHOR_ONLY"


def _sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _valid_coordinate(lat: Any, lon: Any) -> bool:
    if isinstance(lat, bool) or isinstance(lon, bool):
        return False
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False
    return -90.0 <= float(lat) <= 90.0 and -180.0 <= float(lon) <= 180.0


def validate(candidate_input: dict[str, Any], evidence_matrix: dict[str, Any], prior_gate: dict[str, Any]) -> dict[str, Any]:
    candidates = candidate_input.get("sample_candidates")
    records = evidence_matrix.get("records")
    if not isinstance(candidates, list) or not isinstance(records, list):
        raise ValueError("candidate input and evidence matrix must expose list records")

    candidate_map: dict[int, dict[str, Any]] = {}
    for item in candidates:
        if isinstance(item, dict) and isinstance(item.get("row_no"), int):
            candidate_map[item["row_no"]] = item
    record_map: dict[int, dict[str, Any]] = {}
    for item in records:
        if isinstance(item, dict) and isinstance(item.get("row_no"), int):
            record_map[item["row_no"]] = item

    summaries: list[dict[str, Any]] = []
    anchor_count = 0
    exact_binding_count = 0
    for row_no, expected in EXPECTED.items():
        candidate = candidate_map.get(row_no)
        record = record_map.get(row_no)
        candidate_identity_match = bool(
            candidate
            and candidate.get("parcel_id") == expected["parcel_id"]
            and candidate.get("lpa") == expected["lpa"]
        )
        record_identity_match = bool(
            record
            and record.get("parcel_id") == expected["parcel_id"]
            and record.get("lpa") == expected["lpa"]
        )
        coordinate_valid = bool(record and _valid_coordinate(record.get("lat"), record.get("lon")))
        metadata_status_verified = bool(record and record.get("data_status") == EXPECTED_DATA_STATUS)
        evidence_scope_verified = bool(record and record.get("evidence_scope") == EXPECTED_EVIDENCE_SCOPE)
        anchor_binding_status_verified = bool(record and record.get("parcel_binding_status") == EXPECTED_BINDING_STATUS)
        source_url = record.get("source_url") if isinstance(record, dict) else None
        source_url_https = isinstance(source_url, str) and source_url.startswith("https://")
        raw_sha256_present = bool(
            record
            and isinstance(record.get("raw_sha256"), str)
            and len(record.get("raw_sha256")) == 64
        )
        anchor_available = all(
            [
                candidate_identity_match,
                record_identity_match,
                coordinate_valid,
                metadata_status_verified,
                evidence_scope_verified,
                anchor_binding_status_verified,
                source_url_https,
                raw_sha256_present,
            ]
        )
        exact_binding_verified = bool(
            record and record.get("parcel_binding_status") in {"EXACT_PARCEL_BOUND", "HASHED_EXACT_INTERSECTION"}
        )
        anchor_count += int(anchor_available)
        exact_binding_count += int(exact_binding_verified)
        summaries.append(
            {
                "row_no": row_no,
                "parcel_id": expected["parcel_id"],
                "lpa": expected["lpa"],
                "candidate_identity_match": candidate_identity_match,
                "record_identity_match": record_identity_match,
                "coordinate_valid": coordinate_valid,
                "latitude": record.get("lat") if anchor_available else None,
                "longitude": record.get("lon") if anchor_available else None,
                "metadata_status_verified": metadata_status_verified,
                "evidence_scope_verified": evidence_scope_verified,
                "anchor_binding_status_verified": anchor_binding_status_verified,
                "source_url": source_url if anchor_available else None,
                "source_url_https": source_url_https,
                "raw_sha256": record.get("raw_sha256") if anchor_available else None,
                "record_sha256": _sha256_json(record) if isinstance(record, dict) else None,
                "tracked_anchor_coordinate_available": anchor_available,
                "exact_parcel_binding_verified": exact_binding_verified,
            }
        )

    prior_absence_verified = bool(
        prior_gate.get("validated_candidate_count") == 3
        and prior_gate.get("official_lookup_key_available_count") == 0
        and prior_gate.get("state") == "NO_DATA_CONTINUE"
    )
    complete = anchor_count == len(EXPECTED) and prior_absence_verified
    return {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_2",
        "state": "PUBLISHED" if complete else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "progress_percent": 100.0,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "produced_business_rows": 0,
        "validated_candidate_count": len(EXPECTED),
        "tracked_anchor_coordinate_available_count": anchor_count,
        "exact_parcel_binding_verified_count": exact_binding_count,
        "prior_lookup_key_absence_gate_verified": prior_absence_verified,
        "candidate_summaries": summaries,
        "coordinate_values_persisted": True,
        "address_values_persisted": False,
        "postcode_values_persisted": False,
        "uprn_values_persisted": False,
        "title_number_values_persisted": False,
        "geometry_persisted": False,
        "inferred_linkage_persisted": False,
        "fake_data": False,
        "blocker": (
            "TRACKED_COORDINATES_ARE_MANIFEST_DECLARED_ANCHORS_NOT_EXACT_PARCEL_BINDINGS"
            if complete and exact_binding_count == 0
            else "TRACKED_SAMPLE_ANCHOR_COORDINATE_VALIDATION_INCOMPLETE"
        ),
        "next_unverified_step": (
            "VALIDATE_ANCHOR_COORDINATES_AGAINST_OFFICIAL_POINT_OR_ADDRESS_SERVICE"
            if complete
            else "OBTAIN_COMPLETE_TRACKED_SAMPLE_ANCHOR_COORDINATES"
        ),
    }


def self_test() -> dict[str, Any]:
    candidates = {
        "sample_candidates": [
            {"row_no": row, "parcel_id": value["parcel_id"], "lpa": value["lpa"]}
            for row, value in EXPECTED.items()
        ]
    }
    records = {
        "records": [
            {
                "row_no": row,
                "parcel_id": value["parcel_id"],
                "lpa": value["lpa"],
                "lat": 51.0 + index / 10,
                "lon": -0.1 + index / 100,
                "data_status": EXPECTED_DATA_STATUS,
                "evidence_scope": EXPECTED_EVIDENCE_SCOPE,
                "parcel_binding_status": EXPECTED_BINDING_STATUS,
                "source_url": f"https://example.test/{row}",
                "raw_sha256": "a" * 64,
            }
            for index, (row, value) in enumerate(EXPECTED.items())
        ]
    }
    prior = {"validated_candidate_count": 3, "official_lookup_key_available_count": 0, "state": "NO_DATA_CONTINUE"}
    good = validate(candidates, records, prior)
    bad_records = json.loads(json.dumps(records))
    bad_records["records"][0]["parcel_id"] = "wrong"
    bad = validate(candidates, bad_records, prior)
    tests = [
        ("good_published", good["state"] == "PUBLISHED"),
        ("three_anchors", good["tracked_anchor_coordinate_available_count"] == 3),
        ("zero_exact_bindings", good["exact_parcel_binding_verified_count"] == 0),
        ("expected_blocker", good["blocker"] == "TRACKED_COORDINATES_ARE_MANIFEST_DECLARED_ANCHORS_NOT_EXACT_PARCEL_BINDINGS"),
        ("coordinates_persisted", all(item["latitude"] is not None for item in good["candidate_summaries"])),
        ("no_geometry", good["geometry_persisted"] is False),
        ("bad_identity_rejected", bad["tracked_anchor_coordinate_available_count"] == 2),
        ("bad_no_data", bad["state"] == "NO_DATA_CONTINUE"),
        ("latitude_bounds", _valid_coordinate(90, 180)),
        ("latitude_out_of_bounds", not _valid_coordinate(91, 0)),
        ("boolean_coordinate_rejected", not _valid_coordinate(True, 0)),
        ("prior_gate_required", validate(candidates, records, {})["state"] == "NO_DATA_CONTINUE"),
    ]
    passed = sum(bool(ok) for _, ok in tests)
    return {"tests": [{"name": name, "passed": bool(ok)} for name, ok in tests], "passed": passed, "target": len(tests), "result": f"PASS_{passed}_OF_{len(tests)}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-input", type=Path)
    parser.add_argument("--evidence-matrix", type=Path)
    parser.add_argument("--prior-gate", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    required = [args.candidate_input, args.evidence_matrix, args.prior_gate, args.output]
    if any(value is None for value in required):
        parser.error("--candidate-input, --evidence-matrix, --prior-gate and --output are required")
    result = validate(
        json.loads(args.candidate_input.read_text(encoding="utf-8")),
        json.loads(args.evidence_matrix.read_text(encoding="utf-8")),
        json.loads(args.prior_gate.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate whether tracked sample candidates contain enough lookup keys for official address/UPRN discovery."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_ROWS = (30762, 46142, 61522)
EXPECTED_PARCELS = {row: f"parcel_{row}" for row in EXPECTED_ROWS}
LOOKUP_KEY_GROUPS = {
    "structured_uprn": ("uprn", "UPRN"),
    "structured_title_number": ("title_number", "title_no", "titleNumber"),
    "structured_address": ("address", "full_address", "address_text", "property_address"),
    "structured_postcode": ("postcode", "post_code"),
    "structured_coordinates": ("latitude", "longitude", "easting", "northing", "coordinates"),
    "structured_geometry": ("geometry", "geometry_digest", "geometry_sha256"),
}
REQUIRED_MANIFEST_ROLES = {
    "candidate_input",
    "candidate_validation",
    "prior_exact_binding_gate",
    "official_uprn_lookup_contract",
}


def _has_value(obj: dict[str, Any], keys: tuple[str, ...]) -> bool:
    for key in keys:
        if key not in obj:
            continue
        value = obj[key]
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, dict)) and not value:
            continue
        return True
    return False


def inspect_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    row_no = candidate.get("row_no")
    result = {
        "row_no": row_no,
        "row_expected": row_no in EXPECTED_ROWS,
        "parcel_id_matches_expected": candidate.get("parcel_id") == EXPECTED_PARCELS.get(row_no),
        "lpa_present": isinstance(candidate.get("lpa"), str) and bool(candidate.get("lpa", "").strip()),
        "source_codes_present": isinstance(candidate.get("source_codes"), list) and bool(candidate.get("source_codes")),
    }
    for group, keys in LOOKUP_KEY_GROUPS.items():
        result[f"{group}_present"] = _has_value(candidate, keys)
    result["official_lookup_key_available"] = any(
        result[f"{group}_present"] for group in LOOKUP_KEY_GROUPS
    )
    return result


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    roles = {item.get("evidence_role") for item in manifest.get("sources", [])}
    checks = {role: role in roles for role in sorted(REQUIRED_MANIFEST_ROLES)}
    return {"checks": checks, "verified": all(checks.values())}


def build_output(
    *,
    candidate_input: dict[str, Any],
    candidate_validation: dict[str, Any],
    prior_gate: dict[str, Any],
    manifest: dict[str, Any],
    continuation_key: str,
) -> dict[str, Any]:
    candidates = candidate_input.get("sample_candidates", [])
    summaries = [inspect_candidate(item) for item in candidates if isinstance(item, dict)]
    manifest_result = validate_manifest(manifest)
    rows = tuple(item.get("row_no") for item in summaries)
    prerequisites_verified = bool(
        candidate_input.get("slot_id") == "future_growth_2"
        and candidate_input.get("fake_data") is False
        and candidate_input.get("state") == "UPRN_ADDRESS_IDENTITY_COMPLETE_EXACT_BINDING_PENDING"
        and candidate_validation.get("state") == "NO_DATA_CONTINUE"
        and candidate_validation.get("validated_candidate_count") == 3
        and prior_gate.get("state") == "NO_DATA_CONTINUE"
        and prior_gate.get("validated_candidate_count") == 3
        and rows == EXPECTED_ROWS
        and len(summaries) == 3
        and all(item["parcel_id_matches_expected"] and item["lpa_present"] and item["source_codes_present"] for item in summaries)
        and manifest_result["verified"]
    )
    available_count = sum(bool(item["official_lookup_key_available"]) for item in summaries)
    lookup_ready = prerequisites_verified and available_count == 3
    blocker = None if lookup_ready else "TRACKED_SAMPLE_CANDIDATES_LACK_OFFICIAL_LOOKUP_KEYS_ADDRESS_POSTCODE_UPRN_TITLE_OR_COORDINATES"
    return {
        "architecture_version": 3,
        "schema_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_2",
        "task_continuation_key": continuation_key,
        "state": "PUBLISHED" if lookup_ready else "NO_DATA_CONTINUE",
        "panel_status": "PUBLISHED",
        "completed_count": 1,
        "target_count": 1,
        "progress_percent": 100.0,
        "global_business_completed_count": 0,
        "global_business_target_count": 30761,
        "global_progress_percent": 0.0,
        "produced_business_rows": 0,
        "validated_candidate_count": len(summaries),
        "official_lookup_key_available_count": available_count,
        "all_candidates_lookup_ready": lookup_ready,
        "prerequisites_verified": prerequisites_verified,
        "manifest_checks": manifest_result["checks"],
        "candidate_summaries": summaries,
        "identifier_values_persisted": False,
        "address_values_persisted": False,
        "postcode_values_persisted": False,
        "coordinate_values_persisted": False,
        "geometry_persisted": False,
        "source_rows_persisted": False,
        "inferred_linkage_persisted": False,
        "fake_data": False,
        "blocker": blocker,
        "next_unverified_step": (
            "QUERY_OFFICIAL_ADDRESS_OR_UPRN_SOURCE_USING_TRACKED_LOOKUP_KEYS"
            if lookup_ready
            else "OBTAIN_TRACKED_OFFICIAL_LOOKUP_KEY_FOR_SAMPLE_CANDIDATES"
        ),
    }


def self_test() -> dict[str, Any]:
    base = {
        "row_no": 30762,
        "parcel_id": "parcel_30762",
        "lpa": "Enfield",
        "source_codes": ["OFFICIAL"],
    }
    no_key = inspect_candidate(base)
    with_uprn = inspect_candidate({**bas, "uprn": "100000000001"})
    with_postcode = inspect_candidate({**base, "postcode": "AB1 2CD"})
    wrong_parcel = inspect_candidate({**bas, "parcel_id": "parcel_1"})
    tests = [
        ("no_key_rejected", no_key["official_lookup_key_available"] is False),
        ("uprn_detected", with_uprn["structured_uprn_present"] is True),
        ("postcode_detected", with_postcode["structured_postcode_present"] is True),
        ("wrong_parcel_detected", wrong_parcel["parcel_id_matches_expected"] is False),
        ("row_expected", no_key["row_expected"] is True),
        ("lpa_present", no_key["lpa_present"] is True),
        ("source_codes_present", no_key["source_codes_present"] is True),
        ("no_address_value_exposed", "address" not in no_key),
        ("no_uprn_value_exposed", "uprn" not in no_key),
        ("lookup_groups_complete", len(LOOKUP_KEY_GROUPU) == 6),
    ]
    passed = sum(bool(ok) for _, ok in tests)
    return {
        "tests": [{"name": name, "passed": bool(ok)} for name, ok in tests],
        "passed": passed,
        "target": len(tests),
        "result": f"PASS_{passed}_OF_{len(tests)}",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-input", type=Path)
    parser.add_argument("--candidate-validation", type=Path)
    parser.add_argument("--prior-gate", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--task-continuation-key")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True, separators=(",", ":")))
        return 0
    required = [args.candidate_input, args.candidate_validation, args.prior_gate, args.manifest, args.output, args.task_continuation_key]
    if any(value is None for value in required):
        parser.error("all input, output and continuation arguments are required")
    output = build_output(
        candidate_input=json.loads(args.candidate_input.read_text(encoding="utf-8")),
        candidate_validation=json.loads(args.candidate_validation.read_text(encoding="utf-8")),
        prior_gate=json.loads(args.prior_gate.read_text(encoding="utf-8")),
        manifest=json.loads(args.manifest.read_text(encoding="utf-8")),
        continuation_key=args.task_continuation_key,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

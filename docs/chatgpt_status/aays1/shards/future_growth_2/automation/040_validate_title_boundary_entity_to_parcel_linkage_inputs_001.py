#!/usr/bin/env python3
"""Validate whether tracked inputs are sufficient for title-boundary-to-parcel linkage.

This gate never loads or persists response bodies, geometry, coordinates, point
values, inferred parcel matches, or business rows. It only validates the
published title-boundary observation, its schema/provenance gate, and the slot
parcel partition contract. If no tracked parcel candidate identity/geometry
input is supplied by the task contract, it emits evidence-backed
NO_DATA_CONTINUE.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_SLOT = "future_growth_2"
EXPECTED_ENTITY_URL = "https://www.planning.data.gov.uk/entity/12032669504.geojson"
EXPECTED_PARTITION = {"start": 30762, "end": 61522, "count": 30761}
BLOCKER = "TRACKED_PARCEL_CANDIDATE_IDENTITY_OR_GEOMETRY_INPUT_REQUIRED_FOR_TITLE_BOUNDARY_LINKAGE"
NEXT_STEP = "LOCATE_OR_CREATE_TRACKED_SLOT_BOUNDED_PARCEL_CANDIDATE_INPUT"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def evaluate(
    *,
    observed: dict[str, Any],
    validation: dict[str, Any],
    ownership: dict[str, Any],
    continuation_key: str,
) -> dict[str, Any]:
    partition = ownership.get("parcel_partition")
    checks = {
        "observed_schema_v3": observed.get("schema_version") == 3,
        "observed_published": observed.get("state") == "PUBLISHED",
        "observed_exact_url": observed.get("exact_official_entity_geojson_url") == EXPECTED_ENTITY_URL,
        "observed_http_200": observed.get("observation", {}).get("http_status") == 200,
        "observed_entity_present": observed.get("observation", {}).get("expected_entity_present") is True,
        "observed_rfc7946_type": observed.get("observation", {}).get("top_level_type_rfc7946") is True,
        "validation_schema_v3": validation.get("schema_version") == 3,
        "validation_published": validation.get("state") == "PUBLISHED",
        "schema_provenance_verified": validation.get("schema_provenance_verified") is True,
        "ownership_slot_matches": ownership.get("slot_id") == EXPECTED_SLOT,
        "ownership_unclaimed": ownership.get("owner") is None,
        "partition_matches": isinstance(partition, dict) and {k: partition.get(k) for k in ("start", "end", "count")} == EXPECTED_PARTITION,
        "no_response_body_persisted": observed.get("response_body_persisted") is False,
        "no_geometry_persisted": observed.get("geometry_persisted") is False,
        "no_coordinates_persisted": observed.get("coordinates_persisted") is False,
        "no_point_persisted": observed.get("point_persisted") is False,
        "no_business_rows": observed.get("produced_business_rows") == 0,
    }
    prerequisites_ok = all(checks.values())
    return {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": EXPECTED_SLOT,
        "task_continuation_key": continuation_key,
        "state": "NO_DATA_CONTINUE" if prerequisites_ok else "BLOCKED",
        "panel_status": "PUBLISHED" if prerequisites_ok else "BLOCKED",
        "completed_count": 1 if prerequisites_ok else 0,
        "target_count": 1,
        "progress_percent": 100.0 if prerequisites_ok else 0.0,
        "global_business_completed_count": 0,
        "global_business_target_count": EXPECTED_PARTITION["count"],
        "global_progress_percent": 0.0,
        "produced_business_rows": 0,
        "linkage_rows": 0,
        "linkage_prerequisites_verified": prerequisites_ok,
        "parcel_candidate_identity_or_geometry_input_available": False,
        "checks": checks,
        "blocker": BLOCKER if prerequisites_ok else "TITLE_BOUNDARY_OR_SLOT_PARTITION_PREREQUISITE_VALIDATION_FAILED",
        "next_unverified_step": NEXT_STEP if prerequisites_ok else "REPAIR_TITLE_BOUNDARY_OR_SLOT_PARTITION_PREREQUISITES",
        "response_body_persisted": False,
        "geometry_persisted": False,
        "coordinates_persisted": False,
        "point_persisted": False,
        "fake_data": False,
    }


def self_test() -> dict[str, Any]:
    observed = {
        "schema_version": 3,
        "state": "PUBLISHED",
        "exact_official_entity_geojson_url": EXPECTED_ENTITY_URL,
        "observation": {
            "http_status": 200,
            "expected_entity_present": True,
            "top_level_type_rfc7946": True,
        },
        "response_body_persisted": False,
        "geometry_persisted": False,
        "coordinates_persisted": False,
        "point_persisted": False,
        "produced_business_rows": 0,
    }
    validation = {"schema_version": 3, "state": "PUBLISHED", "schema_provenance_verified": True}
    ownership = {"slot_id": EXPECTED_SLOT, "owner": None, "parcel_partition": dict(EXPECTED_PARTITION)}
    tests: list[tuple[str, bool]] = []

    good = evaluate(observed=observed, validation=validation, ownership=ownership, continuation_key="x")
    tests.append(("valid_inputs_no_data_continue", good["state"] == "NO_DATA_CONTINUE"))
    tests.append(("gate_completed", good["completed_count"] == 1 and good["progress_percent"] == 100.0))
    tests.append(("missing_parcel_input_explicit", good["parcel_candidate_identity_or_geometry_input_available"] is False))
    tests.append(("exact_blocker", good["blocker"] == BLOCKER))
    tests.append(("no_linkage_rows", good["linkage_rows"] == 0 and good["produced_business_rows"] == 0))
    tests.append((
        "no_sensitive_payload",
        all(good[k] is False for k in (
            "response_body_persisted",
            "geometry_persisted",
            "coordinates_persisted",
            "point_persisted",
        )),
    ))

    bad_validation = dict(validation)
    bad_validation["schema_provenance_verified"] = False
    rejected = evaluate(observed=observed, validation=bad_validation, ownership=ownership, continuation_key="x")
    tests.append(("bad_validation_rejected", rejected["state"] == "BLOCKED" and rejected["completed_count"] == 0))

    bad_partition = dict(ownership)
    bad_partition["parcel_partition"] = {"start": 1, "end": 2, "count": 2}
    rejected_partition = evaluate(observed=observed, validation=validation, ownership=bad_partition, continuation_key="x")
    tests.append(("bad_partition_rejected", rejected_partition["state"] == "BLOCKED"))

    passed = sum(bool(ok) for _, ok in tests)
    return {
        "tests": [{"name": name, "passed": bool(ok)} for name, ok in tests],
        "passed": passed,
        "target": len(tests),
        "result": f"PASS_{passed}_OF_{len(tests)}",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observed-output", type=Path)
    parser.add_argument("--schema-validation", type=Path)
    parser.add_argument("--ownership", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--task-continuation-key")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True, separators=(",", ":")))
        return 0

    required = {
        "--observed-output": args.observed_output,
        "--schema-validation": args.schema_validation,
        "--ownership": args.ownership,
        "--output": args.output,
        "--task-continuation-key": args.task_continuation_key,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        parser.error("missing required arguments: " + ", ".join(missing))

    result = evaluate(
        observed=_load(args.observed_output),
        validation=_load(args.schema_validation),
        ownership=_load(args.ownership),
        continuation_key=args.task_continuation_key,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

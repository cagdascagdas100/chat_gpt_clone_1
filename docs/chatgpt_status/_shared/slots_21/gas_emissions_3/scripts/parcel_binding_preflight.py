#!/usr/bin/env python3
"""Fail-closed parcel-binding eligibility preflight for gas_emissions_3.

The script never infers a parcel identity from free-text location labels. A row is
eligible only when the input schema contains an explicit parcel locator field.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXACT_LOCATOR_FIELDS = {
    "parcel_id",
    "security_parcel_id",
    "uprn",
    "postcode",
    "address",
    "latitude",
    "longitude",
    "geometry",
}
REQUIRED_FIELDS = {
    "subject",
    "location",
    "measure",
    "value",
    "unit",
    "qualifier",
    "comparison",
    "period",
    "source",
    "scope_result",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-slot", default="gas_emissions_3")
    parser.add_argument("--expected-batch", default=254, type=int)
    parser.add_argument("--expected-candidates", default=50, type=int)
    parser.add_argument("--expected-normalized-sha256", required=True)
    return parser.parse_args()


def decode(record: list[Any], field: str, field_index: dict[str, int], dictionaries: dict[str, list[Any]]) -> Any:
    value = record[field_index[field]]
    if field == "value":
        return value
    return dictionaries[field][value]


def main() -> int:
    args = parse_args()
    raw = args.input.read_bytes()
    input_sha256 = hashlib.sha256(raw).hexdigest()
    data = json.loads(raw)

    if data.get("slot_id") != args.expected_slot:
        raise ValueError(f"unexpected slot_id: {data.get('slot_id')!r}")
    if data.get("batch") != args.expected_batch:
        raise ValueError(f"unexpected batch: {data.get('batch')!r}")

    field_order = data.get("field_order")
    if not isinstance(field_order, list) or set(field_order) != REQUIRED_FIELDS:
        raise ValueError("candidate field_order does not match the bounded batch-254 schema")

    records = data.get("records")
    if not isinstance(records, list) or len(records) != args.expected_candidates:
        raise ValueError(f"expected {args.expected_candidates} candidates, found {len(records) if isinstance(records, list) else 'non-list'}")
    if data.get("expected_candidate_rows") != args.expected_candidates:
        raise ValueError("expected_candidate_rows mismatch")
    if data.get("normalized_expanded_rows_sha256") != args.expected_normalized_sha256:
        raise ValueError("normalized row SHA-256 mismatch")

    dictionaries = data.get("dictionaries")
    if not isinstance(dictionaries, dict):
        raise ValueError("missing dictionaries")
    field_index = {name: idx for idx, name in enumerate(field_order)}
    explicit_locator_fields = sorted(set(field_order) & EXACT_LOCATOR_FIELDS)

    classifications = []
    for rank0, record in enumerate(records):
        if not isinstance(record, list) or len(record) != len(field_order):
            raise ValueError(f"record {rank0 + 1} has invalid field count")
        classifications.append(
            {
                "rank": rank0 + 1,
                "subject": decode(record, "subject", field_index, dictionaries),
                "location": decode(record, "location", field_index, dictionaries),
                "source_id": decode(record, "source", field_index, dictionaries),
                "scope_result": decode(record, "scope_result", field_index, dictionaries),
                "binding_state": "NO_DATA_EXACT_PARCEL_LOCATOR_ABSENT",
            }
        )

    exact_locator_rows = len(records) if explicit_locator_fields else 0
    no_data_rows = len(records) - exact_locator_rows
    state = "READY_FOR_EXACT_BINDING" if exact_locator_rows else "NO_DATA_CONTINUE"

    output = {
        "schema_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": args.expected_slot,
        "batch": args.expected_batch,
        "state": state,
        "result": "PASS_FAIL_CLOSED",
        "first_unverified_step_completed": "PARCEL_BINDING_SEPARATE_GATE_BATCH_254_PREFLIGHT",
        "next_unverified_step": "DISCOVER_EXACT_SITE_LOCATORS_FOR_PARCEL_BINDABLE_GAS_EMISSIONS_CANDIDATES",
        "input": {
            "path": args.input.as_posix(),
            "content_sha256": input_sha256,
            "normalized_expanded_rows_sha256": data["normalized_expanded_rows_sha256"],
            "field_order": field_order,
            "explicit_locator_fields": explicit_locator_fields,
        },
        "counts": {
            "completed_count": len(records),
            "target_count": args.expected_candidates,
            "candidate_rows": len(records),
            "exact_locator_rows": exact_locator_rows,
            "no_data_rows": no_data_rows,
            "produced_parcel_bindings": 0,
            "produced_evidence_records": len(classifications),
        },
        "decision": {
            "parcel_binding_gate_passed": bool(exact_locator_rows),
            "reason": "EXPLICIT_PARCEL_LOCATOR_FIELDS_ABSENT" if not exact_locator_rows else "EXPLICIT_LOCATOR_FIELDS_PRESENT",
            "free_text_location_not_used_as_property_identity": True,
            "inferred_values": 0,
            "fake_data": False,
        },
        "classifications": classifications,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    tmp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

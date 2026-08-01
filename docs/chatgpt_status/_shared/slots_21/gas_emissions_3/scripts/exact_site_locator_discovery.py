#!/usr/bin/env python3
"""Fail-closed exact site-locator discovery for gas_emissions_3 batch 256.

This script binds only source-explicit site addresses or depicted-place coordinates.
It does not infer parcel identity, geometry, ownership, or emissions attribution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_CANDIDATE_FIELDS = {
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
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-slot", default="gas_emissions_3")
    parser.add_argument("--expected-batch", default=254, type=int)
    parser.add_argument("--expected-candidates", default=50, type=int)
    parser.add_argument("--expected-normalized-sha256", required=True)
    parser.add_argument("--expected-target-count", default=3, type=int)
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def decode(record: list[Any], field: str, field_index: dict[str, int], dictionaries: dict[str, list[Any]]) -> Any:
    raw = record[field_index[field]]
    if field == "value":
        return raw
    values = dictionaries.get(field)
    if not isinstance(values, list) or not isinstance(raw, int) or raw < 0 or raw >= len(values):
        raise ValueError(f"invalid dictionary index for {field}")
    return values[raw]


def validate_source(source: dict[str, Any]) -> None:
    required = {
        "source_id",
        "source_url",
        "accessed_at",
        "source_kind",
        "license_or_terms_url",
        "evidence_excerpt",
        "evidence_excerpt_sha256",
        "hash_scope",
        "supports_fields",
        "relevant_record_scope",
    }
    missing = sorted(required - set(source))
    if missing:
        raise ValueError(f"source evidence missing fields: {missing}")
    excerpt = source["evidence_excerpt"]
    if not isinstance(excerpt, str) or not excerpt.strip():
        raise ValueError("empty evidence excerpt")
    if sha256_text(excerpt) != source["evidence_excerpt_sha256"]:
        raise ValueError(f"evidence excerpt SHA mismatch for {source['source_id']}")
    if source["hash_scope"] != "exact evidence_excerpt UTF-8 bytes":
        raise ValueError("unsupported hash scope")
    if source["source_kind"] not in {"official", "open_geotag"}:
        raise ValueError("unsupported source kind")
    if not isinstance(source["supports_fields"], list) or not source["supports_fields"]:
        raise ValueError("supports_fields must be non-empty")
    if not isinstance(source["relevant_record_scope"], dict):
        raise ValueError("relevant_record_scope must be an object")


def main() -> int:
    args = parse_args()
    input_bytes = args.input.read_bytes()
    manifest_bytes = args.manifest.read_bytes()
    data = json.loads(input_bytes)
    manifest = json.loads(manifest_bytes)

    if data.get("slot_id") != args.expected_slot:
        raise ValueError("unexpected candidate slot")
    if data.get("batch") != args.expected_batch:
        raise ValueError("unexpected candidate batch")
    if data.get("expected_candidate_rows") != args.expected_candidates:
        raise ValueError("candidate row count declaration mismatch")
    records = data.get("records")
    if not isinstance(records, list) or len(records) != args.expected_candidates:
        raise ValueError("candidate record count mismatch")
    field_order = data.get("field_order")
    if not isinstance(field_order, list) or set(field_order) != REQUIRED_CANDIDATE_FIELDS:
        raise ValueError("candidate field_order mismatch")
    if data.get("normalized_expanded_rows_sha256") != args.expected_normalized_sha256:
        raise ValueError("normalized candidate SHA mismatch")
    dictionaries = data.get("dictionaries")
    if not isinstance(dictionaries, dict):
        raise ValueError("candidate dictionaries missing")

    if manifest.get("schema_version") != 3:
        raise ValueError("manifest schema_version must be 3")
    if manifest.get("slot_id") != args.expected_slot or manifest.get("batch") != args.expected_batch:
        raise ValueError("manifest slot/batch mismatch")
    if manifest.get("candidate_normalized_expanded_rows_sha256") != args.expected_normalized_sha256:
        raise ValueError("manifest candidate SHA mismatch")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("manifest sources missing")
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("source evidence entry must be an object")
        validate_source(source)
    sources_by_id = {source["source_id"]: source for source in sources}
    if len(sources_by_id) != len(sources):
        raise ValueError("duplicate source_id")

    bindings = manifest.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != args.expected_target_count:
        raise ValueError("binding target count mismatch")
    field_index = {name: idx for idx, name in enumerate(field_order)}
    produced = []
    unique_sites = set()

    for binding in bindings:
        rank = binding.get("candidate_rank")
        if not isinstance(rank, int) or rank < 1 or rank > len(records):
            raise ValueError("invalid candidate rank")
        record = records[rank - 1]
        if not isinstance(record, list) or len(record) != len(field_order):
            raise ValueError(f"invalid record at rank {rank}")
        subject = decode(record, "subject", field_index, dictionaries)
        location = decode(record, "location", field_index, dictionaries)
        if subject != binding.get("expected_subject"):
            raise ValueError(f"subject mismatch at rank {rank}")
        if location != binding.get("expected_location"):
            raise ValueError(f"location mismatch at rank {rank}")

        source_ids = binding.get("source_ids")
        if not isinstance(source_ids, list) or not source_ids:
            raise ValueError("binding source_ids missing")
        used_sources = []
        for source_id in source_ids:
            source = sources_by_id.get(source_id)
            if source is None:
                raise ValueError(f"unknown source_id {source_id}")
            used_sources.append(source)

        locator = binding.get("exact_site_locator")
        if not isinstance(locator, dict):
            raise ValueError("exact_site_locator missing")
        if not locator.get("site_name"):
            raise ValueError("site_name missing")
        has_address = bool(locator.get("postcode") or locator.get("address_lines"))
        has_coordinates = isinstance(locator.get("latitude"), (int, float)) and isinstance(locator.get("longitude"), (int, float))
        if not (has_address or has_coordinates):
            raise ValueError("locator has neither address nor coordinates")
        if locator.get("locator_scope") not in {"site_address", "site_entrance_depicted_place", "site_depicted_place"}:
            raise ValueError("unsupported locator_scope")
        if locator.get("parcel_geometry_claimed") is not False:
            raise ValueError("parcel geometry must not be claimed")
        if locator.get("inferred_values") != 0 or locator.get("fake_data") is not False:
            raise ValueError("inferred or fake values forbidden")

        if rank == 23 and not any(s["source_kind"] == "official" for s in used_sources):
            raise ValueError("LLWR binding requires official address evidence")
        if has_coordinates and not any(s["source_kind"] == "open_geotag" for s in used_sources):
            raise ValueError("coordinate binding requires open geotag evidence")

        unique_sites.add(locator["site_name"])
        produced.append(
            {
                "candidate_rank": rank,
                "subject": subject,
                "location": location,
                "source_ids": source_ids,
                "binding_state": "EXACT_SITE_LOCATOR_DISCOVERED",
                "exact_site_locator": locator,
            }
        )

    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": args.expected_slot,
        "batch": args.expected_batch,
        "task_batch": 256,
        "state": "EXACT_SITE_LOCATORS_DISCOVERED",
        "result": "PASS_SOURCE_EXPLICIT_SITE_LOCATORS",
        "first_unverified_step_completed": "DISCOVER_EXACT_SITE_LOCATORS_FOR_PARCEL_BINDABLE_GAS_EMISSIONS_CANDIDATES",
        "next_unverified_step": "VALIDATE_SITE_LOCATOR_TO_PARCEL_GEOMETRY",
        "input": {
            "candidate_path": args.input.as_posix(),
            "candidate_content_sha256": sha256_bytes(input_bytes),
            "candidate_normalized_expanded_rows_sha256": data["normalized_expanded_rows_sha256"],
            "manifest_path": args.manifest.as_posix(),
            "manifest_content_sha256": sha256_bytes(manifest_bytes),
        },
        "counts": {
            "completed_count": len(produced),
            "target_count": args.expected_target_count,
            "produced_evidence_records": len(produced),
            "unique_sites": len(unique_sites),
            "address_locator_rows": sum(bool(x["exact_site_locator"].get("postcode") or x["exact_site_locator"].get("address_lines")) for x in produced),
            "coordinate_locator_rows": sum(isinstance(x["exact_site_locator"].get("latitude"), (int, float)) for x in produced),
            "parcel_geometries": 0,
            "parcel_bindings": 0,
        },
        "decision": {
            "site_locator_discovery_passed": len(produced) == args.expected_target_count,
            "parcel_geometry_claimed": False,
            "parcel_binding_gate_passed": False,
            "inferred_values": 0,
            "fake_data": False,
        },
        "bindings": produced,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    tmp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

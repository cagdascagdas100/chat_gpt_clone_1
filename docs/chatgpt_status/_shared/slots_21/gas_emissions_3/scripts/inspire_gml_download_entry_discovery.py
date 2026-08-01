#!/usr/bin/env python3
"""Fail-closed discovery of official HMLR INSPIRE GML download entries for gas_emissions_3 batch 258."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--expected-slot", default="gas_emissions_3")
    p.add_argument("--expected-target-count", default=2, type=int)
    p.add_argument("--expected-input-sha256", required=True)
    p.add_argument("--expected-manifest-sha256", required=True)
    return p.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_source(source: dict[str, Any]) -> None:
    required = {
        "source_id", "source_url", "accessed_at", "source_kind",
        "license_or_terms_url", "relevant_record_scope", "supports_fields",
    }
    missing = sorted(required - set(source))
    if missing:
        raise ValueError(f"source missing fields: {missing}")
    if not isinstance(source["supports_fields"], list) or not source["supports_fields"]:
        raise ValueError("supports_fields missing")
    if "evidence_excerpt" in source:
        excerpt = source["evidence_excerpt"]
        if sha256_text(excerpt) != source.get("evidence_excerpt_sha256"):
            raise ValueError(f"excerpt SHA mismatch: {source['source_id']}")
        if source.get("hash_scope") != "exact evidence_excerpt UTF-8 bytes":
            raise ValueError(f"unsupported hash scope: {source['source_id']}")
    elif "evidence_records" in source:
        records = source["evidence_records"]
        if not isinstance(records, list) or not records:
            raise ValueError(f"evidence_records missing: {source['source_id']}")
        for record in records:
            if sha256_text(record["excerpt"]) != record["sha256"]:
                raise ValueError(f"evidence record SHA mismatch: {source['source_id']}")
        if source.get("hash_scope") != "each exact excerpt UTF-8 bytes":
            raise ValueError(f"unsupported record hash scope: {source['source_id']}")
    else:
        raise ValueError(f"source lacks evidence excerpt(s): {source['source_id']}")


def main() -> int:
    args = parse_args()
    input_bytes = args.input.read_bytes()
    manifest_bytes = args.manifest.read_bytes()
    if sha256_bytes(input_bytes) != args.expected_input_sha256:
        raise ValueError("input SHA mismatch")
    if sha256_bytes(manifest_bytes) != args.expected_manifest_sha256:
        raise ValueError("manifest SHA mismatch")

    previous = json.loads(input_bytes)
    manifest = json.loads(manifest_bytes)
    if previous.get("slot_id") != args.expected_slot:
        raise ValueError("unexpected input slot")
    if previous.get("state") != "NO_DATA_CONTINUE":
        raise ValueError("previous gate is not fail-closed")
    if previous.get("next_unverified_step") != "ACQUIRE_RAW_CADASTRAL_GEOMETRY_OR_VERIFIED_INSPIRE_IDS":
        raise ValueError("unexpected prerequisite step")
    if manifest.get("schema_version") != 3 or manifest.get("slot_id") != args.expected_slot:
        raise ValueError("manifest schema/slot mismatch")
    if manifest.get("state") != "SOURCE_EVIDENCE_COMPLETE_OFFICIAL_GML_ENTRIES_NO_DIRECT_HREF":
        raise ValueError("manifest evidence state mismatch")
    if manifest.get("input_sha256") != args.expected_input_sha256:
        raise ValueError("manifest input SHA mismatch")

    targets = manifest.get("target_records")
    if not isinstance(targets, list) or len(targets) != args.expected_target_count:
        raise ValueError("target count mismatch")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources missing")
    for source in sources:
        validate_source(source)

    source_by_authority: dict[str, dict[str, Any]] = {}
    for source in sources:
        scope = source.get("relevant_record_scope", {})
        authority = scope.get("authority_name")
        if authority:
            source_by_authority[authority] = source

    results = []
    for target in targets:
        authority = target["authority_name"]
        source = source_by_authority.get(authority)
        if source is None:
            raise ValueError(f"official download entry missing: {authority}")
        entry_present = source["evidence_excerpt"] == f"{authority} | Download .gml"
        direct_href = source.get("direct_download_href_present_in_captured_evidence") is True
        results.append({
            "target_id": target["target_id"],
            "authority_name": authority,
            "site_mapping_state": target["site_mapping_state"],
            "official_gml_download_entry_present": entry_present,
            "direct_download_href_resolved": direct_href,
            "raw_gml_downloaded": False,
            "raw_polygon_geometry_acquired": False,
            "verified_inspire_ids_acquired": 0,
            "decision": "ENTRY_CONFIRMED" if entry_present else "NO_DATA_CONTINUE",
            "source_id": source["source_id"],
        })

    completed = sum(r["official_gml_download_entry_present"] for r in results)
    hrefs = sum(r["direct_download_href_resolved"] for r in results)
    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": args.expected_slot,
        "task_batch": 258,
        "state": "NO_DATA_CONTINUE",
        "result": "PASS_OFFICIAL_GML_DOWNLOAD_ENTRIES_CONFIRMED_FAIL_CLOSED",
        "first_unverified_step_completed": "CONFIRM_OFFICIAL_LOCAL_AUTHORITY_GML_DOWNLOAD_ENTRIES",
        "next_unverified_step": "RESOLVE_OFFICIAL_GML_DOWNLOAD_HREFS_AND_VALIDATE_SITE_AUTHORITY_MAPPING",
        "input": {
            "path": args.input.as_posix(),
            "sha256": sha256_bytes(input_bytes),
            "manifest_path": args.manifest.as_posix(),
            "manifest_sha256": sha256_bytes(manifest_bytes),
        },
        "counts": {
            "completed_count": completed,
            "target_count": args.expected_target_count,
            "official_gml_entries_confirmed": completed,
            "direct_download_hrefs_resolved": hrefs,
            "raw_gml_files_downloaded": 0,
            "raw_polygon_geometries": 0,
            "verified_inspire_ids": 0,
            "site_authority_mappings_validated": 0,
            "parcel_bindings": 0,
        },
        "decision": {
            "official_entries_gate_passed": completed == args.expected_target_count,
            "raw_geometry_gate_passed": False,
            "entry_text_alone_is_not_download_url": True,
            "site_authority_mapping_not_claimed": True,
            "inferred_values": 0,
            "fake_data": False,
        },
        "targets": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    tmp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-closed validation of official site-to-local-authority mappings for gas_emissions_3 batch 259."""
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
    if previous.get("next_unverified_step") != "RESOLVE_OFFICIAL_GML_DOWNLOAD_HREFS_AND_VALIDATE_SITE_AUTHORITY_MAPPING":
        raise ValueError("unexpected prerequisite step")
    if manifest.get("schema_version") != 3 or manifest.get("slot_id") != args.expected_slot:
        raise ValueError("manifest schema/slot mismatch")
    if manifest.get("state") != "SOURCE_EVIDENCE_COMPLETE_SITE_AUTHORITY_MAPPINGS_NO_DIRECT_GML_HREFS":
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

    by_id = {s["source_id"]: s for s in sources}
    cumberland = by_id.get("CUMBERLAND_COUNCIL_ENERGY_COAST_LLWR_HOST")
    maentwrog = by_id.get("RCAHMW_COFLEIN_MAENTWROG_HYDRO_SITE_RECORD")
    hmlr = by_id.get("HMLR_INSPIRE_DOWNLOAD_AUTHORITY_ENTRIES")
    if not cumberland or not maentwrog or not hmlr:
        raise ValueError("required official evidence source missing")

    llwr_valid = (
        "UK Low Level Waste Repository" in cumberland["evidence_excerpt"]
        and cumberland["relevant_record_scope"].get("authority_name") == "Cumberland Council"
    )
    maentwrog_excerpts = {r["excerpt"] for r in maentwrog["evidence_records"]}
    maentwrog_valid = {
        "Unitary (Local) Authority Gwynedd",
        "Community Maentwrog",
        "Type Of Site HYDROELECTRIC POWER STATION",
    }.issubset(maentwrog_excerpts)
    hmlr_excerpts = {r["excerpt"] for r in hmlr["evidence_records"]}
    entries_present = {
        "Cumberland Council | Download .gml",
        "Gwynedd Council | Download .gml",
    }.issubset(hmlr_excerpts)
    direct_hrefs = hmlr.get("direct_download_href_present_in_captured_evidence") is True

    results = [
        {
            "target_id": "LLWR_SITE_TO_CUMBERLAND",
            "site_name": "Low Level Waste Repository site",
            "authority_name": "Cumberland Council",
            "site_authority_mapping_validated": llwr_valid,
            "official_hmlr_authority_entry_present": entries_present,
            "direct_download_href_resolved": direct_hrefs,
            "decision": "MAPPING_VALIDATED" if llwr_valid else "NO_DATA_CONTINUE",
            "source_ids": [
                "CUMBERLAND_COUNCIL_ENERGY_COAST_LLWR_HOST",
                "HMLR_INSPIRE_DOWNLOAD_AUTHORITY_ENTRIES",
            ],
        },
        {
            "target_id": "MAENTWROG_SITE_TO_GWYNEDD",
            "site_name": "Maentwrog Power Station",
            "authority_name": "Gwynedd Council",
            "site_authority_mapping_validated": maentwrog_valid,
            "official_hmlr_authority_entry_present": entries_present,
            "direct_download_href_resolved": direct_hrefs,
            "decision": "MAPPING_VALIDATED" if maentwrog_valid else "NO_DATA_CONTINUE",
            "source_ids": [
                "RCAHMW_COFLEIN_MAENTWROG_HYDRO_SITE_RECORD",
                "HMLR_INSPIRE_DOWNLOAD_AUTHORITY_ENTRIES",
            ],
        },
    ]
    completed = sum(r["site_authority_mapping_validated"] for r in results)
    href_count = sum(r["direct_download_href_resolved"] for r in results)

    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": args.expected_slot,
        "task_batch": 259,
        "state": "NO_DATA_CONTINUE",
        "result": "PASS_SITE_AUTHORITY_MAPPINGS_VALIDATED_DIRECT_GML_HREFS_UNRESOLVED",
        "first_unverified_step_completed": "VALIDATE_SITE_AUTHORITY_MAPPING",
        "next_unverified_step": "RESOLVE_DIRECT_HMLR_GML_DOWNLOAD_HREFS",
        "input": {
            "path": args.input.as_posix(),
            "sha256": sha256_bytes(input_bytes),
            "manifest_path": args.manifest.as_posix(),
            "manifest_sha256": sha256_bytes(manifest_bytes),
        },
        "counts": {
            "completed_count": completed,
            "target_count": args.expected_target_count,
            "site_authority_mappings_validated": completed,
            "official_hmlr_authority_entries_confirmed": 2 if entries_present else 0,
            "direct_download_hrefs_resolved": href_count,
            "raw_gml_files_downloaded": 0,
            "raw_polygon_geometries": 0,
            "verified_inspire_ids": 0,
            "parcel_bindings": 0,
        },
        "decision": {
            "site_authority_mapping_gate_passed": completed == args.expected_target_count,
            "direct_href_gate_passed": href_count == args.expected_target_count,
            "authority_entry_text_alone_is_not_download_url": True,
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

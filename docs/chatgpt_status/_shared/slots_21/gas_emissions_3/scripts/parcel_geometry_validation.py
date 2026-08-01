#!/usr/bin/env python3
"""Fail-closed parcel-geometry evidence validation for gas_emissions_3 batch 257."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--locators", required=True, type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--expected-slot", default="gas_emissions_3")
    p.add_argument("--expected-target-sites", default=2, type=int)
    p.add_argument("--expected-locator-sha256", required=True)
    p.add_argument("--expected-manifest-sha256", required=True)
    return p.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def require_source(source: dict[str, Any]) -> None:
    required = {
        "source_id", "source_url", "accessed_at", "source_kind",
        "license_or_terms_url", "evidence_excerpt",
        "evidence_excerpt_sha256", "hash_scope", "supports_fields",
        "relevant_record_scope", "raw_polygon_vertices_present",
        "land_registry_inspire_id_present",
    }
    missing = sorted(required - set(source))
    if missing:
        raise ValueError(f"source missing fields: {missing}")
    excerpt = source["evidence_excerpt"]
    if not isinstance(excerpt, str) or not excerpt.strip():
        raise ValueError("empty evidence excerpt")
    if sha256_text(excerpt) != source["evidence_excerpt_sha256"]:
        raise ValueError(f"excerpt SHA mismatch: {source['source_id']}")
    if source["hash_scope"] != "exact evidence_excerpt UTF-8 bytes":
        raise ValueError("unsupported hash scope")
    if not isinstance(source["supports_fields"], list) or not source["supports_fields"]:
        raise ValueError("supports_fields missing")
    if not isinstance(source["relevant_record_scope"], dict):
        raise ValueError("relevant_record_scope missing")


def main() -> int:
    args = parse_args()
    locator_bytes = args.locators.read_bytes()
    manifest_bytes = args.manifest.read_bytes()
    if sha256_bytes(locator_bytes) != args.expected_locator_sha256:
        raise ValueError("locator SHA mismatch")
    if sha256_bytes(manifest_bytes) != args.expected_manifest_sha256:
        raise ValueError("manifest SHA mismatch")

    locators = json.loads(locator_bytes)
    manifest = json.loads(manifest_bytes)
    if locators.get("slot_id") != args.expected_slot:
        raise ValueError("unexpected locator slot")
    if locators.get("state") != "EXACT_SITE_LOCATORS_DISCOVERED":
        raise ValueError("locator prerequisite not complete")
    if manifest.get("schema_version") != 3 or manifest.get("slot_id") != args.expected_slot:
        raise ValueError("manifest schema/slot mismatch")
    if manifest.get("state") != "SOURCE_EVIDENCE_COMPLETE_NO_RAW_GEOMETRY":
        raise ValueError("manifest evidence state mismatch")
    if manifest.get("input_locator_sha256") != args.expected_locator_sha256:
        raise ValueError("manifest locator SHA mismatch")

    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources missing")
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("source must be object")
        require_source(source)

    bindings = locators.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        raise ValueError("locator bindings missing")
    sites: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        locator = binding.get("exact_site_locator")
        if not isinstance(locator, dict):
            raise ValueError("exact_site_locator missing")
        site_name = locator.get("site_name")
        if not isinstance(site_name, str) or not site_name:
            raise ValueError("site name missing")
        if locator.get("parcel_geometry_claimed") is not False:
            raise ValueError("upstream parcel geometry claim forbidden")
        sites.setdefault(site_name, locator)
    if len(sites) != args.expected_target_sites:
        raise ValueError("unique site count mismatch")

    site_sources = {
        s.get("relevant_record_scope", {}).get("site_name"): s
        for s in sources
        if s.get("source_kind") == "open_site_geometry_index"
    }
    results = []
    for site_name, locator in sorted(sites.items()):
        source = site_sources.get(site_name)
        if source is None:
            raise ValueError(f"open site geometry index missing for {site_name}")
        raw_vertices = source["raw_polygon_vertices_present"] is True
        inspire_id = source["land_registry_inspire_id_present"] is True
        point_in_polygon = False
        validated = bool(raw_vertices and point_in_polygon)
        results.append({
            "site_name": site_name,
            "locator": {
                "latitude": locator.get("latitude"),
                "longitude": locator.get("longitude"),
                "locator_scope": locator.get("locator_scope"),
            },
            "source_id": source["source_id"],
            "open_geometry_identifier": source["relevant_record_scope"].get("openstreetmap_way_id"),
            "raw_polygon_vertices_present": raw_vertices,
            "land_registry_inspire_id_present": inspire_id,
            "point_in_polygon_validated": point_in_polygon,
            "parcel_geometry_validated": validated,
            "decision": "VALIDATED" if validated else "NO_DATA_CONTINUE",
        })

    geometry_count = sum(r["parcel_geometry_validated"] for r in results)
    output = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": args.expected_slot,
        "task_batch": 257,
        "state": "NO_DATA_CONTINUE" if geometry_count == 0 else "PARCEL_GEOMETRY_VALIDATED",
        "result": "PASS_FAIL_CLOSED_GEOMETRY_EVIDENCE_GATE",
        "first_unverified_step_completed": "VALIDATE_SITE_LOCATOR_TO_PARCEL_GEOMETRY",
        "next_unverified_step": (
            "ACQUIRE_RAW_CADASTRAL_GEOMETRY_OR_VERIFIED_INSPIRE_IDS"
            if geometry_count == 0 else "VALIDATE_PARCEL_BINDING_TO_SOURCE_CLAIM"
        ),
        "input": {
            "locator_path": args.locators.as_posix(),
            "locator_sha256": sha256_bytes(locator_bytes),
            "manifest_path": args.manifest.as_posix(),
            "manifest_sha256": sha256_bytes(manifest_bytes),
        },
        "counts": {
            "completed_count": len(results),
            "target_count": args.expected_target_sites,
            "sites_assessed": len(results),
            "open_site_geometry_ids": sum(r["open_geometry_identifier"] is not None for r in results),
            "raw_polygon_geometries": sum(r["raw_polygon_vertices_present"] for r in results),
            "land_registry_inspire_ids": sum(r["land_registry_inspire_id_present"] for r in results),
            "point_in_polygon_validations": sum(r["point_in_polygon_validated"] for r in results),
            "parcel_geometries_validated": geometry_count,
            "parcel_bindings": 0,
        },
        "decision": {
            "parcel_geometry_gate_passed": geometry_count == args.expected_target_sites,
            "open_site_way_id_alone_is_not_parcel_geometry": True,
            "centroid_alone_is_not_geometry": True,
            "inferred_values": 0,
            "fake_data": False,
        },
        "sites": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    tmp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

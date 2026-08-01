#!/usr/bin/env python3
"""Validate the canonical AAYS parcel matrix and future_growth_3 partition.

This script is deliberately fail-closed: it writes only compact validation and
source-evidence manifests. It never writes inferred future-growth scores or a
large shard export.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_CANONICAL = "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
DEFAULT_REGISTRY = "england_map_web/data/aays_21_slots/future_growth_3/source_geometry_registry_latest.json"
DEFAULT_PREFLIGHT = "england_map_web/data/aays_21_slots/future_growth_3/canonical_partition_preflight_latest.json"
DEFAULT_EVIDENCE = "england_map_web/data/aays_21_slots/future_growth_3/source_evidence_manifest_latest.json"
ALLOWED_OUTPUT_ROOT = Path("england_map_web/data/aays_21_slots/future_growth_3")

OFFICIAL_SOURCE_URL = (
    "https://www.planning.data.gov.uk/entity.json?dataset=brownfield-land&"
    "geometry_entity=626195&geometry_relation=within&limit=100"
)
OFFICIAL_LICENSE_URL = "https://www.planning.data.gov.uk/terms-and-conditions"
OFFICIAL_PROJECTION = {
    "dataset": "brownfield-land",
    "end-date": "2019-12-20",
    "entity": 1705636,
    "name": "BLR001",
    "point": "POINT (-0.109462 51.460578)",
    "quality": "authoritative",
    "reference": "BLR001",
    "start-date": "2017-12-15",
}
OFFICIAL_PROJECTION_SHA256 = "80ff2070149fc705d0b82c51461c2364796cbb13bbc3aed1dde37ed4ff4bde29"
OFFICIAL_ACCESSED_AT = "2026-08-01T13:43:00Z"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_relative(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"path must be repository-relative: {path_text}")
    return path


def ensure_output_allowed(path: Path) -> None:
    try:
        path.relative_to(ALLOWED_OUTPUT_ROOT)
    except ValueError as exc:
        raise ValueError(f"output path outside slot root: {path}") from exc


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def feature_summary(feature: dict[str, Any], ordinal: int) -> dict[str, Any]:
    geometry = feature.get("geometry") or {}
    properties = feature.get("properties") or {}
    preferred_keys = (
        "row_id",
        "parcel_id",
        "id",
        "uprn",
        "title_number",
        "name",
    )
    selected = {key: properties[key] for key in preferred_keys if key in properties}
    return {
        "ordinal": ordinal,
        "feature_id": feature.get("id"),
        "geometry_type": geometry.get("type"),
        "selected_properties": selected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--canonical", default=DEFAULT_CANONICAL)
    parser.add_argument("--registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--preflight-output", default=DEFAULT_PREFLIGHT)
    parser.add_argument("--evidence-output", default=DEFAULT_EVIDENCE)
    parser.add_argument("--expected-total", type=int, default=92283)
    parser.add_argument("--partition-start", type=int, default=61523)
    parser.add_argument("--partition-end", type=int, default=92283)
    parser.add_argument("--expected-eligible-source-geometries", type=int, default=4409)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    canonical_rel = ensure_relative(args.canonical)
    registry_rel = ensure_relative(args.registry)
    preflight_rel = ensure_relative(args.preflight_output)
    evidence_rel = ensure_relative(args.evidence_output)
    ensure_output_allowed(preflight_rel)
    ensure_output_allowed(evidence_rel)

    canonical_path = repo_root / canonical_rel
    registry_path = repo_root / registry_rel
    preflight_path = repo_root / preflight_rel
    evidence_path = repo_root / evidence_rel

    if not canonical_path.is_file():
        raise FileNotFoundError(canonical_rel)
    if not registry_path.is_file():
        raise FileNotFoundError(registry_rel)
    if args.partition_start < 1 or args.partition_end < args.partition_start:
        raise ValueError("invalid inclusive partition bounds")

    canonical = load_json(canonical_path)
    if canonical.get("type") != "FeatureCollection":
        raise ValueError("canonical GeoJSON must be a FeatureCollection")
    features = canonical.get("features")
    if not isinstance(features, list):
        raise ValueError("canonical GeoJSON features must be a list")
    if len(features) != args.expected_total:
        raise ValueError(f"feature count {len(features)} != expected {args.expected_total}")
    if args.partition_end > len(features):
        raise ValueError("partition end exceeds canonical feature count")

    partition = features[args.partition_start - 1 : args.partition_end]
    expected_partition_count = args.partition_end - args.partition_start + 1
    if len(partition) != expected_partition_count:
        raise ValueError("partition count mismatch")

    geometry_types: dict[str, int] = {}
    missing_geometry = 0
    for feature in partition:
        geometry = feature.get("geometry") if isinstance(feature, dict) else None
        geometry_type = geometry.get("type") if isinstance(geometry, dict) else None
        if not geometry_type:
            missing_geometry += 1
            geometry_type = "MISSING"
        geometry_types[geometry_type] = geometry_types.get(geometry_type, 0) + 1
    if missing_geometry:
        raise ValueError(f"partition contains {missing_geometry} missing geometries")

    registry = load_json(registry_path)
    coverage = registry.get("coverage") or {}
    eligible_geometry_count = coverage.get(
        "eligible_rows_with_official_point_polygon_or_council_coordinate"
    )
    if eligible_geometry_count != args.expected_eligible_source_geometries:
        raise ValueError(
            f"eligible source geometry count {eligible_geometry_count} != "
            f"expected {args.expected_eligible_source_geometries}"
        )
    intersections_completed = coverage.get("canonical_parcel_intersections_completed")
    if intersections_completed != 0:
        raise ValueError("preflight expected zero prior canonical intersections")

    sample_ordinals = sorted(
        {
            args.partition_start,
            args.partition_start + expected_partition_count // 2,
            args.partition_end,
        }
    )
    samples = [feature_summary(features[ordinal - 1], ordinal) for ordinal in sample_ordinals]
    canonical_sha256 = sha256_file(canonical_path)
    registry_sha256 = sha256_file(registry_path)

    preflight_payload = {
        "schema_version": 3,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_3",
        "state": "READY_FOR_GEOMETRY_INTERSECTION",
        "panel_status": "BİLGİ TOPLANIYOR",
        "canonical_path": canonical_rel.as_posix(),
        "canonical_sha256": canonical_sha256,
        "canonical_feature_count": len(features),
        "partition": {
            "start": args.partition_start,
            "end": args.partition_end,
            "count": len(partition),
        },
        "partition_geometry_types": geometry_types,
        "sample_features": samples,
        "source_registry_path": registry_rel.as_posix(),
        "source_registry_sha256": registry_sha256,
        "eligible_source_geometry_count": eligible_geometry_count,
        "canonical_intersections_before_task": intersections_completed,
        "produced_business_rows": 0,
        "produced_evidence_records": 2,
        "fake_data": False,
        "next_step": "INTERSECT_ONLY_CURRENT_OFFICIAL_SOURCE_GEOMETRIES_WITH_EXACT_PARTITION_ROWS",
        "blocker": "CANDIDATE_TO_CANONICAL_PARCEL_GEOMETRY_CROSSWALK_NOT_STARTED",
    }
    evidence_payload = {
        "schema_version": 1,
        "slot_id": "future_growth_3",
        "sources": [
            {
                "source_url": OFFICIAL_SOURCE_URL,
                "accessed_at": OFFICIAL_ACCESSED_AT,
                "content_sha256": OFFICIAL_PROJECTION_SHA256,
                "content_sha256_scope": "canonical_json_projection_utf8",
                "supports_fields": sorted(OFFICIAL_PROJECTION.keys()),
                "relevant_record_ids_or_excerpt": OFFICIAL_PROJECTION,
                "license_or_terms_url": OFFICIAL_LICENSE_URL,
            },
            {
                "source_url": f"repo://{canonical_rel.as_posix()}",
                "accessed_at": OFFICIAL_ACCESSED_AT,
                "content_sha256": canonical_sha256,
                "content_sha256_scope": "full_file_bytes",
                "supports_fields": ["geometry", "properties", "feature_ordinal"],
                "relevant_record_ids_or_excerpt": {
                    "feature_count": len(features),
                    "partition_start": args.partition_start,
                    "partition_end": args.partition_end,
                    "sample_ordinals": sample_ordinals,
                },
                "license_or_terms_url": OFFICIAL_LICENSE_URL,
            },
        ],
        "large_raw_files_committed": False,
        "derived_compact_manifests_only": True,
    }

    atomic_write_json(preflight_path, preflight_payload)
    atomic_write_json(evidence_path, evidence_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Exact-point intersection for one fully evidenced official source geometry.

Fail-closed rules:
- only exact coordinate equality is accepted;
- no proximity, parcel assignment, score, or business value is inferred;
- outputs are compact JSON manifests written atomically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

DEFAULT_CANONICAL = "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
DEFAULT_SOURCE_MANIFEST = "england_map_web/data/aays_21_slots/future_growth_3/source_evidence_manifest_latest.json"
DEFAULT_OUTPUT = "england_map_web/data/aays_21_slots/future_growth_3/exact_point_intersection_entity_1705636_latest.json"
DEFAULT_EVIDENCE_OUTPUT = "england_map_web/data/aays_21_slots/future_growth_3/exact_point_intersection_entity_1705636_evidence_latest.json"
ALLOWED_OUTPUT_ROOT = Path("england_map_web/data/aays_21_slots/future_growth_3")
EXPECTED_ENTITY = 1705636
EXPECTED_REFERENCE = "BLR001"
EXPECTED_SOURCE_SHA256 = "80ff2070149fc705d0b82c51461c2364796cbb13bbc3aed1dde37ed4ff4bde29"
EXPECTED_SOURCE_URL = "https://www.planning.data.gov.uk/entity.json?dataset=brownfield-land&geometry_entity=626195&geometry_relation=within&limit=100"
EXPECTED_POINT_WKT = "POINT (-0.109462 51.460578)"
POINT_RE = re.compile(r"^POINT\s*\(\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*\)$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    resolved_parent = path.parent.resolve()
    allowed = ALLOWED_OUTPUT_ROOT.resolve()
    if resolved_parent != allowed:
        raise ValueError(f"write path outside slot boundary: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def parse_point_wkt(value: str) -> tuple[Decimal, Decimal]:
    match = POINT_RE.match(value.strip())
    if not match:
        raise ValueError(f"unsupported point WKT: {value!r}")
    try:
        return Decimal(match.group(1)), Decimal(match.group(2))
    except InvalidOperation as exc:
        raise ValueError(f"invalid point WKT: {value!r}") from exc


def coordinate_pair(geometry: Any) -> tuple[Decimal, Decimal] | None:
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        return None
    coords = geometry.get("coordinates")
    if not isinstance(coords, list) or len(coords) < 2:
        return None
    try:
        return Decimal(str(coords[0])), Decimal(str(coords[1]))
    except InvalidOperation:
        return None


def find_source_record(manifest: dict[str, Any]) -> dict[str, Any]:
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise ValueError("source manifest lacks sources list")
    for source in sources:
        if not isinstance(source, dict):
            continue
        excerpt = source.get("relevant_record_ids_or_excerpt")
        if not isinstance(excerpt, dict):
            continue
        if excerpt.get("entity") == EXPECTED_ENTITY and excerpt.get("reference") == EXPECTED_REFERENCE:
            return source
    raise ValueError("expected official source entity not found")


def run(args: argparse.Namespace) -> dict[str, Any]:
    canonical_path = Path(args.canonical)
    source_manifest_path = Path(args.source_manifest)
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    if canonical.get("type") != "FeatureCollection" or not isinstance(canonical.get("features"), list):
        raise ValueError("canonical input must be a GeoJSON FeatureCollection")
    features = canonical["features"]
    if len(features) != args.canonical_count:
        raise ValueError(f"canonical feature count {len(features)} != {args.canonical_count}")
    if args.partition_start < 1 or args.partition_end < args.partition_start or args.partition_end > len(features):
        raise ValueError("invalid inclusive partition")
    partition = features[args.partition_start - 1 : args.partition_end]
    expected_partition_count = args.partition_end - args.partition_start + 1
    if len(partition) != expected_partition_count:
        raise ValueError("partition count mismatch")

    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source = find_source_record(source_manifest)
    if source.get("source_url") != EXPECTED_SOURCE_URL:
        raise ValueError("official source URL mismatch")
    if source.get("content_sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("official source projection SHA-256 mismatch")
    excerpt = source["relevant_record_ids_or_excerpt"]
    if excerpt.get("point") != EXPECTED_POINT_WKT:
        raise ValueError("official source point mismatch")
    source_point = parse_point_wkt(EXPECTED_POINT_WKT)

    non_point_ordinals: list[int] = []
    matches: list[dict[str, Any]] = []
    for offset, feature in enumerate(partition):
        ordinal = args.partition_start + offset
        geometry = feature.get("geometry") if isinstance(feature, dict) else None
        pair = coordinate_pair(geometry)
        if pair is None:
            non_point_ordinals.append(ordinal)
            continue
        if pair == source_point:
            properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
            matches.append({
                "ordinal": ordinal,
                "feature_id": feature.get("id"),
                "selected_property_keys": sorted(str(key) for key in properties.keys())[:12],
                "geometry_type": "Point",
                "coordinates": [str(pair[0]), str(pair[1])],
            })
    if non_point_ordinals:
        raise ValueError(f"partition contains non-Point or invalid geometry at ordinals: {non_point_ordinals[:10]}")

    state = "EXACT_MATCH_CANDIDATES_FOUND" if matches else "NO_DATA_CONTINUE"
    canonical_sha = sha256_file(canonical_path)
    result = {
        "schema_version": 1,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "future_growth_3",
        "state": state,
        "panel_status": "BİLGİ TOPLANIYOR",
        "method": "EXACT_POINT_COORDINATE_EQUALITY_ONLY",
        "canonical_feature_count": len(features),
        "partition": {"start": args.partition_start, "end": args.partition_end, "count": len(partition)},
        "completed_count": len(partition),
        "target_count": expected_partition_count,
        "progress_percent": round((len(partition) / expected_partition_count) * 100.0, 8),
        "source_entity": EXPECTED_ENTITY,
        "source_reference": EXPECTED_REFERENCE,
        "source_point_wkt": EXPECTED_POINT_WKT,
        "exact_match_count": len(matches),
        "matches": matches,
        "produced_business_rows": 0,
        "future_growth_scores_produced": 0,
        "fake_data": False,
        "no_inference": True,
        "next_step": "REVIEW_EXACT_MATCHES_OR_CONTINUE_WITH_NEXT_EVIDENCED_SOURCE_GEOMETRY",
    }
    evidence = {
        "schema_version": 1,
        "slot_id": "future_growth_3",
        "method": "EXACT_POINT_COORDINATE_EQUALITY_ONLY",
        "canonical_path": args.canonical,
        "canonical_sha256": canonical_sha,
        "source_manifest_path": args.source_manifest,
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "source_url": source["source_url"],
        "accessed_at": source.get("accessed_at"),
        "content_sha256": source["content_sha256"],
        "content_sha256_scope": source.get("content_sha256_scope"),
        "relevant_record_ids_or_excerpt": excerpt,
        "supports_fields": source.get("supports_fields", []),
        "license_or_terms_url": source.get("license_or_terms_url"),
        "record_scope": "one fully evidenced official Point geometry against exact partition ordinals",
        "proven_fields": ["entity", "reference", "point", "dataset", "quality"],
        "exact_match_count": len(matches),
        "state": state,
        "fake_data": False,
    }
    atomic_json_write(Path(args.output), result)
    atomic_json_write(Path(args.evidence_output), evidence)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", default=DEFAULT_CANONICAL)
    parser.add_argument("--source-manifest", default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--evidence-output", default=DEFAULT_EVIDENCE_OUTPUT)
    parser.add_argument("--canonical-count", type=int, default=92283)
    parser.add_argument("--partition-start", type=int, default=61523)
    parser.add_argument("--partition-end", type=int, default=92283)
    parser.add_argument("--validate-only", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.validate_only:
        outputs = [Path(args.output), Path(args.evidence_output)]
        if any(path.parent.resolve() != ALLOWED_OUTPUT_ROOT.resolve() for path in outputs):
            parser.error("output path outside slot boundary")
        if args.partition_start < 1 or args.partition_end < args.partition_start:
            parser.error("invalid partition")
        print(json.dumps({"validation": "PASS", "target_count": args.partition_end - args.partition_start + 1}, sort_keys=True))
        return 0
    result = run(args)
    print(json.dumps({"state": result["state"], "completed_count": result["completed_count"], "target_count": result["target_count"], "exact_match_count": result["exact_match_count"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

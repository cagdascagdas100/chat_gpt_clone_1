#!/usr/bin/env python3
"""Build official parcel-to-brownfield polygon relations for future_growth_1.

The script is fail closed. It requires exactly three canonical parcel seeds,
exact HM Land Registry INSPIRE identifier matches, the parcel point covered by
each matched parcel polygon, and all three current GLA Brownfield polygons.
The stale/completed LBBD23 polygon is optional and is never promoted as active
growth. No Future Growth score or database row is emitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import fiona
from pyproj import CRS, Transformer
from shapely import make_valid
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform as shapely_transform

SLOT_ID = "future_growth_1"
TARGET_CRS = CRS.from_epsg(27700)
WGS84 = CRS.from_epsg(4326)
CURRENT_SITE_REFS = {"LBBD49/XJ", "LBBD72/ZZ", "LBBD91/DI"}
OPTIONAL_STALE_SITE_REFS = {"LBBD23"}
ALLOWED_SITE_REFS = CURRENT_SITE_REFS | OPTIONAL_STALE_SITE_REFS
ID_KEY_RE = re.compile(r"(inspire|cadastral|identifier|local.?id|(^|_)id($|_))", re.I)
VECTOR_SUFFIXES = {".gml", ".xml", ".gpkg", ".geojson", ".json", ".shp"}


def clean(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip()).casefold()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def finite_float(value: Any, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid {field}: {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"non-finite {field}: {value!r}")
    return result


def load_starter(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("starter manifest must contain exactly three candidates")
    transformer = Transformer.from_crs(WGS84, TARGET_CRS, always_xy=True)
    result: list[dict[str, Any]] = []
    seen_rows: set[int] = set()
    seen_ids: set[str] = set()
    for value in rows:
        row = dict(value)
        row_no = int(row.get("row_no"))
        parcel_id = str(row.get("parcel_id") or "").strip()
        inspire_id = str(row.get("hmlr_inspire_id") or "").strip()
        lon = finite_float(row.get("longitude"), "longitude")
        lat = finite_float(row.get("latitude"), "latitude")
        authority = str(row.get("local_authority_name") or "").strip()
        if row_no not in {1, 2, 3} or row_no in seen_rows:
            raise ValueError("starter rows must be unique and exactly within 1..3")
        if not parcel_id or not inspire_id or inspire_id in seen_ids or not authority:
            raise ValueError("starter identity fields are missing or duplicated")
        easting, northing = transformer.transform(lon, lat)
        result.append(
            {
                "row_no": row_no,
                "parcel_id": parcel_id,
                "hmlr_inspire_id": inspire_id,
                "longitude": lon,
                "latitude": lat,
                "bng_easting": float(easting),
                "bng_northing": float(northing),
                "local_authority_name": authority,
            }
        )
        seen_rows.add(row_no)
        seen_ids.add(inspire_id)
    result.sort(key=lambda row: row["row_no"])
    expected = ["39729785", "39724273", "60116682"]
    if [row["hmlr_inspire_id"] for row in result] != expected:
        raise ValueError("canonical first-three HMLR INSPIRE identifiers changed")
    return result


def load_candidate_pairs(path: Path) -> list[dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or len(rows) != 6:
        raise ValueError("candidate JSON must contain exactly six point candidates")
    result: list[dict[str, Any]] = []
    for value in rows:
        row = dict(value)
        reference = str(row.get("source_reference") or "").strip()
        if reference not in ALLOWED_SITE_REFS:
            raise ValueError(f"unexpected site reference: {reference}")
        if row.get("future_growth_score") is not None or bool(row.get("scorable")):
            raise ValueError("input candidate already contains an impermissible score")
        result.append(row)
    current_pairs = sum(1 for row in result if bool(row.get("source_current")))
    stale_pairs = len(result) - current_pairs
    if current_pairs != 5 or stale_pairs != 1:
        raise ValueError("candidate current/stale partition changed")
    return result


def resolve_vectors(explicit: list[Path], roots: list[Path], max_files: int) -> list[Path]:
    paths: list[Path] = []
    for path in explicit:
        if not path.is_file():
            raise FileNotFoundError(path)
        paths.append(path.resolve())
    for root in roots:
        if not root.is_dir():
            raise NotADirectoryError(root)
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in VECTOR_SUFFIXES:
                paths.append(path.resolve())
            if len(paths) > max_files:
                raise ValueError("vector file limit exceeded")
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    if not unique:
        raise ValueError("no HMLR vectors found")
    return unique


def identifier_values(feature: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    feature_id = clean(feature.get("id"))
    if feature_id:
        values.add(feature_id)
    for key, value in dict(feature.get("properties") or {}).items():
        if ID_KEY_RE.search(str(key)) and value not in (None, ""):
            cleaned = clean(value)
            if cleaned:
                values.add(cleaned)
    return values


def exact_hmlr_matches(candidates: list[dict[str, Any]], vector_paths: list[Path]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    states: dict[str, dict[str, Any]] = {
        clean(candidate["hmlr_inspire_id"]): {"candidate": candidate, "matches": []} for candidate in candidates
    }
    sources: list[dict[str, Any]] = []
    for path in vector_paths:
        file_count = 0
        layer_summaries: list[dict[str, Any]] = []
        for layer_name in fiona.listlayers(path):
            with fiona.open(path, layer=layer_name) as collection:
                if not collection.crs and not collection.crs_wkt:
                    raise ValueError(f"missing CRS in {path} layer {layer_name}")
                source_crs = CRS.from_user_input(collection.crs_wkt or collection.crs)
                transformer = None if source_crs == TARGET_CRS else Transformer.from_crs(source_crs, TARGET_CRS, always_xy=True)
                layer_count = 0
                for feature_obj in collection:
                    layer_count += 1
                    file_count += 1
                    feature = dict(feature_obj)
                    matched_ids = set(states) & identifier_values(feature)
                    if not matched_ids or feature.get("geometry") is None:
                        continue
                    geometry = shape(feature["geometry"])
                    if transformer is not None:
                        geometry = shapely_transform(transformer.transform, geometry)
                    if not geometry.is_valid:
                        geometry = make_valid(geometry)
                    if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
                        continue
                    for inspire_id in matched_ids:
                        candidate = states[inspire_id]["candidate"]
                        point = Point(candidate["bng_easting"], candidate["bng_northing"])
                        states[inspire_id]["matches"].append(
                            {
                                "source_path": str(path),
                                "source_layer": layer_name,
                                "source_feature_id": feature.get("id"),
                                "source_crs": source_crs.to_string(),
                                "geometry": geometry,
                                "geometry_type": geometry.geom_type,
                                "geometry_area_m2": round(float(geometry.area), 3),
                                "candidate_point_inside": bool(geometry.covers(point)),
                            }
                        )
                layer_summaries.append({"layer": layer_name, "features": layer_count, "crs": source_crs.to_string()})
        sources.append(
            {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
                "feature_count": file_count,
                "layers": layer_summaries,
            }
        )

    chosen: dict[str, dict[str, Any]] = {}
    for inspire_id, state in states.items():
        matches = state["matches"]
        covering = [record for record in matches if record["candidate_point_inside"]]
        if len(matches) != 1 or len(covering) != 1:
            raise ValueError(
                f"exact HMLR match gate failed for {state['candidate']['hmlr_inspire_id']}: "
                f"matches={len(matches)} covering={len(covering)}"
            )
        chosen[inspire_id] = matches[0]
    return chosen, sources


def load_gla(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    payload = read_json(path)
    features = payload.get("features") if isinstance(payload, dict) else None
    if payload.get("type") != "FeatureCollection" or not isinstance(features, list):
        raise ValueError("GLA input is not a GeoJSON FeatureCollection")
    result: dict[str, dict[str, Any]] = {}
    for feature in features:
        props = dict(feature.get("properties") or {})
        reference = str(props.get("sitereference") or "").strip()
        if reference not in ALLOWED_SITE_REFS or reference in result:
            raise ValueError(f"unexpected or duplicate GLA site reference: {reference!r}")
        geometry = shape(feature.get("geometry"))
        if not geometry.is_valid:
            geometry = make_valid(geometry)
        if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"invalid GLA polygon for {reference}")
        result[reference] = {"properties": props, "geometry_wgs84": geometry}
    missing_current = CURRENT_SITE_REFS - set(result)
    if missing_current:
        raise ValueError(f"missing current GLA polygons: {sorted(missing_current)}")
    return result, {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "feature_count": len(features),
        "current_references_required": sorted(CURRENT_SITE_REFS),
        "current_references_present": sorted(CURRENT_SITE_REFS & set(result)),
        "optional_stale_references_present": sorted(OPTIONAL_STALE_SITE_REFS & set(result)),
        "optional_stale_references_missing": sorted(OPTIONAL_STALE_SITE_REFS - set(result)),
    }


def relation(parcel_bng, site_wgs84) -> dict[str, Any]:
    to_bng = Transformer.from_crs(WGS84, TARGET_CRS, always_xy=True).transform
    site_bng = shapely_transform(to_bng, site_wgs84)
    if not site_bng.is_valid:
        site_bng = make_valid(site_bng)
    if site_bng.is_empty or site_bng.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError("transformed GLA geometry is invalid")
    distance = float(parcel_bng.distance(site_bng))
    intersects = bool(parcel_bng.intersects(site_bng))
    if intersects:
        relation_type, weight, cap = "INTERSECTS_PARCEL", 1.0, "high_if_all_other_factors_pass"
    elif distance <= 250:
        relation_type, weight, cap = "WITHIN_250M", 0.85, "medium_high"
    elif distance <= 500:
        relation_type, weight, cap = "WITHIN_500M", 0.70, "medium"
    elif distance <= 1000:
        relation_type, weight, cap = "WITHIN_1000M", 0.52, "low_medium"
    elif distance <= 2000:
        relation_type, weight, cap = "WITHIN_2000M", 0.35, "low"
    else:
        relation_type, weight, cap = "OUTSIDE_2000M", 0.0, "none"
    return {
        "relation_type": relation_type,
        "polygon_distance_m": round(distance, 3),
        "intersects": intersects,
        "relation_weight_hint": weight,
        "confidence_cap": cap,
        "site_geometry_bng_area_m2": round(float(site_bng.area), 3),
        "parcel_geometry_bng_area_m2": round(float(parcel_bng.area), 3),
    }


def publish(
    starter: list[dict[str, Any]],
    candidate_pairs: list[dict[str, Any]],
    hmlr_matches: dict[str, dict[str, Any]],
    hmlr_sources: list[dict[str, Any]],
    gla: dict[str, dict[str, Any]],
    gla_source: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    parcel_by_id = {clean(row["hmlr_inspire_id"]): row for row in starter}
    to_wgs84 = Transformer.from_crs(TARGET_CRS, WGS84, always_xy=True).transform
    rows: list[dict[str, Any]] = []
    spatial_features: list[dict[str, Any]] = []

    for inspire_id, match in hmlr_matches.items():
        parcel = parcel_by_id[inspire_id]
        parcel_wgs84 = shapely_transform(to_wgs84, match["geometry"])
        spatial_features.append(
            {
                "type": "Feature",
                "geometry": mapping(parcel_wgs84),
                "properties": {
                    "role": "hmlr_parcel_polygon",
                    "row_no": parcel["row_no"],
                    "parcel_id": parcel["parcel_id"],
                    "hmlr_inspire_id": parcel["hmlr_inspire_id"],
                    "source_path": match["source_path"],
                    "source_sha256": next(item["sha256"] for item in hmlr_sources if item["path"] == match["source_path"]),
                },
            }
        )

    for reference, site in gla.items():
        spatial_features.append(
            {
                "type": "Feature",
                "geometry": mapping(site["geometry_wgs84"]),
                "properties": {
                    "role": "gla_brownfield_polygon",
                    "source_reference": reference,
                    "source_current": reference in CURRENT_SITE_REFS,
                    "site_address": site["properties"].get("sitenameaddress"),
                },
            }
        )

    for pair in candidate_pairs:
        inspire_id = clean(pair["hmlr_inspire_id"])
        parcel_match = hmlr_matches[inspire_id]
        reference = str(pair["source_reference"])
        site = gla.get(reference)
        source_current = bool(pair.get("source_current"))
        if source_current and site is None:
            raise ValueError(f"current candidate lacks GLA polygon: {reference}")
        if not source_current:
            rows.append(
                {
                    **pair,
                    "official_entity_state": "STALE_COMPLETED_REJECTED",
                    "site_polygon_verified": site is not None,
                    "parcel_polygon_verified": True,
                    "relation_type": "STALE_COMPLETED_NOT_ACTIVE_GROWTH",
                    "polygon_distance_m": None,
                    "intersects": None,
                    "relation_weight_hint": 0.0,
                    "confidence_cap": "zero_for_active_growth",
                    "future_growth_score": None,
                    "scorable": False,
                    "score_blocker": "STALE_COMPLETED_ENTITY_AND_FULL_FACTOR_MATRIX_NOT_VALIDATED",
                }
            )
            continue
        spatial = relation(parcel_match["geometry"], site["geometry_wgs84"])
        rows.append(
            {
                **pair,
                **spatial,
                "official_entity_state": "CURRENT_AUTHORITATIVE",
                "site_polygon_verified": True,
                "parcel_polygon_verified": True,
                "future_growth_score": None,
                "scorable": False,
                "score_blocker": "FULL_FUTURE_GROWTH_FACTOR_MATRIX_NOT_VALIDATED",
            }
        )

    current_rows = [row for row in rows if row.get("source_current")]
    if len(current_rows) != 5 or not all(row["site_polygon_verified"] and row["parcel_polygon_verified"] for row in current_rows):
        raise ValueError("five current candidate polygon relations were not verified")

    result = {
        "schema_version": 2,
        "architecture_version": 3,
        "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": SLOT_ID,
        "calculation_version": "future_growth_v1",
        "canonical_scope": "LONDON_CANONICAL_92283_NOT_ALL_ENGLAND",
        "parcel_partition": {"start": 1, "end": 30761, "count": 30761, "canonical_count": 92283},
        "matching_method": "EXACT_HMLR_INSPIRE_ID_AND_POINT_INSIDE_THEN_GLA_POLYGON_RELATION",
        "processing_crs": "EPSG:27700",
        "hmlr_sources": hmlr_sources,
        "gla_source": gla_source,
        "counts": {
            "canonical_parcels_sampled": 3,
            "exact_hmlr_parcel_polygons": 3,
            "current_gla_site_polygons": len(CURRENT_SITE_REFS & set(gla)),
            "optional_stale_gla_site_polygons": len(OPTIONAL_STALE_SITE_REFS & set(gla)),
            "candidate_rows": len(rows),
            "current_polygon_relations_verified": len(current_rows),
            "stale_or_completed_rejections": sum(1 for row in rows if not bool(row.get("source_current"))),
            "scored_business_rows": 0,
            "actual_business_data_rows_written": 0,
        },
        "rows": rows,
        "quality_gates": {
            "exact_hmlr_id_match": "3/3",
            "candidate_point_inside_exact_hmlr_polygon": "3/3",
            "current_gla_polygon_readback": "3/3",
            "current_candidate_polygon_relations": "5/5",
            "stale_false_positive_rejected": "1/1",
            "nearest_polygon_fill_used": False,
            "point_only_promotion_used": False,
            "future_growth_score_emitted": "0/30761",
        },
        "first_unverified_step": "BUILD_30761_ROW_FULL_FACTOR_MATRIX_THEN_SCORE_WITH_CONFIDENCE",
        "output_semantics": "VERIFIED_SAMPLE_POLYGON_RELATIONS_NOT_FULL_MATRIX_NOT_SCORE",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    write_json(output_dir / "official_geometry_relations_v2_latest.json", result)
    write_json(output_dir / "official_geometry_relations_v2_latest.geojson", {"type": "FeatureCollection", "features": spatial_features})
    return result


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starter-manifest", type=Path, required=True)
    parser.add_argument("--candidate-json", type=Path, required=True)
    parser.add_argument("--gla-geojson", type=Path, required=True)
    parser.add_argument("--vector", type=Path, action="append", default=[])
    parser.add_argument("--vector-root", type=Path, action="append", default=[])
    parser.add_argument("--max-files", type=int, default=100)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    starter = load_starter(args.starter_manifest)
    pairs = load_candidate_pairs(args.candidate_json)
    vectors = resolve_vectors(args.vector, args.vector_root, args.max_files)
    matches, hmlr_sources = exact_hmlr_matches(starter, vectors)
    gla, gla_source = load_gla(args.gla_geojson)
    result = publish(starter, pairs, matches, hmlr_sources, gla, gla_source, args.output_dir)
    print(
        json.dumps(
            {
                "ok": True,
                "slot_id": SLOT_ID,
                "exact_hmlr_parcel_polygons": result["counts"]["exact_hmlr_parcel_polygons"],
                "current_gla_site_polygons": result["counts"]["current_gla_site_polygons"],
                "current_polygon_relations_verified": result["counts"]["current_polygon_relations_verified"],
                "scored_business_rows": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "slot_id": SLOT_ID, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

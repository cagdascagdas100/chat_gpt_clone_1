#!/usr/bin/env python3
"""Match real parcel candidates to HMLR INSPIRE polygons without nearest fill.

The matcher accepts HMLR GML (or another Fiona-readable vector file) and a
starter candidate manifest. Exact official-identifier equality is preferred;
otherwise a unique EPSG:27700 point-in-polygon match is allowed. Ambiguous or
missing matches remain explicit blockers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

try:
    import fiona
    from pyproj import CRS, Transformer
    from shapely import make_valid
    from shapely.geometry import Point, mapping, shape
    from shapely.ops import transform as shapely_transform
except ImportError as exc:
    raise SystemExit(f"Required geospatial dependency is missing: {exc}")

TARGET_CRS = CRS.from_epsg(27700)
AUTHORITATIVE_HMLR_ID_KEYS = {
    "gmlid",
    "inspireid",
    "nationalcadastralreference",
}
CANDIDATE_ID_FIELDS = (
    "hmlr_inspire_id",
    "national_cadastral_reference",
    "parcel_registry_id",
    "hmlr_title_number",
    "title_number",
    "uprn",
)
VECTOR_SUFFIXES = {".gml", ".gpkg", ".geojson", ".json", ".shp"}


def _clean_id(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip()).casefold()


def _property_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def _file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    values = payload.get("candidates") if isinstance(payload, dict) else payload
    if not isinstance(values, list) or not values:
        raise ValueError("starter manifest must contain a non-empty candidates list")
    result: list[dict[str, Any]] = []
    for index, value in enumerate(values, start=1):
        row = dict(value)
        for field_name in ("row_no", "parcel_id", "bng_easting", "bng_northing"):
            if field_name not in row or str(row[field_name]).strip() == "":
                raise ValueError(f"candidate {index} lacks {field_name}")
        row["row_no"] = int(row["row_no"])
        row["bng_easting"] = float(row["bng_easting"])
        row["bng_northing"] = float(row["bng_northing"])
        if not all(math.isfinite(row[name]) for name in ("bng_easting", "bng_northing")):
            raise ValueError(f"candidate {index} has non-finite BNG coordinates")
        result.append(row)
    return result


def _resolve_vectors(explicit: list[Path], roots: list[Path], max_files: int) -> list[Path]:
    paths: list[Path] = []
    for path in explicit:
        if path.is_file():
            paths.append(path.resolve())
        else:
            raise FileNotFoundError(path)
    for root in roots:
        if not root.is_dir():
            raise NotADirectoryError(root)
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in VECTOR_SUFFIXES:
                paths.append(path.resolve())
                if len(paths) > max_files:
                    raise ValueError(f"vector discovery exceeded max_files={max_files}")
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    if not unique:
        raise ValueError("no vector files were supplied or discovered")
    return unique


def _source_crs(collection: Any) -> CRS:
    value = collection.crs_wkt or collection.crs
    if not value:
        raise ValueError(f"vector layer {collection.name!r} has no CRS")
    return CRS.from_user_input(value)


def _identifier_values(feature: dict[str, Any]) -> set[str]:
    """Return only publisher-defined HMLR identifier properties.

    Fiona's top-level ``feature.id`` is an adapter/driver feature sequence
    identifier and is retained only as provenance. It must never participate in
    an exact Land Registry INSPIRE identifier match.
    """
    values: set[str] = set()
    for key, value in dict(feature.get("properties") or {}).items():
        if _property_key(key) not in AUTHORITATIVE_HMLR_ID_KEYS or value in (None, ""):
            continue
        cleaned = _clean_id(value)
        if cleaned:
            values.add(cleaned)
    return values


def _candidate_ids(candidate: dict[str, Any]) -> set[str]:
    return {
        cleaned
        for field_name in CANDIDATE_ID_FIELDS
        if (cleaned := _clean_id(candidate.get(field_name)))
    }


@dataclass
class CandidateState:
    row: dict[str, Any]
    point: Point
    ids: set[str]
    exact: list[dict[str, Any]] = field(default_factory=list)
    contains: list[dict[str, Any]] = field(default_factory=list)
    files_scanned: int = 0
    features_scanned: int = 0


def _record_match(
    state: CandidateState,
    *,
    feature: dict[str, Any],
    geometry: Any,
    source_path: Path,
    layer_name: str,
    source_crs: CRS,
    matched_ids: list[str],
    kind: str,
) -> None:
    record = {
        "source_path": str(source_path),
        "source_layer": layer_name,
        "source_feature_id": feature.get("id"),
        "source_crs": source_crs.to_string(),
        "matched_identifier_values": matched_ids,
        "geometry_type": geometry.geom_type,
        "geometry_area_m2": round(float(geometry.area), 3),
        "geometry_wkt_epsg27700": geometry.wkt,
        "geometry_geojson_epsg27700": mapping(geometry),
        "point_inside": bool(geometry.covers(state.point)),
    }
    (state.exact if kind == "exact" else state.contains).append(record)


def _choose_match(state: CandidateState) -> dict[str, Any]:
    exact = state.exact
    if exact:
        exact_covering = [record for record in exact if record["point_inside"]]
        if len(exact) == 1:
            chosen = exact[0]
            method = "EXACT_OFFICIAL_ID"
        elif len(exact_covering) == 1:
            chosen = exact_covering[0]
            method = "EXACT_OFFICIAL_ID_PLUS_POINT_DISAMBIGUATION"
        else:
            return {
                "status": "AMBIGUOUS_EXACT_IDENTIFIER_MATCH",
                "match_method": None,
                "exact_match_count": len(exact),
                "containment_match_count": len(state.contains),
                "matches": exact,
            }
    elif len(state.contains) == 1:
        chosen = state.contains[0]
        method = "UNIQUE_POINT_IN_POLYGON"
    elif len(state.contains) > 1:
        return {
            "status": "AMBIGUOUS_POINT_IN_POLYGON_MATCH",
            "match_method": None,
            "exact_match_count": 0,
            "containment_match_count": len(state.contains),
            "matches": state.contains,
        }
    else:
        return {
            "status": "NO_MATCH",
            "match_method": None,
            "exact_match_count": 0,
            "containment_match_count": 0,
            "matches": [],
        }

    return {
        "status": "MATCHED",
        "match_method": method,
        "exact_match_count": len(exact),
        "containment_match_count": len(state.contains),
        "match": chosen,
    }


def _scan_vector(path: Path, states: list[CandidateState]) -> dict[str, Any]:
    file_feature_count = 0
    layer_summaries = []
    for layer_name in fiona.listlayers(path):
        with fiona.open(path, layer=layer_name) as collection:
            source_crs = _source_crs(collection)
            transformer = None
            if source_crs != TARGET_CRS:
                transformer = Transformer.from_crs(source_crs, TARGET_CRS, always_xy=True)
            layer_count = 0
            for feature_obj in collection:
                feature = dict(feature_obj)
                layer_count += 1
                file_feature_count += 1
                identifier_values = _identifier_values(feature)
                exact_state_indexes = [
                    index for index, state in enumerate(states) if state.ids & identifier_values
                ]

                geometry_value = feature.get("geometry")
                if geometry_value is None:
                    continue
                bounds = feature_obj.get("bbox")
                spatial_state_indexes: list[int] = []
                if bounds and len(bounds) == 4 and transformer is None:
                    minx, miny, maxx, maxy = map(float, bounds)
                    spatial_state_indexes = [
                        index
                        for index, state in enumerate(states)
                        if minx <= state.point.x <= maxx and miny <= state.point.y <= maxy
                    ]
                else:
                    spatial_state_indexes = list(range(len(states)))

                interested = set(exact_state_indexes) | set(spatial_state_indexes)
                if not interested:
                    continue
                geometry = shape(geometry_value)
                if transformer is not None:
                    geometry = shapely_transform(transformer.transform, geometry)
                if not geometry.is_valid:
                    geometry = make_valid(geometry)
                if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
                    continue

                for index in interested:
                    state = states[index]
                    state.features_scanned += 1
                    matched_ids = sorted(state.ids & identifier_values)
                    if matched_ids:
                        _record_match(
                            state,
                            feature=feature,
                            geometry=geometry,
                            source_path=path,
                            layer_name=layer_name,
                            source_crs=source_crs,
                            matched_ids=matched_ids,
                            kind="exact",
                        )
                    elif geometry.covers(state.point):
                        _record_match(
                            state,
                            feature=feature,
                            geometry=geometry,
                            source_path=path,
                            layer_name=layer_name,
                            source_crs=source_crs,
                            matched_ids=[],
                            kind="contains",
                        )
            layer_summaries.append({"layer": layer_name, "features": layer_count, "crs": source_crs.to_string()})
    for state in states:
        state.files_scanned += 1
    stat = path.stat()
    return {
        "path": str(path),
        "size_bytes": stat.st_size,
        "sha256": _file_sha256(path),
        "feature_count": file_feature_count,
        "layers": layer_summaries,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starter-manifest", type=Path, required=True)
    parser.add_argument("--vector", type=Path, action="append", default=[])
    parser.add_argument("--vector-root", type=Path, action="append", default=[])
    parser.add_argument("--max-files", type=int, default=200)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    candidates = _load_candidates(args.starter_manifest)
    vectors = _resolve_vectors(args.vector, args.vector_root, args.max_files)
    states = [
        CandidateState(
            row=row,
            point=Point(row["bng_easting"], row["bng_northing"]),
            ids=_candidate_ids(row),
        )
        for row in candidates
    ]
    source_files = [_scan_vector(path, states) for path in vectors]

    results = []
    for state in states:
        decision = _choose_match(state)
        results.append(
            {
                "row_no": state.row["row_no"],
                "parcel_id": state.row["parcel_id"],
                "bng_easting": state.row["bng_easting"],
                "bng_northing": state.row["bng_northing"],
                "candidate_official_ids": sorted(state.ids),
                "files_scanned": state.files_scanned,
                "candidate_features_examined": state.features_scanned,
                **decision,
                "nearest_polygon_fill_used": False,
                "measured_value_promoted": False,
            }
        )

    matched = sum(result["status"] == "MATCHED" for result in results)
    payload = {
        "schema_version": 2,
        "slot_id": "height_difference_3",
        "target_crs": "EPSG:27700",
        "candidate_count": len(results),
        "matched_candidate_count": matched,
        "blocked_candidate_count": len(results) - matched,
        "source_files": source_files,
        "results": results,
        "matching_priority": ["exact_authoritative_hmlr_property_identifier", "unique_point_in_polygon"],
        "exact_identifier_source_policy": "HMLR_PROPERTY_FIELDS_ONLY_NO_FIONA_FEATURE_SEQUENCE_ID",
        "authoritative_hmlr_identifier_property_keys": sorted(AUTHORITATIVE_HMLR_ID_KEYS),
        "fiona_feature_id_used_for_matching": False,
        "nearest_polygon_fill_forbidden": True,
        "measurement_values_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    _write_json(args.output, payload)
    print(json.dumps({"ok": True, "candidates": len(results), "matched": matched}))
    return 0 if matched == len(results) else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

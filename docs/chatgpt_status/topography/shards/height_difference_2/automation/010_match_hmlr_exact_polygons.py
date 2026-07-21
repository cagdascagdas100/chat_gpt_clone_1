#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable
import fiona
from pyproj import CRS, Transformer
from shapely import make_valid
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform as shapely_transform

TARGET_CRS = CRS.from_epsg(27700)
ID_KEY_RE = re.compile(r"(inspire|cadastral|identifier|(^|_)id($|_))", re.I)
VECTOR_SUFFIXES = {".gml", ".xml", ".gpkg", ".geojson", ".json", ".shp"}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip()).casefold()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("exactly three candidates required")
    candidates: list[dict[str, Any]] = []
    for index, value in enumerate(rows, start=1):
        row = dict(value)
        for field in ("row_no", "parcel_id", "hmlr_inspire_id", "bng_easting", "bng_northing"):
            if row.get(field) in (None, ""):
                raise ValueError(f"candidate {index} lacks {field}")
        row["row_no"] = int(row["row_no"])
        row["bng_easting"] = float(row["bng_easting"])
        row["bng_northing"] = float(row["bng_northing"])
        candidates.append(row)
    return candidates


def _resolve_vectors(explicit: list[Path], roots: list[Path], max_files: int) -> list[Path]:
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


def _identifier_values(feature: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    feature_id = _clean(feature.get("id"))
    if feature_id:
        values.add(feature_id)
    for key, value in dict(feature.get("properties") or {}).items():
        if ID_KEY_RE.search(str(key)) and value not in (None, ""):
            cleaned = _clean(value)
            if cleaned:
                values.add(cleaned)
    return values


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starter-manifest", type=Path, required=True)
    parser.add_argument("--vector", type=Path, action="append", default=[])
    parser.add_argument("--vector-root", type=Path, action="append", default=[])
    parser.add_argument("--max-files", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        candidates = _load_candidates(args.starter_manifest)
        vector_paths = _resolve_vectors(args.vector, args.vector_root, args.max_files)
        states: dict[str, dict[str, Any]] = {
            _clean(candidate["hmlr_inspire_id"]): {"candidate": candidate, "matches": []} for candidate in candidates
        }
        source_files: list[dict[str, Any]] = []
        for path in vector_paths:
            file_feature_count = 0
            layer_summaries: list[dict[str, Any]] = []
            for layer_name in fiona.listlayers(path):
                with fiona.open(path, layer=layer_name) as collection:
                    source_crs = CRS.from_user_input(collection.crs_wkt or collection.crs)
                    transformer = None if source_crs == TARGET_CRS else Transformer.from_crs(source_crs, TARGET_CRS, always_xy=True)
                    layer_count = 0
                    for feature_obj in collection:
                        layer_count += 1
                        file_feature_count += 1
                        feature = dict(feature_obj)
                        matched_ids = set(states) & _identifier_values(feature)
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
                                    "geometry_type": geometry.geom_type,
                                    "geometry_area_m2": round(float(geometry.area), 3),
                                    "geometry_wkt_epsg27700": geometry.wkt,
                                    "geometry_geojson_epsg27700": mapping(geometry),
                                    "candidate_point_inside": bool(geometry.covers(point)),
                                }
                            )
                    layer_summaries.append({"layer": layer_name, "features": layer_count, "crs": source_crs.to_string()})
            source_files.append(
                {
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                    "feature_count": file_feature_count,
                    "layers": layer_summaries,
                }
            )
        results: list[dict[str, Any]] = []
        for state in states.values():
            matches = state["matches"]
            covering = [record for record in matches if record["candidate_point_inside"]]
            if len(matches) == 1 and len(covering) == 1:
                status = "MATCHED_EXACT_ID_AND_POINT_INSIDE"
                chosen = matches[0]
            elif len(matches) == 1:
                status = "BLOCKED_EXACT_ID_POINT_OUTSIDE"
                chosen = None
            elif len(matches) > 1:
                status = "BLOCKED_AMBIGUOUS_EXACT_ID"
                chosen = None
            else:
                status = "BLOCKED_NO_EXACT_ID_MATCH"
                chosen = None
            candidate = state["candidate"]
            results.append(
                {
                    "row_no": candidate["row_no"],
                    "parcel_id": candidate["parcel_id"],
                    "hmlr_inspire_id": candidate["hmlr_inspire_id"],
                    "bng_easting": candidate["bng_easting"],
                    "bng_northing": candidate["bng_northing"],
                    "status": status,
                    "exact_match_count": len(matches),
                    "match": chosen,
                    "nearest_polygon_fill_used": False,
                    "measured_value_promoted": False,
                }
            )
        results.sort(key=lambda row: row["row_no"])
        matched = sum(row["status"] == "MATCHED_EXACT_ID_AND_POINT_INSIDE" for row in results)
        status = "THREE_HMLR_EXACT_POLYGONS_MATCHED" if matched == 3 else "BLOCKED_THREE_HMLR_EXACT_POLYGONS_NOT_MATCHED"
        code = 0 if matched == 3 else 2
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": status,
            "target_crs": "EPSG:27700",
            "candidate_count": 3,
            "matched_candidate_count": matched,
            "source_files": source_files,
            "results": results,
            "matching_method": "EXACT_HMLR_INSPIRE_ID_AND_POINT_INSIDE",
            "point_in_polygon_only_fallback_used": False,
            "nearest_polygon_fill_forbidden": True,
            "measurement_values_written": 0,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
    except Exception as exc:
        payload = {
            "schema_version": 1,
            "slot_id": "height_difference_2",
            "status": "BLOCKED_HMLR_EXACT_MATCHER",
            "error": f"{type(exc).__name__}: {exc}",
            "matched_candidate_count": 0,
            "measurement_values_written": 0,
            "final_ready": False,
            "fake_data": False,
            "db_write": False,
            "migration": False,
            "production_deploy": False,
        }
        code = 2
    _write(args.output, payload)
    print(json.dumps({"ok": code == 0, "status": payload["status"], "matched": payload.get("matched_candidate_count", 0)}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Sample EA DTM and OS Terrain 50 for HMLR-matched real parcels.

The primary parcel metric is derived from EA DTM cells inside the matched
polygon. OS Terrain 50 is an independent coarse-grid elevation cross-check.
No value is promoted when geometry, cell-count, nodata or cross-source gates
fail.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import numpy as np
    import rasterio
    from pyproj import CRS, Transformer
    from rasterio.mask import mask
    from shapely.geometry import Point, box, mapping
    from shapely.ops import transform as shapely_transform
    from shapely import wkt
except ImportError as exc:
    raise SystemExit(f"Required geospatial dependency is missing: {exc}")

TARGET_CRS = CRS.from_epsg(27700)
DISPLAY_CRS = CRS.from_epsg(4326)
EA_SUFFIXES = {".tif", ".tiff"}
OS_SUFFIXES = {".asc", ".tif", ".tiff"}


def _sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _discover(explicit: list[Path], roots: list[Path], suffixes: set[str], max_files: int) -> list[Path]:
    values: list[Path] = []
    for path in explicit:
        if not path.is_file():
            raise FileNotFoundError(path)
        values.append(path.resolve())
    for root in roots:
        if not root.is_dir():
            raise NotADirectoryError(root)
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in suffixes:
                values.append(path.resolve())
                if len(values) > max_files:
                    raise ValueError(f"raster discovery exceeded max_files={max_files}")
    result: list[Path] = []
    seen: set[Path] = set()
    for path in values:
        if path not in seen:
            seen.add(path)
            result.append(path)
    if not result:
        raise ValueError("no matching raster files were supplied or discovered")
    return result


def _load_matches(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list) or not results:
        raise ValueError("matched manifest must contain results")
    return [dict(value) for value in results]


def _transform_geometry(geometry: Any, source: CRS, target: CRS) -> Any:
    if source == target:
        return geometry
    transformer = Transformer.from_crs(source, target, always_xy=True)
    return shapely_transform(transformer.transform, geometry)


@dataclass
class RasterUse:
    path: Path
    crs: str
    count: int
    resolution: tuple[float, float]
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "crs": self.crs,
            "valid_cell_count": self.count,
            "resolution": [round(self.resolution[0], 6), round(self.resolution[1], 6)],
            "sha256": self.sha256,
        }


def _raster_crs(dataset: Any, path: Path, *, terrain50_ascii: bool) -> CRS:
    if dataset.crs is not None:
        return CRS.from_user_input(dataset.crs)
    # Esri ASCII grids do not embed a CRS. Official OS Terrain 50 GB grids
    # are explicitly British National Grid; the preceding tile/header gate
    # has already validated their 10 km BNG origin and 50 m cell size.
    if terrain50_ascii and path.suffix.casefold() == ".asc":
        return TARGET_CRS
    raise ValueError("raster CRS missing")


def _polygon_values(
    geometry_27700: Any,
    paths: list[Path],
    *,
    terrain50_ascii: bool = False,
) -> tuple[np.ndarray, list[RasterUse], list[str]]:
    arrays: list[np.ndarray] = []
    uses: list[RasterUse] = []
    errors: list[str] = []
    for path in paths:
        try:
            with rasterio.open(path) as dataset:
                raster_crs = _raster_crs(dataset, path, terrain50_ascii=terrain50_ascii)
                geometry_raster = _transform_geometry(geometry_27700, TARGET_CRS, raster_crs)
                if not geometry_raster.intersects(box(*dataset.bounds)):
                    continue
                output, _ = mask(
                    dataset,
                    [mapping(geometry_raster)],
                    crop=True,
                    all_touched=False,
                    filled=False,
                    indexes=1,
                )
                values = np.asarray(output.compressed(), dtype="float64")
                values = values[np.isfinite(values)]
                if values.size == 0:
                    continue
                arrays.append(values)
                uses.append(
                    RasterUse(
                        path=path,
                        crs=raster_crs.to_string(),
                        count=int(values.size),
                        resolution=(abs(dataset.res[0]), abs(dataset.res[1])),
                        sha256=_sha256(path),
                    )
                )
        except Exception as exc:
            errors.append(f"{path}: {type(exc).__name__}: {exc}")
    if not arrays:
        return np.array([], dtype="float64"), uses, errors
    return np.concatenate(arrays), uses, errors


def _centroid_sample(centroid_27700: Point, paths: list[Path]) -> tuple[float | None, dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    matches: list[tuple[float, dict[str, Any]]] = []
    for path in paths:
        try:
            with rasterio.open(path) as dataset:
                raster_crs = _raster_crs(dataset, path, terrain50_ascii=True)
                point_raster = _transform_geometry(centroid_27700, TARGET_CRS, raster_crs)
                if not box(*dataset.bounds).covers(point_raster):
                    continue
                sample = next(dataset.sample([(point_raster.x, point_raster.y)], indexes=1, masked=True))
                value = sample[0]
                if np.ma.is_masked(value) or not math.isfinite(float(value)):
                    continue
                matches.append(
                    (
                        float(value),
                        {
                            "path": str(path),
                            "crs": raster_crs.to_string(),
                            "resolution": [round(abs(dataset.res[0]), 6), round(abs(dataset.res[1]), 6)],
                            "sha256": _sha256(path),
                        },
                    )
                )
        except Exception as exc:
            errors.append(f"{path}: {type(exc).__name__}: {exc}")
    if len(matches) == 1:
        return matches[0][0], matches[0][1], errors
    if len(matches) > 1:
        errors.append("centroid intersects multiple OS Terrain 50 rasters; unique tile required")
    return None, None, errors


def _stats(values: np.ndarray) -> dict[str, Any]:
    if values.size == 0:
        return {}
    q05, q25, q50, q75, q95 = np.percentile(values, [5, 25, 50, 75, 95])
    return {
        "valid_cell_count": int(values.size),
        "minimum_m": round(float(np.min(values)), 3),
        "maximum_m": round(float(np.max(values)), 3),
        "median_m": round(float(q50), 3),
        "q05_m": round(float(q05), 3),
        "q25_m": round(float(q25), 3),
        "q75_m": round(float(q75), 3),
        "q95_m": round(float(q95), 3),
        "iqr_m": round(float(q75 - q25), 3),
        "raw_range_m": round(float(np.max(values) - np.min(values)), 3),
        "robust_height_difference_p95_p05_m": round(float(q95 - q05), 3),
    }


def _confidence(ea_count: int, cross_difference: float) -> str:
    if ea_count >= 16 and cross_difference <= 4.0:
        return "HIGH"
    if ea_count >= 4 and cross_difference <= 8.0:
        return "MEDIUM_HIGH"
    return "NOT_PROMOTED"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matched-manifest", type=Path, required=True)
    parser.add_argument("--ea-raster", type=Path, action="append", default=[])
    parser.add_argument("--ea-root", type=Path, action="append", default=[])
    parser.add_argument("--terrain50-raster", type=Path, action="append", default=[])
    parser.add_argument("--terrain50-root", type=Path, action="append", default=[])
    parser.add_argument("--max-files", type=int, default=500)
    parser.add_argument("--minimum-ea-cells", type=int, default=4)
    parser.add_argument("--max-crosscheck-difference-m", type=float, default=8.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    matched_rows = _load_matches(args.matched_manifest)
    ea_paths = _discover(args.ea_raster, args.ea_root, EA_SUFFIXES, args.max_files)
    os_paths = _discover(args.terrain50_raster, args.terrain50_root, OS_SUFFIXES, args.max_files)

    outputs = []
    promoted_rows = []
    for row in matched_rows:
        base = {
            "row_no": row.get("row_no"),
            "parcel_id": row.get("parcel_id"),
            "hmlr_match_status": row.get("status"),
            "hmlr_match_method": row.get("match_method"),
            "measured_value_promoted": False,
        }
        if row.get("status") != "MATCHED" or not isinstance(row.get("match"), dict):
            outputs.append({**base, "status": "BLOCKED_HMLR_MATCH_REQUIRED"})
            continue

        geometry = wkt.loads(row["match"]["geometry_wkt_epsg27700"])
        display_geometry = _transform_geometry(geometry, TARGET_CRS, DISPLAY_CRS)
        centroid = geometry.centroid
        ea_values, ea_uses, ea_errors = _polygon_values(geometry, ea_paths)
        os_values, os_uses, os_errors = _polygon_values(geometry, os_paths, terrain50_ascii=True)
        os_centroid, os_centroid_source, os_centroid_errors = _centroid_sample(centroid, os_paths)
        ea_stats = _stats(ea_values)
        os_stats = _stats(os_values)
        errors = ea_errors + os_errors + os_centroid_errors

        gate_reasons: list[str] = []
        ea_count = int(ea_stats.get("valid_cell_count", 0))
        if ea_count < args.minimum_ea_cells:
            gate_reasons.append("INSUFFICIENT_EA_DTM_CELLS")
        if os_centroid is None:
            gate_reasons.append("OS_TERRAIN50_CENTROID_SAMPLE_MISSING_OR_AMBIGUOUS")

        difference = None
        confidence = "NOT_PROMOTED"
        if ea_stats and os_centroid is not None:
            difference = round(abs(float(ea_stats["median_m"]) - os_centroid), 3)
            if difference > args.max_crosscheck_difference_m:
                gate_reasons.append("CROSS_SOURCE_DIFFERENCE_EXCEEDS_THRESHOLD")
            confidence = _confidence(ea_count, difference)

        promoted = not gate_reasons and confidence in {"HIGH", "MEDIUM_HIGH"}
        result = {
            **base,
            "status": "MEASURED_AND_CROSSCHECKED" if promoted else "NOT_PROMOTED",
            "geometry_area_m2": row["match"].get("geometry_area_m2"),
            "geometry_wkt_epsg27700": geometry.wkt,
            "geometry_geojson_epsg4326_display_only": mapping(display_geometry),
            "geometry_centroid_epsg27700": [round(centroid.x, 3), round(centroid.y, 3)],
            "ea_dtm": {
                "statistics": ea_stats,
                "source_rasters": [use.as_dict() for use in ea_uses],
                "errors": ea_errors,
            },
            "os_terrain50": {
                "polygon_statistics": os_stats,
                "centroid_elevation_m": None if os_centroid is None else round(os_centroid, 3),
                "centroid_source": os_centroid_source,
                "source_rasters": [use.as_dict() for use in os_uses],
                "errors": os_errors + os_centroid_errors,
            },
            "cross_source_absolute_difference_m": difference,
            "crosscheck_threshold_m": args.max_crosscheck_difference_m,
            "confidence": confidence,
            "gate_reasons": gate_reasons,
            "measurement_errors": errors,
            "nearest_point_fill_used": False,
            "measured_value_promoted": promoted,
        }
        outputs.append(result)
        if promoted:
            promoted_rows.append(
                {
                    "row_no": row.get("row_no"),
                    "parcel_id": row.get("parcel_id"),
                    "height_difference_m": ea_stats["robust_height_difference_p95_p05_m"],
                    "height_difference_method": "EA_DTM_1M_POLYGON_P95_MINUS_P05",
                    "elevation_median_m": ea_stats["median_m"],
                    "elevation_iqr_m": ea_stats["iqr_m"],
                    "ea_valid_cell_count": ea_count,
                    "os_terrain50_centroid_elevation_m": round(float(os_centroid), 3),
                    "cross_source_absolute_difference_m": difference,
                    "boundary_match_method": row.get("match_method"),
                    "confidence": confidence,
                    "data_status": "official_sources_crosschecked",
                    "geometry_geojson_epsg4326_display_only": mapping(display_geometry),
                }
            )

    payload = {
        "schema_version": 1,
        "slot_id": "height_difference_3",
        "target_crs": "EPSG:27700",
        "vertical_reference": "metres_Ordnance_Datum_Newlyn_where_documented_by_source",
        "candidate_count": len(outputs),
        "promoted_measurement_count": len(promoted_rows),
        "blocked_measurement_count": len(outputs) - len(promoted_rows),
        "minimum_ea_cells": args.minimum_ea_cells,
        "max_crosscheck_difference_m": args.max_crosscheck_difference_m,
        "height_difference_definition": "EA_DTM_polygon_95th_percentile_minus_5th_percentile",
        "results": outputs,
        "measured_rows": promoted_rows,
        "nearest_point_fill_forbidden": True,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    _write_json(args.output, payload)
    print(json.dumps({"ok": True, "candidates": len(outputs), "promoted": len(promoted_rows)}))
    return 0 if len(promoted_rows) == len(outputs) else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        raise

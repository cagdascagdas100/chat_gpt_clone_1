#!/usr/bin/env python3
"""Measure parcel height difference from EA DTM and cross-check at one point with OS Terrain 50.

The primary metric is the 95th-minus-5th percentile of finite EA DTM cells
strictly inside the matched HMLR polygon. Promotion is fail-closed: one exact EA
coverage, one exact OS Terrain 50 tile, matching-point cross-source agreement,
valid source geometry/CRS/resolution and an error-free read are all required.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
try:
    import numpy as np
    import rasterio
    from pyproj import CRS, Transformer
    from rasterio.mask import mask
    from shapely import wkt
    from shapely.geometry import Point, box, mapping
    from shapely.ops import transform as shapely_transform
except ImportError as exc:
    raise SystemExit(f'Required geospatial dependency is missing: {exc}')
TARGET_CRS = CRS.from_epsg(27700)
DISPLAY_CRS = CRS.from_epsg(4326)
TARGET_BOUNDS = box(0.0, 0.0, 700000.0, 1300000.0)
EA_SUFFIXES = {'.tif', '.tiff'}
OS_SUFFIXES = {'.asc', '.tif', '.tiff'}
MIN_PLAUSIBLE_ELEVATION_M = -100.0
MAX_PLAUSIBLE_ELEVATION_M = 1500.0

def _sha256(path: Path, chunk_size: int=1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b''):
            digest.update(chunk)
    return digest.hexdigest()

def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f'.{path.name}_', suffix='.json.tmp', dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        temp.unlink(missing_ok=True)
        raise

def _strict_transformer(source: CRS, target: CRS) -> Transformer:
    return Transformer.from_crs(source, target, always_xy=True, allow_ballpark=False, only_best=True)

def _transform_geometry(geometry: Any, source: CRS, target: CRS) -> Any:
    if source == target:
        return geometry
    transformer = _strict_transformer(source, target)
    return shapely_transform(transformer.transform, geometry)

def _discover(explicit: list[Path], roots: list[Path], suffixes: set[str], max_files: int) -> list[Path]:
    if max_files < 1:
        raise ValueError('max_files must be positive')
    values: list[Path] = []
    for path in explicit:
        if not path.is_file():
            raise FileNotFoundError(path)
        values.append(path.resolve())
    for root in roots:
        if not root.is_dir():
            raise NotADirectoryError(root)
        for path in sorted(root.rglob('*')):
            if path.is_file() and path.suffix.casefold() in suffixes:
                values.append(path.resolve())
                if len(values) > max_files:
                    raise ValueError(f'raster discovery exceeded max_files={max_files}')
    result: list[Path] = []
    seen: set[Path] = set()
    for path in values:
        if path not in seen:
            seen.add(path)
            result.append(path)
    if not result:
        raise ValueError('no matching raster files were supplied or discovered')
    return result

def _load_matches(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding='utf-8-sig'))
    results = payload.get('results') if isinstance(payload, dict) else None
    if not isinstance(results, list) or not results:
        raise ValueError('matched manifest must contain a non-empty results list')
    seen_rows: set[int] = set()
    seen_parcels: set[str] = set()
    output: list[dict[str, Any]] = []
    for index, raw in enumerate(results, 1):
        if not isinstance(raw, dict):
            raise ValueError(f'matched result {index} is not an object')
        row = dict(raw)
        row_no = int(row['row_no'])
        parcel_id = str(row['parcel_id']).strip()
        if not parcel_id:
            raise ValueError(f'matched result {index} has empty parcel_id')
        if row_no in seen_rows or parcel_id in seen_parcels:
            raise ValueError('matched manifest contains duplicate row_no or parcel_id')
        seen_rows.add(row_no)
        seen_parcels.add(parcel_id)
        output.append(row)
    return output

@dataclass(frozen=True)
class RasterUse:
    path: Path
    crs: str
    count: int
    resolution: tuple[float, float]
    bounds: tuple[float, float, float, float]
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        return {'path': str(self.path), 'crs': self.crs, 'valid_cell_count': self.count, 'resolution': [round(v, 6) for v in self.resolution], 'bounds': [round(v, 3) for v in self.bounds], 'sha256': self.sha256}

def _raster_crs(dataset: Any, path: Path, *, terrain50_ascii: bool) -> CRS:
    if dataset.crs is not None:
        return CRS.from_user_input(dataset.crs)
    if terrain50_ascii and path.suffix.casefold() == '.asc':
        return TARGET_CRS
    raise ValueError(f'raster CRS missing: {path}')

def _validate_raster_contract(dataset: Any, path: Path, *, terrain50: bool) -> tuple[CRS, tuple[float, float]]:
    if dataset.count != 1:
        raise ValueError(f'single-band elevation raster required: {path}')
    crs = _raster_crs(dataset, path, terrain50_ascii=terrain50)
    if crs != TARGET_CRS:
        raise ValueError(f'elevation raster must be EPSG:27700: {path} got={crs}')
    rx, ry = (abs(float(dataset.res[0])), abs(float(dataset.res[1])))
    if not all((math.isfinite(v) and v > 0 for v in (rx, ry))):
        raise ValueError(f'invalid raster resolution: {path}')
    if terrain50:
        if abs(rx - 50.0) > 1e-06 or abs(ry - 50.0) > 1e-06:
            raise ValueError(f'Terrain50 raster must be 50m: {path} res={(rx, ry)}')
    elif abs(rx - 1.0) > 0.05 or abs(ry - 1.0) > 0.05:
        raise ValueError(f'EA DTM raster must be nominal 1m: {path} res={(rx, ry)}')
    return (crs, (rx, ry))

def _plausible(values: np.ndarray, path: Path) -> np.ndarray:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return finite
    if float(np.min(finite)) < MIN_PLAUSIBLE_ELEVATION_M:
        raise ValueError(f'elevation below plausible GB DTM range: {path}')
    if float(np.max(finite)) > MAX_PLAUSIBLE_ELEVATION_M:
        raise ValueError(f'elevation above plausible GB DTM range: {path}')
    return finite

def _polygon_values(geometry_27700: Any, paths: list[Path], *, terrain50: bool) -> tuple[np.ndarray, list[RasterUse], list[str]]:
    arrays: list[np.ndarray] = []
    uses: list[RasterUse] = []
    errors: list[str] = []
    for path in paths:
        try:
            with rasterio.open(path) as dataset:
                crs, resolution = _validate_raster_contract(dataset, path, terrain50=terrain50)
                geometry_raster = _transform_geometry(geometry_27700, TARGET_CRS, crs)
                if not geometry_raster.intersects(box(*dataset.bounds)):
                    continue
                output, _ = mask(dataset, [mapping(geometry_raster)], crop=True, all_touched=False, filled=False, indexes=1)
                values = _plausible(np.asarray(output.compressed(), dtype='float64'), path)
                if values.size == 0:
                    continue
                arrays.append(values)
                uses.append(RasterUse(path=path, crs=crs.to_string(), count=int(values.size), resolution=resolution, bounds=tuple(map(float, dataset.bounds)), sha256=_sha256(path)))
        except Exception as exc:
            errors.append(f'{path}: {type(exc).__name__}: {exc}')
    if not arrays:
        return (np.array([], dtype='float64'), uses, errors)
    return (np.concatenate(arrays), uses, errors)

def _point_sample(point_27700: Point, paths: list[Path], *, terrain50: bool) -> tuple[float | None, dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    matches: list[tuple[float, dict[str, Any]]] = []
    for path in paths:
        try:
            with rasterio.open(path) as dataset:
                crs, resolution = _validate_raster_contract(dataset, path, terrain50=terrain50)
                point_raster = _transform_geometry(point_27700, TARGET_CRS, crs)
                if not box(*dataset.bounds).covers(point_raster):
                    continue
                sampled = next(dataset.sample([(point_raster.x, point_raster.y)], indexes=1, masked=True))[0]
                if np.ma.is_masked(sampled):
                    continue
                value = float(sampled)
                if not math.isfinite(value):
                    continue
                _plausible(np.asarray([value], dtype='float64'), path)
                matches.append((value, {'path': str(path), 'crs': crs.to_string(), 'resolution': [round(v, 6) for v in resolution], 'sha256': _sha256(path)}))
        except Exception as exc:
            errors.append(f'{path}: {type(exc).__name__}: {exc}')
    if len(matches) == 1:
        return (matches[0][0], matches[0][1], errors)
    if len(matches) > 1:
        errors.append('point intersects multiple elevation rasters; unique source raster required')
    return (None, None, errors)

def _stats(values: np.ndarray) -> dict[str, Any]:
    if values.size == 0:
        return {}
    q05, q25, q50, q75, q95 = np.percentile(values, [5, 25, 50, 75, 95])
    return {'valid_cell_count': int(values.size), 'minimum_m': round(float(np.min(values)), 3), 'maximum_m': round(float(np.max(values)), 3), 'median_m': round(float(q50), 3), 'q05_m': round(float(q05), 3), 'q25_m': round(float(q25), 3), 'q75_m': round(float(q75), 3), 'q95_m': round(float(q95), 3), 'iqr_m': round(float(q75 - q25), 3), 'raw_range_m': round(float(np.max(values) - np.min(values)), 3), 'robust_height_difference_p95_p05_m': round(float(q95 - q05), 3)}

def _confidence(ea_count: int, cross_difference: float) -> str:
    if ea_count >= 16 and cross_difference <= 4.0:
        return 'HIGH'
    if ea_count >= 4 and cross_difference <= 8.0:
        return 'MEDIUM_HIGH'
    return 'NOT_PROMOTED'

def _validated_geometry(row: dict[str, Any]) -> Any:
    match = row.get('match')
    if row.get('status') != 'MATCHED' or not isinstance(match, dict):
        raise ValueError('HMLR MATCHED result required')
    geometry = wkt.loads(str(match['geometry_wkt_epsg27700']))
    if geometry.is_empty or geometry.geom_type not in {'Polygon', 'MultiPolygon'}:
        raise ValueError('matched geometry must be a non-empty polygon')
    if not geometry.is_valid:
        raise ValueError('matched geometry must already be valid')
    if not math.isfinite(float(geometry.area)) or geometry.area <= 0:
        raise ValueError('matched geometry has invalid area')
    if not TARGET_BOUNDS.covers(geometry):
        raise ValueError('matched geometry outside accepted British National Grid extent')
    point_inside = match.get('point_inside')
    if point_inside is not True:
        raise ValueError('matched geometry is not point-consistent')
    return geometry

def main(argv: Iterable[str] | None=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--matched-manifest', type=Path, required=True)
    parser.add_argument('--ea-raster', type=Path, action='append', default=[])
    parser.add_argument('--ea-root', type=Path, action='append', default=[])
    parser.add_argument('--terrain50-raster', type=Path, action='append', default=[])
    parser.add_argument('--terrain50-root', type=Path, action='append', default=[])
    parser.add_argument('--max-files', type=int, default=500)
    parser.add_argument('--minimum-ea-cells', type=int, default=4)
    parser.add_argument('--max-crosscheck-difference-m', type=float, default=8.0)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.minimum_ea_cells < 4:
        raise ValueError('minimum-ea-cells must be at least 4')
    if not math.isfinite(args.max_crosscheck_difference_m) or not 0 < args.max_crosscheck_difference_m <= 20:
        raise ValueError('max-crosscheck-difference-m must be in (0, 20]')
    matched_path = args.matched_manifest.resolve()
    matched_rows = _load_matches(matched_path)
    ea_paths = _discover(args.ea_raster, args.ea_root, EA_SUFFIXES, args.max_files)
    os_paths = _discover(args.terrain50_raster, args.terrain50_root, OS_SUFFIXES, args.max_files)
    outputs: list[dict[str, Any]] = []
    promoted_rows: list[dict[str, Any]] = []
    for row in matched_rows:
        base = {'row_no': row.get('row_no'), 'parcel_id': row.get('parcel_id'), 'hmlr_match_status': row.get('status'), 'hmlr_match_method': row.get('match_method'), 'measured_value_promoted': False}
        try:
            geometry = _validated_geometry(row)
        except Exception as exc:
            outputs.append({**base, 'status': 'BLOCKED_HMLR_MATCH_REQUIRED', 'gate_reasons': [f'{type(exc).__name__}: {exc}']})
            continue
        display_geometry = _transform_geometry(geometry, TARGET_CRS, DISPLAY_CRS)
        centroid = geometry.representative_point()
        ea_values, ea_uses, ea_errors = _polygon_values(geometry, ea_paths, terrain50=False)
        os_values, os_uses, os_errors = _polygon_values(geometry, os_paths, terrain50=True)
        ea_point, ea_point_source, ea_point_errors = _point_sample(centroid, ea_paths, terrain50=False)
        os_point, os_point_source, os_point_errors = _point_sample(centroid, os_paths, terrain50=True)
        ea_stats = _stats(ea_values)
        os_stats = _stats(os_values)
        errors = ea_errors + os_errors + ea_point_errors + os_point_errors
        gate_reasons: list[str] = []
        ea_count = int(ea_stats.get('valid_cell_count', 0))
        if ea_count < args.minimum_ea_cells:
            gate_reasons.append('INSUFFICIENT_EA_DTM_CELLS')
        if len(ea_uses) != 1:
            gate_reasons.append('EA_DTM_UNIQUE_COVERAGE_REQUIRED')
        if len(os_uses) != 1:
            gate_reasons.append('OS_TERRAIN50_UNIQUE_TILE_REQUIRED')
        if ea_point is None:
            gate_reasons.append('EA_DTM_POINT_SAMPLE_MISSING_OR_AMBIGUOUS')
        if os_point is None:
            gate_reasons.append('OS_TERRAIN50_POINT_SAMPLE_MISSING_OR_AMBIGUOUS')
        if errors:
            gate_reasons.append('SOURCE_READ_OR_VALIDATION_ERROR_PRESENT')
        difference: float | None = None
        confidence = 'NOT_PROMOTED'
        if ea_point is not None and os_point is not None:
            difference = round(abs(float(ea_point) - float(os_point)), 3)
            if difference > args.max_crosscheck_difference_m:
                gate_reasons.append('CROSS_SOURCE_DIFFERENCE_EXCEEDS_THRESHOLD')
            confidence = _confidence(ea_count, difference)
        robust_difference = ea_stats.get('robust_height_difference_p95_p05_m')
        if robust_difference is None or not math.isfinite(float(robust_difference)):
            gate_reasons.append('ROBUST_HEIGHT_DIFFERENCE_MISSING')
        elif float(robust_difference) < 0:
            gate_reasons.append('ROBUST_HEIGHT_DIFFERENCE_NEGATIVE')
        gate_reasons = list(dict.fromkeys(gate_reasons))
        promoted = not gate_reasons and confidence in {'HIGH', 'MEDIUM_HIGH'}
        result = {**base, 'status': 'MEASURED_AND_CROSSCHECKED' if promoted else 'NOT_PROMOTED', 'geometry_area_m2': round(float(geometry.area), 3), 'geometry_wkt_epsg27700': geometry.wkt, 'geometry_geojson_epsg4326_display_only': mapping(display_geometry), 'geometry_sample_point_epsg27700': [round(centroid.x, 3), round(centroid.y, 3)], 'ea_dtm': {'statistics': ea_stats, 'point_elevation_m': None if ea_point is None else round(ea_point, 3), 'point_source': ea_point_source, 'source_rasters': [use.as_dict() for use in ea_uses], 'errors': ea_errors + ea_point_errors}, 'os_terrain50': {'polygon_statistics': os_stats, 'point_elevation_m': None if os_point is None else round(os_point, 3), 'point_source': os_point_source, 'source_rasters': [use.as_dict() for use in os_uses], 'errors': os_errors + os_point_errors}, 'cross_source_same_point_absolute_difference_m': difference, 'crosscheck_threshold_m': args.max_crosscheck_difference_m, 'confidence': confidence, 'gate_reasons': gate_reasons, 'measurement_errors': errors, 'nearest_point_fill_used': False, 'measured_value_promoted': promoted}
        outputs.append(result)
        if promoted:
            promoted_rows.append({'row_no': int(row['row_no']), 'parcel_id': str(row['parcel_id']), 'height_difference_m': float(robust_difference), 'height_difference_method': 'EA_DTM_1M_POLYGON_P95_MINUS_P05', 'elevation_median_m': ea_stats['median_m'], 'elevation_iqr_m': ea_stats['iqr_m'], 'ea_valid_cell_count': ea_count, 'ea_sample_point_elevation_m': round(float(ea_point), 3), 'os_terrain50_sample_point_elevation_m': round(float(os_point), 3), 'cross_source_same_point_absolute_difference_m': difference, 'os_terrain50_centroid_elevation_m': round(float(os_point), 3), 'cross_source_absolute_difference_m': difference, 'boundary_match_method': row.get('match_method'), 'confidence': confidence, 'data_status': 'official_sources_crosschecked_same_point', 'geometry_geojson_epsg4326_display_only': mapping(display_geometry)})
    payload = {'schema_version': 2, 'measurement_contract_version': 'EA_DTM_POLYGON_P95_P05_OS_T50_SAME_POINT_V2', 'slot_id': 'height_difference_3', 'target_crs': 'EPSG:27700', 'vertical_reference': 'metres_Ordnance_Datum_Newlyn_where_documented_by_source', 'candidate_count': len(outputs), 'promoted_measurement_count': len(promoted_rows), 'blocked_measurement_count': len(outputs) - len(promoted_rows), 'minimum_ea_cells': args.minimum_ea_cells, 'max_crosscheck_difference_m': args.max_crosscheck_difference_m, 'height_difference_definition': 'EA_DTM_polygon_95th_percentile_minus_5th_percentile', 'crosscheck_definition': 'EA_DTM_and_OS_Terrain50_at_same_polygon_representative_point', 'matched_manifest': str(matched_path), 'matched_manifest_sha256': _sha256(matched_path), 'ea_raster_count': len(ea_paths), 'terrain50_raster_count': len(os_paths), 'results': outputs, 'measured_rows': promoted_rows, 'unique_ea_coverage_required': True, 'unique_terrain50_tile_required': True, 'source_errors_forbid_promotion': True, 'strict_crs_resolution_gate': True, 'atomic_output_materialization': True, 'nearest_point_fill_forbidden': True, 'final_ready': False, 'fake_data': False, 'db_write': False, 'migration': False, 'production_deploy': False}
    _atomic_json(args.output, payload)
    print(json.dumps({'ok': len(promoted_rows) == len(outputs), 'candidates': len(outputs), 'promoted': len(promoted_rows), 'output': str(args.output)}))
    return 0 if len(promoted_rows) == len(outputs) else 2
if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': f'{type(exc).__name__}: {exc}'}), file=__import__('sys').stderr)
        raise

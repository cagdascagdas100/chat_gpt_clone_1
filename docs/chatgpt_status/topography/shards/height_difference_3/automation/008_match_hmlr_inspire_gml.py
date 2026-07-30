#!/usr/bin/env python3
"""Match canonical candidates to HMLR INSPIRE polygons without nearest fill.

Only publisher-defined INSPIRE identifiers participate in exact matching. Exact
identifier matches must also cover the canonical BNG point. Identical polygons
repeated across local-authority files are deduplicated by identifier and geometry;
all other ambiguity fails closed. Output JSON is atomically materialized.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
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
    raise SystemExit(f'Required geospatial dependency is missing: {exc}')
TARGET_CRS = CRS.from_epsg(27700)
TARGET_BOUNDS = (0.0, 0.0, 700000.0, 1300000.0)
AUTHORITATIVE_HMLR_ID_KEYS = {'gmlid', 'inspireid', 'nationalcadastralreference'}
CANDIDATE_INSPIRE_ID_FIELDS = ('hmlr_inspire_id', 'national_cadastral_reference', 'parcel_registry_id')
IGNORED_NON_INSPIRE_ID_FIELDS = ('hmlr_title_number', 'title_number', 'uprn')
VECTOR_SUFFIXES = {'.gml', '.gpkg', '.geojson', '.json', '.shp'}

def _clean_id(value: Any) -> str:
    return re.sub('\\s+', '', str(value or '').strip()).casefold()

def _property_key(value: Any) -> str:
    return re.sub('[^a-z0-9]+', '', str(value or '').casefold())

def _file_sha256(path: Path, chunk_size: int=1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b''):
            digest.update(chunk)
    return digest.hexdigest()

def _load_candidates(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding='utf-8-sig'))
    values = payload.get('candidates') if isinstance(payload, dict) else payload
    if not isinstance(values, list) or not values:
        raise ValueError('starter manifest must contain a non-empty candidates list')
    result: list[dict[str, Any]] = []
    seen_rows: set[int] = set()
    for index, value in enumerate(values, start=1):
        row = dict(value)
        for field_name in ('row_no', 'parcel_id', 'bng_easting', 'bng_northing'):
            if field_name not in row or str(row[field_name]).strip() == '':
                raise ValueError(f'candidate {index} lacks {field_name}')
        row['row_no'] = int(row['row_no'])
        row['bng_easting'] = float(row['bng_easting'])
        row['bng_northing'] = float(row['bng_northing'])
        if row['row_no'] in seen_rows:
            raise ValueError(f"duplicate candidate row_no: {row['row_no']}")
        seen_rows.add(row['row_no'])
        if not all((math.isfinite(row[name]) for name in ('bng_easting', 'bng_northing'))):
            raise ValueError(f'candidate {index} has non-finite BNG coordinates')
        minx, miny, maxx, maxy = TARGET_BOUNDS
        if not (minx <= row['bng_easting'] <= maxx and miny <= row['bng_northing'] <= maxy):
            raise ValueError(f'candidate {index} is outside the accepted BNG extent')
        result.append(row)
    return result

def _resolve_vectors(explicit: list[Path], roots: list[Path], max_files: int) -> list[Path]:
    if max_files < 1:
        raise ValueError('max-files must be positive')
    paths: list[Path] = []
    for path in explicit:
        if not path.is_file():
            raise FileNotFoundError(path)
        paths.append(path.resolve())
    for root in roots:
        if not root.is_dir():
            raise NotADirectoryError(root)
        for path in sorted(root.rglob('*')):
            if path.is_file() and path.suffix.lower() in VECTOR_SUFFIXES:
                paths.append(path.resolve())
                if len(paths) > max_files:
                    raise ValueError(f'vector discovery exceeded max_files={max_files}')
    unique = list(dict.fromkeys(paths))
    if not unique:
        raise ValueError('no vector files were supplied or discovered')
    return unique

def _source_crs(collection: Any) -> CRS:
    value = collection.crs_wkt or collection.crs
    if not value:
        raise ValueError(f'vector layer {collection.name!r} has no CRS')
    return CRS.from_user_input(value)

def _identifier_values(feature: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for key, value in dict(feature.get('properties') or {}).items():
        if _property_key(key) not in AUTHORITATIVE_HMLR_ID_KEYS or value in (None, ''):
            continue
        cleaned = _clean_id(value)
        if cleaned:
            values.add(cleaned)
    return values

def _candidate_ids(candidate: dict[str, Any]) -> set[str]:
    return {cleaned for field_name in CANDIDATE_INSPIRE_ID_FIELDS if (cleaned := _clean_id(candidate.get(field_name)))}

@dataclass
class CandidateState:
    row: dict[str, Any]
    point: Point
    ids: set[str]
    exact: list[dict[str, Any]] = field(default_factory=list)
    contains: list[dict[str, Any]] = field(default_factory=list)
    files_scanned: int = 0
    features_scanned: int = 0

def _record_match(state: CandidateState, *, feature: dict[str, Any], geometry: Any, source_path: Path, layer_name: str, source_crs: CRS, matched_ids: list[str], kind: str) -> None:
    record = {'source_path': str(source_path), 'source_layer': layer_name, 'source_feature_id': feature.get('id'), 'source_crs': source_crs.to_string(), 'matched_identifier_values': matched_ids, 'geometry_type': geometry.geom_type, 'geometry_area_m2': round(float(geometry.area), 3), 'geometry_wkt_epsg27700': geometry.wkt, 'geometry_geojson_epsg27700': mapping(geometry), 'point_inside': bool(geometry.covers(state.point))}
    (state.exact if kind == 'exact' else state.contains).append(record)

def _dedupe_matches(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    for record in records:
        key = (str(record['geometry_wkt_epsg27700']), tuple(sorted(record.get('matched_identifier_values') or [])))
        source = {'source_path': record.get('source_path'), 'source_layer': record.get('source_layer'), 'source_feature_id': record.get('source_feature_id')}
        if key not in unique:
            copied = dict(record)
            copied['equivalent_duplicate_sources'] = [source]
            unique[key] = copied
        else:
            unique[key]['equivalent_duplicate_sources'].append(source)
    return list(unique.values())

def _blocked(status: str, exact: list[dict[str, Any]], contains: list[dict[str, Any]]) -> dict[str, Any]:
    return {'status': status, 'match_method': None, 'exact_match_count': len(exact), 'containment_match_count': len(contains), 'matches': exact if exact else contains}

def _choose_match(state: CandidateState) -> dict[str, Any]:
    exact = _dedupe_matches(state.exact)
    contains = _dedupe_matches(state.contains)
    if exact:
        exact_covering = [record for record in exact if record['point_inside']]
        if len(exact_covering) == 1:
            chosen = exact_covering[0]
            method = 'EXACT_OFFICIAL_ID_PLUS_POINT_CONSISTENCY' if len(exact) == 1 else 'EXACT_OFFICIAL_ID_PLUS_POINT_DISAMBIGUATION'
        elif not exact_covering:
            return _blocked('EXACT_IDENTIFIER_COORDINATE_MISMATCH', exact, contains)
        else:
            return _blocked('AMBIGUOUS_EXACT_IDENTIFIER_MATCH', exact, contains)
    elif len(contains) == 1:
        chosen = contains[0]
        method = 'UNIQUE_POINT_IN_POLYGON'
    elif len(contains) > 1:
        return _blocked('AMBIGUOUS_POINT_IN_POLYGON_MATCH', exact, contains)
    else:
        return _blocked('NO_MATCH', exact, contains)
    return {'status': 'MATCHED', 'match_method': method, 'exact_match_count': len(exact), 'containment_match_count': len(contains), 'match': chosen}

def _scan_vector(path: Path, states: list[CandidateState]) -> dict[str, Any]:
    file_feature_count = 0
    layer_summaries = []
    for layer_name in fiona.listlayers(path):
        with fiona.open(path, layer=layer_name) as collection:
            source_crs = _source_crs(collection)
            transformer = None
            if source_crs != TARGET_CRS:
                transformer = Transformer.from_crs(source_crs, TARGET_CRS, always_xy=True, allow_ballpark=False, only_best=True)
            layer_count = 0
            for feature_obj in collection:
                feature = dict(feature_obj)
                layer_count += 1
                file_feature_count += 1
                identifier_values = _identifier_values(feature)
                exact_indexes = [i for i, state in enumerate(states) if state.ids & identifier_values]
                geometry_value = feature.get('geometry')
                if geometry_value is None:
                    continue
                bounds = feature_obj.get('bbox')
                if bounds and len(bounds) == 4 and (transformer is None):
                    minx, miny, maxx, maxy = map(float, bounds)
                    spatial_indexes = [i for i, state in enumerate(states) if minx <= state.point.x <= maxx and miny <= state.point.y <= maxy]
                else:
                    spatial_indexes = list(range(len(states)))
                interested = set(exact_indexes) | set(spatial_indexes)
                if not interested:
                    continue
                geometry = shape(geometry_value)
                if transformer is not None:
                    geometry = shapely_transform(transformer.transform, geometry)
                if not geometry.is_valid:
                    geometry = make_valid(geometry)
                if geometry.is_empty or geometry.geom_type not in {'Polygon', 'MultiPolygon'} or (not math.isfinite(float(geometry.area))) or (geometry.area <= 0):
                    continue
                for index in interested:
                    state = states[index]
                    state.features_scanned += 1
                    matched_ids = sorted(state.ids & identifier_values)
                    if matched_ids:
                        _record_match(state, feature=feature, geometry=geometry, source_path=path, layer_name=layer_name, source_crs=source_crs, matched_ids=matched_ids, kind='exact')
                    elif geometry.covers(state.point):
                        _record_match(state, feature=feature, geometry=geometry, source_path=path, layer_name=layer_name, source_crs=source_crs, matched_ids=[], kind='contains')
            layer_summaries.append({'layer': layer_name, 'features': layer_count, 'crs': source_crs.to_string()})
    for state in states:
        state.files_scanned += 1
    stat = path.stat()
    return {'path': str(path), 'size_bytes': stat.st_size, 'sha256': _file_sha256(path), 'feature_count': file_feature_count, 'layers': layer_summaries}

def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f'.{path.name}_', suffix='.json.tmp', dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with temp.open('w', encoding='utf-8', newline='\n') as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    except Exception:
        temp.unlink(missing_ok=True)
        raise

def main(argv: Iterable[str] | None=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--starter-manifest', type=Path, required=True)
    parser.add_argument('--vector', type=Path, action='append', default=[])
    parser.add_argument('--vector-root', type=Path, action='append', default=[])
    parser.add_argument('--max-files', type=int, default=200)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    candidates = _load_candidates(args.starter_manifest)
    vectors = _resolve_vectors(args.vector, args.vector_root, args.max_files)
    states = [CandidateState(row=row, point=Point(row['bng_easting'], row['bng_northing']), ids=_candidate_ids(row)) for row in candidates]
    source_files = [_scan_vector(path, states) for path in vectors]
    results = []
    for state in states:
        results.append({'row_no': state.row['row_no'], 'parcel_id': state.row['parcel_id'], 'bng_easting': state.row['bng_easting'], 'bng_northing': state.row['bng_northing'], 'candidate_official_ids': sorted(state.ids), 'ignored_non_inspire_candidate_fields': list(IGNORED_NON_INSPIRE_ID_FIELDS), 'files_scanned': state.files_scanned, 'candidate_features_examined': state.features_scanned, **_choose_match(state), 'nearest_polygon_fill_used': False, 'measured_value_promoted': False})
    matched = sum((result['status'] == 'MATCHED' for result in results))
    payload = {'schema_version': 3, 'slot_id': 'height_difference_3', 'target_crs': 'EPSG:27700', 'candidate_count': len(results), 'matched_candidate_count': matched, 'blocked_candidate_count': len(results) - matched, 'source_files': source_files, 'results': results, 'matching_priority': ['exact_authoritative_hmlr_property_identifier_plus_point_consistency', 'unique_point_in_polygon'], 'exact_identifier_source_policy': 'HMLR_INSPIRE_FIELDS_ONLY_NO_TITLE_NUMBER_NO_UPRN_NO_FIONA_SEQUENCE_ID', 'candidate_inspire_id_fields': list(CANDIDATE_INSPIRE_ID_FIELDS), 'ignored_non_inspire_id_fields': list(IGNORED_NON_INSPIRE_ID_FIELDS), 'authoritative_hmlr_identifier_property_keys': sorted(AUTHORITATIVE_HMLR_ID_KEYS), 'equivalent_boundary_duplicate_geometry_deduplication': True, 'exact_identifier_requires_point_consistency': True, 'strict_non_ballpark_crs_transform': True, 'fiona_feature_id_used_for_matching': False, 'nearest_polygon_fill_forbidden': True, 'manifest_atomic_materialization': True, 'measurement_values_written': 0, 'final_ready': False, 'fake_data': False, 'db_write': False, 'migration': False, 'production_deploy': False}
    _write_json(args.output, payload)
    print(json.dumps({'ok': True, 'candidates': len(results), 'matched': matched}))
    return 0 if matched == len(results) else 2
if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': f'{type(exc).__name__}: {exc}'}), file=sys.stderr)
        raise

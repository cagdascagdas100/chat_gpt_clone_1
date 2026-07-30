#!/usr/bin/env python3
"""Execute the official HMLR + EA DTM + OS Terrain 50 measurement chain fail-closed.

Every successful subprocess is followed by schema, identity and hash validation of
its declared outputs. The execution receipt is atomically written. Exact HMLR
INSPIRE identity is required unless an explicit diagnostic-only fallback flag is
provided; the canonical runner never uses that fallback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

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

def _run(command: list[str], cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    try:
        process = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout_seconds)
        return {'command': command, 'exit_code': process.returncode, 'timed_out': False, 'stdout': process.stdout[-12000:], 'stderr': process.stderr[-12000:]}
    except subprocess.TimeoutExpired as exc:
        return {'command': command, 'exit_code': 124, 'timed_out': True, 'stdout': str(exc.stdout or '')[-12000:], 'stderr': str(exc.stderr or '')[-12000:]}

def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError(f'expected JSON object: {path}')
    return value

def _clean_id(value: Any) -> str:
    return re.sub('\\s+', '', str(value or '').strip()).casefold()

def _starter_by_row(path: Path) -> dict[int, dict[str, Any]]:
    payload = _load_json(path)
    candidates = payload.get('candidates')
    if not isinstance(candidates, list) or not candidates:
        raise ValueError('starter manifest has no candidates')
    result: dict[int, dict[str, Any]] = {}
    parcels: set[str] = set()
    for raw in candidates:
        if not isinstance(raw, dict):
            raise ValueError('starter candidate is not an object')
        row_no = int(raw['row_no'])
        parcel_id = str(raw['parcel_id']).strip()
        if row_no in result or parcel_id in parcels:
            raise ValueError('duplicate starter row_no or parcel_id')
        result[row_no] = dict(raw)
        parcels.add(parcel_id)
    return result

def _exact_hmlr_matches_only(matches_path: Path, starter_path: Path) -> tuple[bool, list[dict[str, Any]]]:
    payload = _load_json(matches_path)
    results = payload.get('results')
    if not isinstance(results, list) or not results:
        raise ValueError('HMLR match manifest has no results')
    candidates = _starter_by_row(starter_path)
    if len(results) != len(candidates):
        raise ValueError('HMLR match result count differs from starter count')
    failures: list[dict[str, Any]] = []
    seen: set[int] = set()
    for row in results:
        row_no = int(row.get('row_no'))
        if row_no in seen:
            raise ValueError(f'duplicate HMLR match row: {row_no}')
        seen.add(row_no)
        method = str(row.get('match_method') or '')
        status = str(row.get('status') or '')
        candidate = candidates.get(row_no) or {}
        expected_values = {_clean_id(candidate.get(name)) for name in ('hmlr_inspire_id', 'national_cadastral_reference', 'parcel_registry_id') if _clean_id(candidate.get(name))}
        match = row.get('match') if isinstance(row.get('match'), dict) else {}
        matched_values = {_clean_id(value) for value in match.get('matched_identifier_values') or [] if _clean_id(value)}
        exact_value_matched = bool(expected_values & matched_values)
        point_inside = match.get('point_inside') is True
        if status != 'MATCHED' or not method.startswith('EXACT_OFFICIAL_ID') or (not exact_value_matched) or (not point_inside):
            failures.append({'row_no': row_no, 'parcel_id': row.get('parcel_id'), 'status': status, 'match_method': method or None, 'expected_inspire_values': sorted(expected_values), 'matched_identifier_values': sorted(matched_values), 'point_inside': point_inside})
    return (not failures, failures)

def _validate_hmlr_source(path: Path, candidate_count: int) -> dict[str, Any]:
    payload = _load_json(path)
    if payload.get('slot_id') != 'height_difference_3':
        raise ValueError('HMLR source slot mismatch')
    if payload.get('status') != 'READY':
        raise ValueError('HMLR source manifest is not READY')
    if int(payload.get('candidate_count', -1)) != candidate_count:
        raise ValueError('HMLR source candidate count mismatch')
    if int(payload.get('prepared_authority_count', -1)) < 1:
        raise ValueError('HMLR source has no prepared authority')
    if payload.get('atomic_download_materialization') is not True:
        raise ValueError('HMLR source atomic download flag missing')
    if payload.get('archive_tree_transactional_publish') is not True:
        raise ValueError('HMLR source transactional vector-tree flag missing')
    return payload

def _validate_matches(path: Path, candidate_count: int) -> dict[str, Any]:
    payload = _load_json(path)
    results = payload.get('results')
    if not isinstance(results, list) or len(results) != candidate_count:
        raise ValueError('HMLR match result count mismatch')
    if int(payload.get('matched_candidate_count', -1)) != candidate_count:
        raise ValueError('not all HMLR candidates are matched')
    if payload.get('exact_identifier_requires_point_consistency') is not True:
        raise ValueError('HMLR point-consistency flag missing')
    if payload.get('manifest_atomic_materialization') is not True:
        raise ValueError('HMLR match atomic output flag missing')
    return payload

def _validate_ea_source(path: Path, candidate_count: int) -> dict[str, Any]:
    payload = _load_json(path)
    if payload.get('slot_id') != 'height_difference_3':
        raise ValueError('EA source slot mismatch')
    if payload.get('status') != 'READY':
        raise ValueError('EA source manifest is not READY')
    if int(payload.get('candidate_count', -1)) != candidate_count:
        raise ValueError('EA source candidate count mismatch')
    if payload.get('manifest_atomic_materialization') is not True:
        raise ValueError('EA source atomic manifest flag missing')
    return payload

def _validate_terrain_source(path: Path, candidate_count: int) -> dict[str, Any]:
    payload = _load_json(path)
    if payload.get('slot_id') != 'height_difference_3':
        raise ValueError('Terrain50 source slot mismatch')
    if payload.get('status') != 'READY':
        raise ValueError('Terrain50 source manifest is not READY')
    if int(payload.get('candidate_count', -1)) != candidate_count:
        raise ValueError('Terrain50 source candidate count mismatch')
    if payload.get('atomic_tile_materialization') is not True or payload.get('atomic_manifest_materialization') is not True:
        raise ValueError('Terrain50 atomic tile/manifest flag missing')
    return payload

def _validate_measurements(path: Path, candidate_count: int, matches_path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    if payload.get('measurement_contract_version') != 'EA_DTM_POLYGON_P95_P05_OS_T50_SAME_POINT_V2':
        raise ValueError('measurement contract version mismatch')
    if int(payload.get('candidate_count', -1)) != candidate_count:
        raise ValueError('measurement candidate count mismatch')
    if int(payload.get('promoted_measurement_count', -1)) != candidate_count:
        raise ValueError('not all candidate measurements are promoted')
    if payload.get('source_errors_forbid_promotion') is not True:
        raise ValueError('measurement source-error gate missing')
    if payload.get('matched_manifest_sha256') != _sha256(matches_path):
        raise ValueError('measurement manifest is not bound to current HMLR matches')
    rows = payload.get('measured_rows')
    if not isinstance(rows, list) or len(rows) != candidate_count:
        raise ValueError('measurement row count mismatch')
    return payload

def _validate_publication(summary_path: Path, geojson_path: Path, measurement_path: Path, candidate_count: int) -> tuple[dict[str, Any], dict[str, Any]]:
    summary = _load_json(summary_path)
    geojson = _load_json(geojson_path)
    measurement_sha = _sha256(measurement_path)
    if summary.get('status') != 'VERIFIED_EXAMPLES_PUBLISHED':
        raise ValueError('website summary is not published')
    if int(summary.get('published_example_count', -1)) != candidate_count:
        raise ValueError('website published row count mismatch')
    if summary.get('measurement_manifest_sha256') != measurement_sha:
        raise ValueError('website summary is not bound to measurement manifest')
    if geojson.get('measurement_manifest_sha256') != measurement_sha:
        raise ValueError('website GeoJSON is not bound to measurement manifest')
    if int(geojson.get('feature_count', -1)) != candidate_count:
        raise ValueError('website GeoJSON feature count mismatch')
    if summary.get('atomic_json_geojson_bundle') is not True:
        raise ValueError('website atomic bundle flag missing')
    return (summary, geojson)

def main(argv: Iterable[str] | None=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--starter-manifest', type=Path, required=True)
    parser.add_argument('--terrain50-source', type=Path, action='append', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--hmlr-download-page', default='https://use-land-property-data.service.gov.uk/datasets/inspire/download')
    parser.add_argument('--ea-wcs-base', default='https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs')
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--stage-timeout', type=int, default=7200)
    parser.add_argument('--maximum-crosscheck-difference-m', type=float, default=8.0)
    parser.add_argument('--require-exact-official-id', action='store_true')
    parser.add_argument('--allow-point-in-polygon-fallback', action='store_true', help='Diagnostic only; canonical execution must not use this flag.')
    args = parser.parse_args(argv)
    if args.stage_timeout < 60:
        raise ValueError('stage-timeout must be at least 60 seconds')
    script_dir = Path(__file__).resolve().parent
    scripts = {'HMLR_SOURCE_PREPARATION': script_dir / '012_download_hmlr_inspire_sources.py', 'HMLR_BOUNDARY_MATCH': script_dir / '008_match_hmlr_inspire_gml.py', 'EA_DTM_WCS_PREPARATION': script_dir / '013_fetch_ea_dtm_wcs_for_matches.py', 'TERRAIN50_SOURCE_PREPARATION': script_dir / '014_prepare_os_terrain50_tiles.py', 'EA_DTM_AND_TERRAIN50_SAMPLE': script_dir / '009_sample_ea_dtm_and_os_terrain50.py', 'WEBSITE_PUBLICATION': script_dir / '010_publish_verified_height_difference_examples.py'}
    for path in scripts.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    starter = args.starter_manifest.resolve()
    candidates = _starter_by_row(starter)
    candidate_count = len(candidates)
    output_root = args.output_dir.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    hmlr_source = output_root / 'sources' / 'hmlr_source_manifest.json'
    matches = output_root / 'hmlr_matches.json'
    ea_source = output_root / 'sources' / 'ea_dtm_source_manifest.json'
    terrain_source = output_root / 'sources' / 'terrain50_source_manifest.json'
    measurements = output_root / 'official_measurements.json'
    site_json = output_root / 'verified_examples.json'
    site_geojson = output_root / 'verified_examples.geojson'
    execution_path = output_root / 'auto_source_pipeline_execution.json'
    commands: list[tuple[str, list[str]]] = [('HMLR_SOURCE_PREPARATION', [sys.executable, str(scripts['HMLR_SOURCE_PREPARATION']), '--starter-manifest', str(starter), '--output-dir', str(output_root / 'sources'), '--download-page', args.hmlr_download_page, '--timeout', str(args.timeout)]), ('HMLR_BOUNDARY_MATCH', [sys.executable, str(scripts['HMLR_BOUNDARY_MATCH']), '--starter-manifest', str(starter), '--vector-root', str(output_root / 'sources' / 'hmlr'), '--output', str(matches)]), ('EA_DTM_WCS_PREPARATION', [sys.executable, str(scripts['EA_DTM_WCS_PREPARATION']), '--matched-manifest', str(matches), '--output-dir', str(output_root / 'sources'), '--wcs-base', args.ea_wcs_base, '--timeout', str(args.timeout)])]
    terrain_command = [sys.executable, str(scripts['TERRAIN50_SOURCE_PREPARATION']), '--matched-manifest', str(matches), '--output-dir', str(output_root / 'sources')]
    for source in args.terrain50_source:
        terrain_command.extend(['--source', str(source.resolve())])
    commands.append(('TERRAIN50_SOURCE_PREPARATION', terrain_command))
    commands.extend([('EA_DTM_AND_TERRAIN50_SAMPLE', [sys.executable, str(scripts['EA_DTM_AND_TERRAIN50_SAMPLE']), '--matched-manifest', str(matches), '--ea-root', str(output_root / 'sources' / 'ea_dtm'), '--terrain50-root', str(output_root / 'sources' / 'terrain50'), '--max-crosscheck-difference-m', str(args.maximum_crosscheck_difference_m), '--output', str(measurements)]), ('WEBSITE_PUBLICATION', [sys.executable, str(scripts['WEBSITE_PUBLICATION']), '--measurement-manifest', str(measurements), '--output-json', str(site_json), '--output-geojson', str(site_geojson)])])
    validators = {'HMLR_SOURCE_PREPARATION': lambda: _validate_hmlr_source(hmlr_source, candidate_count), 'HMLR_BOUNDARY_MATCH': lambda: _validate_matches(matches, candidate_count), 'EA_DTM_WCS_PREPARATION': lambda: _validate_ea_source(ea_source, candidate_count), 'TERRAIN50_SOURCE_PREPARATION': lambda: _validate_terrain_source(terrain_source, candidate_count), 'EA_DTM_AND_TERRAIN50_SAMPLE': lambda: _validate_measurements(measurements, candidate_count, matches), 'WEBSITE_PUBLICATION': lambda: _validate_publication(site_json, site_geojson, measurements, candidate_count)}
    stages: list[dict[str, Any]] = []
    status = 'BLOCKED'
    exact_required = not args.allow_point_in_polygon_fallback
    exact_hmlr_gate = {'required': exact_required, 'checked': False, 'passed': None, 'failures': []}
    output_hashes: dict[str, str] = {}
    for name, command in commands:
        result = _run(command, script_dir, args.stage_timeout)
        result['stage'] = name
        stages.append(result)
        if result['exit_code'] != 0:
            status = f'BLOCKED_{name}'
            break
        try:
            validators[name]()
            result['output_validation'] = 'PASS'
        except Exception as exc:
            result['output_validation'] = 'FAIL'
            result['output_validation_error'] = f'{type(exc).__name__}: {exc}'
            status = f'BLOCKED_{name}_OUTPUT_VALIDATION'
            break
        if name == 'HMLR_BOUNDARY_MATCH' and exact_required:
            exact_hmlr_gate['checked'] = True
            passed, failures = _exact_hmlr_matches_only(matches, starter)
            exact_hmlr_gate['passed'] = passed
            exact_hmlr_gate['failures'] = failures
            if not passed:
                status = 'BLOCKED_HMLR_EXACT_INSPIRE_ID_POINT_CONSISTENCY_REQUIRED'
                break
    else:
        status = 'THREE_REAL_PARCELS_OFFICIAL_SOURCES_PREPARED_MEASURED_AND_PUBLISHED'
    for label, path in {'starter_manifest': starter, 'hmlr_source_manifest': hmlr_source, 'hmlr_matches': matches, 'ea_source_manifest': ea_source, 'terrain50_source_manifest': terrain_source, 'official_measurements': measurements, 'website_json': site_json, 'website_geojson': site_geojson}.items():
        if path.is_file():
            output_hashes[label] = _sha256(path)
    execution = {'schema_version': 4, 'slot_id': 'height_difference_3', 'single_shared_runner_only': True, 'new_runner_created': False, 'parallel_runner_used': False, 'starter_manifest': str(starter), 'starter_manifest_sha256': _sha256(starter), 'status': status, 'stages': stages, 'stage_timeout_seconds': args.stage_timeout, 'exact_hmlr_official_id_gate': exact_hmlr_gate, 'output_hashes': output_hashes, 'outputs': {'hmlr_source_manifest': str(hmlr_source), 'hmlr_matches': str(matches), 'ea_source_manifest': str(ea_source), 'terrain50_source_manifest': str(terrain_source), 'official_measurements': str(measurements), 'website_json': str(site_json), 'website_geojson': str(site_geojson)}, 'subprocess_success_requires_output_validation': True, 'atomic_execution_receipt': True, 'nearest_fill_forbidden': True, 'final_ready': False, 'fake_data': False, 'db_write': False, 'migration': False, 'production_deploy': False}
    _atomic_json(execution_path, execution)
    print(json.dumps({'ok': status.startswith('THREE_REAL'), 'status': status, 'execution': str(execution_path), 'execution_sha256': _sha256(execution_path)}))
    return 0 if status.startswith('THREE_REAL') else 2
if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': f'{type(exc).__name__}: {exc}'}), file=sys.stderr)
        raise

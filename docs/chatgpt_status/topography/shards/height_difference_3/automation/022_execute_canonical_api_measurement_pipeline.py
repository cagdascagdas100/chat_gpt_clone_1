#!/usr/bin/env python3
"""Run and verify the complete canonical-to-publication chain on the existing runner.

Subprocess exit code alone is never sufficient. Each stage is bound to its current
inputs by counts and SHA-256 values, and the execution receipt is atomically
materialized. Exact HMLR INSPIRE identity is mandatory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
CANONICAL_COUNT = 92283
ROW_START = 61523
ROW_END = 92283
SHARD_COUNT = ROW_END - ROW_START + 1
FIRST_THREE = [61523, 61524, 61525]

def sha256_file(path: Path, chunk_size: int=1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b''):
            digest.update(chunk)
    return digest.hexdigest()

def atomic_json(path: Path, payload: Any) -> None:
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

def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(value, dict):
        raise ValueError(f'expected JSON object: {path}')
    return value

def run(stage: str, command: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False, timeout=timeout)
        return {'stage': stage, 'command': command, 'exit_code': proc.returncode, 'timed_out': False, 'stdout': proc.stdout[-16000:], 'stderr': proc.stderr[-16000:]}
    except subprocess.TimeoutExpired as exc:
        return {'stage': stage, 'command': command, 'exit_code': 124, 'timed_out': True, 'stdout': str(exc.stdout or '')[-16000:], 'stderr': str(exc.stderr or '')[-16000:]}

def validate_jsonl_shard(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    count = 0
    first_row = None
    last_row = None
    previous = ROW_START - 1
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for raw in handle:
            digest.update(raw)
            if not raw.strip():
                raise ValueError('canonical shard contains blank line')
            row = json.loads(raw)
            if not isinstance(row, dict):
                raise ValueError('canonical shard row is not an object')
            row_no = int(row['row_no'])
            if row_no != previous + 1:
                raise ValueError(f'canonical shard is not contiguous: previous={previous} current={row_no}')
            if count == 0:
                first_row = row_no
            previous = row_no
            last_row = row_no
            count += 1
    if count != SHARD_COUNT or first_row != ROW_START or last_row != ROW_END:
        raise ValueError(f'canonical shard range mismatch count={count} first={first_row} last={last_row}')
    return {'rows': count, 'first_row': first_row, 'last_row': last_row, 'sha256': digest.hexdigest()}

def validate_canonical_stage(source: Path, canonical_out: Path) -> dict[str, Any]:
    manifest_path = canonical_out / 'stream_extraction_manifest.json'
    shard_path = canonical_out / f'canonical_shard_{ROW_START}_{ROW_END}.jsonl'
    first_three_path = canonical_out / 'first_three_canonical_candidates.json'
    starter_path = canonical_out / 'starter_three_query_manifest.json'
    manifest = load_json(manifest_path)
    if int(manifest.get('canonical_features_validated', -1)) != CANONICAL_COUNT:
        raise ValueError('canonical feature count mismatch')
    if int(manifest.get('shard_rows_exported', -1)) != SHARD_COUNT:
        raise ValueError('canonical shard count mismatch')
    if [int(v) for v in manifest.get('first_three_explicit_rows', [])] != FIRST_THREE:
        raise ValueError('canonical first-three rows mismatch')
    if manifest.get('source_sha256') != sha256_file(source):
        raise ValueError('canonical manifest source SHA mismatch')
    if manifest.get('row_order_inference_used') is not False:
        raise ValueError('canonical row-order inference must be false')
    shard = validate_jsonl_shard(shard_path)
    first_three = load_json(first_three_path)
    starter = load_json(starter_path)
    for label, payload in (('first_three', first_three), ('starter', starter)):
        candidates = payload.get('candidates')
        if not isinstance(candidates, list) or len(candidates) != 3:
            raise ValueError(f'{label} manifest does not contain exactly three candidates')
        if [int(row['row_no']) for row in candidates] != FIRST_THREE:
            raise ValueError(f'{label} rows mismatch')
        if len({str(row['parcel_id']) for row in candidates}) != 3:
            raise ValueError(f'{label} parcel identities are not unique')
        if any((not str(row.get('hmlr_inspire_id') or '').strip() for row in candidates)):
            raise ValueError(f'{label} candidate lacks HMLR INSPIRE ID')
    return {'manifest_path': str(manifest_path), 'manifest_sha256': sha256_file(manifest_path), 'shard_path': str(shard_path), 'shard': shard, 'first_three_sha256': sha256_file(first_three_path), 'starter_sha256': sha256_file(starter_path)}

def validate_terrain_stage(terrain_out: Path, archive: Path) -> dict[str, Any]:
    provenance_path = terrain_out / 'terrain50_official_api_provenance.json'
    provenance = load_json(provenance_path)
    if provenance.get('official_catalog_verified') is not True:
        raise ValueError('Terrain50 official catalogue verification is required')
    if provenance.get('national_tile_count_exact_match') is not True:
        raise ValueError('Terrain50 national tile count is not exact')
    if int(provenance.get('ascii_tile_count', -1)) != 2858:
        raise ValueError('Terrain50 tile count must be 2,858')
    if provenance.get('archive_sha256') != sha256_file(archive):
        raise ValueError('Terrain50 archive SHA mismatch')
    if int(provenance.get('archive_size_bytes', -1)) != archive.stat().st_size:
        raise ValueError('Terrain50 archive size mismatch')
    if provenance.get('validation_before_canonical_replace') is not True:
        raise ValueError('Terrain50 validation-before-replace flag missing')
    if provenance.get('atomic_provenance_materialization') is not True:
        raise ValueError('Terrain50 atomic provenance flag missing')
    return {'provenance_path': str(provenance_path), 'provenance_sha256': sha256_file(provenance_path), 'archive_path': str(archive), 'archive_sha256': sha256_file(archive)}

def validate_measurement_stage(measurement_out: Path, starter: Path) -> dict[str, Any]:
    execution_path = measurement_out / 'auto_source_pipeline_execution.json'
    measurement_path = measurement_out / 'official_measurements.json'
    verified_json = measurement_out / 'verified_examples.json'
    verified_geojson = measurement_out / 'verified_examples.geojson'
    execution = load_json(execution_path)
    if execution.get('status') != 'THREE_REAL_PARCELS_OFFICIAL_SOURCES_PREPARED_MEASURED_AND_PUBLISHED':
        raise ValueError('measurement pipeline execution is not successful')
    if execution.get('starter_manifest_sha256') != sha256_file(starter):
        raise ValueError('measurement execution is not bound to current starter')
    exact_gate = execution.get('exact_hmlr_official_id_gate')
    if not isinstance(exact_gate, dict) or exact_gate.get('passed') is not True:
        raise ValueError('exact HMLR INSPIRE identity gate did not pass')
    if execution.get('subprocess_success_requires_output_validation') is not True:
        raise ValueError('measurement output-validation flag missing')
    measurement = load_json(measurement_path)
    if int(measurement.get('promoted_measurement_count', -1)) != 3:
        raise ValueError('measurement stage did not promote exactly three rows')
    summary = load_json(verified_json)
    geojson = load_json(verified_geojson)
    measurement_sha = sha256_file(measurement_path)
    if summary.get('measurement_manifest_sha256') != measurement_sha:
        raise ValueError('verified JSON is not bound to measurement manifest')
    if geojson.get('measurement_manifest_sha256') != measurement_sha:
        raise ValueError('verified GeoJSON is not bound to measurement manifest')
    if int(summary.get('published_example_count', -1)) != 3:
        raise ValueError('verified JSON row count mismatch')
    if int(geojson.get('feature_count', -1)) != 3:
        raise ValueError('verified GeoJSON feature count mismatch')
    return {'execution_path': str(execution_path), 'execution_sha256': sha256_file(execution_path), 'measurement_sha256': measurement_sha, 'verified_json_sha256': sha256_file(verified_json), 'verified_geojson_sha256': sha256_file(verified_geojson)}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--security-geojson', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--terrain50-archive', type=Path)
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--stage-timeout', type=int, default=7200)
    parser.add_argument('--script-dir', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--no-network-query-preparer', action='store_true')
    args = parser.parse_args()
    if args.stage_timeout < 60:
        raise ValueError('stage-timeout must be at least 60 seconds')
    script_dir = args.script_dir.resolve()
    scripts = {'extractor': script_dir / '020_stream_extract_security_canonical.py', 'query_preparer': script_dir / '004_prepare_three_real_sample_queries.py', 'terrain_api': script_dir / '021_download_os_terrain50_via_api.py', 'measurement': script_dir / '015_execute_auto_source_and_measurement_pipeline.py'}
    for path in scripts.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    source = args.security_geojson.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    canonical_out = out / 'canonical'
    terrain_out = out / 'terrain50'
    measurement_out = out / 'measurement'
    execution_path = out / 'canonical_api_measurement_execution.json'
    starter = canonical_out / 'starter_three_query_manifest.json'
    stages: list[dict[str, Any]] = []
    validations: dict[str, Any] = {}
    status = 'BLOCKED_CANONICAL_STREAM_EXTRACT_AND_PREPARE_THREE'
    extract_cmd = [sys.executable, str(scripts['extractor']), '--source-geojson', str(source), '--output-dir', str(canonical_out), '--query-preparer', str(scripts['query_preparer'])]
    if args.no_network_query_preparer:
        extract_cmd.append('--no-network')
    stage = run('CANONICAL_STREAM_EXTRACT_AND_PREPARE_THREE', extract_cmd, script_dir, args.stage_timeout)
    stages.append(stage)
    if stage['exit_code'] == 0:
        try:
            validations[stage['stage']] = validate_canonical_stage(source, canonical_out)
            stage['output_validation'] = 'PASS'
        except Exception as exc:
            stage['output_validation'] = 'FAIL'
            stage['output_validation_error'] = f'{type(exc).__name__}: {exc}'
            status = 'BLOCKED_CANONICAL_OUTPUT_VALIDATION'
    terrain_archive: Path | None = None
    if stage.get('output_validation') == 'PASS':
        terrain_cmd = [sys.executable, str(scripts['terrain_api']), '--output-dir', str(terrain_out), '--timeout', str(args.timeout)]
        if args.terrain50_archive:
            terrain_archive = args.terrain50_archive.resolve()
            terrain_cmd += ['--archive', str(terrain_archive)]
        else:
            terrain_archive = terrain_out / 'OS_Terrain50_July_2026_GB_ASCII_Grid.zip'
        terrain_stage = run('OS_TERRAIN50_OFFICIAL_API_ACQUISITION', terrain_cmd, script_dir, args.stage_timeout)
        stages.append(terrain_stage)
        status = 'BLOCKED_OS_TERRAIN50_OFFICIAL_API_ACQUISITION'
        if terrain_stage['exit_code'] == 0 and terrain_archive is not None:
            try:
                validations[terrain_stage['stage']] = validate_terrain_stage(terrain_out, terrain_archive)
                terrain_stage['output_validation'] = 'PASS'
            except Exception as exc:
                terrain_stage['output_validation'] = 'FAIL'
                terrain_stage['output_validation_error'] = f'{type(exc).__name__}: {exc}'
                status = 'BLOCKED_TERRAIN50_OUTPUT_VALIDATION'
    if len(stages) == 2 and stages[-1].get('output_validation') == 'PASS':
        measure_cmd = [sys.executable, str(scripts['measurement']), '--starter-manifest', str(starter), '--terrain50-source', str(terrain_archive), '--output-dir', str(measurement_out), '--timeout', str(args.timeout), '--stage-timeout', str(args.stage_timeout), '--require-exact-official-id']
        measure_stage = run('OFFICIAL_HMLR_EA_OS_MEASURE_AND_PUBLISH', measure_cmd, script_dir, args.stage_timeout)
        stages.append(measure_stage)
        status = 'BLOCKED_OFFICIAL_HMLR_EA_OS_MEASURE_AND_PUBLISH'
        if measure_stage['exit_code'] == 0:
            try:
                validations[measure_stage['stage']] = validate_measurement_stage(measurement_out, starter)
                measure_stage['output_validation'] = 'PASS'
                status = 'THREE_REAL_SHARD_ROWS_OFFICIAL_CROSSCHECKED_AND_PUBLISHED'
            except Exception as exc:
                measure_stage['output_validation'] = 'FAIL'
                measure_stage['output_validation_error'] = f'{type(exc).__name__}: {exc}'
                status = 'BLOCKED_MEASUREMENT_PUBLICATION_OUTPUT_VALIDATION'
    execution = {'schema_version': 2, 'slot_id': 'height_difference_3', 'single_shared_runner_only': True, 'new_runner_created': False, 'parallel_runner_used': False, 'queue_submission': False, 'security_geojson': str(source), 'security_geojson_sha256': sha256_file(source), 'status': status, 'stages': stages, 'stage_validations': validations, 'stage_timeout_seconds': args.stage_timeout, 'outputs': {'canonical_manifest': str(canonical_out / 'stream_extraction_manifest.json'), 'canonical_shard': str(canonical_out / f'canonical_shard_{ROW_START}_{ROW_END}.jsonl'), 'first_three_candidates': str(canonical_out / 'first_three_canonical_candidates.json'), 'starter_manifest': str(starter), 'terrain50_provenance': str(terrain_out / 'terrain50_official_api_provenance.json'), 'measurement_execution': str(measurement_out / 'auto_source_pipeline_execution.json'), 'verified_json': str(measurement_out / 'verified_examples.json'), 'verified_geojson': str(measurement_out / 'verified_examples.geojson')}, 'subprocess_success_requires_output_validation': True, 'exact_hmlr_inspire_identity_required': True, 'official_terrain50_catalogue_required': True, 'atomic_execution_receipt': True, 'nearest_fill_forbidden': True, 'final_ready': False, 'fake_data': False, 'db_write': False, 'migration': False, 'production_deploy': False}
    atomic_json(execution_path, execution)
    ok = status.startswith('THREE_REAL')
    print(json.dumps({'ok': ok, 'status': status, 'execution': str(execution_path), 'execution_sha256': sha256_file(execution_path)}))
    return 0 if ok else 2
if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': f'{type(exc).__name__}: {exc}'}), file=sys.stderr)
        raise

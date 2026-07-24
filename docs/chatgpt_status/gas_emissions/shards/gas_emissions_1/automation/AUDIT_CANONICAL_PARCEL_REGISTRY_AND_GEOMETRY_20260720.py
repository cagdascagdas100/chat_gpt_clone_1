from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_PARSE_BYTES = 50 * 1024 * 1024
MAX_SAMPLE_BYTES = 512 * 1024
MAX_INSPECTED_FILES = 60


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def tracked_files(root: Path) -> list[str]:
    completed = subprocess.run(
        ['git', '-C', str(root), 'ls-files', '-z'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError('GIT_LS_FILES_FAILED: ' + completed.stderr.decode('utf-8', errors='replace'))
    return [value.decode('utf-8', errors='surrogateescape') for value in completed.stdout.split(b'\0') if value]


def path_score(value: str) -> int:
    lowered = value.casefold()
    score = 0
    for token, weight in (
        ('92283', 12), ('canonical', 10), ('registry', 10), ('parcel', 7),
        ('polygon', 5), ('geometry', 5), ('hmlr', 5), ('inspire', 5),
        ('geojson', 4), ('program_layer_matrix', 2),
    ):
        if token in lowered:
            score += weight
    return score


def text_markers(path: Path) -> dict[str, bool]:
    with path.open('rb') as handle:
        sample = handle.read(MAX_SAMPLE_BYTES).decode('utf-8', errors='replace').casefold()
    return {
        'parcel_id_key': any(token in sample for token in ('"parcel_id"', 'parcel_registry_id', 'hmlr_inspire_id')),
        'geometry_key': any(token in sample for token in ('"geometry"', 'polygon', 'multipolygon', 'wkt')),
        'official_id_key': any(token in sample for token in ('hmlr_inspire_id', 'inspire_id', 'national cadastral', 'title_number')),
    }


def extract_json_rows(payload: Any) -> tuple[list[Any] | None, str | None]:
    if isinstance(payload, list):
        return payload, 'list'
    if not isinstance(payload, dict):
        return None, None
    for key in ('features', 'rows', 'parcels', 'records', 'data'):
        value = payload.get(key)
        if isinstance(value, list):
            return value, key
    return None, None


def row_fields(row: Any) -> tuple[str | None, Any, dict[str, Any]]:
    if not isinstance(row, dict):
        return None, None, {}
    properties = row.get('properties') if isinstance(row.get('properties'), dict) else row
    parcel_id = None
    for key in ('parcel_id', 'parcel_registry_id', 'hmlr_inspire_id', 'inspire_id', 'id'):
        value = properties.get(key)
        if value not in (None, ''):
            parcel_id = str(value)
            break
    geometry = row.get('geometry') if 'geometry' in row else properties.get('geometry')
    return parcel_id, geometry, properties


def parse_candidate(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        'parsed': False,
        'row_container': None,
        'row_count': None,
        'unique_parcel_id_count': None,
        'duplicate_parcel_id_count': None,
        'geometry_row_count': None,
        'sample_rows': [],
        'parse_error': None,
    }
    try:
        suffix = path.suffix.casefold()
        size = path.stat().st_size
        if size > MAX_PARSE_BYTES:
            result['parse_error'] = f'FILE_TOO_LARGE_FOR_BOUNDED_PARSE:{size}'
            return result
        if suffix in ('.json', '.geojson'):
            payload = json.loads(path.read_text(encoding='utf-8-sig'))
            rows, container = extract_json_rows(payload)
            if rows is None:
                result['parse_error'] = 'NO_RECOGNISED_ROW_CONTAINER'
                return result
            ids: list[str] = []
            geometry_count = 0
            samples: list[dict[str, Any]] = []
            for row in rows:
                parcel_id, geometry, properties = row_fields(row)
                if parcel_id is not None:
                    ids.append(parcel_id)
                if geometry not in (None, '', {}):
                    geometry_count += 1
                if len(samples) < 5 and parcel_id is not None:
                    geometry_type = geometry.get('type') if isinstance(geometry, dict) else ('WKT_OR_TEXT' if geometry else None)
                    samples.append({'parcel_id': parcel_id, 'geometry_type': geometry_type, 'authority': properties.get('authority')})
            unique_count = len(set(ids))
            result.update({
                'parsed': True,
                'row_container': container,
                'row_count': len(rows),
                'unique_parcel_id_count': unique_count,
                'duplicate_parcel_id_count': len(ids) - unique_count,
                'geometry_row_count': geometry_count,
                'sample_rows': samples,
            })
            return result
        if suffix == '.csv':
            ids: list[str] = []
            geometry_count = 0
            samples: list[dict[str, Any]] = []
            row_count = 0
            with path.open('r', encoding='utf-8-sig', newline='') as handle:
                reader = csv.DictReader(handle)
                fields = {str(value).casefold(): value for value in (reader.fieldnames or [])}
                id_field = next((fields[key] for key in ('parcel_id', 'parcel_registry_id', 'hmlr_inspire_id', 'inspire_id') if key in fields), None)
                geometry_field = next((fields[key] for key in ('geometry', 'wkt', 'geom') if key in fields), None)
                for row in reader:
                    row_count += 1
                    parcel_id = str(row.get(id_field) or '') if id_field else ''
                    if parcel_id:
                        ids.append(parcel_id)
                    if geometry_field and row.get(geometry_field):
                        geometry_count += 1
                    if len(samples) < 5 and parcel_id:
                        samples.append({'parcel_id': parcel_id, 'geometry_type': 'CSV_GEOMETRY' if geometry_field else None})
            unique_count = len(set(ids))
            result.update({
                'parsed': True,
                'row_container': 'csv',
                'row_count': row_count,
                'unique_parcel_id_count': unique_count,
                'duplicate_parcel_id_count': len(ids) - unique_count,
                'geometry_row_count': geometry_count,
                'sample_rows': samples,
            })
            return result
        result['parse_error'] = 'UNSUPPORTED_BOUNDED_PARSE_FORMAT'
        return result
    except Exception as exc:
        result['parse_error'] = f'{type(exc).__name__}: {exc}'
        return result


def main() -> int:
    root = Path.cwd()
    slot_id = os.environ.get('AAYS_SLOT_ID', '')
    task_id = os.environ.get('AAYS_TASK_ID', '')
    if slot_id != 'gas_emissions_1' or not task_id:
        raise RuntimeError('GAS_EMISSIONS_1_REGISTRY_AUDIT_WRONG_SLOT_CONTEXT')

    extensions = {'.json', '.geojson', '.csv', '.parquet', '.gpkg', '.fgb', '.pmtiles'}
    candidates = []
    for relative in tracked_files(root):
        lowered = relative.casefold()
        path = root / relative
        if path.suffix.casefold() not in extensions:
            continue
        if 'parcel' not in lowered and 'hmlr' not in lowered and 'inspire' not in lowered and '92283' not in lowered:
            continue
        if not path.is_file():
            continue
        candidates.append((path_score(relative), relative, path))
    candidates.sort(key=lambda item: (-item[0], item[1]))

    inspected: list[dict[str, Any]] = []
    verified = None
    for score, relative, path in candidates[:MAX_INSPECTED_FILES]:
        markers = text_markers(path)
        parsed = parse_candidate(path) if markers['parcel_id_key'] else {
            'parsed': False,
            'row_container': None,
            'row_count': None,
            'unique_parcel_id_count': None,
            'duplicate_parcel_id_count': None,
            'geometry_row_count': None,
            'sample_rows': [],
            'parse_error': 'PARCEL_ID_MARKER_NOT_FOUND_IN_BOUNDED_SAMPLE',
        }
        item = {
            'path': relative,
            'path_score': score,
            'size_bytes': path.stat().st_size,
            **markers,
            **parsed,
        }
        item['verified_92283_geometry_registry'] = bool(
            parsed.get('parsed')
            and parsed.get('row_count') == 92283
            and parsed.get('unique_parcel_id_count') == 92283
            and parsed.get('duplicate_parcel_id_count') == 0
            and parsed.get('geometry_row_count') == 92283
        )
        inspected.append(item)
        if item['verified_92283_geometry_registry'] and verified is None:
            verified = item

    status_value = 'PASS_VERIFIED_92283_GEOMETRY_REGISTRY' if verified else 'BLOCKED_NO_VERIFIED_92283_GEOMETRY_REGISTRY'
    payload = {
        'schema_version': 1,
        'slot_id': slot_id,
        'task_id': task_id,
        'parcel_partition': {'start': 1, 'end': 30761, 'count': 30761},
        'status': status_value,
        'generated_at': utc_now(),
        'tracked_candidate_file_count': len(candidates),
        'inspected_file_count': len(inspected),
        'bounded_parse_max_bytes': MAX_PARSE_BYTES,
        'verified_registry_ready': verified is not None,
        'verified_registry': verified,
        'sample_parcels': verified.get('sample_rows', []) if verified else [],
        'sample_parcel_count': len(verified.get('sample_rows', [])) if verified else 0,
        'inspected_candidates': inspected[:25],
        'measured_emission_rows_created': 0,
        'area_proxy_rows_created': 0,
        'data_status': 'no_data' if verified is None else 'registry_only_no_emissions_value',
        'blocker': None if verified else 'CANONICAL_92283_UNIQUE_PARCEL_ID_PLUS_GEOMETRY_FILE_NOT_VERIFIED_IN_BOUNDED_SCAN',
        'next_action': 'Use the verified registry if present; otherwise hydrate or build the canonical parcel registry before any grid or point-source binding.',
        'final_ready': False,
        'product_final_ready': False,
        'fake_data': False,
        'db_write': False,
        'migration': False,
        'production_deploy': False,
    }
    report = root / 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_registry_geometry_preflight_latest.json'
    status = root / 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_registry_geometry_preflight_latest.json'
    write_json(report, payload)
    write_json(status, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

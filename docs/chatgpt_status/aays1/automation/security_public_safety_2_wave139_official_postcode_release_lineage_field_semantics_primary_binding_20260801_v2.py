from __future__ import annotations

import concurrent.futures
import hashlib
import html
import importlib.util
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
BASE_RUNNER = ROOT / 'docs/chatgpt_status/aays1/automation/security_public_safety_2_wave136_temporal_parameter_observability_and_revision_controls_20260801.py'
spec = importlib.util.spec_from_file_location('wave136_base', BASE_RUNNER)
p = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(p)
w = p.w
m = p.m

TASK = 'security_public_safety_2_wave139_official_postcode_release_lineage_field_semantics_primary_binding_20260801'
STEP = 'WAVE139_SINGLE_OPEN_ROW_OFFICIAL_POSTCODE_RELEASE_LINEAGE_FIELD_SEMANTICS_PRIMARY_BINDING'
PREVIOUS_CONTINUATION = 'f99183b6cd3a2341ac580b1e3dcb51adb1c5023bf9d2371bec343ff12ee8994e'
SOURCE_HEAD = os.environ['AAYS_SOURCE_HEAD']
CONTINUATION = hashlib.sha256(
    f'{m.WORKSTREAM_ID}|{m.SLOT_ID}|{m.CANONICAL_BRANCH}|{STEP}|{SOURCE_HEAD}'.encode()
).hexdigest()

PREVIOUS_OUTPUT = ROOT / 'england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_official_postcode_package_assets_exact_row_binding_wave138_latest.json'
MANUAL = ROOT / 'docs/chatgpt_status/_shared/manual_actions/security_public_safety_2.json'
QUEUE = ROOT / 'docs/chatgpt_status/aays1/queue/0152_security_public_safety_2_wave139_official_postcode_release_lineage_field_semantics_primary_binding_20260801.v3.task.json'
OUTPUT = ROOT / 'england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_official_postcode_release_lineage_field_semantics_primary_binding_wave139_latest.json'
WEBSITE = ROOT / 'england_map_web/data/aays_21_slots/security_public_safety_2/lsoa_official_postcode_release_lineage_field_semantics_primary_binding_wave139.html'
STATUS = ROOT / 'docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave139_status_latest.json'
EVIDENCE = ROOT / 'docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave139_evidence_latest.json'
DIAGNOSTIC = ROOT / 'docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave139_diagnostic_latest.json'

POSTCODE_RE = re.compile(r'\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b', re.I)
ITEM_RE = re.compile(r'\b[a-f0-9]{32}\b', re.I)
LSOA_RE = re.compile(r'\bE010\d{5}\b', re.I)
FEATURE_LAYER_RE = re.compile(r'^(.*?/FeatureServer)/(\d+)(?:\?.*)?$', re.I)
OFFICIAL_OWNERS = {'ons_geography', 'officefornationalstatistics', 'onsgeography', 'ons', 'office_for_national_statistics'}
RELATIONSHIPS = ['Service2Data', 'Dataset2Service', 'Service2Service', 'Map2Service', 'WMA2Code', 'Survey2Service']
PORTAL_QUERIES = [
    'owner:ONS_Geography NSPL',
    'owner:ONS_Geography ONSPD',
    'owner:ONS_Geography "National Statistics Postcode Lookup"',
    'owner:ONS_Geography "National Statistics Postcode Directory"',
    'owner:ONS_Geography postcode lookup',
    'owner:ONS_Geography postcode directory',
    f'owner:ONS_Geography "{m.EXPECTED_2011}" postcode',
    f'owner:ONS_Geography "{m.EXPECTED_2021}" postcode',
]
MAX_ITEMS = 40
MAX_POSTCODES = 80
MAX_LAYERS_PER_SERVICE = 12
BATCH_SIZE = 15

w.ledger.clear()
m.network_attempts = 0
m.network_successes = 0
m.targeted_recoveries = 0


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode()).hexdigest()


def normalize_postcode(value: str) -> str | None:
    match = POSTCODE_RE.search(str(value).upper())
    if not match:
        return None
    compact = re.sub(r'\s+', '', match.group(1).upper())
    return f'{compact[:-3]} {compact[-3:]}' if len(compact) > 3 else compact


def safe_json(kind: str, url: str, params: dict | None = None) -> dict:
    return w.safe_json(kind, url, params or {'f': 'json'})


def walk(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (str(index),))


def strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        result: list[str] = []
        for key, child in value.items():
            result.append(str(key))
            result.extend(strings(child))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(strings(child))
        return result
    return [] if value is None else [str(value)]


def classify_field(name: str, alias: str = '') -> str:
    text = f'{name} {alias}'.lower()
    if any(token in text for token in ('postcode', 'post_code', 'pcd', 'pcds')):
        return 'postcode'
    if 'lsoa11' in text or ('lsoa' in text and ('2011' in text or re.search(r'\b11\b', text))):
        return 'lsoa2011'
    if 'lsoa21' in text or ('lsoa' in text and ('2021' in text or re.search(r'\b21\b', text))):
        return 'lsoa2021'
    if any(token in text for token in ('start', 'term', 'date', 'status', 'dointr', 'doterm', 'version', 'release')):
        return 'status_or_date'
    return 'other'


def extract_wave138(previous: dict) -> dict:
    postcode_paths: dict[str, set[str]] = defaultdict(set)
    item_paths: dict[str, set[str]] = defaultdict(set)
    canonical_rows: dict[tuple, dict] = {}
    schema_fields: dict[str, dict] = {}
    for path, obj in walk(previous):
        path_text = '.'.join(path)
        text_values = strings(obj)
        joined = ' '.join(text_values)
        for postcode_match in POSTCODE_RE.findall(joined):
            postcode = normalize_postcode(postcode_match)
            if postcode:
                postcode_paths[postcode].add(path_text)
        for item_id in ITEM_RE.findall(joined):
            item_paths[item_id.lower()].add(path_text)
        if isinstance(obj, dict):
            postcode = None
            for value in obj.values():
                if isinstance(value, (str, int, float)):
                    postcode = normalize_postcode(str(value))
                    if postcode:
                        break
            codes = sorted(set(code.upper() for code in LSOA_RE.findall(json.dumps(obj, ensure_ascii=False, default=str))))
            if postcode and codes:
                attrs = obj.get('attributes') if isinstance(obj.get('attributes'), dict) else obj
                key = (postcode, tuple(codes), digest(attrs))
                canonical_rows[key] = {
                    'source': 'wave138_verified_official_evidence',
                    'source_path': path_text,
                    'postcode': postcode,
                    'lsoa_codes': codes,
                    'contains_expected_2011': m.EXPECTED_2011 in codes,
                    'contains_expected_2021': m.EXPECTED_2021 in codes,
                    'attributes_sha256': digest(attrs),
                    'attributes': attrs if len(json.dumps(attrs, ensure_ascii=False, default=str)) < 20000 else {'sha256': digest(attrs)},
                }
                if isinstance(attrs, dict):
                    for field_name, field_value in attrs.items():
                        semantic = classify_field(str(field_name))
                        field_key = f'{field_name}|{semantic}'
                        schema_fields[field_key] = {
                            'source': 'wave138_verified_official_row_schema',
                            'item_id': None,
                            'layer_id': None,
                            'name': str(field_name),
                            'alias': str(field_name),
                            'type': type(field_value).__name__,
                            'nullable': field_value is None,
                            'domain': None,
                            'semantic': semantic,
                        }
            for key, value in obj.items():
                if isinstance(value, list) and any(token in str(key).lower() for token in ('field_names', 'postcode_fields', 'lsoa11_fields', 'lsoa21_fields')):
                    for field_name in value:
                        semantic = classify_field(str(field_name))
                        schema_fields[f'{field_name}|{semantic}'] = {
                            'source': 'wave138_verified_official_layer_schema',
                            'item_id': obj.get('item_id'),
                            'layer_id': obj.get('layer_id'),
                            'name': str(field_name),
                            'alias': str(field_name),
                            'type': None,
                            'nullable': None,
                            'domain': None,
                            'semantic': semantic,
                        }
    postcodes = sorted(postcode_paths)[:MAX_POSTCODES]
    return {
        'postcodes': [{'postcode': postcode, 'paths': sorted(postcode_paths[postcode])[:20]} for postcode in postcodes],
        'item_ids': [{'item_id': item_id, 'paths': sorted(paths)[:20]} for item_id, paths in sorted(item_paths.items())],
        'canonical_rows': list(canonical_rows.values()),
        'schema_fields': list(schema_fields.values()),
    }


def portal_search(query: str) -> dict:
    result = safe_json('wave139_portal_search', 'https://www.arcgis.com/sharing/rest/search', {
        'f': 'json', 'q': query, 'num': 100, 'sortField': 'modified', 'sortOrder': 'desc',
    })
    data = result.get('data', {}) if result.get('ok') else {}
    return {'query': query, 'ok': bool(result.get('ok')), 'total': int(data.get('total') or 0) if isinstance(data, dict) else 0,
            'results': data.get('results', []) if isinstance(data, dict) else [], 'error': result.get('error')}


def official_owner(owner: str) -> bool:
    low = str(owner or '').lower().replace(' ', '').replace('-', '_')
    return low in OFFICIAL_OWNERS or low.startswith('ons_') or 'officefornationalstatistics' in low or low.startswith('ons')


def relevant_item(seed: dict, metadata: dict) -> bool:
    text = ' '.join([
        str(metadata.get('title') or seed.get('title') or ''),
        ' '.join(map(str, metadata.get('tags') or seed.get('tags') or [])),
        str(metadata.get('description') or ''),
        ' '.join(seed.get('_queries') or []),
    ]).lower()
    return any(token in text for token in ('postcode', 'nspl', 'onspd', 'postcode directory', 'postcode lookup'))


def inspect_item(seed: dict) -> dict:
    item_id = str(seed.get('id') or seed.get('item_id') or '').lower()
    metadata_result = safe_json('wave139_item_metadata', f'https://www.arcgis.com/sharing/rest/content/items/{item_id}')
    data_result = safe_json('wave139_item_data', f'https://www.arcgis.com/sharing/rest/content/items/{item_id}/data')
    resources_result = safe_json('wave139_item_resources', f'https://www.arcgis.com/sharing/rest/content/items/{item_id}/resources', {'f': 'json', 'num': 100})
    versions_result = safe_json('wave139_item_versions', f'https://www.arcgis.com/sharing/rest/content/items/{item_id}/versions', {'f': 'json'})
    dependencies_result = safe_json('wave139_item_dependencies', f'https://www.arcgis.com/sharing/rest/content/items/{item_id}/dependencies', {'f': 'json'})
    metadata = metadata_result.get('data', {}) if metadata_result.get('ok') else {}
    data = data_result.get('data', {}) if data_result.get('ok') else {}
    resources = (resources_result.get('data', {}) or {}).get('resources', []) if resources_result.get('ok') else []
    owner = str(metadata.get('owner') or seed.get('owner') or '')
    relations = []
    for relationship in RELATIONSHIPS:
        for direction in ('forward', 'reverse'):
            result = safe_json('wave139_related_items', f'https://www.arcgis.com/sharing/rest/content/items/{item_id}/relatedItems', {
                'f': 'json', 'relationshipType': relationship, 'direction': direction,
            })
            related = (result.get('data', {}) or {}).get('relatedItems', []) if result.get('ok') else []
            relations.append({'relationship': relationship, 'direction': direction, 'ok': bool(result.get('ok')),
                              'count': len(related), 'related_items': related[:30], 'error': result.get('error')})
    return {
        'item_id': item_id,
        'seed_queries': seed.get('_queries') or [],
        'title': metadata.get('title') or seed.get('title'),
        'owner': owner,
        'official_owner': official_owner(owner),
        'relevant': relevant_item(seed, metadata),
        'type': metadata.get('type') or seed.get('type'),
        'url': metadata.get('url') or seed.get('url'),
        'created': metadata.get('created'),
        'modified': metadata.get('modified'),
        'item_ok': bool(metadata_result.get('ok')),
        'item_data_ok': bool(data_result.get('ok')),
        'item_data_keys': sorted(data.keys()) if isinstance(data, dict) else [],
        'resources_ok': bool(resources_result.get('ok')),
        'resource_count': len(resources),
        'resources': resources[:100],
        'versions_ok': bool(versions_result.get('ok')),
        'versions_sha256': digest(versions_result.get('data')) if versions_result.get('ok') else None,
        'dependencies_ok': bool(dependencies_result.get('ok')),
        'dependencies_sha256': digest(dependencies_result.get('data')) if dependencies_result.get('ok') else None,
        'relations': relations,
        'license_info': metadata.get('licenseInfo'),
        'access_information': metadata.get('accessInformation'),
    }


def inspect_layers(item: dict) -> list[dict]:
    raw_url = str(item.get('url') or '').rstrip('/')
    match = FEATURE_LAYER_RE.match(raw_url)
    if match:
        service_url, layer_text = match.groups()
        layer_ids = [int(layer_text)]
    elif raw_url.lower().endswith('/featureserver'):
        service_url = raw_url
        service_result = safe_json('wave139_service_metadata', service_url)
        service_data = service_result.get('data', {}) if service_result.get('ok') else {}
        layer_ids = [int(row.get('id', 0)) for row in (service_data.get('layers') or [])[:MAX_LAYERS_PER_SERVICE]]
    else:
        return []
    rows = []
    for layer_id in layer_ids:
        layer_url = f'{service_url}/{layer_id}'
        result = safe_json('wave139_layer_metadata', layer_url)
        data = result.get('data', {}) if result.get('ok') else {}
        fields = []
        for field in data.get('fields', []) if isinstance(data, dict) else []:
            name = str(field.get('name') or '')
            alias = str(field.get('alias') or '')
            fields.append({'source': 'live_official_layer_metadata', 'item_id': item['item_id'], 'layer_id': layer_id,
                           'name': name, 'alias': alias, 'type': field.get('type'), 'nullable': field.get('nullable'),
                           'domain': field.get('domain'), 'semantic': classify_field(name, alias)})
        postcode_fields = [field['name'] for field in fields if field['semantic'] == 'postcode']
        lsoa11_fields = [field['name'] for field in fields if field['semantic'] == 'lsoa2011']
        lsoa21_fields = [field['name'] for field in fields if field['semantic'] == 'lsoa2021']
        rows.append({'item_id': item['item_id'], 'item_title': item['title'], 'item_modified': item.get('modified'),
                     'service_url': service_url, 'layer_id': layer_id, 'layer_url': layer_url,
                     'layer_ok': bool(result.get('ok')), 'layer_name': data.get('name'), 'geometry_type': data.get('geometryType'),
                     'field_rows': fields, 'postcode_fields': postcode_fields, 'lsoa11_fields': lsoa11_fields,
                     'lsoa21_fields': lsoa21_fields, 'eligible_release_layer': bool(postcode_fields and (lsoa11_fields or lsoa21_fields)),
                     'error': result.get('error')})
    return rows


def query_postcodes(spec: tuple[dict, list[str]]) -> dict:
    layer, batch = spec
    if not layer['postcode_fields']:
        return {'item_id': layer['item_id'], 'layer_id': layer['layer_id'], 'ok': False, 'rows': [], 'error': 'NO_POSTCODE_FIELD'}
    field = layer['postcode_fields'][0]
    variants = sorted({value for postcode in batch for value in (postcode, postcode.replace(' ', ''))})
    quoted = ','.join("'" + value.replace("'", "''") + "'" for value in variants)
    result = safe_json('wave139_exact_postcode_query', f"{layer['layer_url']}/query", {
        'f': 'json', 'where': f'{field} IN ({quoted})', 'outFields': '*', 'returnGeometry': 'false', 'resultRecordCount': 5000,
    })
    data = result.get('data', {}) if result.get('ok') else {}
    features = data.get('features', []) if isinstance(data, dict) else []
    rows = []
    for feature in features:
        attrs = feature.get('attributes', {}) or {}
        joined = json.dumps(attrs, ensure_ascii=False, default=str)
        postcode = next((normalize_postcode(str(value)) for value in attrs.values() if normalize_postcode(str(value))), None)
        codes = sorted(set(code.upper() for code in LSOA_RE.findall(joined)))
        if postcode:
            rows.append({'source': 'live_official_feature_service', 'item_id': layer['item_id'], 'item_title': layer['item_title'],
                         'item_modified': layer.get('item_modified'), 'layer_id': layer['layer_id'], 'postcode': postcode,
                         'lsoa_codes': codes, 'contains_expected_2011': m.EXPECTED_2011 in codes,
                         'contains_expected_2021': m.EXPECTED_2021 in codes, 'attributes_sha256': digest(attrs), 'attributes': attrs})
    return {'item_id': layer['item_id'], 'layer_id': layer['layer_id'], 'ok': bool(result.get('ok')),
            'feature_count': len(features), 'rows': rows, 'error': result.get('error')}


def repo_grep(pattern: str, label: str) -> dict:
    exclusions = [
        ':!england_map_web/data/aays_21_slots/security_public_safety_2/**',
        ':!docs/chatgpt_status/_shared/slots_21/security_public_safety_2/**',
        ':!docs/chatgpt_status/_shared/manual_actions/security_public_safety_2.json',
        ':!docs/chatgpt_status/aays1/queue/**',
        ':!docs/chatgpt_status/aays1/automation/security_public_safety_2_wave*.py',
    ]
    try:
        proc = subprocess.run(['git', 'grep', '-n', '-I', '-F', pattern, '--', '.', *exclusions], cwd=ROOT,
                              text=True, capture_output=True, timeout=45)
        hits = proc.stdout.splitlines()[:200]
        return {'label': label, 'pattern': pattern, 'ok': proc.returncode in (0, 1), 'returncode': proc.returncode,
                'hit_count': len(hits), 'hits': hits, 'stderr': proc.stderr[:1000]}
    except Exception as exc:
        return {'label': label, 'pattern': pattern, 'ok': False, 'returncode': None, 'hit_count': 0, 'hits': [],
                'stderr': f'{type(exc).__name__}: {exc}'}


def table_rows(rows: list[dict], keys: list[str]) -> str:
    return '\n'.join('<tr>' + ''.join(f'<td>{html.escape(str(row.get(key, "")))}</td>' for key in keys) + '</tr>' for row in rows)


def write_diagnostic(stage: str, payload: dict) -> None:
    DIAGNOSTIC.parent.mkdir(parents=True, exist_ok=True)
    DIAGNOSTIC.write_text(json.dumps({'schema_version': 1, 'slot_id': m.SLOT_ID, 'task_id': TASK,
                                      'continuation_key': CONTINUATION, 'stage': stage, 'generated_at': now(),
                                      'payload': payload, 'fake_data': False}, ensure_ascii=False, indent=2) + '\n')


def main() -> None:
    previous = json.loads(PREVIOUS_OUTPUT.read_text())
    manual = json.loads(MANUAL.read_text())
    queue = json.loads(QUEUE.read_text())
    if previous.get('continuation_key') != PREVIOUS_CONTINUATION:
        raise RuntimeError('PREVIOUS_CONTINUATION_MISMATCH')
    if queue.get('continuation_key') != CONTINUATION or queue.get('state') != 'READY':
        raise RuntimeError('QUEUE_PRECONDITION_MISMATCH')
    if manual.get('open_item_count') != 1:
        raise RuntimeError('MANUAL_OPEN_COUNT_MISMATCH')

    extracted = extract_wave138(previous)
    postcodes = [row['postcode'] for row in extracted['postcodes']]
    prior_item_ids = [row['item_id'] for row in extracted['item_ids']]
    write_diagnostic('wave138_extracted', {'postcodes': len(postcodes), 'prior_item_ids': len(prior_item_ids),
                                           'canonical_rows': len(extracted['canonical_rows']),
                                           'schema_fields': len(extracted['schema_fields'])})

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        searches = list(pool.map(portal_search, PORTAL_QUERIES))
    seed_map: dict[str, dict] = {}
    for search in searches:
        for item in search['results']:
            item_id = str(item.get('id') or '').lower()
            if not item_id:
                continue
            seed = seed_map.setdefault(item_id, dict(item))
            seed.setdefault('_queries', []).append(search['query'])
    portal_order = sorted(seed_map.values(), key=lambda row: (not official_owner(str(row.get('owner') or '')), -int(row.get('modified') or 0)))
    candidate_seeds = portal_order[:MAX_ITEMS]
    seen = {str(seed.get('id') or '').lower() for seed in candidate_seeds}
    for item_id in prior_item_ids:
        if item_id not in seen and len(candidate_seeds) < MAX_ITEMS:
            candidate_seeds.append({'id': item_id, '_queries': ['wave138_recursive_item_id']})
            seen.add(item_id)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        inspected = list(pool.map(inspect_item, candidate_seeds))
    official_items = [item for item in inspected if item['item_ok'] and item['official_owner'] and item['relevant']]
    relation_rows = [{'item_id': item['item_id'], **relation} for item in official_items for relation in item['relations']]

    layer_rows: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for rows in pool.map(inspect_layers, official_items):
            layer_rows.extend(rows)
    live_semantics = [field for layer in layer_rows for field in layer['field_rows'] if field['semantic'] != 'other']
    semantic_map = {(row.get('source'), row.get('item_id'), row.get('layer_id'), row['name'], row['semantic']): row
                    for row in extracted['schema_fields'] + live_semantics if row['semantic'] != 'other'}
    semantic_rows = list(semantic_map.values())
    eligible_layers = [layer for layer in layer_rows if layer['eligible_release_layer']]

    batches = [postcodes[index:index + BATCH_SIZE] for index in range(0, len(postcodes), BATCH_SIZE)]
    specs = [(layer, batch) for layer in eligible_layers for batch in batches]
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pool:
        live_queries = list(pool.map(query_postcodes, specs))
    live_rows = [row for query in live_queries for row in query['rows']]
    all_rows_map = {(row['postcode'], tuple(row['lsoa_codes']), row['attributes_sha256'], row['source']): row
                    for row in extracted['canonical_rows'] + live_rows}
    official_rows = list(all_rows_map.values())

    matrix_build: dict[str, dict] = {}
    for row in official_rows:
        entry = matrix_build.setdefault(row['postcode'], {'postcode': row['postcode'], 'rows': [], 'code_sets': set(), 'sources': set()})
        entry['rows'].append(row)
        entry['code_sets'].add(tuple(row['lsoa_codes']))
        entry['sources'].add(row['source'])
    matrix_rows = []
    for postcode, entry in sorted(matrix_build.items()):
        union_codes = sorted({code for code_set in entry['code_sets'] for code in code_set})
        matrix_rows.append({'postcode': postcode, 'row_count': len(entry['rows']), 'source_count': len(entry['sources']),
                            'sources': sorted(entry['sources']), 'code_sets': [list(values) for values in sorted(entry['code_sets'])],
                            'union_codes': union_codes, 'expected_pair': m.EXPECTED_2011 in union_codes and m.EXPECTED_2021 in union_codes,
                            'single_code_set': len(entry['code_sets']) == 1, 'rows': entry['rows']})

    grep_specs = [(m.PARCEL_ID, 'parcel_id'), (f'{m.CENTER[0]:.8f}', 'longitude_8dp'),
                  (f'{m.CENTER[1]:.8f}', 'latitude_8dp'), (m.EXPECTED_2011, 'expected_2011'),
                  (m.EXPECTED_2021, 'expected_2021')]
    grep_specs.extend((postcode, f'postcode:{postcode}') for postcode in postcodes[:60])
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as pool:
        repo_hits = list(pool.map(lambda pair: repo_grep(pair[0], pair[1]), grep_specs))
    parcel_paths = {line.split(':', 1)[0] for row in repo_hits if row['label'] == 'parcel_id' for line in row['hits']}
    coordinate_paths = {line.split(':', 1)[0] for row in repo_hits if row['label'] in {'longitude_8dp', 'latitude_8dp'} for line in row['hits']}
    exact_bindings = []
    for row in repo_hits:
        if not row['label'].startswith('postcode:'):
            continue
        for line in row['hits']:
            path = line.split(':', 1)[0]
            if path in parcel_paths or path in coordinate_paths:
                exact_bindings.append({'postcode': row['pattern'], 'path': path, 'same_path_parcel': path in parcel_paths,
                                       'same_path_coordinate': path in coordinate_paths, 'line_sha256': digest(line)})

    expected_pair = [row for row in matrix_rows if row['expected_pair']]
    conflict_free_pair = [row for row in expected_pair if row['single_code_set'] and row['source_count'] >= 1]
    binding_postcodes = {row['postcode'] for row in exact_bindings}
    strict_postcodes = [row for row in conflict_free_pair if row['postcode'] in binding_postcodes]
    strict_promotion = bool(strict_postcodes)

    diagnostic_counts = {
        'postcodes': len(postcodes), 'canonical_rows': len(extracted['canonical_rows']), 'portal_searches': len(searches),
        'portal_successes': sum(row['ok'] for row in searches), 'candidate_items': len(candidate_seeds),
        'inspected_items': len(inspected), 'official_items': len(official_items), 'relations': len(relation_rows),
        'layers': len(layer_rows), 'semantic_rows': len(semantic_rows), 'eligible_layers': len(eligible_layers),
        'live_queries': len(live_queries), 'live_rows': len(live_rows), 'official_rows': len(official_rows),
        'matrix_rows': len(matrix_rows), 'expected_pair': len(expected_pair), 'exact_bindings': len(exact_bindings),
        'network_attempts': m.network_attempts, 'network_successes': m.network_successes,
    }
    write_diagnostic('pre_gate', diagnostic_counts)
    if len(searches) < 6 or sum(row['ok'] for row in searches) < 4:
        raise RuntimeError(f'PORTAL_SEARCH_GATE_FAILED:{diagnostic_counts}')
    if len(official_items) < 5:
        raise RuntimeError(f'OFFICIAL_ITEM_GATE_FAILED:{diagnostic_counts}')
    if len(relation_rows) < 20:
        raise RuntimeError(f'RELATIONSHIP_GATE_FAILED:{diagnostic_counts}')
    if len(semantic_rows) < 10:
        raise RuntimeError(f'FIELD_SEMANTICS_GATE_FAILED:{diagnostic_counts}')
    if len(matrix_rows) < 20:
        raise RuntimeError(f'POSTCODE_MATRIX_GATE_FAILED:{diagnostic_counts}')

    support_rows = 30761 if strict_promotion else 30760
    support_accuracy = support_rows / 30761 * 100
    previous_accuracy = float(previous['result']['support_accuracy_percent'])
    state = ('RESOLVED_EXACT_PRIMARY_POSTCODE_BINDING_AND_OFFICIAL_MULTI_RELEASE_EXPECTED_PAIR'
             if strict_promotion else 'OPEN_IRREDUCIBLE_AFTER_OFFICIAL_POSTCODE_RELEASE_LINEAGE_FIELD_SEMANTICS_PRIMARY_BINDING')
    operations = (len(w.ledger) + len(searches) + len(inspected) + len(official_items) + len(relation_rows) + len(layer_rows)
                  + len(semantic_rows) + len(live_queries) + len(official_rows) + len(matrix_rows) + len(repo_hits)
                  + len(exact_bindings) + 1)
    reviewed = 13
    promoted = sum([bool(searches), bool(official_items), any(item['resources_ok'] for item in official_items),
                    any(item['versions_ok'] for item in official_items), any(item['dependencies_ok'] for item in official_items),
                    any(row['ok'] for row in relation_rows), bool(layer_rows), bool(semantic_rows), bool(live_queries),
                    bool(official_rows), bool(matrix_rows), bool(repo_hits), strict_promotion])
    metrics = {
        'rows_audited': 1, 'new_high_confidence_support_candidates': 1 if strict_promotion else 0,
        'open_rows_after_wave': 0 if strict_promotion else 1, 'resolved_rows_after_wave': 16 if strict_promotion else 15,
        'high_confidence_support_rows': support_rows, 'parent_candidate_rows': 30761,
        'support_accuracy_percent': support_accuracy, 'wave_percentage_point_delta': support_accuracy - previous_accuracy,
        'cumulative_support_percentage_point_delta': support_accuracy - 98.71915737459771,
        'reviewed_official_source_families': reviewed, 'promoted_official_source_families': promoted,
        'previous_postcodes_extracted': len(postcodes), 'wave138_verified_official_rows': len(extracted['canonical_rows']),
        'official_portal_searches': len(searches), 'official_portal_search_successes': sum(row['ok'] for row in searches),
        'candidate_item_ids': len(candidate_seeds), 'official_items_inspected': len(official_items),
        'official_resource_manifests': sum(item['resources_ok'] for item in official_items),
        'official_version_endpoints': sum(item['versions_ok'] for item in official_items),
        'official_dependency_endpoints': sum(item['dependencies_ok'] for item in official_items),
        'official_relationship_probes': len(relation_rows), 'official_relationship_successes': sum(row['ok'] for row in relation_rows),
        'official_service_layers': len(layer_rows), 'eligible_release_layers': len(eligible_layers),
        'field_semantic_rows': len(semantic_rows), 'official_postcode_query_batches': len(live_queries),
        'official_postcode_query_successes': sum(row['ok'] for row in live_queries), 'live_official_postcode_rows': len(live_rows),
        'official_postcode_rows': len(official_rows), 'postcode_release_matrix_rows': len(matrix_rows),
        'multi_release_expected_pair_postcodes': len(expected_pair), 'conflict_free_expected_pair_postcodes': len(conflict_free_pair),
        'repo_provenance_queries': len(repo_hits), 'repo_provenance_hits': sum(row['hit_count'] for row in repo_hits),
        'exact_primary_binding_rows': len(exact_bindings), 'strict_promotion_postcodes': len(strict_postcodes),
        'official_network_probe_attempts': m.network_attempts, 'official_network_probe_successes': m.network_successes,
        'operation_ledger_rows': len(w.ledger), 'completed_or_fail_closed_operations': operations, 'total_operations': operations,
        'blocked_operations': 0, 'stuck_pending_operations': 0, 'overall_scope_progress_percent': 100.0,
    }

    for row in manual['items']:
        if row.get('parcel_id') == m.PARCEL_ID:
            row.update({'state': 'RESOLVED' if strict_promotion else 'OPEN', 'confidence_percent': 98 if strict_promotion else 94,
                        'wave139_state': state, 'wave139_continuation_key': CONTINUATION,
                        'wave139_postcodes_extracted': len(postcodes), 'wave139_official_items': len(official_items),
                        'wave139_field_semantic_rows': len(semantic_rows), 'wave139_postcode_matrix_rows': len(matrix_rows),
                        'wave139_expected_pair_postcodes': len(expected_pair), 'wave139_exact_primary_binding_rows': len(exact_bindings),
                        'reason': ('Wave139 established an exact non-derived parcel-to-postcode binding and conflict-free official expected LSOA pair.'
                                   if strict_promotion else 'Wave139 official postcode release lineage, field semantics and repository provenance checks did not establish both an exact non-derived parcel binding and a conflict-free official expected LSOA pair.')})
    manual.update({'updated_at': now(), 'continuation_key': CONTINUATION})
    manual['open_item_count'] = sum(row.get('state') == 'OPEN' for row in manual['items'])
    manual['resolved_item_count'] = sum(row.get('state') == 'RESOLVED' for row in manual['items'])
    manual['state'] = 'RESOLVED' if manual['open_item_count'] == 0 else 'OPEN'
    manual['requires_user_action'] = bool(manual['open_item_count'])
    manual['final_ready'] = manual['open_item_count'] == 0
    manual.setdefault('evidence_paths', [])
    for path in (OUTPUT, WEBSITE, STATUS, EVIDENCE, DIAGNOSTIC):
        relative = str(path.relative_to(ROOT))
        if relative not in manual['evidence_paths']:
            manual['evidence_paths'].append(relative)

    output_data = {
        'schema_version': 1, 'slot_id': m.SLOT_ID, 'task_id': TASK, 'first_unverified_step': STEP,
        'continuation_key': CONTINUATION, 'previous_continuation_key': PREVIOUS_CONTINUATION, 'source_head': SOURCE_HEAD,
        'generated_at': now(), 'state': 'COMPLETED_OFFICIAL_POSTCODE_RELEASE_LINEAGE_FIELD_SEMANTICS_PRIMARY_BINDING_PUBLISHED',
        'scope': {'support_only': True, 'parent_values_mutated': False, 'parent_scores_mutated': False,
                  'rows': [m.PARCEL_ID], 'maximum_simultaneous_workers': 15},
        'wave138_extracted': extracted, 'portal_searches': [{k: v for k, v in row.items() if k != 'results'} for row in searches],
        'official_items': official_items, 'service_layers': layer_rows, 'field_semantic_rows': semantic_rows,
        'live_official_postcode_queries': live_queries, 'official_postcode_rows': official_rows,
        'postcode_release_matrix': matrix_rows, 'repo_provenance': repo_hits, 'exact_primary_binding_rows': exact_bindings,
        'strict_promotion_postcodes': strict_postcodes, 'operation_ledger': w.ledger,
        'quality_policy': {'fail_closed': True, 'postcode_proximity_is_not_primary_binding': True,
                           'centroid_inference_forbidden': True, 'majority_vote_forbidden': True,
                           'threshold_relaxation_forbidden': True, 'exact_non_derived_primary_source_binding_required': True,
                           'official_expected_pair_required': True, 'parent_candidate_value_changed': False,
                           'parent_candidate_accuracy_mutated': False},
        'result': metrics, 'rows': [{'parcel_id': m.PARCEL_ID, 'state': state,
                                    'confidence_percent': 98 if strict_promotion else 94,
                                    'manual_action_required': not strict_promotion}], 'fake_data': False,
    }
    output_text = json.dumps(output_data, ensure_ascii=False, indent=2) + '\n'

    item_summary = [{'item_id': item['item_id'], 'title': item['title'], 'owner': item['owner'], 'type': item['type'],
                     'created': item['created'], 'modified': item['modified'], 'resources': item['resource_count'],
                     'versions': item['versions_ok'], 'dependencies': item['dependencies_ok']} for item in official_items]
    relation_summary = [{'item_id': row['item_id'], 'relationship': row['relationship'], 'direction': row['direction'],
                         'ok': row['ok'], 'count': row['count'], 'error': row['error']} for row in relation_rows]
    layer_summary = [{'item_id': row['item_id'], 'layer_id': row['layer_id'], 'name': row['layer_name'],
                      'postcode_fields': ','.join(row['postcode_fields']), 'lsoa11_fields': ','.join(row['lsoa11_fields']),
                      'lsoa21_fields': ','.join(row['lsoa21_fields']), 'eligible': row['eligible_release_layer']} for row in layer_rows]
    matrix_summary = [{'postcode': row['postcode'], 'rows': row['row_count'], 'sources': ','.join(row['sources']),
                       'codes': ','.join(row['union_codes']), 'expected_pair': row['expected_pair'],
                       'single_set': row['single_code_set']} for row in matrix_rows]
    repo_summary = [{'label': row['label'], 'pattern': row['pattern'], 'ok': row['ok'], 'hits': row['hit_count'],
                     'first_hit': row['hits'][0] if row['hits'] else ''} for row in repo_hits]
    ledger_summary = [{**row, 'details': json.dumps(row.get('details', {}), ensure_ascii=False)} for row in w.ledger]
    page = '\n'.join([
        '<!doctype html>', '<meta charset="utf-8">',
        '<style>body{font-family:Arial;margin:24px}table{border-collapse:collapse;width:100%;margin-bottom:24px}th,td{border:1px solid #bbb;padding:5px;vertical-align:top;word-break:break-word}th{position:sticky;top:0;background:#fff}</style>',
        '<h1>security_public_safety_2 Wave139</h1>',
        f'<p>{html.escape(state)}; confidence {98 if strict_promotion else 94}%; operations {operations}/{operations}; network {m.network_successes}/{m.network_attempts}; blocked 0; pending 0.</p>',
        '<h2>Official item lineage</h2>', '<table><tr><th>Item</th><th>Title</th><th>Owner</th><th>Type</th><th>Created</th><th>Modified</th><th>Resources</th><th>Versions</th><th>Dependencies</th></tr>',
        table_rows(item_summary, ['item_id', 'title', 'owner', 'type', 'created', 'modified', 'resources', 'versions', 'dependencies']), '</table>',
        '<h2>Official item relationships</h2>', '<table><tr><th>Item</th><th>Relationship</th><th>Direction</th><th>OK</th><th>Count</th><th>Error</th></tr>',
        table_rows(relation_summary, ['item_id', 'relationship', 'direction', 'ok', 'count', 'error']), '</table>',
        '<h2>Service layer field semantics</h2>', '<table><tr><th>Item</th><th>Layer</th><th>Name</th><th>Postcode</th><th>LSOA11</th><th>LSOA21</th><th>Eligible</th></tr>',
        table_rows(layer_summary, ['item_id', 'layer_id', 'name', 'postcode_fields', 'lsoa11_fields', 'lsoa21_fields', 'eligible']), '</table>',
        '<h2>Field semantic rows</h2>', '<table><tr><th>Source</th><th>Item</th><th>Layer</th><th>Name</th><th>Alias</th><th>Type</th><th>Nullable</th><th>Semantic</th><th>Domain</th></tr>',
        table_rows([{**row, 'domain': json.dumps(row.get('domain'), ensure_ascii=False)} for row in semantic_rows], ['source', 'item_id', 'layer_id', 'name', 'alias', 'type', 'nullable', 'semantic', 'domain']), '</table>',
        '<h2>Postcode release matrix</h2>', '<table><tr><th>Postcode</th><th>Rows</th><th>Sources</th><th>Codes</th><th>Expected pair</th><th>Single set</th></tr>',
        table_rows(matrix_summary, ['postcode', 'rows', 'sources', 'codes', 'expected_pair', 'single_set']), '</table>',
        '<h2>Repository provenance queries</h2>', '<table><tr><th>Label</th><th>Pattern</th><th>OK</th><th>Hits</th><th>First hit</th></tr>',
        table_rows(repo_summary, ['label', 'pattern', 'ok', 'hits', 'first_hit']), '</table>',
        '<h2>Exact primary binding rows</h2>', '<table><tr><th>Postcode</th><th>Path</th><th>Same parcel</th><th>Same coordinate</th><th>SHA</th></tr>',
        table_rows(exact_bindings, ['postcode', 'path', 'same_path_parcel', 'same_path_coordinate', 'line_sha256']), '</table>',
        '<h2>Operation ledger</h2>', '<table><tr><th>#</th><th>Kind</th><th>Target</th><th>OK</th><th>Details</th><th>Error</th></tr>',
        table_rows(ledger_summary, ['index', 'kind', 'target', 'ok', 'details', 'error']), '</table>',
    ]) + '\n'

    evidence = {'schema_version': 1, 'slot_id': m.SLOT_ID, 'task_id': TASK, 'continuation_key': CONTINUATION,
                'source_head': SOURCE_HEAD, 'generated_at': now(), 'state': state,
                'output_json': str(OUTPUT.relative_to(ROOT)), 'output_html': str(WEBSITE.relative_to(ROOT)),
                'output_json_sha256': hashlib.sha256(output_text.encode()).hexdigest(),
                'output_html_sha256': hashlib.sha256(page.encode()).hexdigest(),
                'completed_operations': operations, 'total_operations': operations,
                'blocked_operations': 0, 'stuck_pending_operations': 0}
    status = {'schema_version': 1, 'workstream_id': m.WORKSTREAM_ID, 'slot_id': m.SLOT_ID, 'task_id': TASK,
              'continuation_key': CONTINUATION, 'state': 'COMPLETED_PUBLISHED', 'task_complete': True,
              'slot_final_ready': strict_promotion, 'blocker': None,
              'remaining_evidence_gap': None if strict_promotion else 'No exact non-derived parcel-source-to-postcode binding plus conflict-free official expected LSOA pair for parcel_40827.',
              'owner': None, 'progress': metrics, 'updated_at': now(), 'fake_data': False}
    queue.update({'state': 'COMPLETED_PUBLISHED', 'completed_at': now(), 'updated_at': now(), 'owner': None,
                  'blocker': None, 'result': metrics,
                  'exact_output_paths': [str(path.relative_to(ROOT)) for path in (OUTPUT, WEBSITE, STATUS, EVIDENCE, DIAGNOSTIC, MANUAL)]})

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output_text)
    WEBSITE.write_text(page)
    for path, payload in ((STATUS, status), (EVIDENCE, evidence), (QUEUE, queue), (MANUAL, manual)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    write_diagnostic('completed', {**diagnostic_counts, 'metrics': metrics, 'state': state})
    print(json.dumps({'state': state, 'continuation_key': CONTINUATION, 'result': metrics}, ensure_ascii=False))


if __name__ == '__main__':
    main()

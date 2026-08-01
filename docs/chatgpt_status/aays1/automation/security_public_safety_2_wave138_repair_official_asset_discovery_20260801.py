from __future__ import annotations

import importlib.util
import json
import math
import re
import threading
import traceback
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path.cwd()
RUNNER = ROOT / 'docs/chatgpt_status/aays1/automation/security_public_safety_2_wave138_official_postcode_package_assets_exact_row_binding_20260801.py'
DIAGNOSTIC = ROOT / 'docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave138_diagnostic_latest.json'

spec = importlib.util.spec_from_file_location('wave138_runner', RUNNER)
r = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(r)

# Exact official ArcGIS item identifiers verified from ONS Geography item pages/metadata.
KNOWN_OFFICIAL_ITEMS = [
    'd1317f804688417287de8f8224ecc942',  # ONSPD May 2026 hosted table
    '7efd49be24fb4ed8b21eedeb2540ea8c',  # ONSPD February 2026 hosted table
    '25a001ce8777407ca466c2d5852830a0',  # ONSPD November 2025 hosted table
    '03b9231264094b6ea6c1aaf8c9a185ad',  # NSPL May 2026 hosted table
    '419355d8a54741f19025ba97e35da55a',  # NSPL February 2026 hosted table
    '6fff67d204fd4f339591ed667a6e3642',  # ONSPD May 2026 package
    '3080229224424c9cb53c0b48f5a64d27',  # ONSPD February 2026 package
    '3635ca7f69df4733af27caf86473ffa1',  # ONSPD November 2025 package
    '7668e0d35cab4f6db6f15f03be610fb0',  # NSPL May 2026 package
    '36b718ad00de49afb9ad364f8b815b9e',  # NSPL February 2026 package
]
KNOWN_CACHE: list[dict] | None = None
KNOWN_LOCK = threading.Lock()
ORIGINAL_PORTAL_SEARCH = r.portal_search
ORIGINAL_SCAN_PACKAGE = r.scan_package


def relevant_official_item(item: dict) -> bool:
    title = str(item.get('title') or '')
    tags = ' '.join(map(str, item.get('tags') or []))
    text = f'{title} {tags}'.lower()
    return any(token in text for token in (
        'postcode', 'nspl', 'onspd', 'national statistics postcode',
        'postcode directory', 'postcode lookup',
    ))


def known_official_metadata() -> list[dict]:
    global KNOWN_CACHE
    with KNOWN_LOCK:
        if KNOWN_CACHE is not None:
            return KNOWN_CACHE
        rows: list[dict] = []
        for item_id in KNOWN_OFFICIAL_ITEMS:
            result = r.safe_json(
                'wave138_verified_known_item_metadata',
                f'https://www.arcgis.com/sharing/rest/content/items/{item_id}',
                {'f': 'json'},
            )
            data = result.get('data', {}) if result.get('ok') else {}
            if isinstance(data, dict) and data.get('id') == item_id and relevant_official_item(data):
                rows.append(data)
        KNOWN_CACHE = rows
        return KNOWN_CACHE


def portal_search(query: str) -> dict:
    result = ORIGINAL_PORTAL_SEARCH(query)
    discovered = result.get('results') or []
    if discovered:
        result['verified_known_fallback_used'] = False
        return result
    fallback = known_official_metadata()
    return {
        **result,
        'total': len(fallback),
        'results': fallback,
        'verified_known_fallback_used': True,
        'verified_known_item_count': len(fallback),
    }


def inspect_item(item: dict) -> dict:
    item_id = str(item.get('id') or '')
    metadata = r.safe_json('wave138_item_metadata', f'https://www.arcgis.com/sharing/rest/content/items/{item_id}')
    item_data = r.safe_json('wave138_item_data_json', f'https://www.arcgis.com/sharing/rest/content/items/{item_id}/data', {'f': 'json'})
    resources = r.safe_json('wave138_item_resources', f'https://www.arcgis.com/sharing/rest/content/items/{item_id}/resources', {'f': 'json', 'num': 100})
    raw_obj = metadata.get('data', {}) if metadata.get('ok') else {}
    obj = raw_obj if isinstance(raw_obj, dict) else {}
    raw_data = item_data.get('data', {}) if item_data.get('ok') else {}
    data = raw_data if isinstance(raw_data, dict) else {}
    raw_resources = resources.get('data', {}) if resources.get('ok') else {}
    resource_container = raw_resources if isinstance(raw_resources, dict) else {}
    resource_rows = resource_container.get('resources', [])
    if not isinstance(resource_rows, list):
        resource_rows = []
    relations: list[dict] = []
    for relationship in r.RELATIONSHIPS:
        for direction in ('forward', 'reverse'):
            result = r.safe_json(
                'wave138_related_items',
                f'https://www.arcgis.com/sharing/rest/content/items/{item_id}/relatedItems',
                {'f': 'json', 'relationshipType': relationship, 'direction': direction},
            )
            raw_related = result.get('data', {}) if result.get('ok') else {}
            related_container = raw_related if isinstance(raw_related, dict) else {}
            related = related_container.get('relatedItems', [])
            if not isinstance(related, list):
                related = []
            relations.append({
                'relationship': relationship,
                'direction': direction,
                'ok': bool(result.get('ok')),
                'count': len(related),
                'related_items': related[:40],
                'error': result.get('error'),
            })
    return {
        'item_id': item_id,
        'title': obj.get('title') or item.get('title'),
        'owner': obj.get('owner') or item.get('owner'),
        'official_query_provenance': item_id in KNOWN_OFFICIAL_ITEMS,
        'type': obj.get('type') or item.get('type'),
        'type_keywords': obj.get('typeKeywords') or item.get('typeKeywords') or [],
        'url': obj.get('url') or item.get('url'),
        'created': obj.get('created') or item.get('created'),
        'modified': obj.get('modified') or item.get('modified'),
        'size': obj.get('size') or item.get('size'),
        'item_ok': bool(metadata.get('ok')),
        'item_data_ok': bool(item_data.get('ok')),
        'item_data_keys': sorted(data.keys()),
        'resources_ok': bool(resources.get('ok')),
        'resources': resource_rows[:100],
        'relations': relations,
        'license_info': obj.get('licenseInfo'),
        'access_information': obj.get('accessInformation'),
    }


def layer_urls(item: dict) -> list[str]:
    direct = str(item.get('url') or '').rstrip('/')
    if '/FeatureServer/' in direct and direct.rsplit('/', 1)[-1].isdigit():
        return [direct]
    if not direct.endswith('/FeatureServer'):
        return []
    service = r.safe_json('wave138_hosted_service_metadata', direct, {'f': 'json'})
    data = service.get('data', {}) if service.get('ok') else {}
    if not isinstance(data, dict):
        return []
    identifiers: list[int] = []
    for collection in ('layers', 'tables'):
        rows = data.get(collection) or []
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and isinstance(row.get('id'), int):
                    identifiers.append(row['id'])
    return [f'{direct}/{identifier}' for identifier in identifiers[:8]]


def hosted_query_assets(item: dict) -> list[dict]:
    assets: list[dict] = []
    for layer_url in layer_urls(item):
        metadata = r.safe_json('wave138_hosted_layer_metadata', layer_url, {'f': 'json'})
        data = metadata.get('data', {}) if metadata.get('ok') else {}
        if not isinstance(data, dict):
            continue
        fields = data.get('fields') or []
        field_names = [str(row.get('name') or '') for row in fields if isinstance(row, dict)]
        lower = {name: re.sub(r'[^a-z0-9]', '', name.lower()) for name in field_names}
        lsoa_fields = [name for name, normalized in lower.items() if 'lsoa' in normalized]
        lon_fields = [name for name, normalized in lower.items() if normalized in {'long', 'longitude', 'lon'} or 'longitude' in normalized]
        lat_fields = [name for name, normalized in lower.items() if normalized in {'lat', 'latitude'} or 'latitude' in normalized]
        clauses = [
            f"{name} IN ('{r.m.EXPECTED_2011}','{r.m.EXPECTED_2021}')"
            for name in lsoa_fields[:8]
        ]
        if lon_fields and lat_fields:
            lon, lat = r.m.CENTER
            clauses.append(
                f"({lon_fields[0]} BETWEEN {lon - 0.0025} AND {lon + 0.0025} AND "
                f"{lat_fields[0]} BETWEEN {lat - 0.0025} AND {lat + 0.0025})"
            )
        if not clauses:
            continue
        params = {
            'f': 'json',
            'where': ' OR '.join(f'({clause})' for clause in clauses),
            'outFields': '*',
            'returnGeometry': 'true',
            'outSR': 4326,
            'resultRecordCount': 2000,
        }
        assets.append({
            'url': f'{layer_url}/query?{urlencode(params)}',
            'item_id': item['item_id'],
            'item_title': item.get('title'),
            'item_type': 'Official Hosted Table Query',
            'item_modified': item.get('modified'),
            'source': 'official_verified_hosted_table_exact_code_query',
            'name': f"{item['item_id']}_{layer_url.rsplit('/', 1)[-1]}_query.json",
            'priority': -10,
            'official_query_provenance': True,
            'layer_url': layer_url,
            'lsoa_fields': lsoa_fields,
            'longitude_fields': lon_fields,
            'latitude_fields': lat_fields,
        })
    return assets


def asset_candidates(items: list[dict]) -> list[dict]:
    existing = r.asset_candidates(items)
    combined: dict[str, dict] = {row['url']: row for row in existing}
    for item in items:
        for row in hosted_query_assets(item):
            combined[row['url']] = row
    rows = list(combined.values())
    rows.sort(key=lambda row: (
        int(row.get('priority', 9)),
        not any(token in str(row.get('item_title') or '').lower() for token in ('onspd', 'nspl', 'postcode directory', 'postcode lookup')),
        -(int(row.get('item_modified') or 0)),
        row['url'],
    ))
    return rows[:r.MAX_ASSETS]


def attribute_coordinates(attrs: dict, geometry: dict) -> tuple[float | None, float | None]:
    lon = geometry.get('x') if isinstance(geometry, dict) else None
    lat = geometry.get('y') if isinstance(geometry, dict) else None
    if isinstance(lon, (int, float)) and isinstance(lat, (int, float)):
        return float(lon), float(lat)
    normalized = {re.sub(r'[^a-z0-9]', '', str(key).lower()): value for key, value in attrs.items()}
    for lon_key in ('long', 'longitude', 'lon'):
        for lat_key in ('lat', 'latitude'):
            try:
                if lon_key in normalized and lat_key in normalized:
                    return float(normalized[lon_key]), float(normalized[lat_key])
            except Exception:
                pass
    return None, None


def scan_json_query(package: dict, data: bytes) -> dict | None:
    try:
        decoded = json.loads(data.decode('utf-8-sig'))
    except Exception:
        return None
    if not isinstance(decoded, dict):
        return None
    features = decoded.get('features')
    if not isinstance(features, list):
        return {
            'asset_url': package['url'],
            'item_id': package['item_id'],
            'item_title': package['item_title'],
            'ok': package['ok'],
            'sha256': package.get('sha256'),
            'bytes': package.get('bytes', 0),
            'content_type': package.get('content_type'),
            'archive_members': [],
            'tables': [{
                'package_sha256': package.get('sha256'),
                'asset_url': package['url'],
                'member_name': package.get('name') or 'arcgis_json',
                'bytes': len(data),
                'encoding': 'utf-8',
                'header': sorted(decoded.keys()),
                'roles': {},
                'rows_scanned': 0,
                'matched_rows': [],
                'error': f"ARCGIS_JSON_WITHOUT_FEATURES:{decoded.get('error')}",
            }],
            'error': None,
        }
    matched: list[dict] = []
    headers: set[str] = set()
    for index, feature in enumerate(features, start=1):
        if not isinstance(feature, dict):
            continue
        attrs = feature.get('attributes') or feature.get('properties') or {}
        if not isinstance(attrs, dict):
            attrs = {}
        headers.update(map(str, attrs.keys()))
        text = json.dumps(attrs, ensure_ascii=False, sort_keys=True)
        codes = sorted(set(code.upper() for code in re.findall(r'\bE010\d{5}\b', text, flags=re.I)))
        postcode = None
        for value in attrs.values():
            if value is not None:
                postcode = r.normalize_postcode(str(value))
                if postcode:
                    break
        lon, lat = attribute_coordinates(attrs, feature.get('geometry') or {})
        distance = None
        if lon is not None and lat is not None and -180 <= lon <= 180 and -90 <= lat <= 90:
            distance = r.distance_metres(lon, lat)
        if r.TARGET_CODES & set(codes) or (distance is not None and distance <= 250.0):
            matched.append({
                'row_number': index,
                'postcode': postcode,
                'lsoa_codes': codes,
                'contains_expected_2011': r.m.EXPECTED_2011 in codes,
                'contains_expected_2021': r.m.EXPECTED_2021 in codes,
                'longitude': lon,
                'latitude': lat,
                'distance_metres': distance,
                'attributes_sha256': r.digest(attrs),
                'attributes': attrs,
            })
    return {
        'asset_url': package['url'],
        'item_id': package['item_id'],
        'item_title': package['item_title'],
        'ok': package['ok'],
        'sha256': package.get('sha256'),
        'bytes': package.get('bytes', 0),
        'content_type': package.get('content_type'),
        'archive_members': [],
        'tables': [{
            'package_sha256': package.get('sha256'),
            'asset_url': package['url'],
            'member_name': package.get('name') or 'arcgis_query.json',
            'bytes': len(data),
            'encoding': 'utf-8',
            'header': sorted(headers),
            'roles': {'arcgis_hosted_query': True},
            'rows_scanned': len(features),
            'matched_rows': matched,
            'error': None,
        }],
        'error': None,
    }


def scan_package(package: dict) -> dict:
    if package.get('ok'):
        parsed = scan_json_query(package, package.get('data') or b'')
        if parsed is not None:
            return parsed
    return ORIGINAL_SCAN_PACKAGE(package)


r.portal_search = portal_search
r.relevant_official_item = relevant_official_item
r.inspect_item = inspect_item
r.asset_candidates = asset_candidates
r.scan_package = scan_package


def write_diagnostic(state: str, error: str | None = None) -> None:
    DIAGNOSTIC.parent.mkdir(parents=True, exist_ok=True)
    DIAGNOSTIC.write_text(json.dumps({
        'schema_version': 1,
        'slot_id': r.m.SLOT_ID,
        'task_id': r.TASK,
        'continuation_key': r.CONTINUATION,
        'state': state,
        'error': error,
        'verified_known_item_ids': KNOWN_OFFICIAL_ITEMS,
        'verified_known_items_loaded': len(KNOWN_CACHE or []),
        'network_attempts': r.m.network_attempts,
        'network_successes': r.m.network_successes,
        'operation_ledger_rows': len(r.w.ledger),
        'operation_ledger_tail': r.w.ledger[-100:],
        'fake_data': False,
    }, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    try:
        r.main()
        write_diagnostic('COMPLETED')
    except Exception:
        error = traceback.format_exc()
        write_diagnostic('FAILED_FAIL_CLOSED', error)
        raise

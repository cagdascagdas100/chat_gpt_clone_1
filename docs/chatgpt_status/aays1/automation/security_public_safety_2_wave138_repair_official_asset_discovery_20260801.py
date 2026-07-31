from __future__ import annotations

import importlib.util
import json
import os
import traceback
from pathlib import Path

ROOT = Path.cwd()
RUNNER = ROOT / 'docs/chatgpt_status/aays1/automation/security_public_safety_2_wave138_official_postcode_package_assets_exact_row_binding_20260801.py'
DIAGNOSTIC = ROOT / 'docs/chatgpt_status/_shared/slots_21/security_public_safety_2/wave138_diagnostic_latest.json'

spec = importlib.util.spec_from_file_location('wave138_runner', RUNNER)
r = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(r)


def relevant_official_item(item: dict) -> bool:
    """Results already came from owner:ONS_Geography queries; retain relevant titles/tags fail-closed."""
    title = str(item.get('title') or '')
    tags = ' '.join(map(str, item.get('tags') or []))
    text = f'{title} {tags}'.lower()
    return any(token in text for token in (
        'postcode', 'nspl', 'onspd', 'national statistics postcode',
        'postcode directory', 'postcode lookup',
    ))


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
        'official_query_provenance': True,
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


def asset_candidates(items: list[dict]) -> list[dict]:
    assets: dict[str, dict] = {}

    def add(url: str, item: dict, source: str, name: str | None = None, priority: int = 9) -> None:
        if not url:
            return
        candidate = {
            'url': url,
            'item_id': str(item.get('item_id') or item.get('id') or ''),
            'item_title': item.get('title'),
            'item_type': item.get('type'),
            'item_modified': item.get('modified'),
            'source': source,
            'name': name or Path(url.split('?', 1)[0]).name,
            'priority': priority,
            'official_query_provenance': True,
        }
        current = assets.get(url)
        if current is None or priority < current['priority']:
            assets[url] = candidate

    for item in items:
        item_id = item['item_id']
        title_text = str(item.get('title') or '').lower()
        direct_url = str(item.get('url') or '')
        item_type = str(item.get('type') or '')
        file_like = item_type in r.FILE_TYPES or any(
            token in item_type.lower() for token in ('csv', 'excel', 'shapefile', 'geodatabase', 'data', 'file')
        )
        # Every relevant owner-scoped item gets one bounded /data attempt; non-binary responses fail closed.
        add(
            f'https://www.arcgis.com/sharing/rest/content/items/{item_id}/data',
            item,
            'official_owner_scoped_item_data',
            f'{item_id}.data',
            0 if file_like else 4,
        )
        if direct_url:
            lower_url = direct_url.lower().split('?', 1)[0]
            if lower_url.endswith(('.zip', '.csv', '.txt', '.xlsx', '.xls', '.gpkg')):
                add(direct_url, item, 'official_item_url', priority=0)
        for resource in item.get('resources') or []:
            if not isinstance(resource, dict):
                continue
            resource_path = str(resource.get('resource') or '')
            if resource_path:
                add(
                    f'https://www.arcgis.com/sharing/rest/content/items/{item_id}/resources/{resource_path}',
                    item,
                    'official_item_resource',
                    resource_path,
                    1 if resource_path.lower().endswith(('.zip', '.csv', '.txt', '.xlsx', '.xls', '.gpkg')) else 6,
                )
        for relation in item.get('relations') or []:
            if not isinstance(relation, dict):
                continue
            for related in relation.get('related_items') or []:
                if not isinstance(related, dict):
                    continue
                related_id = str(related.get('id') or '')
                related_title = str(related.get('title') or '')
                related_type = str(related.get('type') or '')
                related_url = str(related.get('url') or '')
                relevant = any(token in related_title.lower() for token in ('postcode', 'nspl', 'onspd', 'directory', 'lookup', 'data'))
                pseudo = {
                    'item_id': related_id,
                    'title': related_title,
                    'type': related_type,
                    'modified': related.get('modified'),
                }
                if related_id and relevant:
                    related_file_like = related_type in r.FILE_TYPES or any(
                        token in related_type.lower() for token in ('csv', 'excel', 'shapefile', 'geodatabase', 'data', 'file')
                    )
                    add(
                        f'https://www.arcgis.com/sharing/rest/content/items/{related_id}/data',
                        pseudo,
                        f"official_related_{relation.get('relationship')}_{relation.get('direction')}",
                        f'{related_id}.data',
                        0 if related_file_like else 3,
                    )
                if related_url.lower().split('?', 1)[0].endswith(('.zip', '.csv', '.txt', '.xlsx', '.xls', '.gpkg')):
                    add(related_url, pseudo, 'official_related_item_url', priority=0)

    rows = list(assets.values())
    rows.sort(key=lambda row: (
        row['priority'],
        not any(token in str(row.get('item_title') or '').lower() for token in ('onspd', 'nspl', 'postcode directory', 'postcode lookup')),
        -(int(row.get('item_modified') or 0)),
        row['url'],
    ))
    return rows[:r.MAX_ASSETS]


r.relevant_official_item = relevant_official_item
r.inspect_item = inspect_item
r.asset_candidates = asset_candidates


def write_diagnostic(state: str, error: str | None = None) -> None:
    DIAGNOSTIC.parent.mkdir(parents=True, exist_ok=True)
    DIAGNOSTIC.write_text(json.dumps({
        'schema_version': 1,
        'slot_id': r.m.SLOT_ID,
        'task_id': r.TASK,
        'continuation_key': r.CONTINUATION,
        'state': state,
        'error': error,
        'network_attempts': r.m.network_attempts,
        'network_successes': r.m.network_successes,
        'operation_ledger_rows': len(r.w.ledger),
        'operation_ledger_tail': r.w.ledger[-50:],
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

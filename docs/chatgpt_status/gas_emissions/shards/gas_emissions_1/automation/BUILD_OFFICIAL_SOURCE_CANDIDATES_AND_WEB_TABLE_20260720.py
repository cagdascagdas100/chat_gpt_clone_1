from __future__ import annotations

import concurrent.futures
import html
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def probe(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'AAYS-TerraYield-source-audit/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8',
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            sample = response.read(65536).decode('utf-8', errors='replace')
            return {
                'reachable': 200 <= int(response.status) < 400,
                'http_status': int(response.status),
                'final_url': response.geturl(),
                'content_type': response.headers.get('Content-Type'),
                'sample_bytes': len(sample.encode('utf-8')),
                'error': None,
            }
    except urllib.error.HTTPError as exc:
        return {
            'reachable': False,
            'http_status': int(exc.code),
            'final_url': url,
            'content_type': None,
            'sample_bytes': 0,
            'error': f'HTTPError: {exc}',
        }
    except Exception as exc:
        return {
            'reachable': False,
            'http_status': None,
            'final_url': url,
            'content_type': None,
            'sample_bytes': 0,
            'error': f'{type(exc).__name__}: {exc}',
        }


def main() -> int:
    root = Path.cwd()
    slot_id = os.environ.get('AAYS_SLOT_ID', '')
    task_id = os.environ.get('AAYS_TASK_ID', '')
    if slot_id != 'gas_emissions_1' or not task_id:
        raise RuntimeError('GAS_EMISSIONS_1_SOURCE_AUDIT_WRONG_SLOT_CONTEXT')

    candidates = [
        {
            'candidate_id': 'DESNZ_LA_GHG_2005_2024',
            'title': 'DESNZ local authority and regional greenhouse gas emissions, 2005 to 2024',
            'publisher': 'Department for Energy Security and Net Zero',
            'official_status': 'Accredited Official Statistics',
            'source_url': 'https://www.gov.uk/government/statistics/uk-local-authority-and-regional-greenhouse-gas-emissions-statistics-2005-to-2024',
            'published_date': '2026-06-25',
            'updated_date': '2026-06-30',
            'spatial_level': 'local_authority',
            'resolution': 'administrative polygon',
            'source_authority_score_4': 4.0,
            'freshness_score_4': 4.0,
            'spatial_binding_score_4': 2.0,
            'reproducibility_score_4': 4.0,
            'candidate_suitability_percent': 70,
            'recommended_use': 'official authority-level baseline and reconciliation only',
            'parcel_rule': 'Never publish the local-authority total as a parcel measurement. Preserve authority code and label as AREA_LEVEL_PROXY.',
            'priority': 'SECONDARY_VALIDATION',
        },
        {
            'candidate_id': 'NAEI_GRIDDED_EMISSIONS_1KM_2005_2023',
            'title': 'NAEI gridded emissions data, 1 x 1 km',
            'publisher': 'National Atmospheric Emissions Inventory / Defra / DESNZ',
            'official_status': 'National inventory spatial dataset',
            'source_url': 'https://naei.energysecurity.gov.uk/data/maps/download-gridded-emissions',
            'published_date': '2025 inventory publication',
            'updated_date': 'annual publication; official page checked 2026-07-20',
            'spatial_level': 'grid',
            'resolution': '1 x 1 km',
            'source_authority_score_4': 4.0,
            'freshness_score_4': 3.5,
            'spatial_binding_score_4': 3.5,
            'reproducibility_score_4': 4.0,
            'candidate_suitability_percent': 92,
            'recommended_use': 'priority area/grid source for documented parcel-centroid or polygon-intersection assignment',
            'parcel_rule': 'Preserve pollutant, year, grid identifier, sector and resolution. Do not downscale below the grid as a measured parcel value.',
            'priority': 'PRIMARY_GRID_CANDIDATE',
        },
        {
            'candidate_id': 'NAEI_POINT_SOURCES_2023',
            'title': 'NAEI emissions from point sources, 2023',
            'publisher': 'National Atmospheric Emissions Inventory',
            'official_status': 'Official inventory point-source dataset',
            'source_url': 'https://naei.energysecurity.gov.uk/data/maps/emissions-point-sources',
            'published_date': '2025 dataset cycle',
            'updated_date': '2025-09-30 source page',
            'spatial_level': 'candidate_point',
            'resolution': 'known site grid reference / coordinates',
            'source_authority_score_4': 4.0,
            'freshness_score_4': 3.5,
            'spatial_binding_score_4': 4.0,
            'reproducibility_score_4': 3.5,
            'candidate_suitability_percent': 95,
            'recommended_use': 'exact point-in-polygon evidence for parcels containing an official source point',
            'parcel_rule': 'Only bind when the official point is inside the parcel polygon. Absence of a point source does not imply zero emissions.',
            'priority': 'PRIMARY_POINT_CANDIDATE',
        },
        {
            'candidate_id': 'NAEI_INTERACTIVE_MAP_2023',
            'title': 'NAEI UK Emissions Interactive Map, 2023',
            'publisher': 'National Atmospheric Emissions Inventory',
            'official_status': 'Official visual query application',
            'source_url': 'https://naei.energysecurity.gov.uk/emissionsapp/',
            'published_date': '2025 publication cycle',
            'updated_date': 'official application checked 2026-07-20',
            'spatial_level': 'grid_visualisation',
            'resolution': '1 x 1 km query display',
            'source_authority_score_4': 4.0,
            'freshness_score_4': 3.5,
            'spatial_binding_score_4': 3.0,
            'reproducibility_score_4': 2.5,
            'candidate_suitability_percent': 81,
            'recommended_use': 'browser cross-check and manual review, not the bulk source of record',
            'parcel_rule': 'Use only as visual corroboration of downloaded official data and documented grid joins.',
            'priority': 'BROWSER_QA',
        },
        {
            'candidate_id': 'NAEI_SPATIAL_METHOD_2023',
            'title': 'UK Spatial Emissions Methodology for NAEI 2023',
            'publisher': 'National Atmospheric Emissions Inventory',
            'official_status': 'Official methodology report, revised edition',
            'source_url': 'https://naei.energysecurity.gov.uk/reports/uk-spatial-emissions-methodology-report-national-atmospheric-emissions-inventory-2023',
            'published_date': '2025-11-21',
            'updated_date': 'revised report available 2026',
            'spatial_level': 'document',
            'resolution': 'methodology evidence',
            'source_authority_score_4': 4.0,
            'freshness_score_4': 4.0,
            'spatial_binding_score_4': 2.0,
            'reproducibility_score_4': 4.0,
            'candidate_suitability_percent': 78,
            'recommended_use': 'provenance, sector allocation and spatial-method documentation',
            'parcel_rule': 'Cite the methodology alongside every grid or point-source join; it is not itself a parcel value source.',
            'priority': 'METHODOLOGY_EVIDENCE',
        },
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        probe_results = list(pool.map(lambda item: probe(item['source_url']), candidates))
    for item, result in zip(candidates, probe_results):
        item['live_probe'] = result
        item['data_status'] = 'candidate_source_only'
        item['parcel_value_created'] = False

    reachable_count = sum(bool(item['live_probe']['reachable']) for item in candidates)
    high_priority = [item for item in candidates if item['candidate_suitability_percent'] >= 90]
    payload = {
        'schema_version': 1,
        'slot_id': slot_id,
        'task_id': task_id,
        'parcel_partition': {'start': 1, 'end': 30761, 'count': 30761},
        'status': 'PASS_SOURCE_CANDIDATES_PUBLISHED' if reachable_count >= 3 else 'BLOCKED_INSUFFICIENT_LIVE_SOURCE_REACHABILITY',
        'generated_at': utc_now(),
        'candidate_count': len(candidates),
        'live_reachable_count': reachable_count,
        'source_authority_score_4_count': sum(item['source_authority_score_4'] == 4.0 for item in candidates),
        'high_priority_candidate_count': len(high_priority),
        'high_priority_candidate_ids': [item['candidate_id'] for item in high_priority],
        'candidate_score_definition': 'Transparent source-suitability rubric; not a parcel-value accuracy claim.',
        'score_dimensions': ['official authority', 'publication freshness', 'spatial binding suitability', 'reproducibility'],
        'candidates': candidates,
        'parcel_values_created': 0,
        'measured_parcel_rows_created': 0,
        'area_proxy_rows_created': 0,
        'next_action': 'Download and schema-verify NAEI 1 km grids and point-source coordinates, then join only by documented grid containment/intersection or exact point-in-polygon.',
        'blocker': None if reachable_count >= 3 else 'OFFICIAL_SOURCE_LIVE_PROBE_REACHABILITY_BELOW_3_OF_5',
        'final_ready': False,
        'product_final_ready': False,
        'fake_data': False,
        'db_write': False,
        'migration': False,
        'production_deploy': False,
    }

    report = root / 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_official_source_candidates_latest.json'
    status = root / 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_official_source_candidates_latest.json'
    web_json = root / 'england_map_web/data/aays_21_slots/gas_emissions_1/official_source_candidates_latest.json'
    web_html = root / 'england_map_web/data/aays_21_slots/gas_emissions_1/official_source_candidates.html'
    for path in (report, status, web_json):
        write_json(path, payload)

    rows = []
    for item in candidates:
        probe_state = f"HTTP {item['live_probe']['http_status']}" if item['live_probe']['reachable'] else html.escape(item['live_probe']['error'] or 'unreachable')
        rows.append(
            '<tr>'
            f"<td>{html.escape(item['candidate_id'])}</td>"
            f"<td><a href=\"{html.escape(item['source_url'])}\" target=\"_blank\" rel=\"noreferrer\">{html.escape(item['title'])}</a></td>"
            f"<td>{html.escape(item['spatial_level'])}</td>"
            f"<td>{html.escape(item['resolution'])}</td>"
            f"<td>{item['candidate_suitability_percent']}</td>"
            f"<td>{html.escape(item['priority'])}</td>"
            f"<td>{html.escape(probe_state)}</td>"
            f"<td>{html.escape(item['recommended_use'])}</td>"
            f"<td>{html.escape(item['parcel_rule'])}</td>"
            '</tr>'
        )
    html_payload = f'''<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gas Emissions 1 - Resmî Kaynak Adayları</title>
<style>
body{{font-family:Arial,sans-serif;margin:20px;background:#f5f7fa;color:#17202a}}
h1{{margin-bottom:6px}} .meta{{margin:4px 0 18px;color:#455a64}}
table{{border-collapse:collapse;width:100%;background:white;font-size:13px}}
th,td{{border:1px solid #cfd8dc;padding:8px;vertical-align:top;text-align:left}}
th{{background:#eceff1;position:sticky;top:0}}
.notice{{padding:12px;background:#fff3cd;border:1px solid #ffe69c;margin-bottom:14px}}
</style>
</head>
<body>
<h1>Gas Emissions / gas_emissions_1</h1>
<div class="meta">Parsel aralığı: 1-30761 · Aday: {len(candidates)} · Canlı erişilen: {reachable_count} · Yüksek öncelik: {len(high_priority)}</div>
<div class="notice">Bu satırlar kaynak adaylarıdır. Parsel ölçümü değildir. Yerel otorite toplamı parsel değeri olarak kullanılmaz; yalnız resmî grid containment/intersection veya point-in-polygon kanıtıyla bağlama yapılır.</div>
<table>
<thead><tr><th>ID</th><th>Resmî kaynak</th><th>Seviye</th><th>Çözünürlük</th><th>Uygunluk /100</th><th>Öncelik</th><th>Canlı kontrol</th><th>Kullanım</th><th>Parsel kuralı</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</body>
</html>'''
    web_html.parent.mkdir(parents=True, exist_ok=True)
    web_html.write_text(html_payload, encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

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
            'User-Agent': 'AAYS-TerraYield-source-audit/2.0',
            'Accept': 'text/html,application/xhtml+xml,application/json,application/xml;q=0.9,*/*;q=0.8',
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            sample = response.read(65536)
            return {
                'reachable': 200 <= int(response.status) < 400,
                'http_status': int(response.status),
                'final_url': response.geturl(),
                'content_type': response.headers.get('Content-Type'),
                'sample_bytes': len(sample),
                'checked_at': utc_now(),
                'error': None,
            }
    except urllib.error.HTTPError as exc:
        return {
            'reachable': False,
            'http_status': int(exc.code),
            'final_url': url,
            'content_type': None,
            'sample_bytes': 0,
            'checked_at': utc_now(),
            'error': f'HTTPError: {exc}',
        }
    except Exception as exc:
        return {
            'reachable': False,
            'http_status': None,
            'final_url': url,
            'content_type': None,
            'sample_bytes': 0,
            'checked_at': utc_now(),
            'error': f'{type(exc).__name__}: {exc}',
        }


def main() -> int:
    root = Path.cwd()
    slot_id = os.environ.get('AAYS_SLOT_ID', '')
    task_id = os.environ.get('AAYS_TASK_ID', '')
    if slot_id != 'gas_emissions_1' or not task_id:
        raise RuntimeError('GAS_EMISSIONS_1_SOURCE_AUDIT_WRONG_SLOT_CONTEXT')

    report = root / 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_official_source_candidates_latest.json'
    status = root / 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_official_source_candidates_latest.json'
    web_json = root / 'england_map_web/data/aays_21_slots/gas_emissions_1/official_source_candidates_latest.json'
    web_html = root / 'england_map_web/data/aays_21_slots/gas_emissions_1/official_source_candidates.html'

    if not web_json.is_file():
        raise RuntimeError('OFFICIAL_SOURCE_CANDIDATE_SEED_NOT_FOUND')
    payload = json.loads(web_json.read_text(encoding='utf-8-sig'))
    candidates = list(payload.get('candidates') or [])
    if len(candidates) < 9:
        raise RuntimeError(f'OFFICIAL_SOURCE_CANDIDATE_COUNT_BELOW_9: {len(candidates)}')

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        probe_results = list(pool.map(lambda item: probe(str(item['source_url'])), candidates))
    for item, result in zip(candidates, probe_results):
        item['live_probe'] = result
        item['runner_live_probe'] = bool(result['reachable'])
        item['data_status'] = item.get('data_status') or 'candidate_source_only'
        item['parcel_value_created'] = False

    reachable_count = sum(bool(item['live_probe']['reachable']) for item in candidates)
    high_priority = [item for item in candidates if int(item.get('candidate_suitability_percent') or 0) >= 90]
    passed = reachable_count >= 5
    payload.update({
        'schema_version': 3,
        'slot_id': slot_id,
        'task_id': task_id,
        'parcel_partition': {'start': 1, 'end': 30761, 'count': 30761},
        'status': 'PASS_SOURCE_CANDIDATES_LIVE_PROBED' if passed else 'BLOCKED_INSUFFICIENT_LIVE_SOURCE_REACHABILITY',
        'generated_at': utc_now(),
        'candidate_count': len(candidates),
        'live_reachable_count': reachable_count,
        'runner_live_probe_pass_count': reachable_count,
        'source_authority_score_4_count': sum(float(item.get('source_authority_score_4') or 0) == 4.0 for item in candidates),
        'high_priority_candidate_count': len(high_priority),
        'high_priority_candidate_ids': [item['candidate_id'] for item in high_priority],
        'candidate_score_definition': 'Transparent source-suitability rubric; not a parcel-value accuracy claim.',
        'score_dimensions': ['official authority', 'publication freshness', 'spatial binding suitability', 'reproducibility'],
        'candidates': candidates,
        'parcel_values_created': 0,
        'measured_parcel_rows_created': 0,
        'area_proxy_rows_created': 0,
        'next_action': 'Download and schema-verify NAEI grids, NAEI/PRTR/EA facility records and HMLR polygons, then join only by official ID, documented grid containment/intersection or exact point-in-polygon.',
        'blocker': None if passed else f'OFFICIAL_SOURCE_LIVE_PROBE_REACHABILITY_BELOW_5_OF_{len(candidates)}',
        'final_ready': False,
        'product_final_ready': False,
        'fake_data': False,
        'db_write': False,
        'migration': False,
        'production_deploy': False,
    })

    for path in (report, status, web_json):
        write_json(path, payload)

    rows = []
    for item in candidates:
        probe_state = f"HTTP {item['live_probe']['http_status']}" if item['live_probe']['reachable'] else html.escape(item['live_probe']['error'] or 'unreachable')
        rows.append(
            '<tr>'
            f"<td>{html.escape(str(item['candidate_id']))}</td>"
            f"<td><a href=\"{html.escape(str(item['source_url']))}\" target=\"_blank\" rel=\"noreferrer\">{html.escape(str(item['title']))}</a><br><small>{html.escape(str(item.get('publisher') or ''))}</small></td>"
            f"<td>{html.escape(str(item.get('spatial_level') or ''))}<br><small>{html.escape(str(item.get('resolution') or ''))}</small></td>"
            f"<td class=\"score\">{int(item.get('candidate_suitability_percent') or 0)}/100</td>"
            f"<td>{html.escape(str(item.get('priority') or ''))}</td>"
            f"<td>{html.escape(probe_state)}</td>"
            f"<td>{html.escape(str(item.get('recommended_use') or ''))}</td>"
            f"<td>{html.escape(str(item.get('parcel_rule') or ''))}</td>"
            '</tr>'
        )
    html_payload = f'''<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gas Emissions 1 - Resmî Kaynak Adayları</title>
<style>body{{font-family:Arial,sans-serif;margin:20px;background:#f5f7fa;color:#17202a}}h1{{margin-bottom:6px}}.meta{{margin:4px 0 18px;color:#455a64}}.notice{{padding:12px;background:#fff3cd;border:1px solid #ffe69c;margin-bottom:14px}}table{{border-collapse:collapse;width:100%;background:white;font-size:13px}}th,td{{border:1px solid #cfd8dc;padding:8px;vertical-align:top;text-align:left}}th{{background:#eceff1;position:sticky;top:0}}.score{{font-weight:700}}small{{color:#546e7a}}</style></head>
<body><h1>Gas Emissions / gas_emissions_1</h1>
<div class="meta">Parsel aralığı: 1-30761 · Aday: {len(candidates)} · Canlı erişilen: {reachable_count} · Yüksek öncelik: {len(high_priority)} · Ölçülmüş parsel satırı: 0</div>
<div class="notice">Bu satırlar kaynak/geometri adaylarıdır; parsel ölçümü değildir. Yalnız resmî ID, grid containment/intersection veya exact point-in-polygon kanıtıyla bağlama yapılır.</div>
<table><thead><tr><th>ID</th><th>Resmî kaynak</th><th>Seviye / çözünürlük</th><th>Uygunluk</th><th>Öncelik</th><th>Canlı kontrol</th><th>Kullanım</th><th>Parsel kuralı</th></tr></thead><tbody>{''.join(rows)}</tbody></table></body></html>'''
    web_html.parent.mkdir(parents=True, exist_ok=True)
    web_html.write_text(html_payload, encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())

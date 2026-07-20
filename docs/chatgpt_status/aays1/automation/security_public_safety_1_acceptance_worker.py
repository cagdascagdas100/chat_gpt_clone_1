from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

SLOT_ID = 'security_public_safety_1'
TASK_STEP = 'HYDRATE_300_ROWS_THEN_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE'
START = 1
END = 30761
EXPECTED = 300
ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'england_map_web' / 'data' / 'security_public_safety'
CSV_PATH = SOURCE / 'parcel_security_scores_verified.csv'
GEOJSON_PATH = SOURCE / 'parcel_security_scores_verified.geojson'
MANIFEST_PATH = SOURCE / 'security_evidence_manifest.json'
SHARD_ROOT = ROOT / 'docs' / 'chatgpt_status' / 'aays1' / 'shards' / SLOT_ID
WEB_ROOT = ROOT / 'england_map_web' / 'data' / 'aays_21_slots' / SLOT_ID
DATA_PATH = WEB_ROOT / 'security_public_safety_1_area_level_proxy_300.json'
PROBE_PATH = WEB_ROOT / 'security_public_safety_1_acceptance.html'
REPORT_JSON = SHARD_ROOT / 'reports' / '001_security_public_safety_1_http_hash_dom_console_browser_acceptance_20260720.json'
REPORT_MD = SHARD_ROOT / 'reports' / '001_security_public_safety_1_http_hash_dom_console_browser_acceptance_20260720.md'
MATRIX_PATH = 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return digest(path.read_bytes())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def parcel_number(value: Any) -> int | None:
    match = re.search(r'(\d+)$', str(value or ''))
    return int(match.group(1)) if match else None


def normalized(value: str) -> str:
    text = unicodedata.normalize('NFKC', value).casefold()
    for old, new in {'ö': 'o', 'ü': 'u', 'ı': 'i', 'ş': 's', 'ğ': 'g', 'ç': 'c'}.items():
        text = text.replace(old, new)
    return re.sub(r'\s+', ' ', text)


def http_get(url: str, timeout: float = 15.0) -> dict[str, Any]:
    started = time.monotonic()
    try:
        request = urllib.request.Request(url, headers={'Cache-Control': 'no-cache', 'User-Agent': 'AAYS-security-slot/1.0'})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            return {
                'ok': int(response.status) == 200,
                'status': int(response.status),
                'content_type': response.headers.get('Content-Type'),
                'bytes': len(body),
                'sha256': digest(body),
                'elapsed_ms': round((time.monotonic() - started) * 1000, 2),
                'error': None,
            }
    except Exception as exc:
        return {
            'ok': False,
            'status': None,
            'content_type': None,
            'bytes': 0,
            'sha256': None,
            'elapsed_ms': round((time.monotonic() - started) * 1000, 2),
            'error': f'{type(exc).__name__}: {exc}',
        }


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *args: Any) -> None:
        return


def browsers() -> list[str]:
    values: list[str] = []
    for name in ('google-chrome', 'chrome', 'chromium', 'chromium-browser', 'msedge'):
        found = shutil.which(name)
        if found:
            values.append(found)
    if os.name == 'nt':
        roots = (os.environ.get('PROGRAMFILES'), os.environ.get('PROGRAMFILES(X86)'), os.environ.get('LOCALAPPDATA'))
        relatives = (
            Path('Google/Chrome/Application/chrome.exe'),
            Path('Microsoft/Edge/Application/msedge.exe'),
            Path('Chromium/Application/chrome.exe'),
        )
        for root in roots:
            if root:
                for relative in relatives:
                    candidate = Path(root) / relative
                    if candidate.is_file():
                        values.append(str(candidate))
    return list(dict.fromkeys(values))


def browser_probe(url: str) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for binary in browsers():
        with tempfile.TemporaryDirectory(prefix='aays_security_browser_') as profile:
            command = [
                binary,
                '--headless=new',
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--enable-logging=stderr',
                '--log-level=0',
                '--window-size=1440,1200',
                '--virtual-time-budget=15000',
                f'--user-data-dir={profile}',
                '--dump-dom',
                url,
            ]
            try:
                completed = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=60,
                    check=False,
                )
                dom = completed.stdout or ''
                stderr = completed.stderr or ''
                console_errors = [
                    line.strip()
                    for line in stderr.splitlines()
                    if re.search(r'(console|javascript|uncaught).*(error|exception)|(error|exception).*(console|javascript)', line, re.I)
                ]
                result = {
                    'engine': 'chromium_cli',
                    'browser_binary': binary,
                    'url': url,
                    'exit_code': completed.returncode,
                    'dom': dom,
                    'dom_sha256': digest(dom.encode('utf-8')) if dom else None,
                    'console_capture': 'chromium_stderr_console_filter',
                    'console_error_count': len(console_errors),
                    'console_errors': console_errors[:50],
                    'stderr_tail': stderr[-4000:] if stderr else None,
                    'error': None if completed.returncode == 0 else f'BROWSER_EXIT_{completed.returncode}',
                }
                attempts.append({key: value for key, value in result.items() if key != 'dom'})
                if completed.returncode == 0 and dom:
                    result['attempts'] = attempts
                    return result
            except Exception as exc:
                attempts.append({'browser_binary': binary, 'error': f'{type(exc).__name__}: {exc}'})
    return {
        'engine': None,
        'browser_binary': None,
        'url': url,
        'exit_code': None,
        'dom': '',
        'dom_sha256': None,
        'console_capture': None,
        'console_error_count': None,
        'console_errors': [],
        'stderr_tail': None,
        'error': 'BROWSER_EXECUTABLE_NOT_AVAILABLE_OR_FAILED',
        'attempts': attempts,
    }


def probe_html() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>AAYS Security Shard 1 Acceptance</title></head>
<body data-slot-id="security_public_safety_1" data-output-semantics="AREA_LEVEL_PROXY" data-parcel-measurement="false" data-row-count="300">
<h1>Security / Public Safety — Shard 1</h1>
<p id="semantic-label">AREA_LEVEL_PROXY — LSOA/area-level evidence; not a parcel measurement.</p>
<p id="visible-rows">Görünür / izlenen satır: yükleniyor</p>
<table><thead><tr><th>Parcel reference</th><th>Area proxy score</th><th>Source geography</th></tr></thead><tbody id="rows"></tbody></table>
<script>
(async () => {
  const response = await fetch('./security_public_safety_1_area_level_proxy_300.json', {cache: 'no-store'});
  if (!response.ok) throw new Error(`proxy_json_http_${response.status}`);
  const payload = await response.json();
  const valid = payload.output_semantics === 'AREA_LEVEL_PROXY' && payload.parcel_measurement === false && payload.row_count === 300;
  document.body.dataset.loadedCount = String(payload.row_count);
  document.body.dataset.semanticValid = String(valid);
  document.getElementById('visible-rows').textContent = `Görünür / izlenen satır: ${payload.row_count}`;
  document.getElementById('rows').innerHTML = payload.rows.slice(0, 20).map(row => `<tr><td>${row.parcel_id}</td><td>${row.security_score_percent}</td><td>${row.source_geography_level}</td></tr>`).join('');
  if (!valid) throw new Error('area_level_proxy_contract_failed');
})().catch(error => { document.body.dataset.acceptanceError = String(error); console.error(error); });
</script></body></html>
"""


def hydrate() -> tuple[dict[str, Any], dict[str, bool]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8-sig'))
    with CSV_PATH.open('r', encoding='utf-8-sig', newline='') as handle:
        source_rows = list(csv.DictReader(handle))
    geojson = json.loads(GEOJSON_PATH.read_text(encoding='utf-8-sig'))
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        number = parcel_number(row.get('parcel_id'))
        if number is None or not START <= number <= END:
            continue
        item = dict(row)
        item.update({
            'parcel_number': number,
            'measurement_level': 'lsoa',
            'output_semantics': 'AREA_LEVEL_PROXY',
            'parcel_measurement': False,
            'display_disclaimer': 'LSOA/area-level proxy; not a parcel measurement',
        })
        rows.append(item)
    rows.sort(key=lambda item: int(item['parcel_number']))
    feature_ids: list[int] = []
    for feature in geojson.get('features', []):
        properties = feature.get('properties') or {}
        number = parcel_number(properties.get('parcel_id') or properties.get('id'))
        if number is not None and START <= number <= END:
            feature_ids.append(number)
    feature_ids.sort()
    row_ids = [int(item['parcel_number']) for item in rows]
    checks = {
        'manifest_rows_300': int(manifest.get('selected_verified_rows') or 0) == EXPECTED,
        'csv_rows_300': len(rows) == EXPECTED,
        'geojson_rows_300': len(feature_ids) == EXPECTED,
        'csv_geojson_parity': row_ids == feature_ids,
        'ids_1_to_300': row_ids == list(range(1, EXPECTED + 1)),
        'all_in_shard_1': all(START <= value <= END for value in row_ids),
        'source_geography_lsoa': all(str(item.get('source_geography_level', '')).upper() == 'LSOA' for item in rows),
        'official_source_only': all(str(item.get('source_url', '')).startswith('https://data.police.uk/') for item in rows),
    }
    payload = {
        'schema_version': 1,
        'slot_id': SLOT_ID,
        'task_step': TASK_STEP,
        'parcel_partition': {'start': START, 'end': END, 'count': END - START + 1},
        'row_count': len(rows),
        'measurement_level': 'lsoa',
        'output_semantics': 'AREA_LEVEL_PROXY',
        'parcel_measurement': False,
        'display_disclaimer': 'LSOA/area-level proxy; not a parcel measurement',
        'source_url': manifest.get('source_url'),
        'source_snapshot_date': manifest.get('official_api_latest_month'),
        'matching_method': 'parcel_centroid_inside_lsoa_polygon',
        'source_manifest_sha256': file_digest(MANIFEST_PATH),
        'source_csv_sha256': file_digest(CSV_PATH),
        'source_geojson_sha256': file_digest(GEOJSON_PATH),
        'validations': checks,
        'rows': rows,
        'fake_data': False,
        'db_write': False,
        'migration': False,
        'production_deploy': False,
        'final_ready': False,
        'generated_at': now(),
    }
    write_json(DATA_PATH, payload)
    PROBE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROBE_PATH.write_text(probe_html(), encoding='utf-8')
    return payload, checks


def run() -> dict[str, Any]:
    slot_env = os.environ.get('AAYS_SLOT_ID')
    task_id = os.environ.get('AAYS_TASK_ID')
    if slot_env and slot_env != SLOT_ID:
        raise RuntimeError(f'WRONG_SLOT_ENV:{slot_env}')
    payload, hydration_checks = hydrate()
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{port}'
    probe_url = f'{base}/england_map_web/data/aays_21_slots/{SLOT_ID}/security_public_safety_1_acceptance.html?task={task_id or "manual"}'
    data_url = f'{base}/england_map_web/data/aays_21_slots/{SLOT_ID}/security_public_safety_1_area_level_proxy_300.json?task={task_id or "manual"}'
    matrix_url = f'{base}/{MATRIX_PATH}?refresh=security_public_safety_1_20260720'
    try:
        http_proof = {
            'probe_html': http_get(probe_url),
            'proxy_json': http_get(data_url),
            'product_matrix': http_get(matrix_url),
            'canonical_8012_health': http_get('http://127.0.0.1:8012/health', timeout=5.0),
        }
        probe_browser = browser_probe(probe_url)
        matrix_browser = browser_probe(matrix_url)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    probe_dom = normalized(str(probe_browser.get('dom') or ''))
    matrix_dom = normalized(str(matrix_browser.get('dom') or ''))
    probe_checks = {
        'http_200': bool(http_proof['probe_html'].get('ok')),
        'json_http_200': bool(http_proof['proxy_json'].get('ok')),
        'browser_exit_zero': probe_browser.get('exit_code') == 0,
        'visible_rows_300': 'gorunur / izlenen satir: 300' in probe_dom and 'data-loaded-count="300"' in probe_dom,
        'area_level_proxy_visible': 'area_level_proxy' in probe_dom,
        'not_parcel_measurement_visible': 'not a parcel measurement' in probe_dom and 'data-parcel-measurement="false"' in probe_dom,
        'semantic_contract_true': 'data-semantic-valid="true"' in probe_dom,
        'console_zero': probe_browser.get('console_error_count') == 0,
        'dom_hash_present': bool(probe_browser.get('dom_sha256')),
        'http_hash_present': bool(http_proof['probe_html'].get('sha256') and http_proof['proxy_json'].get('sha256')),
    }
    matrix_checks = {
        'http_200': bool(http_proof['product_matrix'].get('ok')),
        'browser_exit_zero': matrix_browser.get('exit_code') == 0,
        'visible_rows_300': 'gorunur / izlenen satir: 300' in matrix_dom or 'visible / monitored rows: 300' in matrix_dom,
        'area_level_proxy_visible': 'area_level_proxy' in matrix_dom and 'not a parcel measurement' in matrix_dom,
        'console_zero': matrix_browser.get('console_error_count') == 0,
        'dom_hash_present': bool(matrix_browser.get('dom_sha256')),
    }
    hydration_pass = all(hydration_checks.values())
    probe_pass = all(probe_checks.values())
    matrix_pass = all(matrix_checks.values())
    acceptance_pass = hydration_pass and probe_pass and matrix_pass
    blockers: list[str] = []
    if not hydration_pass:
        blockers.append('HYDRATION_300_ROW_VALIDATION_FAILED')
    if not probe_pass:
        blockers.append('SHARD_HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE_FAILED')
    if not matrix_pass:
        blockers.append('PRODUCT_MATRIX_AREA_LEVEL_PROXY_DOM_ACCEPTANCE_FAILED')
    return {
        'schema_version': 1,
        'slot_id': SLOT_ID,
        'task_id': task_id,
        'task_step': TASK_STEP,
        'status': 'PASS' if acceptance_pass else 'BLOCKED',
        'acceptance_pass': acceptance_pass,
        'completed_steps': ['HYDRATE_300_ROWS'] + (['HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE'] if acceptance_pass else []),
        'first_unverified_step': None if acceptance_pass else 'HTTP_HASH_DOM_CONSOLE_BROWSER_ACCEPTANCE',
        'blockers': blockers,
        'hydrated_rows': payload['row_count'],
        'measurement_level': 'lsoa',
        'output_semantics': 'AREA_LEVEL_PROXY',
        'parcel_measurement': False,
        'display_disclaimer': 'LSOA/area-level proxy; not a parcel measurement',
        'hydration_checks': hydration_checks,
        'hash_proof': {
            'source_manifest_sha256': payload['source_manifest_sha256'],
            'source_csv_sha256': payload['source_csv_sha256'],
            'source_geojson_sha256': payload['source_geojson_sha256'],
            'proxy_json_sha256': file_digest(DATA_PATH),
            'probe_html_sha256': file_digest(PROBE_PATH),
        },
        'http_proof': http_proof,
        'probe_browser': {key: value for key, value in probe_browser.items() if key != 'dom'},
        'probe_checks': probe_checks,
        'product_matrix_browser': {key: value for key, value in matrix_browser.items() if key != 'dom'},
        'product_matrix_checks': matrix_checks,
        'outputs': [DATA_PATH.relative_to(ROOT).as_posix(), PROBE_PATH.relative_to(ROOT).as_posix(), REPORT_JSON.relative_to(ROOT).as_posix(), REPORT_MD.relative_to(ROOT).as_posix()],
        'fake_data': False,
        'db_write': False,
        'migration': False,
        'production_deploy': False,
        'final_ready': False,
        'product_final_ready': False,
        'checked_at': now(),
    }


def write_report(result: dict[str, Any]) -> None:
    write_json(REPORT_JSON, result)
    lines = [
        '# Security / Public Safety Shard 1 — HTTP, Hash, DOM, Console and Browser Acceptance',
        '',
        f'- SLOT_ID: `{SLOT_ID}`',
        f'- Task: `{result.get("task_id")}`',
        f'- Parcel partition: `{START}-{END}`',
        f'- Status: `{result.get("status")}`',
        f'- Hydrated rows: `{result.get("hydrated_rows")}`',
        '- Data semantics: `AREA_LEVEL_PROXY`',
        '- Parcel measurement: `false`',
        '- Display disclaimer: `LSOA/area-level proxy; not a parcel measurement`',
        '',
        '## Acceptance',
        '',
        f'- Shard probe checks: `{json.dumps(result.get("probe_checks"), ensure_ascii=False, sort_keys=True)}`',
        f'- Product matrix checks: `{json.dumps(result.get("product_matrix_checks"), ensure_ascii=False, sort_keys=True)}`',
        f'- Blockers: `{”; ”.join(result.get("blockers") or []) or "none"}`',
        '',
        '## Safety',
        '',
        '`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.',
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> int:
    try:
        result = run()
    except Exception as exc:
        result = {
            'schema_version': 1,
            'slot_id': SLOT_ID,
            'task_id': os.environ.get('AAYS_TASK_ID'),
            'task_step': TASK_STEP,
            'status': 'BLOCKED',
            'acceptance_pass': False,
            'completed_steps': [],
            'first_unverified_step': TASK_STEP,
            'blockers': [f'{type(exc).__name__}: {exc}'],
            'output_semantics': 'AREA_LEVEL_PROXY',
            'parcel_measurement': False,
            'fake_data': False,
            'db_write': False,
            'migration': False,
            'production_deploy': False,
            'final_ready': False,
            'product_final_ready': False,
            'checked_at': now(),
        }
    write_report(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

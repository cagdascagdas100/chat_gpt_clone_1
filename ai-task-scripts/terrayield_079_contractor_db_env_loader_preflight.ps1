$ErrorActionPreference = "Stop"
$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$AuditPath = Join-Path $ResultsDir "terrayield-079-contractor-db-env-loader-preflight.audit.json"
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
Set-Location $ProjectRoot
$py = @"
import datetime as dt
import json
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse
sys.path.insert(0, str(Path(r'$ProjectRoot') / 'scripts'))
from contractor_env import load_contractor_env, redact_secrets
project_root = Path(r'$ProjectRoot')
env_info = load_contractor_env(project_root)
report = dict(env_info['report'])
result = {
    'task_id': 'terrayield-079-contractor-db-env-loader-preflight',
    'project_root': str(project_root),
    'env_local_present': bool((project_root / '.env.local').exists()),
    'loaded_paths': dict(env_info['loaded_paths']),
    'database_url_present': report.get('database_url_present', False),
    'pghost_present': report.get('pghost_present', False),
    'pgdatabase_present': report.get('pgdatabase_present', False),
    'pguser_present': report.get('pguser_present', False),
    'pgpassword_present': report.get('pgpassword_present', False),
    'pgport_present': report.get('pgport_present', False),
    'db_credentials_present': report.get('db_credentials_present', False),
    'tcp_connect_ok': False,
    'db_query_ok': False,
    'connection_ok': False,
    'generated_at': dt.datetime.now(dt.UTC).isoformat(),
}
database_url = env_info.get('database_url')
if not database_url:
    result['status'] = 'blocked_missing_credentials'
    result['next_action'] = 'Add DATABASE_URL or PGHOST/PGDATABASE/PGUSER/PGPASSWORD to Codex/runner secrets or local .env.local, then rerun preflight.'
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0)
parsed = urlparse(database_url)
try:
    with socket.create_connection((parsed.hostname, parsed.port or 5432), timeout=8):
        result['tcp_connect_ok'] = True
except Exception as exc:
    result['status'] = 'blocked_db_tcp_connect_failed'
    result['error'] = redact_secrets(exc, env_info)
    result['next_action'] = 'Check DB host, port, firewall, and local tunnel/container status, then rerun preflight.'
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0)
try:
    import psycopg
    with psycopg.connect(database_url, connect_timeout=8) as conn:
        with conn.cursor() as cur:
            cur.execute('select 1')
            row = cur.fetchone()
            result['db_query_ok'] = bool(row and row[0] == 1)
except Exception as exc:
    result['status'] = 'blocked_db_query_failed'
    result['error'] = redact_secrets(exc, env_info)
    result['next_action'] = 'Check database name/user/password and psycopg connectivity, then rerun preflight.'
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0)
result['connection_ok'] = bool(result['tcp_connect_ok'] and result['db_query_ok'])
result['status'] = 'completed' if result['connection_ok'] else 'blocked_db_query_failed'
result['next_action'] = 'Proceed to schema apply, DB load, parcel match, and app export.' if result['connection_ok'] else 'Check DB connectivity, then rerun preflight.'
print(json.dumps(result, sort_keys=True))
"@
$jsonText = python -c $py
Set-Content -Path $AuditPath -Value $jsonText -Encoding UTF8
$payload = $jsonText | ConvertFrom-Json
Write-Host "audit_path=$AuditPath"
Write-Host "status=$($payload.status)"
Write-Host "db_credentials_present=$($payload.db_credentials_present)"
Write-Host "connection_ok=$($payload.connection_ok)"
if ($payload.status -eq "completed") { exit 0 }
exit 2

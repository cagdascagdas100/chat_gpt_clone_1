$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-078-contractor-db-credential-preflight'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$TempRoot = 'C:\AAYS1_GITHUB_BRIDGE\pytest_tmp'
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

function HasValue([string]$Name) {
  $v = [Environment]::GetEnvironmentVariable($Name)
  return -not [string]::IsNullOrWhiteSpace($v)
}

function SafeError([object]$Err) {
  if ($null -eq $Err) { return $null }
  $text = [string]$Err
  $secret = [Environment]::GetEnvironmentVariable('PGPASSWORD')
  $url = [Environment]::GetEnvironmentVariable('DATABASE_URL')
  if (-not [string]::IsNullOrWhiteSpace($secret)) { $text = $text.Replace($secret, '[REDACTED]') }
  if (-not [string]::IsNullOrWhiteSpace($url)) { $text = $text.Replace($url, '[REDACTED_DATABASE_URL]') }
  return $text
}

$databaseUrlPresent = HasValue 'DATABASE_URL'
$pgHostPresent = HasValue 'PGHOST'
$pgDatabasePresent = HasValue 'PGDATABASE'
$pgUserPresent = HasValue 'PGUSER'
$pgPasswordPresent = HasValue 'PGPASSWORD'
$pgPortPresent = HasValue 'PGPORT'
$pgVarSetComplete = $pgHostPresent -and $pgDatabasePresent -and $pgUserPresent -and $pgPasswordPresent
$dbCredentialsPresent = $databaseUrlPresent -or $pgVarSetComplete

$hostName = $null
$port = 5432
if ($databaseUrlPresent) {
  try {
    $uri = [System.Uri]([Environment]::GetEnvironmentVariable('DATABASE_URL'))
    $hostName = $uri.Host
    if ($uri.Port -gt 0) { $port = $uri.Port }
  } catch {}
} elseif ($pgHostPresent) {
  $hostName = [Environment]::GetEnvironmentVariable('PGHOST')
  if ($pgPortPresent) {
    try { $port = [int]([Environment]::GetEnvironmentVariable('PGPORT')) } catch { $port = 5432 }
  }
}

$tcpOk = $false
$tcpError = $null
if (-not [string]::IsNullOrWhiteSpace($hostName)) {
  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $async = $client.BeginConnect($hostName, $port, $null, $null)
    $waitOk = $async.AsyncWaitHandle.WaitOne(5000, $false)
    if ($waitOk) {
      $client.EndConnect($async)
      $tcpOk = $true
    } else {
      $tcpError = 'tcp_connect_timeout'
    }
    $client.Close()
  } catch {
    $tcpError = SafeError $_.Exception.Message
  }
}

$pythonJsonPath = Join-Path $TempRoot ($TaskId + '.python-db-check.json')
$pythonScriptPath = Join-Path $TempRoot ($TaskId + '.python-db-check.py')
@'
import json
import os
import sys

out_path = os.environ.get('AAYS_DB_PREFLIGHT_OUT')
result = {
    'python_available': True,
    'driver': None,
    'driver_available': False,
    'db_connection_ok': False,
    'db_query_ok': False,
    'error_type': None,
    'error_message_sanitized': None,
}

def sanitize(msg: object) -> str:
    text = str(msg)
    for key in ('DATABASE_URL', 'PGPASSWORD'):
        val = os.environ.get(key)
        if val:
            text = text.replace(val, '[REDACTED]')
    return text

conninfo = os.environ.get('DATABASE_URL')
if not conninfo:
    host = os.environ.get('PGHOST')
    db = os.environ.get('PGDATABASE')
    user = os.environ.get('PGUSER')
    password = os.environ.get('PGPASSWORD')
    port = os.environ.get('PGPORT') or '5432'
    if host and db and user and password:
        conninfo = f'host={host} port={port} dbname={db} user={user} password={password} connect_timeout=5'

try:
    try:
        import psycopg
        result['driver'] = 'psycopg'
        result['driver_available'] = True
        if conninfo:
            with psycopg.connect(conninfo, connect_timeout=5) as conn:
                result['db_connection_ok'] = True
                with conn.cursor() as cur:
                    cur.execute('select 1')
                    row = cur.fetchone()
                    result['db_query_ok'] = bool(row and row[0] == 1)
    except ImportError:
        import psycopg2
        result['driver'] = 'psycopg2'
        result['driver_available'] = True
        if conninfo:
            conn = psycopg2.connect(conninfo, connect_timeout=5)
            try:
                result['db_connection_ok'] = True
                cur = conn.cursor()
                try:
                    cur.execute('select 1')
                    row = cur.fetchone()
                    result['db_query_ok'] = bool(row and row[0] == 1)
                finally:
                    cur.close()
            finally:
                conn.close()
except Exception as exc:
    result['error_type'] = exc.__class__.__name__
    result['error_message_sanitized'] = sanitize(exc)

if out_path:
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
else:
    print(json.dumps(result, indent=2))
'@ | Set-Content -Path $pythonScriptPath -Encoding UTF8

$env:AAYS_DB_PREFLIGHT_OUT = $pythonJsonPath
$pythonExitCode = $null
$pythonCheck = $null
try {
  & python $pythonScriptPath | Out-Null
  $pythonExitCode = $LASTEXITCODE
  if (Test-Path $pythonJsonPath) {
    $pythonCheck = Get-Content $pythonJsonPath -Raw | ConvertFrom-Json
  }
} catch {
  $pythonExitCode = 999
  $pythonCheck = [ordered]@{
    python_available = $false
    driver = $null
    driver_available = $false
    db_connection_ok = $false
    db_query_ok = $false
    error_type = $_.Exception.GetType().Name
    error_message_sanitized = (SafeError $_.Exception.Message)
  }
}

$dbConnectionOk = $false
$dbQueryOk = $false
$driverAvailable = $false
$driver = $null
$pythonErrorType = $null
$pythonErrorMessage = $null
if ($null -ne $pythonCheck) {
  $dbConnectionOk = [bool]$pythonCheck.db_connection_ok
  $dbQueryOk = [bool]$pythonCheck.db_query_ok
  $driverAvailable = [bool]$pythonCheck.driver_available
  $driver = $pythonCheck.driver
  $pythonErrorType = $pythonCheck.error_type
  $pythonErrorMessage = $pythonCheck.error_message_sanitized
}

$status = if ($dbCredentialsPresent -and ($dbQueryOk -or $tcpOk)) { 'completed' } elseif ($dbCredentialsPresent) { 'failed' } else { 'blocked_missing_credentials' }
$progress = if ($dbQueryOk) { 60 } elseif ($tcpOk) { 58 } elseif ($dbCredentialsPresent) { 54 } else { 52 }
$nextAction = if (-not $dbCredentialsPresent) {
  'Set DATABASE_URL or PGHOST/PGDATABASE/PGUSER/PGPASSWORD in the runner environment, then rerun DB credential preflight.'
} elseif ($dbQueryOk) {
  'DB credential preflight passed. Proceed to schema apply and contractor DB load.'
} elseif ($tcpOk -and -not $driverAvailable) {
  'TCP connectivity is available but Python PostgreSQL driver is missing. Install psycopg or psycopg2, then rerun preflight.'
} elseif ($tcpOk) {
  'TCP connectivity is available but DB query failed. Inspect sanitized driver error and credentials.'
} else {
  'Credentials are present but DB host/port connection failed. Check host, port, firewall, and credential scope.'
}

$audit = [ordered]@{
  task_id = $TaskId
  status = $status
  generated_at = (Get-Date).ToString('s')
  database_url_present = $databaseUrlPresent
  pghost_present = $pgHostPresent
  pgdatabase_present = $pgDatabasePresent
  pguser_present = $pgUserPresent
  pgpassword_present = $pgPasswordPresent
  pgport_present = $pgPortPresent
  db_credentials_present = $dbCredentialsPresent
  db_host_present = (-not [string]::IsNullOrWhiteSpace($hostName))
  db_port = $port
  tcp_connect_ok = $tcpOk
  tcp_error_sanitized = $tcpError
  python_exit_code = $pythonExitCode
  python_driver = $driver
  python_driver_available = $driverAvailable
  db_connection_ok = $dbConnectionOk
  db_query_ok = $dbQueryOk
  python_error_type = $pythonErrorType
  python_error_message_sanitized = $pythonErrorMessage
  plan_progress_percent = $progress
  plan_percent_remaining = (100 - $progress)
  next_action = $nextAction
}

$auditPath = Join-Path $ResultsDir ($TaskId + '.audit.json')
$audit | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $auditPath

try {
  Push-Location $BridgeRoot
  git add ai-results 2>&1 | Out-String | Write-Output
  git commit -m ('chore(ai): contractor db credential preflight ' + $TaskId) 2>&1 | Out-String | Write-Output
  git push origin main 2>&1 | Out-String | Write-Output
  Pop-Location
} catch { try { Pop-Location } catch {}; Write-Output ('GIT_PUSH_WARNING=' + (SafeError $_.Exception.Message)) }

Write-Output ('STATUS=' + $status)
Write-Output ('DB_CREDENTIALS_PRESENT=' + $dbCredentialsPresent)
Write-Output ('TCP_CONNECT_OK=' + $tcpOk)
Write-Output ('DB_QUERY_OK=' + $dbQueryOk)
Write-Output ('PLAN_PROGRESS_PERCENT=' + $progress)
Write-Output ('NEXT_ACTION=' + $nextAction)
if ($status -eq 'completed') { exit 0 }
exit 1

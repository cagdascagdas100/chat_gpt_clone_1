$ErrorActionPreference = 'Continue'

$TaskId = 'terrayield-080-contractor-schema-load-match-export'
$BridgeRoot = 'C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$LegalRoot = 'E:\AAYS_DATA\legal'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$HandoffDir = Join-Path $BridgeRoot 'ai-handoff'
$TempRoot = 'C:\AAYS1_GITHUB_BRIDGE\pytest_tmp'
$LogsDir = Join-Path $BridgeRoot 'ai-runner-logs'

New-Item -ItemType Directory -Force -Path $ResultsDir,$HandoffDir,$TempRoot,$LogsDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $LegalRoot 'raw\companies_house'),(Join-Path $LegalRoot 'raw\procurement'),(Join-Path $LegalRoot 'processed'),(Join-Path $LegalRoot 'exports'),(Join-Path $LegalRoot 'reports') | Out-Null
$env:TEMP = $TempRoot
$env:TMP = $TempRoot

function Redact([string]$Text) {
  if ($null -eq $Text) { return '' }
  $out = [string]$Text
  foreach ($name in @('DATABASE_URL','PGPASSWORD','SUPABASE_SERVICE_ROLE_KEY','SUPABASE_ANON_KEY','JWT_SECRET','API_KEY','TOKEN')) {
    $v = [Environment]::GetEnvironmentVariable($name)
    if (-not [string]::IsNullOrWhiteSpace($v)) { $out = $out.Replace($v, '[REDACTED_' + $name + ']') }
  }
  $out = [regex]::Replace($out, 'postgresql://[^\s"'']+', 'postgresql://[REDACTED]')
  return $out
}

function CountRows([string]$Path) {
  try {
    if (Test-Path $Path) {
      $lineCount = 0
      $reader = [System.IO.File]::OpenText($Path)
      try { while ($null -ne $reader.ReadLine()) { $lineCount++ } } finally { $reader.Close() }
      if ($lineCount -gt 0) { return ($lineCount - 1) }
    }
  } catch {}
  return 0
}

function FileInfo([string]$Path) {
  if (Test-Path $Path) {
    $i = Get-Item $Path
    return [ordered]@{ path=$Path; exists=$true; bytes=$i.Length; modified=$i.LastWriteTime.ToString('s') }
  }
  return [ordered]@{ path=$Path; exists=$false; bytes=0; modified=$null }
}

function Run-Step([string]$Name, [string]$Exe, [string[]]$Args) {
  $logPath = Join-Path $LogsDir ($TaskId + '.' + $Name + '.log')
  $started = Get-Date
  $output = ''
  $exitCode = 999
  try {
    Push-Location $ProjectRoot
    $output = (& $Exe @Args 2>&1 | Out-String)
    $exitCode = $LASTEXITCODE
    Pop-Location
  } catch {
    try { Pop-Location } catch {}
    $output = $_.Exception.Message
    $exitCode = 999
  }
  $safeOutput = Redact $output
  $safeOutput | Set-Content -Path $logPath -Encoding UTF8
  $preview = $safeOutput
  if ($preview.Length -gt 2000) { $preview = $preview.Substring([Math]::Max(0, $preview.Length - 2000)) }
  return [ordered]@{
    name=$Name
    exe=$Exe
    args=($Args -join ' ')
    exit_code=$exitCode
    started_at=$started.ToString('s')
    ended_at=(Get-Date).ToString('s')
    log_path=$logPath
    output_tail=$preview
  }
}

$steps = New-Object System.Collections.Generic.List[object]
$errors = New-Object System.Collections.Generic.List[string]

if (-not (Test-Path $ProjectRoot)) {
  $errors.Add('project_root_missing')
} else {
  $compileArgs = @('-m','py_compile',
    'scripts\contractor_env.py',
    'scripts\contractor_collect_companies_house.py',
    'scripts\contractor_collect_procurement_ocds.py',
    'scripts\contractor_normalize_and_score.py',
    'scripts\contractor_load_to_postgres.py',
    'scripts\contractor_match_to_parcels.py',
    'scripts\contractor_export_for_app.py')
  $steps.Add((Run-Step 'py_compile' 'python' $compileArgs))

  $schemaRunner = Join-Path $TempRoot ($TaskId + '.schema_apply.py')
@'
import json
import os
from pathlib import Path

project = Path(r'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence')
bridge_secret = Path(r'C:\AAYS1_GITHUB_BRIDGE\local-secrets\contractor-db.env')
result_path = Path(os.environ.get('AAYS_SCHEMA_APPLY_RESULT', r'C:\AAYS1_GITHUB_BRIDGE\pytest_tmp\schema_apply_result.json'))

def load_dotenv(path: Path):
    if not path.exists():
        return False
    for raw in path.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v
    return True

loaded = {
    'env_local_present': load_dotenv(project / '.env.local'),
    'env_present': load_dotenv(project / '.env'),
    'bridge_local_secrets_present': load_dotenv(bridge_secret),
}

def build_conninfo():
    if os.environ.get('DATABASE_URL'):
        return os.environ['DATABASE_URL']
    host = os.environ.get('PGHOST')
    db = os.environ.get('PGDATABASE')
    user = os.environ.get('PGUSER')
    password = os.environ.get('PGPASSWORD')
    port = os.environ.get('PGPORT') or '5432'
    if host and db and user and password:
        return f'host={host} port={port} dbname={db} user={user} password={password} connect_timeout=10'
    return None

out = {
    'loaded_paths': loaded,
    'db_credentials_present': bool(os.environ.get('DATABASE_URL') or (os.environ.get('PGHOST') and os.environ.get('PGDATABASE') and os.environ.get('PGUSER') and os.environ.get('PGPASSWORD'))),
    'schema_file_present': False,
    'schema_apply_ok': False,
    'db_query_ok': False,
    'driver': None,
    'error_type': None,
    'error_message_sanitized': None,
}

def sanitize(msg):
    text = str(msg)
    for key in ('DATABASE_URL','PGPASSWORD'):
        val = os.environ.get(key)
        if val:
            text = text.replace(val, '[REDACTED]')
    return text

try:
    try:
        import psycopg
        out['driver'] = 'psycopg'
        connect = psycopg.connect
    except ImportError:
        import psycopg2
        out['driver'] = 'psycopg2'
        connect = psycopg2.connect
    conninfo = build_conninfo()
    if not conninfo:
        raise RuntimeError('missing_db_credentials')
    schema = project / 'db_transfer' / 'schema_apply.sql'
    out['schema_file_present'] = schema.exists()
    sql = schema.read_text(encoding='utf-8', errors='ignore') if schema.exists() else ''
    with connect(conninfo, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute('select 1')
            row = cur.fetchone()
            out['db_query_ok'] = bool(row and row[0] == 1)
            if sql.strip():
                cur.execute(sql)
                out['schema_apply_ok'] = True
            else:
                out['schema_apply_ok'] = False
        try:
            conn.commit()
        except Exception:
            pass
except Exception as exc:
    out['error_type'] = exc.__class__.__name__
    out['error_message_sanitized'] = sanitize(exc)

result_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
print(json.dumps(out, indent=2))
'@ | Set-Content -Path $schemaRunner -Encoding UTF8
  $schemaResult = Join-Path $TempRoot ($TaskId + '.schema_apply.result.json')
  $env:AAYS_SCHEMA_APPLY_RESULT = $schemaResult
  $steps.Add((Run-Step 'schema_apply' 'python' @($schemaRunner)))

  $scriptSequence = @(
    @{name='collect_companies_house'; path='scripts\contractor_collect_companies_house.py'},
    @{name='collect_procurement_ocds'; path='scripts\contractor_collect_procurement_ocds.py'},
    @{name='normalize_and_score'; path='scripts\contractor_normalize_and_score.py'},
    @{name='load_to_postgres'; path='scripts\contractor_load_to_postgres.py'},
    @{name='match_to_parcels'; path='scripts\contractor_match_to_parcels.py'},
    @{name='export_for_app'; path='scripts\contractor_export_for_app.py'}
  )
  foreach ($s in $scriptSequence) {
    $full = Join-Path $ProjectRoot $s.path
    if (Test-Path $full) {
      $steps.Add((Run-Step $s.name 'python' @($s.path)))
    } else {
      $steps.Add([ordered]@{name=$s.name; exe='python'; args=$s.path; exit_code=998; started_at=(Get-Date).ToString('s'); ended_at=(Get-Date).ToString('s'); log_path=$null; output_tail='script_missing'})
    }
  }
}

$scorePath = Join-Path $LegalRoot 'processed\contractor_scores.csv'
$appCsvPath = Join-Path $LegalRoot 'exports\contractor_app_export.csv'
$appJsonlPath = Join-Path $LegalRoot 'exports\contractor_app_export.jsonl'
$matchPath = Join-Path $LegalRoot 'processed\contractor_parcel_matches.csv'
$normalizedPath = Join-Path $LegalRoot 'processed\contractors_normalized.csv'
$eventsPath = Join-Path $LegalRoot 'processed\procurement_events_normalized.csv'
$cfPath = Join-Path $LegalRoot 'raw\procurement\contracts_finder_ocds.jsonl'
$ftPath = Join-Path $LegalRoot 'raw\procurement\find_tender_ocds.jsonl'
$chPath = Join-Path $LegalRoot 'raw\companies_house\company_profiles.jsonl'

$fileChecks = @(
  (FileInfo (Join-Path $ProjectRoot 'db_transfer\schema_apply.sql')),
  (FileInfo (Join-Path $ProjectRoot 'db_transfer\load_order.csv')),
  (FileInfo (Join-Path $ProjectRoot 'db_transfer\export_manifest.csv')),
  (FileInfo (Join-Path $ProjectRoot 'db_transfer\runbook_windows_linux.txt')),
  (FileInfo $chPath),
  (FileInfo $cfPath),
  (FileInfo $ftPath),
  (FileInfo $normalizedPath),
  (FileInfo $eventsPath),
  (FileInfo $scorePath),
  (FileInfo $matchPath),
  (FileInfo $appCsvPath),
  (FileInfo $appJsonlPath)
)

$scoreRows = CountRows $scorePath
$appRows = CountRows $appCsvPath
$matchRows = CountRows $matchPath
$normalizedRows = CountRows $normalizedPath
$eventRows = CountRows $eventsPath

$dbCredsPresent = $false
try {
  $dbCredsPresent = [bool]($env:DATABASE_URL -or ($env:PGHOST -and $env:PGDATABASE -and $env:PGUSER -and $env:PGPASSWORD) -or (Test-Path (Join-Path $ProjectRoot '.env.local')))
} catch {}

$failedSteps = @($steps | Where-Object { $_.exit_code -ne 0 })
$plan = 58
if ($dbCredsPresent) { $plan = 60 }
if ((Test-Path (Join-Path $ProjectRoot 'db_transfer\schema_apply.sql'))) { $plan = [Math]::Max($plan, 64) }
if ($normalizedRows -gt 0 -or $eventRows -gt 0 -or $scoreRows -gt 0) { $plan = [Math]::Max($plan, 74) }
if ($scoreRows -gt 0) { $plan = [Math]::Max($plan, 80) }
if ($matchRows -gt 0) { $plan = [Math]::Max($plan, 90) }
if ($appRows -gt 0) { $plan = [Math]::Max($plan, 100) }

$status = if ($appRows -gt 0 -and $matchRows -gt 0 -and $failedSteps.Count -eq 0) { 'completed' } elseif ($failedSteps.Count -gt 0) { 'partial_failed' } else { 'partial_completed' }
$next = if ($status -eq 'completed') { 'Run final audit and integrate app export.' } elseif (-not $dbCredsPresent) { 'DB credentials not visible. Restore .env.local or runner secrets and rerun.' } elseif ($scoreRows -lt 1) { 'Inspect collect/normalize logs; produce contractor_scores.csv then rerun load/match/export.' } elseif ($matchRows -lt 1) { 'Inspect parcel match logs and parcel source availability.' } elseif ($appRows -lt 1) { 'Inspect app export logs and rerun export.' } else { 'Inspect failed step logs and rerun from failed stage.' }

$audit = [ordered]@{
  task_id=$TaskId
  status=$status
  generated_at=(Get-Date).ToString('s')
  project_root=$ProjectRoot
  legal_root=$LegalRoot
  db_credentials_present=$dbCredsPresent
  steps=$steps
  failed_step_count=$failedSteps.Count
  file_checks=$fileChecks
  normalized_rows=$normalizedRows
  procurement_event_rows=$eventRows
  contractor_score_rows=$scoreRows
  parcel_match_rows=$matchRows
  app_export_rows=$appRows
  plan_progress_percent=$plan
  plan_percent_remaining=(100 - $plan)
  next_action=$next
}
$auditPath = Join-Path $ResultsDir ($TaskId + '.audit.json')
$audit | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -Path $auditPath

$reportPath = Join-Path $HandoffDir 'aays1-contractor-schema-load-match-export-status.md'
$lines = @(
  '# Contractor Schema Load Match Export Status',
  '',
  ('Generated at: ' + $audit.generated_at),
  ('Status: ' + $status),
  ('Plan completed: ' + $plan + '%'),
  ('Plan remaining: ' + (100 - $plan) + '%'),
  ('DB credentials present: ' + $dbCredsPresent),
  ('Failed step count: ' + $failedSteps.Count),
  '',
  '## Rows',
  ('- normalized_rows: ' + $normalizedRows),
  ('- procurement_event_rows: ' + $eventRows),
  ('- contractor_score_rows: ' + $scoreRows),
  ('- parcel_match_rows: ' + $matchRows),
  ('- app_export_rows: ' + $appRows),
  '',
  '## Next Action',
  $next,
  '',
  '## Step Exit Codes'
)
foreach ($s in $steps) { $lines += ('- ' + $s.name + ': exit_code=' + $s.exit_code + ' log=' + $s.log_path) }
$lines | Set-Content -Encoding UTF8 -Path $reportPath

try {
  Push-Location $BridgeRoot
  git add ai-results ai-handoff ai-runner-logs 2>&1 | Out-String | Write-Output
  git commit -m ('chore(ai): contractor schema load match export ' + $TaskId) 2>&1 | Out-String | Write-Output
  git push origin main 2>&1 | Out-String | Write-Output
  Pop-Location
} catch { try { Pop-Location } catch {}; Write-Output ('GIT_PUSH_WARNING=' + (Redact $_.Exception.Message)) }

Write-Output ('STATUS=' + $status)
Write-Output ('PLAN_PROGRESS_PERCENT=' + $plan)
Write-Output ('PLAN_PERCENT_REMAINING=' + (100 - $plan))
Write-Output ('NEXT_ACTION=' + $next)
if ($status -eq 'completed') { exit 0 }
exit 1

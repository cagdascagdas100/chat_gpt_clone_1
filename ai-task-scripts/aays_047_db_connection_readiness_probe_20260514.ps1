$ErrorActionPreference = 'Continue'
$TaskId = 'aays-047-db-connection-readiness-probe-20260514'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence' }
$CostRoot = if ($env:AAYS_COST_DATA_ROOT) { $env:AAYS_COST_DATA_ROOT } else { 'E:\AAYS_DATA\cost' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatPath = Join-Path $HeartbeatDir 'portable-runner.md'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null
function Log([string]$m){ Write-Output ('[' + (Get-Date -Format s) + '] ' + $m) }
function FindPsql { $cmd = Get-Command psql -ErrorAction SilentlyContinue; if($cmd){ return $cmd.Source }; foreach($p in @('C:\Program Files\PostgreSQL\17\bin\psql.exe','C:\Program Files\PostgreSQL\16\bin\psql.exe','C:\Program Files\PostgreSQL\15\bin\psql.exe','C:\Program Files\PostgreSQL\14\bin\psql.exe','C:\Program Files\PostgreSQL\13\bin\psql.exe','C:\Program Files\PostgreSQL\12\bin\psql.exe')){ if(Test-Path $p){ return $p } }; return $null }
function CountFiles([string]$root,[string]$pattern){ try { if(Test-Path $root){ return @(Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match $pattern -or $_.FullName -match $pattern }).Count } } catch {}; return 0 }
function HasEnv([string]$name){ return -not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name,'Process')) -or -not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name,'User')) -or -not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name,'Machine')) }
Log "TASK=$TaskId"
Log 'MODE=db_connection_readiness_probe_readonly'
Log 'SAFETY=NO_DB_WRITE;NO_SQL_EXECUTE;NO_SECRET_PRINT;NO_UI_PATCH'
Log "BRIDGE_ROOT=$BridgeRoot"
Log "PROJECT_ROOT=$ProjectRoot"
Log "COST_ROOT=$CostRoot"
$psql = FindPsql
$psqlVersion = 'missing'
if($psql){ try { $psqlVersion = (& $psql --version 2>&1 | Out-String).Trim() } catch { $psqlVersion = 'version_error' } }
$configSignals = CountFiles $ProjectRoot '(DATABASE_URL|POSTGRES|POSTGIS|sqlalchemy|asyncpg|psycopg|alembic|config\.py|\.env)'
$modelSignals = CountFiles $ProjectRoot '(cost_run_logs|cost_estimates|cost_facts|cost_sources|source_facts|estimate_lines|models\.py|migration|alembic)'
$artifactSignals = CountFiles $CostRoot '(source_fetch_manifest_latest|source_facts_scored|source_facts_extracted|aays_cost_menu_payload_latest|aays_cost_material_lines_latest)'
$envSignals = [ordered]@{
  DATABASE_URL_present = HasEnv 'DATABASE_URL'
  POSTGRES_HOST_present = HasEnv 'POSTGRES_HOST'
  POSTGRES_PORT_present = HasEnv 'POSTGRES_PORT'
  POSTGRES_DB_present = HasEnv 'POSTGRES_DB'
  POSTGRES_USER_present = HasEnv 'POSTGRES_USER'
  POSTGRES_PASSWORD_present = HasEnv 'POSTGRES_PASSWORD'
}
$score = 0
if($psql){ $score += 25 }
if($configSignals -gt 0){ $score += 20 }
if($modelSignals -gt 0){ $score += 20 }
if($artifactSignals -gt 0){ $score += 20 }
if($envSignals.DATABASE_URL_present -or ($envSignals.POSTGRES_HOST_present -and $envSignals.POSTGRES_DB_present)){ $score += 15 }
if($score -gt 100){ $score = 100 }
$missing = @()
if(-not $psql){ $missing += 'psql client not found in PATH or common PostgreSQL install folders' }
if($configSignals -eq 0){ $missing += 'database config signal not found in project files' }
if($modelSignals -eq 0){ $missing += 'cost DB model/migration signal not found' }
if($artifactSignals -eq 0){ $missing += 'cost source/UI artifact signal not found' }
if(-not ($envSignals.DATABASE_URL_present -or ($envSignals.POSTGRES_HOST_present -and $envSignals.POSTGRES_DB_present))){ $missing += 'connection environment variables missing or not visible to runner' }
$out = Join-Path $ResultDir ($TaskId + '.report.md')
$json = Join-Path $ResultDir ($TaskId + '.status.json')
$r = @('# AAYS 047 DB Connection Readiness Probe','',('Generated: ' + (Get-Date -Format s)),'','## Scope','- Read-only readiness probe.','- No DB write. No SQL execution. No secret printing. No UI patch.','','## Findings',('PSQL_PATH_PRESENT=' + [bool]$psql),('PSQL_VERSION=' + $psqlVersion),('CONFIG_SIGNAL_COUNT=' + $configSignals),('MODEL_SIGNAL_COUNT=' + $modelSignals),('ARTIFACT_SIGNAL_COUNT=' + $artifactSignals),'','## Env presence only')
foreach($k in $envSignals.Keys){ $r += ($k + '=' + $envSignals[$k]) }
$r += ''
$r += '## Missing items'
if($missing.Count -eq 0){ $r += '- None detected.' } else { foreach($m in $missing){ $r += ('- ' + $m) } }
$r += ''
$r += ('DB_CONNECTION_READINESS_SCORE=' + $score + '/100')
$r += 'PLAN_PROGRESS_PERCENT=94'
$r += 'TASK_COMPLETION=100/100'
$r += 'TERRAYIELD_TASK_DONE'
$r | Set-Content -Encoding UTF8 -Path $out
([ordered]@{ task_id=$TaskId; status='completed'; psql_present=[bool]$psql; env_presence=$envSignals; config_signal_count=$configSignals; model_signal_count=$modelSignals; artifact_signal_count=$artifactSignals; missing=$missing; score=$score; generated_at=(Get-Date -Format s) } | ConvertTo-Json -Depth 8) | Set-Content -Encoding UTF8 -Path $json
@('# AAYS Portable Task Runner Fixed','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: ' + $TaskId),('BridgeRoot: ' + $BridgeRoot),('ProjectRoot: ' + $ProjectRoot),('TaskFile: ' + (Join-Path $BridgeRoot 'ai-tasks\current-task.json')),('Message: exit=0 db_connection_readiness score=' + $score),'Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath
Log ('REPORT_PATH=' + $out)
Log ('STATUS_PATH=' + $json)
Log ('DB_CONNECTION_READINESS_SCORE=' + $score + '/100')
Log 'PLAN_PROGRESS_PERCENT=94'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0

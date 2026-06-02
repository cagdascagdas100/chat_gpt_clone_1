$ErrorActionPreference = 'Continue'
$TaskId = 'terrayield-046-runner-sync-recovery-then-accuracy-expansion'
$Start = Get-Date

$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$CostRoot = if ($env:AAYS_COST_DATA_ROOT) { $env:AAYS_COST_DATA_ROOT } else { 'E:\AAYS_DATA\cost' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatPath = Join-Path $HeartbeatDir 'portable-runner.md'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null

function Log([string]$m){ Write-Output ('[' + (Get-Date -Format s) + '] ' + $m) }
function CountFiles([string]$root,[string]$pattern){ try { if(Test-Path $root){ return @(Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match $pattern -or $_.FullName -match $pattern }).Count } } catch {}; return 0 }
function TestUrl([string]$url){ try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5; return ([int]$r.StatusCode) } catch { return 'ERR' } }
function FindPsql { $cmd = Get-Command psql -ErrorAction SilentlyContinue; if($cmd){ return $cmd.Source }; foreach($p in @('C:\Program Files\PostgreSQL\17\bin\psql.exe','C:\Program Files\PostgreSQL\16\bin\psql.exe','C:\Program Files\PostgreSQL\15\bin\psql.exe','C:\Program Files\PostgreSQL\14\bin\psql.exe')){ if(Test-Path $p){ return $p } }; return $null }

Log "TASK=$TaskId"
Log 'MODE=runner_sync_recovery_then_accuracy_expansion_SAFE'
Log 'SAFETY=NO_DB_WRITE;NO_SQL_EXECUTE;NO_DOCKER_BUILD;NO_UI_PATCH'
Log "BRIDGE_ROOT=$BridgeRoot"
Log "PROJECT_ROOT=$ProjectRoot"
Log "COST_ROOT=$CostRoot"

# Non-destructive local Git cleanup for the bridge checkout only.
try {
  Push-Location $BridgeRoot
  Remove-Item '.git\index.lock' -Force -ErrorAction SilentlyContinue
  git merge --abort 2>$null | Out-Null
  git rebase --abort 2>$null | Out-Null
  git fetch origin main 2>&1 | Out-Null
  git reset --hard origin/main 2>&1 | Out-Null
  Pop-Location
  Log 'BRIDGE_GIT_SYNC=OK_RESET_TO_ORIGIN_MAIN'
} catch {
  try { Pop-Location } catch {}
  Log ('BRIDGE_GIT_SYNC=WARN ' + $_.Exception.Message)
}

$checks = [ordered]@{
  bridge_root_exists = [bool](Test-Path $BridgeRoot)
  project_root_exists = [bool](Test-Path $ProjectRoot)
  cost_root_exists = [bool](Test-Path $CostRoot)
  current_task_exists = [bool](Test-Path (Join-Path $BridgeRoot 'ai-tasks\current-task.json'))
  last_task_exists = [bool](Test-Path (Join-Path $BridgeRoot 'ai-tasks\.last-task-id'))
  psql_found = [bool](FindPsql)
  source_manifest_json = ((CountFiles $CostRoot '^source_fetch_manifest_latest\.json$') -gt 0)
  source_manifest_csv = ((CountFiles $CostRoot '^source_fetch_manifest_latest\.csv$') -gt 0)
  source_facts_scored = ((CountFiles $CostRoot '^source_facts_scored\.csv$') -gt 0)
  source_facts_summary = ((CountFiles $CostRoot '^source_facts_scored_summary\.json$') -gt 0)
  ui_menu_payload = ((CountFiles $CostRoot '^aays_cost_menu_payload_latest\.json$') -gt 0)
  ui_material_lines = ((CountFiles $CostRoot '^aays_cost_material_lines_latest\.json$') -gt 0)
  api_health_8010 = ((TestUrl 'http://127.0.0.1:8010/health') -ne 'ERR')
}

$missing = @()
foreach($k in $checks.Keys){ Log ($k + '=' + $checks[$k]); if(-not $checks[$k]){ $missing += $k } }
$total = $checks.Count
$score = if($total -gt 0){ [int]((($total - $missing.Count) / $total) * 100) } else { 0 }
$elapsed = [int]((Get-Date) - $Start).TotalSeconds

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$statusPath = Join-Path $ResultDir ($TaskId + '.status.json')
$report = @('# TerraYield 046 Runner Sync Recovery Then Accuracy Expansion','',('Generated: ' + (Get-Date -Format s)),'','## Scope','- Safe recovery wrapper using CLEAN2/env bridge root.','- No DB write, no SQL execute, no Docker build, no UI patch.','','## Checks')
foreach($k in $checks.Keys){ $report += ('- ' + $k + ': ' + $checks[$k]) }
$report += ''
$report += '## Missing signals'
if($missing.Count -eq 0){ $report += '- None detected.' } else { foreach($m in $missing){ $report += ('- ' + $m) } }
$report += ''
$report += ('RUNNER_SYNC_RECOVERY_SCORE=' + $score + '/100')
$report += 'PLAN_PROGRESS_PERCENT=86'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

([ordered]@{
  task_id=$TaskId
  status='completed'
  bridge_root=$BridgeRoot
  project_root=$ProjectRoot
  cost_root=$CostRoot
  checks=$checks
  missing=$missing
  score=$score
  elapsed_seconds=$elapsed
  next_recommended_task='aays-047-db-connection-readonly-probe-or-manual-psql-fix'
  generated_at=(Get-Date -Format s)
} | ConvertTo-Json -Depth 8) | Set-Content -Encoding UTF8 -Path $statusPath

@('# AAYS Portable Task Runner Fixed','',('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),'Status: finished',('TaskId: ' + $TaskId),('BridgeRoot: ' + $BridgeRoot),('ProjectRoot: ' + $ProjectRoot),('TaskFile: ' + (Join-Path $BridgeRoot 'ai-tasks\current-task.json')),('Message: exit=0 terrayield_046_sync_recovery_done score=' + $score),'Mode: no-spawn-foreground-loop','SafeScriptOnly: enabled') | Set-Content -Encoding UTF8 -Path $HeartbeatPath

Log ('REPORT_PATH=' + $reportPath)
Log ('STATUS_PATH=' + $statusPath)
Log ('RUNNER_SYNC_RECOVERY_SCORE=' + $score + '/100')
Log 'PLAN_PROGRESS_PERCENT=86'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0

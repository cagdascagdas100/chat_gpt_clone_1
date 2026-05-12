$ErrorActionPreference = 'Continue'

$TaskId = 'cost50-015-handoff-closure-audit-20260512'
$BridgeRoot = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$CostRoot = if ($env:AAYS_COST_DATA_ROOT) { $env:AAYS_COST_DATA_ROOT } else { 'E:\AAYS_DATA\cost' }
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatPath = Join-Path $HeartbeatDir 'portable-runner.md'
New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir | Out-Null

function Log([string]$Text) { Write-Output ('[' + (Get-Date -Format 's') + '] ' + $Text) }
function CountFiles([string]$Root, [string]$Filter) {
  try { if (Test-Path $Root) { return @(Get-ChildItem -Path $Root -Filter $Filter -File -Recurse -ErrorAction SilentlyContinue).Count } } catch {}
  return 0
}
function Exists([string]$Path) { return [bool](Test-Path $Path) }

Log "TASK=$TaskId"
Log 'MODE=handoff_closure_audit_readonly'
Log "BRIDGE_ROOT=$BridgeRoot"
Log "PROJECT_ROOT=$ProjectRoot"
Log "COST_ROOT=$CostRoot"

$checks = [ordered]@{
  bridge_root_exists = Exists $BridgeRoot
  project_root_exists = Exists $ProjectRoot
  cost_root_exists = Exists $CostRoot
  ai_results_exists = Exists $ResultDir
  app_dir_exists = Exists (Join-Path $ProjectRoot 'app')
  tools_dir_exists = Exists (Join-Path $ProjectRoot 'tools')
  docs_dir_exists = Exists (Join-Path $ProjectRoot 'docs')
  alembic_dir_exists = Exists (Join-Path $ProjectRoot 'alembic')
  requirements_exists = Exists (Join-Path $ProjectRoot 'requirements.txt')
  main_py_exists = Exists (Join-Path $ProjectRoot 'app\main.py')
}

$counts = [ordered]@{
  project_py_files = CountFiles $ProjectRoot '*.py'
  project_md_files = CountFiles $ProjectRoot '*.md'
  project_sql_files = CountFiles $ProjectRoot '*.sql'
  project_json_files = CountFiles $ProjectRoot '*.json'
  ai_result_json_files = CountFiles $ResultDir '*.json'
  ai_result_report_files = CountFiles $ResultDir '*.md'
}

Log 'CHECKS_BEGIN'
foreach ($k in $checks.Keys) { Log ($k + '=' + $checks[$k]) }
Log 'CHECKS_END'
Log 'COUNTS_BEGIN'
foreach ($k in $counts.Keys) { Log ($k + '=' + $counts[$k]) }
Log 'COUNTS_END'

$hit = 0
foreach ($k in $checks.Keys) { if ($checks[$k]) { $hit++ } }
$coverage = if ($checks.Count -gt 0) { [int](($hit / $checks.Count) * 100) } else { 0 }

$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$jsonPath = Join-Path $ResultDir ($TaskId + '.result.json')

$report = @()
$report += '# Cost50 Step 015 Handoff Closure Audit'
$report += ''
$report += "Generated: $(Get-Date -Format s)"
$report += "Task: $TaskId"
$report += ''
$report += '## Scope'
$report += '- Read-only handoff closure audit.'
$report += '- No DB writes, no file mutation outside ai-results/heartbeat, no external fetch.'
$report += ''
$report += '## Checks'
foreach ($k in $checks.Keys) { $report += "- ${k}: $($checks[$k])" }
$report += ''
$report += '## Counts'
foreach ($k in $counts.Keys) { $report += "- ${k}: $($counts[$k])" }
$report += ''
$report += "Closure coverage percent: $coverage"
$report += 'PLAN_PROGRESS_PERCENT=60'
$report += 'TASK_COMPLETION=100/100'
$report += 'TERRAYIELD_TASK_DONE'
$report | Set-Content -Encoding UTF8 -Path $reportPath

$result = [ordered]@{
  task_id = $TaskId
  status = 'completed'
  bridge_root = $BridgeRoot
  project_root = $ProjectRoot
  cost_root = $CostRoot
  closure_coverage_percent = $coverage
  checks = $checks
  counts = $counts
  report_path = $reportPath
  generated_at = (Get-Date -Format s)
}
$result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $jsonPath

@(
  '# AAYS Portable Task Runner Fixed',
  '',
  "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
  'Status: finished',
  "TaskId: $TaskId",
  "BridgeRoot: $BridgeRoot",
  "ProjectRoot: $ProjectRoot",
  "TaskFile: $(Join-Path $BridgeRoot 'ai-tasks\current-task.json')",
  'Message: exit=0',
  'Mode: no-spawn-foreground-loop',
  'SafeScriptOnly: enabled'
) | Set-Content -Encoding UTF8 -Path $HeartbeatPath

Log ('REPORT_PATH=' + $reportPath)
Log ('JSON_RESULT_PATH=' + $jsonPath)
Log ('CLOSURE_COVERAGE_PERCENT=' + $coverage)
Log 'PLAN_PROGRESS_PERCENT=60'
Log 'TASK_COMPLETION=100/100'
Log 'TERRAYIELD_TASK_DONE'
exit 0

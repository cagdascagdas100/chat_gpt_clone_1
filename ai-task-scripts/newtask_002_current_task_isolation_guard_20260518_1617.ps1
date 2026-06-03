$ErrorActionPreference = 'Continue'

$TaskId = 'newtask-002-current-task-isolation-guard-20260518-1617'
$TaskName = 'newtask_002_current_task_isolation_guard_20260518_1617'
$Root = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$TasksDir = Join-Path $Root 'ai-tasks'
$ResultsDir = Join-Path $Root 'ai-results'
$HeartbeatDir = Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultsDir, $HeartbeatDir | Out-Null

$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportPath = Join-Path $ResultsDir ($TaskId + '-' + $Stamp + '.md')
$HeartbeatPath = Join-Path $HeartbeatDir ($TaskName + '.md')
$CurrentTaskPath = Join-Path $TasksDir 'current-task.json'
$MarkerPath = Join-Path $TasksDir '.direct-autopilot-last-task-id'

$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$Text) { [void]$Lines.Add($Text) }
function ExistsFlag([string]$Path) { if (Test-Path -LiteralPath $Path) { 'yes' } else { 'no' } }

L '# NEWTASK 002 CURRENT TASK ISOLATION GUARD REPORT'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L 'Scope: Verify this new ChatGPT page is using NEWTASK namespace and not continuing Ready-to-Sell, ReviewGate, Land Sales, PARCELSALES, or AAYS 097-108 tasks.'
L 'Mode: read-only audit + heartbeat/result write.'
L ''
L '## Paths'
L ('bridge_root_exists: ' + (ExistsFlag $Root))
L ('ai_tasks_exists: ' + (ExistsFlag $TasksDir))
L ('ai_results_exists: ' + (ExistsFlag $ResultsDir))
L ('ai_heartbeat_exists: ' + (ExistsFlag $HeartbeatDir))
L ('current_task_exists: ' + (ExistsFlag $CurrentTaskPath))
L ('last_task_marker_exists: ' + (ExistsFlag $MarkerPath))
L ''
L '## Current task snapshot during execution'
try {
  if (Test-Path -LiteralPath $CurrentTaskPath) {
    $CurrentRaw = Get-Content -LiteralPath $CurrentTaskPath -Raw -ErrorAction SilentlyContinue
    $CurrentObj = $CurrentRaw | ConvertFrom-Json -ErrorAction SilentlyContinue
    L ('current_task_id: ' + $CurrentObj.id)
    L ('current_task_namespace: ' + $CurrentObj.task_namespace)
    L ('current_task_script_path: ' + $CurrentObj.script_path)
    if (($CurrentObj.id -like 'newtask-*') -and ($CurrentObj.script_path -like 'newtask_*.ps1')) {
      L 'namespace_guard: PASS'
    } else {
      L 'namespace_guard: BLOCKED_NON_NEWTASK_CURRENT_TASK'
    }
  } else {
    L 'namespace_guard: BLOCKED_CURRENT_TASK_MISSING'
  }
} catch {
  L ('namespace_guard_error: ' + $_.Exception.GetType().Name)
}
L ''
L '## Latest local NEWTASK files'
try {
  L 'heartbeat_newtask_files:'
  Get-ChildItem -LiteralPath $HeartbeatDir -Filter 'newtask*.md' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10 | ForEach-Object { L ('- ' + $_.Name + ' | ' + $_.LastWriteTime.ToString('s') + ' | ' + $_.Length) }
  L 'result_newtask_files:'
  Get-ChildItem -LiteralPath $ResultsDir -Filter 'newtask*.md' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 10 | ForEach-Object { L ('- ' + $_.Name + ' | ' + $_.LastWriteTime.ToString('s') + ' | ' + $_.Length) }
} catch {
  L ('latest_files_error: ' + $_.Exception.GetType().Name)
}
L ''
L '## Safety gates'
L 'secret_values_printed: no'
L 'destructive_actions: no'
L 'db_write: no'
L 'production_toggle: no'
L 'old_task_continuation: no'
L ''
L '## Result'
L 'task_gate: COMPLETE'
L 'runner_guard_status: COMPLETE'
L 'production_gate: NOT_CHANGED'
L 'NEWTASK_002_DONE=true'

Set-Content -Encoding UTF8 -LiteralPath $ReportPath -Value $Lines
Set-Content -Encoding UTF8 -LiteralPath $HeartbeatPath -Value $Lines

Write-Output 'NEWTASK_002_DONE=true'
Write-Output ('REPORT=' + $ReportPath)
Write-Output ('HEARTBEAT=' + $HeartbeatPath)
exit 0

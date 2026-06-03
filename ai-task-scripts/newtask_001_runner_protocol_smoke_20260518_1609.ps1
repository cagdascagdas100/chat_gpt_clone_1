$ErrorActionPreference = 'Continue'

$TaskId = 'newtask-001-runner-protocol-smoke-20260518-1609'
$TaskName = 'newtask_001_runner_protocol_smoke_20260518_1609'
$Root = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultsDir = Join-Path $Root 'ai-results'
$HeartbeatDir = Join-Path $Root 'ai-heartbeat'
$TasksDir = Join-Path $Root 'ai-tasks'

New-Item -ItemType Directory -Force -Path $ResultsDir, $HeartbeatDir | Out-Null

$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportPath = Join-Path $ResultsDir ($TaskId + '-' + $Stamp + '.md')
$HeartbeatPath = Join-Path $HeartbeatDir ($TaskName + '.md')
$CurrentTaskPath = Join-Path $TasksDir 'current-task.json'
$MarkerPath = Join-Path $TasksDir '.direct-autopilot-last-task-id'

$Lines = New-Object System.Collections.Generic.List[string]
function Add-Line([string]$Text) { [void]$Lines.Add($Text) }
function Safe-Exists([string]$Path) { if (Test-Path -LiteralPath $Path) { 'yes' } else { 'no' } }

Add-Line '# NEWTASK 001 RUNNER PROTOCOL SMOKE REPORT'
Add-Line ('Generated: ' + (Get-Date -Format s))
Add-Line ('TaskId: ' + $TaskId)
Add-Line 'Scope: Read-only runner protocol check. No old Ready-to-Sell/ReviewGate/Land Sales/AAYS 097-108 continuation.'
Add-Line 'Mode: safe read-only + local report/heartbeat write only.'
Add-Line ''
Add-Line '## Bridge paths'
Add-Line ('bridge_root_exists: ' + (Safe-Exists $Root))
Add-Line ('ai_tasks_exists: ' + (Safe-Exists $TasksDir))
Add-Line ('ai_results_exists: ' + (Safe-Exists $ResultsDir))
Add-Line ('ai_heartbeat_exists: ' + (Safe-Exists $HeartbeatDir))
Add-Line ('current_task_exists: ' + (Safe-Exists $CurrentTaskPath))
Add-Line ('last_task_marker_exists: ' + (Safe-Exists $MarkerPath))
Add-Line ''
Add-Line '## Current task check'
try {
  if (Test-Path -LiteralPath $CurrentTaskPath) {
    $CurrentRaw = Get-Content -LiteralPath $CurrentTaskPath -Raw -ErrorAction SilentlyContinue
    $CurrentObj = $CurrentRaw | ConvertFrom-Json -ErrorAction SilentlyContinue
    Add-Line ('current_task_id: ' + $CurrentObj.id)
    Add-Line ('current_task_script_path: ' + $CurrentObj.script_path)
    Add-Line ('current_task_timeout_seconds: ' + $CurrentObj.timeout_seconds)
  } else {
    Add-Line 'current_task_id: MISSING'
  }
} catch {
  Add-Line ('current_task_read_error: ' + $_.Exception.GetType().Name)
}
Add-Line ''
Add-Line '## Safety gates'
Add-Line 'secret_values_printed: no'
Add-Line 'destructive_actions: no'
Add-Line 'db_write: no'
Add-Line 'production_toggle: no'
Add-Line 'old_task_continuation: no'
Add-Line ''
Add-Line '## Result'
Add-Line 'runner_protocol_smoke_status: COMPLETE'
Add-Line 'task_gate: COMPLETE'
Add-Line 'production_gate: NOT_CHANGED'
Add-Line 'NEWTASK_001_DONE=true'

Set-Content -Encoding UTF8 -LiteralPath $ReportPath -Value $Lines
Set-Content -Encoding UTF8 -LiteralPath $HeartbeatPath -Value $Lines

Write-Output 'NEWTASK_001_DONE=true'
Write-Output ('REPORT=' + $ReportPath)
Write-Output ('HEARTBEAT=' + $HeartbeatPath)
exit 0

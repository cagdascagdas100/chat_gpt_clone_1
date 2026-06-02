$ErrorActionPreference = 'Continue'

$TaskId = 'newtask-003-current-task-drift-lock-20260518-1629'
$TaskName = 'newtask_003_current_task_drift_lock_20260518_1629'
$Root = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$TasksDir = Join-Path $Root 'ai-tasks'
$ResultsDir = Join-Path $Root 'ai-results'
$HeartbeatDir = Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultsDir, $HeartbeatDir | Out-Null

$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportPath = Join-Path $ResultsDir ($TaskId + '-' + $Stamp + '.md')
$HeartbeatPath = Join-Path $HeartbeatDir ($TaskName + '.md')
$CurrentTaskPath = Join-Path $TasksDir 'current-task.json'
$DriftFlagPath = Join-Path $TasksDir 'newtask_current_task_drift_flag.txt'

$Lines = New-Object System.Collections.Generic.List[string]
function L([string]$Text) { [void]$Lines.Add($Text) }
function ExistsFlag([string]$Path) { if (Test-Path -LiteralPath $Path) { 'yes' } else { 'no' } }

L '# NEWTASK 003 CURRENT TASK DRIFT LOCK REPORT'
L ('Generated: ' + (Get-Date -Format s))
L ('TaskId: ' + $TaskId)
L 'Scope: Detect and document whether current-task drifts back to old/non-NEWTASK namespace after a NEWTASK task is queued.'
L 'Mode: read-only audit + heartbeat/result write + non-secret drift flag.'
L ''
L '## Paths'
L ('bridge_root_exists: ' + (ExistsFlag $Root))
L ('ai_tasks_exists: ' + (ExistsFlag $TasksDir))
L ('ai_results_exists: ' + (ExistsFlag $ResultsDir))
L ('ai_heartbeat_exists: ' + (ExistsFlag $HeartbeatDir))
L ('current_task_exists: ' + (ExistsFlag $CurrentTaskPath))
L ''
L '## Current task snapshot during execution'
$GuardStatus = 'UNKNOWN'
try {
  if (Test-Path -LiteralPath $CurrentTaskPath) {
    $CurrentRaw = Get-Content -LiteralPath $CurrentTaskPath -Raw -ErrorAction SilentlyContinue
    $CurrentObj = $CurrentRaw | ConvertFrom-Json -ErrorAction SilentlyContinue
    L ('current_task_id: ' + $CurrentObj.id)
    L ('current_task_namespace: ' + $CurrentObj.task_namespace)
    L ('current_task_script_path: ' + $CurrentObj.script_path)
    if (($CurrentObj.id -like 'newtask-*') -and ($CurrentObj.task_namespace -eq 'NEWTASK') -and ($CurrentObj.script_path -like 'newtask_*.ps1')) {
      $GuardStatus = 'PASS_NEWTASK_CURRENT_TASK'
    } else {
      $GuardStatus = 'DRIFTED_TO_NON_NEWTASK_CURRENT_TASK'
    }
  } else {
    $GuardStatus = 'BLOCKED_CURRENT_TASK_MISSING'
  }
} catch {
  $GuardStatus = 'ERROR_READING_CURRENT_TASK_' + $_.Exception.GetType().Name
}
L ('drift_guard_status: ' + $GuardStatus)
L ''
L '## Drift flag'
try {
  $Flag = @(
    'task_id=' + $TaskId,
    'generated=' + (Get-Date -Format s),
    'drift_guard_status=' + $GuardStatus,
    'note=This flag is non-secret and exists only to show the NEWTASK page detected current-task namespace drift.'
  )
  Set-Content -Encoding UTF8 -LiteralPath $DriftFlagPath -Value $Flag
  L ('drift_flag_written: yes')
  L ('drift_flag_path: ' + $DriftFlagPath)
} catch {
  L ('drift_flag_written: no')
  L ('drift_flag_error: ' + $_.Exception.GetType().Name)
}
L ''
L '## Latest local NEWTASK outputs'
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
L 'NEWTASK_003_DONE=true'

Set-Content -Encoding UTF8 -LiteralPath $ReportPath -Value $Lines
Set-Content -Encoding UTF8 -LiteralPath $HeartbeatPath -Value $Lines

Write-Output 'NEWTASK_003_DONE=true'
Write-Output ('REPORT=' + $ReportPath)
Write-Output ('HEARTBEAT=' + $HeartbeatPath)
Write-Output ('DRIFT_GUARD_STATUS=' + $GuardStatus)
exit 0

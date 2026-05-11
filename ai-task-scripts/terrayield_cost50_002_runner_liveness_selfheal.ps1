$ErrorActionPreference = 'Continue'

$bridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN' }
$configPath = Join-Path $bridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $configPath) { . $configPath }

$bridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { $bridgeRoot }
$projectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence' }
$runnerPath = Join-Path $bridgeRoot 'AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1'
$heartbeatPath = Join-Path $bridgeRoot 'ai-heartbeat\portable-runner.md'
$resultDir = Join-Path $bridgeRoot 'ai-results'
$probeJson = Join-Path $resultDir 'runner-liveness-selfheal-latest.json'

New-Item -ItemType Directory -Force -Path $resultDir | Out-Null

function Safe-RunText {
  param([scriptblock]$Block)
  try { return (& $Block 2>&1 | Out-String).Trim() } catch { return ('ERROR: ' + $_.Exception.Message) }
}

$now = Get-Date -Format 's'
Write-Host "AAYS_COST50_STEP02_RUNNER_LIVENESS_SELFHEAL"
Write-Host "checked_at=$now"
Write-Host "bridge_root=$bridgeRoot"
Write-Host "project_root=$projectRoot"
Write-Host "runner_path=$runnerPath"
Write-Host "heartbeat_path=$heartbeatPath"
Write-Host "project_root_exists=$(Test-Path $projectRoot)"
Write-Host "runner_path_exists=$(Test-Path $runnerPath)"

$sentinels = @(
  'app\main.py',
  'app\db\models.py',
  'alembic\versions',
  'tools\cost_uk_real_engine',
  'docs\chatgpt_handoff\cost_uk_postgres_50step\COST50_01_MASTER_PLAN_50_STEPS_TR.md'
)

$missing = @()
foreach ($s in $sentinels) {
  $p = Join-Path $projectRoot $s
  if (-not (Test-Path $p)) { $missing += $s }
}

if ($missing.Count -gt 0) {
  Write-Host 'repo_status=INVALID'
  Write-Host 'missing_sentinels='
  $missing | ForEach-Object { Write-Host (' - ' + $_) }
} else {
  Write-Host 'repo_status=OK'
}

$runnerProcesses = @()
try {
  $runnerProcesses = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -match 'AAYS_PORTABLE_TASK_RUNNER_FIXED\.ps1' } |
    Select-Object ProcessId, ParentProcessId, CommandLine
} catch {
  Write-Host ('runner_process_probe_error=' + $_.Exception.Message)
}

Write-Host ('runner_process_count=' + @($runnerProcesses).Count)
foreach ($p in @($runnerProcesses)) {
  Write-Host ('runner_process=' + $p.ProcessId + ' parent=' + $p.ParentProcessId)
}

if (Test-Path $heartbeatPath) {
  Write-Host 'heartbeat_begin'
  Get-Content -Raw -Encoding UTF8 $heartbeatPath | Write-Host
  Write-Host 'heartbeat_end'
} else {
  Write-Host 'heartbeat_missing=true'
}

$scheduledTaskName = 'AAYS-Portable-Task-Runner-Fixed'
$scheduledTaskStatus = 'not_attempted'
try {
  if (Test-Path $runnerPath) {
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "' + $runnerPath + '"')
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    Register-ScheduledTask -TaskName $scheduledTaskName -Action $action -Trigger $trigger -Settings $settings -Description 'AAYS GitHub bridge portable task runner auto-start' -Force | Out-Null
    $scheduledTaskStatus = 'registered_or_updated'
  } else {
    $scheduledTaskStatus = 'skipped_runner_missing'
  }
} catch {
  $scheduledTaskStatus = 'error: ' + $_.Exception.Message
}
Write-Host ('scheduled_task_status=' + $scheduledTaskStatus)

$taskInfoText = Safe-RunText { Get-ScheduledTask -TaskName $scheduledTaskName | Select-Object TaskName, State | Format-List }
Write-Host 'scheduled_task_info_begin'
Write-Host $taskInfoText
Write-Host 'scheduled_task_info_end'

$bridgeGitStatus = Safe-RunText { git -C $bridgeRoot status --short }
$projectGitStatus = if (Test-Path $projectRoot) { Safe-RunText { git -C $projectRoot status --short } } else { 'PROJECT_ROOT_MISSING' }
Write-Host 'bridge_git_status_begin'
Write-Host $bridgeGitStatus
Write-Host 'bridge_git_status_end'
Write-Host 'project_git_status_begin'
Write-Host $projectGitStatus
Write-Host 'project_git_status_end'

$payload = [ordered]@{
  checked_at = $now
  bridge_root = $bridgeRoot
  project_root = $projectRoot
  runner_path = $runnerPath
  project_root_exists = [bool](Test-Path $projectRoot)
  runner_path_exists = [bool](Test-Path $runnerPath)
  repo_status = if ($missing.Count -eq 0) { 'OK' } else { 'INVALID' }
  missing_sentinels = $missing
  runner_process_count = @($runnerProcesses).Count
  scheduled_task_name = $scheduledTaskName
  scheduled_task_status = $scheduledTaskStatus
}
$payload | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $probeJson
Write-Host ('probe_json=' + $probeJson)

if ($missing.Count -gt 0) { exit 2 }
if (-not (Test-Path $runnerPath)) { exit 3 }
exit 0

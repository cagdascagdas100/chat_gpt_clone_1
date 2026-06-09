$ErrorActionPreference = 'Stop'

$RepoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$QueueRoot = Join-Path $BridgeRoot 'ai-queue'
$TaskDir = Join-Path $QueueRoot 'tasks'
$RunnerPath = Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1'
$StatusRoot = Join-Path $RepoRoot 'docs\chatgpt_status'
$InputDir = Join-Path $StatusRoot 'runner_inputs'
$OutputDir = Join-Path $StatusRoot 'runner_outputs'
$BridgeStatusDir = Join-Path $StatusRoot 'AAYS_AUTOMATION_BRIDGE_REPAIR_20260609'
$BridgeLatest = Join-Path $OutputDir 'aays-automation-bridge-repair-latest.txt'

function New-Dir($p) {
  if (-not (Test-Path -LiteralPath $p)) {
    New-Item -ItemType Directory -Force -Path $p | Out-Null
  }
}

function Write-Text($p, $v) {
  New-Dir (Split-Path -Parent $p)
  Set-Content -LiteralPath $p -Value $v -Encoding UTF8
}

New-Dir $QueueRoot
New-Dir $TaskDir
New-Dir $InputDir
New-Dir $OutputDir
New-Dir $BridgeStatusDir

$runnerProcs = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
  ($_.CommandLine -like '*portable_queue_runner.ps1*') -and ($_.CommandLine -notlike '*Get-CimInstance*')
})

$latestInput = Get-ChildItem -LiteralPath $InputDir -File -Filter '*.txt' -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

$taskId = 'aays-bridge-repair-no-input'
$queued = $false
$blocker = ''

if ($runnerProcs.Count -gt 1) {
  $blocker = 'multiple_runner_processes'
} elseif (-not $latestInput) {
  $blocker = 'no_runner_input_file_found'
} else {
  $taskId = [IO.Path]::GetFileNameWithoutExtension($latestInput.Name)
  $taskText = Get-Content -LiteralPath $latestInput.FullName -Raw -Encoding UTF8
  Write-Text (Join-Path $TaskDir ($taskId + '.txt')) $taskText
  Write-Text (Join-Path $QueueRoot 'current-task.txt') $taskText
  $queued = $true
}

$runnerAction = 'none'
if ($runnerProcs.Count -eq 0 -and (Test-Path -LiteralPath $RunnerPath)) {
  Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$RunnerPath`"" -WindowStyle Minimized
  $runnerAction = 'started'
} elseif ($runnerProcs.Count -eq 1) {
  $runnerAction = 'already_running'
} elseif ($runnerProcs.Count -gt 1) {
  $runnerAction = 'blocked_multiple_runners'
} else {
  $runnerAction = 'missing_runner_path'
}

$report = @"
timestamp=$(Get-Date -Format s)
project=AAYS_AUTOMATION_BRIDGE_REPAIR
task_id=$taskId
status=$(if($queued){'queued'}else{'blocked'})
progress=65
runner_count=$($runnerProcs.Count)
runner_action=$runnerAction
input_file=$(if($latestInput){$latestInput.FullName}else{'none'})
queue_root=$QueueRoot
task_dir=$TaskDir
current_task=$(Join-Path $QueueRoot 'current-task.txt')
expected_runner_output=docs/chatgpt_status/runner_outputs/*latest*.txt
exact_blocker=$blocker
next_action=Wait for runner output; if output remains queued, inspect portable_queue_runner.ps1 dispatch logic.
wait_minutes=$(if($queued){25}else{0})
safety_flags=db_write_false,deploy_false,migration_false,ddl_false,fake_data_false,destructive_git_false,force_push_false
"@

Write-Text $BridgeLatest $report
Write-Text (Join-Path $BridgeStatusDir 'BRIDGE_REPAIR_STATUS.txt') $report

Push-Location $RepoRoot
try {
  git add 'docs/chatgpt_status/runner_outputs/aays-automation-bridge-repair-latest.txt' 'docs/chatgpt_status/AAYS_AUTOMATION_BRIDGE_REPAIR_20260609/BRIDGE_REPAIR_STATUS.txt'
  git commit -m 'Add AAYS automation bridge repair status' 2>$null
  $branch = 'chatgpt/aays-automation-bridge-repair-output-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
  git push -u origin "HEAD:refs/heads/$branch" 2>$null
} finally {
  Pop-Location
}

Write-Host "DONE bridge_repair status=$(if($queued){'queued'}else{'blocked'}) runner_action=$runnerAction progress=65 wait_minutes=$(if($queued){25}else{0})" -ForegroundColor Green

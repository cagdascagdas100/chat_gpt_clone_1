# Sync aays1 repo-side task to F bridge pending, check/start portable shared runner, and push repo-visible diagnostics.
# No fake heartbeat/output/final marker is produced by this script.
$ErrorActionPreference = 'Continue'
$RepoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS'
$PageKey = 'aays1'
$TaskId = 'aays1_fg100_runner_contract_blocker_20260623_008'
$TaskRel = 'docs\chatgpt_status\aays1\queue\aays1_fg100_runner_contract_blocker_20260623_008_live_bridge.task.json'
$ReportRel = 'docs\chatgpt_status\aays1\reports\aays1_f_bridge_queue_sync_and_runner_check_20260624.txt'
$ExpectedOutputRel = 'docs\chatgpt_status\aays1\reports\aays1_fg100_runner_contract_blocker_20260623_008_runner_output.txt'
$ExpectedHeartbeatRel = 'docs\chatgpt_status\aays1\heartbeat\aays1_fg100_runner_contract_blocker_20260623_008_heartbeat.txt'

function Resolve-BridgeRoot {
  $candidates = @()
  if ($env:AAYS_BRIDGE_ROOT) { $candidates += $env:AAYS_BRIDGE_ROOT }
  $candidates += @('F:\AAYS_GITHUB_BRIDGE_CLEAN2','D:\AAYS_GITHUB_BRIDGE_CLEAN2','C:\AAYS_GITHUB_BRIDGE_CLEAN2')
  foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) { return $candidate }
  }
  return $null
}

$BridgeRoot = Resolve-BridgeRoot
$ReportPath = Join-Path $RepoRoot $ReportRel
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null
function Add-ReportLine([string]$line) { $line | Out-File -FilePath $ReportPath -Encoding utf8 -Append }

if (Test-Path $ReportPath) { Remove-Item $ReportPath -Force }
Add-ReportLine "time=$(Get-Date -Format o)"
Add-ReportLine "page_key=$PageKey"
Add-ReportLine "task_id=$TaskId"
Add-ReportLine "repo_root=$RepoRoot"
Add-ReportLine "bridge_root=$BridgeRoot"
Add-ReportLine "fake_data=false"
Add-ReportLine "final_ready=false"

if (!(Test-Path $RepoRoot)) {
  Add-ReportLine "blocker=wrong_root"
  Add-ReportLine "detail=Repo root path does not exist."
  exit 2
}
Set-Location $RepoRoot

Add-ReportLine "branch=$(git branch --show-current 2>&1)"
Add-ReportLine "remote_begin"
(git remote -v 2>&1) | ForEach-Object { Add-ReportLine $_ }
Add-ReportLine "remote_end"

Add-ReportLine "git_pull_begin"
(git pull 2>&1) | ForEach-Object { Add-ReportLine $_ }
Add-ReportLine "git_pull_end"

$TaskSrc = Join-Path $RepoRoot $TaskRel
if (!(Test-Path $TaskSrc)) {
  Add-ReportLine "blocker=missing_repo_side_task"
  Add-ReportLine "missing=$TaskRel"
} elseif (!$BridgeRoot) {
  Add-ReportLine "blocker=missing_bridge_root"
  Add-ReportLine "detail=AAYS_BRIDGE_ROOT/F/D/C bridge root not found."
} else {
  $PendingDir = Join-Path $BridgeRoot 'ai-queue\pending'
  New-Item -ItemType Directory -Force -Path $PendingDir | Out-Null
  $PendingPath = Join-Path $PendingDir (Split-Path $TaskSrc -Leaf)
  Copy-Item -Path $TaskSrc -Destination $PendingPath -Force
  Add-ReportLine "pending_task_copied=true"
  Add-ReportLine "pending_task_path=$PendingPath"
  Add-ReportLine "pending_task_exists=$(Test-Path $PendingPath)"
}

$runnerProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' })
Add-ReportLine "portable_runner_process_count_before=$($runnerProcesses.Count)"

if ($BridgeRoot -and $runnerProcesses.Count -eq 0) {
  $runnerCandidates = @(
    (Join-Path $BridgeRoot 'portable_queue_runner.ps1'),
    (Join-Path $BridgeRoot 'tools\portable_queue_runner.ps1'),
    (Join-Path $RepoRoot 'tools\portable_queue_runner.ps1')
  )
  $runnerScript = $runnerCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
  if ($runnerScript) {
    Add-ReportLine "runner_start_attempt=true"
    Add-ReportLine "runner_script=$runnerScript"
    Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$runnerScript) -WorkingDirectory $BridgeRoot
    Start-Sleep -Seconds 10
  } else {
    Add-ReportLine "blocker=missing_portable_queue_runner"
    Add-ReportLine "searched=$($runnerCandidates -join ';')"
  }
} else {
  Add-ReportLine "runner_start_attempt=false"
}

$runnerProcessesAfter = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' })
Add-ReportLine "portable_runner_process_count_after=$($runnerProcessesAfter.Count)"

$ExpectedOutput = Join-Path $RepoRoot $ExpectedOutputRel
$ExpectedHeartbeat = Join-Path $RepoRoot $ExpectedHeartbeatRel
Start-Sleep -Seconds 20
Add-ReportLine "expected_output_exists=$(Test-Path $ExpectedOutput)"
Add-ReportLine "expected_heartbeat_exists=$(Test-Path $ExpectedHeartbeat)"
if (Test-Path $ExpectedOutput) { Add-ReportLine "expected_output_path=$ExpectedOutput" }
if (Test-Path $ExpectedHeartbeat) { Add-ReportLine "expected_heartbeat_path=$ExpectedHeartbeat" }

Add-ReportLine "git_status_before_add_begin"
(git status --short 2>&1) | ForEach-Object { Add-ReportLine $_ }
Add-ReportLine "git_status_before_add_end"

$pathsToAdd = @($ReportRel)
if (Test-Path $ExpectedOutput) { $pathsToAdd += $ExpectedOutputRel }
if (Test-Path $ExpectedHeartbeat) { $pathsToAdd += $ExpectedHeartbeatRel }

Add-ReportLine "git_add_begin"
foreach ($p in $pathsToAdd) { (git add -- $p 2>&1) | ForEach-Object { Add-ReportLine $_ } }
Add-ReportLine "git_add_end"

$hasStaged = git diff --cached --name-only
if ($hasStaged) {
  Add-ReportLine "git_commit_begin"
  (git commit -m "sync aays1 task to F bridge and report runner check" 2>&1) | ForEach-Object { Add-ReportLine $_ }
  Add-ReportLine "git_commit_end"
  Add-ReportLine "git_push_begin"
  (git push 2>&1) | ForEach-Object { Add-ReportLine $_ }
  Add-ReportLine "git_push_end"
} else {
  Add-ReportLine "git_commit_skipped=no_staged_changes"
}

Add-ReportLine "done=true"
Write-Output "AAYS1_F_BRIDGE_SYNC_AND_RUNNER_CHECK_DONE report=$ReportPath"

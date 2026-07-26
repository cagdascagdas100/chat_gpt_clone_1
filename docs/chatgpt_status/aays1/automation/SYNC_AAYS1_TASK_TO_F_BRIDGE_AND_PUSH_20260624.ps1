# AAYS1 F repo + F bridge sync/test script.
# Purpose: copy repo-side aays1 task to F bridge pending, verify shared runner, wait for real output/heartbeat, then push only aays1 evidence.
# No fake heartbeat/output/report/final marker is produced.
$ErrorActionPreference = 'Continue'
$env:AAYS_REPO_ROOT = 'F:\chatgpt\chat_gpt_clone_1_main'
$env:AAYS_BRIDGE_ROOT = 'F:\AAYS_GITHUB_BRIDGE_CLEAN2'

$RepoRoot = $env:AAYS_REPO_ROOT
$BridgeRoot = $env:AAYS_BRIDGE_ROOT
$PageKey = 'aays1'
$TaskId = 'aays1_fg100_runner_contract_blocker_20260623_008'
$TaskName = 'aays1_fg100_runner_contract_blocker_20260623_008_live_bridge.task.json'
$TaskRel = "docs\chatgpt_status\$PageKey\queue\$TaskName"
$ReportRel = "docs\chatgpt_status\$PageKey\reports\aays1_f_repo_f_bridge_runner_test_20260625.txt"
$ExpectedOutputRel = "docs\chatgpt_status\$PageKey\reports\aays1_fg100_runner_contract_blocker_20260623_008_runner_output.txt"
$ExpectedHeartbeatRel = "docs\chatgpt_status\$PageKey\heartbeat\aays1_fg100_runner_contract_blocker_20260623_008_heartbeat.txt"
$RunnerBootstrapRel = 'docs\chatgpt_status\runner_outputs\aays-runner-bootstrap-report-latest.txt'

function Write-Report([string]$line) {
  $line | Out-File -FilePath $script:ReportPath -Encoding utf8 -Append
}

$ReportPath = Join-Path $RepoRoot $ReportRel
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null
if (Test-Path $ReportPath) { Remove-Item $ReportPath -Force }

Write-Report "time=$(Get-Date -Format o)"
Write-Report "page_key=$PageKey"
Write-Report "task_id=$TaskId"
Write-Report "repo_root=$RepoRoot"
Write-Report "bridge_root=$BridgeRoot"
Write-Report "fake_data=false"
Write-Report "final_ready=false"

if (!(Test-Path $RepoRoot)) {
  Write-Report 'blocker=wrong_root'
  Write-Report 'detail=F repo root missing.'
  Write-Output "AAYS1_BLOCKER wrong_root report=$ReportPath"
  exit 2
}
if (!(Test-Path $BridgeRoot)) {
  Write-Report 'blocker=missing_bridge_root'
  Write-Report 'detail=F bridge root missing.'
  Write-Output "AAYS1_BLOCKER missing_bridge_root report=$ReportPath"
  exit 3
}

Set-Location $RepoRoot
Write-Report "branch=$(git branch --show-current 2>&1)"
Write-Report 'remote_begin'
(git remote -v 2>&1) | ForEach-Object { Write-Report $_ }
Write-Report 'remote_end'

Write-Report 'git_pull_begin'
(git pull 2>&1) | ForEach-Object { Write-Report $_ }
Write-Report 'git_pull_end'

$TaskSrc = Join-Path $RepoRoot $TaskRel
if (!(Test-Path $TaskSrc)) {
  Write-Report 'blocker=missing_repo_side_task'
  Write-Report "missing=$TaskRel"
} else {
  $PendingDir = Join-Path $BridgeRoot 'ai-queue\pending'
  New-Item -ItemType Directory -Force -Path $PendingDir | Out-Null
  $PendingPath = Join-Path $PendingDir $TaskName
  Copy-Item -Path $TaskSrc -Destination $PendingPath -Force
  Write-Report 'pending_task_copied=true'
  Write-Report "pending_task_path=$PendingPath"
  Write-Report "pending_task_exists=$(Test-Path $PendingPath)"
}

$HeartbeatFile = Join-Path $BridgeRoot 'ai-queue\heartbeat.txt'
Write-Report "bridge_heartbeat_exists=$(Test-Path $HeartbeatFile)"
if (Test-Path $HeartbeatFile) {
  Write-Report 'bridge_heartbeat_begin'
  Get-Content $HeartbeatFile -Tail 20 | ForEach-Object { Write-Report $_ }
  Write-Report 'bridge_heartbeat_end'
}

$runnerProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' })
Write-Report "portable_runner_process_count=$($runnerProcesses.Count)"
if ($runnerProcesses.Count -gt 0) {
  $runnerProcesses | ForEach-Object { Write-Report "runner_pid=$($_.ProcessId)" }
} else {
  Write-Report 'blocker=runner_not_active'
  Write-Report 'detail=No new runner started by this script because single shared runner rule is active.'
}

# Give existing runner a short window to pick up and write real repo evidence.
Start-Sleep -Seconds 45

$ExpectedOutput = Join-Path $RepoRoot $ExpectedOutputRel
$ExpectedHeartbeat = Join-Path $RepoRoot $ExpectedHeartbeatRel
$RunnerBootstrap = Join-Path $RepoRoot $RunnerBootstrapRel
Write-Report "expected_output_exists=$(Test-Path $ExpectedOutput)"
Write-Report "expected_heartbeat_exists=$(Test-Path $ExpectedHeartbeat)"
Write-Report "runner_bootstrap_report_exists=$(Test-Path $RunnerBootstrap)"

if (!(Test-Path $ExpectedOutput) -or !(Test-Path $ExpectedHeartbeat)) {
  Write-Report 'blocker=runner_pickup_or_output_not_proven'
  Write-Report "expected_output_rel=$ExpectedOutputRel"
  Write-Report "expected_heartbeat_rel=$ExpectedHeartbeatRel"
}

Write-Report 'git_status_before_add_begin'
(git status --short 2>&1) | ForEach-Object { Write-Report $_ }
Write-Report 'git_status_before_add_end'

$pathsToAdd = @($ReportRel)
if (Test-Path $ExpectedOutput) { $pathsToAdd += $ExpectedOutputRel }
if (Test-Path $ExpectedHeartbeat) { $pathsToAdd += $ExpectedHeartbeatRel }
if (Test-Path $RunnerBootstrap) { $pathsToAdd += $RunnerBootstrapRel }

Write-Report 'git_add_begin'
foreach ($p in $pathsToAdd) {
  (git add -- $p 2>&1) | ForEach-Object { Write-Report $_ }
}
Write-Report 'git_add_end'

$staged = git diff --cached --name-only
if ($staged) {
  Write-Report 'git_commit_begin'
  (git commit -m 'test aays1 F repo F bridge runner pickup' 2>&1) | ForEach-Object { Write-Report $_ }
  Write-Report 'git_commit_end'
  Write-Report 'git_push_begin'
  (git push origin main 2>&1) | ForEach-Object { Write-Report $_ }
  Write-Report 'git_push_end'
} else {
  Write-Report 'git_commit_skipped=no_staged_changes'
}

Write-Report 'done=true'
Write-Output "AAYS1_F_REPO_F_BRIDGE_RUNNER_TEST_DONE report=$ReportPath"

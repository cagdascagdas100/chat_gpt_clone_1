param(
  [string]$PageKey = "AAYS_TERRAYIELD_PAGE_20260603_001"
)

$ErrorActionPreference = "Continue"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$RunnerPath = Join-Path $BridgeRoot "ai-task-scripts\portable_queue_runner.ps1"
$RepoStatusDir = Join-Path $RepoRoot "docs\chatgpt_status"
$RepoOutDir = Join-Path $RepoStatusDir "runner_outputs"
$BridgeResultsDir = Join-Path $BridgeRoot "ai-results"
New-Item -ItemType Directory -Force -Path $RepoOutDir,$BridgeResultsDir | Out-Null

$TaskId = "aays-stepwise-parallel-report-loop-$Stamp"
$TranscriptPath = Join-Path $RepoOutDir "aays-stepwise-powershell-transcript-latest.txt"
$StepTxt = Join-Path $RepoOutDir "aays-stepwise-current-step-latest.txt"
$StepJson = Join-Path $RepoOutDir "aays-stepwise-current-step-latest.json"
$FinalTxt = Join-Path $RepoOutDir "aays-stepwise-final-summary-latest.txt"
$FinalJson = Join-Path $RepoOutDir "aays-stepwise-final-summary-latest.json"
$SyncVerifyTxt = Join-Path $RepoOutDir "aays-stepwise-sync-verification-latest.txt"
$BridgeReport = Join-Path $BridgeResultsDir "${PageKey}_stepwise_queue_and_kick_${Stamp}.txt"
$RepoReport = Join-Path $RepoStatusDir "${PageKey}_stepwise_queue_and_kick_${Stamp}.txt"

function Write-StepReport {
  param(
    [string]$StepName,
    [string]$Status,
    [string]$CommandGroup,
    [string]$Blocker = "",
    [string]$NextAction = "",
    [string[]]$OutputFiles = @(),
    [bool]$GithubVerified = $false
  )
  $Now = Get-Date -Format "s"
  $obj = [ordered]@{
    task_id = $TaskId
    page_key = $PageKey
    step_name = $StepName
    start_time = $Now
    end_time = $Now
    duration_seconds = 0
    status = $Status
    command_group = $CommandGroup
    stdout_tail = "see transcript: $TranscriptPath"
    stderr_tail = "merged to transcript when available"
    output_files_written = $OutputFiles
    github_verified = $GithubVerified
    blocker_if_any = $Blocker
    next_action = $NextAction
    overall_progress = 99
    bridge_progress_if_known = 39
    db_write = $false
    deploy = $false
    migration = $false
    fake_data = $false
    secret_values_printed = $false
  }
  $obj | ConvertTo-Json -Depth 8 | Set-Content $StepJson -Encoding UTF8
  @"
AAYS stepwise current step
stamp=$Stamp
task_id=$TaskId
page_key=$PageKey
step_name=$StepName
status=$Status
command_group=$CommandGroup
github_verified=$GithubVerified
blocker_if_any=$Blocker
next_action=$NextAction
overall_progress=99
bridge_progress_if_known=39
db_write=false
deploy=false
migration=false
fake_data=false
secret_values_printed=false
"@ | Set-Content $StepTxt -Encoding UTF8
}

function Get-RunnerProcesses {
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and ($_.CommandLine -like "*$RunnerPath*" -or $_.CommandLine -like "*portable_queue_runner.ps1*") }
}

function Find-QueueRoot {
  $candidates = @(
    (Join-Path $BridgeRoot "ai-queue"),
    (Join-Path $BridgeRoot "queue"),
    (Join-Path $BridgeRoot "ai-tasks")
  )
  foreach ($c in $candidates) {
    if ((Test-Path (Join-Path $c "pending")) -and (Test-Path (Join-Path $c "done"))) { return $c }
  }
  $pendingDirs = Get-ChildItem $BridgeRoot -Directory -Filter "pending" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 20
  foreach ($p in $pendingDirs) {
    $parent = Split-Path $p.FullName -Parent
    if ((Test-Path (Join-Path $parent "done")) -or (Test-Path (Join-Path $parent "failed")) -or (Test-Path (Join-Path $parent "running"))) { return $parent }
  }
  $fallback = Join-Path $BridgeRoot "ai-queue"
  New-Item -ItemType Directory -Force -Path (Join-Path $fallback "pending"),(Join-Path $fallback "running"),(Join-Path $fallback "done"),(Join-Path $fallback "failed") | Out-Null
  return $fallback
}

try { Start-Transcript -Path $TranscriptPath -Force | Out-Null } catch {}

Write-StepReport -StepName "preflight_process_check" -Status "STARTED" -CommandGroup "runner/process/paths" -NextAction "detect runner and queue root"

$RunnerProcesses = @(Get-RunnerProcesses)
$RunnerActiveCount = $RunnerProcesses.Count
$QueueRoot = Find-QueueRoot
$PendingDir = Join-Path $QueueRoot "pending"
$RunningDir = Join-Path $QueueRoot "running"
$DoneDir = Join-Path $QueueRoot "done"
$FailedDir = Join-Path $QueueRoot "failed"
New-Item -ItemType Directory -Force -Path $PendingDir,$RunningDir,$DoneDir,$FailedDir | Out-Null
$LockPath = Join-Path $QueueRoot "queue.lock"

Write-StepReport -StepName "queue_lock_acquire" -Status "STARTED" -CommandGroup "queue-lock" -NextAction "create pending task under lock" -OutputFiles @($StepTxt,$StepJson,$TranscriptPath)

$LockAcquired = $false
try {
  $lockStream = [System.IO.File]::Open($LockPath, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
  $LockAcquired = $true
} catch {
  $LockAcquired = $false
}

$TaskJsonPath = Join-Path $PendingDir "$TaskId.json"
$TaskTxtPath = Join-Path $PendingDir "$TaskId.txt"

$TaskBody = @"
AAYS / TerraYield stepwise runner task
page_key=$PageKey
task_id=$TaskId
priority=urgent
protocol=TEK_RUNNER_QUEUE_LOCK_KISA_CEVAP

Objective:
Run stepwise report loop only through the existing portable queue runner. Do not use current-task.json. Do not start a new global runner if one is active.

Required outputs:
- $RepoOutDir\aays-stepwise-current-step-latest.txt
- $RepoOutDir\aays-stepwise-current-step-latest.json
- $RepoOutDir\aays-stepwise-final-summary-latest.txt
- $RepoOutDir\aays-stepwise-final-summary-latest.json
- $RepoOutDir\aays-stepwise-powershell-transcript-latest.txt
- $RepoOutDir\aays-stepwise-sync-verification-latest.txt
- $BridgeResultsDir\${PageKey}_stepwise_*.txt

Step sequence:
1. preflight_process_check
2. repo_and_git_sync_check
3. local_output_inventory
4. github_output_verification
5. parallel_safe_diagnostics
6. gate_rerun_read_only
7. sync_and_verify
8. final_summary

Rules:
- Write TXT and JSON after every named step.
- Capture stdout/stderr to transcript files, not user chat.
- Verify GitHub push by checking remote accessibility; do not trust SYNC_DONE alone.
- If sync fails, write FAIL_STEP_SYNC_DNS with local recovery path.
- DB write=false, deploy=false, migration=false, fake_data=false, secret_values_printed=false.
- Never set overall_progress=100 unless all required region assets are runtime verified.

Known current state:
- overall_progress=99
- bridge_progress_estimate=39
- HMLR deep probe status=BLOCKED_AT_DOWNLOAD_SERVICE_NO_DIRECT_RUNTIME_FILE
- Wales runtime file candidates=0
- runtime_verified_source_count=1
- missing_region_asset_count=7
"@

$TaskObj = [ordered]@{
  task_id = $TaskId
  page_key = $PageKey
  project = "AAYS_TerraYield"
  created_at = (Get-Date -Format "s")
  status = "pending"
  priority = "urgent"
  instructions = $TaskBody
  safety = [ordered]@{ db_write=$false; deploy=$false; migration=$false; fake_data=$false; secret_values_printed=$false; destructive_git=$false }
}

if ($LockAcquired) {
  $TaskObj | ConvertTo-Json -Depth 8 | Set-Content $TaskJsonPath -Encoding UTF8
  $TaskBody | Set-Content $TaskTxtPath -Encoding UTF8
  try { $lockStream.Close() } catch {}
  Write-StepReport -StepName "queue_task_written" -Status "PASS" -CommandGroup "queue/pending" -NextAction "runner consumes pending task" -OutputFiles @($TaskJsonPath,$TaskTxtPath,$StepTxt,$StepJson,$TranscriptPath)
} else {
  Write-StepReport -StepName "queue_lock_acquire" -Status "FAIL_STEP_LOCK_BUSY" -CommandGroup "queue-lock" -Blocker "queue.lock is busy" -NextAction "wait and run again" -OutputFiles @($StepTxt,$StepJson,$TranscriptPath)
}

$QueueBeforePending = @(Get-ChildItem $PendingDir -File -ErrorAction SilentlyContinue).Count
$QueueRunning = @(Get-ChildItem $RunningDir -File -ErrorAction SilentlyContinue).Count
$QueueDone = @(Get-ChildItem $DoneDir -File -ErrorAction SilentlyContinue).Count
$QueueFailed = @(Get-ChildItem $FailedDir -File -ErrorAction SilentlyContinue).Count

$KickAction = "not_started"
if ($RunnerActiveCount -gt 0) {
  $KickAction = "runner_already_active_task_left_pending"
} elseif (Test-Path $RunnerPath) {
  try {
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$RunnerPath) -WorkingDirectory $BridgeRoot | Out-Null
    Start-Sleep -Seconds 3
    $RunnerActiveCount = @(Get-RunnerProcesses).Count
    $KickAction = "started_main_portable_runner"
  } catch {
    $KickAction = "failed_to_start_main_portable_runner: $($_.Exception.Message)"
  }
} else {
  $KickAction = "runner_path_missing"
}

$Final = [ordered]@{
  stamp = $Stamp
  page_key = $PageKey
  task_id = $TaskId
  status = if ($LockAcquired) { "QUEUED_STEPWISE_TASK" } else { "FAILED_QUEUE_LOCK_BUSY" }
  runner_path = $RunnerPath
  runner_active_count = $RunnerActiveCount
  queue_root = $QueueRoot
  pending_count = $QueueBeforePending
  running_count = $QueueRunning
  done_count = $QueueDone
  failed_count = $QueueFailed
  task_json = $TaskJsonPath
  task_txt = $TaskTxtPath
  kick_action = $KickAction
  overall_progress = 99
  bridge_progress_estimate = 39
  wait_minutes = "30-60"
  report_repo = $RepoReport
  report_bridge = $BridgeReport
  db_write = $false
  deploy = $false
  migration = $false
  fake_data = $false
  secret_values_printed = $false
}

$Final | ConvertTo-Json -Depth 8 | Set-Content $FinalJson -Encoding UTF8
@"
AAYS stepwise final summary
stamp=$Stamp
page_key=$PageKey
task_id=$TaskId
status=$($Final.status)
runner_path=$RunnerPath
runner_active_count=$RunnerActiveCount
queue_root=$QueueRoot
pending_count=$QueueBeforePending
running_count=$QueueRunning
done_count=$QueueDone
failed_count=$QueueFailed
task_json=$TaskJsonPath
task_txt=$TaskTxtPath
kick_action=$KickAction
overall_progress=99
bridge_progress_estimate=39
wait_minutes=30-60
db_write=false
deploy=false
migration=false
fake_data=false
secret_values_printed=false
"@ | Set-Content $FinalTxt -Encoding UTF8
Copy-Item $FinalTxt $BridgeReport -Force
Copy-Item $FinalTxt $RepoReport -Force

Write-StepReport -StepName "final_summary" -Status $Final.status -CommandGroup "summary" -NextAction "wait 30-60 minutes then inspect GitHub reports" -OutputFiles @($FinalTxt,$FinalJson,$BridgeReport,$RepoReport,$StepTxt,$StepJson,$TranscriptPath)

$SyncStatus = "not_run"
try {
  Set-Location $RepoRoot
  $gitOut = git status --short 2>&1 | Out-String
  git add "docs/chatgpt_status" 2>&1 | Out-Null
  git commit -m "Add AAYS stepwise queue reports $Stamp" 2>&1 | Out-Null
  $pushOut = git push origin HEAD:chatgpt-local-sync 2>&1 | Out-String
  $SyncStatus = if ($LASTEXITCODE -eq 0 -or $pushOut -match "Everything up-to-date") { "SYNC_PUSH_ATTEMPTED" } else { "SYNC_PUSH_FAILED" }
  @"
AAYS stepwise sync verification
stamp=$Stamp
status=$SyncStatus
git_status_before=$gitOut
push_output=$pushOut
latest_report=$FinalTxt
"@ | Set-Content $SyncVerifyTxt -Encoding UTF8
} catch {
  $SyncStatus = "SYNC_EXCEPTION"
  @"
AAYS stepwise sync verification
stamp=$Stamp
status=SYNC_EXCEPTION
error=$($_.Exception.Message)
latest_report=$FinalTxt
"@ | Set-Content $SyncVerifyTxt -Encoding UTF8
}

try { Stop-Transcript | Out-Null } catch {}

Write-Host "PAGE_KEY=$PageKey"
Write-Host "RUNNER_PATH=$RunnerPath"
Write-Host "RUNNER_ACTIVE_COUNT=$RunnerActiveCount"
Write-Host "QUEUE_ROOT=$QueueRoot"
Write-Host "TASK_ID=$TaskId"
Write-Host "TASK_ACTION=$($Final.status)"
Write-Host "KICK_ACTION=$KickAction"
Write-Host "REPORT=$BridgeReport"
Write-Host "REPO_REPORT=$RepoReport"
Write-Host "FINAL_SUMMARY=$FinalTxt"
Write-Host "PROGRESS_ESTIMATE=39"
Write-Host "AAYS_COVERAGE_PROGRESS=99"
Write-Host "Bekleme suresi: 30-60 dakika"

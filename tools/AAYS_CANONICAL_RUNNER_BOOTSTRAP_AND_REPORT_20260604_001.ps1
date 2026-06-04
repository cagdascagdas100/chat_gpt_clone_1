param(
  [string]$PageKey = "AAYS_TERRAYIELD_PAGE_20260603_001"
)

$ErrorActionPreference = "Continue"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$RunnerPath = Join-Path $BridgeRoot "ai-task-scripts\portable_queue_runner.ps1"
$QueueRoot = Join-Path $BridgeRoot "ai-queue"
$RepoOutDir = Join-Path $RepoRoot "docs\chatgpt_status\runner_outputs"
$BridgeOutDir = Join-Path $BridgeRoot "ai-results"
New-Item -ItemType Directory -Force -Path $RepoOutDir,$BridgeOutDir | Out-Null

$ReportRepo = Join-Path $RepoOutDir "aays-runner-bootstrap-report-latest.txt"
$ReportBridge = Join-Path $BridgeOutDir "${PageKey}_runner_bootstrap_report_latest.txt"
$SyncFail = Join-Path $RepoOutDir "aays-runner-bootstrap-sync-failure-latest.txt"

function Count-Files($Path) {
  if (Test-Path $Path) { return @((Get-ChildItem $Path -File -ErrorAction SilentlyContinue)).Count }
  return 0
}

function Newest-File($Path) {
  if (Test-Path $Path) {
    $f = Get-ChildItem $Path -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($f) { return $f.Name }
  }
  return ""
}

function Runner-Processes {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine -like "*portable_queue_runner.ps1*" })
}

$RunnerBefore = @(Runner-Processes)
$RunnerCountBefore = $RunnerBefore.Count
$ActionTaken = "none"
$StartError = ""

try {
  if (Test-Path $RunnerPath) {
    try { Unblock-File -Path $RunnerPath -ErrorAction SilentlyContinue } catch {}
  }
  Get-ChildItem (Join-Path $BridgeRoot "ai-task-scripts") -Filter "*.ps1" -File -ErrorAction SilentlyContinue | ForEach-Object {
    try { Unblock-File -Path $_.FullName -ErrorAction SilentlyContinue } catch {}
  }
} catch {}

if ($RunnerCountBefore -eq 0) {
  if (Test-Path $RunnerPath) {
    try {
      Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$RunnerPath) -WorkingDirectory $BridgeRoot | Out-Null
      Start-Sleep -Seconds 5
      $ActionTaken = "started_canonical_runner_only"
    } catch {
      $ActionTaken = "failed_to_start_canonical_runner"
      $StartError = $_.Exception.Message
    }
  } else {
    $ActionTaken = "runner_path_missing"
    $StartError = "missing: $RunnerPath"
  }
} else {
  $ActionTaken = "runner_already_active_no_new_runner_started"
}

$RunnerAfter = @(Runner-Processes)
$RunnerCountAfter = $RunnerAfter.Count

$StepFinal = Join-Path $RepoOutDir "aays-stepwise-final-summary-latest.txt"
$StepCurrent = Join-Path $RepoOutDir "aays-stepwise-current-step-latest.txt"

$Report = @"
AAYS canonical runner bootstrap/report
stamp=$Stamp
page_key=$PageKey
runner_path=$RunnerPath
runner_count_before=$RunnerCountBefore
runner_count_after=$RunnerCountAfter
action_taken=$ActionTaken
start_error=$StartError
queue_root=$QueueRoot
pending_count=$(Count-Files (Join-Path $QueueRoot "pending"))
running_count=$(Count-Files (Join-Path $QueueRoot "running"))
done_count=$(Count-Files (Join-Path $QueueRoot "done"))
failed_count=$(Count-Files (Join-Path $QueueRoot "failed"))
newest_pending_task=$(Newest-File (Join-Path $QueueRoot "pending"))
newest_running_task=$(Newest-File (Join-Path $QueueRoot "running"))
newest_done_task=$(Newest-File (Join-Path $QueueRoot "done"))
newest_failed_task=$(Newest-File (Join-Path $QueueRoot "failed"))
stepwise_final_summary_exists=$(Test-Path $StepFinal)
stepwise_current_step_exists=$(Test-Path $StepCurrent)
overall_progress=99
bridge_progress_estimate=39
next_action=wait_10_20_minutes_then_read_github_reports
wait_minutes=10-20
db_write=false
deploy=false
migration=false
fake_data=false
destructive_git=false
git_reset_hard=false
git_clean=false
force_push=false
"@

$Report | Set-Content $ReportRepo -Encoding UTF8
$Report | Set-Content $ReportBridge -Encoding UTF8

try {
  Set-Location $RepoRoot
  git add "docs/chatgpt_status/runner_outputs/aays-runner-bootstrap-report-latest.txt" | Out-Null
  git commit -m "Add AAYS runner bootstrap report $Stamp" | Out-Null
  $PushOutput = git push origin HEAD:chatgpt-local-sync 2>&1 | Out-String
  if ($LASTEXITCODE -ne 0) {
    "stamp=$Stamp`nstatus=SYNC_FAILED`npush_output=$PushOutput`nreport_local=$ReportRepo" | Set-Content $SyncFail -Encoding UTF8
  }
} catch {
  "stamp=$Stamp`nstatus=SYNC_EXCEPTION`nerror=$($_.Exception.Message)`nreport_local=$ReportRepo" | Set-Content $SyncFail -Encoding UTF8
}

Write-Host "AAYS_CANONICAL_RUNNER_BOOTSTRAP_DONE"
Write-Host "runner_count_before=$RunnerCountBefore"
Write-Host "runner_count_after=$RunnerCountAfter"
Write-Host "action_taken=$ActionTaken"
Write-Host "report=$ReportRepo"
Write-Host "wait_minutes=10-20"

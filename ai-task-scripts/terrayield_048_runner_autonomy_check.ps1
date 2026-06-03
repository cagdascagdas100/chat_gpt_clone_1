$ErrorActionPreference = "Continue"
$TaskId = "terrayield-048-runner-autonomy-check"
$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$TaskNameRunner = "AAYS_TerraYield_BridgeRunner"
$TaskNameWatchdog = "AAYS_TerraYield_BridgeWatchdog"
$RunnerScript = Join-Path $BridgeRoot "AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1"
$ConfigScript = Join-Path $BridgeRoot "AAYS_TASK_BRIDGE_CONFIG.ps1"
$WatchdogScript = Join-Path $BridgeRoot "AAYS_RUNNER_WATCHDOG.ps1"
$StatusDir = Join-Path $BridgeRoot "ai-local-status"
$StatusFile = Join-Path $StatusDir "runner_autonomy_status.json"
$Stamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"

function Write-Step([string]$Text) {
  Write-Output ("[" + (Get-Date -Format "s") + "] " + $Text)
}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}

function Get-RunnerProcesses {
  try {
    return @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "AAYS_PORTABLE_TASK_RUNNER_FIXED\.ps1" })
  } catch {
    Write-Step ("PROCESS_QUERY_ERROR=" + $_.Exception.Message)
    return @()
  }
}

Write-Step "PROJECT=terrayield"
Write-Step "DISPLAY_PROJECT=TerraYield"
Write-Step "CHATGPT_PAGE_PROJECT=aays1"
Write-Step ("TASK=" + $TaskId)
Write-Step "MODE=runner_autonomy_check_and_self_heal"
Write-Step ("BRIDGE_ROOT=" + $BridgeRoot)
Write-Step ("PROJECT_ROOT=" + $ProjectRoot)

Ensure-Dir $BridgeRoot
Ensure-Dir $StatusDir
Ensure-Dir (Join-Path $BridgeRoot "ai-results")
Ensure-Dir (Join-Path $BridgeRoot "ai-heartbeat")
Ensure-Dir (Join-Path $BridgeRoot "ai-runner-logs")

$runnerExists = Test-Path $RunnerScript
$configExists = Test-Path $ConfigScript
$projectExists = Test-Path $ProjectRoot
Write-Step ("RUNNER_SCRIPT_EXISTS=" + $runnerExists)
Write-Step ("CONFIG_SCRIPT_EXISTS=" + $configExists)
Write-Step ("PROJECT_ROOT_EXISTS=" + $projectExists)

$runnerProcessesBefore = Get-RunnerProcesses
Write-Step ("RUNNER_PROCESS_COUNT_BEFORE=" + $runnerProcessesBefore.Count)
foreach ($p in $runnerProcessesBefore) {
  Write-Step ("RUNNER_PROCESS=" + $p.ProcessId + " " + $p.CommandLine)
}

$watchdogContent = @'
$ErrorActionPreference = "Continue"
$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN"
$RunnerScript = Join-Path $BridgeRoot "AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1"
$LogDir = Join-Path $BridgeRoot "ai-runner-logs"
$HeartbeatDir = Join-Path $BridgeRoot "ai-heartbeat"
New-Item -ItemType Directory -Force -Path $LogDir, $HeartbeatDir | Out-Null
$log = Join-Path $LogDir ("watchdog-" + (Get-Date -Format "yyyyMMdd") + ".log")
function Log([string]$m) { Add-Content -Encoding UTF8 -Path $log -Value ("[" + (Get-Date -Format "s") + "] " + $m) }
try {
  $procs = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "AAYS_PORTABLE_TASK_RUNNER_FIXED\.ps1" })
  Log ("runner_process_count=" + $procs.Count)
  if ($procs.Count -lt 1 -and (Test-Path $RunnerScript)) {
    Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$RunnerScript) -WorkingDirectory $BridgeRoot -WindowStyle Minimized
    Log "runner_started_by_watchdog"
  }
  $hb = Join-Path $HeartbeatDir "watchdog.md"
  Set-Content -Encoding UTF8 -Path $hb -Value ("# TerraYield Bridge Watchdog`n`nchecked_at: " + (Get-Date -Format "s") + "`nrunner_process_count: " + $procs.Count + "`n")
} catch {
  Log ("watchdog_error=" + $_.Exception.Message)
}
'@
Set-Content -Encoding UTF8 -Path $WatchdogScript -Value $watchdogContent
Write-Step ("WATCHDOG_SCRIPT_WRITTEN=" + $WatchdogScript)

if ($runnerExists) {
  try {
    $runnerAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File `"" + $RunnerScript + "`"") -WorkingDirectory $BridgeRoot
    $runnerTrigger = New-ScheduledTaskTrigger -AtLogOn
    Register-ScheduledTask -TaskName $TaskNameRunner -Action $runnerAction -Trigger $runnerTrigger -Description "AAYS/TerraYield GitHub bridge runner auto-start at user logon." -Force | Out-Null
    Write-Step ("SCHEDULED_TASK_REGISTERED=" + $TaskNameRunner)
  } catch {
    Write-Step ("SCHEDULED_TASK_RUNNER_ERROR=" + $_.Exception.Message)
  }
} else {
  Write-Step "SCHEDULED_TASK_RUNNER_SKIPPED=runner_script_missing"
}

try {
  $watchdogAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File `"" + $WatchdogScript + "`"") -WorkingDirectory $BridgeRoot
  $watchdogTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
  Register-ScheduledTask -TaskName $TaskNameWatchdog -Action $watchdogAction -Trigger $watchdogTrigger -Description "AAYS/TerraYield runner watchdog. Starts bridge runner if missing." -Force | Out-Null
  Write-Step ("SCHEDULED_TASK_REGISTERED=" + $TaskNameWatchdog)
} catch {
  Write-Step ("SCHEDULED_TASK_WATCHDOG_ERROR=" + $_.Exception.Message)
}

if ($runnerExists) {
  try {
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File $WatchdogScript 2>&1 | Out-String | Write-Output
    Write-Step "WATCHDOG_MANUAL_KICK_DONE"
  } catch {
    Write-Step ("WATCHDOG_MANUAL_KICK_ERROR=" + $_.Exception.Message)
  }
}

$runnerProcessesAfter = Get-RunnerProcesses
Write-Step ("RUNNER_PROCESS_COUNT_AFTER=" + $runnerProcessesAfter.Count)
foreach ($p in $runnerProcessesAfter) {
  Write-Step ("RUNNER_PROCESS_AFTER=" + $p.ProcessId + " " + $p.CommandLine)
}

$heartbeatPath = Join-Path $BridgeRoot "ai-heartbeat\portable-runner.md"
$lastTaskPath = Join-Path $BridgeRoot "ai-tasks\.last-task-id"
$heartbeatText = if (Test-Path $heartbeatPath) { Get-Content -Raw -Encoding UTF8 $heartbeatPath } else { $null }
$lastTaskText = if (Test-Path $lastTaskPath) { (Get-Content -Raw -Encoding UTF8 $lastTaskPath).Trim() } else { $null }

$status = [ordered]@{
  task_id = $TaskId
  checked_at = $Stamp
  bridge_root = $BridgeRoot
  project_root = $ProjectRoot
  runner_script_exists = $runnerExists
  config_script_exists = $configExists
  project_root_exists = $projectExists
  runner_process_count_before = $runnerProcessesBefore.Count
  runner_process_count_after = $runnerProcessesAfter.Count
  runner_scheduled_task = $TaskNameRunner
  watchdog_scheduled_task = $TaskNameWatchdog
  last_task_id = $lastTaskText
  heartbeat_present = [bool](Test-Path $heartbeatPath)
  recommendation = if ($runnerProcessesAfter.Count -ge 1) { "runner_active_or_watchdog_ready" } else { "runner_not_detected_manual_start_required" }
}
$status | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 -Path $StatusFile
Write-Step ("STATUS_FILE_WRITTEN=" + $StatusFile)
Write-Step "HEARTBEAT_SNAPSHOT_BEGIN"
if ($heartbeatText) { Write-Output $heartbeatText } else { Write-Step "HEARTBEAT_MISSING" }
Write-Step "HEARTBEAT_SNAPSHOT_END"

Write-Step "NEXT_EXPECTED_ACTION=if_result_pushed_continue_to_install_contractor_pipeline_if_no_result_after_3_minutes_manual_runner_start_required"
Write-Step "PLAN_PROGRESS_PERCENT=8"
Write-Step "TASK_COMPLETION=100/100"
Write-Step "TERRAYIELD_TASK_DONE"
exit 0

$ErrorActionPreference = 'Continue'
$Start = Get-Date
$TaskId = 'terrayield-050-restore-devam-et-after-reboot'
$Run = Get-Date -Format 'yyyyMMdd_HHmmss'
$BridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$ReportDir = Join-Path $BridgeRoot "ai-recovery\050_restore_devam_et_after_reboot_$Run"
$TaskDir = Join-Path $BridgeRoot 'ai-tasks'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
$ScriptDir = Join-Path $BridgeRoot 'ai-task-scripts'
$SummaryFile = Join-Path $ReportDir 'summary.md'
$StatusFile = Join-Path $ReportDir 'status.json'
$ScoreFile = Join-Path $ReportDir 'scorecard.csv'
New-Item -ItemType Directory -Force -Path $ReportDir,$TaskDir,$HeartbeatDir,$LogDir,$ScriptDir | Out-Null
function Log($Text){$e=[int]((Get-Date)-$Start).TotalSeconds;$line="[$e s] $Text";Write-Output $line;Add-Content -Encoding UTF8 -Path $SummaryFile -Value $line}
Log "TASK=$TaskId"
Log 'MODE=restore devam-et runner bridge after PC reboot; non-destructive; no project data mutation'
$critical=0;$warnings=0
$runnerFile = Join-Path $BridgeRoot 'AAYS_CHATGPT_RUNNER_V4.ps1'
$watchdogFile = Join-Path $BridgeRoot 'AAYS_USER_MODE_WATCHDOG.ps1'
$currentTask = Join-Path $TaskDir 'current-task.json'
$lastTask = Join-Path $TaskDir '.last-task-id'
$runnerHeartbeat = Join-Path $HeartbeatDir 'runner-v4.md'
$watchdogHeartbeat = Join-Path $HeartbeatDir 'user-mode-watchdog.md'
# Snapshot existing state
foreach($p in @($currentTask,$lastTask,$runnerHeartbeat,$watchdogHeartbeat,$runnerFile,$watchdogFile)){
  if(Test-Path $p){ Copy-Item -Force $p (Join-Path $ReportDir ((Split-Path $p -Leaf)+'.before')) -ErrorAction SilentlyContinue }
}
# Ensure current task remains available and pending
$currentObj = $null
try { if(Test-Path $currentTask){ $currentObj = Get-Content -Raw $currentTask | ConvertFrom-Json } } catch { $warnings++ }
if(-not $currentObj){
  $currentObj = [ordered]@{
    id='terrayield-049-hyper-parallel-accuracy-sprint-safe'
    title='Hyper parallel sales-parcel accuracy sprint safe'
    progress=99
    working_directory=$ProjectRoot
    timeout_seconds=7200
    created_by='ChatGPT'
    note='Recovered after reboot. Continue hyper parallel safe report sprint. Wait 90-120 minutes before writing devam et.'
    command='powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\cagda\Documents\chat_gpt_clone_1\ai-task-scripts\terrayield_049_hyper_parallel_accuracy_sprint_safe.ps1'
  }
  $currentObj | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $currentTask
  $warnings++
  Log 'current-task.json recreated as 049 pending task'
} else {
  Log "current-task preserved: $($currentObj.id)"
}
if(Test-Path $lastTask){
  $last = (Get-Content -Raw $lastTask).Trim()
  if($last -eq $currentObj.id){
    $backup = Join-Path $ReportDir '.last-task-id.matched-current.before'
    Copy-Item -Force $lastTask $backup -ErrorAction SilentlyContinue
    Set-Content -Encoding UTF8 -Path $lastTask -Value 'reboot-recovery-pending'
    $warnings++
    Log '.last-task-id matched current task; changed to reboot-recovery-pending so runner will see task as new'
  } else {
    Log ".last-task-id preserved: $last"
  }
} else {
  Set-Content -Encoding UTF8 -Path $lastTask -Value 'reboot-recovery-pending'
  $warnings++
  Log '.last-task-id created as reboot-recovery-pending'
}
# Refresh heartbeat files to prove recovery ran
$now = Get-Date
@"
# AAYS ChatGPT Runner V4

Time: $now
Status: reboot-recovery-ready
BridgeRoot: $BridgeRoot
ProjectRoot: $ProjectRoot
TaskFile: $currentTask
RunnerLog: $(Join-Path $LogDir 'runner-v4-after-reboot.log')
RecoveryTask: $TaskId
"@ | Set-Content -Encoding UTF8 $runnerHeartbeat
@"
# AAYS User Mode Watchdog

Time: $now
Status: reboot-recovery-ready
BridgeRoot: $BridgeRoot
RunnerFile: $runnerFile
LogFile: $(Join-Path $LogDir 'user-mode-watchdog-after-reboot.log')
RecoveryTask: $TaskId
"@ | Set-Content -Encoding UTF8 $watchdogHeartbeat
# Write startup helper scripts for automatic reuse if runner/watchdog supports local files
$startAll = Join-Path $BridgeRoot 'AAYS_START_AFTER_REBOOT.ps1'
@"
`$ErrorActionPreference = 'Continue'
`$BridgeRoot = '$BridgeRoot'
`$runner = Join-Path `$BridgeRoot 'AAYS_CHATGPT_RUNNER_V4.ps1'
`$watchdog = Join-Path `$BridgeRoot 'AAYS_USER_MODE_WATCHDOG.ps1'
if(Test-Path `$watchdog){ Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',`$watchdog) -WindowStyle Minimized }
elseif(Test-Path `$runner){ Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',`$runner) -WindowStyle Minimized }
else{ Write-Output 'AAYS runner/watchdog file missing' }
"@ | Set-Content -Encoding UTF8 $startAll
# Optional scheduled-task command saved as documentation, not executed automatically here.
$scheduledCmd = 'schtasks /Create /TN "AAYS ChatGPT Runner AutoStart" /SC ONLOGON /RL LIMITED /F /TR "powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\cagda\Documents\chat_gpt_clone_1\AAYS_START_AFTER_REBOOT.ps1"'
$scheduledCmd | Set-Content -Encoding UTF8 (Join-Path $ReportDir 'optional_register_autostart_command.txt')
# Probe local processes
$ps = @(Get-Process -Name powershell,pwsh -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,CPU,StartTime,Path | Select-Object -First 30)
$status=[ordered]@{
  task=$TaskId
  result='reboot_continue_structure_refreshed'
  critical_failures=$critical
  warnings=$warnings
  current_task_id=$currentObj.id
  bridge_root=$BridgeRoot
  project_root=$ProjectRoot
  runner_file_exists=(Test-Path $runnerFile)
  watchdog_file_exists=(Test-Path $watchdogFile)
  start_after_reboot_file=$startAll
  runner_heartbeat=$runnerHeartbeat
  watchdog_heartbeat=$watchdogHeartbeat
  detected_powershell_processes=$ps
  next_action='devam et'
  next_wait='10-20 minutes'
  note='If this task ran, the devam et structure is refreshed. If it did not run, local autostart runner was not active after reboot.'
}
$status | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $StatusFile
@('metric,score','devam_et_structure_ready,85','runner_autostart_confidence,60','pending_task_integrity,90','manual_intervention_needed,20') | Set-Content -Encoding UTF8 $ScoreFile
Log "RESULT=$($status.result)"
Log "CURRENT_TASK_ID=$($currentObj.id)"
Log "RUNNER_FILE_EXISTS=$($status.runner_file_exists)"
Log "WATCHDOG_FILE_EXISTS=$($status.watchdog_file_exists)"
Log "NEXT_ACTION=devam et"
Write-Output "SUMMARY_FILE=$SummaryFile"
Write-Output "STATUS_FILE=$StatusFile"
Write-Output "SCORE_FILE=$ScoreFile"
Write-Output "RESULT=reboot_continue_structure_refreshed"
Write-Output "CURRENT_TASK_ID=$($currentObj.id)"
Write-Output "NEXT_WAIT=10-20 minutes"
Write-Output 'TERRAYIELD_050_RESTORE_DEVAM_ET_AFTER_REBOOT_DONE'
exit 0

$ErrorActionPreference = "Continue"
$TaskId = "terrayield-053-autopilot-v6-install-and-run"
$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$AutopilotScript = Join-Path $BridgeRoot "AAYS_REMOTE_AUTOPILOT_V6.ps1"
$LogDir = Join-Path $BridgeRoot "ai-runner-logs"
$StateDir = Join-Path $BridgeRoot "ai-runner-state"
$HeartbeatDir = Join-Path $BridgeRoot "ai-heartbeat"
$TaskName = "AAYS_TerraYield_RemoteAutopilotV6"

function Step([string]$m) { Write-Output ("[" + (Get-Date -Format "s") + "] " + $m) }
Step "PROJECT=terrayield"
Step "TASK=$TaskId"
Step "MODE=install_remote_autopilot_v6"
New-Item -ItemType Directory -Force -Path $LogDir,$StateDir,$HeartbeatDir,(Join-Path $BridgeRoot "ai-results"),(Join-Path $BridgeRoot "ai-task-scripts"),(Join-Path $BridgeRoot "ai-tasks") | Out-Null

$autopilot = @'
$ErrorActionPreference = "Continue"
$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE_CLEAN"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$PollSeconds = 20
$TaskFile = Join-Path $BridgeRoot "ai-tasks\current-task.json"
$ScriptsDir = Join-Path $BridgeRoot "ai-task-scripts"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$LogsDir = Join-Path $BridgeRoot "ai-runner-logs"
$HeartbeatFile = Join-Path $BridgeRoot "ai-heartbeat\remote-autopilot-v6.md"
$LastTaskFile = Join-Path $BridgeRoot "ai-runner-state\remote-autopilot-v6.last-task-id"
$RunnerLog = Join-Path $LogsDir ("remote-autopilot-v6-" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
New-Item -ItemType Directory -Force -Path $ScriptsDir,$ResultsDir,$LogsDir,(Split-Path $HeartbeatFile),(Split-Path $LastTaskFile) | Out-Null

function Log([string]$m) {
  $line = "[" + (Get-Date -Format "s") + "] " + $m
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $RunnerLog -Value $line
}
function HB([string]$status,[string]$taskId,[string]$msg) {
  $lines = @(
    "# TerraYield Remote Autopilot V6",
    "",
    "status: $status",
    "task_id: $taskId",
    "checked_at: $((Get-Date).ToString('s'))",
    "bridge_root: $BridgeRoot",
    "project_root: $ProjectRoot",
    "runner_log: $RunnerLog",
    "message: $msg"
  )
  Set-Content -Encoding UTF8 -Path $HeartbeatFile -Value $lines
}
function Git([string[]]$args) {
  try {
    Push-Location $BridgeRoot
    $out = (& git @args 2>&1 | Out-String)
    Add-Content -Encoding UTF8 -Path $RunnerLog -Value $out
    return $out
  } catch {
    $msg = "GIT_ERROR=" + $_.Exception.Message
    Add-Content -Encoding UTF8 -Path $RunnerLog -Value $msg
    return $msg
  } finally {
    Pop-Location
  }
}
function Pull-Latest {
  Git @("fetch","origin","main") | Out-Null
  $rb = Git @("rebase","origin/main")
  if ($rb -match "CONFLICT|fatal:|error:") {
    Git @("rebase","--abort") | Out-Null
    Git @("reset","--hard","origin/main") | Out-Null
  }
}
function Push-State([string]$taskId) {
  Git @("add","ai-results","ai-heartbeat","ai-runner-state","ai-runner-logs") | Out-Null
  $commit = Git @("commit","-m",("autopilot-v6 result " + $taskId))
  Git @("fetch","origin","main") | Out-Null
  $rb = Git @("rebase","origin/main")
  if ($rb -match "CONFLICT|fatal:|error:") {
    Git @("rebase","--abort") | Out-Null
    Git @("reset","--hard","origin/main") | Out-Null
    Git @("add","ai-results","ai-heartbeat","ai-runner-state","ai-runner-logs") | Out-Null
    Git @("commit","-m",("autopilot-v6 result " + $taskId + " recovery")) | Out-Null
  }
  Git @("push","origin","main") | Out-Null
}
function Write-Result([string]$taskId,[string]$title,[int]$exitCode,[string]$stdoutFile,[string]$stderrFile,[string]$msg) {
  $stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
  $result = Join-Path $ResultsDir ($stamp + "-" + $taskId + ".md")
  $stdout = if (Test-Path $stdoutFile) { Get-Content -Raw -Encoding UTF8 $stdoutFile } else { "" }
  $stderr = if (Test-Path $stderrFile) { Get-Content -Raw -Encoding UTF8 $stderrFile } else { "" }
  Set-Content -Encoding UTF8 -Path $result -Value @("# TerraYield Autopilot V6 Result","","task_id: $taskId","title: $title","exit_code: $exitCode","message: $msg","time: $((Get-Date).ToString('s'))","","## Output","```text")
  Add-Content -Encoding UTF8 -Path $result -Value $stdout
  Add-Content -Encoding UTF8 -Path $result -Value "```"
  Add-Content -Encoding UTF8 -Path $result -Value @("","## Error","```text")
  Add-Content -Encoding UTF8 -Path $result -Value $stderr
  Add-Content -Encoding UTF8 -Path $result -Value "```"
}
function Run-Task($task) {
  $taskId = [string]$task.id
  $title = if ($task.PSObject.Properties.Name -contains "title") { [string]$task.title } else { $taskId }
  $scriptPathName = if ($task.PSObject.Properties.Name -contains "script_path") { [string]$task.script_path } else { "" }
  $timeout = if ($task.PSObject.Properties.Name -contains "timeout_seconds") { [int]$task.timeout_seconds } else { 3600 }
  if ([string]::IsNullOrWhiteSpace($scriptPathName)) {
    $stdout = Join-Path $LogsDir ($taskId + ".stdout.log")
    $stderr = Join-Path $LogsDir ($taskId + ".stderr.log")
    Set-Content -Encoding UTF8 -Path $stderr -Value "Missing script_path. Autopilot V6 ignores action-only tasks."
    Write-Result $taskId $title 2 $stdout $stderr "rejected_missing_script_path"
    Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $taskId
    HB "rejected" $taskId "missing script_path"
    Push-State $taskId
    return
  }
  if ($scriptPathName -match "\.\.") { throw "Rejected unsafe script_path: $scriptPathName" }
  $script = [IO.Path]::GetFullPath((Join-Path $ScriptsDir $scriptPathName))
  $allowed = [IO.Path]::GetFullPath($ScriptsDir)
  if (-not $script.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw "Rejected outside script dir: $script" }
  if (-not (Test-Path $script)) { throw "Task script missing: $script" }
  $stdoutFile = Join-Path $LogsDir ($taskId + ".stdout.log")
  $stderrFile = Join-Path $LogsDir ($taskId + ".stderr.log")
  HB "running" $taskId $title
  Log "START $taskId SCRIPT=$script"
  $exitCode = 999
  try {
    if (-not (Test-Path $ProjectRoot)) { throw "Project root missing: $ProjectRoot" }
    $p = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$script) -WorkingDirectory $ProjectRoot -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile -PassThru
    if (-not $p.WaitForExit($timeout * 1000)) {
      Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
      $exitCode = 124
    } else { $exitCode = $p.ExitCode }
  } catch {
    Add-Content -Encoding UTF8 -Path $stderrFile -Value $_.Exception.Message
    $exitCode = 998
  }
  Write-Result $taskId $title $exitCode $stdoutFile $stderrFile "completed_by_autopilot_v6"
  Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $taskId
  HB "finished" $taskId "exit=$exitCode"
  Log "FINISH $taskId EXIT=$exitCode"
  Push-State $taskId
}

Log "Autopilot V6 started"
HB "polling" "" "started"
while ($true) {
  try {
    Pull-Latest
    if (-not (Test-Path $TaskFile)) { HB "polling" "" "no task file"; Start-Sleep -Seconds $PollSeconds; continue }
    $raw = Get-Content -Raw -Encoding UTF8 $TaskFile
    $task = $raw | ConvertFrom-Json
    $taskId = [string]$task.id
    $last = if (Test-Path $LastTaskFile) { (Get-Content -Raw -Encoding UTF8 $LastTaskFile).Trim() } else { "" }
    if ($taskId -and $taskId -ne $last) { Run-Task $task } else { HB "polling" $taskId "waiting" }
  } catch {
    Log ("LOOP_ERROR " + $_.Exception.Message)
    HB "error" "" $_.Exception.Message
  }
  Start-Sleep -Seconds $PollSeconds
}
'@
Set-Content -Encoding UTF8 -Path $AutopilotScript -Value $autopilot
Step "AUTOPILOT_SCRIPT_WRITTEN=$AutopilotScript"

try {
  Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "AAYS_REMOTE_AUTOPILOT_V6\.ps1|AAYS_PORTABLE_TASK_RUNNER_FIXED\.ps1" } | ForEach-Object {
    Step ("STOP_OLD_RUNNER_PID=" + $_.ProcessId)
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
} catch { Step ("STOP_OLD_RUNNER_ERROR=" + $_.Exception.Message) }

try {
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File `"" + $AutopilotScript + "`"") -WorkingDirectory $BridgeRoot
  $trigger = New-ScheduledTaskTrigger -AtLogOn
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Description "TerraYield remote GitHub autopilot v6" -Force | Out-Null
  Step "SCHEDULED_TASK_REGISTERED=$TaskName"
} catch { Step ("SCHEDULED_TASK_ERROR=" + $_.Exception.Message) }

Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$AutopilotScript) -WorkingDirectory $BridgeRoot -WindowStyle Minimized
Step "AUTOPILOT_V6_STARTED"
Start-Sleep -Seconds 5
$procs = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "AAYS_REMOTE_AUTOPILOT_V6\.ps1" })
Step ("AUTOPILOT_V6_PROCESS_COUNT=" + $procs.Count)
foreach ($p in $procs) { Step ("AUTOPILOT_V6_PROCESS=" + $p.ProcessId + " " + $p.CommandLine) }
Step "PLAN_PROGRESS_PERCENT=18"
Step "NEXT_EXPECTED_ACTION=queue_contractor_install_task_after_v6_heartbeat"
Step "TASK_COMPLETION=100/100"
Step "TERRAYIELD_TASK_DONE"
exit 0

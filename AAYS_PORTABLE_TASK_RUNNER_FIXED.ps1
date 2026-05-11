$ErrorActionPreference = "Continue"

$ConfigPath = Join-Path $PSScriptRoot "AAYS_TASK_BRIDGE_CONFIG.ps1"
if (Test-Path $ConfigPath) { . $ConfigPath }

$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { $PSScriptRoot }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { $BridgeRoot }
$PollSeconds = if ($env:AAYS_RUNNER_POLL_SECONDS) { [int]$env:AAYS_RUNNER_POLL_SECONDS } else { 20 }
$DefaultTimeout = if ($env:AAYS_TASK_TIMEOUT_SECONDS) { [int]$env:AAYS_TASK_TIMEOUT_SECONDS } else { 3600 }
$AllowedScriptDir = if ($env:AAYS_ALLOWED_SCRIPT_DIR) { $env:AAYS_ALLOWED_SCRIPT_DIR } else { "ai-task-scripts" }

$TaskFile = Join-Path $BridgeRoot "ai-tasks\current-task.json"
$LastTaskFile = Join-Path $BridgeRoot "ai-tasks\.last-task-id"
$HeartbeatFile = Join-Path $BridgeRoot "ai-heartbeat\portable-runner.md"
$ResultDir = Join-Path $BridgeRoot "ai-results"
$LogDir = Join-Path $BridgeRoot "ai-runner-logs"
$RunnerLog = Join-Path $LogDir ("portable-runner-fixed-" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")

New-Item -ItemType Directory -Force -Path (Join-Path $BridgeRoot "ai-tasks"),(Join-Path $BridgeRoot "ai-heartbeat"),$ResultDir,$LogDir,(Join-Path $BridgeRoot $AllowedScriptDir) | Out-Null

function Write-RunnerLog([string]$Text) {
  $line = "[" + (Get-Date -Format "s") + "] " + $Text
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $RunnerLog -Value $line
}

function Write-Heartbeat([string]$Status, [string]$TaskId = "", [string]$Message = "") {
  $body = @"
# AAYS Portable Task Runner Fixed

Time: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Status: $Status
TaskId: $TaskId
BridgeRoot: $BridgeRoot
ProjectRoot: $ProjectRoot
TaskFile: $TaskFile
RunnerLog: $RunnerLog
Message: $Message
GitRecovery: enabled
SafeScriptOnly: enabled
"@
  Set-Content -Encoding UTF8 -Path $HeartbeatFile -Value $body
}

function Invoke-GitCmd([string]$ArgsLine) {
  try {
    Push-Location $BridgeRoot
    $out = Invoke-Expression ("git " + $ArgsLine + " 2>&1") | Out-String
    Add-Content -Encoding UTF8 -Path $RunnerLog -Value $out
    return $out
  } catch {
    $msg = "GIT_EXCEPTION=" + $_.Exception.Message
    Add-Content -Encoding UTF8 -Path $RunnerLog -Value $msg
    return $msg
  } finally {
    Pop-Location
  }
}

function Sync-GitBeforeRead {
  Invoke-GitCmd "add ai-heartbeat ai-runner-logs ai-results ai-tasks/.last-task-id"
  Invoke-GitCmd "stash push -m portable-runner-auto-stash-before-pull -- ai-heartbeat ai-runner-logs ai-results ai-tasks/.last-task-id"
  Invoke-GitCmd "fetch origin main"
  $pull = Invoke-GitCmd "rebase origin/main"
  if ($pull -match "CONFLICT|error:|fatal:") {
    Invoke-GitCmd "rebase --abort"
    Invoke-GitCmd "reset --hard origin/main"
  }
}

function Push-ResultToGit([string]$TaskId) {
  Invoke-GitCmd "add ai-results ai-heartbeat ai-tasks/.last-task-id ai-runner-logs"
  Invoke-GitCmd ('commit -m "Portable runner result ' + $TaskId + '"')
  Invoke-GitCmd "fetch origin main"
  $rb = Invoke-GitCmd "rebase origin/main"
  if ($rb -match "CONFLICT|error:|fatal:") {
    Invoke-GitCmd "rebase --abort"
    Invoke-GitCmd "reset --hard origin/main"
    Invoke-GitCmd "add ai-results ai-heartbeat ai-tasks/.last-task-id ai-runner-logs"
    Invoke-GitCmd ('commit -m "Portable runner result ' + $TaskId + ' recovery"')
  }
  Invoke-GitCmd "push origin main"
}

function Read-TaskSafely {
  if (-not (Test-Path $TaskFile)) { return $null }
  try {
    $raw = Get-Content -Raw -Encoding UTF8 $TaskFile
    if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
    $task = $raw | ConvertFrom-Json
    if ($null -eq $task) { return $null }
    if (-not ($task.PSObject.Properties.Name -contains "id")) { return $null }
    if ([string]::IsNullOrWhiteSpace([string]$task.id)) { return $null }
    return $task
  } catch {
    Write-RunnerLog ("TASK_JSON_ERROR " + $_.Exception.Message)
    return $null
  }
}

function Resolve-TaskCommand($Task) {
  if ($Task.PSObject.Properties.Name -contains "command" -and -not [string]::IsNullOrWhiteSpace([string]$Task.command)) {
    return [string]$Task.command
  }
  if ($Task.PSObject.Properties.Name -contains "script_path" -and -not [string]::IsNullOrWhiteSpace([string]$Task.script_path)) {
    $candidate = [string]$Task.script_path
    $scriptPath = [IO.Path]::GetFullPath((Join-Path (Join-Path $BridgeRoot $AllowedScriptDir) $candidate))
    $allowedRoot = [IO.Path]::GetFullPath((Join-Path $BridgeRoot $AllowedScriptDir))
    if (-not $scriptPath.StartsWith($allowedRoot,[StringComparison]::OrdinalIgnoreCase)) { return "" }
    return "powershell -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
  }
  return ""
}

function Test-AllowedTaskCommand([string]$CommandText) {
  if ([string]::IsNullOrWhiteSpace($CommandText)) { return $false }
  $normalized = $CommandText.Replace("/", "\")
  $allowedPart = "\" + $AllowedScriptDir + "\"
  if ($normalized -notmatch "powershell") { return $false }
  if ($normalized -notmatch "\-File") { return $false }
  if ($normalized -notlike ("*" + $allowedPart + "*.ps1*")) { return $false }
  if ($normalized -match "\.\.") { return $false }
  return $true
}

function Run-CurrentTask($Task) {
  $TaskId = [string]$Task.id
  $Title = if ($Task.PSObject.Properties.Name -contains "title") { [string]$Task.title } else { $TaskId }
  $WorkingDirectory = if ($Task.PSObject.Properties.Name -contains "working_directory") { [string]$Task.working_directory } else { $ProjectRoot }
  $TimeoutSeconds = if ($Task.PSObject.Properties.Name -contains "timeout_seconds") { [int]$Task.timeout_seconds } else { $DefaultTimeout }
  $Command = Resolve-TaskCommand $Task
  $stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
  $stdoutFile = Join-Path $LogDir ($TaskId + "-stdout.log")
  $stderrFile = Join-Path $LogDir ($TaskId + "-stderr.log")
  $ResultFile = Join-Path $ResultDir ($stamp + "-" + $TaskId + ".md")

  Write-Heartbeat "running" $TaskId $Title
  Write-RunnerLog ("START " + $TaskId + " :: " + $Command)

  if (-not (Test-AllowedTaskCommand $Command)) {
    Set-Content -Encoding UTF8 -Path $ResultFile -Value ("# AAYS Portable Task Runner Result`n`n## Task ID`n" + $TaskId + "`n`n## Status`nRejected`n`n## Reason`nCommand rejected by safe-script policy.`n`n## Command`n```text`n" + $Command + "`n```")
    Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $TaskId
    Push-ResultToGit $TaskId
    return
  }

  $exitCode = 999
  $timedOut = $false
  try {
    if (-not (Test-Path $WorkingDirectory)) { New-Item -ItemType Directory -Force -Path $WorkingDirectory | Out-Null }
    $p = Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-Command",$Command) -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile -PassThru -WindowStyle Hidden
    $finished = $p.WaitForExit($TimeoutSeconds * 1000)
    if (-not $finished) { $timedOut = $true; try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch {}; $exitCode = 124 } else { $exitCode = $p.ExitCode }
  } catch {
    Add-Content -Encoding UTF8 -Path $stderrFile -Value $_.Exception.Message
    $exitCode = 998
  }

  $stdout = if (Test-Path $stdoutFile) { Get-Content -Raw -Encoding UTF8 $stdoutFile } else { "" }
  $stderr = if (Test-Path $stderrFile) { Get-Content -Raw -Encoding UTF8 $stderrFile } else { "" }
  $body = @"
# AAYS Portable Task Runner Result

## Task
$Title

## Task ID
$TaskId

## Time
$(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Working Directory
$WorkingDirectory

## Timeout Seconds
$TimeoutSeconds

## Timed Out
$timedOut

## Exit Code
$exitCode

## Output
````text
$stdout
````

## Error
````text
$stderr
````
"@
  Set-Content -Encoding UTF8 -Path $ResultFile -Value $body
  Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $TaskId
  Write-RunnerLog ("FINISH " + $TaskId + " EXIT=" + $exitCode)
  Push-ResultToGit $TaskId
  Write-Heartbeat "finished" $TaskId ("exit=" + $exitCode)
}

Write-RunnerLog "Portable fixed runner started"
Write-Heartbeat "polling" "" "started"
while ($true) {
  try {
    Sync-GitBeforeRead
    $task = Read-TaskSafely
    if ($null -eq $task) { Write-Heartbeat "polling" "" "no-valid-task"; Start-Sleep -Seconds $PollSeconds; continue }
    $taskId = [string]$task.id
    $lastId = if (Test-Path $LastTaskFile) { (Get-Content -Raw -Encoding UTF8 $LastTaskFile).Trim() } else { "" }
    if (-not [string]::IsNullOrWhiteSpace($taskId) -and $taskId -ne $lastId) { Run-CurrentTask $task } else { Write-Heartbeat "polling" $taskId "already-processed-or-waiting" }
  } catch {
    Write-RunnerLog ("LOOP_ERROR " + $_.Exception.Message)
    Write-Heartbeat "error" "" $_.Exception.Message
  }
  Start-Sleep -Seconds $PollSeconds
}

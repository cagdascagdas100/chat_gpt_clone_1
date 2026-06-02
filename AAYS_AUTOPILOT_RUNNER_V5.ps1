$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$TaskFile = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$StateFile = Join-Path $BridgeRoot 'ai-tasks\.last-task-id'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
$TmpDir = Join-Path $BridgeRoot 'ai-tmp'
$AllowedScriptDir = Join-Path $BridgeRoot 'ai-task-scripts'
$RunnerName = 'AAYS_AUTOPILOT_RUNNER_V5'
$MutexName = 'Global\AAYS_AUTOPILOT_RUNNER_V5_SINGLE_INSTANCE'
$PollSeconds = 12

New-Item -ItemType Directory -Force -Path $ResultDir,$HeartbeatDir,$LogDir,$TmpDir,$AllowedScriptDir | Out-Null
$RunnerLog = Join-Path $LogDir ('autopilot-v5-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')

$Mutex = New-Object System.Threading.Mutex($false, $MutexName)
if (-not $Mutex.WaitOne(1000)) {
  Write-Host 'AAYS_AUTOPILOT_RUNNER_V5_ALREADY_RUNNING'
  exit 0
}

function Write-TextSafe([string]$Path, [string]$Text) {
  for ($i=1; $i -le 10; $i++) {
    try {
      $dir = Split-Path $Path -Parent
      if (!(Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
      $tmp = Join-Path $dir ('.' + [IO.Path]::GetFileName($Path) + '.tmp.' + [guid]::NewGuid().ToString('N'))
      [IO.File]::WriteAllText($tmp, $Text, [Text.UTF8Encoding]::new($true))
      Move-Item -Force $tmp $Path
      return $true
    } catch { Start-Sleep -Milliseconds (200*$i) }
  }
  return $false
}

function Log([string]$Text) {
  $line = '[' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '] ' + $Text
  Write-Host $line
  Add-Content -Encoding UTF8 -Path $RunnerLog -Value $line
}

function Heartbeat([string]$Status) {
  $txt = "# AAYS Autopilot Runner V5`n`nTime: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`nStatus: $Status`nBridgeRoot: $BridgeRoot`nProjectRoot: $ProjectRoot`nTaskFile: $TaskFile`nStateFile: $StateFile`nRunnerLog: $RunnerLog`nSupports: command, script_path, action=status_check, action=health_check`n"
  Write-TextSafe (Join-Path $HeartbeatDir 'autopilot-v5.md') $txt | Out-Null
}

function GitSync() {
  try {
    git -C $BridgeRoot config --local pull.rebase false | Out-Null
    git -C $BridgeRoot fetch origin main --prune | Out-Null
    git -C $BridgeRoot pull --ff-only origin main | Out-Null
  } catch { Log ('GIT_SYNC_WARN: ' + $_.Exception.Message) }
}

function GitPush([string]$Message) {
  try {
    git -C $BridgeRoot add ai-results ai-heartbeat ai-runner-logs ai-tasks AAYS_AUTOPILOT_RUNNER_V5.ps1 INSTALL_AAYS_AUTOPILOT_STARTUP.ps1 2>$null | Out-Null
    $s = git -C $BridgeRoot status --short 2>$null
    if ($s) {
      git -C $BridgeRoot commit -m $Message | Out-Null
      git -C $BridgeRoot fetch origin main --prune | Out-Null
      git -C $BridgeRoot pull --rebase origin main | Out-Null
      git -C $BridgeRoot push origin main | Out-Null
    }
  } catch { Log ('GIT_PUSH_WARN: ' + $_.Exception.Message) }
}

function IsAllowedWorkdir([string]$Path) {
  try {
    $full = [IO.Path]::GetFullPath($Path)
    $allowed = [IO.Path]::GetFullPath($ProjectRoot)
    return $full.StartsWith($allowed, [StringComparison]::OrdinalIgnoreCase)
  } catch { return $false }
}

function IsAllowedScript([string]$Path) {
  try {
    $full = [IO.Path]::GetFullPath($Path)
    $allowed = [IO.Path]::GetFullPath($AllowedScriptDir)
    return $full.StartsWith($allowed, [StringComparison]::OrdinalIgnoreCase)
  } catch { return $false }
}

function BuildActionCommand([string]$Action) {
  if ($Action -eq 'health_check') { return "Write-Output 'AAYS_AUTOPILOT_HEALTH=OK'; Get-Date" }
  if ($Action -eq 'status_check') { return "Write-Output 'AAYS_AUTOPILOT_STATUS=OK'; git status --short" }
  return "Write-Output 'UNKNOWN_ACTION: $Action'; exit 9005"
}

function BuildScriptPathCommand([string]$ScriptPath) {
  if ([string]::IsNullOrWhiteSpace($ScriptPath)) { return $null }
  $candidate = $ScriptPath
  if (-not [IO.Path]::IsPathRooted($candidate)) { $candidate = Join-Path $AllowedScriptDir $candidate }
  $full = [IO.Path]::GetFullPath($candidate)
  if (-not (IsAllowedScript $full)) { return "Write-Output 'SCRIPT_PATH_NOT_ALLOWED: $full'; exit 9003" }
  if (-not (Test-Path $full)) { return "Write-Output 'SCRIPT_PATH_NOT_FOUND: $full'; exit 9004" }
  return "& '$full'; exit `$LASTEXITCODE"
}

function IsBlocked([string]$Command) {
  if ([string]::IsNullOrWhiteSpace($Command)) { return $false }
  $patterns = @('Remove-Item\s+-Recurse\s+-Force\s+C:\\','rm\s+-rf','Format-Volume','Clear-Disk','Remove-Partition','shutdown','Restart-Computer','Stop-Computer','cipher\s+/w','net\s+user','New-LocalUser','Set-LocalUser','\biex\b')
  foreach ($p in $patterns) { if ($Command -match $p) { return $true } }
  return $false
}

function RunScriptText([string]$Text, [string]$Workdir, [int]$TimeoutSeconds, [string]$TaskId) {
  $safeId = $TaskId -replace '[^a-zA-Z0-9_-]+','-'
  $tmpScript = Join-Path $TmpDir ('autopilot-' + $safeId + '.ps1')
  Write-TextSafe $tmpScript $Text | Out-Null
  $psi = New-Object Diagnostics.ProcessStartInfo
  $psi.FileName = 'powershell.exe'
  $psi.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $tmpScript + '"'
  $psi.WorkingDirectory = $Workdir
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.UseShellExecute = $false
  $psi.CreateNoWindow = $true
  $p = New-Object Diagnostics.Process
  $p.StartInfo = $psi
  try { [void]$p.Start() } catch { return [pscustomobject]@{ExitCode=997;Output='PROCESS_START_FAILED';Error=$_.Exception.Message} }
  $outTask = $p.StandardOutput.ReadToEndAsync()
  $errTask = $p.StandardError.ReadToEndAsync()
  $done = $p.WaitForExit($TimeoutSeconds * 1000)
  if (-not $done) {
    try { $p.Kill() } catch {}
    return [pscustomobject]@{ExitCode=124;Output=$outTask.Result;Error=$errTask.Result + "`nTIMEOUT_AFTER_SECONDS=$TimeoutSeconds"}
  }
  return [pscustomobject]@{ExitCode=$p.ExitCode;Output=$outTask.Result;Error=$errTask.Result}
}

Log 'AAYS Autopilot Runner V5 started. This window should stay open.'
Heartbeat 'started'
GitPush 'Autopilot V5 started'

while ($true) {
  try {
    GitSync
    Heartbeat 'polling'
    if (!(Test-Path $TaskFile)) { Log 'No current-task.json'; GitPush 'Autopilot V5 heartbeat no task'; Start-Sleep -Seconds $PollSeconds; continue }

    $raw = Get-Content -Raw -Encoding UTF8 $TaskFile
    $task = $raw | ConvertFrom-Json
    $taskId = [string]$task.id
    if ([string]::IsNullOrWhiteSpace($taskId)) { Log 'Task without id'; Start-Sleep -Seconds $PollSeconds; continue }

    $lastId = ''
    if (Test-Path $StateFile) { $lastId = (Get-Content -Raw -Encoding UTF8 $StateFile).Trim([char]0xFEFF).Trim() }
    if ($lastId -eq $taskId.Trim()) { Log "Idle. Last task=$lastId"; Start-Sleep -Seconds $PollSeconds; continue }

    $title = if ($task.title) { [string]$task.title } else { 'Untitled task' }
    $workdir = if ($task.working_directory) { [string]$task.working_directory } else { $ProjectRoot }
    $timeout = if ($task.timeout_seconds -ne $null) { [int]$task.timeout_seconds } else { 600 }
    if ($timeout -lt 30) { $timeout = 30 }
    if ($timeout -gt 14400) { $timeout = 14400 }

    $command = if ($task.command) { [string]$task.command } else { '' }
    $scriptPath = if ($task.script_path) { [string]$task.script_path } else { '' }
    $action = if ($task.action) { [string]$task.action } else { '' }
    if ([string]::IsNullOrWhiteSpace($command) -and -not [string]::IsNullOrWhiteSpace($scriptPath)) { $command = BuildScriptPathCommand $scriptPath }
    if ([string]::IsNullOrWhiteSpace($command)) { $command = BuildActionCommand $action }

    Log "Task found: $taskId | $title | timeout=$timeout"
    Heartbeat "running $taskId"

    if (-not (IsAllowedWorkdir $workdir)) {
      $exitCode = 9001; $output = "WORKDIR_NOT_ALLOWED: $workdir"; $errorText = ''
    } elseif (IsBlocked $command) {
      $exitCode = 9002; $output = 'BLOCKED_BY_RUNNER_SAFETY_POLICY'; $errorText = $command
    } else {
      $run = RunScriptText $command $workdir $timeout $taskId
      $exitCode = $run.ExitCode; $output = $run.Output; $errorText = $run.Error
    }

    $safeId = $taskId -replace '[^a-zA-Z0-9_-]+','-'
    $ts = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
    $resultPath = Join-Path $ResultDir ("$ts-$safeId.md")
    $md = "# AAYS Autopilot Runner V5 Result`n`n## Task`n$title`n`n## Task ID`n$taskId`n`n## Time`n$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n`n## Working Directory`n$workdir`n`n## Timeout Seconds`n$timeout`n`n## Exit Code`n$exitCode`n`n## Output`n````text`n$output`n`````n`n## Error`n````text`n$errorText`n`````n"
    Write-TextSafe $resultPath $md | Out-Null
    Write-TextSafe $StateFile $taskId | Out-Null
    Heartbeat "finished $taskId exit=$exitCode"
    GitPush "Autopilot V5 result $taskId"
    Log "Task finished: $taskId exit=$exitCode"
  } catch {
    Log ('LOOP_ERROR: ' + $_.Exception.Message)
    Heartbeat ('error-continuing ' + $_.Exception.Message)
    GitPush 'Autopilot V5 error heartbeat'
    Start-Sleep -Seconds $PollSeconds
  }
}

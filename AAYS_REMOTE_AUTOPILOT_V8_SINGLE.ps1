$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$TaskFile = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$ScriptsDir = Join-Path $BridgeRoot 'ai-task-scripts'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$LogsDir = Join-Path $BridgeRoot 'ai-runner-logs'
$StateDir = Join-Path $BridgeRoot 'ai-runner-state'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatFile = Join-Path $HeartbeatDir 'remote-autopilot-v8.md'
$LastTaskFile = Join-Path $StateDir 'remote-autopilot-v8.last-task-id'
$RunnerLog = Join-Path $LogsDir ('remote-autopilot-v8-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
$PollSeconds = 20
New-Item -ItemType Directory -Force -Path $ScriptsDir,$ResultsDir,$LogsDir,$StateDir,$HeartbeatDir | Out-Null

function Log([string]$m) {
  $line = '[' + (Get-Date -Format 's') + '] ' + $m
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $RunnerLog -Value $line
}

function HB([string]$status,[string]$taskId,[string]$msg) {
  $lines = @(
    '# TerraYield Remote Autopilot V8',
    '',
    ('status: ' + $status),
    ('task_id: ' + $taskId),
    ('checked_at: ' + (Get-Date -Format 's')),
    ('bridge_root: ' + $BridgeRoot),
    ('project_root: ' + $ProjectRoot),
    ('runner_log: ' + $RunnerLog),
    ('message: ' + $msg)
  )
  Set-Content -Encoding UTF8 -Path $HeartbeatFile -Value $lines
}

function Stop-StaleGitLocks {
  try {
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'git.exe' -and $_.CommandLine -match [regex]::Escape($BridgeRoot) } | ForEach-Object {
      Log ('STOP_STALE_GIT_PID=' + $_.ProcessId)
      Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
  } catch {}
  Start-Sleep -Milliseconds 500
  Remove-Item (Join-Path $BridgeRoot '.git\index.lock') -Force -ErrorAction SilentlyContinue
}

function GitTimed([string[]]$Args,[int]$TimeoutSeconds = 60) {
  Stop-StaleGitLocks
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
  $outFile = Join-Path $LogsDir ('git-v8-' + $stamp + '.out.log')
  $errFile = Join-Path $LogsDir ('git-v8-' + $stamp + '.err.log')
  try {
    $p = Start-Process -FilePath 'git.exe' -ArgumentList $Args -WorkingDirectory $BridgeRoot -RedirectStandardOutput $outFile -RedirectStandardError $errFile -PassThru -WindowStyle Hidden
    if (-not $p.WaitForExit($TimeoutSeconds * 1000)) {
      Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
      Log ('GIT_TIMEOUT ' + ($Args -join ' '))
      return @{ Code = 124; Out = ''; Err = 'timeout' }
    }
    $o = if (Test-Path $outFile) { Get-Content -Raw -Encoding UTF8 $outFile } else { '' }
    $e = if (Test-Path $errFile) { Get-Content -Raw -Encoding UTF8 $errFile } else { '' }
    Add-Content -Encoding UTF8 -Path $RunnerLog -Value ('GIT ' + ($Args -join ' ') + ' EXIT=' + $p.ExitCode)
    if (-not [string]::IsNullOrWhiteSpace($o)) { Add-Content -Encoding UTF8 -Path $RunnerLog -Value $o }
    if (-not [string]::IsNullOrWhiteSpace($e)) { Add-Content -Encoding UTF8 -Path $RunnerLog -Value $e }
    return @{ Code = [int]$p.ExitCode; Out = $o; Err = $e }
  } catch {
    Log ('GIT_EXCEPTION ' + ($Args -join ' ') + ' :: ' + $_.Exception.Message)
    return @{ Code = 998; Out = ''; Err = $_.Exception.Message }
  }
}

function PullLatest {
  $r1 = GitTimed @('fetch','origin','main') 60
  if ($r1.Code -ne 0) { return $false }
  $r2 = GitTimed @('reset','--hard','origin/main') 60
  return ($r2.Code -eq 0)
}

function PushState([string]$taskId) {
  GitTimed @('add','ai-results','ai-heartbeat','ai-runner-state','ai-runner-logs') 60 | Out-Null
  GitTimed @('commit','-m',('autopilot-v8 state ' + $taskId)) 60 | Out-Null
  GitTimed @('pull','--rebase','origin','main') 90 | Out-Null
  GitTimed @('push','origin','main') 90 | Out-Null
}

function WriteResult([string]$id,[string]$title,[int]$code,[string]$stdout,[string]$stderr,[string]$msg) {
  $result = Join-Path $ResultsDir ((Get-Date -Format 'yyyy-MM-dd_HH-mm-ss') + '-' + $id + '.md')
  $so = if (Test-Path $stdout) { Get-Content -Raw -Encoding UTF8 $stdout } else { '' }
  $se = if (Test-Path $stderr) { Get-Content -Raw -Encoding UTF8 $stderr } else { '' }
  Set-Content -Encoding UTF8 -Path $result -Value @('# TerraYield Autopilot V8 Result','',('task_id: ' + $id),('title: ' + $title),('exit_code: ' + $code),('message: ' + $msg),('time: ' + (Get-Date -Format 's')),'','## Output','```text')
  Add-Content -Encoding UTF8 -Path $result -Value $so
  Add-Content -Encoding UTF8 -Path $result -Value '```'
  Add-Content -Encoding UTF8 -Path $result -Value @('','## Error','```text')
  Add-Content -Encoding UTF8 -Path $result -Value $se
  Add-Content -Encoding UTF8 -Path $result -Value '```'
}

function RunTask($task) {
  $id = [string]$task.id
  $title = if ($task.PSObject.Properties.Name -contains 'title') { [string]$task.title } else { $id }
  $sp = if ($task.PSObject.Properties.Name -contains 'script_path') { [string]$task.script_path } else { '' }
  $timeout = if ($task.PSObject.Properties.Name -contains 'timeout_seconds') { [int]$task.timeout_seconds } else { 3600 }
  $stdout = Join-Path $LogsDir ($id + '.stdout.log')
  $stderr = Join-Path $LogsDir ($id + '.stderr.log')
  if ([string]::IsNullOrWhiteSpace($sp)) {
    Set-Content -Encoding UTF8 -Path $stderr -Value 'missing script_path; V8 ignores command/action-only tasks'
    WriteResult $id $title 2 $stdout $stderr 'rejected_missing_script_path'
    Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $id
    HB 'rejected' $id 'missing script_path'
    PushState $id
    return
  }
  if ($sp -match '\.\.') { throw ('unsafe script_path: ' + $sp) }
  $script = [IO.Path]::GetFullPath((Join-Path $ScriptsDir $sp))
  $allowed = [IO.Path]::GetFullPath($ScriptsDir)
  if (-not $script.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw ('script outside ai-task-scripts: ' + $script) }
  if (-not (Test-Path $script)) { throw ('script missing: ' + $script) }
  HB 'running' $id $title
  Log ('START_TASK ' + $id + ' SCRIPT=' + $script)
  $code = 999
  try {
    $p = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$script) -WorkingDirectory $ProjectRoot -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    if (-not $p.WaitForExit($timeout * 1000)) {
      Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
      $code = 124
    } else {
      if ($null -eq $p.ExitCode) { $code = 0 } else { $code = [int]$p.ExitCode }
    }
  } catch {
    Add-Content -Encoding UTF8 -Path $stderr -Value $_.Exception.Message
    $code = 998
  }
  WriteResult $id $title $code $stdout $stderr 'completed_by_v8'
  Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $id
  HB 'finished' $id ('exit=' + $code)
  Log ('FINISH_TASK ' + $id + ' EXIT=' + $code)
  PushState $id
}

Log 'Autopilot V8 started'
HB 'polling' '' 'started'
PushState 'v8-started'
while ($true) {
  try {
    HB 'polling' '' 'pulling'
    $pulled = PullLatest
    if (-not $pulled) {
      HB 'error' '' 'pull failed; will retry'
      Start-Sleep -Seconds $PollSeconds
      continue
    }
    if (-not (Test-Path $TaskFile)) {
      HB 'polling' '' 'no task file'
      PushState 'no-task-file'
      Start-Sleep -Seconds $PollSeconds
      continue
    }
    $task = Get-Content -Raw -Encoding UTF8 $TaskFile | ConvertFrom-Json
    $id = [string]$task.id
    $last = if (Test-Path $LastTaskFile) { (Get-Content -Raw -Encoding UTF8 $LastTaskFile).Trim() } else { '' }
    if ($id -and $id -ne $last) { RunTask $task } else { HB 'polling' $id 'waiting'; PushState 'waiting' }
  } catch {
    Log ('LOOP_ERROR ' + $_.Exception.Message)
    HB 'error' '' $_.Exception.Message
    PushState 'loop-error'
  }
  Start-Sleep -Seconds $PollSeconds
}

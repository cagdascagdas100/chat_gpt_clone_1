$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$TaskFile = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$ScriptsDir = Join-Path $BridgeRoot 'ai-task-scripts'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$LogsDir = Join-Path $BridgeRoot 'ai-runner-logs'
$StateDir = Join-Path $BridgeRoot 'ai-runner-state'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatFile = Join-Path $HeartbeatDir 'remote-autopilot-v81.md'
$LastTaskFile = Join-Path $StateDir 'remote-autopilot-v81.last-task-id'
$RunnerLog = Join-Path $LogsDir ('remote-autopilot-v81-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
$PollSeconds = 20
New-Item -ItemType Directory -Force -Path $ScriptsDir,$ResultsDir,$LogsDir,$StateDir,$HeartbeatDir | Out-Null

function Log {
  param([string]$Message)
  $line = '[' + (Get-Date -Format 's') + '] ' + $Message
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $RunnerLog -Value $line
}

function Write-HB {
  param([string]$Status,[string]$TaskId,[string]$Message)
  $lines = @(
    '# TerraYield Remote Autopilot V8.1',
    '',
    ('status: ' + $Status),
    ('task_id: ' + $TaskId),
    ('checked_at: ' + (Get-Date -Format 's')),
    ('bridge_root: ' + $BridgeRoot),
    ('project_root: ' + $ProjectRoot),
    ('runner_log: ' + $RunnerLog),
    ('message: ' + $Message)
  )
  Set-Content -Encoding UTF8 -Path $HeartbeatFile -Value $lines
}

function Clear-Git-Locks {
  try {
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'git.exe' -and $_.CommandLine -match [regex]::Escape($BridgeRoot) } | ForEach-Object {
      Log ('STOP_STALE_GIT_PID=' + $_.ProcessId)
      Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
  } catch {}
  Start-Sleep -Milliseconds 300
  Remove-Item (Join-Path $BridgeRoot '.git\index.lock') -Force -ErrorAction SilentlyContinue
}

function Invoke-GitTimed {
  param(
    [Parameter(Mandatory=$true)][string[]]$GitArgs,
    [int]$TimeoutSeconds = 60
  )
  Clear-Git-Locks
  if ($null -eq $GitArgs -or $GitArgs.Count -lt 1) {
    Log 'GIT_ARGS_EMPTY'
    return @{ Code = 997; Out = ''; Err = 'empty args' }
  }
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
  $outFile = Join-Path $LogsDir ('git-v81-' + $stamp + '.out.log')
  $errFile = Join-Path $LogsDir ('git-v81-' + $stamp + '.err.log')
  $argText = ($GitArgs -join ' ')
  try {
    Log ('GIT_START ' + $argText)
    $p = Start-Process -FilePath 'git.exe' -ArgumentList $GitArgs -WorkingDirectory $BridgeRoot -RedirectStandardOutput $outFile -RedirectStandardError $errFile -PassThru
    if (-not $p.WaitForExit($TimeoutSeconds * 1000)) {
      Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
      Log ('GIT_TIMEOUT ' + $argText)
      return @{ Code = 124; Out = ''; Err = 'timeout' }
    }
    $o = if (Test-Path $outFile) { Get-Content -Raw -Encoding UTF8 $outFile } else { '' }
    $e = if (Test-Path $errFile) { Get-Content -Raw -Encoding UTF8 $errFile } else { '' }
    Log ('GIT_EXIT ' + $p.ExitCode + ' ' + $argText)
    if (-not [string]::IsNullOrWhiteSpace($o)) { Add-Content -Encoding UTF8 -Path $RunnerLog -Value $o }
    if (-not [string]::IsNullOrWhiteSpace($e)) { Add-Content -Encoding UTF8 -Path $RunnerLog -Value $e }
    return @{ Code = [int]$p.ExitCode; Out = $o; Err = $e }
  } catch {
    Log ('GIT_EXCEPTION ' + $argText + ' :: ' + $_.Exception.Message)
    return @{ Code = 998; Out = ''; Err = $_.Exception.Message }
  }
}

function Pull-Latest {
  $r1 = Invoke-GitTimed -GitArgs @('fetch','origin','main') -TimeoutSeconds 90
  if ($r1.Code -ne 0) { return $false }
  $r2 = Invoke-GitTimed -GitArgs @('reset','--hard','origin/main') -TimeoutSeconds 90
  return ($r2.Code -eq 0)
}

function Push-State {
  param([string]$TaskId)
  Invoke-GitTimed -GitArgs @('add','ai-results','ai-heartbeat','ai-runner-state','ai-runner-logs') -TimeoutSeconds 90 | Out-Null
  Invoke-GitTimed -GitArgs @('commit','-m',('autopilot-v81 state ' + $TaskId)) -TimeoutSeconds 90 | Out-Null
  Invoke-GitTimed -GitArgs @('pull','--rebase','origin','main') -TimeoutSeconds 120 | Out-Null
  Invoke-GitTimed -GitArgs @('push','origin','main') -TimeoutSeconds 120 | Out-Null
}

function Write-Result {
  param([string]$Id,[string]$Title,[int]$Code,[string]$Stdout,[string]$Stderr,[string]$Message)
  $result = Join-Path $ResultsDir ((Get-Date -Format 'yyyy-MM-dd_HH-mm-ss') + '-' + $Id + '.md')
  $so = if (Test-Path $Stdout) { Get-Content -Raw -Encoding UTF8 $Stdout } else { '' }
  $se = if (Test-Path $Stderr) { Get-Content -Raw -Encoding UTF8 $Stderr } else { '' }
  Set-Content -Encoding UTF8 -Path $result -Value @('# TerraYield Autopilot V8.1 Result','',('task_id: ' + $Id),('title: ' + $Title),('exit_code: ' + $Code),('message: ' + $Message),('time: ' + (Get-Date -Format 's')),'','## Output','```text')
  Add-Content -Encoding UTF8 -Path $result -Value $so
  Add-Content -Encoding UTF8 -Path $result -Value '```'
  Add-Content -Encoding UTF8 -Path $result -Value @('','## Error','```text')
  Add-Content -Encoding UTF8 -Path $result -Value $se
  Add-Content -Encoding UTF8 -Path $result -Value '```'
}

function Run-Task {
  param($Task)
  $id = [string]$Task.id
  $title = if ($Task.PSObject.Properties.Name -contains 'title') { [string]$Task.title } else { $id }
  $sp = if ($Task.PSObject.Properties.Name -contains 'script_path') { [string]$Task.script_path } else { '' }
  $timeout = if ($Task.PSObject.Properties.Name -contains 'timeout_seconds') { [int]$Task.timeout_seconds } else { 3600 }
  $stdout = Join-Path $LogsDir ($id + '.stdout.log')
  $stderr = Join-Path $LogsDir ($id + '.stderr.log')
  if ([string]::IsNullOrWhiteSpace($sp)) {
    Set-Content -Encoding UTF8 -Path $stderr -Value 'missing script_path; V8.1 ignores command/action-only tasks'
    Write-Result -Id $id -Title $title -Code 2 -Stdout $stdout -Stderr $stderr -Message 'rejected_missing_script_path'
    Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $id
    Write-HB -Status 'rejected' -TaskId $id -Message 'missing script_path'
    Push-State -TaskId $id
    return
  }
  if ($sp -match '\.\.') { throw ('unsafe script_path: ' + $sp) }
  $script = [IO.Path]::GetFullPath((Join-Path $ScriptsDir $sp))
  $allowed = [IO.Path]::GetFullPath($ScriptsDir)
  if (-not $script.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw ('script outside ai-task-scripts: ' + $script) }
  if (-not (Test-Path $script)) { throw ('script missing: ' + $script) }
  Write-HB -Status 'running' -TaskId $id -Message $title
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
  Write-Result -Id $id -Title $title -Code $code -Stdout $stdout -Stderr $stderr -Message 'completed_by_v81'
  Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $id
  Write-HB -Status 'finished' -TaskId $id -Message ('exit=' + $code)
  Log ('FINISH_TASK ' + $id + ' EXIT=' + $code)
  Push-State -TaskId $id
}

Log 'Autopilot V8.1 started'
Write-HB -Status 'polling' -TaskId '' -Message 'started'
Push-State -TaskId 'v81-started'
while ($true) {
  try {
    Write-HB -Status 'polling' -TaskId '' -Message 'pulling'
    $pulled = Pull-Latest
    if (-not $pulled) {
      Write-HB -Status 'error' -TaskId '' -Message 'pull failed; will retry'
      Push-State -TaskId 'pull-failed'
      Start-Sleep -Seconds $PollSeconds
      continue
    }
    if (-not (Test-Path $TaskFile)) {
      Write-HB -Status 'polling' -TaskId '' -Message 'no task file'
      Push-State -TaskId 'no-task-file'
      Start-Sleep -Seconds $PollSeconds
      continue
    }
    $task = Get-Content -Raw -Encoding UTF8 $TaskFile | ConvertFrom-Json
    $id = [string]$task.id
    $last = if (Test-Path $LastTaskFile) { (Get-Content -Raw -Encoding UTF8 $LastTaskFile).Trim() } else { '' }
    if ($id -and $id -ne $last) { Run-Task -Task $task } else { Write-HB -Status 'polling' -TaskId $id -Message 'waiting'; Push-State -TaskId 'waiting' }
  } catch {
    Log ('LOOP_ERROR ' + $_.Exception.Message)
    Write-HB -Status 'error' -TaskId '' -Message $_.Exception.Message
    Push-State -TaskId 'loop-error'
  }
  Start-Sleep -Seconds $PollSeconds
}

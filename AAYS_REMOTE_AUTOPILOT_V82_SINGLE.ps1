$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$TaskFile = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$ScriptsDir = Join-Path $BridgeRoot 'ai-task-scripts'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$LogsDir = Join-Path $BridgeRoot 'ai-runner-logs'
$StateDir = Join-Path $BridgeRoot 'ai-runner-state'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatFile = Join-Path $HeartbeatDir 'remote-autopilot-v82.md'
$LastTaskFile = Join-Path $StateDir 'remote-autopilot-v82.last-task-id'
$RunnerLog = Join-Path $LogsDir ('remote-autopilot-v82-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
$PollSeconds = 25
New-Item -ItemType Directory -Force -Path $ScriptsDir,$ResultsDir,$LogsDir,$StateDir,$HeartbeatDir | Out-Null
Set-Content -Encoding UTF8 -Path (Join-Path $StateDir '.gitkeep') -Value ''

function Log([string]$Message) {
  $line = '[' + (Get-Date -Format 's') + '] ' + $Message
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $RunnerLog -Value $line
}

function Write-HB([string]$Status,[string]$TaskId,[string]$Message) {
  Set-Content -Encoding UTF8 -Path $HeartbeatFile -Value @(
    '# TerraYield Remote Autopilot V8.2','',
    ('status: ' + $Status),
    ('task_id: ' + $TaskId),
    ('checked_at: ' + (Get-Date -Format 's')),
    ('bridge_root: ' + $BridgeRoot),
    ('project_root: ' + $ProjectRoot),
    ('runner_log: ' + $RunnerLog),
    ('message: ' + $Message)
  )
}

function Clear-GitLocks {
  Remove-Item (Join-Path $BridgeRoot '.git\index.lock') -Force -ErrorAction SilentlyContinue
}

function GitRun([string[]]$Args) {
  Clear-GitLocks
  Push-Location $BridgeRoot
  try {
    $argText = $Args -join ' '
    Log ('GIT_START ' + $argText)
    $output = (& git @Args 2>&1 | Out-String)
    $code = $LASTEXITCODE
    Log ('GIT_EXIT ' + $code + ' ' + $argText)
    if (-not [string]::IsNullOrWhiteSpace($output)) { Add-Content -Encoding UTF8 -Path $RunnerLog -Value $output }
    return @{ Code = [int]$code; Out = $output }
  } catch {
    Log ('GIT_EXCEPTION ' + ($Args -join ' ') + ' :: ' + $_.Exception.Message)
    return @{ Code = 998; Out = $_.Exception.Message }
  } finally {
    Pop-Location
  }
}

function Ensure-MainBranch {
  $b = GitRun @('branch','--show-current')
  if (($b.Out.Trim()) -ne 'main') {
    GitRun @('checkout','-B','main','origin/main') | Out-Null
  }
}

function Pull-Latest {
  Ensure-MainBranch
  $r1 = GitRun @('fetch','origin','main')
  if ($r1.Code -ne 0) { return $false }
  Ensure-MainBranch
  $r2 = GitRun @('reset','--hard','origin/main')
  return ($r2.Code -eq 0)
}

function Push-State([string]$TaskId) {
  Ensure-MainBranch
  New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
  Set-Content -Encoding UTF8 -Path (Join-Path $StateDir '.gitkeep') -Value ''
  GitRun @('add','--','ai-results','ai-heartbeat','ai-runner-logs','ai-runner-state') | Out-Null
  GitRun @('commit','-m',('autopilot-v82 state ' + $TaskId)) | Out-Null
  for ($i = 1; $i -le 5; $i++) {
    Ensure-MainBranch
    GitRun @('pull','--rebase','origin','main') | Out-Null
    $push = GitRun @('push','origin','main')
    if ($push.Code -eq 0) { Log ('PUSH_OK attempt=' + $i); return }
    Log ('PUSH_RETRY attempt=' + $i)
    Start-Sleep -Seconds 3
  }
}

function Write-Result([string]$Id,[string]$Title,[int]$Code,[string]$Stdout,[string]$Stderr,[string]$Message) {
  $result = Join-Path $ResultsDir ((Get-Date -Format 'yyyy-MM-dd_HH-mm-ss') + '-' + $Id + '.md')
  $so = if (Test-Path $Stdout) { Get-Content -Raw -Encoding UTF8 $Stdout } else { '' }
  $se = if (Test-Path $Stderr) { Get-Content -Raw -Encoding UTF8 $Stderr } else { '' }
  Set-Content -Encoding UTF8 -Path $result -Value @('# TerraYield Autopilot V8.2 Result','',('task_id: ' + $Id),('title: ' + $Title),('exit_code: ' + $Code),('message: ' + $Message),('time: ' + (Get-Date -Format 's')),'','## Output','```text')
  Add-Content -Encoding UTF8 -Path $result -Value $so
  Add-Content -Encoding UTF8 -Path $result -Value '```'
  Add-Content -Encoding UTF8 -Path $result -Value @('','## Error','```text')
  Add-Content -Encoding UTF8 -Path $result -Value $se
  Add-Content -Encoding UTF8 -Path $result -Value '```'
}

function Run-Task($Task) {
  $id = [string]$Task.id
  $title = if ($Task.PSObject.Properties.Name -contains 'title') { [string]$Task.title } else { $id }
  $sp = if ($Task.PSObject.Properties.Name -contains 'script_path') { [string]$Task.script_path } else { '' }
  $timeout = if ($Task.PSObject.Properties.Name -contains 'timeout_seconds') { [int]$Task.timeout_seconds } else { 3600 }
  $stdout = Join-Path $LogsDir ($id + '.stdout.log')
  $stderr = Join-Path $LogsDir ($id + '.stderr.log')
  if ([string]::IsNullOrWhiteSpace($sp)) {
    Set-Content -Encoding UTF8 -Path $stderr -Value 'missing script_path; V8.2 ignores command/action-only tasks'
    Write-Result $id $title 2 $stdout $stderr 'rejected_missing_script_path'
    Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $id
    Write-HB 'rejected' $id 'missing script_path'
    Push-State $id
    return
  }
  if ($sp -match '\.\.') { throw ('unsafe script_path: ' + $sp) }
  $script = [IO.Path]::GetFullPath((Join-Path $ScriptsDir $sp))
  $allowed = [IO.Path]::GetFullPath($ScriptsDir)
  if (-not $script.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)) { throw ('script outside ai-task-scripts: ' + $script) }
  if (-not (Test-Path $script)) { throw ('script missing: ' + $script) }
  Write-HB 'running' $id $title
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
  Write-Result $id $title $code $stdout $stderr 'completed_by_v82'
  Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $id
  Write-HB 'finished' $id ('exit=' + $code)
  Log ('FINISH_TASK ' + $id + ' EXIT=' + $code)
  Push-State $id
}

Log 'Autopilot V8.2 started'
Write-HB 'polling' '' 'started'
Push-State 'v82-started'
while ($true) {
  try {
    Write-HB 'polling' '' 'pulling'
    if (-not (Pull-Latest)) {
      Write-HB 'error' '' 'pull failed; will retry'
      Push-State 'pull-failed'
      Start-Sleep -Seconds $PollSeconds
      continue
    }
    if (-not (Test-Path $TaskFile)) {
      Write-HB 'polling' '' 'no task file'
      Push-State 'no-task-file'
      Start-Sleep -Seconds $PollSeconds
      continue
    }
    $task = Get-Content -Raw -Encoding UTF8 $TaskFile | ConvertFrom-Json
    $id = [string]$task.id
    $last = if (Test-Path $LastTaskFile) { (Get-Content -Raw -Encoding UTF8 $LastTaskFile).Trim() } else { '' }
    if ($id -and $id -ne $last) { Run-Task $task } else { Write-HB 'polling' $id 'waiting'; Push-State 'waiting' }
  } catch {
    Log ('LOOP_ERROR ' + $_.Exception.Message)
    Write-HB 'error' '' $_.Exception.Message
    Push-State 'loop-error'
  }
  Start-Sleep -Seconds $PollSeconds
}

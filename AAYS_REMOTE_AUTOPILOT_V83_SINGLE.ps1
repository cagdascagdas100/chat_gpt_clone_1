$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
$ProjectRoot = 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$TaskFile = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$ScriptsDir = Join-Path $BridgeRoot 'ai-task-scripts'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$LogsDir = Join-Path $BridgeRoot 'ai-runner-logs'
$StateDir = Join-Path $BridgeRoot 'ai-runner-state'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$HeartbeatFile = Join-Path $HeartbeatDir 'remote-autopilot-v83.md'
$LastTaskFile = Join-Path $StateDir 'remote-autopilot-v83.last-task-id'
$RunnerLog = Join-Path $LogsDir ('remote-autopilot-v83-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
$PollSeconds = 25
New-Item -ItemType Directory -Force -Path $ScriptsDir,$ResultsDir,$LogsDir,$StateDir,$HeartbeatDir | Out-Null
Set-Content -Encoding UTF8 -Path (Join-Path $StateDir '.gitkeep') -Value ''

function Log([string]$Message) {
  $line = '[' + (Get-Date -Format 's') + '] ' + $Message
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $RunnerLog -Value $line
}
function HB([string]$Status,[string]$TaskId,[string]$Message) {
  Set-Content -Encoding UTF8 -Path $HeartbeatFile -Value @('# TerraYield Remote Autopilot V8.3','',('status: ' + $Status),('task_id: ' + $TaskId),('checked_at: ' + (Get-Date -Format 's')),('bridge_root: ' + $BridgeRoot),('project_root: ' + $ProjectRoot),('runner_log: ' + $RunnerLog),('message: ' + $Message))
}
function GitRun([string[]]$Args) {
  Push-Location $BridgeRoot
  try {
    Remove-Item (Join-Path $BridgeRoot '.git\index.lock') -Force -ErrorAction SilentlyContinue
    $txt = $Args -join ' '
    Log ('GIT_START ' + $txt)
    $out = (& git @Args 2>&1 | Out-String)
    $code = $LASTEXITCODE
    Log ('GIT_EXIT ' + $code + ' ' + $txt)
    if (-not [string]::IsNullOrWhiteSpace($out)) { Add-Content -Encoding UTF8 -Path $RunnerLog -Value $out }
    return @{ Code = [int]$code; Out = $out }
  } catch { Log ('GIT_EXCEPTION ' + ($Args -join ' ') + ' :: ' + $_.Exception.Message); return @{ Code = 998; Out = $_.Exception.Message } }
  finally { Pop-Location }
}
function EnsureMainNoReset {
  $b = GitRun @('branch','--show-current')
  if (($b.Out.Trim()) -ne 'main') { GitRun @('checkout','-B','main') | Out-Null }
}
function CommitLocalState([string]$Label) {
  EnsureMainNoReset
  New-Item -ItemType Directory -Force -Path $StateDir | Out-Null
  Set-Content -Encoding UTF8 -Path (Join-Path $StateDir '.gitkeep') -Value ''
  GitRun @('add','--','ai-results','ai-heartbeat','ai-runner-logs','ai-runner-state') | Out-Null
  $s = GitRun @('status','--porcelain')
  if ([string]::IsNullOrWhiteSpace($s.Out)) { Log ('NO_LOCAL_STATE_TO_COMMIT ' + $Label); return }
  GitRun @('commit','-m',('autopilot-v83 state ' + $Label)) | Out-Null
}
function PushLocalState([string]$Label) {
  CommitLocalState $Label
  for ($i=1; $i -le 8; $i++) {
    EnsureMainNoReset
    GitRun @('fetch','origin','main') | Out-Null
    $rb = GitRun @('rebase','origin/main')
    if ($rb.Code -ne 0) { GitRun @('rebase','--abort') | Out-Null; GitRun @('pull','--rebase','--autostash','origin','main') | Out-Null }
    $p = GitRun @('push','origin','main')
    if ($p.Code -eq 0) { Log ('PUSH_OK attempt=' + $i); return $true }
    Start-Sleep -Seconds 4
  }
  Log ('PUSH_FAILED ' + $Label)
  return $false
}
function PullLatestAfterPush {
  PushLocalState 'pre-pull' | Out-Null
  EnsureMainNoReset
  GitRun @('fetch','origin','main') | Out-Null
  $r = GitRun @('pull','--rebase','--autostash','origin','main')
  return ($r.Code -eq 0)
}
function WriteResult([string]$Id,[string]$Title,[int]$Code,[string]$Stdout,[string]$Stderr,[string]$Message) {
  $result = Join-Path $ResultsDir ((Get-Date -Format 'yyyy-MM-dd_HH-mm-ss') + '-' + $Id + '.md')
  $so = if (Test-Path $Stdout) { Get-Content -Raw -Encoding UTF8 $Stdout } else { '' }
  $se = if (Test-Path $Stderr) { Get-Content -Raw -Encoding UTF8 $Stderr } else { '' }
  Set-Content -Encoding UTF8 -Path $result -Value @('# TerraYield Autopilot V8.3 Result','',('task_id: ' + $Id),('title: ' + $Title),('exit_code: ' + $Code),('message: ' + $Message),('time: ' + (Get-Date -Format 's')),'','## Output','```text')
  Add-Content -Encoding UTF8 -Path $result -Value $so
  Add-Content -Encoding UTF8 -Path $result -Value '```'
  Add-Content -Encoding UTF8 -Path $result -Value @('','## Error','```text')
  Add-Content -Encoding UTF8 -Path $result -Value $se
  Add-Content -Encoding UTF8 -Path $result -Value '```'
}
function RunTask($Task) {
  $id = [string]$Task.id
  $title = if ($Task.PSObject.Properties.Name -contains 'title') { [string]$Task.title } else { $id }
  $sp = if ($Task.PSObject.Properties.Name -contains 'script_path') { [string]$Task.script_path } else { '' }
  $timeout = if ($Task.PSObject.Properties.Name -contains 'timeout_seconds') { [int]$Task.timeout_seconds } else { 3600 }
  $stdout = Join-Path $LogsDir ($id + '.stdout.log')
  $stderr = Join-Path $LogsDir ($id + '.stderr.log')
  if ([string]::IsNullOrWhiteSpace($sp)) { Set-Content -Encoding UTF8 -Path $stderr -Value 'missing script_path'; WriteResult $id $title 2 $stdout $stderr 'rejected_missing_script_path'; Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $id; HB 'rejected' $id 'missing script_path'; PushLocalState $id | Out-Null; return }
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
    if (-not $p.WaitForExit($timeout * 1000)) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; $code = 124 } else { if ($null -eq $p.ExitCode) { $code = 0 } else { $code = [int]$p.ExitCode } }
  } catch { Add-Content -Encoding UTF8 -Path $stderr -Value $_.Exception.Message; $code = 998 }
  WriteResult $id $title $code $stdout $stderr 'completed_by_v83'
  Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $id
  HB 'finished' $id ('exit=' + $code)
  Log ('FINISH_TASK ' + $id + ' EXIT=' + $code)
  PushLocalState $id | Out-Null
}
Log 'Autopilot V8.3 started'
HB 'polling' '' 'started'
PushLocalState 'v83-started' | Out-Null
while ($true) {
  try {
    HB 'polling' '' 'pulling'
    if (-not (PullLatestAfterPush)) { HB 'error' '' 'pull failed; will retry'; PushLocalState 'pull-failed' | Out-Null; Start-Sleep -Seconds $PollSeconds; continue }
    if (-not (Test-Path $TaskFile)) { HB 'polling' '' 'no task file'; PushLocalState 'no-task-file' | Out-Null; Start-Sleep -Seconds $PollSeconds; continue }
    $task = Get-Content -Raw -Encoding UTF8 $TaskFile | ConvertFrom-Json
    $id = [string]$task.id
    $last = if (Test-Path $LastTaskFile) { (Get-Content -Raw -Encoding UTF8 $LastTaskFile).Trim() } else { '' }
    if ($id -and $id -ne $last) { RunTask $task } else { HB 'polling' $id 'waiting'; PushLocalState 'waiting' | Out-Null }
  } catch { Log ('LOOP_ERROR ' + $_.Exception.Message); HB 'error' '' $_.Exception.Message; PushLocalState 'loop-error' | Out-Null }
  Start-Sleep -Seconds $PollSeconds
}

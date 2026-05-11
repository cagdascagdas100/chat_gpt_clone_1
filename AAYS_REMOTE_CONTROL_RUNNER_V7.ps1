$ErrorActionPreference = 'Continue'

$RepoUrl = 'https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { 'C:\AAYS_GITHUB_BRIDGE_CLEAN' }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { 'C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence' }
$PollSeconds = if ($env:AAYS_RUNNER_POLL_SECONDS) { [int]$env:AAYS_RUNNER_POLL_SECONDS } else { 20 }
$TaskFile = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$StateFile = Join-Path $BridgeRoot 'ai-runner-state\remote-control-v7.last-task-id'
$HeartbeatFile = Join-Path $BridgeRoot 'ai-heartbeat\remote-control-v7.md'
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$LogsDir = Join-Path $BridgeRoot 'ai-runner-logs'
$ScriptsDir = Join-Path $BridgeRoot 'ai-task-scripts'
$TmpDir = Join-Path $BridgeRoot 'ai-tmp'
$RunnerLog = Join-Path $LogsDir ('remote-control-v7-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
$MutexName = 'Global\AAYS_REMOTE_CONTROL_V7_SINGLE_INSTANCE'

function Ensure-Dirs {
  New-Item -ItemType Directory -Force -Path $BridgeRoot,$ResultsDir,$LogsDir,$ScriptsDir,$TmpDir,(Split-Path $StateFile),(Split-Path $HeartbeatFile) | Out-Null
}

function Log([string]$Text) {
  Ensure-Dirs
  $line = '[' + (Get-Date -Format 's') + '] ' + $Text
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $RunnerLog -Value $line
}

function Write-Atomic([string]$Path,[string]$Text) {
  try {
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $tmp = Join-Path $dir ('.' + [IO.Path]::GetFileName($Path) + '.' + [guid]::NewGuid().ToString('N') + '.tmp')
    [IO.File]::WriteAllText($tmp,$Text,[Text.UTF8Encoding]::new($true))
    Move-Item -Force $tmp $Path
    return $true
  } catch {
    Log ('WRITE_ATOMIC_ERROR path=' + $Path + ' error=' + $_.Exception.Message)
    return $false
  }
}

function Heartbeat([string]$Status,[string]$TaskId,[string]$Message) {
  $txt = @(
    '# AAYS Remote Control Runner V7',
    '',
    ('time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
    ('status: ' + $Status),
    ('task_id: ' + $TaskId),
    ('bridge_root: ' + $BridgeRoot),
    ('project_root: ' + $ProjectRoot),
    ('task_file: ' + $TaskFile),
    ('state_file: ' + $StateFile),
    ('runner_log: ' + $RunnerLog),
    ('message: ' + $Message),
    'mode: scheduled-self-healing-single-instance',
    'supports: script_path, action=health_check, action=status_check'
  ) -join "`n"
  Write-Atomic $HeartbeatFile $txt | Out-Null
}

function GitSafe([string[]]$ArgsList) {
  try {
    Push-Location $BridgeRoot
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $out = & git @ArgsList 2>&1 | Out-String
    $code = $LASTEXITCODE
    $ErrorActionPreference = $old
    if ($out) { Add-Content -Encoding UTF8 -Path $RunnerLog -Value $out }
    return [pscustomobject]@{ Code=$code; Output=$out }
  } catch {
    return [pscustomobject]@{ Code=999; Output=('GIT_EXCEPTION=' + $_.Exception.Message) }
  } finally {
    try { Pop-Location } catch {}
  }
}

function Ensure-Repo {
  Ensure-Dirs
  if (-not (Test-Path (Join-Path $BridgeRoot '.git'))) {
    $parent = Split-Path -Parent $BridgeRoot
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    if (Test-Path $BridgeRoot) {
      $items = Get-ChildItem -Path $BridgeRoot -Force -ErrorAction SilentlyContinue
      if ($items.Count -gt 0) { Log 'BridgeRoot exists but is not git repo; leaving contents in place.' }
    }
    if (-not (Test-Path (Join-Path $BridgeRoot '.git'))) {
      $clone = & git clone $RepoUrl $BridgeRoot 2>&1 | Out-String
      Add-Content -Encoding UTF8 -Path $RunnerLog -Value $clone
    }
  }
}

function Pull-Latest {
  Ensure-Repo
  GitSafe @('config','--local','pull.rebase','true') | Out-Null
  GitSafe @('fetch','origin','main','--prune') | Out-Null
  $pull = GitSafe @('pull','--rebase','origin','main')
  if ($pull.Output -match 'CONFLICT|fatal:|error:') {
    Log 'Pull rebase failed; resetting bridge repo to origin/main after preserving generated dirs.'
    GitSafe @('rebase','--abort') | Out-Null
    GitSafe @('reset','--hard','origin/main') | Out-Null
  }
}

function Push-State([string]$TaskId) {
  GitSafe @('add','ai-results','ai-heartbeat','ai-runner-state','ai-runner-logs') | Out-Null
  $status = GitSafe @('status','--short')
  if ([string]::IsNullOrWhiteSpace($status.Output)) { return }
  GitSafe @('commit','-m',('remote-control-v7 result ' + $TaskId)) | Out-Null
  GitSafe @('fetch','origin','main','--prune') | Out-Null
  $rb = GitSafe @('pull','--rebase','origin','main')
  if ($rb.Output -match 'CONFLICT|fatal:|error:') {
    GitSafe @('rebase','--abort') | Out-Null
    GitSafe @('reset','--hard','origin/main') | Out-Null
    GitSafe @('add','ai-results','ai-heartbeat','ai-runner-state','ai-runner-logs') | Out-Null
    GitSafe @('commit','-m',('remote-control-v7 result ' + $TaskId + ' recovery')) | Out-Null
  }
  GitSafe @('push','origin','main') | Out-Null
}

function Is-SafeScriptPath([string]$ScriptPath) {
  if ([string]::IsNullOrWhiteSpace($ScriptPath)) { return $false }
  if ($ScriptPath -match '\.\.') { return $false }
  $candidate = $ScriptPath
  if (-not [IO.Path]::IsPathRooted($candidate)) { $candidate = Join-Path $ScriptsDir $candidate }
  $full = [IO.Path]::GetFullPath($candidate)
  $allowed = [IO.Path]::GetFullPath($ScriptsDir)
  return $full.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)
}

function Resolve-Script([string]$ScriptPath) {
  $candidate = $ScriptPath
  if (-not [IO.Path]::IsPathRooted($candidate)) { $candidate = Join-Path $ScriptsDir $candidate }
  return [IO.Path]::GetFullPath($candidate)
}

function Write-Result([string]$TaskId,[string]$Title,[int]$ExitCode,[string]$Output,[string]$ErrorText,[string]$Message) {
  $safeId = $TaskId -replace '[^a-zA-Z0-9_-]+','-'
  $stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
  $path = Join-Path $ResultsDir ($stamp + '-' + $safeId + '.md')
  $body = @"
# AAYS Remote Control Runner V7 Result

## Task
$Title

## Task ID
$TaskId

## Time
$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## Exit Code
$ExitCode

## Message
$Message

## Output
````text
$Output
````

## Error
````text
$ErrorText
````
"@
  Write-Atomic $path $body | Out-Null
}

function Run-Task($Task) {
  $taskId = [string]$Task.id
  $title = if ($Task.PSObject.Properties.Name -contains 'title') { [string]$Task.title } else { $taskId }
  $timeout = if ($Task.PSObject.Properties.Name -contains 'timeout_seconds') { [int]$Task.timeout_seconds } else { 600 }
  if ($timeout -lt 30) { $timeout = 30 }
  if ($timeout -gt 14400) { $timeout = 14400 }
  $action = if ($Task.PSObject.Properties.Name -contains 'action') { [string]$Task.action } else { '' }
  $scriptPathName = if ($Task.PSObject.Properties.Name -contains 'script_path') { [string]$Task.script_path } else { '' }

  Heartbeat 'running' $taskId $title
  Log ('START task=' + $taskId + ' title=' + $title)

  if ([string]::IsNullOrWhiteSpace($scriptPathName) -and $action -eq 'health_check') {
    $out = "AAYS_REMOTE_CONTROL_V7_HEALTH=OK`nTIME=$(Get-Date -Format s)`nBRIDGE_ROOT=$BridgeRoot"
    Write-Result $taskId $title 0 $out '' 'health_check_completed'
    Write-Atomic $StateFile $taskId | Out-Null
    Heartbeat 'finished' $taskId 'exit=0 health_check_completed'
    Push-State $taskId
    return
  }

  if ([string]::IsNullOrWhiteSpace($scriptPathName) -and $action -eq 'status_check') {
    $gitStatus = GitSafe @('status','--short')
    $out = "AAYS_REMOTE_CONTROL_V7_STATUS=OK`n" + $gitStatus.Output
    Write-Result $taskId $title 0 $out '' 'status_check_completed'
    Write-Atomic $StateFile $taskId | Out-Null
    Heartbeat 'finished' $taskId 'exit=0 status_check_completed'
    Push-State $taskId
    return
  }

  if (-not (Is-SafeScriptPath $scriptPathName)) {
    Write-Result $taskId $title 9003 '' ('Unsafe or missing script_path: ' + $scriptPathName) 'rejected'
    Write-Atomic $StateFile $taskId | Out-Null
    Heartbeat 'rejected' $taskId 'unsafe_or_missing_script_path'
    Push-State $taskId
    return
  }

  $script = Resolve-Script $scriptPathName
  if (-not (Test-Path $script)) {
    Write-Result $taskId $title 9004 '' ('Script not found: ' + $script) 'script_missing'
    Write-Atomic $StateFile $taskId | Out-Null
    Heartbeat 'rejected' $taskId 'script_missing'
    Push-State $taskId
    return
  }

  $stdoutFile = Join-Path $LogsDir ($taskId + '.stdout.log')
  $stderrFile = Join-Path $LogsDir ($taskId + '.stderr.log')
  $exitCode = 999
  try {
    if (-not (Test-Path $ProjectRoot)) { New-Item -ItemType Directory -Force -Path $ProjectRoot | Out-Null }
    $p = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$script) -WorkingDirectory $ProjectRoot -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile -PassThru -WindowStyle Hidden
    if (-not $p.WaitForExit($timeout * 1000)) {
      try { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue } catch {}
      $exitCode = 124
    } else { $exitCode = $p.ExitCode }
  } catch {
    Add-Content -Encoding UTF8 -Path $stderrFile -Value $_.Exception.Message
    $exitCode = 998
  }
  $outText = if (Test-Path $stdoutFile) { Get-Content -Raw -Encoding UTF8 $stdoutFile } else { '' }
  $errText = if (Test-Path $stderrFile) { Get-Content -Raw -Encoding UTF8 $stderrFile } else { '' }
  Write-Result $taskId $title $exitCode $outText $errText 'script_completed'
  Write-Atomic $StateFile $taskId | Out-Null
  Heartbeat 'finished' $taskId ('exit=' + $exitCode)
  Push-State $taskId
  Log ('FINISH task=' + $taskId + ' exit=' + $exitCode)
}

Ensure-Dirs
$mutex = New-Object System.Threading.Mutex($false,$MutexName)
if (-not $mutex.WaitOne(1000)) {
  Log 'Another Remote Control V7 instance is already running.'
  exit 0
}

try {
  Log 'Remote Control Runner V7 started.'
  Heartbeat 'started' '' 'runner_started'
  Push-State 'runner-started'
  while ($true) {
    try {
      Pull-Latest
      Heartbeat 'polling' '' 'waiting_for_task'
      if (-not (Test-Path $TaskFile)) { Start-Sleep -Seconds $PollSeconds; continue }
      $raw = Get-Content -Raw -Encoding UTF8 $TaskFile
      $task = $raw | ConvertFrom-Json
      $taskId = [string]$task.id
      if ([string]::IsNullOrWhiteSpace($taskId)) { Start-Sleep -Seconds $PollSeconds; continue }
      $last = if (Test-Path $StateFile) { (Get-Content -Raw -Encoding UTF8 $StateFile).Trim([char]0xFEFF).Trim() } else { '' }
      if ($taskId -ne $last) { Run-Task $task } else { Log ('POLL already-processed ' + $taskId) }
    } catch {
      Log ('LOOP_ERROR=' + $_.Exception.Message)
      Heartbeat 'error' '' $_.Exception.Message
      Push-State 'loop-error'
    }
    Start-Sleep -Seconds $PollSeconds
  }
} finally {
  try { $mutex.ReleaseMutex() | Out-Null } catch {}
}

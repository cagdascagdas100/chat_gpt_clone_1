param([switch]$Once)
$ErrorActionPreference = 'Continue'

$ConfigPath = Join-Path $PSScriptRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if (Test-Path $ConfigPath) { . $ConfigPath }

$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { $PSScriptRoot }
$ProjectRoot = if ($env:AAYS_PROJECT_ROOT) { $env:AAYS_PROJECT_ROOT } else { $BridgeRoot }
$PollSeconds = if ($env:AAYS_RUNNER_POLL_SECONDS) { [int]$env:AAYS_RUNNER_POLL_SECONDS } else { 20 }
$DefaultTimeout = if ($env:AAYS_TASK_TIMEOUT_SECONDS) { [int]$env:AAYS_TASK_TIMEOUT_SECONDS } else { 3600 }
$AllowedScriptDir = if ($env:AAYS_ALLOWED_SCRIPT_DIR) { $env:AAYS_ALLOWED_SCRIPT_DIR } else { 'ai-task-scripts' }

$TaskFile = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$LastTaskFile = Join-Path $BridgeRoot 'ai-tasks\.last-task-id'
$HeartbeatFile = Join-Path $BridgeRoot 'ai-heartbeat\portable-runner.md'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
$ScriptDir = Join-Path $BridgeRoot $AllowedScriptDir
$RunnerLog = Join-Path $LogDir ('portable-runner-fixed-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')

New-Item -ItemType Directory -Force -Path (Join-Path $BridgeRoot 'ai-tasks'),(Join-Path $BridgeRoot 'ai-heartbeat'),$ResultDir,$LogDir,$ScriptDir | Out-Null

function Write-RunnerLog {
  param([string]$Text)
  $line = '[' + (Get-Date -Format 's') + '] ' + $Text
  Write-Output $line
  Add-Content -Encoding UTF8 -Path $RunnerLog -Value $line
}

function Write-Heartbeat {
  param([string]$Status,[string]$TaskId = '',[string]$Message = '')
  $lines = @(
    '# AAYS Portable Task Runner Fixed',
    '',
    ('Time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
    ('Status: ' + $Status),
    ('TaskId: ' + $TaskId),
    ('BridgeRoot: ' + $BridgeRoot),
    ('ProjectRoot: ' + $ProjectRoot),
    ('TaskFile: ' + $TaskFile),
    ('RunnerLog: ' + $RunnerLog),
    ('Message: ' + $Message),
    'GitRecovery: enabled',
    'SafeScriptOnly: enabled'
  )
  Set-Content -Encoding UTF8 -Path $HeartbeatFile -Value $lines
}

function Invoke-GitSafe {
  param([string[]]$GitArgs)
  try {
    Push-Location $BridgeRoot
    $out = (& git @GitArgs 2>&1 | Out-String)
    Add-Content -Encoding UTF8 -Path $RunnerLog -Value $out
    return $out
  } catch {
    $msg = 'GIT_EXCEPTION=' + $_.Exception.Message
    Add-Content -Encoding UTF8 -Path $RunnerLog -Value $msg
    return $msg
  } finally {
    Pop-Location
  }
}

function Sync-GitBeforeRead {
  Invoke-GitSafe @('add','ai-heartbeat','ai-runner-logs','ai-results','ai-tasks/.last-task-id') | Out-Null
  Invoke-GitSafe @('stash','push','-m','portable-runner-auto-stash-before-pull','--','ai-heartbeat','ai-runner-logs','ai-results','ai-tasks/.last-task-id') | Out-Null
  Invoke-GitSafe @('fetch','origin','main') | Out-Null
  $rb = Invoke-GitSafe @('rebase','origin/main')
  if ($rb -match 'CONFLICT|error:|fatal:') {
    Invoke-GitSafe @('rebase','--abort') | Out-Null
    Invoke-GitSafe @('reset','--hard','origin/main') | Out-Null
  }
}

function Push-ResultToGit {
  param([string]$TaskId)
  Invoke-GitSafe @('add','ai-results','ai-heartbeat','ai-tasks/.last-task-id','ai-runner-logs') | Out-Null
  Invoke-GitSafe @('commit','-m',('Portable runner result ' + $TaskId)) | Out-Null
  Invoke-GitSafe @('fetch','origin','main') | Out-Null
  $rb = Invoke-GitSafe @('rebase','origin/main')
  if ($rb -match 'CONFLICT|error:|fatal:') {
    Invoke-GitSafe @('rebase','--abort') | Out-Null
    Invoke-GitSafe @('reset','--hard','origin/main') | Out-Null
    Invoke-GitSafe @('add','ai-results','ai-heartbeat','ai-tasks/.last-task-id','ai-runner-logs') | Out-Null
    Invoke-GitSafe @('commit','-m',('Portable runner result ' + $TaskId + ' recovery')) | Out-Null
  }
  Invoke-GitSafe @('push','origin','main') | Out-Null
}

function Read-TaskSafely {
  if (-not (Test-Path $TaskFile)) { return $null }
  try {
    $raw = Get-Content -Raw -Encoding UTF8 $TaskFile
    if ([string]::IsNullOrWhiteSpace($raw)) { return $null }
    $task = $raw | ConvertFrom-Json
    if ($null -eq $task) { return $null }
    if (-not ($task.PSObject.Properties.Name -contains 'id')) { return $null }
    if ([string]::IsNullOrWhiteSpace([string]$task.id)) { return $null }
    return $task
  } catch {
    Write-RunnerLog ('TASK_JSON_ERROR ' + $_.Exception.Message)
    return $null
  }
}

function Write-RejectedResult {
  param([string]$TaskId,[string]$Reason)
  $stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
  $resultFile = Join-Path $ResultDir ($stamp + '-' + $TaskId + '.md')
  $lines = @('# AAYS Portable Task Runner Result','','## Task ID',$TaskId,'','## Status','Rejected','','## Reason',$Reason)
  Set-Content -Encoding UTF8 -Path $resultFile -Value $lines
  Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $TaskId
  Write-Heartbeat 'rejected' $TaskId $Reason
  Push-ResultToGit $TaskId
}

function Run-CurrentTask {
  param($Task)
  $TaskId = [string]$Task.id
  $Title = if ($Task.PSObject.Properties.Name -contains 'title') { [string]$Task.title } else { $TaskId }
  $WorkingDirectory = if ($Task.PSObject.Properties.Name -contains 'working_directory') { [string]$Task.working_directory } else { $ProjectRoot }
  $TimeoutSeconds = if ($Task.PSObject.Properties.Name -contains 'timeout_seconds') { [int]$Task.timeout_seconds } else { $DefaultTimeout }
  $candidate = if ($Task.PSObject.Properties.Name -contains 'script_path') { [string]$Task.script_path } else { '' }

  if ([string]::IsNullOrWhiteSpace($candidate)) { Write-RejectedResult $TaskId 'Missing script_path.'; return }
  if ($candidate -match '\.\.') { Write-RejectedResult $TaskId 'Rejected script_path containing parent traversal.'; return }

  $scriptPath = [IO.Path]::GetFullPath((Join-Path $ScriptDir $candidate))
  $allowedRoot = [IO.Path]::GetFullPath($ScriptDir)
  if (-not $scriptPath.StartsWith($allowedRoot,[StringComparison]::OrdinalIgnoreCase)) { Write-RejectedResult $TaskId ('Blocked script path: ' + $scriptPath); return }
  if (-not (Test-Path $scriptPath)) { Write-RejectedResult $TaskId ('Task script not found: ' + $scriptPath); return }

  $stdoutFile = Join-Path $LogDir ($TaskId + '-stdout.log')
  $stderrFile = Join-Path $LogDir ($TaskId + '-stderr.log')
  $stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
  $resultFile = Join-Path $ResultDir ($stamp + '-' + $TaskId + '.md')
  $exitCode = 999
  $timedOut = $false

  Write-Heartbeat 'running' $TaskId $Title
  Write-RunnerLog ('START ' + $TaskId + ' SCRIPT=' + $scriptPath)

  try {
    if (-not (Test-Path $WorkingDirectory)) { New-Item -ItemType Directory -Force -Path $WorkingDirectory | Out-Null }
    $argList = @('-NoProfile','-ExecutionPolicy','Bypass','-File',$scriptPath)
    $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList $argList -WorkingDirectory $WorkingDirectory -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile -PassThru
    $finished = $proc.WaitForExit($TimeoutSeconds * 1000)
    if (-not $finished) {
      $timedOut = $true
      try { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue } catch {}
      $exitCode = 124
    } else {
      $exitCode = $proc.ExitCode
    }
  } catch {
    Add-Content -Encoding UTF8 -Path $stderrFile -Value $_.Exception.Message
    $exitCode = 998
  }

  $stdout = if (Test-Path $stdoutFile) { Get-Content -Raw -Encoding UTF8 $stdoutFile } else { '' }
  $stderr = if (Test-Path $stderrFile) { Get-Content -Raw -Encoding UTF8 $stderrFile } else { '' }

  $head = @(
    '# AAYS Portable Task Runner Result',
    '',
    '## Task',
    $Title,
    '',
    '## Task ID',
    $TaskId,
    '',
    '## Time',
    (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),
    '',
    '## Working Directory',
    $WorkingDirectory,
    '',
    '## Timeout Seconds',
    ([string]$TimeoutSeconds),
    '',
    '## Timed Out',
    ([string]$timedOut),
    '',
    '## Exit Code',
    ([string]$exitCode),
    '',
    '## Output',
    '```text'
  )
  Set-Content -Encoding UTF8 -Path $resultFile -Value $head
  Add-Content -Encoding UTF8 -Path $resultFile -Value $stdout
  Add-Content -Encoding UTF8 -Path $resultFile -Value '```'
  Add-Content -Encoding UTF8 -Path $resultFile -Value @('','## Error','```text')
  Add-Content -Encoding UTF8 -Path $resultFile -Value $stderr
  Add-Content -Encoding UTF8 -Path $resultFile -Value '```'

  Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $TaskId
  Write-RunnerLog ('FINISH ' + $TaskId + ' EXIT=' + $exitCode)
  Write-Heartbeat 'finished' $TaskId ('exit=' + $exitCode)
  Push-ResultToGit $TaskId
}

Write-RunnerLog 'Portable fixed runner started.'
Write-Heartbeat 'polling' '' 'started'

while ($true) {
  try {
    Sync-GitBeforeRead
    $task = Read-TaskSafely
    if ($null -eq $task) {
      Write-Heartbeat 'polling' '' 'no-valid-task'
      if ($Once) { break }
      Start-Sleep -Seconds $PollSeconds
      continue
    }
    $taskId = [string]$task.id
    $lastId = if (Test-Path $LastTaskFile) { (Get-Content -Raw -Encoding UTF8 $LastTaskFile).Trim() } else { '' }
    if ($taskId -ne $lastId) {
      Run-CurrentTask $task
    } else {
      Write-Heartbeat 'polling' $taskId 'already-processed-or-waiting'
    }
  } catch {
    Write-RunnerLog ('LOOP_ERROR ' + $_.Exception.Message)
    Write-Heartbeat 'error' '' $_.Exception.Message
  }
  if ($Once) { break }
  Start-Sleep -Seconds $PollSeconds
}

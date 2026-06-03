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
$RunnerLog = Join-Path $LogDir ('portable-runner-no-spawn-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')

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
    'Mode: no-spawn-foreground-loop',
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
  Invoke-GitSafe @('fetch','origin','main') | Out-Null
  $pull = Invoke-GitSafe @('pull','--ff-only','origin','main')
  if ($pull -match 'fatal:|error:|CONFLICT') {
    Write-RunnerLog 'Git fast-forward pull failed; keeping local state and continuing poll.'
  }
}

function Push-ResultToGit {
  param([string]$TaskId)
  Invoke-GitSafe @('add','ai-results','ai-heartbeat','ai-tasks/.last-task-id','ai-runner-logs') | Out-Null
  $commit = Invoke-GitSafe @('commit','-m',('Portable runner result ' + $TaskId))
  if ($commit -match 'nothing to commit') { return }
  Invoke-GitSafe @('pull','--rebase','origin','main') | Out-Null
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

  Write-Heartbeat 'running' $TaskId $Title
  Write-RunnerLog ('START ' + $TaskId + ' SCRIPT=' + $scriptPath)

  try {
    if (-not (Test-Path $WorkingDirectory)) { New-Item -ItemType Directory -Force -Path $WorkingDirectory | Out-Null }
    Push-Location $WorkingDirectory
    $output = (& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath 2>&1 | Out-String)
    $exitCode = if ($null -ne $LASTEXITCODE) { [int]$LASTEXITCODE } else { 0 }
    Pop-Location
    Set-Content -Encoding UTF8 -Path $stdoutFile -Value $output
    Set-Content -Encoding UTF8 -Path $stderrFile -Value ''
  } catch {
    try { Pop-Location } catch {}
    Set-Content -Encoding UTF8 -Path $stdoutFile -Value ''
    Set-Content -Encoding UTF8 -Path $stderrFile -Value $_.Exception.Message
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
    '## Exit Code',
    ([string]$exitCode),
    '',
    '## Runner Mode',
    'no-spawn-foreground-loop',
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

Write-RunnerLog 'Portable fixed runner started in no-spawn foreground loop.'
Write-Heartbeat 'polling' '' 'started'

while ($true) {
  try {
    Sync-GitBeforeRead
    $task = Read-TaskSafely
    if ($null -eq $task) {
      Write-Heartbeat 'polling' '' 'no-valid-task'
      Write-RunnerLog 'POLL no-valid-task'
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
      Write-RunnerLog ('POLL already-processed-or-waiting ' + $taskId)
    }
  } catch {
    Write-RunnerLog ('LOOP_ERROR ' + $_.Exception.Message)
    Write-Heartbeat 'error' '' $_.Exception.Message
  }
  if ($Once) { break }
  Start-Sleep -Seconds $PollSeconds
}

param(
  [switch]$Once
)

$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$ConfigPath = Join-Path $BridgeRoot "AAYS_TASK_BRIDGE_CONFIG.ps1"

if (Test-Path -Path $ConfigPath) {
  . $ConfigPath
}

if (-not $env:AAYS_BRIDGE_ROOT) {
  $env:AAYS_BRIDGE_ROOT = $BridgeRoot
}

$TaskFile = Join-Path $env:AAYS_BRIDGE_ROOT "ai-tasks\current-task.json"
$ScriptsDir = Join-Path $env:AAYS_BRIDGE_ROOT "ai-task-scripts"
$ResultsDir = Join-Path $env:AAYS_BRIDGE_ROOT "ai-results"
$LogsDir = Join-Path $env:AAYS_BRIDGE_ROOT "ai-runner-logs"
$HeartbeatFile = Join-Path $env:AAYS_BRIDGE_ROOT "ai-heartbeat\portable-runner.md"

New-Item -ItemType Directory -Force -Path (Split-Path $TaskFile) | Out-Null
New-Item -ItemType Directory -Force -Path $ScriptsDir | Out-Null
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $HeartbeatFile) | Out-Null

$PollSeconds = 20
if ($env:AAYS_RUNNER_POLL_SECONDS) {
  [int]$PollSeconds = $env:AAYS_RUNNER_POLL_SECONDS
}

$LastTaskId = $null

function Write-Heartbeat {
  param(
    [string]$Status,
    [string]$TaskId,
    [string]$Message
  )

  @"
# TerraYield Portable Runner Heartbeat

status: $Status
task_id: $TaskId
checked_at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
bridge_root: $env:AAYS_BRIDGE_ROOT
project_root: $env:AAYS_PROJECT_ROOT
planned_data_root: $env:AAYS_PLANNED_DATA_ROOT
message: $Message
"@ | Set-Content -Path $HeartbeatFile -Encoding UTF8
}

function Write-Result {
  param(
    [string]$TaskId,
    [string]$Status,
    [string]$Message,
    [string]$OutputPath = "",
    [string]$ErrorPath = ""
  )

  $SafeTaskId = ($TaskId -replace '[^a-zA-Z0-9._-]', '_')
  if (-not $SafeTaskId) {
    $SafeTaskId = "unknown-task"
  }

  $ResultPath = Join-Path $ResultsDir "$SafeTaskId.result.json"

  $Result = [ordered]@{
    task_id = $TaskId
    status = $Status
    message = $Message
    output_path = $OutputPath
    error_path = $ErrorPath
    written_at = (Get-Date).ToString("s")
  }

  $Result | ConvertTo-Json -Depth 8 | Set-Content -Path $ResultPath -Encoding UTF8
}

function Get-SafeScriptPath {
  param([object]$Task)

  $Candidate = $null

  if ($Task.script_path) {
    $Candidate = [string]$Task.script_path
  } elseif ($Task.script) {
    $Candidate = [string]$Task.script
  } elseif ($Task.command) {
    $Candidate = [string]$Task.command
  }

  if (-not $Candidate -or $Candidate.Trim() -eq "") {
    return $null
  }

  if ([System.IO.Path]::IsPathRooted($Candidate)) {
    $FullPath = [System.IO.Path]::GetFullPath($Candidate)
  } else {
    $FullPath = [System.IO.Path]::GetFullPath((Join-Path $ScriptsDir $Candidate))
  }

  $AllowedRoot = [System.IO.Path]::GetFullPath($ScriptsDir)

  if (-not $FullPath.StartsWith($AllowedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Blocked unsafe script path outside ai-task-scripts: $FullPath"
  }

  if ([System.IO.Path]::GetExtension($FullPath).ToLowerInvariant() -ne ".ps1") {
    throw "Blocked non-ps1 task script: $FullPath"
  }

  if (-not (Test-Path -Path $FullPath)) {
    throw "Task script not found: $FullPath"
  }

  return $FullPath
}

function Invoke-Task {
  param([object]$Task)

  $TaskId = [string]$Task.id
  if (-not $TaskId) {
    $TaskId = "unknown-task"
  }

  $ScriptPath = Get-SafeScriptPath -Task $Task

  if (-not $ScriptPath) {
    Write-Heartbeat -Status "idle" -TaskId $TaskId -Message "No script_path/script/command provided."
    Write-Result -TaskId $TaskId -Status "idle" -Message "No executable task script provided."
    return
  }

  $WorkingDirectory = $env:AAYS_PROJECT_ROOT
  if ($Task.working_directory) {
    $WorkingDirectory = [string]$Task.working_directory
  }

  if (-not (Test-Path -Path $WorkingDirectory)) {
    throw "Working directory not found: $WorkingDirectory"
  }

  $SafeTaskId = ($TaskId -replace '[^a-zA-Z0-9._-]', '_')
  $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $LogPath = Join-Path $LogsDir "$SafeTaskId.$Timestamp.log"
  $ErrPath = Join-Path $LogsDir "$SafeTaskId.$Timestamp.err.log"

  Write-Heartbeat -Status "running" -TaskId $TaskId -Message "Running $ScriptPath"

  Push-Location $WorkingDirectory
  try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath 1> $LogPath 2> $ErrPath
    $ExitCode = $LASTEXITCODE
  } finally {
    Pop-Location
  }

  if ($null -eq $ExitCode) {
    $ExitCode = 999
  }

  if ($ExitCode -eq 0) {
    Write-Heartbeat -Status "completed" -TaskId $TaskId -Message "Task completed successfully."
    Write-Result -TaskId $TaskId -Status "completed" -Message "Task completed successfully." -OutputPath $LogPath -ErrorPath $ErrPath
  } else {
    $ErrPreview = ""
    if (Test-Path -Path $ErrPath) {
      $ErrPreview = ((Get-Content -Path $ErrPath -ErrorAction SilentlyContinue | Select-Object -First 20) -join " ")
    }
    Write-Heartbeat -Status "failed" -TaskId $TaskId -Message "Task failed with exit code $ExitCode."
    Write-Result -TaskId $TaskId -Status "failed" -Message "Task failed with exit code $ExitCode. $ErrPreview" -OutputPath $LogPath -ErrorPath $ErrPath
  }
}

Write-Heartbeat -Status "started" -TaskId "" -Message "Portable runner started."

while ($true) {
  try {
    if (-not (Test-Path -Path $TaskFile)) {
      Write-Heartbeat -Status "waiting" -TaskId "" -Message "Task file not found."
    } else {
      $Task = Get-Content -Path $TaskFile -Raw | ConvertFrom-Json
      $TaskId = [string]$Task.id

      if (-not $TaskId) {
        $TaskId = "unknown-task"
      }

      if ($TaskId -ne $LastTaskId) {
        $LastTaskId = $TaskId
        Invoke-Task -Task $Task
      } else {
        Write-Heartbeat -Status "polling" -TaskId $TaskId -Message "No new task."
      }
    }
  } catch {
    Write-Heartbeat -Status "error" -TaskId $LastTaskId -Message $_.Exception.Message
    Write-Result -TaskId $LastTaskId -Status "error" -Message $_.Exception.Message
  }

  if ($Once) {
    break
  }

  Start-Sleep -Seconds $PollSeconds
}

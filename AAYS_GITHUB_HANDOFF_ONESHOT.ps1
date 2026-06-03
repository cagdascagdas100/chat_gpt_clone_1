$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE\chat_gpt_clone_1"
$OldBridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"

$TaskFile = Join-Path $BridgeRoot "ai-tasks\current-task.json"
$ScriptsDir = Join-Path $BridgeRoot "ai-task-scripts"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$LogsDir = Join-Path $BridgeRoot "ai-runner-logs"
$HandoffDir = Join-Path $BridgeRoot "ai-handoff"
$HandoffJson = Join-Path $HandoffDir "latest-status.json"
$HandoffMd = Join-Path $HandoffDir "latest-status.md"
$HeartbeatFile = Join-Path $BridgeRoot "ai-heartbeat\github-handoff-runner.md"

New-Item -ItemType Directory -Force -Path $ScriptsDir | Out-Null
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null
New-Item -ItemType Directory -Force -Path $HandoffDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $HeartbeatFile) | Out-Null

function Write-Handoff {
  param(
    [string]$Status,
    [string]$TaskId,
    [string]$Message,
    [string]$ResultPath = ""
  )

  [ordered]@{
    status = $Status
    project = "terrayield"
    task_id = $TaskId
    message = $Message
    result_path = $ResultPath
    heartbeat_status = "oneshot-v2"
    bridge_root = $BridgeRoot
    updated_at = (Get-Date).ToString("s")
  } | ConvertTo-Json -Depth 8 | Set-Content -Path $HandoffJson -Encoding UTF8

  @(
    "# AAYS GitHub Handoff Status",
    "",
    "- Status: $Status",
    "- Project: terrayield",
    "- Task ID: $TaskId",
    "- Message: $Message",
    "- Result path: $ResultPath",
    "- Heartbeat status: oneshot-v2",
    "- Updated at: $((Get-Date).ToString("s"))"
  ) | Set-Content -Path $HandoffMd -Encoding UTF8
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

  [ordered]@{
    task_id = $TaskId
    status = $Status
    message = $Message
    output_path = $OutputPath
    error_path = $ErrorPath
    bridge_root = $BridgeRoot
    written_at = (Get-Date).ToString("s")
  } | ConvertTo-Json -Depth 8 | Set-Content -Path $ResultPath -Encoding UTF8

  return $ResultPath
}

function Resolve-TaskScriptPath {
  param([object]$Task)

  $Candidate = ""

  if ($Task.script_path) {
    $Candidate = [string]$Task.script_path
  } elseif ($Task.command) {
    $CommandText = [string]$Task.command

    if ($CommandText -match '-File\s+("?)([^"]+?\.ps1)\1') {
      $Candidate = $Matches[2]
    }
  }

  if (-not $Candidate -or $Candidate.Trim() -eq "") {
    return ""
  }

  if ($Candidate.StartsWith($OldBridgeRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    $Candidate = $Candidate.Replace($OldBridgeRoot, $BridgeRoot)
  }

  if ([System.IO.Path]::IsPathRooted($Candidate)) {
    $ScriptPath = [System.IO.Path]::GetFullPath($Candidate)
  } else {
    $ScriptPath = [System.IO.Path]::GetFullPath((Join-Path $ScriptsDir $Candidate))
  }

  $AllowedRoot = [System.IO.Path]::GetFullPath($ScriptsDir)

  if (-not $ScriptPath.StartsWith($AllowedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Blocked unsafe script path outside ai-task-scripts: $ScriptPath"
  }

  if ([System.IO.Path]::GetExtension($ScriptPath).ToLowerInvariant() -ne ".ps1") {
    throw "Blocked non-ps1 task script: $ScriptPath"
  }

  return $ScriptPath
}

function Commit-And-Push {
  param([string]$Message)

  Push-Location $BridgeRoot
  try {
    git add -f AAYS_GITHUB_HANDOFF_ONESHOT.ps1 ai-results ai-handoff ai-heartbeat ai-tasks ai-task-scripts
    $Status = git status --short
    if ($Status) {
      git commit -m $Message

      git push origin main
      if ($LASTEXITCODE -ne 0) {
        git fetch origin
        git pull --rebase origin main
        git push origin main
      }
    }
  } finally {
    Pop-Location
  }
}

try {
  if (-not (Test-Path -Path $TaskFile)) {
    Write-Handoff -Status "error" -TaskId "" -Message "Task file missing."
    Commit-And-Push -Message "chore(ai): oneshot-v2 task file missing"
    exit 1
  }

  $Task = Get-Content -Path $TaskFile -Raw | ConvertFrom-Json
  $TaskId = [string]$Task.id
  if (-not $TaskId) {
    $TaskId = "unknown-task"
  }

  $ScriptPath = Resolve-TaskScriptPath -Task $Task

  if (-not $ScriptPath) {
    $ResultPath = Write-Result -TaskId $TaskId -Status "idle" -Message "No script_path or command -File ps1 provided."
    Write-Handoff -Status "idle" -TaskId $TaskId -Message "No script_path or command -File ps1 provided." -ResultPath $ResultPath
    Commit-And-Push -Message "chore(ai): oneshot-v2 idle $TaskId"
    exit 0
  }

  if (-not (Test-Path -Path $ScriptPath)) {
    throw "Task script not found: $ScriptPath"
  }

  $WorkingDirectory = [string]$Task.working_directory
  if (-not $WorkingDirectory) {
    $WorkingDirectory = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
  }

  if (-not (Test-Path -Path $WorkingDirectory)) {
    throw "Working directory not found: $WorkingDirectory"
  }

  $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $OutPath = Join-Path $LogsDir "$TaskId.$Timestamp.log"
  $ErrPath = Join-Path $LogsDir "$TaskId.$Timestamp.err.log"

  @(
    "# GitHub Handoff Runner Heartbeat",
    "",
    "- Status: running",
    "- Task ID: $TaskId",
    "- Checked at: $((Get-Date).ToString("s"))"
  ) | Set-Content -Path $HeartbeatFile -Encoding UTF8

  Write-Handoff -Status "running" -TaskId $TaskId -Message "One-shot v2 executor running task."

  Push-Location $WorkingDirectory
  try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath 1> $OutPath 2> $ErrPath
    $ExitCode = $LASTEXITCODE
  } finally {
    Pop-Location
  }

  if ($null -eq $ExitCode) {
    $ExitCode = 999
  }

  if ($ExitCode -eq 0) {
    $ResultPath = Write-Result -TaskId $TaskId -Status "completed" -Message "Task completed successfully." -OutputPath $OutPath -ErrorPath $ErrPath
    Write-Handoff -Status "completed" -TaskId $TaskId -Message "Task completed successfully." -ResultPath $ResultPath
  } else {
    $ResultPath = Write-Result -TaskId $TaskId -Status "failed" -Message "Task failed with exit code $ExitCode." -OutputPath $OutPath -ErrorPath $ErrPath
    Write-Handoff -Status "failed" -TaskId $TaskId -Message "Task failed with exit code $ExitCode." -ResultPath $ResultPath
  }

  @(
    "# GitHub Handoff Runner Heartbeat",
    "",
    "- Status: done",
    "- Task ID: $TaskId",
    "- Checked at: $((Get-Date).ToString("s"))"
  ) | Set-Content -Path $HeartbeatFile -Encoding UTF8

  Commit-And-Push -Message "chore(ai): oneshot-v2 result $TaskId"
  exit 0
} catch {
  $TaskIdForError = ""
  try { $TaskIdForError = [string]$Task.id } catch {}
  $ResultPath = Write-Result -TaskId $TaskIdForError -Status "error" -Message $_.Exception.Message
  Write-Handoff -Status "error" -TaskId $TaskIdForError -Message $_.Exception.Message -ResultPath $ResultPath
  Commit-And-Push -Message "chore(ai): oneshot-v2 error $TaskIdForError"
  exit 1
}

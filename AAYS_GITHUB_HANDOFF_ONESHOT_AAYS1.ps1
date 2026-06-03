$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1"
$TaskFile = Join-Path $BridgeRoot "ai-tasks\aays1-current-task.json"
$ScriptsDir = Join-Path $BridgeRoot "ai-task-scripts"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$LogsDir = Join-Path $BridgeRoot "ai-runner-logs"
$HandoffDir = Join-Path $BridgeRoot "ai-handoff"
$HandoffJson = Join-Path $HandoffDir "aays1-latest-status.json"
$HandoffMd = Join-Path $HandoffDir "aays1-latest-status.md"

New-Item -ItemType Directory -Force -Path $ScriptsDir | Out-Null
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null
New-Item -ItemType Directory -Force -Path $HandoffDir | Out-Null

function Write-Aays1Handoff {
  param([string]$Status, [string]$TaskId, [string]$Message, [string]$ResultPath = "")

  [ordered]@{
    status = $Status
    project = "terrayield"
    task_id = $TaskId
    message = $Message
    result_path = $ResultPath
    heartbeat_status = "aays1-oneshot"
    bridge_root = $BridgeRoot
    task_file = "ai-tasks/aays1-current-task.json"
    updated_at = (Get-Date).ToString("s")
  } | ConvertTo-Json -Depth 8 | Set-Content -Path $HandoffJson -Encoding UTF8

  @(
    "# AAYS1 Handoff Status",
    "",
    "- Status: $Status",
    "- Task ID: $TaskId",
    "- Message: $Message",
    "- Result path: $ResultPath",
    "- Updated at: $((Get-Date).ToString("s"))"
  ) | Set-Content -Path $HandoffMd -Encoding UTF8
}

function Write-Result {
  param([string]$TaskId, [string]$Status, [string]$Message, [string]$OutputPath = "", [string]$ErrorPath = "")

  $SafeTaskId = ($TaskId -replace '[^a-zA-Z0-9._-]', '_')
  if (-not $SafeTaskId) { $SafeTaskId = "unknown-task" }

  $ResultPath = Join-Path $ResultsDir "$SafeTaskId.result.json"

  [ordered]@{
    task_id = $TaskId
    status = $Status
    message = $Message
    output_path = $OutputPath
    error_path = $ErrorPath
    bridge_root = $BridgeRoot
    task_file = "ai-tasks/aays1-current-task.json"
    written_at = (Get-Date).ToString("s")
  } | ConvertTo-Json -Depth 8 | Set-Content -Path $ResultPath -Encoding UTF8

  return $ResultPath
}

function Commit-And-Push {
  param([string]$Message)

  Push-Location $BridgeRoot
  try {
    git add -f AAYS_GITHUB_HANDOFF_ONESHOT_AAYS1.ps1 AAYS_DEVAM_LOOP_AAYS1.ps1 ai-results ai-handoff/aays1-latest-status.json ai-handoff/aays1-latest-status.md ai-tasks/aays1-current-task.json ai-task-scripts
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
    Write-Aays1Handoff -Status "error" -TaskId "" -Message "AAYS1 task file missing."
    Commit-And-Push -Message "chore(ai): aays1 task file missing"
    exit 1
  }

  $Task = Get-Content -Path $TaskFile -Raw | ConvertFrom-Json
  $TaskId = [string]$Task.id
  if (-not $TaskId) { $TaskId = "unknown-task" }

  $ScriptName = [string]$Task.script_path
  if (-not $ScriptName -or $ScriptName.Trim() -eq "") {
    $ResultPath = Write-Result -TaskId $TaskId -Status "idle" -Message "No script_path provided."
    Write-Aays1Handoff -Status "idle" -TaskId $TaskId -Message "No script_path provided." -ResultPath $ResultPath
    Commit-And-Push -Message "chore(ai): aays1 idle $TaskId"
    exit 0
  }

  $ScriptPath = [System.IO.Path]::GetFullPath((Join-Path $ScriptsDir $ScriptName))
  $AllowedRoot = [System.IO.Path]::GetFullPath($ScriptsDir)

  if (-not $ScriptPath.StartsWith($AllowedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Blocked unsafe script path outside ai-task-scripts: $ScriptPath"
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

  Write-Aays1Handoff -Status "running" -TaskId $TaskId -Message "AAYS1 one-shot running task."

  Push-Location $WorkingDirectory
  try {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath 1> $OutPath 2> $ErrPath
    $ExitCode = $LASTEXITCODE
  } finally {
    Pop-Location
  }

  if ($null -eq $ExitCode) { $ExitCode = 999 }

  if ($ExitCode -eq 0) {
    $ResultPath = Write-Result -TaskId $TaskId -Status "completed" -Message "Task completed successfully." -OutputPath $OutPath -ErrorPath $ErrPath
    Write-Aays1Handoff -Status "completed" -TaskId $TaskId -Message "Task completed successfully." -ResultPath $ResultPath
  } else {
    $ResultPath = Write-Result -TaskId $TaskId -Status "failed" -Message "Task failed with exit code $ExitCode." -OutputPath $OutPath -ErrorPath $ErrPath
    Write-Aays1Handoff -Status "failed" -TaskId $TaskId -Message "Task failed with exit code $ExitCode." -ResultPath $ResultPath
  }

  Commit-And-Push -Message "chore(ai): aays1 result $TaskId"
  exit 0
} catch {
  $TaskIdForError = ""
  try { $TaskIdForError = [string]$Task.id } catch {}
  $ResultPath = Write-Result -TaskId $TaskIdForError -Status "error" -Message $_.Exception.Message
  Write-Aays1Handoff -Status "error" -TaskId $TaskIdForError -Message $_.Exception.Message -ResultPath $ResultPath
  Commit-And-Push -Message "chore(ai): aays1 error $TaskIdForError"
  exit 1
}

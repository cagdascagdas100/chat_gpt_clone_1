param(
  [int]$PollSeconds = 20
)

$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE\chat_gpt_clone_1"
$RunnerPath = Join-Path $BridgeRoot "AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1"
$TaskFile = Join-Path $BridgeRoot "ai-tasks\current-task.json"
$HandoffDir = Join-Path $BridgeRoot "ai-handoff"
$HandoffJson = Join-Path $HandoffDir "latest-status.json"
$HandoffMd = Join-Path $HandoffDir "latest-status.md"
$HeartbeatFile = Join-Path $BridgeRoot "ai-heartbeat\github-handoff-runner.md"
$ResultsDir = Join-Path $BridgeRoot "ai-results"

New-Item -ItemType Directory -Force -Path $HandoffDir | Out-Null
New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $HeartbeatFile) | Out-Null

$LastTaskId = $null

function Write-Handoff {
  param(
    [string]$Status,
    [string]$TaskId,
    [string]$Message,
    [string]$ResultPath = "",
    [string]$HeartbeatStatus = ""
  )

  $payload = [ordered]@{
    status = $Status
    project = "terrayield"
    task_id = $TaskId
    message = $Message
    result_path = $ResultPath
    heartbeat_status = $HeartbeatStatus
    bridge_root = $BridgeRoot
    updated_at = (Get-Date).ToString("s")
  }

  $payload | ConvertTo-Json -Depth 8 | Set-Content -Path $HandoffJson -Encoding UTF8

  @(
    "# AAYS GitHub Handoff Status",
    "",
    "- Status: $Status",
    "- Project: terrayield",
    "- Task ID: $TaskId",
    "- Message: $Message",
    "- Result path: $ResultPath",
    "- Heartbeat status: $HeartbeatStatus",
    "- Updated at: $((Get-Date).ToString("s"))"
  ) | Set-Content -Path $HandoffMd -Encoding UTF8
}

function Git-Sync {
  param([string]$CommitMessage)

  try {
    Push-Location $BridgeRoot

    git add -f ai-tasks ai-task-scripts ai-results ai-heartbeat ai-handoff AAYS_GITHUB_HANDOFF_RUNNER.ps1 AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1 AAYS_TASK_BRIDGE_CONFIG.ps1 2>$null

    $status = git status --short --untracked-files=no
    if ($status) {
      git commit -m $CommitMessage
      git push origin main
    }

    Pop-Location
  } catch {
    try { Pop-Location } catch {}
  }
}

function Get-CurrentTaskId {
  if (-not (Test-Path -Path $TaskFile)) {
    return ""
  }

  try {
    $task = Get-Content -Path $TaskFile -Raw | ConvertFrom-Json
    return [string]$task.id
  } catch {
    return ""
  }
}

Write-Handoff -Status "ready" -TaskId "" -Message "Clean GitHub handoff runner started." -HeartbeatStatus "started"
Git-Sync -CommitMessage "chore(ai): start clean github handoff runner"

while ($true) {
  try {
    Push-Location $BridgeRoot
    git pull --rebase origin main
    Pop-Location

    $TaskId = Get-CurrentTaskId

    @(
      "# GitHub Handoff Runner Heartbeat",
      "",
      "- Status: polling",
      "- Task ID: $TaskId",
      "- Checked at: $((Get-Date).ToString("s"))"
    ) | Set-Content -Path $HeartbeatFile -Encoding UTF8

    if ($TaskId -and $TaskId -ne $LastTaskId) {
      $LastTaskId = $TaskId

      Write-Handoff -Status "running" -TaskId $TaskId -Message "Task detected and running."
      Git-Sync -CommitMessage "chore(ai): task $TaskId running"

      if (Test-Path -Path $RunnerPath) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $RunnerPath -Once
      } else {
        Write-Handoff -Status "error" -TaskId $TaskId -Message "Portable runner file missing."
        Git-Sync -CommitMessage "chore(ai): task $TaskId runner missing"
        Start-Sleep -Seconds $PollSeconds
        continue
      }

      $ResultFile = Join-Path $ResultsDir "$TaskId.result.json"
      $ResultStatus = "unknown"
      $ResultMessage = "Result file not found."

      if (Test-Path -Path $ResultFile) {
        try {
          $result = Get-Content -Path $ResultFile -Raw | ConvertFrom-Json
          $ResultStatus = [string]$result.status
          $ResultMessage = [string]$result.message
        } catch {
          $ResultStatus = "result_parse_error"
          $ResultMessage = $_.Exception.Message
        }
      }

      Write-Handoff -Status $ResultStatus -TaskId $TaskId -Message $ResultMessage -ResultPath $ResultFile
      Git-Sync -CommitMessage "chore(ai): task $TaskId result"
    }
  } catch {
    Write-Handoff -Status "error" -TaskId $LastTaskId -Message $_.Exception.Message
    Git-Sync -CommitMessage "chore(ai): handoff error"
  }

  Start-Sleep -Seconds $PollSeconds
}

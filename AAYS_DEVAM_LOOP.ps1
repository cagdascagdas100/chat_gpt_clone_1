param(
  [int]$PollSeconds = 20
)

$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\AAYS_GITHUB_BRIDGE\chat_gpt_clone_1"
$StateRoot = "C:\AAYS_GITHUB_BRIDGE\runner-state"
$LastTaskFile = Join-Path $StateRoot "last-task-id.txt"
$OneShot = Join-Path $BridgeRoot "AAYS_GITHUB_HANDOFF_ONESHOT.ps1"
$TaskFile = Join-Path $BridgeRoot "ai-tasks\current-task.json"
$LoopHeartbeat = Join-Path $BridgeRoot "ai-heartbeat\devam-loop.md"

New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $LoopHeartbeat) | Out-Null

function Get-TaskId {
  if (-not (Test-Path -Path $TaskFile)) {
    return ""
  }

  try {
    $Task = Get-Content -Path $TaskFile -Raw | ConvertFrom-Json
    return [string]$Task.id
  } catch {
    return ""
  }
}

function Write-LoopHeartbeat {
  param(
    [string]$Status,
    [string]$TaskId,
    [string]$Message
  )

  @(
    "# AAYS Devam Loop",
    "",
    "- Status: $Status",
    "- Task ID: $TaskId",
    "- Message: $Message",
    "- Checked at: $((Get-Date).ToString("s"))"
  ) | Set-Content -Path $LoopHeartbeat -Encoding UTF8
}

while ($true) {
  try {
    Set-Location $BridgeRoot

    git rebase --abort 2>$null
    git fetch origin
    git checkout main 2>$null
    git reset --hard origin/main | Out-Null

    $TaskId = Get-TaskId

    $LastTaskId = ""
    if (Test-Path -Path $LastTaskFile) {
      $LastTaskId = (Get-Content -Path $LastTaskFile -Raw).Trim()
    }

    if (-not $TaskId) {
      Write-LoopHeartbeat -Status "polling" -TaskId "" -Message "No task id found."
    } elseif ($TaskId -eq $LastTaskId) {
      Write-LoopHeartbeat -Status "polling" -TaskId $TaskId -Message "No new task."
    } else {
      Write-LoopHeartbeat -Status "running" -TaskId $TaskId -Message "New task detected. Running one-shot."

      powershell -NoProfile -ExecutionPolicy Bypass -File $OneShot

      Set-Content -Path $LastTaskFile -Value $TaskId -Encoding UTF8

      Write-LoopHeartbeat -Status "completed" -TaskId $TaskId -Message "One-shot finished for task."
    }

    git add -f ai-heartbeat ai-handoff ai-results ai-tasks 2>$null
    $Status = git status --short
    if ($Status) {
      git commit -m "chore(ai): devam loop heartbeat $TaskId" 2>$null
      git push origin main 2>$null
    }
  } catch {
    Write-LoopHeartbeat -Status "error" -TaskId "" -Message $_.Exception.Message
  }

  Start-Sleep -Seconds $PollSeconds
}

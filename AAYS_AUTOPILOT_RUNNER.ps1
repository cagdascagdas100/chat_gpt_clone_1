$ErrorActionPreference = "Continue"

$Repo = "C:\AAYS_GITHUB_BRIDGE_CLEAN"
$StateDir = "C:\AAYS_AUTOPILOT_STATE"
$LogDir = Join-Path $StateDir "logs"
$LastTaskFile = Join-Path $StateDir "last-task-id.txt"

New-Item -ItemType Directory -Force $StateDir,$LogDir | Out-Null

function Log($m) {
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  $line = "[$ts] $m"
  Write-Host $line
  Add-Content -Encoding UTF8 (Join-Path $LogDir "autopilot.log") $line
}

function GitCleanPull {
  Set-Location $Repo
  git rebase --abort 2>$null | Out-Null
  git merge --abort 2>$null | Out-Null
  if (Test-Path ".git\rebase-merge") { Remove-Item -Recurse -Force ".git\rebase-merge" }
  if (Test-Path ".git\rebase-apply") { Remove-Item -Recurse -Force ".git\rebase-apply" }
  git fetch origin main | Out-Null
  git reset --hard origin/main | Out-Null
}

function GitPushRetry($message) {
  Set-Location $Repo
  git add -f ai-results ai-runner-logs ai-heartbeat ai-handoff ai-tasks 2>$null | Out-Null
  git commit -m $message 2>$null | Out-Null

  for ($i=1; $i -le 12; $i++) {
    Log "push try $i"
    git fetch origin main | Out-Null
    git rebase origin/main 2>$null | Out-Null
    git push origin main 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
      Log "push ok"
      return $true
    }
    Start-Sleep -Seconds 4
  }

  Log "push failed"
  return $false
}

function GetTask {
  $taskPath = Join-Path $Repo "ai-tasks\current-task.json"
  if (!(Test-Path $taskPath)) { return $null }
  try { return Get-Content $taskPath -Raw | ConvertFrom-Json } catch { return $null }
}

function RunTask($task) {
  $taskId = [string]$task.id
  $scriptPath = [string]$task.script_path
  $workDir = [string]$task.working_directory

  if ([string]::IsNullOrWhiteSpace($taskId)) { return }
  if ([string]::IsNullOrWhiteSpace($scriptPath)) {
    Log "skip ${taskId}: no script_path; command ignored"
    return
  }
  if ($scriptPath -match "[:\\\/]") {
    Log "skip ${taskId}: script_path must be filename only"
    return
  }

  $scriptFull = Join-Path $Repo ("ai-task-scripts\" + $scriptPath)
  if (!(Test-Path $scriptFull)) {
    Log "skip ${taskId}: script not found $scriptFull"
    return
  }

  New-Item -ItemType Directory -Force (Join-Path $Repo "ai-results") | Out-Null
  New-Item -ItemType Directory -Force (Join-Path $Repo "ai-runner-logs") | Out-Null
  New-Item -ItemType Directory -Force (Join-Path $Repo "ai-heartbeat") | Out-Null
  New-Item -ItemType Directory -Force (Join-Path $Repo "ai-handoff") | Out-Null

  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $out = Join-Path $Repo "ai-runner-logs\$taskId.$stamp.log"
  $err = Join-Path $Repo "ai-runner-logs\$taskId.$stamp.err.log"

  Log "running $taskId via $scriptPath"

  $p = Start-Process powershell -PassThru -Wait -NoNewWindow -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $scriptFull
  ) -RedirectStandardOutput $out -RedirectStandardError $err -WorkingDirectory $workDir

  $status = if ($p.ExitCode -eq 0) { "completed" } else { "failed" }

  $result = [ordered]@{
    task_id = $taskId
    status = $status
    exit_code = $p.ExitCode
    message = if ($p.ExitCode -eq 0) { "Task completed successfully." } else { "Task failed." }
    output_path = $out
    error_path = $err
    bridge_root = $Repo
    written_at = (Get-Date -Format o)
  }

  $result | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $Repo "ai-results\$taskId.result.json")

  Set-Content -Encoding UTF8 (Join-Path $Repo "ai-heartbeat\autopilot-runner.md") "# AAYS Autopilot Runner`n`nstatus: $status`ntask_id: $taskId`nchecked_at: $(Get-Date -Format o)`nbridge_root: $Repo`n"
  Set-Content -Encoding UTF8 (Join-Path $Repo "ai-handoff\latest-status.md") "# AAYS Autopilot Status`n`n- Status: $status`n- Task ID: $taskId`n- Updated at: $(Get-Date -Format o)`n"

  Set-Content -Encoding UTF8 $LastTaskFile $taskId
  GitPushRetry "chore(ai): autopilot result $taskId" | Out-Null
}

Log "AAYS autopilot started. Leave this window open."

while ($true) {
  GitCleanPull
  $task = GetTask

  if ($null -ne $task) {
    $taskId = [string]$task.id
    $last = ""
    if (Test-Path $LastTaskFile) {
      $last = (Get-Content $LastTaskFile -Raw).Trim()
    }

    if ($taskId -and $taskId -ne $last) {
      RunTask $task
    } else {
      Log "polling; no new task. last=$last"
    }
  }

  Start-Sleep -Seconds 15
}


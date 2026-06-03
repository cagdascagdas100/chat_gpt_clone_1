$ErrorActionPreference = "Continue"

$Root = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
Set-Location $Root

$TasksDir = "$Root\ai-tasks"
$ResultsDir = "$Root\ai-results"
$HeartbeatDir = "$Root\ai-heartbeat"
$LastTaskFile = "$TasksDir\.last-safe-lite-task-id"

New-Item -ItemType Directory -Force -Path $TasksDir,$ResultsDir,$HeartbeatDir | Out-Null

function Stamp {
  (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Write-HB($Status, $TaskId, $Message) {
@"
# AAYS Safe Continue Bridge Lite

Time: $(Stamp)
Status: $Status
TaskId: $TaskId
BridgeRoot: $Root
Message: $Message
Mode: allowlist-only-lite
AllowedActions: status_check, git_sync_check, heartbeat_push, artifact_collect

Safety:
- migration_apply=blocked
- prod_deploy=blocked
- arbitrary_script_execution=blocked
- secret_write_update=blocked
- production_db_write_ddl_index=blocked
"@ | Set-Content -Encoding UTF8 "$HeartbeatDir\safe-continue-bridge.md"
}

function Push-Safe($Message) {
  git add ai-heartbeat ai-results ai-tasks 2>$null
  git commit -m $Message 2>$null
  git pull --rebase --autostash origin main 2>$null
  git push origin main 2>$null
}

function Write-Result($TaskId, $Obj) {
  $Obj | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 "$ResultsDir\$TaskId.result.json"
}

Write-HB "started" "none" "lite bridge started"
Push-Safe "Start safe bridge lite"

while ($true) {
  try {
    Set-Location $Root
    git pull --rebase --autostash origin main 2>$null | Out-Null

    $TaskFile = "$TasksDir\current-task.json"
    if (-not (Test-Path $TaskFile)) {
      Write-HB "polling" "none" "current-task missing"
      Push-Safe "Update safe bridge lite heartbeat"
      Start-Sleep -Seconds 30
      continue
    }

    $task = Get-Content $TaskFile -Raw | ConvertFrom-Json
    $taskId = [string]$task.id
    $action = [string]$task.action

    $last = ""
    if (Test-Path $LastTaskFile) {
      $last = (Get-Content $LastTaskFile -Raw).Trim()
    }

    if ([string]::IsNullOrWhiteSpace($taskId) -or $taskId -eq $last) {
      Write-HB "polling" $taskId "no new task"
      Push-Safe "Update safe bridge lite polling"
      Start-Sleep -Seconds 30
      continue
    }

    Write-HB "running" $taskId "action=$action"

    switch ($action) {
      "status_check" {
        $ps = Get-Process powershell -ErrorAction SilentlyContinue |
          Select-Object Id, ProcessName, MainWindowTitle

        Write-Result $taskId ([ordered]@{
          task_id = $taskId
          action = $action
          time_utc = Stamp
          bridge_root = $Root
          powershell_process_count = @($ps).Count
          powershell_processes = @($ps)
          git_status = @(git status --short)
          safety = @{
            migration_apply = "blocked"
            prod_deploy = "blocked"
            secret_write_update = "blocked"
            production_db_write_ddl_index = "blocked"
          }
        })
      }

      "git_sync_check" {
        Write-Result $taskId ([ordered]@{
          task_id = $taskId
          action = $action
          time_utc = Stamp
          status_output = @(git status --short 2>&1)
        })
      }

      "heartbeat_push" {
        Write-Result $taskId ([ordered]@{
          task_id = $taskId
          action = $action
          time_utc = Stamp
          status = "ok"
        })
      }

      "artifact_collect" {
        Write-Result $taskId ([ordered]@{
          task_id = $taskId
          action = $action
          time_utc = Stamp
          latest_results = @(Get-ChildItem $ResultsDir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 30 FullName,Length,LastWriteTime)
          heartbeat_files = @(Get-ChildItem $HeartbeatDir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 20 FullName,Length,LastWriteTime)
        })
      }

      default {
        Write-Result $taskId ([ordered]@{
          task_id = $taskId
          action = $action
          status = "BLOCKED_BY_ACTION_NOT_ALLOWED"
          allowed_actions = @("status_check","git_sync_check","heartbeat_push","artifact_collect")
          time_utc = Stamp
        })
      }
    }

    Set-Content -Encoding UTF8 -Path $LastTaskFile -Value $taskId
    Write-HB "finished" $taskId "action=$action"
    Push-Safe "Complete safe bridge lite task $taskId"
  } catch {
    Write-HB "error" "unknown" $_.Exception.Message
    Push-Safe "Update safe bridge lite error"
  }

  Start-Sleep -Seconds 30
}

$ErrorActionPreference = "Stop"

$RepoRoot = "F:\chatgpt\chat_gpt_clone_1_main"
$BridgeRoot = "F:\AAYS_GITHUB_BRIDGE_CLEAN2"
$PageKey = "aays1"
$WatchRepo = "F:\chatgpt\aays1_repo_to_bridge_watch_worktree"
$WatchBranch = "aays1-repo-to-bridge-watch"
$SleepSeconds = 60
$RepoHeartbeatSeconds = 60

if (!(Test-Path $RepoRoot)) { throw "Repo root not found: $RepoRoot" }
if (!(Test-Path $BridgeRoot)) { throw "Bridge root not found: $BridgeRoot" }

$ScriptDir = Join-Path $BridgeRoot "ai-task-scripts"
$StateDir = Join-Path $BridgeRoot "state\repo_to_bridge_watch\$PageKey"
$WatcherPath = Join-Path $ScriptDir "aays_repo_to_bridge_watch_$PageKey.ps1"
New-Item -ItemType Directory -Force -Path $ScriptDir,$StateDir | Out-Null

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'aays_repo_to_bridge_watch_aays1\.ps1' -or $_.CommandLine -match 'portable_queue_runner\.ps1' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

Start-Sleep -Seconds 2

git -C $RepoRoot fetch origin main
if ($LASTEXITCODE -ne 0) { throw "git fetch origin main failed from $RepoRoot" }

if (!(Test-Path "$WatchRepo\.git")) {
  if (Test-Path $WatchRepo) { Remove-Item -Recurse -Force $WatchRepo }
  git -C $RepoRoot worktree add -B $WatchBranch $WatchRepo origin/main
  if ($LASTEXITCODE -ne 0) { throw "watch worktree add failed" }
} else {
  git -C $WatchRepo fetch origin main
  git -C $WatchRepo reset --hard origin/main
}

$Watcher = @'
$ErrorActionPreference = "Continue"

$RepoRoot = "F:\chatgpt\chat_gpt_clone_1_main"
$BridgeRoot = "F:\AAYS_GITHUB_BRIDGE_CLEAN2"
$PageKey = "aays1"
$WatchRepo = "F:\chatgpt\aays1_repo_to_bridge_watch_worktree"
$SleepSeconds = 60
$RepoHeartbeatSeconds = 60

$StateDir = Join-Path $BridgeRoot "state\repo_to_bridge_watch\$PageKey"
$PendingDir = Join-Path $BridgeRoot "ai-queue\pending"
$QueueDir = Join-Path $WatchRepo "docs\chatgpt_status\$PageKey\queue"
$RunnerScript = Join-Path $BridgeRoot "ai-task-scripts\portable_queue_runner.ps1"
New-Item -ItemType Directory -Force -Path $StateDir,$PendingDir | Out-Null

function CopyRepoControlToActiveRepo {
  $items = @("automation","queue","control")
  foreach ($item in $items) {
    $src = Join-Path $WatchRepo "docs\chatgpt_status\$PageKey\$item"
    $dst = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\$item"
    if (Test-Path $src) {
      New-Item -ItemType Directory -Force -Path $dst | Out-Null
      Copy-Item -Recurse -Force (Join-Path $src "*") $dst -ErrorAction SilentlyContinue
    }
  }
}

function TaskIdFromFile($path) {
  try {
    $j = Get-Content $path -Raw | ConvertFrom-Json
    if ($j.task_id) { return [string]$j.task_id }
  } catch {}
  return [IO.Path]::GetFileNameWithoutExtension($path)
}

function TaskKnown($taskId) {
  foreach ($sub in @("pending","running","done","failed","processed","error")) {
    $dir = Join-Path $BridgeRoot "ai-queue\$sub"
    if (Test-Path $dir) {
      $hit = Get-ChildItem $dir -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*$taskId*" } | Select-Object -First 1
      if ($hit) { return $true }
    }
  }
  $marker = Join-Path $StateDir ("copied_" + ($taskId -replace '[^A-Za-z0-9_.-]','_') + ".txt")
  return (Test-Path $marker)
}

function EnsureRunner {
  $running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' } | Select-Object -First 1
  if (!$running -and (Test-Path $RunnerScript)) {
    Start-Process powershell -ArgumentList "-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-File",$RunnerScript
  }
}

function PushRepoStatus($text) {
  try {
    $now = Get-Date
    $lastPath = Join-Path $StateDir "last_repo_heartbeat_push.txt"
    $shouldPush = $true
    if (Test-Path $lastPath) {
      try {
        $last = [datetime](Get-Content $lastPath -Raw)
        if (($now - $last).TotalSeconds -lt $RepoHeartbeatSeconds) { $shouldPush = $false }
      } catch { $shouldPush = $true }
    }
    if (!$shouldPush) { return }

    git -C $WatchRepo fetch origin main | Out-Null
    git -C $WatchRepo reset --hard origin/main | Out-Null
    $statusDir = Join-Path $WatchRepo "docs\chatgpt_status\$PageKey\status"
    New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
    $repoStatus = Join-Path $statusDir "061_repo_to_bridge_watch_heartbeat_latest.txt"
    $text | Set-Content -Encoding UTF8 $repoStatus
    git -C $WatchRepo add -- "docs/chatgpt_status/$PageKey/status/061_repo_to_bridge_watch_heartbeat_latest.txt" | Out-Null
    $changes = git -C $WatchRepo status --porcelain -- "docs/chatgpt_status/$PageKey/status/061_repo_to_bridge_watch_heartbeat_latest.txt"
    if ($changes) {
      git -C $WatchRepo commit -m "Update aays1 repo-to-bridge watcher heartbeat" | Out-Null
      git -C $WatchRepo pull --rebase origin main | Out-Null
      git -C $WatchRepo push origin HEAD:main | Out-Null
    }
    $now.ToString("o") | Set-Content -Encoding UTF8 $lastPath
  } catch {
    "heartbeat_push_error=$($_.Exception.Message)" | Set-Content -Encoding UTF8 (Join-Path $StateDir "last_push_error.txt")
  }
}

while ($true) {
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $copied = 0
  try {
    git -C $WatchRepo fetch origin main | Out-Null
    git -C $WatchRepo reset --hard origin/main | Out-Null
    CopyRepoControlToActiveRepo

    if (Test-Path $QueueDir) {
      Get-ChildItem $QueueDir -File -Filter "*.task.json" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | ForEach-Object {
        $taskId = TaskIdFromFile $_.FullName
        if (!(TaskKnown $taskId)) {
          $dest = Join-Path $PendingDir $_.Name
          Copy-Item -Force $_.FullName $dest
          $marker = Join-Path $StateDir ("copied_" + ($taskId -replace '[^A-Za-z0-9_.-]','_') + ".txt")
          "copied_at=$stamp`nsource=$($_.FullName)`ndest=$dest`ntask_id=$taskId" | Set-Content -Encoding UTF8 $marker
          $copied += 1
        }
      }
    }

    EnsureRunner
    $hb = "status=WATCHING`npage_key=$PageKey`nrepo_root=$RepoRoot`nwatch_repo=$WatchRepo`nbridge_root=$BridgeRoot`nqueue_dir=$QueueDir`nbridge_pending=$PendingDir`ncopied_this_loop=$copied`nupdated_at=$stamp`nfinal_ready=false"
    $hb | Set-Content -Encoding UTF8 (Join-Path $StateDir "heartbeat.txt")
    PushRepoStatus $hb
  } catch {
    $err = "status=WATCH_ERROR`npage_key=$PageKey`nerror=$($_.Exception.Message)`nupdated_at=$stamp`nfinal_ready=false"
    $err | Set-Content -Encoding UTF8 (Join-Path $StateDir "last_error.txt")
    PushRepoStatus $err
  }
  Start-Sleep -Seconds $SleepSeconds
}
'@

$Watcher | Set-Content -Encoding UTF8 $WatcherPath

Start-Process powershell -ArgumentList "-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-File",$WatcherPath

$installed = "status=REPO_TO_BRIDGE_WATCH_INSTALLER_RAN`nfinal_ready=false`nwatcher_path=$WatcherPath`nwatch_repo=$WatchRepo`nbridge_root=$BridgeRoot`nrepo_root=$RepoRoot`npage_key=$PageKey`nupdated_at=$(Get-Date -Format yyyyMMdd_HHmmss)"
$installed | Set-Content -Encoding UTF8 (Join-Path $StateDir "installer_ran.txt")

Write-Host "Repo-to-bridge watcher clean-worktree installer ran." -ForegroundColor Green
Write-Host "Wait 90 seconds, then type devam." -ForegroundColor Cyan
exit 0

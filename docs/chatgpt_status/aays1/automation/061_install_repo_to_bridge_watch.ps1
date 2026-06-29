$ErrorActionPreference = "Stop"

param(
  [string]$RepoRoot = "F:\chatgpt\chat_gpt_clone_1_main",
  [string]$BridgeRoot = "F:\AAYS_GITHUB_BRIDGE_CLEAN2",
  [string]$PageKey = "aays1",
  [int]$SleepSeconds = 60,
  [int]$RepoHeartbeatSeconds = 300
)

$ScriptDir = Join-Path $BridgeRoot "ai-task-scripts"
$StateDir = Join-Path $BridgeRoot "state\repo_to_bridge_watch\$PageKey"
$WatcherPath = Join-Path $ScriptDir "aays_repo_to_bridge_watch_$PageKey.ps1"
New-Item -ItemType Directory -Force -Path $ScriptDir,$StateDir | Out-Null

$Watcher = @'
$ErrorActionPreference = "Continue"
param(
  [string]$RepoRoot = "F:\chatgpt\chat_gpt_clone_1_main",
  [string]$BridgeRoot = "F:\AAYS_GITHUB_BRIDGE_CLEAN2",
  [string]$PageKey = "aays1",
  [int]$SleepSeconds = 60,
  [int]$RepoHeartbeatSeconds = 300
)

$StateDir = Join-Path $BridgeRoot "state\repo_to_bridge_watch\$PageKey"
$PendingDir = Join-Path $BridgeRoot "ai-queue\pending"
$QueueDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\queue"
$RunnerScript = Join-Path $BridgeRoot "ai-task-scripts\portable_queue_runner.ps1"
New-Item -ItemType Directory -Force -Path $StateDir,$PendingDir | Out-Null

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

function EnsureRunner() {
  $running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' } | Select-Object -First 1
  if (!$running -and (Test-Path $RunnerScript)) {
    Start-Process powershell -ArgumentList "-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-File",$RunnerScript
  }
}

function PublishRepoHeartbeat($text) {
  try {
    if (!(Test-Path $RepoRoot)) { return }
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

    Set-Location $RepoRoot
    $statusDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
    New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
    $repoStatus = Join-Path $statusDir "061_repo_to_bridge_watch_heartbeat_latest.txt"
    $text | Set-Content -Encoding UTF8 $repoStatus
    git add -- "docs/chatgpt_status/$PageKey/status/061_repo_to_bridge_watch_heartbeat_latest.txt" | Out-Null
    $changes = git status --porcelain -- "docs/chatgpt_status/$PageKey/status/061_repo_to_bridge_watch_heartbeat_latest.txt"
    if ($changes) {
      git commit -m "Update aays1 repo-to-bridge watcher heartbeat" | Out-Null
      git pull --rebase origin main | Out-Null
      git push origin HEAD:main | Out-Null
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
    if (Test-Path $RepoRoot) {
      Set-Location $RepoRoot
      git fetch origin main | Out-Null
      git pull --ff-only origin main | Out-Null
    }

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
    $hb = "status=WATCHING`npage_key=$PageKey`nrepo_root=$RepoRoot`nbridge_root=$BridgeRoot`nqueue_dir=$QueueDir`nbridge_pending=$PendingDir`ncopied_this_loop=$copied`nupdated_at=$stamp`nfinal_ready=false"
    $hb | Set-Content -Encoding UTF8 (Join-Path $StateDir "heartbeat.txt")
    PublishRepoHeartbeat $hb
  } catch {
    $err = "status=WATCH_ERROR`npage_key=$PageKey`nerror=$($_.Exception.Message)`nupdated_at=$stamp`nfinal_ready=false"
    $err | Set-Content -Encoding UTF8 (Join-Path $StateDir "last_error.txt")
    PublishRepoHeartbeat $err
  }
  Start-Sleep -Seconds $SleepSeconds
}
'@

$Watcher | Set-Content -Encoding UTF8 $WatcherPath

$already = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match [regex]::Escape($WatcherPath) } | Select-Object -First 1
if (!$already) {
  Start-Process powershell -ArgumentList "-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-File",$WatcherPath,"-RepoRoot",$RepoRoot,"-BridgeRoot",$BridgeRoot,"-PageKey",$PageKey,"-SleepSeconds",$SleepSeconds,"-RepoHeartbeatSeconds",$RepoHeartbeatSeconds
}

$StatusDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$statusText = "status=REPO_TO_BRIDGE_WATCH_INSTALLED`nfinal_ready=false`nwatcher_path=$WatcherPath`nbridge_root=$BridgeRoot`nrepo_root=$RepoRoot`npage_key=$PageKey`nupdated_at=$stamp"
$statusText | Set-Content -Encoding UTF8 (Join-Path $StatusDir "061_repo_to_bridge_watch_installed_latest.txt")

try {
  Set-Location $RepoRoot
  git add -- "docs/chatgpt_status/$PageKey/status/061_repo_to_bridge_watch_installed_latest.txt"
  git commit -m "Record aays1 repo-to-bridge watcher install" | Out-Null
  git pull --rebase origin main | Out-Null
  git push origin HEAD:main | Out-Null
} catch {}

Write-Host "Repo-to-bridge watcher installed and started: $WatcherPath" -ForegroundColor Green
Write-Host "From now on, GitHub queue task files will be copied into the bridge pending queue." -ForegroundColor Cyan
exit 0

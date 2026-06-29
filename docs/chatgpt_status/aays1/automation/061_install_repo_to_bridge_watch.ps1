$ErrorActionPreference = "Stop"

param(
  [string]$RepoRoot = "F:\chatgpt\chat_gpt_clone_1_main",
  [string]$BridgeRoot = "F:\AAYS_GITHUB_BRIDGE_CLEAN2",
  [string]$PageKey = "aays1",
  [int]$SleepSeconds = 60
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
  [int]$SleepSeconds = 60
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

while ($true) {
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
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
        }
      }
    }

    EnsureRunner
    "status=WATCHING`npage_key=$PageKey`nrepo_root=$RepoRoot`nbridge_root=$BridgeRoot`nqueue_dir=$QueueDir`nupdated_at=$stamp" | Set-Content -Encoding UTF8 (Join-Path $StateDir "heartbeat.txt")
  } catch {
    "status=WATCH_ERROR`npage_key=$PageKey`nerror=$($_.Exception.Message)`nupdated_at=$stamp" | Set-Content -Encoding UTF8 (Join-Path $StateDir "last_error.txt")
  }
  Start-Sleep -Seconds $SleepSeconds
}
'@

$Watcher | Set-Content -Encoding UTF8 $WatcherPath

$already = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match [regex]::Escape($WatcherPath) } | Select-Object -First 1
if (!$already) {
  Start-Process powershell -ArgumentList "-NoExit","-NoProfile","-ExecutionPolicy","Bypass","-File",$WatcherPath,"-RepoRoot",$RepoRoot,"-BridgeRoot",$BridgeRoot,"-PageKey",$PageKey,"-SleepSeconds",$SleepSeconds
}

$StatusDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
New-Item -ItemType Directory -Force -Path $StatusDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
"status=REPO_TO_BRIDGE_WATCH_INSTALLED`nfinal_ready=false`nwatcher_path=$WatcherPath`nbridge_root=$BridgeRoot`nrepo_root=$RepoRoot`npage_key=$PageKey`nupdated_at=$stamp" | Set-Content -Encoding UTF8 (Join-Path $StatusDir "061_repo_to_bridge_watch_installed_$stamp.txt")

Write-Host "Repo-to-bridge watcher installed and started: $WatcherPath" -ForegroundColor Green
Write-Host "From now on, GitHub queue task files will be copied into the bridge pending queue." -ForegroundColor Cyan
exit 0

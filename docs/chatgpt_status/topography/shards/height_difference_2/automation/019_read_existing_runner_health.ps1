[CmdletBinding()]
param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$BridgeRoot = 'F:\AAYS_GITHUB_BRIDGE_CLEAN2',
  [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
if (-not $RepoRoot) { throw 'AAYS_REPO_ROOT is required' }
if (-not $OutputPath) {
  $OutputPath = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_2\runner_outputs\009_existing_runner_health_readback_latest.json'
}

$watcher = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'aays_repo_to_bridge_watch_aays1\.ps1' } |
  Select-Object ProcessId,Name,CommandLine

$runner = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' } |
  Select-Object ProcessId,Name,CommandLine

$watcherHeartbeat = Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1\heartbeat.txt'
$pendingDir = Join-Path $BridgeRoot 'ai-queue\pending'
$runningDir = Join-Path $BridgeRoot 'ai-queue\running'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'

function Find-TaskMarker([string]$Dir) {
  if (!(Test-Path -LiteralPath $Dir)) { return @() }
  return @(Get-ChildItem -LiteralPath $Dir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "*$taskId*" } |
    Select-Object -ExpandProperty FullName)
}

$payload = [ordered]@{
  schema_version = 1
  slot_id = 'height_difference_2'
  task_id = $taskId
  captured_at = (Get-Date).ToString('o')
  watcher_process_count = @($watcher).Count
  runner_process_count = @($runner).Count
  watcher_processes = @($watcher)
  runner_processes = @($runner)
  watcher_heartbeat_path = $watcherHeartbeat
  watcher_heartbeat_exists = (Test-Path -LiteralPath $watcherHeartbeat)
  bridge_pending_dir_exists = (Test-Path -LiteralPath $pendingDir)
  bridge_running_dir_exists = (Test-Path -LiteralPath $runningDir)
  pending_task_markers = @(Find-TaskMarker $pendingDir)
  running_task_markers = @(Find-TaskMarker $runningDir)
  read_only = $true
  process_started = $false
  process_stopped = $false
  queue_modified = $false
  new_runner = $false
  parallel_runner = $false
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}

$parent = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $parent | Out-Null
$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Output ($payload | ConvertTo-Json -Depth 8)

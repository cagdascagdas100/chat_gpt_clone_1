[CmdletBinding()]
param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$BridgeRoot = 'F:\AAYS_GITHUB_BRIDGE_CLEAN2',
  [string]$SourceBranch = 'codex/aays-single-runner-v5-20260706',
  [string]$WatchRepo = 'F:\chatgpt\aays1_repo_to_bridge_watch_worktree',
  [switch]$Apply,
  [switch]$RestoreRunner,
  [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$TaskId = 'height-difference-1-official-boundary-elevation-samples-20260720'
$QueueRel = 'docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json'
$TopographyQueueRel = 'docs/chatgpt_status/topography/queue/height_difference_1_004_official_boundary_numeric_samples_20260720.v3.task.json'
$MetricScriptRel = 'docs/chatgpt_status/topography/shards/height_difference_1/automation/013_height_difference_1_revision_9_height_difference_metric_20260721.py'
$Revision8EntryRel = 'docs/chatgpt_status/topography/shards/height_difference_1/automation/012_height_difference_1_revision_8_entry_20260721.py'
$Revision8PayloadRel = 'docs/chatgpt_status/topography/shards/height_difference_1/automation/011_height_difference_1_revision_8_geometry_datum_quality_gate_20260721.py.gz.b64'
$Revision7EntryRel = 'docs/chatgpt_status/topography/shards/height_difference_1/automation/010_height_difference_1_revision_7_bulk_gml_gate_20260721.py'
$TaskAssetDirs = @(
  'docs/chatgpt_status/topography/shards/height_difference_1/automation',
  'docs/chatgpt_status/topography/shards/height_difference_1/validation'
)
$TaskQueueFiles = @($QueueRel, $TopographyQueueRel)
$RequiredFiles = @($QueueRel, $TopographyQueueRel, $MetricScriptRel, $Revision8EntryRel, $Revision8PayloadRel, $Revision7EntryRel)
$RunnerScript = Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1'
$WatcherScript = Join-Path $BridgeRoot 'ai-task-scripts\aays_repo_to_bridge_watch_aays1.ps1'
$StateDir = Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1'
$RunningDir = Join-Path $BridgeRoot 'ai-queue\running'
$PendingDir = Join-Path $BridgeRoot 'ai-queue\pending'
if (-not $OutputPath) {
  $OutputPath = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\015_existing_watcher_exact_task_recovery_preflight_latest.json'
}

function Invoke-Git([string[]]$Args, [string]$Cwd = $RepoRoot) {
  $result = & git -C $Cwd @Args 2>&1
  if ($LASTEXITCODE -ne 0) { throw "git failed: git -C $Cwd $($Args -join ' ')`n$result" }
  return @($result)
}
function Test-GitPath([string]$Ref, [string]$Path) {
  & git -C $RepoRoot cat-file -e "$Ref`:$Path" 2>$null
  return ($LASTEXITCODE -eq 0)
}
function Get-Watchers {
  return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'aays_repo_to_bridge_watch_aays1\.ps1' } |
    Select-Object ProcessId,Name,CommandLine)
}
function Get-Runners {
  return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' } |
    Select-Object ProcessId,Name,CommandLine)
}
function Read-StrictTaskId([string]$Path) {
  try {
    $json = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($json.task_id) { return [string]$json.task_id }
  } catch {}
  return $null
}
function Emit([System.Collections.IDictionary]$Payload) {
  $Payload.output_path = $OutputPath
  $Payload.final_ready = $false
  $Payload.product_final_ready = $false
  $Payload.fake_data = $false
  $Payload.db_write = $false
  $Payload.migration = $false
  $Payload.production_deploy = $false
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
  $Payload | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
  Write-Output ($Payload | ConvertTo-Json -Depth 16)
}

if (!(Test-Path -LiteralPath $RepoRoot)) { throw "Repo root not found: $RepoRoot" }
if (!(Test-Path -LiteralPath $BridgeRoot)) { throw "Bridge root not found: $BridgeRoot" }
Invoke-Git @('fetch','origin',$SourceBranch) | Out-Null
$SourceRef = "origin/$SourceBranch"
$RequiredPresence = [ordered]@{}
foreach ($Rel in $RequiredFiles) { $RequiredPresence[$Rel] = Test-GitPath $SourceRef $Rel }
$WatcherProcesses = @(Get-Watchers)
$RunnerProcesses = @(Get-Runners)
$RunningFiles = if (Test-Path -LiteralPath $RunningDir) { @(Get-ChildItem -LiteralPath $RunningDir -File -ErrorAction SilentlyContinue) } else { @() }
$RunningTaskIds = @($RunningFiles | ForEach-Object { Read-StrictTaskId $_.FullName } | Where-Object { $_ })
$Blockers = @()
foreach ($Rel in $RequiredFiles) { if (!$RequiredPresence[$Rel]) { $Blockers += "SOURCE_ASSET_MISSING:$Rel" } }
if ($WatcherProcesses.Count -gt 1) { $Blockers += 'MULTIPLE_WATCHER_PROCESSES_DETECTED' }
if ($RunnerProcesses.Count -gt 1) { $Blockers += 'MULTIPLE_RUNNER_PROCESSES_DETECTED' }
if ($RunningFiles.Count -gt 0) { $Blockers += 'BRIDGE_RUNNING_TASK_PRESENT_RECOVERY_DEFERRED' }
if ($RestoreRunner -and !(Test-Path -LiteralPath $RunnerScript)) { $Blockers += 'CANONICAL_RUNNER_SCRIPT_MISSING' }

$Preflight = [ordered]@{
  schema_version = 3
  slot_id = 'height_difference_1'
  task_id = $TaskId
  source_branch = $SourceBranch
  source_ref = $SourceRef
  apply_requested = [bool]$Apply
  restore_existing_runner_requested = [bool]$RestoreRunner
  required_source_assets = $RequiredPresence
  watcher_process_count = $WatcherProcesses.Count
  runner_process_count = $RunnerProcesses.Count
  bridge_running_file_count = $RunningFiles.Count
  bridge_running_task_ids = $RunningTaskIds
  blockers = $Blockers
  exact_task_filter_required = $true
  strict_json_task_id_required = $true
  active_asset_post_sync_verification_required = $true
  remote_source_heartbeat_verification_required = $true
  shared_control_sync_forbidden = $true
  queue_only_main_mirror_forbidden = $true
  existing_runner_stop_forbidden = $true
  new_runner = $false
  parallel_runner = $false
}
if ($Blockers.Count -gt 0) { $Preflight.status = 'BLOCKED_EXACT_TASK_RECOVERY_PREFLIGHT'; Emit $Preflight; exit 2 }
if (!$Apply) {
  $Preflight.status = 'READY_FOR_EXACT_TASK_RECOVERY_APPLY'
  $Preflight.required_command = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Apply"
  $Preflight.restore_runner_command = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Apply -RestoreRunner"
  Emit $Preflight
  exit 0
}

# Stop only the existing watcher. Never stop the portable runner.
foreach ($Process in $WatcherProcesses) { Stop-Process -Id $Process.ProcessId -Force }
Start-Sleep -Seconds 2
if (!(Test-Path -LiteralPath $WatchRepo)) {
  Invoke-Git @('worktree','add','--detach',$WatchRepo,$SourceRef) | Out-Null
} else {
  Invoke-Git @('fetch','origin',$SourceBranch) $WatchRepo | Out-Null
  Invoke-Git @('reset','--hard',$SourceRef) $WatchRepo | Out-Null
}

$RestoreLiteral = if ($RestoreRunner) { '$true' } else { '$false' }
$AssetDirsLiteral = ($TaskAssetDirs | ForEach-Object { "'$_'" }) -join ','
$QueueFilesLiteral = ($TaskQueueFiles | ForEach-Object { "'$_'" }) -join ','
$RequiredFilesLiteral = ($RequiredFiles | ForEach-Object { "'$_'" }) -join ','
$Template = @'
$ErrorActionPreference = 'Continue'
$RepoRoot = '__REPO_ROOT__'
$BridgeRoot = '__BRIDGE_ROOT__'
$WatchRepo = '__WATCH_REPO__'
$SourceBranch = '__SOURCE_BRANCH__'
$RestoreRunner = __RESTORE_RUNNER__
$TaskId = '__TASK_ID__'
$TaskAssetDirs = @(__ASSET_DIRS__)
$TaskQueueFiles = @(__QUEUE_FILES__)
$RequiredFiles = @(__REQUIRED_FILES__)
$StateDir = Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1'
$PendingDir = Join-Path $BridgeRoot 'ai-queue\pending'
$QueuePath = Join-Path $WatchRepo 'docs\chatgpt_status\aays1\queue\aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json'
$RunnerScript = Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1'
$HeartbeatRel = 'docs/chatgpt_status/aays1/status/061_repo_to_bridge_watch_heartbeat_latest.txt'
$HeartbeatPushSeconds = 300
New-Item -ItemType Directory -Force -Path $StateDir,$PendingDir | Out-Null

function StrictTaskId([string]$Path) {
  try {
    $j = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($j.task_id) { return [string]$j.task_id }
  } catch {}
  return $null
}
function KnownExactTask([string]$Id) {
  foreach ($state in @('pending','running','done','failed','processed','error')) {
    $dir = Join-Path $BridgeRoot "ai-queue\$state"
    if (Test-Path -LiteralPath $dir) {
      foreach ($file in @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue)) {
        if ((StrictTaskId $file.FullName) -eq $Id) { return $true }
      }
    }
  }
  return $false
}
function SyncDirectory([string]$Rel) {
  $src = Join-Path $WatchRepo ($Rel -replace '/','\')
  $dst = Join-Path $RepoRoot ($Rel -replace '/','\')
  if (!(Test-Path -LiteralPath $src)) { throw "SOURCE_DIRECTORY_MISSING:$Rel" }
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  Copy-Item -Recurse -Force -ErrorAction Stop (Join-Path $src '*') $dst
}
function SyncFile([string]$Rel) {
  $src = Join-Path $WatchRepo ($Rel -replace '/','\')
  $dst = Join-Path $RepoRoot ($Rel -replace '/','\')
  if (!(Test-Path -LiteralPath $src)) { throw "SOURCE_FILE_MISSING:$Rel" }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
  Copy-Item -Force -ErrorAction Stop $src $dst
}
function AssertActiveAssets {
  foreach ($rel in $RequiredFiles) {
    $path = Join-Path $RepoRoot ($rel -replace '/','\')
    if (!(Test-Path -LiteralPath $path)) { throw "ACTIVE_ASSET_MISSING_AFTER_SYNC:$rel" }
  }
  $activeTaskId = StrictTaskId (Join-Path $RepoRoot ('docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json' -replace '/','\'))
  if ($activeTaskId -ne $TaskId) { throw "ACTIVE_QUEUE_TASK_ID_MISMATCH:$activeTaskId" }
}
function EnsureSingleRunner {
  $runners = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' })
  if ($runners.Count -gt 1) { throw 'MULTIPLE_RUNNER_PROCESSES_DETECTED' }
  if ($runners.Count -eq 0 -and $RestoreRunner) {
    if (!(Test-Path -LiteralPath $RunnerScript)) { throw 'CANONICAL_RUNNER_SCRIPT_MISSING' }
    Start-Process powershell -ArgumentList '-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File',$RunnerScript
  }
}
function WriteSourceHeartbeat([string]$Text) {
  $statusPath = Join-Path $WatchRepo ($HeartbeatRel -replace '/','\')
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $statusPath) | Out-Null
  $Text | Set-Content -LiteralPath $statusPath -Encoding UTF8
}
function PushSourceHeartbeat([string]$Text) {
  $lastPath = Join-Path $StateDir 'last_source_heartbeat_push.txt'
  $now = Get-Date
  if (Test-Path -LiteralPath $lastPath) {
    try {
      $last = [datetime](Get-Content -LiteralPath $lastPath -Raw)
      if (($now - $last).TotalSeconds -lt $HeartbeatPushSeconds) { return }
    } catch {}
  }
  for ($attempt = 1; $attempt -le 2; $attempt++) {
    git -C $WatchRepo fetch origin $SourceBranch | Out-Null
    git -C $WatchRepo reset --hard "origin/$SourceBranch" | Out-Null
    WriteSourceHeartbeat $Text
    git -C $WatchRepo add -- $HeartbeatRel | Out-Null
    $changes = git -C $WatchRepo status --porcelain -- $HeartbeatRel
    if (!$changes) { break }
    git -C $WatchRepo commit -m 'Update aays1 exact-task watcher heartbeat' | Out-Null
    git -C $WatchRepo push origin "HEAD:$SourceBranch" | Out-Null
    if ($LASTEXITCODE -eq 0) { break }
    if ($attempt -eq 2) { throw 'SOURCE_HEARTBEAT_PUSH_FAILED_AFTER_RETRY' }
  }
  $now.ToString('o') | Set-Content -LiteralPath $lastPath -Encoding UTF8
}

while ($true) {
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
  $copied = 0
  try {
    git -C $WatchRepo fetch origin $SourceBranch | Out-Null
    git -C $WatchRepo reset --hard "origin/$SourceBranch" | Out-Null
    foreach ($rel in $TaskAssetDirs) { SyncDirectory $rel }
    foreach ($rel in $TaskQueueFiles) { SyncFile $rel }
    AssertActiveAssets

    $queueTaskId = StrictTaskId $QueuePath
    if ($queueTaskId -ne $TaskId) { throw "WATCH_QUEUE_TASK_ID_MISMATCH:$queueTaskId" }
    if (!(KnownExactTask $TaskId)) {
      Copy-Item -Force -ErrorAction Stop $QueuePath (Join-Path $PendingDir ([IO.Path]::GetFileName($QueuePath)))
      $copied = 1
    }
    EnsureSingleRunner
    $hb = "status=WATCHING`npage_key=aays1`nsource_branch=$SourceBranch`nrepo_root=$RepoRoot`nwatch_repo=$WatchRepo`nbridge_root=$BridgeRoot`nbridge_pending=$PendingDir`ntask_id=$TaskId`nexact_task_filter=true`ncopied_this_loop=$copied`nupdated_at=$stamp`nfinal_ready=false"
    $hb | Set-Content -LiteralPath (Join-Path $StateDir 'heartbeat.txt') -Encoding UTF8
    PushSourceHeartbeat $hb
  } catch {
    $err = "status=WATCH_ERROR`npage_key=aays1`nsource_branch=$SourceBranch`ntask_id=$TaskId`nerror=$($_.Exception.Message)`nupdated_at=$stamp`nfinal_ready=false"
    $err | Set-Content -LiteralPath (Join-Path $StateDir 'last_error.txt') -Encoding UTF8
    try { PushSourceHeartbeat $err } catch {}
  }
  Start-Sleep -Seconds 60
}
'@

$WatcherText = $Template.Replace('__REPO_ROOT__',$RepoRoot).Replace('__BRIDGE_ROOT__',$BridgeRoot).Replace('__WATCH_REPO__',$WatchRepo).Replace('__SOURCE_BRANCH__',$SourceBranch).Replace('__RESTORE_RUNNER__',$RestoreLiteral).Replace('__TASK_ID__',$TaskId).Replace('__ASSET_DIRS__',$AssetDirsLiteral).Replace('__QUEUE_FILES__',$QueueFilesLiteral).Replace('__REQUIRED_FILES__',$RequiredFilesLiteral)
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $WatcherScript),$StateDir,$PendingDir | Out-Null
$WatcherText | Set-Content -LiteralPath $WatcherScript -Encoding UTF8
$Watcher = Start-Process powershell -ArgumentList '-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File',$WatcherScript -PassThru
$RunnerAfter = @(Get-Runners)
Emit ([ordered]@{
  schema_version = 3
  slot_id = 'height_difference_1'
  task_id = $TaskId
  status = if ($RunnerAfter.Count -eq 1) { 'EXACT_TASK_WATCHER_AND_EXISTING_SINGLE_RUNNER_RECOVERED' } else { 'EXACT_TASK_WATCHER_RECOVERED_EXISTING_RUNNER_RESTORE_PENDING' }
  source_branch = $SourceBranch
  watcher_process_id = $Watcher.Id
  runner_process_count = $RunnerAfter.Count
  watcher_script = $WatcherScript
  canonical_runner_script = $RunnerScript
  exact_task_filter = $true
  strict_json_task_id = $true
  active_asset_post_sync_verification = $true
  source_branch_heartbeat_retry = $true
  shared_control_synced = $false
  existing_runner_stopped = $false
  new_runner = $false
  parallel_runner = $false
})
exit 0

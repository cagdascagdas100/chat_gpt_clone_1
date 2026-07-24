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
$AutomationRel = 'docs/chatgpt_status/topography/shards/height_difference_1/automation/013_height_difference_1_revision_9_height_difference_metric_20260721.py'
$RunnerScript = Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1'
$WatcherScript = Join-Path $BridgeRoot 'ai-task-scripts\aays_repo_to_bridge_watch_aays1.ps1'
$StateDir = Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1'
$RunningDir = Join-Path $BridgeRoot 'ai-queue\running'
$PendingDir = Join-Path $BridgeRoot 'ai-queue\pending'
if (-not $OutputPath) {
  $OutputPath = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\012_existing_watcher_recovery_preflight_latest.json'
}

function Git([string[]]$Args, [string]$Cwd = $RepoRoot) {
  $result = & git -C $Cwd @Args 2>&1
  if ($LASTEXITCODE -ne 0) { throw "git failed: git -C $Cwd $($Args -join ' ')`n$result" }
  return @($result)
}
function GitPath([string]$Ref, [string]$Path) {
  & git -C $RepoRoot cat-file -e "$Ref`:$Path" 2>$null
  return ($LASTEXITCODE -eq 0)
}
function Watchers {
  return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'aays_repo_to_bridge_watch_aays1\.ps1' } | Select-Object ProcessId,Name,CommandLine)
}
function Runners {
  return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' } | Select-Object ProcessId,Name,CommandLine)
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
  $Payload | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
  Write-Output ($Payload | ConvertTo-Json -Depth 12)
}

if (!(Test-Path -LiteralPath $RepoRoot)) { throw "Repo root not found: $RepoRoot" }
if (!(Test-Path -LiteralPath $BridgeRoot)) { throw "Bridge root not found: $BridgeRoot" }
Git @('fetch','origin',$SourceBranch) | Out-Null
$SourceRef = "origin/$SourceBranch"
$QueueVisible = GitPath $SourceRef $QueueRel
$AutomationVisible = GitPath $SourceRef $AutomationRel
$WatcherProcesses = @(Watchers)
$RunnerProcesses = @(Runners)
$RunningFiles = if (Test-Path -LiteralPath $RunningDir) { @(Get-ChildItem -LiteralPath $RunningDir -File -ErrorAction SilentlyContinue) } else { @() }
$Blockers = @()
if (!$QueueVisible) { $Blockers += 'TASK_QUEUE_NOT_PRESENT_ON_SOURCE_BRANCH' }
if (!$AutomationVisible) { $Blockers += 'TASK_AUTOMATION_NOT_PRESENT_ON_SOURCE_BRANCH' }
if ($WatcherProcesses.Count -gt 1) { $Blockers += 'MULTIPLE_WATCHER_PROCESSES_DETECTED' }
if ($RunnerProcesses.Count -gt 1) { $Blockers += 'MULTIPLE_RUNNER_PROCESSES_DETECTED' }
if ($RunningFiles.Count -gt 0) { $Blockers += 'BRIDGE_RUNNING_TASK_PRESENT_RECOVERY_DEFERRED' }
if ($RestoreRunner -and !(Test-Path -LiteralPath $RunnerScript)) { $Blockers += 'CANONICAL_RUNNER_SCRIPT_MISSING' }

$Preflight = [ordered]@{
  schema_version = 1; slot_id = 'height_difference_1'; task_id = $TaskId
  source_branch = $SourceBranch; source_ref = $SourceRef
  apply_requested = [bool]$Apply; restore_runner_requested = [bool]$RestoreRunner
  queue_present_on_source_branch = $QueueVisible; automation_present_on_source_branch = $AutomationVisible
  watcher_process_count = $WatcherProcesses.Count; runner_process_count = $RunnerProcesses.Count
  bridge_running_file_count = $RunningFiles.Count; blockers = $Blockers
  queue_only_mirror_forbidden = $true; existing_runner_stop_forbidden = $true
  new_runner = $false; parallel_runner = $false
}
if ($Blockers.Count -gt 0) { $Preflight.status = 'BLOCKED_RECOVERY_PREFLIGHT'; Emit $Preflight; exit 2 }
if (!$Apply) {
  $Preflight.status = 'READY_FOR_OPERATOR_APPLY'
  $Preflight.required_command = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Apply"
  $Preflight.restore_runner_command = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Apply -RestoreRunner"
  Emit $Preflight
  exit 0
}

# Stop only the watcher. Never stop the portable runner.
foreach ($Process in $WatcherProcesses) { Stop-Process -Id $Process.ProcessId -Force }
Start-Sleep -Seconds 2
if (!(Test-Path -LiteralPath $WatchRepo)) {
  Git @('worktree','add','--detach',$WatchRepo,$SourceRef) | Out-Null
} else {
  Git @('fetch','origin',$SourceBranch) $WatchRepo | Out-Null
  Git @('reset','--hard',$SourceRef) $WatchRepo | Out-Null
}

$RestoreLiteral = if ($RestoreRunner) { '$true' } else { '$false' }
$Template = @'
$ErrorActionPreference = 'Continue'
$RepoRoot = '__REPO_ROOT__'
$BridgeRoot = '__BRIDGE_ROOT__'
$WatchRepo = '__WATCH_REPO__'
$SourceBranch = '__SOURCE_BRANCH__'
$RestoreRunner = __RESTORE_RUNNER__
$StateDir = Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1'
$PendingDir = Join-Path $BridgeRoot 'ai-queue\pending'
$QueueDir = Join-Path $WatchRepo 'docs\chatgpt_status\aays1\queue'
$RunnerScript = Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1'
New-Item -ItemType Directory -Force -Path $StateDir,$PendingDir | Out-Null
function TaskId([string]$Path) { try { $j = Get-Content $Path -Raw | ConvertFrom-Json; if ($j.task_id) { return [string]$j.task_id } } catch {}; return [IO.Path]::GetFileNameWithoutExtension($Path) }
function Known([string]$Id) { foreach ($s in @('pending','running','done','failed','processed','error')) { $d = Join-Path $BridgeRoot "ai-queue\$s"; if (Test-Path $d) { if (Get-ChildItem $d -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "*$Id*" } | Select-Object -First 1) { return $true } } }; return $false }
function EnsureSingleRunner { $r = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' }); if ($r.Count -gt 1) { throw 'MULTIPLE_RUNNER_PROCESSES_DETECTED' }; if ($r.Count -eq 0 -and $RestoreRunner -and (Test-Path $RunnerScript)) { Start-Process powershell -ArgumentList '-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File',$RunnerScript } }
while ($true) {
  $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'; $copied = 0
  try {
    git -C $WatchRepo fetch origin $SourceBranch | Out-Null
    git -C $WatchRepo reset --hard "origin/$SourceBranch" | Out-Null
    foreach ($item in @('automation','queue','control')) { $src = Join-Path $WatchRepo "docs\chatgpt_status\aays1\$item"; $dst = Join-Path $RepoRoot "docs\chatgpt_status\aays1\$item"; if (Test-Path $src) { New-Item -ItemType Directory -Force -Path $dst | Out-Null; Copy-Item -Recurse -Force (Join-Path $src '*') $dst -ErrorAction SilentlyContinue } }
    if (Test-Path $QueueDir) { Get-ChildItem $QueueDir -File -Filter '*.task.json' | Sort-Object LastWriteTime | ForEach-Object { $id = TaskId $_.FullName; if (!(Known $id)) { Copy-Item -Force $_.FullName (Join-Path $PendingDir $_.Name); $copied += 1 } } }
    EnsureSingleRunner
    "status=WATCHING`npage_key=aays1`nsource_branch=$SourceBranch`nrepo_root=$RepoRoot`nwatch_repo=$WatchRepo`nbridge_root=$BridgeRoot`nqueue_dir=$QueueDir`ncopied_this_loop=$copied`nupdated_at=$stamp`nfinal_ready=false" | Set-Content -LiteralPath (Join-Path $StateDir 'heartbeat.txt') -Encoding UTF8
  } catch { "status=WATCH_ERROR`npage_key=aays1`nsource_branch=$SourceBranch`nerror=$($_.Exception.Message)`nupdated_at=$stamp`nfinal_ready=false" | Set-Content -LiteralPath (Join-Path $StateDir 'last_error.txt') -Encoding UTF8 }
  Start-Sleep -Seconds 60
}
'@
$WatcherText = $Template.Replace('__REPO_ROOT__',$RepoRoot).Replace('__BRIDGE_ROOT__',$BridgeRoot).Replace('__WATCH_REPO__',$WatchRepo).Replace('__SOURCE_BRANCH__',$SourceBranch).Replace('__RESTORE_RUNNER__',$RestoreLiteral)
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $WatcherScript),$StateDir,$PendingDir | Out-Null
$WatcherText | Set-Content -LiteralPath $WatcherScript -Encoding UTF8
$Watcher = Start-Process powershell -ArgumentList '-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File',$WatcherScript -PassThru
$RunnerAfter = @(Runners)
Emit ([ordered]@{
  schema_version = 1; slot_id = 'height_difference_1'; task_id = $TaskId
  status = if ($RunnerAfter.Count -eq 1) { 'EXISTING_WATCHER_AND_SINGLE_RUNNER_RECOVERED' } else { 'WATCHER_RECOVERED_RUNNER_RESTORE_PENDING' }
  source_branch = $SourceBranch; watcher_process_id = $Watcher.Id; runner_process_count = $RunnerAfter.Count
  watcher_script = $WatcherScript; canonical_runner_script = $RunnerScript
  queue_present_on_source_branch = $QueueVisible; automation_present_on_source_branch = $AutomationVisible
  queue_only_mirror_forbidden = $true; existing_runner_stopped = $false
  new_runner = $false; parallel_runner = $false
})
exit 0

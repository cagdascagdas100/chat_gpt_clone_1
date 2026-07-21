[CmdletBinding()]
param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$BridgeRoot = 'F:\AAYS_GITHUB_BRIDGE_CLEAN2',
  [string]$SourceBranch = 'codex/aays-single-runner-v5-20260706',
  [int]$WaitSeconds = 120,
  [int]$PollSeconds = 5,
  [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$TaskId = 'height-difference-1-official-boundary-elevation-samples-20260720'
$WatcherHeartbeat = Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1\heartbeat.txt'
$SlotHeartbeat = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\slots_21\height_difference_1\heartbeat_latest.json'
$ExpectedOutput = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\011_height_difference_metric_gate_latest.json'
$WebOutput = Join-Path $RepoRoot 'england_map_web\data\aays_21_slots\height_difference_1\existing_watcher_complete_recovery_readback_latest.json'
$RequiredFiles = @(
  'docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json',
  'docs/chatgpt_status/topography/shards/height_difference_1/automation/013_height_difference_1_revision_9_height_difference_metric_20260721.py',
  'docs/chatgpt_status/topography/shards/height_difference_1/automation/012_height_difference_1_revision_8_entry_20260721.py',
  'docs/chatgpt_status/topography/shards/height_difference_1/automation/011_height_difference_1_revision_8_geometry_datum_quality_gate_20260721.py.gz.b64'
)
if (-not $OutputPath) {
  $OutputPath = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\014_existing_watcher_complete_recovery_readback_latest.json'
}

function Parse-Kv([string]$Path) {
  $result = @{}
  if (!(Test-Path -LiteralPath $Path)) { return $result }
  foreach ($line in (Get-Content -LiteralPath $Path -Encoding UTF8)) {
    if ($line -match '^\s*([^=]+)=(.*)$') { $result[$matches[1].Trim()] = $matches[2].Trim() }
  }
  return $result
}
function Parse-CompactTime([string]$Value) {
  if (!$Value) { return $null }
  try { return [datetime]::ParseExact($Value,'yyyyMMdd_HHmmss',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeLocal) } catch { return $null }
}
function TaskFileMatches([string]$Path,[string]$Id) {
  try { $j = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json; return ([string]$j.task_id -eq $Id) } catch { return ([IO.Path]::GetFileName($Path) -like "*$Id*") }
}
function Find-TaskMarkers([string]$Id) {
  $hits = @()
  foreach ($state in @('pending','running','done','failed','processed','error')) {
    $dir = Join-Path $BridgeRoot "ai-queue\$state"
    if (Test-Path -LiteralPath $dir) {
      foreach ($file in @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue)) {
        if (TaskFileMatches $file.FullName $Id) { $hits += [ordered]@{ state=$state; path=$file.FullName } }
      }
    }
  }
  return @($hits)
}
function Snapshot {
  $watchers = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'aays_repo_to_bridge_watch_aays1\.ps1' } | Select-Object ProcessId,Name,CommandLine)
  $runners = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' } | Select-Object ProcessId,Name,CommandLine)
  $hb = Parse-Kv $WatcherHeartbeat
  $hbTime = Parse-CompactTime ([string]$hb['updated_at'])
  $hbAge = if ($hbTime) { [math]::Max(0,[int]((Get-Date) - $hbTime).TotalSeconds) } else { $null }
  $required = [ordered]@{}
  foreach ($rel in $RequiredFiles) { $required[$rel] = Test-Path -LiteralPath (Join-Path $RepoRoot ($rel -replace '/','\')) }
  $slotObject = $null
  if (Test-Path -LiteralPath $SlotHeartbeat) { try { $slotObject = Get-Content -LiteralPath $SlotHeartbeat -Raw | ConvertFrom-Json } catch { $slotObject = $null } }
  $slotState = if ($slotObject) { [string]$slotObject.state } else { $null }
  $slotTask = if ($slotObject) { [string]$slotObject.current_task_id } else { $null }
  $markers = @(Find-TaskMarkers $TaskId)
  $allRequired = -not ($required.Values -contains $false)
  $watcherFresh = ($hbAge -ne $null -and $hbAge -le 180 -and [string]$hb['status'] -eq 'WATCHING')
  $sourceMatches = ([string]$hb['source_branch'] -eq $SourceBranch)
  $singleWatcher = ($watchers.Count -eq 1)
  $singleRunner = ($runners.Count -eq 1)
  $taskVisible = ($markers.Count -gt 0)
  $slotClaimed = ($slotTask -eq $TaskId -and $slotState -in @('claimed','running'))
  $resultPresent = Test-Path -LiteralPath $ExpectedOutput
  $status = if ($resultPresent) { 'OFFICIAL_RESULT_AVAILABLE' } elseif ($slotClaimed) { 'SINGLE_RUNNER_CLAIM_OBSERVED' } elseif ($singleWatcher -and $singleRunner -and $watcherFresh -and $sourceMatches -and $allRequired -and $taskVisible) { 'COMPLETE_RECOVERY_VERIFIED_TASK_VISIBLE' } else { 'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED' }
  return [ordered]@{
    schema_version = 1
    slot_id = 'height_difference_1'
    task_id = $TaskId
    checked_at = (Get-Date).ToString('o')
    status = $status
    watcher_process_count = $watchers.Count
    runner_process_count = $runners.Count
    watcher_heartbeat_path = $WatcherHeartbeat
    watcher_heartbeat_status = $hb['status']
    watcher_heartbeat_updated_at_raw = $hb['updated_at']
    watcher_heartbeat_age_seconds = $hbAge
    watcher_heartbeat_fresh = $watcherFresh
    watcher_source_branch = $hb['source_branch']
    expected_source_branch = $SourceBranch
    watcher_source_branch_matches = $sourceMatches
    required_active_repo_files = $required
    all_required_active_repo_files_present = $allRequired
    bridge_task_markers = $markers
    bridge_task_visible = $taskVisible
    slot_heartbeat_path = $SlotHeartbeat
    slot_state = $slotState
    slot_current_task_id = $slotTask
    slot_claimed_for_expected_task = $slotClaimed
    expected_output_path = $ExpectedOutput
    expected_output_present = $resultPresent
    process_started = $false
    process_stopped = $false
    queue_modified = $false
    new_runner = $false
    parallel_runner = $false
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
}

$deadline = (Get-Date).AddSeconds([math]::Max(0,$WaitSeconds))
do {
  $payload = Snapshot
  if ($payload.status -ne 'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED') { break }
  if ((Get-Date) -ge $deadline) { break }
  Start-Sleep -Seconds ([math]::Max(1,$PollSeconds))
} while ($true)
foreach ($path in @($OutputPath,$WebOutput)) {
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
  $payload | ConvertTo-Json -Depth 14 | Set-Content -LiteralPath $path -Encoding UTF8
}
Write-Output ($payload | ConvertTo-Json -Depth 14)
if ($payload.status -eq 'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED') { exit 2 }
exit 0

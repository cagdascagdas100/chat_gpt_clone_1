[CmdletBinding()]
param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$BridgeRoot = 'F:\AAYS_GITHUB_BRIDGE_CLEAN2',
  [string]$SourceBranch = 'codex/aays-single-runner-v5-20260706',
  [int]$WaitSeconds = 180,
  [int]$PollSeconds = 5,
  [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$TaskId = 'height-difference-1-official-boundary-elevation-samples-20260720'
$HeartbeatRel = 'docs/chatgpt_status/aays1/status/061_repo_to_bridge_watch_heartbeat_latest.txt'
$LocalWatcherHeartbeat = Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1\heartbeat.txt'
$SlotHeartbeat = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\slots_21\height_difference_1\heartbeat_latest.json'
$ExpectedOutput = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\011_height_difference_metric_gate_latest.json'
$WebOutput = Join-Path $RepoRoot 'england_map_web\data\aays_21_slots\height_difference_1\existing_watcher_exact_task_recovery_readback_latest.json'
$RequiredFiles = @(
  'docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json',
  'docs/chatgpt_status/topography/queue/height_difference_1_004_official_boundary_numeric_samples_20260720.v3.task.json',
  'docs/chatgpt_status/topography/shards/height_difference_1/automation/013_height_difference_1_revision_9_height_difference_metric_20260721.py',
  'docs/chatgpt_status/topography/shards/height_difference_1/automation/012_height_difference_1_revision_8_entry_20260721.py',
  'docs/chatgpt_status/topography/shards/height_difference_1/automation/011_height_difference_1_revision_8_geometry_datum_quality_gate_20260721.py.gz.b64',
  'docs/chatgpt_status/topography/shards/height_difference_1/automation/010_height_difference_1_revision_7_bulk_gml_gate_20260721.py'
)
if (-not $OutputPath) {
  $OutputPath = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\016_existing_watcher_exact_task_recovery_readback_latest.json'
}

function Parse-KvText([string]$Text) {
  $result = @{}
  foreach ($line in ($Text -split "`r?`n")) {
    if ($line -match '^\s*([^=]+)=(.*)$') { $result[$matches[1].Trim()] = $matches[2].Trim() }
  }
  return $result
}
function Parse-KvFile([string]$Path) {
  if (!(Test-Path -LiteralPath $Path)) { return @{} }
  return Parse-KvText (Get-Content -LiteralPath $Path -Raw -Encoding UTF8)
}
function Parse-CompactTime([string]$Value) {
  if (!$Value) { return $null }
  try { return [datetime]::ParseExact($Value,'yyyyMMdd_HHmmss',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeLocal) } catch { return $null }
}
function StrictTaskId([string]$Path) {
  try {
    $json = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($json.task_id) { return [string]$json.task_id }
  } catch {}
  return $null
}
function Find-ExactTaskMarkers([string]$Id) {
  $hits = @()
  foreach ($state in @('pending','running','done','failed','processed','error')) {
    $dir = Join-Path $BridgeRoot "ai-queue\$state"
    if (Test-Path -LiteralPath $dir) {
      foreach ($file in @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue)) {
        if ((StrictTaskId $file.FullName) -eq $Id) { $hits += [ordered]@{ state=$state; path=$file.FullName } }
      }
    }
  }
  return @($hits)
}
function Read-SlotHeartbeat {
  if (!(Test-Path -LiteralPath $SlotHeartbeat)) { return $null }
  try { return (Get-Content -LiteralPath $SlotHeartbeat -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { return $null }
}
function Read-RemoteHeartbeat {
  & git -C $RepoRoot fetch origin $SourceBranch 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { return @{} }
  $text = & git -C $RepoRoot show "origin/$SourceBranch`:$HeartbeatRel" 2>$null
  if ($LASTEXITCODE -ne 0) { return @{} }
  return Parse-KvText ($text -join "`n")
}
function HeartbeatFacts([hashtable]$Heartbeat) {
  $time = Parse-CompactTime ([string]$Heartbeat['updated_at'])
  $age = if ($time) { [math]::Max(0,[int]((Get-Date) - $time).TotalSeconds) } else { $null }
  return [ordered]@{
    status = $Heartbeat['status']
    updated_at_raw = $Heartbeat['updated_at']
    age_seconds = $age
    fresh = ($age -ne $null -and $age -le 180 -and [string]$Heartbeat['status'] -eq 'WATCHING')
    source_branch = $Heartbeat['source_branch']
    source_branch_matches = ([string]$Heartbeat['source_branch'] -eq $SourceBranch)
    task_id = $Heartbeat['task_id']
    task_id_matches = ([string]$Heartbeat['task_id'] -eq $TaskId)
    exact_task_filter = $Heartbeat['exact_task_filter']
  }
}
function Snapshot {
  $watchers = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'aays_repo_to_bridge_watch_aays1\.ps1' } |
    Select-Object ProcessId,Name,CommandLine)
  $runners = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' } |
    Select-Object ProcessId,Name,CommandLine)
  $localFacts = HeartbeatFacts (Parse-KvFile $LocalWatcherHeartbeat)
  $remoteFacts = HeartbeatFacts (Read-RemoteHeartbeat)
  $required = [ordered]@{}
  foreach ($rel in $RequiredFiles) { $required[$rel] = Test-Path -LiteralPath (Join-Path $RepoRoot ($rel -replace '/','\')) }
  $allRequired = -not ($required.Values -contains $false)
  $queuePath = Join-Path $RepoRoot ('docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json' -replace '/','\')
  $activeQueueTaskId = StrictTaskId $queuePath
  $activeQueueExact = ($activeQueueTaskId -eq $TaskId)
  $markers = @(Find-ExactTaskMarkers $TaskId)
  $slot = Read-SlotHeartbeat
  $slotState = if ($slot) { [string]$slot.state } else { $null }
  $slotTask = if ($slot) { [string]$slot.current_task_id } else { $null }
  $slotClaimed = ($slotTask -eq $TaskId -and $slotState -in @('claimed','running'))
  $resultPresent = Test-Path -LiteralPath $ExpectedOutput
  $completeRecovery = (
    $watchers.Count -eq 1 -and
    $runners.Count -eq 1 -and
    $localFacts.fresh -and $localFacts.source_branch_matches -and $localFacts.task_id_matches -and
    $remoteFacts.fresh -and $remoteFacts.source_branch_matches -and $remoteFacts.task_id_matches -and
    $allRequired -and $activeQueueExact -and $markers.Count -gt 0
  )
  $status = if ($resultPresent) {
    'OFFICIAL_RESULT_AVAILABLE'
  } elseif ($slotClaimed) {
    'SINGLE_RUNNER_CLAIM_OBSERVED'
  } elseif ($completeRecovery) {
    'EXACT_TASK_RECOVERY_VERIFIED_TASK_VISIBLE'
  } else {
    'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED'
  }
  return [ordered]@{
    schema_version = 2
    slot_id = 'height_difference_1'
    task_id = $TaskId
    checked_at = (Get-Date).ToString('o')
    status = $status
    watcher_process_count = $watchers.Count
    runner_process_count = $runners.Count
    local_watcher_heartbeat = $localFacts
    remote_source_branch_heartbeat = $remoteFacts
    required_active_repo_files = $required
    all_required_active_repo_files_present = $allRequired
    active_queue_task_id = $activeQueueTaskId
    active_queue_exact_task_match = $activeQueueExact
    bridge_exact_task_markers = $markers
    bridge_exact_task_visible = ($markers.Count -gt 0)
    slot_state = $slotState
    slot_current_task_id = $slotTask
    slot_claimed_for_expected_task = $slotClaimed
    expected_output_path = $ExpectedOutput
    expected_output_present = $resultPresent
    exact_task_filter_required = $true
    strict_json_task_id_required = $true
    remote_heartbeat_required = $true
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
  $payload | ConvertTo-Json -Depth 18 | Set-Content -LiteralPath $path -Encoding UTF8
}
Write-Output ($payload | ConvertTo-Json -Depth 18)
if ($payload.status -eq 'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED') { exit 2 }
exit 0

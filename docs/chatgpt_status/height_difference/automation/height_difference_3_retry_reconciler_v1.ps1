[CmdletBinding()]
param(
  [ValidateRange(0,1440)][int]$StaleRunningMinutes = 0,
  [ValidateRange(1,5)][int]$MaxRequeues = 3
)

$ErrorActionPreference = 'Stop'
$rawRoot = [string]$env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($rawRoot)) { throw 'AAYS_REPO_ROOT_REQUIRED' }
$root = [System.IO.Path]::GetFullPath($rawRoot)
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'AAYS_REPO_ROOT_NOT_FOUND' }

$slotId = 'height_difference_3'
$canonicalTaskId = 'height-difference-3-canonical-point-extract-v1-1-20260722'
$expectedBlob = 'bb48164e7a0af78df875f30421a6a3068c43edb8'
$templateRel = 'docs/chatgpt_status/height_difference/recovery/height_difference_3_priority2_task_template_latest.json'
$stateRel = 'docs/chatgpt_status/height_difference/recovery/height_difference_3_retry_state_latest.json'
$backupRel = 'docs/chatgpt_status/height_difference/recovery/height_difference_3_priority2_queue_backup_latest.json'
$queueRel = 'docs/chatgpt_status/aays1/queue/0002_000_height_difference_3_canonical_point_extract_v1_20260722.task.json'
$canonicalRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_canonical_points_latest.json'
$probeRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_epoch_provenance_probe_latest.json'
$watchdogRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_execution_watchdog_latest.json'
$chainRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_chain_orchestration_latest.json'
$runnerReportRel = "docs/chatgpt_status/aays1/reports/${canonicalTaskId}_runner_output.txt"
$completedRel = "docs/chatgpt_status/aays1/status/${canonicalTaskId}_completed.json"
$startedRel = "docs/chatgpt_status/aays1/status/${canonicalTaskId}_started.json"
$reportRel = 'docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_retry_reconciliation_latest.json'
$websiteReportRel = 'england_map_web/data/height_difference/height_difference_3_retry_reconciliation_latest.json'
$recoveryTaskRels = @(
  'docs/chatgpt_status/aays1/queue/0006_901_height_difference_3_retry_reconciler_01_20260722.task.json',
  'docs/chatgpt_status/aays1/queue/0006_902_height_difference_3_retry_reconciler_02_20260722.task.json',
  'docs/chatgpt_status/aays1/queue/0006_903_height_difference_3_retry_reconciler_03_20260722.task.json'
)

function Now-Utc { (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function Resolve-RepoPath([string]$Rel) { Join-Path $root ($Rel.Replace('/','\')) }
function Read-JsonOrNull([string]$Rel) {
  $path = Resolve-RepoPath $Rel
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return $null }
  try { return (Get-Content -LiteralPath $path -Raw | ConvertFrom-Json) } catch { return $null }
}
function Write-TextReplace([string]$Rel, [string]$Text, [string]$BackupRel = '') {
  $path = Resolve-RepoPath $Rel
  $dir = Split-Path -Parent $path
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $tmp = $path + '.tmp.' + $PID
  [System.IO.File]::WriteAllText($tmp, $Text, [System.Text.UTF8Encoding]::new($false))
  if (Test-Path -LiteralPath $path -PathType Leaf) {
    $backup = $null
    if (-not [string]::IsNullOrWhiteSpace($BackupRel)) {
      $backup = Resolve-RepoPath $BackupRel
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backup) | Out-Null
      if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup -Force }
    }
    [System.IO.File]::Replace($tmp, $path, $backup, $true)
  } else {
    [System.IO.File]::Move($tmp, $path)
  }
}
function Write-JsonReplace([string]$Rel, [object]$Value, [string]$BackupRel = '') {
  Write-TextReplace $Rel (($Value | ConvertTo-Json -Depth 80) + "`n") $BackupRel
}
function Add-OrSet([object]$Object, [string]$Name, [object]$Value) {
  $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
}
function Exact-CanonicalValid([object]$Doc) {
  if ($null -eq $Doc) { return $false }
  if ([string]$Doc.slot_id -ne $slotId) { return $false }
  if ($null -eq $Doc.acceptance -or -not [bool]$Doc.acceptance.passed) { return $false }
  if ([string]$Doc.source.git_blob_sha -ne $expectedBlob) { return $false }
  if ([int]$Doc.canonical_point_row_count -ne 3) { return $false }
  $ids = @($Doc.canonical_point_rows | ForEach-Object { [string]$_.parcel_id })
  return (($ids -join ',') -eq 'parcel_61523,parcel_61524,parcel_61525')
}
function Slot-JsonExists([string]$Rel) {
  $doc = Read-JsonOrNull $Rel
  return ($null -ne $doc -and [string]$doc.slot_id -eq $slotId)
}
function Chain-CheckpointValid {
  $canonical = Read-JsonOrNull $canonicalRel
  if (-not (Exact-CanonicalValid $canonical)) { return $false }
  if (-not (Slot-JsonExists $probeRel)) { return $false }
  if (-not (Slot-JsonExists $watchdogRel)) { return $false }
  $chain = Read-JsonOrNull $chainRel
  if ($null -eq $chain -or [string]$chain.slot_id -ne $slotId) { return $false }
  return ([string]$chain.state -in @('BLOCKED_EPOCH_PROVENANCE','CHAIN_EXECUTION_PASS_NONFINAL'))
}
function Disable-RemainingRecoveryTasks([string]$Reason) {
  foreach ($rel in $recoveryTaskRels) {
    $doc = Read-JsonOrNull $rel
    if ($null -eq $doc) { continue }
    if ([string]$doc.task_id -eq [string]$env:AAYS_TASK_ID) { continue }
    $status = ([string]$doc.status).Trim().ToLowerInvariant()
    if ($status -in @('pickup_requested','queued','ready','pending','pending_repo_queue','queued_for_single_shared_runner')) {
      Add-OrSet $doc 'status' 'done_no_retry_needed'
      Add-OrSet $doc 'disabled_at' (Now-Utc)
      Add-OrSet $doc 'disabled_reason' $Reason
      Write-JsonReplace $rel $doc
    }
  }
}

$startedAt = Now-Utc
$decision = 'NO_ACTION'
$requeued = $false
$retryReason = @()
$queue = Read-JsonOrNull $queueRel
$template = Read-JsonOrNull $templateRel
if ($null -eq $template) { throw 'RECOVERY_TEMPLATE_NOT_FOUND_OR_INVALID' }
if ([string]$template.task_id -ne $canonicalTaskId) { throw 'RECOVERY_TEMPLATE_TASK_ID_MISMATCH' }
if ([string]$template.slot_id -ne $slotId) { throw 'RECOVERY_TEMPLATE_SLOT_MISMATCH' }

$state = Read-JsonOrNull $stateRel
if ($null -eq $state) {
  $state = [pscustomobject][ordered]@{
    schema_version = 1
    slot_id = $slotId
    canonical_task_id = $canonicalTaskId
    requeue_count = 0
    history = @()
    fake_data = $false
    final_ready = $false
  }
}
$requeueCount = 0
[void][int]::TryParse(([string]$state.requeue_count), [ref]$requeueCount)
$checkpointValid = Chain-CheckpointValid
$queueStatus = if ($null -eq $queue) { 'missing' } else { ([string]$queue.status).Trim().ToLowerInvariant() }
$queueAgeMinutes = $null
$queuePath = Resolve-RepoPath $queueRel
if (Test-Path -LiteralPath $queuePath -PathType Leaf) {
  $queueAgeMinutes = [math]::Round(((Get-Date).ToUniversalTime() - (Get-Item -LiteralPath $queuePath).LastWriteTimeUtc).TotalMinutes, 3)
}

$automationExitCode = $null
$runnerReportPath = Resolve-RepoPath $runnerReportRel
if (Test-Path -LiteralPath $runnerReportPath -PathType Leaf) {
  $text = Get-Content -LiteralPath $runnerReportPath -Raw
  if ($text -match '(?m)^automation_exit_code=(-?\d+)\s*$') { $automationExitCode = [int]$Matches[1] }
}
$completed = Read-JsonOrNull $completedRel
$completedBlockers = @()
if ($null -ne $completed -and $null -ne $completed.blockers) {
  $completedBlockers = @($completed.blockers | ForEach-Object { [string]$_ })
}
$started = Read-JsonOrNull $startedRel
$startedAgeMinutes = $null
if ($null -ne $started -and $started.started_at) {
  try { $startedAgeMinutes = [math]::Round(((Get-Date).ToUniversalTime() - [datetime]::Parse([string]$started.started_at).ToUniversalTime()).TotalMinutes, 3) } catch {}
}

if ($checkpointValid) {
  $decision = 'CHECKPOINT_VALID_NO_REQUEUE'
  Disable-RemainingRecoveryTasks 'VALID_CANONICAL_PROBE_WATCHDOG_CHAIN_CHECKPOINT'
} else {
  if ($queueStatus -eq 'done') { $retryReason += 'QUEUE_DONE_WITHOUT_VALID_CHECKPOINT' }
  if ($queueStatus -eq 'running') {
    # The reconciler itself is running under the single shared-runner lock.
    # Therefore the canonical task cannot still be active in the same runner pass;
    # a remaining canonical `running` queue record is orphaned and retryable.
    $retryReason += 'QUEUE_RUNNING_ORPHANED_WHEN_RECONCILER_SELECTED'
  }
  if ($automationExitCode -ne $null -and $automationExitCode -ne 0) { $retryReason += ('AUTOMATION_EXIT_NONZERO_' + $automationExitCode) }
  if ($completedBlockers -contains 'AUTOMATION_EXIT_NONZERO') { $retryReason += 'COMPLETED_BLOCKER_AUTOMATION_EXIT_NONZERO' }
  if ($completedBlockers -contains 'RUNNER_TASK_FAILED') { $retryReason += 'COMPLETED_BLOCKER_RUNNER_TASK_FAILED' }
  if ($queueStatus -eq 'missing') { $retryReason += 'CANONICAL_QUEUE_FILE_MISSING' }
  $retryReason = @($retryReason | Select-Object -Unique)

  if ($retryReason.Count -gt 0 -and $requeueCount -lt $MaxRequeues) {
    $next = $requeueCount + 1
    $restored = Read-JsonOrNull $templateRel
    Add-OrSet $restored 'status' 'pickup_requested'
    Add-OrSet $restored 'retry_reconciliation_count' $next
    Add-OrSet $restored 'retry_requeued_at' (Now-Utc)
    Add-OrSet $restored 'retry_reason' @($retryReason)
    Add-OrSet $restored 'last_reconciler_task_id' ([string]$env:AAYS_TASK_ID)
    Add-OrSet $restored 'idempotency_key' ("height-difference-3-single-pass-chain-exact-blob-v6-watchdog-retry-" + $next)
    Write-JsonReplace $queueRel $restored $backupRel
    $requeued = $true
    $decision = 'CANONICAL_TASK_REQUEUED'
    $requeueCount = $next
  } elseif ($retryReason.Count -gt 0 -and $requeueCount -ge $MaxRequeues) {
    $decision = 'MAX_REQUEUES_EXHAUSTED'
    Disable-RemainingRecoveryTasks 'MAX_REQUEUES_EXHAUSTED'
  } elseif ($queueStatus -in @('pickup_requested','queued','ready','pending','pending_repo_queue','queued_for_single_shared_runner')) {
    $decision = 'CANONICAL_TASK_ALREADY_SELECTABLE'
  } else {
    $decision = 'NO_RETRY_SIGNAL'
  }
}

$history = @($state.history)
$history += [pscustomobject][ordered]@{
  checked_at = Now-Utc
  reconciler_task_id = [string]$env:AAYS_TASK_ID
  decision = $decision
  requeued = $requeued
  queue_status_before = $queueStatus
  queue_age_minutes = $queueAgeMinutes
  started_age_minutes = $startedAgeMinutes
  automation_exit_code = $automationExitCode
  retry_reason = @($retryReason)
  checkpoint_valid = $checkpointValid
}
if ($history.Count -gt 20) { $history = @($history | Select-Object -Last 20) }
Add-OrSet $state 'updated_at' (Now-Utc)
Add-OrSet $state 'requeue_count' $requeueCount
Add-OrSet $state 'last_decision' $decision
Add-OrSet $state 'history' $history
Write-JsonReplace $stateRel $state

$report = [ordered]@{
  schema_version = 1
  slot_id = $slotId
  task_id = [string]$env:AAYS_TASK_ID
  canonical_task_id = $canonicalTaskId
  started_at = $startedAt
  completed_at = Now-Utc
  decision = $decision
  canonical_task_requeued = $requeued
  requeue_count = $requeueCount
  max_requeues = $MaxRequeues
  queue_status_before = $queueStatus
  queue_age_minutes = $queueAgeMinutes
  started_age_minutes = $startedAgeMinutes
  automation_exit_code = $automationExitCode
  completed_blockers = @($completedBlockers)
  retry_reason = @($retryReason)
  checkpoint_valid = $checkpointValid
  canonical_output_valid = (Exact-CanonicalValid (Read-JsonOrNull $canonicalRel))
  epoch_probe_output_exists = (Slot-JsonExists $probeRel)
  watchdog_output_exists = (Slot-JsonExists $watchdogRel)
  chain_output_exists = (Slot-JsonExists $chainRel)
  recovery_template_path = $templateRel
  canonical_queue_path = $queueRel
  state_path = $stateRel
  output_semantics = 'SLOT_ONLY_RETRY_RECONCILIATION_FOR_V4_FALSE_DONE_OR_STALE_RUNNING_NONFINAL'
  actual_business_data_rows_written = 0
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  final_ready = $false
}
Write-JsonReplace $reportRel $report
Write-JsonReplace $websiteReportRel $report

$gateRel = "docs/chatgpt_status/aays1/status/$([string]$env:AAYS_TASK_ID)_gate.json"
$gate = [ordered]@{
  task_id = [string]$env:AAYS_TASK_ID
  source_row_gate_passed = $false
  ui_token_gate_passed = $false
  browser_smoke_passed = $false
  post_sync_ok = $false
  manual_review_required = $true
  fake_data = $false
  final_ready = $false
}
Write-JsonReplace $gateRel $gate

Write-Host ('HEIGHT_DIFFERENCE_3_RETRY_DECISION=' + $decision)
Write-Host ('HEIGHT_DIFFERENCE_3_REQUEUE_COUNT=' + $requeueCount)
Write-Host 'FINAL_READY=false'
exit 0

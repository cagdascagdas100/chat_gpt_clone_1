[CmdletBinding()]
param(
  [ValidateRange(30,1440)][int]$StaleRunningMinutes = 120,
  [ValidateRange(1,5)][int]$MaxRequeues = 3
)

$ErrorActionPreference = 'Stop'
$rawRoot = [string]$env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($rawRoot)) { throw 'AAYS_REPO_ROOT_REQUIRED' }
$root = [System.IO.Path]::GetFullPath($rawRoot)
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'AAYS_REPO_ROOT_NOT_FOUND' }

$slotId = 'gas_emissions_1'
$canonicalTaskId = 'gas-emissions-1-single-pass-recovery-20260722'
$queueRel = 'docs/chatgpt_status/aays1/queue/0020_100_gas_emissions_1_single_pass_recovery_20260722.task.json'
$templateRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/recovery/gas_emissions_1_priority2_task_template_latest.json'
$stateRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/recovery/gas_emissions_1_retry_state_latest.json'
$backupRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/recovery/gas_emissions_1_priority2_queue_backup_latest.json'
$recoveryRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_single_pass_recovery_latest.json'
$validationRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_single_pass_recovery_validation_latest.json'
$runnerReportRel = "docs/chatgpt_status/aays1/reports/${canonicalTaskId}_runner_output.txt"
$completedRel = "docs/chatgpt_status/aays1/status/${canonicalTaskId}_completed.json"
$startedRel = "docs/chatgpt_status/aays1/status/${canonicalTaskId}_started.json"
$reportRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/reports/gas_emissions_1_retry_reconciliation_latest.json'
$statusRel = 'docs/chatgpt_status/gas_emissions/shards/gas_emissions_1/status/gas_emissions_1_retry_reconciliation_latest.json'
$websiteRel = 'england_map_web/data/aays_21_slots/gas_emissions_1/retry_reconciliation_latest.json'
$recoveryTaskRels = @(
  'docs/chatgpt_status/aays1/queue/0006_911_gas_emissions_1_retry_reconciler_01_20260722.task.json',
  'docs/chatgpt_status/aays1/queue/0006_912_gas_emissions_1_retry_reconciler_02_20260722.task.json',
  'docs/chatgpt_status/aays1/queue/0006_913_gas_emissions_1_retry_reconciler_03_20260722.task.json'
)
$expectedStages = @(
  'browser_dump_dom',
  'hmlr_inspire_proximity',
  'binary_prtr_pi_parse',
  'classify_prtr_pi_records',
  'semantic_annual_air_mass_gate'
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
  $tmp = $path + '.tmp.' + $PID + '.' + [Guid]::NewGuid().ToString('N')
  [System.IO.File]::WriteAllText($tmp, $Text, [System.Text.UTF8Encoding]::new($false))
  if (Test-Path -LiteralPath $path -PathType Leaf) {
    $backup = $null
    if (-not [string]::IsNullOrWhiteSpace($BackupRel)) {
      $backup = Resolve-RepoPath $BackupRel
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backup) | Out-Null
      if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup -Force }
    }
    [System.IO.File]::Replace($tmp, $path, $backup, $true)
  }
  else {
    [System.IO.File]::Move($tmp, $path)
  }
}
function Write-JsonReplace([string]$Rel, [object]$Value, [string]$BackupRel = '') {
  Write-TextReplace $Rel (($Value | ConvertTo-Json -Depth 80) + "`n") $BackupRel
}
function Add-OrSet([object]$Object, [string]$Name, [object]$Value) {
  $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
}
function Safety-Valid([object]$Doc) {
  if ($null -eq $Doc) { return $false }
  return (
    [string]$Doc.slot_id -eq $slotId -and
    $Doc.final_ready -eq $false -and
    $Doc.fake_data -eq $false -and
    $Doc.db_write -eq $false -and
    $Doc.migration -eq $false -and
    $Doc.production_deploy -eq $false
  )
}
function Stage-Names-Valid([object]$Doc, [string]$PropertyName) {
  if ($null -eq $Doc) { return $false }
  $rows = @($Doc.$PropertyName)
  if ($rows.Count -ne $expectedStages.Count) { return $false }
  $names = @($rows | ForEach-Object { [string]$_.name })
  if (@($names | Sort-Object -Unique).Count -ne $expectedStages.Count) { return $false }
  return (($names | Sort-Object) -join ',') -eq (($expectedStages | Sort-Object) -join ',')
}
function Recovery-Checkpoint-Valid {
  $validation = Read-JsonOrNull $validationRel
  $recovery = Read-JsonOrNull $recoveryRel
  if (-not (Safety-Valid $validation)) { return $false }
  if (-not (Safety-Valid $recovery)) { return $false }
  if ([int]$validation.carrier_version -ne 6) { return $false }
  if ($validation.runner_execution_observed -ne $true) { return $false }
  if (-not (Stage-Names-Valid $validation 'stage_summary')) { return $false }
  if (-not (Stage-Names-Valid $recovery 'stages')) { return $false }
  return $true
}
function Disable-Remaining-RecoveryTasks([string]$Reason) {
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
    db_write = $false
    migration = $false
    production_deploy = $false
    final_ready = $false
  }
}
$requeueCount = 0
[void][int]::TryParse(([string]$state.requeue_count), [ref]$requeueCount)
$checkpointValid = Recovery-Checkpoint-Valid
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
  $decision = 'BOUNDED_RECOVERY_CHECKPOINT_VALID_NO_REQUEUE'
  Disable-Remaining-RecoveryTasks 'VALID_V6_RECOVERY_AND_VALIDATION_CHECKPOINT'
}
else {
  if ($queueStatus -eq 'done') { $retryReason += 'QUEUE_DONE_WITHOUT_VALID_V6_CHECKPOINT' }
  if ($queueStatus -eq 'running' -and (($startedAgeMinutes -ne $null -and $startedAgeMinutes -ge $StaleRunningMinutes) -or ($queueAgeMinutes -ne $null -and $queueAgeMinutes -ge $StaleRunningMinutes))) {
    $retryReason += 'QUEUE_RUNNING_STALE'
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
    Add-OrSet $restored 'attempt_id' ("gas-emissions-1-recovery-20260722-002-r" + $next)
    Add-OrSet $restored 'idempotency_key' ("gas-emissions-1-single-pass-recovery-schema10-retry-" + $next)
    Write-JsonReplace $queueRel $restored $backupRel
    $requeued = $true
    $decision = 'CANONICAL_TASK_REQUEUED'
    $requeueCount = $next
  }
  elseif ($retryReason.Count -gt 0 -and $requeueCount -ge $MaxRequeues) {
    $decision = 'MAX_REQUEUES_EXHAUSTED'
    Disable-Remaining-RecoveryTasks 'MAX_REQUEUES_EXHAUSTED'
  }
  elseif ($queueStatus -eq 'running') {
    $decision = 'RUNNING_NOT_STALE_NO_REQUEUE'
  }
  elseif ($queueStatus -in @('pickup_requested','queued','ready','pending','pending_repo_queue','queued_for_single_shared_runner')) {
    $decision = 'CANONICAL_TASK_ALREADY_SELECTABLE'
  }
  else {
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

$validation = Read-JsonOrNull $validationRel
$recovery = Read-JsonOrNull $recoveryRel
$report = [ordered]@{
  schema_version = 1
  architecture_version = 3
  workstream_id = 'AAYS_21_SLOT_SAFE_PARALLEL_V1'
  slot_id = $slotId
  task_id = [string]$env:AAYS_TASK_ID
  canonical_task_id = $canonicalTaskId
  started_at = $startedAt
  completed_at = Now-Utc
  decision = $decision
  canonical_task_requeued = $requeued
  requeue_count = $requeueCount
  max_requeues = $MaxRequeues
  stale_running_minutes = $StaleRunningMinutes
  queue_status_before = $queueStatus
  queue_age_minutes = $queueAgeMinutes
  started_age_minutes = $startedAgeMinutes
  automation_exit_code = $automationExitCode
  completed_blockers = @($completedBlockers)
  retry_reason = @($retryReason)
  checkpoint_valid = $checkpointValid
  validation_output_exists = ($null -ne $validation)
  validation_output_safe = (Safety-Valid $validation)
  validation_stage_set_valid = (Stage-Names-Valid $validation 'stage_summary')
  recovery_output_exists = ($null -ne $recovery)
  recovery_output_safe = (Safety-Valid $recovery)
  recovery_stage_set_valid = (Stage-Names-Valid $recovery 'stages')
  recovery_template_path = $templateRel
  canonical_queue_path = $queueRel
  state_path = $stateRel
  output_semantics = 'SLOT_ONLY_RETRY_RECONCILIATION_FOR_FALSE_DONE_MISSING_OUTPUT_OR_STALE_RUNNING_NONFINAL'
  actual_business_data_rows_written = 0
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  final_ready = $false
}
Write-JsonReplace $reportRel $report
Write-JsonReplace $statusRel $report
Write-JsonReplace $websiteRel $report
$report | ConvertTo-Json -Depth 40
exit 0

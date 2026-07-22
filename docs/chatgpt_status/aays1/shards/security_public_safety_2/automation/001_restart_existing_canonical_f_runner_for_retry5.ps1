[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$taskId = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId = 'attempt-005'
$portableRoot = 'F:\TerraYield_AAYS_Portable'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$launcher = 'F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd'
$repoEntry = Join-Path $repoRoot 'devam.ps1'
$signal = Join-Path $repoRoot 'docs\chatgpt_status\_shared\control\request_queue_refresh.json'
$output = Join-Path $repoRoot 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\001_retry5_existing_runner_recovery_latest.json'
$targets = 30762..30773

function Atomic([string]$Path,[string]$Text) {
  $directory = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $directory)) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
  $temporary = "$Path.tmp.$PID.$([guid]::NewGuid().ToString('N'))"
  [IO.File]::WriteAllText($temporary,$Text,[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $temporary -Destination $Path -Force
}
function Read-Json([string]$Path) {
  try { if (Test-Path -LiteralPath $Path -PathType Leaf) { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } } catch {}
  return $null
}
function Processes([string[]]$Patterns) {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $commandLine = [string]$_.CommandLine
    if (-not $commandLine) { return $false }
    foreach ($pattern in $Patterns) { if ($commandLine -match $pattern) { return $true } }
    return $false
  })
}
function Ensure-RefreshSignal {
  if (Test-Path -LiteralPath $signal -PathType Leaf) {
    $existing = Read-Json $signal
    return [pscustomobject]@{
      written = $false
      preserved = $true
      existing_slot = if ($existing) { [string]$existing.slot_id } else { 'unknown_or_non_json' }
      existing_task = if ($existing) { [string]$existing.task_id } else { '' }
      state = 'EXISTING_SHARED_REFRESH_SIGNAL_PRESERVED'
    }
  }
  $payload = [ordered]@{
    request_id = 'security-public-safety-2-retry5-refresh-20260722-001'
    page_key = 'aays1'
    slot_id = $slotId
    task_id = $taskId
    attempt_id = $attemptId
    action = 'refresh_remote_queue_and_claim_retry5'
    target_branch = 'codex/aays-single-runner-v5-20260706'
    queue_path = 'docs/chatgpt_status/aays1/queue/000000_security_public_safety_2_wave1_retry5_20260722.v3.task.json'
    priority = -100
    single_runner_only = $true
    new_runner = $false
    parallel_runner = $false
    requested_at = [DateTimeOffset]::UtcNow.ToString('o')
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  Atomic $signal (($payload | ConvertTo-Json -Depth 8) + "`n")
  return [pscustomobject]@{ written=$true; preserved=$false; existing_slot=''; existing_task=''; state='RETRY5_REFRESH_SIGNAL_WRITTEN' }
}
function Result([string]$Status,[bool]$Attempted,[bool]$Started,[int]$Before,[int]$After,[int]$Daemons,[object]$SignalState,[string]$Detail) {
  $payload = [ordered]@{
    schema_version = 5
    slot_id = $slotId
    task_id = $taskId
    attempt_id = $attemptId
    status = $Status
    checked_at = [DateTimeOffset]::UtcNow.ToString('o')
    start_attempted = $Attempted
    canonical_runner_started = $Started
    existing_process_count_before = $Before
    existing_process_count_after = $After
    persistent_daemon_count_after = $Daemons
    queue_refresh_signal_written = [bool]($SignalState -and $SignalState.written)
    existing_shared_refresh_signal_preserved = [bool]($SignalState -and $SignalState.preserved)
    existing_shared_refresh_signal_slot = if ($SignalState) { [string]$SignalState.existing_slot } else { '' }
    existing_shared_refresh_signal_task = if ($SignalState) { [string]$SignalState.existing_task } else { '' }
    queue_refresh_signal_state = if ($SignalState) { [string]$SignalState.state } else { 'NOT_REQUESTED' }
    exact_target_rows = @($targets)
    nearest_row_fallback_allowed = $false
    existing_single_runner_architecture_reused = $true
    new_runner_architecture_created = $false
    parallel_runner_started = $false
    wrong_slot_signal_overwrite_forbidden = $true
    task_claimed = $false
    detail = $Detail
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  Atomic $output (($payload | ConvertTo-Json -Depth 8) + "`n")
}
function Wait-Daemon([int]$Seconds) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  do {
    $daemons = @(Processes @('RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707'))
    if ($daemons.Count -gt 0) { return $daemons }
    Start-Sleep -Seconds 2
  } while ((Get-Date) -lt $deadline)
  return @(Processes @('RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707'))
}

$none = [pscustomobject]@{ written=$false; preserved=$false; existing_slot=''; existing_task=''; state='NOT_REQUESTED' }
if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) { throw "CANONICAL_F_REPO_ROOT_MISSING=$repoRoot" }
if (-not (Test-Path -LiteralPath $repoEntry -PathType Leaf)) { Result 'BLOCKED_CANONICAL_REPO_ENTRY_MISSING' $false $false 0 0 0 $none $repoEntry; exit 2 }

$patterns = @(
  [regex]::Escape($launcher),
  [regex]::Escape($repoEntry),
  'RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK',
  'RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709',
  'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707',
  'RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707'
)
$before = @(Processes $patterns)
$daemons = @(Processes @('RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707'))
if ($daemons.Count -gt 1 -or $before.Count -gt 1) {
  Result 'BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES' $false $false $before.Count $before.Count $daemons.Count $none 'Fail closed; no process started and shared signal preserved.'
  exit 3
}
if ($daemons.Count -eq 1) {
  $signalState = Ensure-RefreshSignal
  Result 'CANONICAL_DAEMON_ACTIVE_QUEUE_REFRESH_AVAILABLE' $false $false $before.Count $before.Count 1 $signalState 'Existing daemon preserved; existing shared refresh signal is never overwritten.'
  exit 0
}
if ($before.Count -eq 1) {
  Result 'CANONICAL_TRANSIENT_PROCESS_ACTIVE_NO_SECOND_PROCESS' $false $false 1 1 0 $none 'Existing process preserved; no second process started.'
  exit 0
}

$detail = ''
if (Test-Path -LiteralPath $launcher -PathType Leaf) {
  $process = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c',('"' + $launcher + '"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal
  $detail = "canonical_cmd_pid=$($process.Id)"
}
$daemons = @(Wait-Daemon 30)
$after = @(Processes $patterns)
if ($daemons.Count -eq 0 -and $after.Count -eq 0) {
  $process = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $repoEntry + '"')) -WorkingDirectory $repoRoot -PassThru -WindowStyle Normal
  $detail = ($detail + ';repo_devam_pid=' + $process.Id).TrimStart(';')
  $daemons = @(Wait-Daemon 30)
  $after = @(Processes $patterns)
}
if ($daemons.Count -gt 1) { Result 'BLOCKED_MULTIPLE_DAEMONS_AFTER_START' $true $false 0 $after.Count $daemons.Count $none $detail; exit 3 }
if ($daemons.Count -eq 0) { Result 'BLOCKED_CANONICAL_RUNNER_START_NOT_OBSERVED' $true $false 0 $after.Count 0 $none $detail; exit 4 }
$signalState = Ensure-RefreshSignal
Result 'EXISTING_CANONICAL_DAEMON_RESTARTED_QUEUE_REFRESH_AVAILABLE' $true $true 0 $after.Count 1 $signalState $detail
exit 0

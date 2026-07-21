[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$attemptId = 'height-difference-2-20260721-020'
$portableRoot = 'F:\TerraYield_AAYS_Portable'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$launcher = 'F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd'
$repoEntry = Join-Path $repoRoot 'devam.ps1'
$outputRel = 'docs\chatgpt_status\topography\shards\height_difference_2\runner_outputs\014_existing_canonical_runner_restart_latest.json'

function Write-Result(
  [string]$Status,
  [bool]$StartAttempted,
  [bool]$Started,
  [int]$ProcessCountBefore,
  [int]$ProcessCountAfter,
  [int]$DaemonCountAfter,
  [string]$LaunchMode,
  [string]$Detail
) {
  $output = Join-Path $repoRoot $outputRel
  $parent = Split-Path -Parent $output
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  [ordered]@{
    schema_version = 4
    slot_id = 'height_difference_2'
    task_id = $taskId
    attempt_id = $attemptId
    status = $Status
    checked_at = (Get-Date).ToUniversalTime().ToString('o')
    portable_root = $portableRoot
    repo_root = $repoRoot
    launcher = $launcher
    repo_entry = $repoEntry
    launch_mode = $LaunchMode
    start_attempted = $StartAttempted
    existing_canonical_process_count_before = $ProcessCountBefore
    existing_canonical_process_count_after = $ProcessCountAfter
    persistent_daemon_count_after = $DaemonCountAfter
    canonical_runner_started = $Started
    exact_target_rows = @(30762,46142,61522)
    nearest_row_fallback_allowed = $false
    existing_single_runner_architecture_reused = $true
    new_runner_architecture_created = $false
    parallel_runner_started = $false
    task_claimed = $false
    detail = $Detail
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $output -Encoding UTF8
}

if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) {
  throw "CANONICAL_F_REPO_ROOT_MISSING=$repoRoot"
}
if (-not (Test-Path -LiteralPath $repoEntry -PathType Leaf)) {
  Write-Result 'BLOCKED_CANONICAL_REPO_ENTRY_MISSING' $false $false 0 0 0 'none' $repoEntry
  exit 2
}

$canonicalPatterns = @(
  [regex]::Escape($launcher),
  [regex]::Escape($repoEntry),
  'RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK',
  'RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709',
  'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707',
  'RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707'
)
$daemonPattern = 'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707'

function Get-MatchingProcesses([string[]]$Patterns) {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $commandLine = [string]$_.CommandLine
    if (-not $commandLine) { return $false }
    foreach ($pattern in $Patterns) {
      if ($commandLine -match $pattern) { return $true }
    }
    return $false
  })
}
function Get-CanonicalProcesses { @(Get-MatchingProcesses $canonicalPatterns) }
function Get-PersistentDaemons { @(Get-MatchingProcesses @($daemonPattern)) }
function Wait-ForDaemon([int]$Seconds) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  do {
    $daemons = @(Get-PersistentDaemons)
    if ($daemons.Count -gt 0) { return $daemons }
    Start-Sleep -Seconds 2
  } while ((Get-Date) -lt $deadline)
  return @(Get-PersistentDaemons)
}

$before = @(Get-CanonicalProcesses)
$beforeDaemons = @(Get-PersistentDaemons)
if ($beforeDaemons.Count -gt 1 -or $before.Count -gt 1) {
  Write-Result 'BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES' $false $false $before.Count $before.Count $beforeDaemons.Count 'none' 'Fail closed; no process started.'
  exit 3
}
if ($beforeDaemons.Count -eq 1) {
  Write-Result 'CANONICAL_PERSISTENT_DAEMON_ALREADY_ACTIVE_NO_NEW_PROCESS' $false $false $before.Count $before.Count 1 'existing_persistent_daemon' 'Existing canonical persistent daemon preserved.'
  exit 0
}
if ($before.Count -eq 1) {
  Write-Result 'CANONICAL_TRANSIENT_OR_LEGACY_PROCESS_ALREADY_ACTIVE_NO_NEW_PROCESS' $false $false 1 1 0 'existing_non_daemon_process' 'Fail closed; existing canonical process preserved and no second process started.'
  exit 0
}

$launchMode = 'canonical_cmd'
$detail = ''
if (Test-Path -LiteralPath $launcher -PathType Leaf) {
  $process = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', ('"' + $launcher + '"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal
  $detail = "canonical_cmd_pid=$($process.Id)"
} else {
  $launchMode = 'repo_devam_fallback'
}

$daemons = @(Wait-ForDaemon 30)
$after = @(Get-CanonicalProcesses)
if ($daemons.Count -eq 0 -and $after.Count -eq 0) {
  $launchMode = 'repo_devam_fallback'
  $process = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $repoEntry + '"')) -WorkingDirectory $repoRoot -PassThru -WindowStyle Normal
  $detail = ($detail + ';repo_devam_pid=' + $process.Id).TrimStart(';')
  $daemons = @(Wait-ForDaemon 30)
  $after = @(Get-CanonicalProcesses)
}

if ($daemons.Count -gt 1) {
  Write-Result 'BLOCKED_MULTIPLE_PERSISTENT_DAEMONS_AFTER_START' $true $false 0 $after.Count $daemons.Count $launchMode $detail
  exit 3
}
if ($daemons.Count -eq 0) {
  $status = if ($after.Count -gt 0) { 'BLOCKED_NON_DAEMON_CANONICAL_PROCESS_REMAINS' } else { 'BLOCKED_CANONICAL_RUNNER_START_NOT_OBSERVED' }
  Write-Result $status $true $false 0 $after.Count 0 $launchMode $detail
  exit 4
}

Write-Result 'EXISTING_CANONICAL_PERSISTENT_DAEMON_RESTARTED' $true $true 0 $after.Count 1 $launchMode $detail
exit 0

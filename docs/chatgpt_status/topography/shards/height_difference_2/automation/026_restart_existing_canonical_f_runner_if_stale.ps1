[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$attemptId = 'height-difference-2-20260721-018'
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
  [string]$LaunchMode,
  [string]$Detail
) {
  $output = Join-Path $repoRoot $outputRel
  $parent = Split-Path -Parent $output
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  [ordered]@{
    schema_version = 2
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
    canonical_runner_started = $Started
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
  Write-Result 'BLOCKED_CANONICAL_REPO_ENTRY_MISSING' $false $false 0 0 'none' $repoEntry
  exit 2
}

$patterns = @(
  [regex]::Escape($launcher),
  [regex]::Escape($repoEntry),
  'RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK',
  'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707',
  'RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707'
)
function Get-CanonicalProcesses {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $commandLine = [string]$_.CommandLine
    if (-not $commandLine) { return $false }
    foreach ($pattern in $patterns) {
      if ($commandLine -match $pattern) { return $true }
    }
    return $false
  })
}

$before = @(Get-CanonicalProcesses)
if ($before.Count -gt 1) {
  Write-Result 'BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES' $false $false $before.Count $before.Count 'none' 'Fail closed; no process started.'
  exit 3
}
if ($before.Count -eq 1) {
  Write-Result 'CANONICAL_RUNNER_ALREADY_ACTIVE_NO_NEW_PROCESS' $false $false 1 1 'existing_process' 'Existing canonical process preserved.'
  exit 0
}

$launchMode = 'canonical_cmd'
$detail = ''
if (Test-Path -LiteralPath $launcher -PathType Leaf) {
  $process = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', ('"' + $launcher + '"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal
  $detail = "canonical_cmd_pid=$($process.Id)"
  Start-Sleep -Seconds 8
} else {
  $launchMode = 'repo_devam_fallback'
}

$after = @(Get-CanonicalProcesses)
if ($after.Count -eq 0) {
  $launchMode = 'repo_devam_fallback'
  $process = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $repoEntry + '"')) -WorkingDirectory $repoRoot -PassThru -WindowStyle Normal
  $detail = ($detail + ';repo_devam_pid=' + $process.Id).TrimStart(';')
  Start-Sleep -Seconds 8
  $after = @(Get-CanonicalProcesses)
}

if ($after.Count -gt 1) {
  Write-Result 'BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES_AFTER_START' $true $false 0 $after.Count $launchMode $detail
  exit 3
}
$started = $after.Count -eq 1
$status = if ($started) { 'EXISTING_CANONICAL_RUNNER_RESTARTED_SINGLE_PROCESS' } else { 'BLOCKED_CANONICAL_RUNNER_START_NOT_OBSERVED' }
Write-Result $status $true $started 0 $after.Count $launchMode $detail
exit $(if ($started) { 0 } else { 4 })

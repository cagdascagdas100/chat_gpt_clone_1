[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$attemptId = 'height-difference-2-20260721-017'
$portableRoot = 'F:\TerraYield_AAYS_Portable'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$launcher = 'F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd'
$outputRel = 'docs\chatgpt_status\topography\shards\height_difference_2\runner_outputs\014_existing_canonical_runner_restart_latest.json'

function Write-Result([string]$Status, [bool]$StartAttempted, [bool]$Started, [int]$ProcessCountBefore, [int]$ProcessCountAfter, [string]$Detail) {
  $output = Join-Path $repoRoot $outputRel
  $parent = Split-Path -Parent $output
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  [ordered]@{
    schema_version = 1
    slot_id = 'height_difference_2'
    task_id = $taskId
    attempt_id = $attemptId
    status = $Status
    checked_at = (Get-Date).ToUniversalTime().ToString('o')
    portable_root = $portableRoot
    repo_root = $repoRoot
    launcher = $launcher
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
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
  Write-Result 'BLOCKED_CANONICAL_LAUNCHER_MISSING' $false $false 0 0 $launcher
  exit 2
}

$patterns = @(
  [regex]::Escape($launcher),
  'RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK',
  'RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707',
  'stable_runner_daemon'
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
  Write-Result 'BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES' $false $false $before.Count $before.Count 'Fail closed; no process started.'
  exit 3
}
if ($before.Count -eq 1) {
  Write-Result 'CANONICAL_RUNNER_ALREADY_ACTIVE_NO_NEW_PROCESS' $false $false 1 1 'Existing canonical process preserved.'
  exit 0
}

$process = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', ('"' + $launcher + '"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal
Start-Sleep -Seconds 5
$after = @(Get-CanonicalProcesses)
$started = $after.Count -eq 1
$status = if ($started) { 'EXISTING_CANONICAL_RUNNER_RESTARTED_SINGLE_PROCESS' } else { 'BLOCKED_CANONICAL_RUNNER_START_NOT_OBSERVED' }
Write-Result $status $true $started 0 $after.Count ("launcher_pid=" + $process.Id)
exit $(if ($started) { 0 } else { 4 })

[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$RepoFullName = "cagdascagdas100/chat_gpt_clone_1",
  [string]$MainBranch = "codex/aays-single-runner-v5-20260706",
  [string]$WorkRoot = "",
  [int]$IntervalSeconds = 60,
  [int]$MaxTasks = 1,
  [int]$StaleMinutes = 15,
  [int]$HeartbeatSeconds = 15,
  [int]$RefreshIntervalSeconds = 43200,
  [switch]$NoPanel,
  [switch]$NoLoop,
  [switch]$NoPush
)

$ErrorActionPreference = "Stop"

function Resolve-AaysRepoRoot {
  param([string]$RequestedRoot)
  $localRepo = Join-Path $PSScriptRoot "..\..\..\.."
  $candidates = @($RequestedRoot, $localRepo, "F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707")
  foreach ($candidate in $candidates) {
    if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
    $resolved = Resolve-Path -LiteralPath $candidate -ErrorAction SilentlyContinue
    if ($resolved -and (Test-Path -LiteralPath (Join-Path $resolved.Path "docs/chatgpt_status/_shared"))) { return $resolved.Path }
  }
  throw "AAYS repo root not found. Pass -RepoRoot."
}
function Read-JsonFile([string]$Path) {
  try { if (Test-Path -LiteralPath $Path) { return Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json } } catch {}
  return $null
}
function Test-ProcessAlive([int]$ProcessId) {
  if ($ProcessId -le 0) { return $false }
  return $null -ne (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)
}
function Get-CommandLine([int]$ProcessId) {
  try { return [string](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop).CommandLine } catch { return "" }
}
function Get-HeartbeatAgeSeconds([string]$HeartbeatPath) {
  $heartbeat = Read-JsonFile $HeartbeatPath
  if ($null -eq $heartbeat -or [string]::IsNullOrWhiteSpace([string]$heartbeat.heartbeat_at)) { return [double]::PositiveInfinity }
  try {
    $when = [datetime]::Parse([string]$heartbeat.heartbeat_at).ToUniversalTime()
    return [math]::Max(0, ((Get-Date).ToUniversalTime() - $when).TotalSeconds)
  } catch {
    return [double]::PositiveInfinity
  }
}
function Test-RunnerActive(
  [string]$LockPath,
  [string]$HeartbeatPath,
  [string]$ExpectedRepoRoot,
  [string]$ExpectedBranch,
  [int]$AllowedStaleMinutes
) {
  $lock = Read-JsonFile $LockPath
  if ($null -eq $lock -or $null -eq $lock.pid) {
    return [pscustomobject]@{
      active=$false; alive=$false; pid=$null; stale=$false; verified=$false; identity_verified=$false
      heartbeat_stale=$true; heartbeat_age_seconds=[double]::PositiveInfinity; reason="lock_missing_or_invalid"
    }
  }

  $pidValue = [int]$lock.pid
  $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
  if ($null -eq $proc) {
    return [pscustomobject]@{
      active=$false; alive=$false; pid=$pidValue; stale=$true; verified=$false; identity_verified=$false
      heartbeat_stale=$true; heartbeat_age_seconds=[double]::PositiveInfinity; reason="pid_not_alive"
    }
  }

  $startMatches = $false
  try {
    $expected = [datetime]::Parse([string]$lock.process_start_time).ToUniversalTime()
    $actual = $proc.StartTime.ToUniversalTime()
    $startMatches = ([math]::Abs(($actual - $expected).TotalSeconds) -lt 2)
  } catch {}

  $scopeMatches = ([string]$lock.lock_scope -eq "single_shared_runner_daemon")
  $repoMatches = ([string]$lock.repo_root).TrimEnd('\') -eq $ExpectedRepoRoot.TrimEnd('\')
  $branchMatches = ([string]$lock.branch -eq $ExpectedBranch)
  $commandLine = Get-CommandLine $pidValue
  $commandLineAvailable = -not [string]::IsNullOrWhiteSpace($commandLine)
  $commandMatches = $commandLineAvailable -and
    ($commandLine -like "*RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON*") -and
    ($commandLine -like "*$ExpectedRepoRoot*")

  $baseIdentityMatches = $startMatches -and $scopeMatches -and $repoMatches -and $branchMatches
  $identityUnverifiable = $baseIdentityMatches -and -not $commandLineAvailable
  $identityVerified = $baseIdentityMatches -and $commandMatches
  $heartbeatAge = Get-HeartbeatAgeSeconds $HeartbeatPath
  $processAge = [math]::Max(0, ((Get-Date).ToUniversalTime() - $proc.StartTime.ToUniversalTime()).TotalSeconds)
  $staleThresholdSeconds = [math]::Max(1, $AllowedStaleMinutes) * 60
  $heartbeatStale = if ([double]::IsPositiveInfinity($heartbeatAge)) {
    $processAge -gt $staleThresholdSeconds
  } else {
    $heartbeatAge -gt $staleThresholdSeconds
  }
  $active = $identityVerified -and -not $heartbeatStale

  return [pscustomobject]@{
    active=$active
    alive=$true
    pid=$pidValue
    stale=(-not $baseIdentityMatches -or ($commandLineAvailable -and -not $commandMatches))
    verified=$identityVerified
    identity_verified=$identityVerified
    identity_unverifiable=$identityUnverifiable
    heartbeat_stale=$heartbeatStale
    heartbeat_age_seconds=$heartbeatAge
    process_age_seconds=$processAge
    reason=if($identityUnverifiable){"live_daemon_identity_unverifiable"}elseif(-not $identityVerified){"process_identity_mismatch"}elseif($heartbeatStale){"verified_daemon_heartbeat_stale"}else{"verified_daemon_heartbeat_fresh"}
  }
}
function Stop-VerifiedStaleRunnerTree([object]$RunnerState, [string]$LockPath) {
  if (-not $RunnerState.identity_verified -or -not $RunnerState.heartbeat_stale -or $RunnerState.pid -le 0) {
    throw "STALE_RUNNER_STOP_REQUIRES_VERIFIED_IDENTITY"
  }

  $taskkill = Join-Path $env:SystemRoot "System32\taskkill.exe"
  if (-not (Test-Path -LiteralPath $taskkill)) { throw "TASKKILL_NOT_FOUND=$taskkill" }

  $output = & $taskkill "/PID" "$($RunnerState.pid)" "/T" "/F" 2>&1
  $exitCode = $LASTEXITCODE
  Start-Sleep -Seconds 2
  if ($exitCode -ne 0 -and (Test-ProcessAlive ([int]$RunnerState.pid))) {
    throw ("STALE_RUNNER_TREE_STOP_FAILED: " + (($output | Out-String).Trim()))
  }
  if (Test-ProcessAlive ([int]$RunnerState.pid)) {
    throw "STALE_RUNNER_TREE_STILL_ALIVE=$($RunnerState.pid)"
  }

  Remove-Item -LiteralPath $LockPath -Force -ErrorAction SilentlyContinue
  return [pscustomobject]@{ stopped=$true; pid=[int]$RunnerState.pid; reason="verified_daemon_heartbeat_stale" }
}

$repoRoot = [System.IO.Path]::GetFullPath((Resolve-AaysRepoRoot $RepoRoot)).TrimEnd('\')
if ($repoRoot.StartsWith('C:\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "BLOCKED_C_DRIVE_NOT_CANONICAL=$repoRoot"
}
if ([string]::IsNullOrWhiteSpace($WorkRoot)) {
  $WorkRoot = Join-Path (Split-Path -Parent $repoRoot) 'AAYS_STABLE_RUNNER_WORKTREES'
}
$WorkRoot = [System.IO.Path]::GetFullPath($WorkRoot).TrimEnd('\')
if ($WorkRoot.StartsWith('C:\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "BLOCKED_C_WORK_ROOT_NOT_CANONICAL=$WorkRoot"
}

$sharedRoot = Join-Path $repoRoot "docs/chatgpt_status/_shared"
$automationRoot = Join-Path $sharedRoot "automation"
$compatHelper = Join-Path $automationRoot "PREPARE_AAYS_SLOT21_QUEUE_COMPAT_RUNNER_20260803.py"
$builder = Join-Path $automationRoot "BUILD_AAYS_PAGE_PANEL_INDEX.ps1"
$panel = Join-Path $sharedRoot "panel/AAYS_RUNNER_PANEL.ps1"
$statusDir = Join-Path $sharedRoot "status"
$heartbeatDir = Join-Path $sharedRoot "heartbeat"
$locksDir = Join-Path $sharedRoot "locks"
$logsDir = Join-Path $sharedRoot "logs"
New-Item -ItemType Directory -Force -Path $statusDir, $heartbeatDir, $locksDir, $logsDir, $WorkRoot | Out-Null
$lockPath = Join-Path $locksDir "single_runner.lock"
$daemonHeartbeatPath = Join-Path $heartbeatDir "stable_runner_daemon_heartbeat_latest.json"
$bootstrapStatus = Join-Path $statusDir "runner_bootstrap_latest.json"

if (-not (Test-Path -LiteralPath $compatHelper)) { throw "Missing slot21 queue compatibility helper: $compatHelper" }
if (-not (Test-Path -LiteralPath $builder)) { throw "Missing panel builder: $builder" }

& powershell -NoProfile -ExecutionPolicy Bypass -File $builder -RepoRoot $repoRoot -EnsurePageDirs | Out-Null
$runnerState = Test-RunnerActive $lockPath $daemonHeartbeatPath $repoRoot $MainBranch $StaleMinutes
$preexistingRunnerAlive = [bool]$runnerState.alive
$preexistingRunnerIdentityVerified = [bool]$runnerState.identity_verified
$preexistingRunnerReason = [string]$runnerState.reason
$staleRunnerStopped = $false
$staleRunnerPid = $null
$staleRunnerHeartbeatAgeSeconds = $runnerState.heartbeat_age_seconds

if ($runnerState.alive -and -not $runnerState.identity_verified) {
  throw ("BLOCKED_LIVE_LOCK_OWNER_IDENTITY_UNVERIFIED_PID={0}_REASON={1}" -f $runnerState.pid, $runnerState.reason)
} elseif ($runnerState.identity_verified -and $runnerState.heartbeat_stale) {
  $stopResult = Stop-VerifiedStaleRunnerTree $runnerState $lockPath
  $staleRunnerStopped = [bool]$stopResult.stopped
  $staleRunnerPid = $stopResult.pid
  $runnerState = [pscustomobject]@{
    active=$false; alive=$false; pid=$null; stale=$false; verified=$false; identity_verified=$false
    heartbeat_stale=$false; heartbeat_age_seconds=0; reason="verified_stale_daemon_stopped"
  }
} elseif ($runnerState.stale -and -not $runnerState.active -and (Test-Path -LiteralPath $lockPath)) {
  if ($runnerState.alive) {
    throw ("BLOCKED_LIVE_LOCK_OWNER_IDENTITY_UNVERIFIED_PID={0}_REASON={1}" -f $runnerState.pid, $runnerState.reason)
  }
  Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
  $runnerState = [pscustomobject]@{
    active=$false; alive=$false; pid=$null; stale=$false; verified=$false; identity_verified=$false
    heartbeat_stale=$true; heartbeat_age_seconds=$staleRunnerHeartbeatAgeSeconds; reason="dead_invalid_lock_removed"
  }
}

$runnerPid = $runnerState.pid
$runnerStatus = if ($runnerState.active) { "runner_active" } else { "runner_not_running" }
if (-not $runnerState.active) {
  if ($NoLoop) {
    $args = @("--repo-root",$repoRoot,"--work-root",$WorkRoot,"--mode","scan","--","-RepoRoot",$repoRoot,"-RepoFullName",$RepoFullName,"-MainBranch",$MainBranch,"-WorkRoot",$WorkRoot,"-MaxTasks",$MaxTasks,"-StaleMinutes",$StaleMinutes,"-ScanOnly")
    if ($NoPush) { $args += "-NoPush" }
    $out = & python $compatHelper @args 2>&1
    $runnerStatus = "runner_scan_only_completed"
  } else {
    $args = @($compatHelper,"--repo-root",$repoRoot,"--work-root",$WorkRoot,"--mode","daemon","--","-IntervalSeconds",$IntervalSeconds,"-HeartbeatSeconds",$HeartbeatSeconds,"-RefreshIntervalSeconds",$RefreshIntervalSeconds,"-MaxTasks",$MaxTasks,"-RepoRoot",$repoRoot,"-RepoFullName",$RepoFullName,"-MainBranch",$MainBranch,"-WorkRoot",$WorkRoot,"-StaleMinutes",$StaleMinutes)
    if ($NoPush) { $args += "-NoPush" }
    $proc = Start-Process -FilePath python -ArgumentList $args -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
    $runnerPid = $proc.Id
    $runnerStatus = if ($staleRunnerStopped) { "stale_runner_replaced" } else { "runner_started" }
    Start-Sleep -Seconds 2
  }
}

if (-not $NoPanel -and (Test-Path -LiteralPath $panel)) {
  Start-Process -FilePath powershell -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$panel) -WorkingDirectory $repoRoot | Out-Null
}

$state = [ordered]@{
  updated_at = (Get-Date).ToUniversalTime().ToString("o")
  repo_root = $repoRoot
  work_root = $WorkRoot
  repo_full_name = $RepoFullName
  runner_branch = $MainBranch
  runner_status = $runnerStatus
  runner_engine = "stable_legacy_worktree_runner_20260707_slot21_queue_compat"
  scan_runner = "transient_slot21_compat_copy_of_RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707"
  max_tasks_per_scan = $MaxTasks
  runner_pid = $runnerPid
  runner_lock_active = (Test-Path -LiteralPath $lockPath)
  preexisting_runner_alive = $preexistingRunnerAlive
  preexisting_runner_identity_verified = $preexistingRunnerIdentityVerified
  preexisting_runner_reason = $preexistingRunnerReason
  live_unverified_lock_owner_fail_closed = $true
  stale_runner_identity_verified = [bool]$staleRunnerStopped
  stale_runner_stopped = [bool]$staleRunnerStopped
  stale_runner_pid = $staleRunnerPid
  stale_runner_heartbeat_age_seconds = $staleRunnerHeartbeatAgeSeconds
  lock_file = "docs/chatgpt_status/_shared/locks/single_runner.lock"
  daemon_heartbeat_file = "docs/chatgpt_status/_shared/heartbeat/stable_runner_daemon_heartbeat_latest.json"
  panel_index = "docs/chatgpt_status/_shared/panel/page_status_index_latest.json"
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $bootstrapStatus -Encoding UTF8
$state | ConvertTo-Json -Depth 8

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
function Get-ProcessCommandLine([int]$ProcessId) {
  try { return [string](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop).CommandLine } catch { return "" }
}
function Test-RunnerActive([string]$LockPath, [string]$ExpectedRepoRoot) {
  $lock = Read-JsonFile $LockPath
  if ($null -eq $lock -or $null -eq $lock.pid) { return [pscustomobject]@{ active=$false; alive=$false; pid=$null; stale=$false; verified=$false } }
  $pidValue = [int]$lock.pid
  $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
  if ($null -eq $proc) { return [pscustomobject]@{ active=$false; alive=$false; pid=$pidValue; stale=$true; verified=$false } }
  $startMatches = $true
  if ($lock.process_start_time) {
    try {
      $expected = [datetime]::Parse([string]$lock.process_start_time).ToUniversalTime()
      $actual = $proc.StartTime.ToUniversalTime()
      $startMatches = ([math]::Abs(($actual - $expected).TotalSeconds) -lt 2)
    } catch { $startMatches = $false }
  }
  $scopeMatches = (-not $lock.lock_scope -or [string]$lock.lock_scope -eq "single_shared_runner_daemon")
  $repoMatches = ([string]$lock.repo_root).TrimEnd([char]92) -eq $ExpectedRepoRoot.TrimEnd([char]92)
  $commandLine = Get-ProcessCommandLine $pidValue
  $commandMatches = $commandLine -like "*RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1*" -and $commandLine -like "*$ExpectedRepoRoot*"
  $verified = $startMatches -and $scopeMatches -and $repoMatches -and $commandMatches
  return [pscustomobject]@{ active=$verified; alive=$true; pid=$pidValue; stale=(-not $verified); verified=$verified; command_line=$commandLine }
}
function Test-DaemonHeartbeatFresh([string]$HeartbeatPath, [int]$MaxAgeMinutes) {
  $heartbeat = Read-JsonFile $HeartbeatPath
  if ($null -eq $heartbeat -or -not $heartbeat.heartbeat_at) { return $false }
  try {
    $observed = [datetime]::Parse([string]$heartbeat.heartbeat_at).ToUniversalTime()
    return (((Get-Date).ToUniversalTime() - $observed).TotalMinutes -le [math]::Max(1, $MaxAgeMinutes))
  } catch {
    return $false
  }
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
$locksDir = Join-Path $sharedRoot "locks"
$logsDir = Join-Path $sharedRoot "logs"
New-Item -ItemType Directory -Force -Path $statusDir, $locksDir, $logsDir, $WorkRoot | Out-Null
$lockPath = Join-Path $locksDir "single_runner.lock"
$daemonHeartbeatPath = Join-Path $sharedRoot "heartbeat/stable_runner_daemon_heartbeat_latest.json"
$bootstrapStatus = Join-Path $statusDir "runner_bootstrap_latest.json"

if (-not (Test-Path -LiteralPath $compatHelper)) { throw "Missing slot21 queue compatibility helper: $compatHelper" }
if (-not (Test-Path -LiteralPath $builder)) { throw "Missing panel builder: $builder" }

& powershell -NoProfile -ExecutionPolicy Bypass -File $builder -RepoRoot $repoRoot -EnsurePageDirs | Out-Null
$runnerState = Test-RunnerActive $lockPath $repoRoot
$heartbeatFresh = Test-DaemonHeartbeatFresh $daemonHeartbeatPath $StaleMinutes
if ($runnerState.active -and -not $heartbeatFresh) {
  Stop-Process -Id $runnerState.pid -Force -ErrorAction Stop
  for ($i = 0; $i -lt 10; $i++) {
    Start-Sleep -Milliseconds 500
    if (-not (Get-Process -Id $runnerState.pid -ErrorAction SilentlyContinue)) { break }
  }
  if (Get-Process -Id $runnerState.pid -ErrorAction SilentlyContinue) {
    throw "BLOCKED_STALE_DAEMON_STOP_FAILED=$($runnerState.pid)"
  }
  Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
  $runnerState = [pscustomobject]@{ active=$false; alive=$false; pid=$null; stale=$false; verified=$true }
}
if ($runnerState.stale -and -not $runnerState.active -and (Test-Path -LiteralPath $lockPath)) {
  if ($runnerState.alive) { throw "BLOCKED_LIVE_LOCK_OWNER_IDENTITY_UNVERIFIED=$($runnerState.pid)" }
  Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
  $runnerState = [pscustomobject]@{ active=$false; alive=$false; pid=$null; stale=$false; verified=$false }
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
    $runnerStatus = "runner_started"
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
  lock_file = "docs/chatgpt_status/_shared/locks/single_runner.lock"
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

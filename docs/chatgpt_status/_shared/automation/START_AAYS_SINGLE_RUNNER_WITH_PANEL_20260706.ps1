[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738",
  [string]$RepoFullName = "cagdascagdas100/chat_gpt_clone_1",
  [string]$MainBranch = "codex/aays-single-runner-v5-20260706",
  [string]$WorkRoot = "C:\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES",
  [int]$IntervalSeconds = 60,
  [int]$MaxTasks = 8,
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
  $candidates = @($RequestedRoot, (Join-Path $PSScriptRoot "..\..\..\.."), "C:\AAYS_WT\AAYS_REPAIR_20260706_1738", "C:\Users\cagda\Documents\GitHub\AAYS")
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
function Test-RunnerActive([string]$LockPath) {
  $lock = Read-JsonFile $LockPath
  if ($null -eq $lock -or $null -eq $lock.pid) { return [pscustomobject]@{ active=$false; pid=$null; stale=$false; verified=$false } }
  $pidValue = [int]$lock.pid
  $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
  if ($null -eq $proc) { return [pscustomobject]@{ active=$false; pid=$pidValue; stale=$true; verified=$false } }
  $startMatches = $false
  try {
    $expected = [datetime]::Parse([string]$lock.process_start_time).ToUniversalTime()
    $actual = $proc.StartTime.ToUniversalTime()
    $startMatches = ([math]::Abs(($actual - $expected).TotalSeconds) -lt 2)
  } catch {}
  $scopeMatches = ([string]$lock.lock_scope -eq "single_shared_runner_daemon")
  return [pscustomobject]@{ active=($startMatches -and $scopeMatches); pid=$pidValue; stale=(-not $startMatches); verified=($startMatches -and $scopeMatches) }
}

$repoRoot = Resolve-AaysRepoRoot $RepoRoot
$sharedRoot = Join-Path $repoRoot "docs/chatgpt_status/_shared"
$automationRoot = Join-Path $sharedRoot "automation"
$runner = Join-Path $automationRoot "RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1"
$scanRunner = Join-Path $automationRoot "RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1"
$builder = Join-Path $automationRoot "BUILD_AAYS_PAGE_PANEL_INDEX.ps1"
$panel = Join-Path $sharedRoot "panel/AAYS_RUNNER_PANEL.ps1"
$statusDir = Join-Path $sharedRoot "status"
$locksDir = Join-Path $sharedRoot "locks"
$logsDir = Join-Path $sharedRoot "logs"
New-Item -ItemType Directory -Force -Path $statusDir, $locksDir, $logsDir | Out-Null
$lockPath = Join-Path $locksDir "single_runner.lock"
$bootstrapStatus = Join-Path $statusDir "runner_bootstrap_latest.json"

if (-not (Test-Path -LiteralPath $runner)) { throw "Missing runner daemon: $runner" }
if (-not (Test-Path -LiteralPath $scanRunner)) { throw "Missing scan runner: $scanRunner" }
if (-not (Test-Path -LiteralPath $builder)) { throw "Missing panel builder: $builder" }

& powershell -NoProfile -ExecutionPolicy Bypass -File $builder -RepoRoot $repoRoot -EnsurePageDirs | Out-Null
$runnerState = Test-RunnerActive $lockPath
if ($runnerState.stale -and -not $runnerState.active -and (Test-Path -LiteralPath $lockPath)) {
  Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
  $runnerState = [pscustomobject]@{ active=$false; pid=$null; stale=$false }
}

$runnerPid = $runnerState.pid
$runnerStatus = if ($runnerState.active) { "runner_active" } else { "runner_not_running" }
if (-not $runnerState.active) {
  if ($NoLoop) {
    $args = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$scanRunner,"-RepoRoot",$repoRoot,"-RepoFullName",$RepoFullName,"-MainBranch",$MainBranch,"-WorkRoot",$WorkRoot,"-MaxTasks",$MaxTasks,"-StaleMinutes",$StaleMinutes,"-ScanOnly")
    if ($NoPush) { $args += "-NoPush" }
    $out = & powershell @args 2>&1
    $runnerStatus = "runner_scan_only_completed"
  } else {
    $args = @("-NoProfile","-ExecutionPolicy","Bypass","-File",$runner,"-IntervalSeconds",$IntervalSeconds,"-HeartbeatSeconds",$HeartbeatSeconds,"-RefreshIntervalSeconds",$RefreshIntervalSeconds,"-MaxTasks",$MaxTasks,"-RepoRoot",$repoRoot,"-RepoFullName",$RepoFullName,"-MainBranch",$MainBranch,"-WorkRoot",$WorkRoot,"-StaleMinutes",$StaleMinutes)
    if ($NoPush) { $args += "-NoPush" }
    $proc = Start-Process -FilePath powershell -ArgumentList $args -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
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
  repo_full_name = $RepoFullName
  runner_branch = $MainBranch
  runner_status = $runnerStatus
  runner_engine = "stable_legacy_worktree_runner_20260707"
  scan_runner = "RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707"
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

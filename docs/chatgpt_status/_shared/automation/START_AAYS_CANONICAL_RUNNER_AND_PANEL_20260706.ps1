[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$RepoFullName = "cagdascagdas100/chat_gpt_clone_1",
  [string]$MainBranch = "main",
  [string]$WorkRoot = "C:\AAYS_WT",
  [int]$IntervalSeconds = 60,
  [int]$MaxTasks = 1,
  [switch]$NoPanel
)

$ErrorActionPreference = "Stop"

function Resolve-AaysRepoRoot {
  param([string]$RequestedRoot)
  $candidates = New-Object System.Collections.Generic.List[string]
  if (-not [string]::IsNullOrWhiteSpace($RequestedRoot)) { $candidates.Add($RequestedRoot) }
  $candidates.Add((Join-Path $PSScriptRoot "..\..\..\.."))
  $candidates.Add("C:\Users\cagda\Documents\GitHub\AAYS")
  $candidates.Add("F:\chatgpt\chat_gpt_clone_1_main")
  $candidates.Add("F:\chatgpt\chat_gpt_clone_1_main_fresh")

  foreach ($candidate in @($candidates.ToArray())) {
    $resolved = Resolve-Path -LiteralPath $candidate -ErrorAction SilentlyContinue
    if ($null -eq $resolved) { continue }
    $root = $resolved.Path
    if (Test-Path -LiteralPath (Join-Path $root "docs/chatgpt_status/_shared")) {
      return $root
    }
  }
  throw "AAYS repo root not found. Start from C:\Users\cagda\Documents\GitHub\AAYS or pass -RepoRoot."
}

function Read-JsonFile {
  param([string]$Path)
  try {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    return Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json -ErrorAction Stop
  } catch {
    return $null
  }
}

function Test-RunnerActive {
  param([string]$LockPath)
  $lock = Read-JsonFile -Path $LockPath
  if ($null -eq $lock -or $null -eq $lock.pid) {
    return [pscustomobject]@{ active = $false; pid = $null }
  }
  $pidValue = [int]$lock.pid
  return [pscustomobject]@{
    active = ($null -ne (Get-Process -Id $pidValue -ErrorAction SilentlyContinue))
    pid = $pidValue
  }
}

$repoRoot = Resolve-AaysRepoRoot -RequestedRoot $RepoRoot
$sharedRoot = Join-Path $repoRoot "docs/chatgpt_status/_shared"
$automationRoot = Join-Path $sharedRoot "automation"
$runner = Join-Path $automationRoot "RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_V5_20260706.ps1"
$builder = Join-Path $automationRoot "BUILD_AAYS_PAGE_PANEL_INDEX.ps1"
$panel = Join-Path $sharedRoot "panel/AAYS_RUNNER_PANEL.ps1"
$stateDir = Join-Path $sharedRoot "state"
$statePath = Join-Path $stateDir "runner_panel_state.json"
$lockPath = Join-Path $stateDir "single_runner.lock.json"
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

if (-not (Test-Path -LiteralPath $runner)) { throw "Missing runner: $runner" }
if (-not (Test-Path -LiteralPath $builder)) { throw "Missing panel builder: $builder" }

& powershell -NoProfile -ExecutionPolicy Bypass -File $builder -RepoRoot $repoRoot -EnsurePageDirs | Out-Null

$runnerState = Test-RunnerActive -LockPath $lockPath
$runnerPid = $runnerState.pid
$runnerActive = [bool]$runnerState.active
if (-not $runnerActive) {
  $proc = Start-Process -FilePath powershell -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $runner,
    "-Loop",
    "-IntervalSeconds",
    "$IntervalSeconds",
    "-MaxTasks",
    "$MaxTasks",
    "-RepoRoot",
    $repoRoot,
    "-RepoFullName",
    $RepoFullName,
    "-MainBranch",
    $MainBranch,
    "-WorkRoot",
    $WorkRoot
  ) -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
  $runnerPid = $proc.Id
  $runnerActive = $true
  Start-Sleep -Seconds 2
}

if (-not $NoPanel -and (Test-Path -LiteralPath $panel)) {
  Start-Process -FilePath powershell -ArgumentList @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $panel
  ) -WorkingDirectory $repoRoot | Out-Null
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $builder -RepoRoot $repoRoot -EnsurePageDirs | Out-Null

$state = [ordered]@{
  last_updated = (Get-Date).ToUniversalTime().ToString("o")
  repo_root = $repoRoot
  repo_full_name = $RepoFullName
  main_branch = $MainBranch
  single_runner_active = [bool]$runnerActive
  runner_pid = $runnerPid
  runner_lock_active = (Test-Path -LiteralPath $lockPath)
  panel_index = "docs/chatgpt_status/_shared/panel/page_status_index_latest.json"
  runner_version = "v5_20260706"
}
$state | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statePath -Encoding UTF8
$state | ConvertTo-Json -Depth 8

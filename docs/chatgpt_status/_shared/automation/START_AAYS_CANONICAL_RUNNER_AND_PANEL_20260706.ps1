[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$RepoFullName = "cagdascagdas100/chat_gpt_clone_1",
  [string]$MainBranch = "codex/aays-single-runner-v5-20260706",
  [string]$WorkRoot = "",
  [int]$IntervalSeconds = 60,
  [int]$MaxTasks = 1,
  [int]$StaleMinutes = 15,
  [switch]$NoPanel,
  [switch]$NoLoop,
  [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$legacyLockGuard = Join-Path $PSScriptRoot "PREPARE_AAYS_LEGACY_RUNNER_LOCK_COMPAT_20260803.py"
$starter = Join-Path $PSScriptRoot "START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1"
if (-not (Test-Path -LiteralPath $legacyLockGuard)) {
  throw "Missing legacy runner lock compatibility guard: $legacyLockGuard"
}
if (-not (Test-Path -LiteralPath $starter)) {
  throw "Missing canonical starter: $starter"
}

$guardArgs = @(
  $legacyLockGuard,
  "--repo-root", $RepoRoot,
  "--main-branch", $MainBranch,
  "--stale-minutes", "$StaleMinutes"
)
& python @guardArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$args = @(
  "-File", $starter,
  "-RepoRoot", $RepoRoot,
  "-RepoFullName", $RepoFullName,
  "-MainBranch", $MainBranch,
  "-WorkRoot", $WorkRoot,
  "-IntervalSeconds", "$IntervalSeconds",
  "-MaxTasks", "$MaxTasks",
  "-StaleMinutes", "$StaleMinutes"
)
if ($NoPanel) { $args += "-NoPanel" }
if ($NoLoop) { $args += "-NoLoop" }
if ($NoPush) { $args += "-NoPush" }

& powershell -NoProfile -ExecutionPolicy Bypass @args
exit $LASTEXITCODE

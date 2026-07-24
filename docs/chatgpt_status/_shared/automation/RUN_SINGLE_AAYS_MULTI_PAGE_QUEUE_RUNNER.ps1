[CmdletBinding()]
param(
  [string]$RepoRoot = "C:\AAYS_WT\AAYS_REPAIR_20260706_1738",
  [string]$RepoFullName = "cagdascagdas100/chat_gpt_clone_1",
  [string]$MainBranch = "codex/aays-single-runner-v5-20260706",
  [string]$WorkRoot = "C:\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES",
  [int]$StaleMinutes = 20,
  [int]$MaxTasks = 1,
  [int]$MaxTasksPerScan = 1,
  [switch]$ScanOnly,
  [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$stableRunner = Join-Path $PSScriptRoot "RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1"
if (-not (Test-Path -LiteralPath $stableRunner)) { throw "Missing stable shared runner: $stableRunner" }
$taskCount = if ($MaxTasks -gt 0) { $MaxTasks } else { $MaxTasksPerScan }
$args = @(
  "-RepoRoot", $RepoRoot,
  "-RepoFullName", $RepoFullName,
  "-MainBranch", $MainBranch,
  "-WorkRoot", $WorkRoot,
  "-StaleMinutes", "$StaleMinutes",
  "-MaxTasks", "$taskCount"
)
if ($ScanOnly) { $args += "-ScanOnly" }
if ($NoPush) { $args += "-NoPush" }
& powershell -NoProfile -ExecutionPolicy Bypass -File $stableRunner @args
exit $LASTEXITCODE

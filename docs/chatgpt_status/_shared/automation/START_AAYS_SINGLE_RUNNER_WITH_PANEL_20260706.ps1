[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [switch]$NoPanel,
  [int]$IntervalSeconds = 60,
  [int]$MaxTasks = 1
)

$canonical = Join-Path $PSScriptRoot "START_AAYS_CANONICAL_RUNNER_AND_PANEL_20260706.ps1"
if (-not (Test-Path -LiteralPath $canonical)) {
  throw "Missing canonical launcher: $canonical"
}

$args = @{
  RepoRoot = $RepoRoot
  IntervalSeconds = $IntervalSeconds
  MaxTasks = $MaxTasks
}
if ($NoPanel) { $args.NoPanel = $true }
& $canonical @args

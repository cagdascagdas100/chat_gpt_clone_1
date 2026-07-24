[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [switch]$EnsurePageDirs
)

$builder = Join-Path $PSScriptRoot "BUILD_AAYS_PAGE_PANEL_INDEX.ps1"
if (-not (Test-Path -LiteralPath $builder)) {
  throw "Missing panel index builder: $builder"
}

$args = @{}
if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) { $args.RepoRoot = $RepoRoot }
if ($EnsurePageDirs) { $args.EnsurePageDirs = $true }
& $builder @args

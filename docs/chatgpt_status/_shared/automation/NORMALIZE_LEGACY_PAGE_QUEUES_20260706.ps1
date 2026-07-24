[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [switch]$WriteAliases
)

$normalizer = Join-Path $PSScriptRoot "NORMALIZE_AAYS_QUEUE_TASKS.ps1"
if (-not (Test-Path -LiteralPath $normalizer)) {
  throw "Missing queue normalizer: $normalizer"
}

$args = @{}
if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) { $args.RepoRoot = $RepoRoot }
if ($WriteAliases) { $args.WriteAliases = $true }
& $normalizer @args

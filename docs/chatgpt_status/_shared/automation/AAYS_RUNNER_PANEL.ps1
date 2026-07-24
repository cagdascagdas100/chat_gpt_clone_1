[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [switch]$Console
)

$ErrorActionPreference = "Stop"
$panel = Join-Path $PSScriptRoot "..\panel\AAYS_RUNNER_PANEL.ps1"
if (-not (Test-Path -LiteralPath $panel)) { throw "Missing panel: $panel" }
$args = @("-File", $panel)
if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) { $args += @("-RepoRoot", $RepoRoot) }
if ($Console) { $args += "-Console" }
& powershell -NoProfile -ExecutionPolicy Bypass @args
exit $LASTEXITCODE

[CmdletBinding()]
param(
  [switch]$Console
)

$automationPanel = Join-Path $PSScriptRoot "..\automation\AAYS_RUNNER_PANEL.ps1"
if (-not (Test-Path -LiteralPath $automationPanel)) {
  throw "Missing automation panel: $automationPanel"
}

$args = @{}
if ($Console) { $args.Console = $true }
& $automationPanel @args

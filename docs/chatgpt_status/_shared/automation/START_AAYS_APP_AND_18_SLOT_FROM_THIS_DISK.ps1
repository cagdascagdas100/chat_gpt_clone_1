[CmdletBinding()]
param([switch]$NoBrowser, [switch]$NoPanel)

$ErrorActionPreference = "Stop"
$implementation = Join-Path $PSScriptRoot "START_AAYS_APP_AND_15_SLOT_FROM_THIS_DISK.ps1"
if (-not (Test-Path -LiteralPath $implementation -PathType Leaf)) {
  throw "APP_AND_COORDINATOR_IMPLEMENTATION_MISSING: $implementation"
}
& $implementation -NoBrowser:$NoBrowser -NoPanel:$NoPanel
exit $LASTEXITCODE

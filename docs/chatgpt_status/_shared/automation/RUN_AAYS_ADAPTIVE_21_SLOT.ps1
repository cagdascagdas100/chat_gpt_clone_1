[CmdletBinding()]
param(
  [ValidateSet("Start", "Stop", "Restart", "Status", "Preflight", "FixtureTest")]
  [string]$Action = "Start",
  [int]$StopTimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"
$implementation = Join-Path $PSScriptRoot "RUN_AAYS_ADAPTIVE_15_WORKER.ps1"
if (-not (Test-Path -LiteralPath $implementation -PathType Leaf)) {
  throw "ADAPTIVE_COORDINATOR_IMPLEMENTATION_MISSING: $implementation"
}
& $implementation -Action $Action -StopTimeoutSeconds $StopTimeoutSeconds
exit $LASTEXITCODE

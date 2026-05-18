$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$QueueRoot = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $QueueRoot "016_CLEAN_FULL_PYTEST_RUNNER.ps1"

if (-not (Test-Path -LiteralPath $Runner)) {
  throw "016 runner not found: $Runner"
}

powershell -ExecutionPolicy Bypass -File $Runner
exit $LASTEXITCODE

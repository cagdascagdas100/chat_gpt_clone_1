[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

if ([string]$env:AAYS_PAGE_KEY -ne 'gas_emissions') {
  throw 'GAS_EMISSIONS_151_WRAPPER_WRONG_PAGE_KEY'
}
if ([string]$env:AAYS_TARGET_BRANCH -ne 'codex/aays-single-runner-v5-20260706') {
  throw 'GAS_EMISSIONS_151_WRAPPER_WRONG_BRANCH'
}

$pipeline = Join-Path $PSScriptRoot 'run_gas_emissions_151_pipeline_20260711.py'
if (-not (Test-Path -LiteralPath $pipeline)) {
  throw 'GAS_EMISSIONS_151_PYTHON_PIPELINE_NOT_FOUND'
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
  & $python.Source $pipeline
  $exitCode = $LASTEXITCODE
} else {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if (-not $py) { throw 'PYTHON_NOT_FOUND_FOR_GAS_EMISSIONS_151' }
  & $py.Source -3 $pipeline
  $exitCode = $LASTEXITCODE
}

if ($exitCode -ne 0) {
  throw "GAS_EMISSIONS_151_PIPELINE_FAILED_EXIT_$exitCode"
}

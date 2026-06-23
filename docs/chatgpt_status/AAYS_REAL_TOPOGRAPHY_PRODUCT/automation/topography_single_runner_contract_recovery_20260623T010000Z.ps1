param(
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
)

$ErrorActionPreference = 'Continue'
$v6 = Join-Path $PSScriptRoot 'topography_single_runner_contract_recovery_20260623T010000Z_v6.ps1'
if(Test-Path -LiteralPath $v6){
  & $v6
  exit $LASTEXITCODE
}
$v5 = Join-Path $PSScriptRoot 'topography_single_runner_contract_recovery_20260623T010000Z_v5.ps1'
if(Test-Path -LiteralPath $v5){
  & $v5
  exit $LASTEXITCODE
}
$v4 = Join-Path $PSScriptRoot 'topography_single_runner_contract_recovery_20260623T010000Z_v4.ps1'
if(Test-Path -LiteralPath $v4){
  & $v4
  exit $LASTEXITCODE
}
Write-Host "Missing delegated automation script: $v6, $v5 and $v4"
exit 2

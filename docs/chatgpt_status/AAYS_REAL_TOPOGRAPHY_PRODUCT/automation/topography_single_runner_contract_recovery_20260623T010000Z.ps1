param(
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
)

$ErrorActionPreference = 'Continue'
$v4 = Join-Path $PSScriptRoot 'topography_single_runner_contract_recovery_20260623T010000Z_v4.ps1'
if(Test-Path -LiteralPath $v4){
  & $v4
  exit $LASTEXITCODE
}
Write-Host "Missing delegated automation script: $v4"
exit 2

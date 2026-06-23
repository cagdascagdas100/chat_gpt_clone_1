param(
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$TaskId = 'topography_single_runner_contract_recovery_20260623T010000Z'
)

$ErrorActionPreference = 'Continue'
$v2 = Join-Path $PSScriptRoot 'topography_single_runner_contract_recovery_20260623T010000Z_v2.ps1'
if(Test-Path $v2){
  & $v2 -PageKey $PageKey -TaskId $TaskId
  exit $LASTEXITCODE
}
Write-Host "Missing delegated automation script"
exit 2

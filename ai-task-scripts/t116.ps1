$ErrorActionPreference='Continue'
$Here=Split-Path -Parent $MyInvocation.MyCommand.Path
$Target=Join-Path $Here 'aays_116_dem_source_acquisition_20260521.ps1'
if(!(Test-Path $Target)){Write-Host 'target missing'; exit 1}
powershell -NoProfile -ExecutionPolicy Bypass -File $Target
exit $LASTEXITCODE

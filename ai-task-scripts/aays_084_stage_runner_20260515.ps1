$ErrorActionPreference = 'Continue'
$ScriptDir = $PSScriptRoot
$Target = Join-Path $ScriptDir 'aays_083_sleepwait_wrapper_fixed_20260514.ps1'
if(!(Test-Path $Target)){ Write-Error 'target missing'; exit 2 }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Target
exit $LASTEXITCODE

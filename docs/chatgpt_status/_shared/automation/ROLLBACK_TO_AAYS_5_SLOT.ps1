[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$root = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("")
$v15 = Join-Path $root "RUN_AAYS_ADAPTIVE_15_WORKER.ps1"
$v5 = Join-Path $root "RUN_AAYS_ADAPTIVE_5_WORKER.ps1"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $v15 -Action Stop | Out-Null
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $v5 -Action Start
exit $LASTEXITCODE
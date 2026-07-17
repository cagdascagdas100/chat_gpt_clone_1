[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("\")
$v3 = Join-Path $root "RUN_AAYS_ADAPTIVE_15_WORKER.ps1"
if (-not (Test-Path -LiteralPath $v3 -PathType Leaf)) { throw "ADAPTIVE_V3_LAUNCHER_MISSING: $v3" }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $v3 -Action Start
exit $LASTEXITCODE

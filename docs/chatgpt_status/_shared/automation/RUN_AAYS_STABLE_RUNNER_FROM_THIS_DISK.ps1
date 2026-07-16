[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("\")
$v2 = Join-Path $root "RUN_AAYS_ADAPTIVE_5_WORKER.ps1"
if (-not (Test-Path -LiteralPath $v2 -PathType Leaf)) { throw "ADAPTIVE_V2_LAUNCHER_MISSING: $v2" }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $v2 -Action Start
exit $LASTEXITCODE

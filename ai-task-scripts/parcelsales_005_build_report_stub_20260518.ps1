$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_005_build_report_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Lines = @()
$Lines += "# PARCELSALES 005 Build Report Stub"
$Lines += ""
$Lines += "Status: draft report shell created"
$Lines += "Output set: historical sales workbook, manifest, quality summary, unmatched records, integration plan"
$Lines += ""
$Lines += "Next: verify files and produce final handoff summary"
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "build_report.md") -Encoding UTF8
Write-Host "PARCELSALES_005_OUTPUT=$OutDir"

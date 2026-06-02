$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_002_source_inventory_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Paths = @(
  "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence",
  "F:\AAYS_DATA\sales_match_program\master\historical_sales_parcel_matched_england_wales.xlsx",
  "F:\AAYS_DATA\sales_match_program\master\master_sales_rows.csv",
  "F:\AAYS_DATA\sales_match_program\master\matching_quality_summary.csv",
  "F:\AAYS_DATA\sales_match_program\master\unmatched_records.csv",
  "F:\AAYS_DATA\sales_match_program\master\program_state.json"
)
$Lines = @()
$Lines += "# PARCELSALES 002 Source Inventory"
$Lines += ""
$Lines += "Output dir: $OutDir"
$Lines += ""
foreach ($p in $Paths) { $Lines += "- $p exists=$(Test-Path -LiteralPath $p)" }
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "source_inventory_report.md") -Encoding UTF8
$Lines | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutDir "source_inventory.json") -Encoding UTF8
Write-Host "PARCELSALES_002_OUTPUT=$OutDir"

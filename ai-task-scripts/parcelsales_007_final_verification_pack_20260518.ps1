$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_007_final_verify_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Paths = @(
"F:\AAYS_DATA\sales_match_program\master\historical_sales_parcel_matched_england_wales.xlsx",
"F:\AAYS_DATA\sales_match_program\master\master_sales_rows.csv",
"F:\AAYS_DATA\sales_match_program\master\matching_quality_summary.csv",
"F:\AAYS_DATA\sales_match_program\master\unmatched_records.csv",
"F:\AAYS_DATA\sales_match_program\master\program_state.json"
)
$Lines = @("# PARCELSALES 007 Final Verification Pack", "", "Output dir: $OutDir", "", "## File checks")
foreach ($p in $Paths) { $Lines += "- $p exists=$(Test-Path -LiteralPath $p)" }
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "final_verification_report.md") -Encoding UTF8
Write-Host "PARCELSALES_007_OUTPUT=$OutDir"

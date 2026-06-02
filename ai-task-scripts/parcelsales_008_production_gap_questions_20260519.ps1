$ErrorActionPreference = "Stop"
$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_008_production_gap_questions_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Paths = @(
"F:\AAYS_DATA\sales_match_program\master\historical_sales_parcel_matched_england_wales.xlsx",
"F:\AAYS_DATA\sales_match_program\master\master_sales_rows.csv",
"F:\AAYS_DATA\sales_match_program\master\matching_quality_summary.csv",
"F:\AAYS_DATA\sales_match_program\master\unmatched_records.csv",
"F:\AAYS_DATA\sales_match_program\master\program_state.json",
"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\scripts",
"C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence\app"
)
$Lines = @()
$Lines += "# PARCELSALES 008 Production Gap Questions"
$Lines += ""
$Lines += "Mode: read-only gap and question report. No DB write. No production acceptance."
$Lines += "Output dir: $OutDir"
$Lines += ""
$Lines += "## Existing path checks"
foreach ($p in $Paths) { $Lines += "- $p exists=$(Test-Path -LiteralPath $p)" }
$Lines += ""
$Lines += "## Questions to answer before real production"
$Lines += "1. Which local file/folder is the authoritative raw official historical sales source?"
$Lines += "2. Which local file/folder is the authoritative parcel or title polygon source?"
$Lines += "3. Should output root remain F:\AAYS_DATA or move to another drive?"
$Lines += "4. Should the next real run write only files, or is database import allowed?"
$Lines += "5. What confidence rule is acceptable for verified parcel match?"
$Lines += "6. Should rows without source/evidence stay unmatched?"
$Lines += "7. Should the next run process a small sample first or full dataset?"
$Lines += ""
$Lines += "## Safe defaults"
$Lines += "- files only"
$Lines += "- no database write"
$Lines += "- no production acceptance"
$Lines += "- rows without evidence stay unmatched"
$Lines += "- start with a small sample before full dataset"
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "production_gap_questions.md") -Encoding UTF8
Write-Host "PARCELSALES_008_OUTPUT=$OutDir"

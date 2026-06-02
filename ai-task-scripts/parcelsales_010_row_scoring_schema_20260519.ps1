$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_010_row_scoring_schema_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Lines = @()
$Lines += "# PARCELSALES 010 Row Scoring Schema"
$Lines += ""
$Lines += "Mode: read-only schema output."
$Lines += "Every sale row must be scored independently."
$Lines += ""
$Lines += "## Score columns"
$Cols = @("row_confidence_score","price_score","date_score","address_score","postcode_score","property_type_score","area_score","parcel_match_score","source_score","evidence_score","conflict_score","row_reliability_band","evidence_sources_used","evidence_missing_fields","needs_review")
foreach ($c in $Cols) { $Lines += "- $c" }
$Lines += ""
$Lines += "## Bands"
$Lines += "VERIFIED: 85-100"
$Lines += "HIGH: 70-84"
$Lines += "MEDIUM: 50-69"
$Lines += "LOW: 25-49"
$Lines += "UNMATCHED: no reliable bridge"
$Lines | Set-Content -LiteralPath (Join-Path $OutDir "row_scoring_schema.md") -Encoding UTF8
Write-Host "PARCELSALES_010_OUTPUT=$OutDir"

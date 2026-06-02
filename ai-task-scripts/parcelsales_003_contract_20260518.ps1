$RunId = Get-Date -Format "yyyyMMdd_HHmmss"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BridgeRoot = Split-Path -Parent $ScriptDir
$OutDir = Join-Path $BridgeRoot "ai-runner-outputs\parcelsales_003_contract_$RunId"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$Text = @()
$Text += "sale_id"
$Text += "parcel_id"
$Text += "title_polygon_id"
$Text += "sale_date"
$Text += "price_gbp"
$Text += "address_text"
$Text += "postcode"
$Text += "property_type"
$Text += "match_class"
$Text += "source_url"
$Text += "evidence_ref"
$Text | Set-Content -LiteralPath (Join-Path $OutDir "excel_columns.txt") -Encoding UTF8
Write-Host "PARCELSALES_003_OUTPUT=$OutDir"

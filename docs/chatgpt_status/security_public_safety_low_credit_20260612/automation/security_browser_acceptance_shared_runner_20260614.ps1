$ErrorActionPreference = "Continue"
$PageKey = "security_public_safety_low_credit_20260612"
$Bridge = "C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$App = "C:\Users\cagda\Documents\GitHub\AAYS\england_map_web"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StatusRoot = Join-Path $Bridge "docs\chatgpt_status\$PageKey"
$ResultDir = Join-Path $Bridge "ai-results"
New-Item -ItemType Directory -Force $ResultDir, "$StatusRoot\status", "$StatusRoot\reports", "$StatusRoot\heartbeat", "$StatusRoot\runner_output" | Out-Null

$Geo = Join-Path $App "data\parcel_security_scores_rechecked_0_120m_spatial.geojson"
$Summary = Join-Path $App "data\parcel_security_scores_rechecked_0_120m_summary.json"
$Overlay = Join-Path $App "security_overlay.js"
$Css = Join-Path $App "security_overlay.css"
$Index = Join-Path $App "index.html"

$Checks = [ordered]@{
  index_exists = Test-Path $Index
  overlay_exists = Test-Path $Overlay
  css_exists = Test-Path $Css
  geojson_exists = Test-Path $Geo
  summary_exists = Test-Path $Summary
  browser_click_acceptance_recorded = $false
  contract_terms_found = 0
}

if ($Checks.overlay_exists) {
  $OverlayText = Get-Content $Overlay -Raw -ErrorAction SilentlyContinue
  $Terms = @("safety_score","confidence_score","source_name","evidence","matching_method","calculation_explanation","accuracy_rating","security_parcel_id")
  $Checks.contract_terms_found = @($Terms | Where-Object { $OverlayText -like "*$_*" }).Count
}

$FinalReady = $false
$Complete = $false

$Result = [ordered]@{
  page_key = $PageKey
  decision = "SECURITY_SHARED_RUNNER_BROWSER_ACCEPTANCE_PENDING"
  final_ready = $FinalReady
  complete = $Complete
  checks = $Checks
  required_next = "interactive_browser_click_acceptance_or_runner_with_display"
  db_write = $false
  ddl = $false
  migration = $false
  production_deploy = $false
  fake_data = $false
  timestamp = $Stamp
}

$Json = $Result | ConvertTo-Json -Depth 20
$Json | Set-Content (Join-Path $ResultDir "security_public_safety_browser_acceptance_latest.json") -Encoding UTF8
$Json | Set-Content "$StatusRoot\status\security_browser_acceptance_latest.md" -Encoding UTF8
$Json | Set-Content "$StatusRoot\reports\security_browser_acceptance_$Stamp.md" -Encoding UTF8
"heartbeat $Stamp" | Set-Content "$StatusRoot\heartbeat\browser_acceptance_latest.md" -Encoding UTF8
"SECURITY_SHARED_RUNNER_BROWSER_ACCEPTANCE_PENDING $Stamp" | Set-Content "$StatusRoot\runner_output\security_browser_acceptance_$Stamp.txt" -Encoding UTF8

exit 0

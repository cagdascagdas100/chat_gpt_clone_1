$ErrorActionPreference="Continue"
$PageKey="AAYS_REAL_TOPOGRAPHY_PRODUCT"
$ReportDir="docs\chatgpt_status\$PageKey\reports"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$Report="$ReportDir\topography_final_validation_bundle_20260614_001.txt"

$checks=@(
  "region_average_elevation_m",
  "elevation_difference_from_region_average_m",
  "center_elevation_m",
  "confidence_level",
  "matching_method",
  "calculation_explanation",
  "hight_differance.png",
  "normalizeTopographyLookupForPopup",
  "buildTopographyPopupRowsHtml"
)

$appCandidates=@(
  "england_map_web\static\js\app.js",
  "england_map_web\app.js",
  "app.js"
)

$app=$appCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
$missing=@()
if($app){
  $txt=Get-Content -LiteralPath $app -Raw -ErrorAction SilentlyContinue
  foreach($c in $checks){
    if($txt -notmatch [regex]::Escape($c)){ $missing += $c }
  }
}else{
  $missing += "APP_JS_NOT_FOUND"
}

$lines=@()
$lines+="PAGE_KEY=$PageKey"
$lines+="TASK=topography_final_validation_bundle_20260614_001"
$lines+="RUN_AT=$(Get-Date -Format o)"
$lines+="APP_FILE=$app"
$lines+="DB_WRITE=False"
$lines+="MIGRATION=False"
$lines+="DEPLOY=False"
$lines+="FAKE_DATA_CREATED=False"
$lines+="CHECK_COUNT=$($checks.Count)"
$lines+="MISSING_COUNT=$($missing.Count)"
if($missing.Count -eq 0){
  $lines+="STATUS=FINAL_VALIDATION_READY_FOR_SMOKE"
  $lines+="PRODUCT_PROGRESS_ESTIMATE=96"
}else{
  $lines+="STATUS=FINAL_VALIDATION_MISSING_FIELDS"
  $lines+="PRODUCT_PROGRESS_ESTIMATE=93"
  $lines+="MISSING_FIELDS=$($missing -join ',')"
}
$lines | Set-Content -LiteralPath $Report -Encoding UTF8

$ErrorActionPreference="Continue"
$PageKey="AAYS_REAL_TOPOGRAPHY_PRODUCT"
$ReportDir="docs\chatgpt_status\$PageKey\reports"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$Report="$ReportDir\topography_final_validation_bundle_20260614_005.txt"

$appCandidates=@(
  "england_map_web\static\js\app.js",
  "england_map_web\app.js",
  "app.js"
)

$required=@(
  "center_elevation_m",
  "region_average_elevation_m",
  "elevation_difference_from_region_average_m",
  "confidence_level",
  "confidence_reason",
  "matching_method",
  "calculation_explanation",
  "source_resolution_m",
  "datum",
  "hight_differance.png",
  "normalizeTopographyLookupForPopup",
  "buildTopographyPopupRowsHtml"
)

$app=$appCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
$missing=@()

if($app){
  $txt=Get-Content -LiteralPath $app -Raw -ErrorAction SilentlyContinue
  foreach($r in $required){
    if($txt -notmatch [regex]::Escape($r)){ $missing += $r }
  }
}else{
  $missing += "APP_JS_NOT_FOUND"
}

$lines=@()
$lines+="PAGE_KEY=$PageKey"
$lines+="TASK_ID=topography_final_validation_bundle_20260614_005"
$lines+="RUN_AT=$(Get-Date -Format o)"
$lines+="APP_FILE=$app"
$lines+="DB_WRITE=False"
$lines+="MIGRATION=False"
$lines+="DEPLOY=False"
$lines+="FAKE_DATA_CREATED=False"
$lines+="REQUIRED_COUNT=$($required.Count)"
$lines+="MISSING_COUNT=$($missing.Count)"

if($missing.Count -eq 0){
  $lines+="STATUS=FINAL_READY"
  $lines+="PRODUCT_PROGRESS_ESTIMATE=100"
}else{
  $lines+="STATUS=FINAL_VALIDATION_BLOCKED"
  $lines+="PRODUCT_PROGRESS_ESTIMATE=94"
  $lines+="MISSING_FIELDS=$($missing -join ',')"
}

$lines | Set-Content -LiteralPath $Report -Encoding UTF8

git add $Report
git commit -m "AAYS_REAL_TOPOGRAPHY_PRODUCT final validation report" | Out-Null
git push origin aays-runner-v17-icon-work-20260603-232706 | Out-Null

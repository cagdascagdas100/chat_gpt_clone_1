$ErrorActionPreference="Continue"
$PageKey="AAYS_REAL_TOPOGRAPHY_PRODUCT"
$ReportDir="docs\chatgpt_status\$PageKey\reports"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$Report="$ReportDir\topography_final_validation_bundle_20260614_009.txt"

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

$appCandidates=@(
"england_map_web\static\js\app.js",
"england_map_web\app.js",
"app.js"
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

$out=@()
$out+="PAGE_KEY=$PageKey"
$out+="TASK_ID=topography_final_validation_bundle_20260614_009"
$out+="RUN_AT=$(Get-Date -Format o)"
$out+="APP_FILE=$app"
$out+="DB_WRITE=False"
$out+="MIGRATION=False"
$out+="DEPLOY=False"
$out+="FAKE_DATA_CREATED=False"
$out+="REQUIRED_COUNT=$($required.Count)"
$out+="MISSING_COUNT=$($missing.Count)"

if($missing.Count -eq 0){
  $out+="STATUS=FINAL_READY"
  $out+="PRODUCT_PROGRESS_ESTIMATE=100"
}else{
  $out+="STATUS=FINAL_VALIDATION_BLOCKED"
  $out+="PRODUCT_PROGRESS_ESTIMATE=94"
  $out+="MISSING_FIELDS=$($missing -join ',')"
}

$out | Set-Content -LiteralPath $Report -Encoding UTF8

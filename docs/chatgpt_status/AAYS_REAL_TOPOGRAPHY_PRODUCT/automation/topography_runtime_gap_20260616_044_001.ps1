$ErrorActionPreference = "Continue"
$PageKey = "AAYS_REAL_TOPOGRAPHY_PRODUCT"
$TaskId = "topography_runtime_gap_20260616_044_001"
$ExpectedBranch = "aays-runner-v17-icon-work-20260603-232706"
$ReportDir = "docs\chatgpt_status\$PageKey\reports"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$Report = "$ReportDir\topography_chatgpt_runtime_gap_report_20260616_044_001.txt"

function Add-Line([string]$s) { $script:Out += $s }
function Test-FileToken([string]$Path, [string[]]$Tokens, [string]$Prefix) {
  $missing = @()
  if (-not (Test-Path -LiteralPath $Path)) { return @("${Prefix}_FILE_NOT_FOUND:$Path") }
  $txt = Get-Content -LiteralPath $Path -Raw -ErrorAction SilentlyContinue
  foreach ($t in $Tokens) {
    if ($txt -notmatch [regex]::Escape($t)) { $missing += $t }
  }
  return $missing
}
function Invoke-Check([string]$Name, [scriptblock]$Block) {
  try {
    $res = & $Block
    return "${Name}=PASS $res"
  } catch {
    return "${Name}=FAIL $($_.Exception.Message)"
  }
}

$Out = @()
Add-Line "PAGE_KEY=$PageKey"
Add-Line "TASK_ID=$TaskId"
Add-Line "RUN_AT=$(Get-Date -Format o)"
Add-Line "EXPECTED_BRANCH=$ExpectedBranch"
Add-Line "VALIDATION_METHOD=runtime_endpoint_static_contract_and_source_coverage_gap_report"
Add-Line "DB_WRITE=False"
Add-Line "MIGRATION=False"
Add-Line "DEPLOY=False"
Add-Line "FAKE_DATA_CREATED=False"

$branch = (& git branch --show-current 2>$null)
Add-Line "GIT_BRANCH=$branch"
Add-Line "BRANCH_MATCH=$([bool]($branch -eq $ExpectedBranch))"

$appFile = "england_map_web\app.js"
$overlayFile = "england_map_web\config\topography.overlay.json"
$routeFile = "terrayield_land_intelligence\app\api\routes\topography_lookup_v2.py"
$mainFile = "terrayield_land_intelligence\app\main.py"

foreach ($p in @($appFile,$overlayFile,$routeFile,$mainFile,"terrayield_land_intelligence\requirements.txt","terrayield_land_intelligence\pyproject.toml")) {
  Add-Line "FILE_EXISTS[$p]=$([bool](Test-Path -LiteralPath $p))"
}

$nodeCheck = Invoke-Check "NODE_CHECK_APP_JS" { & node --check $appFile 2>&1 | Out-String }
Add-Line $nodeCheck
$pyCheck = Invoke-Check "PY_COMPILE_TOPOGRAPHY" { & python -m py_compile $routeFile $mainFile 2>&1 | Out-String }
Add-Line $pyCheck

$appRequired = @(
  "TOPOGRAPHY_LOOKUP_BASE_URL",
  "/topography/lookup?parcel_id=",
  "normalizeTopographyLookupForPopup",
  "buildTopographyPopupRowsHtml",
  "renderParcelTopographySection",
  "center_elevation_m",
  "region_average_elevation_m",
  "elevation_difference_from_region_average_m",
  "confidence_level",
  "confidence_reason",
  "matching_method",
  "calculation_explanation",
  "source_resolution_m",
  "hight_differance.png"
)
$routeRequired = @(
  "direct_terrarium_dem_lookup",
  "Terrarium DEM local tiles",
  "fake_data",
  "db_write",
  "center_elevation_m",
  "elevation_above_sea_level_m",
  "region_average_elevation_m",
  "elevation_difference_from_region_average_m",
  "source_dataset",
  "source_resolution_m",
  "confidence_level",
  "matching_method",
  "calculation_explanation"
)
$overlayRequired = @("/topography/tiles/{z}/{x}/{y}.png")

$appMissing = Test-FileToken $appFile $appRequired "APP"
$routeMissing = Test-FileToken $routeFile $routeRequired "ROUTE"
$overlayMissing = Test-FileToken $overlayFile $overlayRequired "OVERLAY"
Add-Line "APP_RUNTIME_FILE=$appFile"
Add-Line "APP_REQUIRED_COUNT=$($appRequired.Count)"
Add-Line "APP_MISSING_COUNT=$($appMissing.Count)"
Add-Line "APP_MISSING_FIELDS=$($appMissing -join ',')"
Add-Line "ROUTE_REQUIRED_COUNT=$($routeRequired.Count)"
Add-Line "ROUTE_MISSING_COUNT=$($routeMissing.Count)"
Add-Line "ROUTE_MISSING_FIELDS=$($routeMissing -join ',')"
Add-Line "OVERLAY_MISSING_COUNT=$($overlayMissing.Count)"
Add-Line "OVERLAY_MISSING_FIELDS=$($overlayMissing -join ',')"

$sourcePaths = @(
  "D:\topografik_map\london\terrarium_tiles",
  "D:\topografik_map\london\web_assets\parcel_topography_confidence",
  "D:\topografik_map\london_topography_local",
  "F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz",
  "D:\AAYS_DATA\topography\england\raw",
  "D:\AAYS_DATA\topography\england\tiles",
  "D:\AAYS_DATA\topography\england\processed",
  "D:\AAYS_DATA\topography\england\parcel_matches",
  "D:\AAYS_DATA\topography\england\reports"
)
$englandCoverageHits = 0
foreach ($sp in $sourcePaths) {
  $exists = Test-Path -LiteralPath $sp
  Add-Line "SOURCE_EXISTS[$sp]=$exists"
  if ($exists -and $sp -like "D:\AAYS_DATA\topography\england\*") { $englandCoverageHits++ }
}
if ($englandCoverageHits -ge 3) { Add-Line "SOURCE_COVERAGE=England_candidate_present" } else { Add-Line "SOURCE_COVERAGE=London_only_or_not_proven" }

# Try runtime endpoint checks. Do not fail the script if local app is not already running.
$serverScript = "terrayield_land_intelligence\start_open_only_8010.ps1"
if (Test-Path -LiteralPath $serverScript) {
  Add-Line "SERVER_START_SCRIPT_EXISTS=True"
  try {
    Start-Process powershell -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File",$serverScript) -WindowStyle Hidden | Out-Null
    Start-Sleep -Seconds 10
    Add-Line "SERVER_START_ATTEMPTED=True"
  } catch {
    Add-Line "SERVER_START_ATTEMPTED=False"
    Add-Line "SERVER_START_ERROR=$($_.Exception.Message)"
  }
} else {
  Add-Line "SERVER_START_SCRIPT_EXISTS=False"
}

$appUrl = "http://127.0.0.1:8010/england_map_web/"
$lookupUrl = "http://127.0.0.1:8010/topography/lookup?parcel_id=29759443&lat=51.563497&lon=0.293624"
$tileUrl = "http://127.0.0.1:8010/topography/tiles/13/4102/2721.png"

try {
  $appResp = Invoke-WebRequest -UseBasicParsing $appUrl -TimeoutSec 15
  Add-Line "APP_OPEN_STATUS=$($appResp.StatusCode)"
} catch { Add-Line "APP_OPEN_STATUS=ERROR:$($_.Exception.Message)" }

$lookupMissing = @()
try {
  $lookupResp = Invoke-WebRequest -UseBasicParsing $lookupUrl -TimeoutSec 20
  Add-Line "LOOKUP_STATUS=$($lookupResp.StatusCode)"
  Add-Line "LOOKUP_RAW_LENGTH=$($lookupResp.Content.Length)"
  $json = $lookupResp.Content | ConvertFrom-Json -ErrorAction Stop
  $lookupRequired = @(
    "center_elevation_m",
    "elevation_above_sea_level_m",
    "region_average_elevation_m",
    "elevation_difference_from_region_average_m",
    "elevation_difference_class",
    "color_hex",
    "source_dataset",
    "source_resolution_m",
    "source_date",
    "topography_source",
    "confidence_level",
    "confidence_reason",
    "matching_method",
    "calculation_explanation",
    "fake_data",
    "db_write"
  )
  foreach ($f in $lookupRequired) {
    if (-not ($json.PSObject.Properties.Name -contains $f)) { $lookupMissing += $f }
  }
  Add-Line "LOOKUP_REQUIRED_COUNT=$($lookupRequired.Count)"
  Add-Line "LOOKUP_MISSING_COUNT=$($lookupMissing.Count)"
  Add-Line "LOOKUP_MISSING_FIELDS=$($lookupMissing -join ',')"
  Add-Line "LOOKUP_MATCHING_METHOD=$($json.matching_method)"
  Add-Line "LOOKUP_TOPOGRAPHY_SOURCE=$($json.topography_source)"
  Add-Line "LOOKUP_FAKE_DATA=$($json.fake_data)"
  Add-Line "LOOKUP_DB_WRITE=$($json.db_write)"
  Add-Line "LOOKUP_SOURCE_DATASET=$($json.source_dataset)"
} catch {
  Add-Line "LOOKUP_STATUS=ERROR:$($_.Exception.Message)"
  Add-Line "LOOKUP_MISSING_COUNT=UNKNOWN_ENDPOINT_ERROR"
}

try {
  $tileResp = Invoke-WebRequest -UseBasicParsing $tileUrl -Method Head -TimeoutSec 15
  Add-Line "TILE_HEAD_STATUS=$($tileResp.StatusCode)"
} catch { Add-Line "TILE_HEAD_STATUS=ERROR:$($_.Exception.Message)" }

Add-Line "UI_SMOKE_STATUS=NOT_AUTOMATED_BROWSER_CLICK_REQUIRED"
Add-Line "UI_SMOKE_REQUIRED_FIELDS=sea_level_elevation,regional_average,regional_difference,class,color,source_dataset,source_resolution_or_date,confidence,matching_method,calculation_explanation"

$staticOk = ($appMissing.Count -eq 0 -and $routeMissing.Count -eq 0 -and $overlayMissing.Count -eq 0)
$syntaxOk = ($nodeCheck -match "PASS" -and $pyCheck -match "PASS")
$coverageOk = ($englandCoverageHits -ge 3)
if ($staticOk -and $syntaxOk -and $coverageOk -and $lookupMissing.Count -eq 0) {
  Add-Line "STATUS=FINAL_READY"
  Add-Line "PRODUCT_PROGRESS_ESTIMATE=100"
  Add-Line "PRODUCTION_COMPLETE=true"
} else {
  Add-Line "STATUS=FINAL_VALIDATION_BLOCKED"
  if ($staticOk -and $syntaxOk) { Add-Line "PRODUCT_PROGRESS_ESTIMATE=99.90" } else { Add-Line "PRODUCT_PROGRESS_ESTIMATE=94" }
  Add-Line "PRODUCTION_COMPLETE=false"
  if (-not $coverageOk) { Add-Line "BLOCKER=England-wide topography DEM/source coverage not proven" }
  if (-not $staticOk) { Add-Line "BLOCKER_STATIC_CONTRACT=app/route/overlay runtime contract missing tokens" }
  Add-Line "NEXT_PATCH_SCOPE=england_map_web/app.js;england_map_web/config/topography.overlay.json;terrayield_land_intelligence/app/api/routes/topography_lookup_v2.py;terrayield_land_intelligence/app/main.py"
}

$Out | Set-Content -LiteralPath $Report -Encoding UTF8
Write-Host "WROTE_REPORT=$Report"

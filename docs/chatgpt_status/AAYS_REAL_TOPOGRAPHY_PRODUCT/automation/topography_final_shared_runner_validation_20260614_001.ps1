$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$Report = "$ReportDir/topography_final_shared_runner_report_$Stamp.txt"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$AppCandidates = @(
  'england_map_web/static/app.js',
  'england_map_web/app.js',
  'terrayield_land_intelligence/england_map_web/static/app.js',
  'terrayield_land_intelligence/england_map_web/app.js'
)
$App = $null
foreach ($Candidate in $AppCandidates) {
  if (Test-Path $Candidate) { $App = $Candidate; break }
}

$Text = ''
if ($App) { $Text = Get-Content $App -Raw }
$HasIcon = $Text.Contains('hight_differance.png')
$HasRegionAverage = $Text.Contains('region_average_elevation_m')
$HasRegionDifference = $Text.Contains('elevation_difference_from_region_average_m')
$HasLookupBinding = ($Text.Contains('normalizeTopographyLookupForPopup') -or $Text.Contains('topography_lookup'))
$Inventory = Get-ChildItem $ReportDir -Filter 'real_topography_source_inventory_*.txt' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$Ready = [bool]$App -and $HasIcon -and $HasRegionAverage -and $HasRegionDifference -and $HasLookupBinding -and [bool]$Inventory

@(
  "PAGE_KEY=$PageKey",
  "RUN_AT=$(Get-Date -Format o)",
  "MODE=FINAL_SHARED_RUNNER_VALIDATION",
  "APP_JS_PATH=$App",
  "HAS_HIGHT_DIFFERANCE_ICON=$HasIcon",
  "HAS_REGION_AVERAGE_ELEVATION_M=$HasRegionAverage",
  "HAS_ELEVATION_DIFFERENCE_FROM_REGION_AVERAGE_M=$HasRegionDifference",
  "HAS_TOPOGRAPHY_LOOKUP_BINDING=$HasLookupBinding",
  "INVENTORY_REPORT_FOUND=$([bool]$Inventory)",
  "FINAL_READY=$Ready",
  "PRODUCT_PROGRESS_ESTIMATE=$(if($Ready){100}else{90})",
  "STATUS=$(if($Ready){'FINAL_READY'}else{'FINAL_READY_BLOCKED'})"
) | Set-Content -Path $Report -Encoding UTF8

Write-Output "DONE=$Report"

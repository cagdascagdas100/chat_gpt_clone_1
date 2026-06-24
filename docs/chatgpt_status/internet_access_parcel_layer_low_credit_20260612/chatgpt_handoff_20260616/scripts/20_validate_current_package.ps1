$ErrorActionPreference = "Stop"

$packageRoot = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610"
$geojson = Join-Path $packageRoot "processed\parcel_internet_access_scores.geojson"
$scoresCsv = Join-Path $packageRoot "processed\parcel_internet_access_scores.csv"
$factorCsv = Join-Path $packageRoot "processed\parcel_internet_access_factor_breakdown.csv"
$manifest = Join-Path $packageRoot "manifests\calculation_manifest.json"
$xlsx = Join-Path $packageRoot "reports\internet_access_parcel_report.xlsx"

Write-Output "package_root=$packageRoot"
Write-Output "geojson_exists=$(Test-Path $geojson)"
Write-Output "scores_csv_exists=$(Test-Path $scoresCsv)"
Write-Output "factor_csv_exists=$(Test-Path $factorCsv)"
Write-Output "manifest_exists=$(Test-Path $manifest)"
Write-Output "xlsx_exists=$(Test-Path $xlsx)"

if (Test-Path $manifest) {
  $json = Get-Content $manifest -Raw | ConvertFrom-Json
  Write-Output "status=$($json.status)"
  Write-Output "geometry_policy=$($json.geometry_policy)"
  Write-Output "db_write=$($json.db_write)"
  Write-Output "production_deploy=$($json.production_deploy)"
}

if (Test-Path $geojson) {
  $firstLines = Get-Content $geojson -TotalCount 20
  Write-Output "geojson_head_begin"
  $firstLines | ForEach-Object { Write-Output $_ }
  Write-Output "geojson_head_end"
}

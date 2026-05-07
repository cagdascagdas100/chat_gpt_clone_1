$ErrorActionPreference = 'Continue'

$PlanBase = 'D:\6 color parcells\plan_l_run01'
$Csv = Join-Path $PlanBase 'output\london_6color.csv'
$GeoJson = Join-Path $PlanBase 'output\london_6color.geojson'
$QaReport = Join-Path $PlanBase 'output\qa\PLAN_L_DEEP_QA_REPORT.md'
$QaJson = Join-Path $PlanBase 'output\qa\plan_l_deep_qa_report.json'
$FinalPackages = Join-Path $PlanBase 'final_packages'
$Expected = @('use6_class','use6_color','use6_confidence','use6_sources')

Write-Output 'PROJECT=terrayield'
Write-Output 'TASK=terrayield-141-final-validation-readonly'
Write-Output 'MODE=read_only_final_validation_after_use6_patch'
Write-Output "PLAN_BASE=$PlanBase"
Write-Output "PLAN_BASE_EXISTS=$((Test-Path $PlanBase))"

Write-Output '--- CSV HEADER VALIDATION ---'
if (Test-Path $Csv) {
  $firstLine = Get-Content -Path $Csv -TotalCount 1 -Encoding UTF8
  $headers = $firstLine -split ','
  Write-Output "CSV_EXISTS=PASS"
  Write-Output "CSV_FILE=$Csv"
  Write-Output "CSV_HEADER_COUNT=$($headers.Count)"
  foreach ($c in $Expected) {
    Write-Output "CSV_HAS_$c=$($headers -contains $c)"
  }
  $rowCount = ((Get-Content -Path $Csv -Encoding UTF8 | Measure-Object -Line).Lines - 1)
  Write-Output "CSV_ROWS=$rowCount"
  Write-Output "CSV_ROWS_34864=$($rowCount -eq 34864)"
} else {
  Write-Output "CSV_EXISTS=FAIL"
}

Write-Output '--- GEOJSON PROPERTY VALIDATION ---'
if (Test-Path $GeoJson) {
  try {
    $json = Get-Content -Raw -Encoding UTF8 $GeoJson | ConvertFrom-Json
    $features = @($json.features)
    $props = $features[0].properties
    $propNames = @($props.PSObject.Properties.Name)
    Write-Output "GEOJSON_EXISTS=PASS"
    Write-Output "GEOJSON_FILE=$GeoJson"
    Write-Output "GEOJSON_FEATURES=$($features.Count)"
    Write-Output "GEOJSON_FEATURES_34864=$($features.Count -eq 34864)"
    foreach ($c in $Expected) {
      Write-Output "GEOJSON_HAS_$c=$($propNames -contains $c)"
    }
  } catch {
    Write-Output "GEOJSON_PARSE=FAIL $($_.Exception.Message)"
  }
} else {
  Write-Output "GEOJSON_EXISTS=FAIL"
}

Write-Output '--- QA REPORT VALIDATION ---'
if (Test-Path $QaReport) {
  $qaText = Get-Content -Raw -Encoding UTF8 $QaReport
  Write-Output "QA_REPORT_EXISTS=PASS"
  Write-Output "QA_REPORT=$QaReport"
  Write-Output "QA_WARNINGS_NONE=$($qaText -match '## Warnings\s*- none')"
  Write-Output "QA_MISSING_EXPECTED_COLUMNS_PRESENT=$($qaText -match 'missing expected columns')"
  Write-Output 'QA_REPORT_HEAD_BEGIN'
  Get-Content -Encoding UTF8 $QaReport -TotalCount 40 | ForEach-Object { Write-Output $_ }
  Write-Output 'QA_REPORT_HEAD_END'
} else {
  Write-Output "QA_REPORT_EXISTS=FAIL"
}

Write-Output '--- FINAL PACKAGE VALIDATION ---'
if (Test-Path $FinalPackages) {
  $latestDir = Get-ChildItem -Directory $FinalPackages -Filter 'terrayield-112-plan-l-recovery-final-pack_*' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  $latestZip = Get-ChildItem -File $FinalPackages -Filter 'terrayield-112-plan-l-recovery-final-pack_*.zip' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  Write-Output "FINAL_PACKAGE_DIR=$($latestDir.FullName)"
  Write-Output "FINAL_PACKAGE_DIR_EXISTS=$($null -ne $latestDir)"
  Write-Output "FINAL_PACKAGE_ZIP=$($latestZip.FullName)"
  Write-Output "FINAL_PACKAGE_ZIP_EXISTS=$($null -ne $latestZip)"
  if ($latestZip) { Write-Output "FINAL_PACKAGE_ZIP_BYTES=$($latestZip.Length)" }
} else {
  Write-Output "FINAL_PACKAGES_ROOT_EXISTS=FAIL"
}

Write-Output '--- OVERALL ---'
Write-Output 'EXPECTED_OUTCOME=CSV_AND_GEOJSON_HAVE_USE6_COLUMNS_AND_QA_WARNINGS_NONE'
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_141_FINAL_VALIDATION_READONLY_DONE'

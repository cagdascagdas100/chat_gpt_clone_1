$Repo="C:\Users\cagda\Documents\GitHub\AAYS"
$Branch="feature/terrayield-aays-integration"
$WorkRoot="F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610"
$StatusRoot="$Repo\docs\chatgpt_status"
$Reports="$StatusRoot\reports"
$Out="$StatusRoot\runner_outputs"
$Task="internet-access-092-build-processed-package"

New-Item -ItemType Directory -Force $Reports,$Out,"$WorkRoot\processed","$WorkRoot\manifests","$WorkRoot\reports" | Out-Null

$ReportTxt="$Reports\$Task.txt"
$ReportJson="$Reports\$Task.json"
$SourceManifest="$WorkRoot\manifests\source_manifest.json"
$HashManifest="$WorkRoot\manifests\hash_manifest.csv"
$ScoresCsv="$WorkRoot\processed\parcel_internet_access_scores.csv"
$BreakdownCsv="$WorkRoot\processed\parcel_internet_access_factor_breakdown.csv"
$ScoresGeojson="$WorkRoot\processed\parcel_internet_access_scores.geojson"
$CalcManifest="$WorkRoot\manifests\calculation_manifest.json"
$ExcelReport="$WorkRoot\reports\internet_access_parcel_report.xlsx"

cd $Repo
"task_id=$Task" | Set-Content $ReportTxt -Encoding UTF8
"status=STARTED_PROCESSED_PACKAGE_BUILD" | Add-Content $ReportTxt
"branch=$Branch" | Add-Content $ReportTxt
"work_root=$WorkRoot" | Add-Content $ReportTxt
"DB_WRITE=false" | Add-Content $ReportTxt
"MIGRATION=false" | Add-Content $ReportTxt
"PRODUCTION_DEPLOY=false" | Add-Content $ReportTxt
"FAKE_DATA=false" | Add-Content $ReportTxt

$rawFiles=@()
if (Test-Path "$WorkRoot\raw") {
  $rawFiles=Get-ChildItem "$WorkRoot\raw" -File -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
}

$sourceManifestExists=Test-Path $SourceManifest
$hashManifestExists=Test-Path $HashManifest
$outputsReady=(Test-Path $ScoresCsv) -and (Test-Path $BreakdownCsv) -and (Test-Path $ScoresGeojson) -and (Test-Path $CalcManifest) -and (Test-Path $ExcelReport)

if ($outputsReady) {
  $status="PROCESSED_PACKAGE_READY"
  $completion=60
  $next="validate_api_ui_integration"
} else {
  $status="BLOCKED_MISSING_REAL_SOURCE_DATA"
  $completion=5
  $next="provide_or_download_official_machine_readable_internet_access_tables"
  "reason=source discovery completed, but required processed output files are not present and no fake data is allowed" | Add-Content $ReportTxt
}

"status=$status" | Add-Content $ReportTxt
"completion_percent=$completion" | Add-Content $ReportTxt
"source_manifest_exists=$sourceManifestExists" | Add-Content $ReportTxt
"hash_manifest_exists=$hashManifestExists" | Add-Content $ReportTxt
"raw_file_count=$($rawFiles.Count)" | Add-Content $ReportTxt
"scores_csv_exists=$(Test-Path $ScoresCsv)" | Add-Content $ReportTxt
"breakdown_csv_exists=$(Test-Path $BreakdownCsv)" | Add-Content $ReportTxt
"scores_geojson_exists=$(Test-Path $ScoresGeojson)" | Add-Content $ReportTxt
"calculation_manifest_exists=$(Test-Path $CalcManifest)" | Add-Content $ReportTxt
"excel_report_exists=$(Test-Path $ExcelReport)" | Add-Content $ReportTxt
"manual_stdout_required=false" | Add-Content $ReportTxt

@{
  task_id=$Task
  status=$status
  completion_percent=$completion
  next_action=$next
  work_root=$WorkRoot
  source_manifest_exists=$sourceManifestExists
  hash_manifest_exists=$hashManifestExists
  raw_file_count=$rawFiles.Count
  output_exists=@{
    scores_csv=(Test-Path $ScoresCsv)
    breakdown_csv=(Test-Path $BreakdownCsv)
    scores_geojson=(Test-Path $ScoresGeojson)
    calculation_manifest=(Test-Path $CalcManifest)
    excel_report=(Test-Path $ExcelReport)
  }
  required_outputs=@{
    scores_csv=$ScoresCsv
    breakdown_csv=$BreakdownCsv
    scores_geojson=$ScoresGeojson
    calculation_manifest=$CalcManifest
    excel_report=$ExcelReport
  }
  db_write=$false
  migration=$false
  production_deploy=$false
  fake_data=$false
  manual_stdout_required=$false
  generated_at=(Get-Date -Format s)
} | ConvertTo-Json -Depth 8 | Set-Content $ReportJson -Encoding UTF8

Copy-Item $ReportJson "$Out\latest_output.json" -Force

git add docs/chatgpt_status/reports/$Task.txt docs/chatgpt_status/reports/$Task.json docs/chatgpt_status/runner_outputs/latest_output.json
$changed=(git status --porcelain)
if ($changed) {
  git commit -m "Run internet access 092 processed package check"
  git pull --rebase origin $Branch
  git push origin $Branch
}

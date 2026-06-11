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
$DownloadManifest="$WorkRoot\manifests\download_manifest.json"
$DownloadHashManifest="$WorkRoot\manifests\download_hash_manifest.csv"
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
  $rawFiles=Get-ChildItem "$WorkRoot\raw" -File -Recurse -ErrorAction SilentlyContinue
}

$machineReadable=@()
$htmlLike=@()
foreach ($f in $rawFiles) {
  $ext=$f.Extension.ToLowerInvariant()
  $isMachine=($ext -in @('.csv','.tsv','.xlsx','.xls','.zip','.json','.geojson','.parquet','.gpkg'))
  $head=''
  try {
    $bytes=[System.IO.File]::ReadAllBytes($f.FullName)
    $take=[Math]::Min(512,[int]$bytes.Length)
    if ($take -gt 0) { $head=[System.Text.Encoding]::UTF8.GetString($bytes,0,$take) }
  } catch {}
  $looksHtml=($head -match '<html|<!doctype html|<head|<body')
  if ($isMachine -and -not $looksHtml) { $machineReadable += $f.FullName }
  if ($looksHtml) { $htmlLike += $f.FullName }
}

$sourceManifestExists=Test-Path $SourceManifest
$hashManifestExists=(Test-Path $HashManifest) -or (Test-Path $DownloadHashManifest)
$outputsReady=(Test-Path $ScoresCsv) -and (Test-Path $BreakdownCsv) -and (Test-Path $ScoresGeojson) -and (Test-Path $CalcManifest) -and (Test-Path $ExcelReport)

if ($outputsReady) {
  $status="PROCESSED_PACKAGE_READY"
  $completion=60
  $next="validate_api_ui_integration"
} elseif ($machineReadable.Count -gt 0) {
  $status="BLOCKED_MACHINE_READABLE_SOURCES_PRESENT_BUT_TRANSFORM_NOT_IMPLEMENTED"
  $completion=20
  $next="implement_transform_from_official_tables_to_parcel_scores"
  "reason=machine_readable_source_files_present; transform step is required and no fake data is allowed" | Add-Content $ReportTxt
} elseif ($rawFiles.Count -gt 0) {
  $status="BLOCKED_RAW_DOWNLOADS_ARE_NOT_MACHINE_READABLE_TABLES"
  $completion=15
  $next="download_official_machine_readable_internet_access_tables"
  "reason=raw downloads exist but are HTML/page-like or not accepted table formats; no fake data is allowed" | Add-Content $ReportTxt
} else {
  $status="BLOCKED_MISSING_REAL_SOURCE_DATA"
  $completion=5
  $next="provide_or_download_official_machine_readable_internet_access_tables"
  "reason=source discovery completed, but no raw source files are present and no fake data is allowed" | Add-Content $ReportTxt
}

"status=$status" | Add-Content $ReportTxt
"completion_percent=$completion" | Add-Content $ReportTxt
"source_manifest_exists=$sourceManifestExists" | Add-Content $ReportTxt
"hash_manifest_exists=$hashManifestExists" | Add-Content $ReportTxt
"download_manifest_exists=$(Test-Path $DownloadManifest)" | Add-Content $ReportTxt
"raw_file_count=$($rawFiles.Count)" | Add-Content $ReportTxt
"machine_readable_file_count=$($machineReadable.Count)" | Add-Content $ReportTxt
"html_like_file_count=$($htmlLike.Count)" | Add-Content $ReportTxt
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
  download_manifest_exists=(Test-Path $DownloadManifest)
  raw_file_count=$rawFiles.Count
  machine_readable_file_count=$machineReadable.Count
  html_like_file_count=$htmlLike.Count
  machine_readable_files=$machineReadable
  html_like_files=$htmlLike
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
} | ConvertTo-Json -Depth 10 | Set-Content $ReportJson -Encoding UTF8

Copy-Item $ReportJson "$Out\latest_output.json" -Force

git add docs/chatgpt_status/reports/$Task.txt docs/chatgpt_status/reports/$Task.json docs/chatgpt_status/runner_outputs/latest_output.json docs/chatgpt_status/runner_inputs/$Task.ps1
$changed=(git status --porcelain)
if ($changed) {
  git commit -m "Run internet access 092 processed package check"
  git pull --rebase origin $Branch
  git push origin $Branch
}

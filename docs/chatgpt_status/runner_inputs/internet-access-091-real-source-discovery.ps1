$ErrorActionPreference = 'Continue'
$Repo = 'C:\Users\cagda\Documents\GitHub\AAYS'
$Branch = 'feature/terrayield-aays-integration'
$WorkRoot = 'F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610'
$StatusRoot = Join-Path $Repo 'docs\chatgpt_status'
$Reports = Join-Path $StatusRoot 'reports'
$Task = 'internet-access-091-real-source-discovery'
New-Item -ItemType Directory -Force $WorkRoot, (Join-Path $WorkRoot 'raw'), (Join-Path $WorkRoot 'raw\source_pages'), (Join-Path $WorkRoot 'processed'), (Join-Path $WorkRoot 'manifests'), (Join-Path $WorkRoot 'reports'), $Reports | Out-Null
$ReportTxt = Join-Path $Reports "$Task.txt"
$ReportJson = Join-Path $Reports "$Task.json"
$SourceManifest = Join-Path $WorkRoot 'manifests\source_manifest.json'
$HashManifest = Join-Path $WorkRoot 'manifests\hash_manifest.csv'
Set-Content -Path $ReportTxt -Encoding UTF8 -Value @"
task_id=$Task
status=STARTED_REAL_SOURCE_DISCOVERY
branch=$Branch
work_root=$WorkRoot
DB_WRITE=false
MIGRATION=false
PRODUCTION_DEPLOY=false
FAKE_DATA=false
"@
$Sources = @(
  @{name='ofcom_connected_nations'; url='https://www.ofcom.org.uk/research-and-data/multi-sector-research/infrastructure-research/connected-nations'},
  @{name='ofcom_coverage_checker'; url='https://checker.ofcom.org.uk/'},
  @{name='ons_open_geography'; url='https://geoportal.statistics.gov.uk/'},
  @{name='os_open_uprn'; url='https://osdatahub.os.uk/downloads/open/OpenUPRN'},
  @{name='bduk_project_gigabit'; url='https://www.gov.uk/government/collections/project-gigabit'}
)
$items = @()
foreach ($s in $Sources) {
  $out = Join-Path $WorkRoot ("raw\source_pages\" + $s.name + ".html")
  try {
    Invoke-WebRequest -Uri $s.url -OutFile $out -UseBasicParsing -TimeoutSec 120
    $h = (Get-FileHash $out -Algorithm SHA256).Hash
    $items += [pscustomobject]@{name=$s.name; url=$s.url; local_path=$out; sha256=$h; fetched=$true}
    Add-Content -Path $ReportTxt -Value "source_page_ok=$($s.name) sha256=$h url=$($s.url)"
  } catch {
    $items += [pscustomobject]@{name=$s.name; url=$s.url; local_path=''; sha256=''; fetched=$false; error=$_.Exception.Message}
    Add-Content -Path $ReportTxt -Value "source_page_failed=$($s.name) error=$($_.Exception.Message)"
  }
}
$items | ConvertTo-Json -Depth 6 | Set-Content -Path $SourceManifest -Encoding UTF8
'file,path,sha256,bytes' | Set-Content -Path $HashManifest -Encoding UTF8
Get-ChildItem $WorkRoot -Recurse -File | ForEach-Object { $h=(Get-FileHash $_.FullName -Algorithm SHA256).Hash; Add-Content -Path $HashManifest -Value "$($_.Name),$($_.FullName),$h,$($_.Length)" }
$required = @{
  scores_csv = Join-Path $WorkRoot 'processed\parcel_internet_access_scores.csv'
  breakdown_csv = Join-Path $WorkRoot 'processed\parcel_internet_access_factor_breakdown.csv'
  scores_geojson = Join-Path $WorkRoot 'processed\parcel_internet_access_scores.geojson'
  source_manifest = $SourceManifest
  calculation_manifest = Join-Path $WorkRoot 'manifests\calculation_manifest.json'
  excel_report = Join-Path $WorkRoot 'reports\internet_access_parcel_report.xlsx'
}
$outExists = @{}
foreach ($k in $required.Keys) { $outExists[$k] = Test-Path $required[$k] }
$status = 'SOURCE_DISCOVERY_READY_BUILD_NOT_DONE'
$completion = 5
if ($outExists.scores_csv -and $outExists.breakdown_csv -and $outExists.scores_geojson -and $outExists.source_manifest -and $outExists.calculation_manifest -and $outExists.excel_report) { $status='CONCRETE_INTERNET_PACKAGE_READY_FOR_VALIDATION'; $completion=60 }
@{task_id=$Task; status=$status; completion_percent=$completion; branch=$Branch; work_root=$WorkRoot; db_write=$false; migration=$false; production_deploy=$false; fake_data=$false; source_manifest=$SourceManifest; hash_manifest=$HashManifest; required_outputs=$required; output_exists=$outExists; next_action='build_processed_internet_score_package_from_official_sources'; manual_stdout_required=$false; generated_at=(Get-Date -Format s)} | ConvertTo-Json -Depth 8 | Set-Content -Path $ReportJson -Encoding UTF8
Add-Content -Path $ReportTxt -Value "status=$status"
Add-Content -Path $ReportTxt -Value "completion_percent=$completion"
Add-Content -Path $ReportTxt -Value "source_manifest=$SourceManifest"
Add-Content -Path $ReportTxt -Value "manual_stdout_required=false"
cd $Repo
git add docs/chatgpt_status/reports/$Task.txt docs/chatgpt_status/reports/$Task.json
git commit -m 'Run internet access 091 source discovery from runner' | Out-Null
git push origin $Branch | Out-Null

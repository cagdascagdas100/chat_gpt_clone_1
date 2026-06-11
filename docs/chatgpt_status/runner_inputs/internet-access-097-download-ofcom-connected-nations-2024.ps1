$ErrorActionPreference='Stop'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Branch='feature/terrayield-aays-integration'
$WorkRoot='F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610'
$StatusRoot=Join-Path $Repo 'docs\chatgpt_status'
$Reports=Join-Path $StatusRoot 'reports'
$RunnerOutputs=Join-Path $StatusRoot 'runner_outputs'
$RawDownloads=Join-Path $WorkRoot 'raw\downloads\ofcom_connected_nations_2024'
$ManifestDir=Join-Path $WorkRoot 'manifests'
$Task='internet-access-097-download-ofcom-connected-nations-2024'
New-Item -ItemType Directory -Force $Reports,$RunnerOutputs,$RawDownloads,$ManifestDir | Out-Null
$Txt=Join-Path $Reports "$Task.txt"
$Json=Join-Path $Reports "$Task.json"
$DownloadManifest=Join-Path $ManifestDir 'ofcom_connected_nations_2024_download_manifest.csv'
$Sources=@(
  @{name='fixed_coverage_postcodes'; url='https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2024/data-downloads/202407-fixed-coverage-postcodes-r01.zip?v=386548'; file='202407-fixed-coverage-postcodes-r01.zip'},
  @{name='fixed_coverage_output_areas'; url='https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2024/data-downloads/202407-fixed-coverage-output-areas.zip?v=386547'; file='202407-fixed-coverage-output-areas.zip'},
  @{name='fixed_coverage_uk_nations_laua_pcon'; url='https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2024/data-downloads/202407-fixed-coverage-uk-nations-laua-pcon-r01.zip?v=386549'; file='202407-fixed-coverage-uk-nations-laua-pcon-r01.zip'}
)
$Rows=@()
$Errors=@()
foreach($s in $Sources){
  $dest=Join-Path $RawDownloads $s.file
  try{
    Invoke-WebRequest -Uri $s.url -OutFile $dest -UseBasicParsing -MaximumRedirection 5
    $bytes=(Get-Item $dest).Length
    $hash=(Get-FileHash $dest -Algorithm SHA256).Hash
    $Rows += [pscustomobject]@{source=$s.name; url=$s.url; path=$dest; bytes=$bytes; sha256=$hash; status='downloaded'}
  } catch {
    $Errors += [pscustomobject]@{source=$s.name; url=$s.url; error=$_.Exception.Message}
  }
}
$Rows | Export-Csv $DownloadManifest -NoTypeInformation -Encoding UTF8
$downloaded=($Rows | Measure-Object).Count
$status=if($downloaded -gt 0){'OFFICIAL_MACHINE_READABLE_SOURCE_DOWNLOADED'}else{'BLOCKED_OFFICIAL_OFcom_DOWNLOAD_FAILED'}
$completion=if($downloaded -gt 0){20}else{15}
@{
  task_id=$Task
  status=$status
  completion_percent=$completion
  work_root=$WorkRoot
  downloaded_count=$downloaded
  downloaded_files=@($Rows)
  errors=@($Errors)
  download_manifest=$DownloadManifest
  db_write=$false
  migration=$false
  production_deploy=$false
  fake_data=$false
  manual_stdout_required=$false
  next_action=if($downloaded -gt 0){'run_092_processed_package_builder'}else{'fix_official_source_download'}
  generated_at=(Get-Date -Format s)
} | ConvertTo-Json -Depth 8 | Set-Content $Json -Encoding UTF8
"task_id=$Task" | Set-Content $Txt -Encoding UTF8
"status=$status" | Add-Content $Txt
"completion_percent=$completion" | Add-Content $Txt
"downloaded_count=$downloaded" | Add-Content $Txt
"download_manifest=$DownloadManifest" | Add-Content $Txt
"manual_stdout_required=false" | Add-Content $Txt
Copy-Item $Json (Join-Path $RunnerOutputs 'latest_output.json') -Force
cd $Repo
git add "docs/chatgpt_status/reports/$Task.txt" "docs/chatgpt_status/reports/$Task.json" "docs/chatgpt_status/runner_outputs/latest_output.json"
git commit -m "Run internet access 097 Ofcom Connected Nations download" | Out-Null
git pull --rebase origin $Branch | Out-Null
git push origin $Branch | Out-Null

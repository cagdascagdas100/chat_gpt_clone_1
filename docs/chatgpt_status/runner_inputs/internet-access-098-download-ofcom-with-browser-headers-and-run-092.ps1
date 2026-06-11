$ErrorActionPreference='Stop'
$Repo='C:\Users\cagda\Documents\GitHub\AAYS'
$Branch='feature/terrayield-aays-integration'
$WorkRoot='F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610'
$StatusRoot=Join-Path $Repo 'docs\chatgpt_status'
$Reports=Join-Path $StatusRoot 'reports'
$RunnerOutputs=Join-Path $StatusRoot 'runner_outputs'
$RawDownloads=Join-Path $WorkRoot 'raw\downloads\ofcom_connected_nations_2024'
$ExtractRoot=Join-Path $WorkRoot 'raw\extracted\ofcom_connected_nations_2024'
$ManifestDir=Join-Path $WorkRoot 'manifests'
$Task='internet-access-098-download-ofcom-with-browser-headers-and-run-092'
New-Item -ItemType Directory -Force $Reports,$RunnerOutputs,$RawDownloads,$ExtractRoot,$ManifestDir | Out-Null
$Txt=Join-Path $Reports "$Task.txt"
$Json=Join-Path $Reports "$Task.json"
$DownloadManifest=Join-Path $ManifestDir 'ofcom_connected_nations_2024_download_manifest_098.csv'
$Page='https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-2024/data-downloads-2024'
$Sources=@(
  @{name='fixed_coverage_postcodes'; url='https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2024/data-downloads/202407-fixed-coverage-postcodes-r01.zip?v=386548'; file='202407-fixed-coverage-postcodes-r01.zip'},
  @{name='fixed_coverage_output_areas'; url='https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2024/data-downloads/202407-fixed-coverage-output-areas.zip?v=386547'; file='202407-fixed-coverage-output-areas.zip'},
  @{name='fixed_coverage_uk_nations_laua_pcon'; url='https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2024/data-downloads/202407-fixed-coverage-uk-nations-laua-pcon-r01.zip?v=386549'; file='202407-fixed-coverage-uk-nations-laua-pcon-r01.zip'}
)
$Rows=@(); $Errors=@()
$Headers=@{
  'User-Agent'='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36'
  'Accept'='application/zip,application/octet-stream,*/*'
  'Referer'=$Page
}
foreach($s in $Sources){
  $dest=Join-Path $RawDownloads $s.file
  $ok=$false; $err=''
  try{
    if(Test-Path $dest){Remove-Item $dest -Force}
    if(Get-Command curl.exe -ErrorAction SilentlyContinue){
      & curl.exe -L --fail --retry 3 --retry-delay 3 -A $Headers['User-Agent'] -H "Referer: $Page" -H "Accept: application/zip,application/octet-stream,*/*" -o $dest $s.url
      if($LASTEXITCODE -ne 0){throw "curl.exe exit code $LASTEXITCODE"}
    } else {
      Invoke-WebRequest -Uri $s.url -OutFile $dest -Headers $Headers -MaximumRedirection 10 -UseBasicParsing
    }
    if((Test-Path $dest) -and ((Get-Item $dest).Length -gt 1024)){$ok=$true}
  } catch {
    $err=$_.Exception.Message
    try{
      if(Test-Path $dest){Remove-Item $dest -Force}
      Invoke-WebRequest -Uri $s.url -OutFile $dest -Headers $Headers -MaximumRedirection 10 -UseBasicParsing
      if((Test-Path $dest) -and ((Get-Item $dest).Length -gt 1024)){$ok=$true}
    } catch { $err=$err + ' | fallback=' + $_.Exception.Message }
  }
  if($ok){
    $bytes=(Get-Item $dest).Length
    $hash=(Get-FileHash $dest -Algorithm SHA256).Hash
    $extractDir=Join-Path $ExtractRoot $s.name
    New-Item -ItemType Directory -Force $extractDir | Out-Null
    try{Expand-Archive -Path $dest -DestinationPath $extractDir -Force; $extracted=$true}catch{$extracted=$false; $Errors += [pscustomobject]@{source=$s.name; url=$s.url; error=('extract_failed='+$_.Exception.Message)}}
    $Rows += [pscustomobject]@{source=$s.name; url=$s.url; path=$dest; bytes=$bytes; sha256=$hash; extracted=$extracted; status='downloaded'}
  } else {
    $Errors += [pscustomobject]@{source=$s.name; url=$s.url; error=$err}
  }
}
$Rows | Export-Csv $DownloadManifest -NoTypeInformation -Encoding UTF8
$downloaded=($Rows | Measure-Object).Count
$status=if($downloaded -gt 0){'OFFICIAL_MACHINE_READABLE_SOURCE_DOWNLOADED'}else{'BLOCKED_OFFICIAL_OFcom_DOWNLOAD_FAILED_WITH_BROWSER_HEADERS'}
$completion=if($downloaded -gt 0){20}else{15}
$result=[ordered]@{
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
  next_action=if($downloaded -gt 0){'run_092_processed_package_builder'}else{'fix_official_source_download_or_manual_browser_download'}
  generated_at=(Get-Date -Format s)
}
$result | ConvertTo-Json -Depth 10 | Set-Content $Json -Encoding UTF8
"task_id=$Task" | Set-Content $Txt -Encoding UTF8
"status=$status" | Add-Content $Txt
"completion_percent=$completion" | Add-Content $Txt
"downloaded_count=$downloaded" | Add-Content $Txt
"download_manifest=$DownloadManifest" | Add-Content $Txt
"manual_stdout_required=false" | Add-Content $Txt
Copy-Item $Json (Join-Path $RunnerOutputs 'latest_output.json') -Force
if($downloaded -gt 0){
  $Builder=Join-Path $StatusRoot 'runner_inputs\internet-access-092-build-processed-package.ps1'
  if(Test-Path $Builder){ & powershell -ExecutionPolicy Bypass -File $Builder }
}
cd $Repo
git add "docs/chatgpt_status/reports/$Task.txt" "docs/chatgpt_status/reports/$Task.json" "docs/chatgpt_status/runner_outputs/latest_output.json"
git commit -m "Run internet access 098 Ofcom browser header download" | Out-Null
git pull --rebase origin $Branch | Out-Null
git push origin $Branch | Out-Null

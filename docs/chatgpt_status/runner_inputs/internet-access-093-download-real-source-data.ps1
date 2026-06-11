$Repo="C:\Users\cagda\Documents\GitHub\AAYS"
$Branch="feature/terrayield-aays-integration"
$WorkRoot="F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610"
$Task="internet-access-093-download-real-source-data"
$StatusRoot="$Repo\docs\chatgpt_status"
$Reports="$StatusRoot\reports"
$RawRoot="$WorkRoot\raw"
$PagesRoot="$RawRoot\pages"
$DownloadsRoot="$RawRoot\downloads"
$ManifestRoot="$WorkRoot\manifests"
$SourceManifest="$ManifestRoot\source_manifest.json"
$ReportTxt="$Reports\$Task.txt"
$ReportJson="$Reports\$Task.json"
$DownloadManifest="$ManifestRoot\download_manifest.json"
$HashManifest="$ManifestRoot\download_hash_manifest.csv"

New-Item -ItemType Directory -Force $Reports,$RawRoot,$PagesRoot,$DownloadsRoot,$ManifestRoot | Out-Null
cd $Repo

git fetch origin 2>&1 | Set-Content $ReportTxt -Encoding UTF8
git switch $Branch 2>&1 | Add-Content $ReportTxt
git pull --ff-only origin $Branch 2>&1 | Add-Content $ReportTxt

Add-Content $ReportTxt "task_id=$Task"
Add-Content $ReportTxt "status=STARTED_REAL_SOURCE_DATA_DOWNLOAD"
Add-Content $ReportTxt "work_root=$WorkRoot"
Add-Content $ReportTxt "DB_WRITE=false"
Add-Content $ReportTxt "MIGRATION=false"
Add-Content $ReportTxt "PRODUCTION_DEPLOY=false"
Add-Content $ReportTxt "FAKE_DATA=false"
Add-Content $ReportTxt "manual_stdout_required=false"

$sources=@{}
if (Test-Path $SourceManifest) {
  try {
    $sourceJson=Get-Content $SourceManifest -Raw | ConvertFrom-Json
    foreach ($p in $sourceJson.PSObject.Properties) {
      if ($p.Value.url) { $sources[$p.Name] = [string]$p.Value.url }
      elseif ($p.Value -is [string]) { $sources[$p.Name] = [string]$p.Value }
    }
  } catch {
    Add-Content $ReportTxt "source_manifest_parse_error=$($_.Exception.Message)"
  }
}
if ($sources.Count -eq 0) {
  $sources=@{
    ofcom_connected_nations="https://www.ofcom.org.uk/research-and-data/multi-sector-research/infrastructure-research/connected-nations"
    ofcom_coverage_checker="https://checker.ofcom.org.uk/"
    ons_open_geography="https://geoportal.statistics.gov.uk/"
    os_open_uprn="https://osdatahub.os.uk/downloads/open/OpenUPRN"
    bduk_project_gigabit="https://www.gov.uk/government/collections/project-gigabit"
  }
}

$allLinks = New-Object System.Collections.Generic.List[object]
$downloaded = New-Object System.Collections.Generic.List[object]
$errors = New-Object System.Collections.Generic.List[object]

foreach ($key in $sources.Keys) {
  $url=$sources[$key]
  $safeKey=($key -replace '[^a-zA-Z0-9_-]','_')
  $pagePath=Join-Path $PagesRoot "$safeKey.html"
  try {
    $resp=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 60
    $resp.Content | Set-Content $pagePath -Encoding UTF8
    $hrefs=@()
    if ($resp.Links) { $hrefs += ($resp.Links | ForEach-Object { $_.href }) }
    $hrefs += ([regex]::Matches($resp.Content,'href=["'']([^"'']+)["'']') | ForEach-Object { $_.Groups[1].Value })
    $hrefs = $hrefs | Where-Object { $_ } | Select-Object -Unique
    foreach ($h in $hrefs) {
      try {
        $abs=[Uri]::new([Uri]$url,$h).AbsoluteUri
        if ($abs -match '(?i)\.(csv|xlsx|xls|zip|json|geojson|parquet)(\?|$)' -or $abs -match '(?i)(broadband|coverage|connected|nation|gigabit|postcode|uprn|premise|availability)') {
          $allLinks.Add([pscustomobject]@{source=$key; url=$abs}) | Out-Null
        }
      } catch {}
    }
  } catch {
    $errors.Add([pscustomobject]@{source=$key; url=$url; error=$_.Exception.Message}) | Out-Null
  }
}

$candidates=$allLinks | Sort-Object url -Unique | Select-Object -First 40
foreach ($c in $candidates) {
  try {
    $u=[Uri]$c.url
    $name=[IO.Path]::GetFileName($u.AbsolutePath)
    if ([string]::IsNullOrWhiteSpace($name)) { $name=("candidate_" + $downloaded.Count + ".bin") }
    $name=($name -replace '[^a-zA-Z0-9._-]','_')
    $dest=Join-Path $DownloadsRoot $name
    Invoke-WebRequest -Uri $c.url -OutFile $dest -UseBasicParsing -TimeoutSec 120
    if ((Test-Path $dest) -and ((Get-Item $dest).Length -gt 0)) {
      $sha=(Get-FileHash $dest -Algorithm SHA256).Hash
      $downloaded.Add([pscustomobject]@{source=$c.source; url=$c.url; path=$dest; bytes=(Get-Item $dest).Length; sha256=$sha}) | Out-Null
    }
  } catch {
    $errors.Add([pscustomobject]@{source=$c.source; url=$c.url; error=$_.Exception.Message}) | Out-Null
  }
}

$downloaded | ConvertTo-Json -Depth 6 | Set-Content $DownloadManifest -Encoding UTF8
"source,url,path,bytes,sha256" | Set-Content $HashManifest -Encoding UTF8
foreach ($d in $downloaded) { '"{0}","{1}","{2}",{3},{4}' -f $d.source,$d.url,$d.path,$d.bytes,$d.sha256 | Add-Content $HashManifest }

$downloadCount=$downloaded.Count
$linkCount=($allLinks | Measure-Object).Count
$errorCount=$errors.Count
if ($downloadCount -gt 0) {
  $status="REAL_SOURCE_DOWNLOAD_CANDIDATES_READY"
  $completion=15
  $next="run_processed_package_builder_with_downloaded_sources"
} else {
  $status="BLOCKED_NO_MACHINE_READABLE_SOURCE_DOWNLOADS"
  $completion=5
  $next="provide_specific_official_download_url_or_source_file"
}

Add-Content $ReportTxt "status=$status"
Add-Content $ReportTxt "completion_percent=$completion"
Add-Content $ReportTxt "candidate_link_count=$linkCount"
Add-Content $ReportTxt "downloaded_file_count=$downloadCount"
Add-Content $ReportTxt "error_count=$errorCount"
Add-Content $ReportTxt "download_manifest=$DownloadManifest"
Add-Content $ReportTxt "hash_manifest=$HashManifest"
Add-Content $ReportTxt "next_action=$next"

@{
  task_id=$Task
  status=$status
  completion_percent=$completion
  work_root=$WorkRoot
  source_manifest_exists=(Test-Path $SourceManifest)
  candidate_link_count=$linkCount
  downloaded_file_count=$downloadCount
  downloaded_files=$downloaded
  errors=$errors
  download_manifest=$DownloadManifest
  hash_manifest=$HashManifest
  db_write=$false
  migration=$false
  production_deploy=$false
  fake_data=$false
  manual_stdout_required=$false
  next_action=$next
  generated_at=(Get-Date -Format s)
} | ConvertTo-Json -Depth 10 | Set-Content $ReportJson -Encoding UTF8

git add docs/chatgpt_status/reports/$Task.txt docs/chatgpt_status/reports/$Task.json 2>&1 | Add-Content $ReportTxt
git commit -m "Run internet access real source data download" 2>&1 | Add-Content $ReportTxt
git pull --rebase origin $Branch 2>&1 | Add-Content $ReportTxt
git push origin $Branch 2>&1 | Add-Content $ReportTxt

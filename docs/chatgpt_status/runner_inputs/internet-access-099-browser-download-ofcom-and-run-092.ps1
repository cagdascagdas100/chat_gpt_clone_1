$ErrorActionPreference = 'Stop'
$Repo = 'C:\Users\cagda\Documents\GitHub\AAYS'
$Branch = 'feature/terrayield-aays-integration'
$WorkRoot = 'F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610'
$TaskId = 'internet-access-099-browser-download-ofcom-and-run-092'
$ReportDir = Join-Path $Repo 'docs\chatgpt_status\reports'
$LatestDir = Join-Path $Repo 'docs\chatgpt_status\runner_outputs'
$RawDir = Join-Path $WorkRoot 'raw\downloads\ofcom_connected_nations_2024_browser'
$ExtractDir = Join-Path $WorkRoot 'raw\extracted\ofcom_connected_nations_2024'
$ManifestDir = Join-Path $WorkRoot 'manifests'
New-Item -ItemType Directory -Force -Path $ReportDir,$LatestDir,$RawDir,$ExtractDir,$ManifestDir | Out-Null
$Sources = @(
  @{name='fixed_coverage_postcodes'; url='https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2024/data-downloads/202407-fixed-coverage-postcodes-r01.zip?v=386548'; file='202407-fixed-coverage-postcodes-r01.zip'},
  @{name='fixed_coverage_output_areas'; url='https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2024/data-downloads/202407-fixed-coverage-output-areas.zip?v=386547'; file='202407-fixed-coverage-output-areas.zip'},
  @{name='fixed_coverage_uk_nations_laua_pcon'; url='https://www.ofcom.org.uk/siteassets/resources/documents/research-and-data/multi-sector/infrastructure-research/connected-nations-2024/data-downloads/202407-fixed-coverage-uk-nations-laua-pcon-r01.zip?v=386549'; file='202407-fixed-coverage-uk-nations-laua-pcon-r01.zip'}
)
Set-Location $Repo
git fetch origin | Out-Null
git switch $Branch | Out-Null
git pull --ff-only origin $Branch | Out-Null
$browser = @(
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles(x86)\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
  "$env:ProgramFiles(x86)\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
$errors = @()
if (-not $browser) {
  $errors += @{stage='browser_lookup'; error='No Edge/Chrome executable found'}
} else {
  $Profile = Join-Path $WorkRoot 'browser_profile_ofcom_download'
  $Default = Join-Path $Profile 'Default'
  New-Item -ItemType Directory -Force -Path $Default | Out-Null
  $prefs = @{
    download = @{ default_directory = $RawDir; prompt_for_download = $false; directory_upgrade = $true }
    safebrowsing = @{ enabled = $true }
    profile = @{ default_content_settings = @{ popups = 0 }; default_content_setting_values = @{ automatic_downloads = 1 } }
  } | ConvertTo-Json -Depth 10
  Set-Content -Path (Join-Path $Default 'Preferences') -Value $prefs -Encoding UTF8
  foreach ($s in $Sources) {
    try {
      Start-Process -FilePath $browser -ArgumentList @("--user-data-dir=$Profile",'--no-first-run','--disable-popup-blocking','--safebrowsing-disable-download-protection',$s.url) | Out-Null
      Start-Sleep -Seconds 8
    } catch {
      $errors += @{stage='browser_start'; source=$s.name; error=$_.Exception.Message}
    }
  }
  $deadline = (Get-Date).AddMinutes(7)
  do {
    Start-Sleep -Seconds 5
    $partial = Get-ChildItem -Path $RawDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '\.crdownload$|\.tmp$|\.download$' }
    $zips = Get-ChildItem -Path $RawDir -File -Filter '*.zip' -ErrorAction SilentlyContinue
  } while ((Get-Date) -lt $deadline -and (($zips.Count -lt 1) -or ($partial.Count -gt 0)))
  Get-Process msedge,chrome -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $browser } | Stop-Process -Force -ErrorAction SilentlyContinue
}
$downloaded = @()
$zips = Get-ChildItem -Path $RawDir -File -Filter '*.zip' -ErrorAction SilentlyContinue
foreach ($zip in $zips) {
  try {
    $h = Get-FileHash -Algorithm SHA256 -Path $zip.FullName
    $dest = Join-Path $ExtractDir ([IO.Path]::GetFileNameWithoutExtension($zip.Name))
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Expand-Archive -Force -Path $zip.FullName -DestinationPath $dest
    $downloaded += @{file=$zip.FullName; bytes=$zip.Length; sha256=$h.Hash; extract_dir=$dest}
  } catch {
    $errors += @{stage='hash_or_extract'; file=$zip.FullName; error=$_.Exception.Message}
  }
}
$manifest = Join-Path $ManifestDir 'ofcom_connected_nations_2024_browser_download_manifest_099.csv'
$downloaded | ForEach-Object { [pscustomobject]$_ } | Export-Csv -NoTypeInformation -Path $manifest -Encoding UTF8
$status = if ($downloaded.Count -gt 0) { 'OFFICIAL_OFcom_BROWSER_DOWNLOAD_READY' } else { 'BLOCKED_OFFICIAL_OFcom_BROWSER_DOWNLOAD_FAILED' }
$completion = if ($downloaded.Count -gt 0) { 20 } else { 15 }
$next = if ($downloaded.Count -gt 0) { 'run_or_review_092_processed_package_builder_output' } else { 'manual_browser_download_or_alternate_official_mirror_required' }
$result = [ordered]@{
  task_id=$TaskId
  status=$status
  completion_percent=$completion
  work_root=$WorkRoot
  downloaded_count=$downloaded.Count
  downloaded_files=$downloaded
  errors=$errors
  download_manifest=$manifest
  db_write=$false
  migration=$false
  production_deploy=$false
  fake_data=$false
  manual_stdout_required=$false
  next_action=$next
  generated_at=(Get-Date).ToString('s')
}
$jsonPath = Join-Path $ReportDir "$TaskId.json"
$txtPath = Join-Path $ReportDir "$TaskId.txt"
$result | ConvertTo-Json -Depth 10 | Set-Content -Path $jsonPath -Encoding UTF8
@"
task_id=$TaskId
status=$status
completion_percent=$completion
downloaded_count=$($downloaded.Count)
work_root=$WorkRoot
download_manifest=$manifest
next_action=$next
manual_stdout_required=false
fake_data=false
db_write=false
migration=false
production_deploy=false
"@ | Set-Content -Path $txtPath -Encoding UTF8
Copy-Item -Force $jsonPath (Join-Path $LatestDir 'latest_output.json')
if ($downloaded.Count -gt 0) {
  $Builder = Join-Path $Repo 'docs\chatgpt_status\runner_inputs\internet-access-092-build-processed-package.ps1'
  if (Test-Path $Builder) {
    try { powershell -ExecutionPolicy Bypass -File $Builder } catch { $errors += @{stage='run_092'; error=$_.Exception.Message} }
  }
}
git add docs/chatgpt_status/reports docs/chatgpt_status/runner_outputs/latest_output.json | Out-Null
git commit -m "internet access 099 browser download fallback result" | Out-Null
git push origin $Branch | Out-Null

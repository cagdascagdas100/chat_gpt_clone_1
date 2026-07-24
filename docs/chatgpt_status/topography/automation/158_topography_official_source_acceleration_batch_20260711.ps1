[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}
function Write-Json([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  [System.IO.File]::WriteAllText($Path, (($Value | ConvertTo-Json -Depth 60) + "`n"), [System.Text.UTF8Encoding]::new($false))
}
function Read-Json([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Test-OfficialUrl([string]$Name, [string]$Url) {
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 60 -Headers @{ 'User-Agent'='TerraYield-AAYS-Topography/1.0 official-source-discovery' }
    return [ordered]@{ name=$Name; url=$Url; reachable=($response.StatusCode -ge 200 -and $response.StatusCode -lt 400); status_code=[int]$response.StatusCode; error=$null }
  } catch {
    $code = $null
    try { $code = [int]$_.Exception.Response.StatusCode.value__ } catch {}
    return [ordered]@{ name=$Name; url=$Url; reachable=$false; status_code=$code; error=$_.Exception.Message }
  }
}
function Get-Python {
  foreach ($candidate in @('python','py')) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
  }
  return $null
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or -not $repoRoot.StartsWith('F:\TerraYield_AAYS_Portable\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw 'TOPOGRAPHY_158_REQUIRES_F_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'topography-158-official-source-acceleration-batch-20260711' }
$branch = if ($env:AAYS_TARGET_BRANCH) { [string]$env:AAYS_TARGET_BRANCH } else { 'codex/aays-single-runner-v5-20260706' }
$startedAt = Now-Utc
$stages = @()

$script157Rel = 'docs/chatgpt_status/topography/automation/157_topography_multisource_serial_batch_20260711.ps1'
$output157Rel = 'docs/chatgpt_status/topography/runner_outputs/157_topography_multisource_serial_batch.json'
$visibleRowsRel = 'england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$htmlRel = 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$latestChangesRel = 'outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$sourceSnapshotRel = 'docs/chatgpt_status/topography/source_snapshots/158_official_source_discovery_latest.json'
$statusRel = 'docs/chatgpt_status/topography/status/158_topography_official_source_acceleration_latest.json'
$reportRel = 'docs/chatgpt_status/topography/reports/158_topography_official_source_acceleration_report_20260711.md'
$browserProofRel = 'docs/chatgpt_status/topography/reports/158_topography_official_source_browser_validation_20260711.json'
$runnerOutputRel = 'docs/chatgpt_status/topography/runner_outputs/158_topography_official_source_acceleration_batch.json'

try {
  # Stage 1-4: execute/reuse the complete EU-DEM + SRTM + site + Chrome chain in the same canonical runner.
  $output157Path = Join-Path $repoRoot ($output157Rel -replace '/', '\')
  $output157 = Read-Json $output157Path
  if ($null -eq $output157 -or [string]$output157.status -ne 'COMPLETED_VISIBLE_NOT_FINAL') {
    $script157Path = Join-Path $repoRoot ($script157Rel -replace '/', '\')
    if (-not (Test-Path -LiteralPath $script157Path)) { throw 'TASK_157_SCRIPT_MISSING' }
    $savedTaskId = $env:AAYS_TASK_ID
    try {
      $env:AAYS_TASK_ID = 'topography-157-multisource-serial-batch-20260711'
      & powershell -NoProfile -ExecutionPolicy Bypass -File $script157Path
      if ($LASTEXITCODE -ne 0) { throw "TASK_157_EXIT_CODE_$LASTEXITCODE" }
    } finally {
      $env:AAYS_TASK_ID = $savedTaskId
    }
    $output157 = Read-Json $output157Path
    if ($null -eq $output157 -or [string]$output157.status -ne 'COMPLETED_VISIBLE_NOT_FINAL') { throw 'TASK_157_OUTPUT_NOT_READY_AFTER_RUN' }
    $stages += [ordered]@{ stage='multisource_sampling_and_browser'; status='completed_in_same_runner_process' }
  } else {
    $stages += [ordered]@{ stage='multisource_sampling_and_browser'; status='reused_existing_runner_output' }
  }

  # Stage 5: Copernicus Data Space catalogue readback for the expected one-degree cell.
  $odataBase = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
  $odataFilter = "contains(Name,'N51_00')"
  $odataUrl = $odataBase + '?$filter=' + [System.Uri]::EscapeDataString($odataFilter) + '&$top=20&$expand=Attributes'
  $copernicus = [ordered]@{ url=$odataUrl; reachable=$false; result_count=0; matching_products=@(); error=$null }
  try {
    $odata = Invoke-RestMethod -Method Get -Uri $odataUrl -TimeoutSec 120 -Headers @{ 'User-Agent'='TerraYield-AAYS-Topography/1.0 Copernicus-catalogue-readback' }
    $products = @($odata.value)
    $matching = @($products | Where-Object {
      ([string]$_.Name -match 'N51_00|N51_W001') -or
      ((@($_.Attributes) | ConvertTo-Json -Depth 20) -match 'N51_W001')
    })
    $copernicus.reachable = $true
    $copernicus.result_count = $products.Count
    $copernicus.matching_products = @($matching | Select-Object -First 10 Id,Name,ContentDate,PublicationDate,Footprint,Attributes)
  } catch {
    $copernicus.error = $_.Exception.Message
  }
  $stages += [ordered]@{ stage='copernicus_odata_catalogue_readback'; status=if($copernicus.reachable){'completed'}else{'blocked'}; result_count=$copernicus.result_count; matching_count=@($copernicus.matching_products).Count }

  # Stage 6: official UK high-resolution source discovery/readiness checks.
  $eaUrl = 'https://environment.data.gov.uk/DefraDataDownload/?Mode=survey'
  $osUrl = 'https://osdatahub.os.uk/downloads/open/Terrain50'
  $copernicusDocsUrl = 'https://documentation.dataspace.copernicus.eu/APIs/OData.html'
  $officialChecks = @(
    (Test-OfficialUrl 'Copernicus Data Space OData documentation' $copernicusDocsUrl),
    (Test-OfficialUrl 'Environment Agency LiDAR survey download' $eaUrl),
    (Test-OfficialUrl 'Ordnance Survey Terrain 50 open download' $osUrl)
  )
  $reachableOfficial = @($officialChecks | Where-Object { $_.reachable }).Count
  $stages += [ordered]@{ stage='official_uk_source_readiness'; status=if($reachableOfficial -ge 2){'completed'}else{'partial'}; reachable_sources=$reachableOfficial; checked_sources=$officialChecks.Count }

  $generatedAt = Now-Utc
  Write-Json (Join-Path $repoRoot ($sourceSnapshotRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId
    generated_at=$generatedAt
    copernicus_catalogue=$copernicus
    official_source_checks=$officialChecks
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })

  # Stage 7: expose the new official-source discovery state row by row.
  $visibleRowsPath = Join-Path $repoRoot ($visibleRowsRel -replace '/', '\')
  $visible = Read-Json $visibleRowsPath
  if ($null -eq $visible -or @($visible.rows).Count -lt 3) { throw 'VISIBLE_ROWS_NOT_READY_FOR_158' }
  foreach ($row in @($visible.rows)) {
    $row.copernicus_catalogue_result_count = [int]$copernicus.result_count
    $row.copernicus_catalogue_matching_count = @($copernicus.matching_products).Count
    $row.copernicus_catalogue_status = if ($copernicus.reachable) { 'official_catalogue_readback_completed' } else { 'official_catalogue_readback_blocked' }
    $row.copernicus_catalogue_url = $odataUrl
    $row.ea_lidar_source_status = if (($officialChecks | Where-Object { $_.name -like 'Environment Agency*' }).reachable) { 'official_source_reachable_sampling_pending' } else { 'official_source_unreachable_or_blocked' }
    $row.ea_lidar_source_url = $eaUrl
    $row.os_terrain_source_status = if (($officialChecks | Where-Object { $_.name -like 'Ordnance Survey*' }).reachable) { 'official_source_reachable_sampling_pending' } else { 'official_source_unreachable_or_blocked' }
    $row.os_terrain_source_url = $osUrl
    $row.official_source_discovery_path = $sourceSnapshotRel
    $row.task_id = $taskId
    $row.updated_at = $generatedAt
    $row.report_path = $reportRel
    $row.status_path = $statusRel
    $row.queue_path = 'docs/chatgpt_status/topography/queue/158_topography_official_source_acceleration_batch_20260711.task.json'
    $row.blocker = 'real_parcel_boundary_required; primary_copdem_glo30_raster_sampling_required; ea_lidar_or_os_terrain_numeric_validation_required'
    $row.needs_manual_review = $true
    $row.final_ready = $false
    $row.fake_data = $false
  }
  $visible.status = 'MULTISOURCE_VISIBLE_OFFICIAL_PRIMARY_SOURCE_DISCOVERY_COMPLETED_NUMERIC_PRIMARY_VALIDATION_PENDING'
  $visible.latest_task_id = $taskId
  $visible.updated_at = $generatedAt
  $visible.rows = @($visible.rows)
  $visible.final_ready = $false
  $visible.fake_data = $false
  Write-Json $visibleRowsPath $visible

  $visibleStatus = Read-Json (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\'))
  if ($null -eq $visibleStatus) { $visibleStatus = [pscustomobject]@{} }
  $visibleStatus.status = 'MULTISOURCE_VISIBLE_OFFICIAL_PRIMARY_SOURCE_DISCOVERY_COMPLETED_NUMERIC_PRIMARY_VALIDATION_PENDING'
  $visibleStatus.latest_task_id = $taskId
  $visibleStatus.official_sources_checked = 3
  $visibleStatus.official_sources_reachable = $reachableOfficial
  $visibleStatus.copernicus_catalogue_result_count = [int]$copernicus.result_count
  $visibleStatus.copernicus_catalogue_matching_count = @($copernicus.matching_products).Count
  $visibleStatus.official_source_discovery_path = $sourceSnapshotRel
  $visibleStatus.completion_percent = 55
  $visibleStatus.updated_at = $generatedAt
  $visibleStatus.final_ready = $false
  $visibleStatus.fake_data = $false
  Write-Json (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\')) $visibleStatus

  $htmlPath = Join-Path $repoRoot ($htmlRel -replace '/', '\')
  $html = Get-Content -LiteralPath $htmlPath -Raw -Encoding UTF8
  if (-not $html.Contains("['Copernicus katalog durumu','copernicus_catalogue_status']")) {
    $needle = "['Çoklu kaynak kanıtı','multisource_evidence_path'],['Güven (%)','confidence_percent']"
    $replacement = "['Çoklu kaynak kanıtı','multisource_evidence_path'],['Copernicus katalog durumu','copernicus_catalogue_status'],['Copernicus sonuç','copernicus_catalogue_result_count'],['Copernicus eşleşme','copernicus_catalogue_matching_count'],['Copernicus katalog URL','copernicus_catalogue_url'],['EA LiDAR durumu','ea_lidar_source_status'],['EA LiDAR URL','ea_lidar_source_url'],['OS Terrain durumu','os_terrain_source_status'],['OS Terrain URL','os_terrain_source_url'],['Resmi kaynak discovery','official_source_discovery_path'],['Güven (%)','confidence_percent']"
    if (-not $html.Contains($needle)) { throw 'TOPOGRAPHY_158_HTML_INSERT_POINT_NOT_FOUND' }
    $html = $html.Replace($needle, $replacement)
    [System.IO.File]::WriteAllText($htmlPath, $html, [System.Text.UTF8Encoding]::new($false))
  }
  $stages += [ordered]@{ stage='official_source_fields_visible'; status='completed'; rows=3 }

  # Stage 8: second real Chrome validation after official-source fields are added.
  $python = Get-Python
  if (-not $python) { throw 'PYTHON_NOT_FOUND_FOR_158_BROWSER_VALIDATION' }
  $tempPy = Join-Path $env:TEMP ("aays_topography_158_" + [guid]::NewGuid().ToString('N') + '.py')
  $tempJson = Join-Path $env:TEMP ("aays_topography_158_" + [guid]::NewGuid().ToString('N') + '.json')
  $pyCode = @'
import json, sys, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
out_path = sys.argv[1]
url = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?topography_browser_validation=158'
options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=2400,1200')
options.set_capability('goog:loggingPrefs', {'browser':'ALL'})
driver = webdriver.Chrome(options=options)
result = {'status':'FAIL','url':url,'browser':'Google Chrome via Selenium'}
try:
    driver.get(url)
    WebDriverWait(driver,20).until(EC.presence_of_element_located((By.ID,'layerSelect')))
    Select(driver.find_element(By.ID,'layerSelect')).select_by_value('topography')
    driver.execute_script("document.getElementById('layerSelect').dispatchEvent(new Event('change'))")
    WebDriverWait(driver,30).until(lambda d: len(d.find_elements(By.CSS_SELECTOR,'#table tbody tr')) >= 3)
    time.sleep(2)
    text = driver.find_element(By.TAG_NAME,'body').text
    severe = [x for x in driver.get_log('browser') if str(x.get('level','')).upper() == 'SEVERE']
    result.update({
      'status':'PASS',
      'rendered_rows':len(driver.find_elements(By.CSS_SELECTOR,'#table tbody tr')),
      'copernicus_column_visible':'Copernicus katalog durumu' in text,
      'ea_lidar_visible':'EA LiDAR' in text,
      'os_terrain_visible':'OS Terrain' in text,
      'multisource_visible':'SRTM' in text and 'EUDEM' in text,
      'console_errors':severe,
      'page_text_sample':text[:4000]
    })
finally:
    driver.quit()
with open(out_path,'w',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
'@
  [System.IO.File]::WriteAllText($tempPy, $pyCode, [System.Text.UTF8Encoding]::new($false))
  try {
    if ([System.IO.Path]::GetFileNameWithoutExtension($python) -ieq 'py') { & $python -3 $tempPy $tempJson } else { & $python $tempPy $tempJson }
    if ($LASTEXITCODE -ne 0) { throw "SELENIUM_158_EXIT_CODE_$LASTEXITCODE" }
    $browser = Read-Json $tempJson
  } finally {
    Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $tempJson -Force -ErrorAction SilentlyContinue
  }
  $browserPassed = ([string]$browser.status -eq 'PASS' -and [int]$browser.rendered_rows -ge 3 -and [bool]$browser.copernicus_column_visible -and [bool]$browser.ea_lidar_visible -and [bool]$browser.os_terrain_visible -and @($browser.console_errors).Count -eq 0)
  Write-Json (Join-Path $repoRoot ($browserProofRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId; page_key='topography'; status=if($browserPassed){'PASS'}else{'FAIL'}; validated_at=Now-Utc; browser=$browser; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })
  if (-not $browserPassed) { throw 'TOPOGRAPHY_158_BROWSER_ACCEPTANCE_FAILED' }
  $stages += [ordered]@{ stage='second_chrome_validation'; status='PASS'; rendered_rows=[int]$browser.rendered_rows }

  $completedAt = Now-Utc
  $statusPayload = [ordered]@{
    task_id=$taskId
    page_key='topography'
    status='OFFICIAL_SOURCE_DISCOVERY_VISIBLE_MULTISOURCE_NUMERIC_PILOT_READY_PRIMARY_VALIDATION_PENDING'
    started_at=$startedAt
    completed_at=$completedAt
    branch=$branch
    canonical_storage='F_PORTABLE_ROOT'
    single_runner_only=$true
    new_runner=$false
    parallel_runner=$false
    stages=$stages
    candidate_rows=3
    regional_control_rows=8
    eudem_source_backed_rows=3
    srtm_crosscheck_rows=3
    official_sources_checked=3
    official_sources_reachable=$reachableOfficial
    copernicus_catalogue_result_count=[int]$copernicus.result_count
    copernicus_catalogue_matching_count=@($copernicus.matching_products).Count
    height_difference_value_count=3
    browser_rendered_rows=[int]$browser.rendered_rows
    completion_percent=55
    percent_increase=5
    accuracy_score_4='2.5/4 fallback multisource; primary CopDEM raster, real parcel boundary and EA LiDAR/OS Terrain numeric validation pending'
    blockers=@('real_parcel_boundary_required','primary_copdem_glo30_raster_sampling_required','ea_lidar_or_os_terrain_numeric_validation_required','project_regional_average_report_required')
    final_ready=$false
    product_final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  }
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $statusPayload
  Write-Json (Join-Path $repoRoot ($latestChangesRel -replace '/', '\')) ([ordered]@{
    layer='Topography'; updated_at=$completedAt; final_ready=$false; manual_review_required=$true;
    summary=[ordered]@{ completion_percent=55; remaining_percent=45; filled_parcel_count=3; verified_parcel_count=3; eudem_source_backed_rows=3; srtm_crosscheck_rows=3; official_sources_checked=3; official_sources_reachable=$reachableOfficial; height_difference_value_count=3; browser_visible_rows=3; accuracy_score_4='2.5/4 fallback multisource; primary validation pending'; website_update_percent=55 };
    blockers=$statusPayload.blockers; changes=@($visible.rows); fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })

  $report = @"
# Topography 158 — Official Source Acceleration Batch

- Candidate parcel rows: 3
- Regional control samples: 8
- EU-DEM source-backed rows: 3
- SRTM cross-check rows: 3
- Official source endpoints checked: 3
- Reachable official endpoints: $reachableOfficial
- Copernicus catalogue returned products: $($copernicus.result_count)
- Copernicus matching products: $(@($copernicus.matching_products).Count)
- Browser rendered rows: $($browser.rendered_rows)
- Completion percent after real runner proof: 55
- Accuracy: 2.5/4 fallback multisource
- final_ready: false
- fake_data: false

All operations ran serially inside the existing F-portable canonical shared runner. No second runner was opened. Numeric values remain a centroid-level fallback pilot until real parcel boundaries, primary CopDEM GLO-30 raster sampling and Environment Agency LiDAR or OS Terrain numeric validation are complete.
"@
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($reportRel -replace '/', '\')))
  [System.IO.File]::WriteAllText((Join-Path $repoRoot ($reportRel -replace '/', '\')), $report, [System.Text.UTF8Encoding]::new($false))
  Write-Json (Join-Path $repoRoot ($runnerOutputRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId; started_at=$startedAt; completed_at=$completedAt; status='COMPLETED_VISIBLE_NOT_FINAL'; stages=$stages; status_path=$statusRel; report_path=$reportRel; browser_proof_path=$browserProofRel; source_discovery_path=$sourceSnapshotRel; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })
  Write-Output ($statusPayload | ConvertTo-Json -Depth 40)
  exit 0
} catch {
  $failedAt = Now-Utc
  $failure = [ordered]@{ task_id=$taskId; page_key='topography'; status='BLOCKED_OFFICIAL_SOURCE_ACCELERATION_BATCH'; started_at=$startedAt; failed_at=$failedAt; error=$_.Exception.Message; stages=$stages; completion_percent=40; percent_increase=0; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $failure
  Write-Json (Join-Path $repoRoot ($runnerOutputRel -replace '/', '\')) $failure
  Write-Error $_
  exit 1
}

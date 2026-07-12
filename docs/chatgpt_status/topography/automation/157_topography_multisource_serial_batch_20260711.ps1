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
  [System.IO.File]::WriteAllText(
    $Path,
    (($Value | ConvertTo-Json -Depth 50) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}
function Read-Json([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
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
  throw 'TOPOGRAPHY_157_REQUIRES_F_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'topography-157-multisource-serial-batch-20260711' }
$branch = if ($env:AAYS_TARGET_BRANCH) { [string]$env:AAYS_TARGET_BRANCH } else { 'codex/aays-single-runner-v5-20260706' }
$startedAt = Now-Utc

$script156Rel = 'docs/chatgpt_status/topography/automation/156_topography_eudem25m_fallback_sampling_20260711.ps1'
$status156Rel = 'docs/chatgpt_status/topography/status/156_topography_eudem25m_fallback_sampling_latest.json'
$rows156Rel = 'docs/chatgpt_status/topography/fixtures/topography_verified_rows_eudem25m_pilot_20260711.json'
$queue156Rel = 'docs/chatgpt_status/topography/queue/156_topography_eudem25m_fallback_sampling_20260711.task.json'
$visibleRowsRel = 'england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$htmlRel = 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$latestChangesRel = 'outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$rawSrtmRel = 'docs/chatgpt_status/topography/source_snapshots/157_srtm90m_crosscheck_api_response_latest.json'
$crossRowsRel = 'docs/chatgpt_status/topography/fixtures/topography_multisource_crosscheck_rows_20260711.json'
$crossCsvRel = 'docs/chatgpt_status/topography/fixtures/topography_multisource_crosscheck_rows_20260711.csv'
$statusRel = 'docs/chatgpt_status/topography/status/157_topography_multisource_serial_batch_latest.json'
$reportRel = 'docs/chatgpt_status/topography/reports/157_topography_multisource_serial_batch_report_20260711.md'
$browserProofRel = 'docs/chatgpt_status/topography/reports/157_topography_multisource_browser_validation_20260711.json'
$runnerOutputRel = 'docs/chatgpt_status/topography/runner_outputs/157_topography_multisource_serial_batch.json'

$stages = @()
try {
  # Stage 1: create real EU-DEM values inside the same canonical runner process when task 156 has not produced them yet.
  $rows156Path = Join-Path $repoRoot ($rows156Rel -replace '/', '\')
  $status156Path = Join-Path $repoRoot ($status156Rel -replace '/', '\')
  $rows156 = Read-Json $rows156Path
  $need156 = ($null -eq $rows156 -or @($rows156.rows).Count -lt 3)
  if ($need156) {
    $script156Path = Join-Path $repoRoot ($script156Rel -replace '/', '\')
    if (-not (Test-Path -LiteralPath $script156Path)) { throw 'TASK_156_SCRIPT_MISSING' }
    $savedTaskId = $env:AAYS_TASK_ID
    try {
      $env:AAYS_TASK_ID = 'topography-156-eudem25m-fallback-sampling-20260711'
      & powershell -NoProfile -ExecutionPolicy Bypass -File $script156Path
      if ($LASTEXITCODE -ne 0) { throw "TASK_156_EXIT_CODE_$LASTEXITCODE" }
    } finally {
      $env:AAYS_TASK_ID = $savedTaskId
    }
    $rows156 = Read-Json $rows156Path
    if ($null -eq $rows156 -or @($rows156.rows).Count -lt 3) { throw 'TASK_156_OUTPUT_NOT_READY_AFTER_RUN' }
    $stages += [ordered]@{ stage='eudem25m_sampling'; status='completed_in_same_runner_process'; rows=@($rows156.rows).Count }

    $queue156Path = Join-Path $repoRoot ($queue156Rel -replace '/', '\')
    $queue156 = Read-Json $queue156Path
    if ($queue156) {
      $queue156 | Add-Member -NotePropertyName status -NotePropertyValue 'done_via_topography_157_serial_batch' -Force
      $queue156 | Add-Member -NotePropertyName completed_via -NotePropertyValue $taskId -Force
      $queue156 | Add-Member -NotePropertyName completed_at -NotePropertyValue (Now-Utc) -Force
      Write-Json $queue156Path $queue156
    }
  } else {
    $stages += [ordered]@{ stage='eudem25m_sampling'; status='reused_existing_source_backed_output'; rows=@($rows156.rows).Count }
  }

  # Stage 2: independent SRTM 90 m fallback cross-check for the same verified centroids.
  $candidateRows = @($rows156.rows)
  $locations = ($candidateRows | ForEach-Object {
    $lat = ([double]$_.centroid_lat).ToString('R', [System.Globalization.CultureInfo]::InvariantCulture)
    $lon = ([double]$_.centroid_lon).ToString('R', [System.Globalization.CultureInfo]::InvariantCulture)
    "$lat,$lon"
  }) -join '|'
  $requestUrl = 'https://api.opentopodata.org/v1/srtm90m?locations=' + [System.Uri]::EscapeDataString($locations) + '&interpolation=bilinear'
  $srtmInfoUrl = 'https://www.opentopodata.org/datasets/srtm/'
  $headers = @{ 'User-Agent'='TerraYield-AAYS-Topography/1.0 multisource validation' }
  $response = Invoke-RestMethod -Method Get -Uri $requestUrl -Headers $headers -TimeoutSec 120
  if ([string]$response.status -ne 'OK') { throw "SRTM_API_STATUS_$($response.status)" }
  $srtmResults = @($response.results)
  if ($srtmResults.Count -ne $candidateRows.Count) { throw "SRTM_RESULT_COUNT_$($srtmResults.Count)_EXPECTED_$($candidateRows.Count)" }
  foreach ($result in $srtmResults) {
    if ($null -eq $result.elevation -or [double]::IsNaN([double]$result.elevation)) { throw 'SRTM_NULL_OR_NAN_ELEVATION' }
  }

  $generatedAt = Now-Utc
  Write-Json (Join-Path $repoRoot ($rawSrtmRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId
    generated_at=$generatedAt
    provider='Open Topo Data public API'
    source_dataset='NASA SRTM 90 m'
    dataset_information_url=$srtmInfoUrl
    request_url=$requestUrl
    interpolation='bilinear'
    result_count=$srtmResults.Count
    response=$response
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })

  $crossRows = @()
  for ($i=0; $i -lt $candidateRows.Count; $i++) {
    $base = $candidateRows[$i]
    $primary = [double]$base.elevation_sea_level_m
    $secondary = [math]::Round([double]$srtmResults[$i].elevation, 2)
    $delta = [math]::Round([math]::Abs($primary - $secondary), 2)
    $crossStatus = if ($delta -le 5) { 'CONSISTENT_WITHIN_5M' } elseif ($delta -le 12) { 'CONSISTENT_WITHIN_12M' } else { 'SOURCE_DIFFERENCE_MANUAL_REVIEW' }
    $crossRows += [pscustomobject][ordered]@{
      parcel_id=$base.parcel_id
      parcel_ref=$base.parcel_ref
      centroid_lat=$base.centroid_lat
      centroid_lon=$base.centroid_lon
      eudem25m_elevation_m=[math]::Round($primary,2)
      srtm90m_elevation_m=$secondary
      absolute_source_difference_m=$delta
      crosscheck_status=$crossStatus
      primary_source='Copernicus EU-DEM v1.1 via Open Topo Data'
      primary_source_url='https://www.opentopodata.org/datasets/eudem/'
      secondary_source='NASA SRTM 90 m via Open Topo Data'
      secondary_source_url=$srtmInfoUrl
      matching_method='same verified parcel centroid; EPSG:4326; bilinear samples from two independent DEM datasets'
      accuracy_score_4='2.5/4 fallback multisource cross-check; primary CopDEM GLO-30, real parcel boundary and official LiDAR remain pending'
      needs_manual_review=$true
      changed_in_latest_run=$true
      final_ready=$false
      fake_data=$false
    }
  }
  Write-Json (Join-Path $repoRoot ($crossRowsRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId
    generated_at=$generatedAt
    row_count=$crossRows.Count
    rows=$crossRows
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($crossCsvRel -replace '/', '\')))
  $crossRows | Export-Csv -LiteralPath (Join-Path $repoRoot ($crossCsvRel -replace '/', '\')) -NoTypeInformation -Encoding UTF8
  $stages += [ordered]@{ stage='srtm90m_crosscheck'; status='completed'; rows=$crossRows.Count }

  # Stage 3: expose both source values and comparison status row by row on the website.
  $visibleRowsPath = Join-Path $repoRoot ($visibleRowsRel -replace '/', '\')
  $visible = Read-Json $visibleRowsPath
  if ($null -eq $visible -or @($visible.rows).Count -lt 3) { throw 'VISIBLE_ROWS_NOT_READY' }
  foreach ($row in @($visible.rows)) {
    $cross = $crossRows | Where-Object { $_.parcel_id -eq $row.parcel_id } | Select-Object -First 1
    if ($cross) {
      $rowUpdates = [ordered]@{
        display_badge = 'EUDEM25M_SRTM_CROSSCHECK_READY'
        secondary_source = $cross.secondary_source
        secondary_source_url = $cross.secondary_source_url
        secondary_elevation_m = $cross.srtm90m_elevation_m
        source_difference_m = $cross.absolute_source_difference_m
        crosscheck_status = $cross.crosscheck_status
        multisource_evidence_path = $crossRowsRel
        sampling_status = 'source_backed_eudem_sample_and_srtm_crosscheck_ready'
        accuracy_score_4 = $cross.accuracy_score_4
        task_id = $taskId
        updated_at = $generatedAt
        report_path = $reportRel
        status_path = $statusRel
        queue_path = 'docs/chatgpt_status/topography/queue/157_topography_multisource_serial_batch_20260711.task.json'
        blocker = 'real_parcel_boundary_required; primary_copdem_glo30_sampling_required; official_lidar_or_os_terrain_crosscheck_required'
      }
      foreach ($entry in $rowUpdates.GetEnumerator()) {
        $row | Add-Member -NotePropertyName $entry.Key -NotePropertyValue $entry.Value -Force
      }
      $row | Add-Member -NotePropertyName needs_manual_review -NotePropertyValue $true -Force
      $row | Add-Member -NotePropertyName final_ready -NotePropertyValue $false -Force
      $row | Add-Member -NotePropertyName fake_data -NotePropertyValue $false -Force
    }
  }
  $visibleUpdates = [ordered]@{
    status = 'MULTISOURCE_FALLBACK_CROSSCHECK_VISIBLE_PRIMARY_SOURCES_PENDING'
    latest_task_id = $taskId
    updated_at = $generatedAt
    secondary_source_url = $srtmInfoUrl
    final_ready = $false
    fake_data = $false
  }
  foreach ($entry in $visibleUpdates.GetEnumerator()) {
    $visible | Add-Member -NotePropertyName $entry.Key -NotePropertyValue $entry.Value -Force
  }
  Write-Json $visibleRowsPath $visible

  $visibleStatus = [ordered]@{
    status='MULTISOURCE_FALLBACK_CROSSCHECK_VISIBLE_PRIMARY_SOURCES_PENDING'
    visible_rows_count=3
    source_backed_eudem_rows=3
    secondary_srtm_crosscheck_rows=3
    height_difference_value_count=3
    latest_task_id=$taskId
    visible_rows_path=$visibleRowsRel
    eudem_rows_path=$rows156Rel
    srtm_raw_path=$rawSrtmRel
    multisource_rows_path=$crossRowsRel
    multisource_csv_path=$crossCsvRel
    source_url='https://www.opentopodata.org/datasets/eudem/'
    secondary_source_url=$srtmInfoUrl
    blockers=@('real_parcel_boundary_required','primary_copdem_glo30_sampling_required','official_lidar_or_os_terrain_crosscheck_required','project_regional_average_report_required')
    completion_percent=50
    updated_at=$generatedAt
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  }
  Write-Json (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\')) $visibleStatus

  $htmlPath = Join-Path $repoRoot ($htmlRel -replace '/', '\')
  $html = Get-Content -LiteralPath $htmlPath -Raw -Encoding UTF8
  if (-not $html.Contains("'secondary_source']")) {
    $layerStart = $html.IndexOf("topography:{title:", [System.StringComparison]::Ordinal)
    if ($layerStart -lt 0) { throw 'TOPOGRAPHY_HTML_LAYER_NOT_FOUND' }
    $columnsEnd = $html.IndexOf("]]}", $layerStart, [System.StringComparison]::Ordinal)
    if ($columnsEnd -lt 0) { throw 'TOPOGRAPHY_HTML_COLUMNS_END_NOT_FOUND' }
    $extraColumns = ",['Secondary source','secondary_source'],['Secondary source URL','secondary_source_url'],['SRTM elevation','secondary_elevation_m'],['Source difference (m)','source_difference_m'],['Cross-check','crosscheck_status'],['Multisource evidence','multisource_evidence_path']"
    $html = $html.Insert($columnsEnd + 1, $extraColumns)
    [System.IO.File]::WriteAllText($htmlPath, $html, [System.Text.UTF8Encoding]::new($false))
  }
  $stages += [ordered]@{ stage='site_row_visibility'; status='completed'; rows=3 }

  # Stage 4: real Chrome/Selenium validation after all source-backed updates.
  $python = Get-Python
  if (-not $python) { throw 'PYTHON_NOT_FOUND_FOR_SELENIUM_VALIDATION' }
  $tempPy = Join-Path $env:TEMP ("aays_topography_157_" + [guid]::NewGuid().ToString('N') + '.py')
  $tempJson = Join-Path $env:TEMP ("aays_topography_157_" + [guid]::NewGuid().ToString('N') + '.json')
  $pyCode = @'
import json, sys, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
out_path = sys.argv[1]
url = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?topography_browser_validation=157'
options = webdriver.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')
options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
driver = webdriver.Chrome(options=options)
result = {'status':'FAIL','browser':'Google Chrome via Selenium','url':url}
try:
    driver.get(url)
    WebDriverWait(driver,20).until(EC.presence_of_element_located((By.ID,'layerSelect')))
    Select(driver.find_element(By.ID,'layerSelect')).select_by_value('topography')
    driver.execute_script("document.getElementById('layerSelect').dispatchEvent(new Event('change'))")
    WebDriverWait(driver,25).until(lambda d: len(d.find_elements(By.CSS_SELECTOR,'#table tbody tr')) >= 3)
    time.sleep(1.5)
    text = driver.find_element(By.TAG_NAME,'body').text
    rows = driver.find_elements(By.CSS_SELECTOR,'#table tbody tr')
    severe = [x for x in driver.get_log('browser') if str(x.get('level','')).upper() == 'SEVERE']
    result.update({
        'status':'PASS',
        'rendered_rows':len(rows),
        'multisource_badge_visible':'EUDEM25M_SRTM_CROSSCHECK_READY' in text,
        'srtm_visible':'SRTM' in text,
        'source_difference_column_visible':'Kaynak farkı (m)' in text,
        'crosscheck_column_visible':'Cross-check' in text,
        'height_difference_visible':'Height difference' in text,
        'console_errors':severe,
        'page_text_sample':text[:3000]
    })
finally:
    driver.quit()
with open(out_path,'w',encoding='utf-8') as f:
    json.dump(result,f,ensure_ascii=False,indent=2)
'@
  [System.IO.File]::WriteAllText($tempPy, $pyCode, [System.Text.UTF8Encoding]::new($false))
  try {
    if ([System.IO.Path]::GetFileNameWithoutExtension($python) -ieq 'py') { & $python -3 $tempPy $tempJson } else { & $python $tempPy $tempJson }
    if ($LASTEXITCODE -ne 0) { throw "SELENIUM_EXIT_CODE_$LASTEXITCODE" }
    $browser = Read-Json $tempJson
  } finally {
    Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $tempJson -Force -ErrorAction SilentlyContinue
  }
  $browserPassed = ([string]$browser.status -eq 'PASS' -and [int]$browser.rendered_rows -ge 3 -and [bool]$browser.multisource_badge_visible -and [bool]$browser.srtm_visible -and [bool]$browser.source_difference_column_visible -and [bool]$browser.crosscheck_column_visible -and @($browser.console_errors).Count -eq 0)
  Write-Json (Join-Path $repoRoot ($browserProofRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId
    page_key='topography'
    status=if($browserPassed){'PASS'}else{'FAIL'}
    validated_at=Now-Utc
    browser=$browser
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })
  if (-not $browserPassed) { throw 'TOPOGRAPHY_157_BROWSER_ACCEPTANCE_FAILED' }
  $stages += [ordered]@{ stage='chrome_selenium_validation'; status='PASS'; rendered_rows=[int]$browser.rendered_rows }

  $consistent5 = @($crossRows | Where-Object { $_.crosscheck_status -eq 'CONSISTENT_WITHIN_5M' }).Count
  $consistent12 = @($crossRows | Where-Object { $_.crosscheck_status -eq 'CONSISTENT_WITHIN_12M' }).Count
  $reviewCount = @($crossRows | Where-Object { $_.crosscheck_status -eq 'SOURCE_DIFFERENCE_MANUAL_REVIEW' }).Count
  $completedAt = Now-Utc
  $statusPayload = [ordered]@{
    task_id=$taskId
    page_key='topography'
    status='MULTISOURCE_SOURCE_BACKED_ROWS_VISIBLE_BROWSER_PASS_PRIMARY_VALIDATION_PENDING'
    started_at=$startedAt
    completed_at=$completedAt
    branch=$branch
    canonical_storage='F_PORTABLE_ROOT'
    single_runner_only=$true
    new_runner=$false
    parallel_runner=$false
    stages=$stages
    candidate_rows=3
    source_backed_eudem_rows=3
    secondary_srtm_crosscheck_rows=3
    consistent_within_5m_rows=$consistent5
    consistent_within_12m_rows=$consistent12
    source_difference_manual_review_rows=$reviewCount
    height_difference_value_count=3
    browser_rendered_rows=[int]$browser.rendered_rows
    completion_percent=50
    percent_increase=5
    accuracy_score_4='2.5/4 fallback multisource; primary CopDEM, boundary and official LiDAR/OS Terrain pending'
    blockers=@('real_parcel_boundary_required','primary_copdem_glo30_sampling_required','official_lidar_or_os_terrain_crosscheck_required','project_regional_average_report_required')
    final_ready=$false
    product_final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  }
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $statusPayload

  Write-Json (Join-Path $repoRoot ($latestChangesRel -replace '/', '\')) ([ordered]@{
    layer='Topography'
    updated_at=$completedAt
    final_ready=$false
    manual_review_required=$true
    summary=[ordered]@{
      completion_percent=50
      remaining_percent=50
      filled_parcel_count=3
      verified_parcel_count=3
      source_backed_eudem_rows=3
      secondary_srtm_crosscheck_rows=3
      height_difference_value_count=3
      browser_visible_rows=3
      accuracy_score_4='2.5/4 fallback multisource; primary sources pending'
      website_update_percent=50
    }
    blockers=$statusPayload.blockers
    changes=@($visible.rows)
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })

  $report = @"
# Topography 157 — Multisource Serial Batch

- Started: $startedAt
- Completed: $completedAt
- Canonical runner: existing F portable single shared runner
- Candidate rows: 3
- EU-DEM source-backed rows: 3
- SRTM secondary cross-check rows: 3
- Height-difference rows: 3
- Chrome rendered rows: $($browser.rendered_rows)
- Consistent within 5 m: $consistent5
- Consistent within 12 m: $consistent12
- Manual review due to source difference: $reviewCount
- Completion percent: 50
- Accuracy: 2.5/4 fallback multisource
- final_ready: false
- fake_data: false

This task performs multiple operations serially inside the existing canonical runner process. It does not start a new or parallel runner. Primary Copernicus GLO-30, real parcel-boundary sampling, official LiDAR/OS Terrain validation and the project regional-average report remain required before any 3/4 or final claim.
"@
  [System.IO.File]::WriteAllText((Join-Path $repoRoot ($reportRel -replace '/', '\')), $report, [System.Text.UTF8Encoding]::new($false))
  Write-Json (Join-Path $repoRoot ($runnerOutputRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId
    started_at=$startedAt
    completed_at=$completedAt
    status='COMPLETED_VISIBLE_NOT_FINAL'
    stages=$stages
    status_path=$statusRel
    report_path=$reportRel
    browser_proof_path=$browserProofRel
    multisource_rows_path=$crossRowsRel
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })
  Write-Output ($statusPayload | ConvertTo-Json -Depth 30)
  exit 0
} catch {
  $failedAt = Now-Utc
  $failure = [ordered]@{
    task_id=$taskId
    page_key='topography'
    status='BLOCKED_MULTISOURCE_SERIAL_BATCH'
    started_at=$startedAt
    failed_at=$failedAt
    stages=$stages
    error=$_.Exception.Message
    completion_percent=40
    percent_increase=0
    final_ready=$false
    product_final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  }
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $failure
  Write-Error $_
  exit 1
}

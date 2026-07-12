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
    (($Value | ConvertTo-Json -Depth 40) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
}
function Classify-Elevation([double]$Value) {
  if ($Value -lt 10) { return 'very_low' }
  if ($Value -lt 30) { return 'low' }
  if ($Value -lt 75) { return 'moderate' }
  if ($Value -lt 150) { return 'elevated' }
  return 'high'
}
function Color-For-Elevation([double]$Value) {
  if ($Value -lt 10) { return 'blue' }
  if ($Value -lt 30) { return 'green' }
  if ($Value -lt 75) { return 'yellow' }
  if ($Value -lt 150) { return 'orange' }
  return 'red'
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or -not $repoRoot.StartsWith('F:\TerraYield_AAYS_Portable\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw 'TOPography_156_REQUIRES_F_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'topography-156-eudem25m-fallback-sampling-20260711' }
$branch = if ($env:AAYS_TARGET_BRANCH) { [string]$env:AAYS_TARGET_BRANCH } else { 'codex/aays-single-runner-v5-20260706' }
$startedAt = Now-Utc

$candidates = @(
  [ordered]@{ parcel_id='parcel_2757'; parcel_ref='52213412'; lat=51.6167362; lon=-0.1421556; bng_tile='TQ2892' },
  [ordered]@{ parcel_id='parcel_2758'; parcel_ref='52213916'; lat=51.6168592; lon=-0.1417993; bng_tile='TQ2892' },
  [ordered]@{ parcel_id='parcel_2759'; parcel_ref='52040420'; lat=51.6169525; lon=-0.1430858; bng_tile='TQ2892' }
)

# Eight nearby control points around the three parcel centroids. These form a pilot
# regional reference only; they are not a substitute for the project-wide regional report.
$regionalControls = @(
  [ordered]@{ id='regional_n';  lat=51.6188493; lon=-0.1423469 },
  [ordered]@{ id='regional_s';  lat=51.6148493; lon=-0.1423469 },
  [ordered]@{ id='regional_e';  lat=51.6168493; lon=-0.1393469 },
  [ordered]@{ id='regional_w';  lat=51.6168493; lon=-0.1453469 },
  [ordered]@{ id='regional_ne'; lat=51.6183493; lon=-0.1401469 },
  [ordered]@{ id='regional_nw'; lat=51.6183493; lon=-0.1445469 },
  [ordered]@{ id='regional_se'; lat=51.6153493; lon=-0.1401469 },
  [ordered]@{ id='regional_sw'; lat=51.6153493; lon=-0.1445469 }
)

$allPoints = @()
foreach ($item in $candidates) { $allPoints += [pscustomobject]@{ id=$item.parcel_id; lat=$item.lat; lon=$item.lon; kind='candidate' } }
foreach ($item in $regionalControls) { $allPoints += [pscustomobject]@{ id=$item.id; lat=$item.lat; lon=$item.lon; kind='regional_control' } }

$locations = ($allPoints | ForEach-Object { ('{0},{1}' -f $_.lat, $_.lon) }) -join '|'
$encodedLocations = [System.Uri]::EscapeDataString($locations)
$requestUrl = "https://api.opentopodata.org/v1/eudem25m?locations=$encodedLocations&interpolation=bilinear"
$requestEndpoint = 'https://api.opentopodata.org/v1/eudem25m'
$datasetInfoUrl = 'https://www.opentopodata.org/datasets/eudem/'

$rawRel = 'docs/chatgpt_status/topography/source_snapshots/156_eudem25m_api_response_latest.json'
$rowsRel = 'docs/chatgpt_status/topography/fixtures/topography_verified_rows_eudem25m_pilot_20260711.json'
$csvRel = 'docs/chatgpt_status/topography/fixtures/topography_verified_rows_eudem25m_pilot_20260711.csv'
$statusRel = 'docs/chatgpt_status/topography/status/156_topography_eudem25m_fallback_sampling_latest.json'
$reportRel = 'docs/chatgpt_status/topography/reports/156_topography_eudem25m_fallback_sampling_report_20260711.md'
$visibleRowsRel = 'england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$latestChangesRel = 'outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'

try {
  $headers = @{ 'User-Agent'='TerraYield-AAYS-Topography/1.0 source-backed pilot' }
  $response = Invoke-RestMethod -Method Post -Uri $requestEndpoint -Headers $headers -Body @{locations=$locations;interpolation='bilinear'} -ContentType 'application/x-www-form-urlencoded' -TimeoutSec 120
  if ([string]$response.status -ne 'OK') { throw "EUDEM_API_STATUS_$($response.status)" }
  $results = @($response.results)
  if ($results.Count -ne $allPoints.Count) { throw "EUDEM_RESULT_COUNT_$($results.Count)_EXPECTED_$($allPoints.Count)" }
  foreach ($result in $results) {
    if ($null -eq $result.elevation -or [double]::IsNaN([double]$result.elevation)) {
      throw 'EUDEM_NULL_OR_NAN_ELEVATION'
    }
  }

  $generatedAt = Now-Utc
  $rawPayload = [ordered]@{
    task_id = $taskId
    generated_at = $generatedAt
    provider = 'Open Topo Data public API'
    source_dataset = 'Copernicus EU-DEM v1.1'
    dataset_endpoint = 'eudem25m'
    dataset_information_url = $datasetInfoUrl
    request_method = 'POST'
    request_url = $requestUrl
    request_locations = $locations
    interpolation = 'bilinear'
    candidate_count = $candidates.Count
    regional_control_count = $regionalControls.Count
    response = $response
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  Write-Json (Join-Path $repoRoot ($rawRel -replace '/', '\')) $rawPayload

  $controlElevations = @()
  for ($i = $candidates.Count; $i -lt $results.Count; $i++) {
    $controlElevations += [double]$results[$i].elevation
  }
  $regionalAverage = [math]::Round([double](($controlElevations | Measure-Object -Average).Average), 2)
  $controlMin = [math]::Round([double](($controlElevations | Measure-Object -Minimum).Minimum), 2)
  $controlMax = [math]::Round([double](($controlElevations | Measure-Object -Maximum).Maximum), 2)

  $verifiedRows = @()
  for ($i = 0; $i -lt $candidates.Count; $i++) {
    $candidate = $candidates[$i]
    $elevation = [math]::Round([double]$results[$i].elevation, 2)
    $difference = [math]::Round($elevation - $regionalAverage, 2)
    $verifiedRows += [pscustomobject][ordered]@{
      parcel_id = $candidate.parcel_id
      parcel_ref = $candidate.parcel_ref
      elevation_sea_level_m = $elevation
      regional_average_elevation_m = $regionalAverage
      elevation_difference_regional_average_m = $difference
      elevation_class = Classify-Elevation $elevation
      color_category = Color-For-Elevation $elevation
      confidence_rating = 'medium_fallback'
      confidence_percent = 72
      source = 'Copernicus EU-DEM v1.1 via Open Topo Data public API'
      source_url = $datasetInfoUrl
      source_date = $generatedAt.Substring(0,10)
      matching_method = 'verified parcel centroid; EPSG:4326; bilinear EU-DEM 25 m sample; parcel boundary not yet applied'
      calculation_explanation = "Parcel elevation minus mean of 8 nearby EU-DEM control samples. Regional pilot mean=$regionalAverage m; control range=$controlMin to $controlMax m."
      accuracy_score_4 = '2.5/4 fallback: official Copernicus-derived DEM and reproducible centroid sample; real parcel boundary, primary CopDEM GLO-30 and browser proof pending'
      needs_manual_review = $true
      changed_in_latest_run = $true
      centroid_lat = $candidate.lat
      centroid_lon = $candidate.lon
      bng_tile = $candidate.bng_tile
      dataset = 'EU-DEM v1.1'
      dataset_resolution_m = 25
      vertical_datum = 'EVRS2000'
      interpolation = 'bilinear'
      regional_control_sample_count = $regionalControls.Count
      regional_control_min_m = $controlMin
      regional_control_max_m = $controlMax
      raw_source_path = $rawRel
      task_id = $taskId
      final_ready = $false
      fake_data = $false
    }
  }

  Write-Json (Join-Path $repoRoot ($rowsRel -replace '/', '\')) ([ordered]@{
    task_id=$taskId
    generated_at=$generatedAt
    row_count=$verifiedRows.Count
    regional_control_sample_count=$regionalControls.Count
    regional_average_elevation_m=$regionalAverage
    rows=$verifiedRows
    final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($csvRel -replace '/', '\')))
  $verifiedRows | Export-Csv -LiteralPath (Join-Path $repoRoot ($csvRel -replace '/', '\')) -NoTypeInformation -Encoding UTF8

  $visibleRowsPath = Join-Path $repoRoot ($visibleRowsRel -replace '/', '\')
  $visible = Get-Content -LiteralPath $visibleRowsPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $updatedVisibleRows = @()
  foreach ($row in @($visible.rows)) {
    $verified = $verifiedRows | Where-Object { $_.parcel_id -eq $row.parcel_id } | Select-Object -First 1
    if ($verified) {
      $row.display_badge = 'EUDEM25M_SOURCE_BACKED_PILOT'
      $row.sampling_status = 'source_backed_fallback_centroid_sample_ready'
      $row.boundary_status = 'pending_real_boundary'
      $row.elevation_sea_level_m = $verified.elevation_sea_level_m
      $row.regional_average_elevation_m = $verified.regional_average_elevation_m
      $row.elevation_difference_regional_average_m = $verified.elevation_difference_regional_average_m
      $row.confidence_percent = $verified.confidence_percent
      $row.accuracy_score_4 = $verified.accuracy_score_4
      $row.dem_lidar_product_name = 'Copernicus EU-DEM v1.1 25 m fallback'
      $row.copdem_dataset = 'EU-DEM v1.1'
      $row.copdem_product_type = 'EUDEM25M_FALLBACK'
      $row.source_url = $datasetInfoUrl
      $row.source_file_path = $rawRel
      $row.local_source_path = $rawRel
      $row.report_path = $reportRel
      $row.status_path = $statusRel
      $row.queue_path = 'docs/chatgpt_status/topography/queue/156_topography_eudem25m_fallback_sampling_20260711.task.json'
      $row.task_id = $taskId
      $row.updated_at = $generatedAt
      $row.needs_manual_review = $true
      $row.blocker = 'real_parcel_boundary_required; primary_copdem_glo30_sampling_required; browser_smoke_required'
    }
    $updatedVisibleRows += $row
  }
  $visible.status = 'EUDEM25M_SOURCE_BACKED_PILOT_VISIBLE_PRIMARY_COPDEM_PENDING'
  $visible.updated_at = $generatedAt
  $visible.latest_task_id = $taskId
  $visible.source_url = $datasetInfoUrl
  $visible.rows = $updatedVisibleRows
  $visible.final_ready = $false
  $visible.fake_data = $false
  Write-Json $visibleRowsPath $visible

  $visibleStatus = [ordered]@{
    status = 'EUDEM25M_SOURCE_BACKED_PILOT_VISIBLE_PRIMARY_COPDEM_PENDING'
    visible_rows_count = 3
    new_operations_count = 3
    source_backed_fallback_elevation_rows = 3
    primary_copdem_elevation_rows = 0
    height_difference_value_count = 3
    latest_task_id = $taskId
    visible_rows_path = $visibleRowsRel
    raw_source_path = $rawRel
    verified_rows_path = $rowsRel
    verified_csv_path = $csvRel
    queue_path = 'docs/chatgpt_status/topography/queue/156_topography_eudem25m_fallback_sampling_20260711.task.json'
    status_path = $statusRel
    report_path = $reportRel
    source_url = $datasetInfoUrl
    regional_control_sample_count = 8
    regional_average_elevation_m = $regionalAverage
    blockers = @('real_parcel_boundary_required','primary_copdem_glo30_sampling_required','browser_smoke_required','project_regional_average_report_required')
    updated_at = $generatedAt
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  Write-Json (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\')) $visibleStatus

  $changes = @()
  foreach ($verified in $verifiedRows) {
    $changes += [ordered]@{
      changed_in_latest_run=$true
      display_badge='EUDEM25M_SOURCE_BACKED_PILOT'
      task_id=$taskId
      parcel_id=$verified.parcel_id
      parcel_ref=$verified.parcel_ref
      centroid_lat=$verified.centroid_lat
      centroid_lon=$verified.centroid_lon
      bng_tile=$verified.bng_tile
      sampling_status='source_backed_fallback_centroid_sample_ready'
      boundary_status='pending_real_boundary'
      elevation_sea_level_m=$verified.elevation_sea_level_m
      regional_average_elevation_m=$verified.regional_average_elevation_m
      elevation_difference_regional_average_m=$verified.elevation_difference_regional_average_m
      confidence_percent=$verified.confidence_percent
      accuracy_score_4=$verified.accuracy_score_4
      source_url=$datasetInfoUrl
      source_file_path=$rawRel
      final_ready=$false
      fake_data=$false
    }
  }
  Write-Json (Join-Path $repoRoot ($latestChangesRel -replace '/', '\')) ([ordered]@{
    layer='Topography'
    updated_at=$generatedAt
    final_ready=$false
    manual_review_required=$true
    summary=[ordered]@{
      completion_percent=45
      remaining_percent=55
      filled_parcel_count=3
      verified_parcel_count=3
      source_backed_fallback_elevation_rows=3
      primary_copdem_elevation_rows=0
      height_difference_value_count=3
      regional_control_sample_count=8
      accuracy_score_4='2.5/4 fallback; primary CopDEM and boundary pending'
      website_update_percent=45
    }
    blockers=@('real_parcel_boundary_required','primary_copdem_glo30_sampling_required','browser_smoke_required','project_regional_average_report_required')
    changes=$changes
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  })

  $statusPayload = [ordered]@{
    task_id=$taskId
    page_key='topography'
    status='SOURCE_BACKED_FALLBACK_PILOT_WRITTEN_BROWSER_AND_PRIMARY_SOURCE_PENDING'
    generated_at=$generatedAt
    branch=$branch
    canonical_storage='F_PORTABLE_ROOT'
    single_runner_only=$true
    new_runner=$false
    parallel_runner=$false
    candidate_rows=3
    regional_control_rows=8
    source_backed_fallback_elevation_rows=3
    primary_copdem_elevation_rows=0
    height_difference_value_count=3
    completion_percent=45
    percent_increase=5
    source='Copernicus EU-DEM v1.1 via Open Topo Data public API'
    source_url=$datasetInfoUrl
    raw_source_path=$rawRel
    verified_rows_path=$rowsRel
    verified_csv_path=$csvRel
    visible_rows_path=$visibleRowsRel
    visible_status_path=$visibleStatusRel
    blockers=@('real_parcel_boundary_required','primary_copdem_glo30_sampling_required','browser_smoke_required','project_regional_average_report_required')
    final_ready=$false
    product_final_ready=$false
    fake_data=$false
    db_write=$false
    migration=$false
    production_deploy=$false
  }
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $statusPayload

  $report = @"
# Topography 156 — EU-DEM 25 m Source-Backed Pilot

- Task: `$taskId`
- Generated: `$generatedAt`
- Candidate rows: 3
- Regional control samples: 8
- Source: Copernicus EU-DEM v1.1 via Open Topo Data public API
- Interpolation: bilinear
- Regional pilot average: $regionalAverage m
- Regional control range: $controlMin–$controlMax m
- Source-backed fallback elevation rows: 3
- Primary CopDEM GLO-30 rows: 0
- Browser smoke: pending
- Real parcel boundary sampling: pending
- final_ready: false
- fake_data: false

The numeric values are a reproducible centroid-level fallback pilot. They must not be promoted to primary or final parcel elevation until real parcel boundaries, primary CopDEM GLO-30/official LiDAR sampling, project regional-average evidence and browser validation are complete.
"@
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($reportRel -replace '/', '\')))
  [System.IO.File]::WriteAllText((Join-Path $repoRoot ($reportRel -replace '/', '\')), $report, [System.Text.UTF8Encoding]::new($false))

  Write-Output ($statusPayload | ConvertTo-Json -Depth 20)
  exit 0
} catch {
  $failedAt = Now-Utc
  $failure = [ordered]@{
    task_id=$taskId
    page_key='topography'
    status='BLOCKED_SOURCE_API_OR_VALIDATION_FAILED'
    generated_at=$failedAt
    error=$_.Exception.Message
    completion_percent=40
    percent_increase=0
    numeric_values_written=$false
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

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
  $tmp = "$Path.tmp"
  [System.IO.File]::WriteAllText($tmp, (($Value | ConvertTo-Json -Depth 80) + "`n"), [System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Read-Json([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Set-Prop([object]$Object, [string]$Name, [object]$Value) {
  Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force
}
function Get-Median([double[]]$Values) {
  $sorted = @($Values | Sort-Object)
  if ($sorted.Count -eq 0) { return $null }
  $mid = [int][math]::Floor($sorted.Count / 2)
  if (($sorted.Count % 2) -eq 1) { return [double]$sorted[$mid] }
  return ([double]$sorted[$mid - 1] + [double]$sorted[$mid]) / 2.0
}
function Invoke-Dem([string]$Dataset, [object[]]$Rows) {
  $locations = ($Rows | ForEach-Object {
    [string]::Format([Globalization.CultureInfo]::InvariantCulture, '{0:R},{1:R}', [double]$_.lat, [double]$_.lon)
  }) -join '|'
  $endpoint = "https://api.opentopodata.org/v1/$Dataset"
  $result = [ordered]@{
    dataset = $Dataset
    endpoint = $endpoint
    request_locations = $locations
    interpolation = 'bilinear'
    reachable = $false
    result_count = 0
    elevations = @()
    response = $null
    error = $null
  }
  try {
    $response = Invoke-RestMethod -Method Post -Uri $endpoint -Body @{ locations = $locations; interpolation = 'bilinear' } -ContentType 'application/x-www-form-urlencoded' -TimeoutSec 180 -Headers @{ 'User-Agent' = 'TerraYield-AAYS-Topography/1.0 regional-controls' }
    $rowsOut = @($response.results)
    if ([string]$response.status -ne 'OK') { throw "${Dataset}_API_STATUS_$($response.status)" }
    if ($rowsOut.Count -ne $Rows.Count) { throw "${Dataset}_RESULT_COUNT_$($rowsOut.Count)_EXPECTED_$($Rows.Count)" }
    foreach ($rowOut in $rowsOut) {
      if ($null -eq $rowOut.elevation) { throw "${Dataset}_NULL_ELEVATION" }
    }
    $result.reachable = $true
    $result.result_count = $rowsOut.Count
    $result.elevations = @($rowsOut | ForEach-Object { [math]::Round([double]$_.elevation, 2) })
    $result.response = $response
  } catch {
    $result.error = $_.Exception.Message
  }
  return [pscustomobject]$result
}
function Test-Source([string]$Name, [string]$Url) {
  $result = [ordered]@{ name = $Name; url = $Url; reachable = $false; status_code = $null; error = $null }
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 90 -Headers @{ 'User-Agent' = 'TerraYield-AAYS-Topography/1.0 official-source-check' }
    $result.status_code = [int]$response.StatusCode
    $result.reachable = ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400)
  } catch {
    try { $result.status_code = [int]$_.Exception.Response.StatusCode.value__ } catch {}
    $result.error = $_.Exception.Message
  }
  return [pscustomobject]$result
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or $repoRoot -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]') {
  throw 'TOPOGRAPHY_160_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'aays1-160-topography-regional-control-expansion-20260713' }
$startedAt = Now-Utc
$batchId = 'topography-160-' + ($startedAt -replace '[^0-9]', '')
$previousBatchId = 'aays1-159-topography-official-source-acceleration-bridge-20260711'
$stageCount = 8
$completedStages = 0
$currentStage = 'task_start'
$operations = @()
$stageRows = @()

$visibleRowsRel = 'england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$operationsRel = 'england_map_web/data/program_layer_matrix/topography_operations_latest.json'
$latestChangesRel = 'outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$sourceRel = 'docs/chatgpt_status/topography/source_snapshots/160_regional_control_sources_latest.json'
$controlRel = 'docs/chatgpt_status/topography/fixtures/topography_regional_control_rows_20260713.json'
$controlCsvRel = 'docs/chatgpt_status/topography/fixtures/topography_regional_control_rows_20260713.csv'
$statusRel = 'docs/chatgpt_status/topography/status/160_topography_regional_control_expansion_latest.json'
$reportRel = 'docs/chatgpt_status/topography/reports/160_topography_regional_control_expansion_report_20260713.md'
$outputRel = 'docs/chatgpt_status/topography/runner_outputs/160_topography_regional_control_expansion_batch.json'

function Add-Operation {
  param(
    [string]$Type,
    [string]$Status,
    [int]$StageNo,
    [string]$StageName,
    [string]$ParcelId = '',
    [object]$NumericValue = $null,
    [string]$Unit = '',
    [string]$SourceName = '',
    [string]$SourceUrl = '',
    [string]$EvidencePath = '',
    [string]$Blocker = ''
  )
  $script:operations += [pscustomobject][ordered]@{
    operation_id = "${batchId}_$($script:operations.Count + 1)"
    stage_no = $StageNo
    operation_type = $Type
    task_id = $taskId
    batch_id = $batchId
    previous_batch_id = $previousBatchId
    parcel_id = if ($ParcelId) { $ParcelId } else { $null }
    status = $Status
    is_new_operation = $true
    is_new_in_latest_batch = $true
    started_at = $startedAt
    completed_at = Now-Utc
    source_name = if ($SourceName) { $SourceName } else { $null }
    source_url = if ($SourceUrl) { $SourceUrl } else { $null }
    numeric_value = $NumericValue
    unit = if ($Unit) { $Unit } else { $null }
    method = if ($Type -match 'sample') { 'bilinear DEM sample' } elseif ($Type -match 'consensus') { 'median of available DEM values' } elseif ($Type -match 'average') { 'mean of 8 control-point medians' } else { $null }
    accuracy_score_4 = '2.5/4 fallback'
    repo_artifact_path = if ($EvidencePath) { $EvidencePath } else { $null }
    report_path = $reportRel
    status_path = $statusRel
    runner_output_path = $outputRel
    blocker = if ($Blocker) { $Blocker } else { $null }
    needs_manual_review = [bool]$Blocker
    final_ready = $false
    fake_data = $false
  }
}
function Publish-Ledger([string]$RunStatus) {
  $path = Join-Path $repoRoot ($operationsRel -replace '/', '\')
  $old = Read-Json $path
  $existing = @()
  if ($old) {
    $existing = @($old.operations)
    foreach ($op in $existing) {
      if ($null -ne $op) {
        Set-Prop $op 'is_new_operation' $false
        Set-Prop $op 'is_new_in_latest_batch' $false
      }
    }
  }
  $all = @($existing + $operations)
  $blocked = @($all | Where-Object { [string]$_.status -match 'blocked|failed|unavailable' })
  Write-Json $path ([ordered]@{
    task_id = $taskId
    batch_id = $batchId
    previous_batch_id = $previousBatchId
    updated_at = Now-Utc
    run_status = $RunStatus
    current_stage = $currentStage
    stage_completed_count = $completedStages
    stage_total_count = $stageCount
    operation_count = $all.Count
    new_operations_count = $operations.Count
    blocked_operation_count = $blocked.Count
    operations = $all
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })
}
function Complete-Stage([int]$StageNo, [string]$Name, [string]$Status = 'completed') {
  $script:completedStages = $StageNo
  $script:currentStage = $Name
  $script:stageRows += [pscustomobject][ordered]@{ stage_no = $StageNo; stage = $Name; status = $Status; completed_at = Now-Utc }
  Add-Operation -Type 'pipeline_stage' -Status $Status -StageNo $StageNo -StageName $Name -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'
}

try {
  Add-Operation -Type 'task_start' -Status 'running' -StageNo 1 -StageName 'task_start' -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'

  $visibleRowsPath = Join-Path $repoRoot ($visibleRowsRel -replace '/', '\')
  $visible = Read-Json $visibleRowsPath
  $parcelRows = @($visible.rows)
  if ($null -eq $visible -or $parcelRows.Count -lt 3) { throw 'TOPOGRAPHY_160_VISIBLE_ROWS_NOT_READY' }

  $centerLat = [double](($parcelRows | Measure-Object -Property centroid_lat -Average).Average)
  $centerLon = [double](($parcelRows | Measure-Object -Property centroid_lon -Average).Average)
  $radiusM = 500.0
  $diagonal = $radiusM / [math]::Sqrt(2.0)
  $lonScale = 111320.0 * [math]::Cos($centerLat * [math]::PI / 180.0)
  $offsets = @(
    @('N', 0.0, $radiusM), @('NE', $diagonal, $diagonal), @('E', $radiusM, 0.0), @('SE', $diagonal, -$diagonal),
    @('S', 0.0, -$radiusM), @('SW', -$diagonal, -$diagonal), @('W', -$radiusM, 0.0), @('NW', -$diagonal, $diagonal)
  )
  $controls = @()
  foreach ($offset in $offsets) {
    $control = [pscustomobject][ordered]@{
      control_id = "control_$($offset[0])"
      lat = [math]::Round($centerLat + ([double]$offset[2] / 111320.0), 7)
      lon = [math]::Round($centerLon + ([double]$offset[1] / $lonScale), 7)
      radius_m = $radiusM
      design_method = 'deterministic_8_point_500m_ring'
    }
    $controls += $control
    Add-Operation -Type 'regional_control_design' -Status 'completed' -StageNo 1 -StageName 'control_design' -ParcelId $control.control_id -NumericValue $radiusM -Unit 'm radius' -EvidencePath $controlRel
  }
  Complete-Stage -StageNo 1 -Name 'regional_control_design'

  $datasets = @('eudem25m', 'srtm90m', 'srtm30m', 'aster30m')
  $datasetUrls = @{
    eudem25m = 'https://www.opentopodata.org/datasets/eudem/'
    srtm90m = 'https://www.opentopodata.org/datasets/srtm/'
    srtm30m = 'https://www.opentopodata.org/datasets/srtm/'
    aster30m = 'https://www.opentopodata.org/datasets/aster/'
  }
  $demResults = [ordered]@{}
  $stageNo = 1
  foreach ($dataset in $datasets) {
    $stageNo++
    $currentStage = "${dataset}_regional_sampling"
    Publish-Ledger -RunStatus 'RUNNING'
    $dem = Invoke-Dem -Dataset $dataset -Rows $controls
    $demResults[$dataset] = $dem
    if ($dem.reachable) {
      for ($i = 0; $i -lt $controls.Count; $i++) {
        Add-Operation -Type 'regional_control_sample' -Status 'sampled' -StageNo $stageNo -StageName $currentStage -ParcelId $controls[$i].control_id -NumericValue ([double]$dem.elevations[$i]) -Unit 'm' -SourceName "Open Topo Data / $dataset" -SourceUrl $datasetUrls[$dataset] -EvidencePath $sourceRel
      }
      Complete-Stage -StageNo $stageNo -Name $currentStage -Status 'completed'
    } else {
      Add-Operation -Type 'regional_control_sample' -Status 'blocked_or_unavailable' -StageNo $stageNo -StageName $currentStage -SourceName "Open Topo Data / $dataset" -SourceUrl $datasetUrls[$dataset] -EvidencePath $sourceRel -Blocker $dem.error
      Complete-Stage -StageNo $stageNo -Name $currentStage -Status 'blocked_or_unavailable'
    }
  }

  $officialChecks = @(
    (Test-Source -Name 'Copernicus Data Space OData catalogue' -Url 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$top=1'),
    (Test-Source -Name 'Environment Agency LiDAR survey download' -Url 'https://environment.data.gov.uk/DefraDataDownload/?Mode=survey'),
    (Test-Source -Name 'Ordnance Survey Terrain 50 open download' -Url 'https://osdatahub.os.uk/downloads/open/Terrain50')
  )
  Write-Json (Join-Path $repoRoot ($sourceRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    batch_id = $batchId
    generated_at = Now-Utc
    control_design = $controls
    datasets = $demResults
    official_source_checks = $officialChecks
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })

  $controlResults = @()
  for ($i = 0; $i -lt $controls.Count; $i++) {
    $named = [ordered]@{}
    foreach ($dataset in $datasets) {
      if ($demResults[$dataset].reachable) { $named[$dataset] = [double]$demResults[$dataset].elevations[$i] }
    }
    $values = @($named.Values | ForEach-Object { [double]$_ })
    if ($values.Count -lt 2) { throw "TOPOGRAPHY_160_CONTROL_REQUIRES_TWO_SOURCES_$($controls[$i].control_id)" }
    $median = [math]::Round([double](Get-Median $values), 2)
    $minimum = [double](($values | Measure-Object -Minimum).Minimum)
    $maximum = [double](($values | Measure-Object -Maximum).Maximum)
    $spread = [math]::Round($maximum - $minimum, 2)
    $controlResult = [pscustomobject][ordered]@{
      control_id = $controls[$i].control_id
      lat = $controls[$i].lat
      lon = $controls[$i].lon
      source_count = $values.Count
      consensus_median_m = $median
      source_spread_m = $spread
      consensus_status = if ($spread -le 8) { 'MODERATE_OR_HIGH_CONSISTENCY' } else { 'WIDE_SPREAD_MANUAL_REVIEW' }
      source_values = $named
      final_ready = $false
      fake_data = $false
    }
    $controlResults += $controlResult
    Add-Operation -Type 'regional_control_consensus' -Status 'calculated' -StageNo 6 -StageName 'regional_control_consensus' -ParcelId $controlResult.control_id -NumericValue $median -Unit 'm' -EvidencePath $controlRel
  }
  Complete-Stage -StageNo 6 -Name 'regional_control_consensus'

  $medians = @($controlResults | ForEach-Object { [double]$_.consensus_median_m })
  if ($medians.Count -ne 8) { throw "TOPOGRAPHY_160_EXPECTED_8_CONTROLS_GOT_$($medians.Count)" }
  $regionalAverage = [math]::Round([double](($medians | Measure-Object -Average).Average), 2)
  $regionalMedian = [math]::Round([double](Get-Median $medians), 2)
  Add-Operation -Type 'regional_average_calculation' -Status 'calculated' -StageNo 7 -StageName 'regional_average' -NumericValue $regionalAverage -Unit 'm' -EvidencePath $controlRel
  Write-Json (Join-Path $repoRoot ($controlRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    batch_id = $batchId
    generated_at = Now-Utc
    control_count = 8
    regional_average_elevation_m = $regionalAverage
    regional_median_elevation_m = $regionalMedian
    method = 'arithmetic mean of 8 control-point multi-DEM medians'
    rows = $controlResults
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($controlCsvRel -replace '/', '\')))
  $controlResults | Export-Csv -LiteralPath (Join-Path $repoRoot ($controlCsvRel -replace '/', '\')) -NoTypeInformation -Encoding UTF8
  Complete-Stage -StageNo 7 -Name 'regional_average_calculation'

  foreach ($row in $parcelRows) {
    $parcelElevation = if ($null -ne $row.elevation_consensus_median_m) { [double]$row.elevation_consensus_median_m } else { [double]$row.elevation_sea_level_m }
    $difference = [math]::Round($parcelElevation - $regionalAverage, 2)
    Set-Prop $row 'regional_average_elevation_m' $regionalAverage
    Set-Prop $row 'regional_median_elevation_m' $regionalMedian
    Set-Prop $row 'regional_control_count' 8
    Set-Prop $row 'regional_control_radius_m' $radiusM
    Set-Prop $row 'regional_average_evidence_path' $controlRel
    Set-Prop $row 'elevation_difference_regional_average_m' $difference
    Set-Prop $row 'display_badge' 'REGIONAL_CONTROL_8POINT_MULTI_DEM_READY'
    Set-Prop $row 'sampling_status' 'parcel_consensus_and_8_control_regional_average_ready'
    Set-Prop $row 'task_id' $taskId
    Set-Prop $row 'updated_at' (Now-Utc)
    Set-Prop $row 'report_path' $reportRel
    Set-Prop $row 'status_path' $statusRel
    Set-Prop $row 'accuracy_score_4' '2.5/4 fallback; regional controls complete, primary CopDEM/boundary/official numeric validation pending'
    Set-Prop $row 'blocker' 'real_parcel_boundary_required; primary_copdem_glo30_raster_sampling_required; ea_lidar_or_os_terrain_numeric_validation_required'
    Add-Operation -Type 'parcel_height_difference' -Status 'calculated' -StageNo 8 -StageName 'parcel_height_difference' -ParcelId ([string]$row.parcel_id) -NumericValue $difference -Unit 'm' -EvidencePath $controlRel
  }
  Set-Prop $visible 'status' 'REGIONAL_CONTROL_8POINT_VISIBLE_PRIMARY_VALIDATION_PENDING'
  Set-Prop $visible 'latest_task_id' $taskId
  Set-Prop $visible 'latest_batch_id' $batchId
  Set-Prop $visible 'updated_at' (Now-Utc)
  Set-Prop $visible 'rows' $parcelRows
  Set-Prop $visible 'final_ready' $false
  Set-Prop $visible 'fake_data' $false
  Write-Json $visibleRowsPath $visible

  foreach ($check in $officialChecks) {
    Add-Operation -Type 'official_source_check_only' -Status (if ($check.reachable) { 'source_check_only_available' } else { 'blocked_or_unavailable' }) -StageNo 8 -StageName 'official_source_checks' -SourceName $check.name -SourceUrl $check.url -EvidencePath $sourceRel -Blocker (if ($check.reachable) { '' } else { $check.error })
  }
  Complete-Stage -StageNo 8 -Name 'parcel_update_official_checks_and_site_publish'

  $availableDemCount = @($datasets | Where-Object { $demResults[$_].reachable }).Count
  $completionPercent = if ($availableDemCount -eq 4) { 70 } elseif ($availableDemCount -eq 3) { 68 } else { 65 }
  $statusPayload = [ordered]@{
    task_id = $taskId
    page_key = 'topography'
    batch_id = $batchId
    previous_batch_id = $previousBatchId
    status = 'REGIONAL_CONTROL_8POINT_VISIBLE_PRIMARY_VALIDATION_PENDING'
    started_at = $startedAt
    completed_at = Now-Utc
    stages = $stageRows
    completed_stage_count = 8
    total_stage_count = 8
    candidate_rows = $parcelRows.Count
    regional_control_rows = $controlResults.Count
    available_dem_sources = $availableDemCount
    regional_average_elevation_m = $regionalAverage
    regional_median_elevation_m = $regionalMedian
    height_difference_value_count = $parcelRows.Count
    official_sources_checked = $officialChecks.Count
    official_sources_reachable = @($officialChecks | Where-Object { $_.reachable }).Count
    new_operation_rows = $operations.Count
    completion_percent = $completionPercent
    percent_increase = ($completionPercent - 60)
    accuracy_score_4 = '2.5/4 fallback'
    blockers = @('real_parcel_boundary_required', 'primary_copdem_glo30_raster_sampling_required', 'ea_lidar_or_os_terrain_numeric_validation_required')
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $statusPayload
  Write-Json (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\')) $statusPayload
  Write-Json (Join-Path $repoRoot ($latestChangesRel -replace '/', '\')) ([ordered]@{ layer = 'Topography'; task_id = $taskId; updated_at = Now-Utc; summary = $statusPayload; rows = $parcelRows; final_ready = $false; fake_data = $false })

  Publish-Ledger -RunStatus 'COMPLETED_VISIBLE_NOT_FINAL'

  if ($env:AAYS_CONTROLLER_REPO_ROOT) {
    $publisher = Join-Path $repoRoot 'docs/chatgpt_status/_shared/automation/PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1'
    $publishPaths = @($visibleRowsRel, $visibleStatusRel, $operationsRel, $sourceRel, $controlRel, $controlCsvRel) -join '|'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $repoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths $publishPaths -AllowGeneratedArtifacts -SyncPortableWeb
    if ($LASTEXITCODE -ne 0) { throw 'TOPOGRAPHY_160_LIVE_CONTROLLER_PUBLISH_BLOCKED' }
  }

  $siteRows = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json' -TimeoutSec 30
  $siteOps = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_operations_latest.json' -TimeoutSec 30
  if ($siteRows.StatusCode -ne 200 -or $siteOps.StatusCode -ne 200) { throw 'TOPOGRAPHY_160_SITE_HTTP_VALIDATION_FAILED' }

  $report = "# Topography 160 Regional Control Expansion`n`n- Task: $taskId`n- Regional controls: 8`n- DEM sources available: $availableDemCount/4`n- Regional average: $regionalAverage m`n- Regional median: $regionalMedian m`n- Height-difference rows: $($parcelRows.Count)`n- New operation rows: $($operations.Count)`n- Site HTTP validation: PASS`n- Completion: $completionPercent%`n- Increase: +$($completionPercent - 60)%`n- Accuracy: 2.5/4 fallback`n- final_ready: false`n"
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($reportRel -replace '/', '\')))
  [System.IO.File]::WriteAllText((Join-Path $repoRoot ($reportRel -replace '/', '\')), $report, [System.Text.UTF8Encoding]::new($false))
  Write-Json (Join-Path $repoRoot ($outputRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    status = 'COMPLETED_VISIBLE_NOT_FINAL'
    completed_at = Now-Utc
    completion_percent = $completionPercent
    percent_increase = ($completionPercent - 60)
    completed_stage_count = 8
    total_stage_count = 8
    candidate_rows = $parcelRows.Count
    regional_control_rows = $controlResults.Count
    height_difference_value_count = $parcelRows.Count
    new_operation_rows = $operations.Count
    site_http_validation = 'PASS'
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })
} catch {
  $errorMessage = $_.Exception.Message
  Add-Operation -Type 'runner_failure' -Status 'blocked' -StageNo ([math]::Max(1, $completedStages + 1)) -StageName $currentStage -EvidencePath $statusRel -Blocker $errorMessage
  Publish-Ledger -RunStatus 'BLOCKED'
  Write-Json (Join-Path $repoRoot ($outputRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    status = 'BLOCKED'
    blocker = $errorMessage
    completed_stage_count = $completedStages
    total_stage_count = $stageCount
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })
  throw
}

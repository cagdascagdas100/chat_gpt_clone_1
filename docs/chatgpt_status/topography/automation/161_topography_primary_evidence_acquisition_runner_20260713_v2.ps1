[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Now-Utc {
  return (Get-Date).ToUniversalTime().ToString('o')
}

function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Write-JsonAtomic([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  $tempPath = "$Path.tmp"
  [System.IO.File]::WriteAllText(
    $tempPath,
    (($Value | ConvertTo-Json -Depth 90) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
  Move-Item -LiteralPath $tempPath -Destination $Path -Force
}

function Read-Json([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Set-Prop([object]$Object, [string]$Name, [object]$Value) {
  Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force
}

function Test-OfficialSource([string]$Name, [string]$Url) {
  $result = [ordered]@{
    name = $Name
    url = $Url
    reachable = $false
    status_code = $null
    final_url = $null
    error = $null
  }
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -MaximumRedirection 10 -TimeoutSec 120 -Headers @{ 'User-Agent' = 'TerraYield-AAYS-Topography/1.0 primary-evidence-v2' }
    $result.status_code = [int]$response.StatusCode
    $result.reachable = ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400)
    try { $result.final_url = [string]$response.BaseResponse.ResponseUri.AbsoluteUri } catch {}
  } catch {
    try { $result.status_code = [int]$_.Exception.Response.StatusCode.value__ } catch {}
    $result.error = $_.Exception.Message
  }
  return [pscustomobject]$result
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or $repoRoot -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]') {
  throw 'TOPOGRAPHY_161_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'aays1-161-topography-primary-evidence-acquisition-20260713' }
$startedAt = Now-Utc
$batchId = 'topography-161-v2-' + ($startedAt -replace '[^0-9]', '')
$previousBatchId = 'aays1-160-topography-regional-control-expansion-20260713'
$completedStages = 0
$currentStage = 'task_start'
$stageTotal = 8
$operations = @()
$stageRows = @()

$visibleRowsRel = 'england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$operationsRel = 'england_map_web/data/program_layer_matrix/topography_operations_latest.json'
$sourceRel = 'docs/chatgpt_status/topography/source_snapshots/161_primary_evidence_sources_latest.json'
$inventoryRel = 'docs/chatgpt_status/topography/source_snapshots/161_boundary_artifact_inventory_latest.json'
$boundaryRel = 'docs/chatgpt_status/topography/fixtures/topography_real_boundary_candidates_20260713.json'
$statusRel = 'docs/chatgpt_status/topography/status/161_topography_primary_evidence_acquisition_latest.json'
$reportRel = 'docs/chatgpt_status/topography/reports/161_topography_primary_evidence_acquisition_report_20260713.md'
$outputRel = 'docs/chatgpt_status/topography/runner_outputs/161_topography_primary_evidence_acquisition_batch.json'
$latestChangesRel = 'outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'

function Add-Operation {
  param(
    [string]$Type,
    [string]$Status,
    [int]$StageNo,
    [string]$StageName,
    [string]$ParcelId = '',
    [string]$SourceName = '',
    [string]$SourceUrl = '',
    [string]$RequestUrl = '',
    [object]$NumericValue = $null,
    [string]$Unit = '',
    [string]$EvidencePath = '',
    [string]$Blocker = ''
  )

  $method = $null
  if ($Type -match 'boundary') { $method = 'parcel-reference property match with non-null Polygon or MultiPolygon geometry' }
  elseif ($Type -match 'source_check') { $method = 'official source HTTP reachability check only' }
  elseif ($Type -match 'catalogue') { $method = 'official Copernicus Data Space OData metadata query' }
  elseif ($Type -match 'inventory') { $method = 'bounded canonical F repository and configured data-root inventory' }

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
    request_url = if ($RequestUrl) { $RequestUrl } else { $null }
    numeric_value = $NumericValue
    unit = if ($Unit) { $Unit } else { $null }
    method = $method
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
  $ledgerPath = Join-Path $repoRoot ($operationsRel -replace '/', '\')
  $oldLedger = Read-Json $ledgerPath
  $existing = @()
  if ($oldLedger) {
    $existing = @($oldLedger.operations)
    foreach ($operation in $existing) {
      if ($null -ne $operation) {
        Set-Prop $operation 'is_new_operation' $false
        Set-Prop $operation 'is_new_in_latest_batch' $false
      }
    }
  }

  $allOperations = @($existing + $operations)
  $blockedOperations = @($allOperations | Where-Object { [string]$_.status -match 'blocked|failed|unavailable|auth_required|not_found|partial' })
  $payload = [ordered]@{
    task_id = $taskId
    batch_id = $batchId
    previous_batch_id = $previousBatchId
    updated_at = Now-Utc
    run_status = $RunStatus
    current_stage = $currentStage
    stage_completed_count = $completedStages
    stage_total_count = $stageTotal
    operation_count = $allOperations.Count
    new_operations_count = $operations.Count
    blocked_operation_count = $blockedOperations.Count
    last_blocked_operation = if ($blockedOperations.Count -gt 0) { $blockedOperations[-1] } else { $null }
    operations = $allOperations
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  Write-JsonAtomic $ledgerPath $payload
}

function Complete-Stage([int]$StageNo, [string]$Name, [string]$Status = 'completed') {
  $script:completedStages = $StageNo
  $script:currentStage = $Name
  $script:stageRows += [pscustomobject][ordered]@{
    stage_no = $StageNo
    stage = $Name
    status = $Status
    completed_at = Now-Utc
  }
  Add-Operation -Type 'pipeline_stage' -Status $Status -StageNo $StageNo -StageName $Name -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'
}

function Publish-LiveArtifacts {
  if (-not $env:AAYS_CONTROLLER_REPO_ROOT) { return }
  $publisher = Join-Path $repoRoot 'docs/chatgpt_status/_shared/automation/PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1'
  if (-not (Test-Path -LiteralPath $publisher)) { throw 'TOPOGRAPHY_161_LIVE_PUBLISHER_MISSING' }
  $paths = @($visibleRowsRel, $visibleStatusRel, $operationsRel, $sourceRel, $inventoryRel, $boundaryRel) -join '|'
  & powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $repoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths $paths -AllowGeneratedArtifacts -SyncPortableWeb
  if ($LASTEXITCODE -ne 0) { throw 'TOPOGRAPHY_161_LIVE_CONTROLLER_PUBLISH_BLOCKED' }
}

try {
  Add-Operation -Type 'task_start' -Status 'running' -StageNo 1 -StageName 'task_start' -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'

  $visibleRowsPath = Join-Path $repoRoot ($visibleRowsRel -replace '/', '\')
  $visible = Read-Json $visibleRowsPath
  $parcelRows = @($visible.rows)
  if ($null -eq $visible -or $parcelRows.Count -lt 3) { throw 'TOPOGRAPHY_161_VISIBLE_ROWS_NOT_READY' }
  Complete-Stage -StageNo 1 -Name 'load_verified_parcel_rows'

  $sourceChecks = @(
    (Test-OfficialSource -Name 'HM Land Registry INSPIRE guidance' -Url 'https://www.gov.uk/guidance/inspire-index-polygons-spatial-data'),
    (Test-OfficialSource -Name 'HM Land Registry INSPIRE data service' -Url 'https://use-land-property-data.service.gov.uk/datasets/inspire'),
    (Test-OfficialSource -Name 'Environment Agency LiDAR survey download' -Url 'https://environment.data.gov.uk/survey'),
    (Test-OfficialSource -Name 'Ordnance Survey Terrain 50 open download' -Url 'https://osdatahub.os.uk/downloads/open/Terrain50')
  )
  foreach ($sourceCheck in $sourceChecks) {
    $sourceStatus = 'blocked_or_unavailable'
    $sourceBlocker = [string]$sourceCheck.error
    if ($sourceCheck.reachable) {
      $sourceStatus = 'source_check_only_available'
      $sourceBlocker = ''
    }
    Add-Operation -Type 'official_source_check_only' -Status $sourceStatus -StageNo 2 -StageName 'official_source_checks' -SourceName ([string]$sourceCheck.name) -SourceUrl ([string]$sourceCheck.url) -RequestUrl ([string]$sourceCheck.final_url) -EvidencePath $sourceRel -Blocker $sourceBlocker
  }
  $reachableOfficialCount = @($sourceChecks | Where-Object { $_.reachable }).Count
  $officialStageStatus = if ($reachableOfficialCount -ge 3) { 'completed' } else { 'partial' }
  Complete-Stage -StageNo 2 -Name 'official_source_checks' -Status $officialStageStatus

  $inventory = @()
  $inventoryRoots = @(
    (Join-Path $repoRoot 'england_map_web\data'),
    (Join-Path $repoRoot 'docs\chatgpt_status'),
    (Join-Path $repoRoot 'outputs')
  ) | Where-Object { Test-Path -LiteralPath $_ }

  foreach ($inventoryRoot in $inventoryRoots) {
    $rootItems = @(Get-ChildItem -LiteralPath $inventoryRoot -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Extension -match '(?i)^\.(geojson|json|gml|xml|gpkg|shp|zip)$' -and
        $_.FullName -match '(?i)inspire|hmlr|boundary|parcel'
      } |
      Select-Object -First 250)
    foreach ($item in $rootItems) {
      $relativePath = $item.FullName.Substring($repoRoot.Length).TrimStart('\') -replace '\\', '/'
      $inventory += [pscustomobject][ordered]@{
        path = $relativePath
        extension = $item.Extension
        size_bytes = $item.Length
        last_write_utc = $item.LastWriteTimeUtc.ToString('o')
      }
    }
  }

  $boundaryMatches = @()
  $jsonCandidates = @($inventory | Where-Object {
    $_.extension -match '(?i)^\.(geojson|json)$' -and [int64]$_.size_bytes -lt 52428800
  })
  foreach ($candidate in $jsonCandidates) {
    try {
      $candidateData = Read-Json (Join-Path $repoRoot ($candidate.path -replace '/', '\'))
      $features = @($candidateData.features)
      foreach ($parcelRow in $parcelRows) {
        foreach ($feature in $features) {
          $geometryType = [string]$feature.geometry.type
          if ($feature.geometry -and $geometryType -match 'Polygon') {
            $propertiesText = ($feature.properties | ConvertTo-Json -Depth 20 -Compress)
            if ($propertiesText -match [regex]::Escape([string]$parcelRow.parcel_ref)) {
              $boundaryMatches += [pscustomobject][ordered]@{
                parcel_id = $parcelRow.parcel_id
                parcel_ref = $parcelRow.parcel_ref
                source_path = $candidate.path
                geometry = $feature.geometry
                properties = $feature.properties
                match_method = 'parcel_ref_property_match_with_non_null_polygon_geometry'
              }
              break
            }
          }
        }
      }
    } catch {}
  }
  $boundaryMatches = @($boundaryMatches | Group-Object parcel_id | ForEach-Object { $_.Group | Select-Object -First 1 })

  Write-JsonAtomic (Join-Path $repoRoot ($inventoryRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    generated_at = Now-Utc
    candidate_count = $inventory.Count
    candidates = $inventory
    final_ready = $false
    fake_data = $false
  })
  Write-JsonAtomic (Join-Path $repoRoot ($boundaryRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    generated_at = Now-Utc
    real_boundary_rows = $boundaryMatches.Count
    rows = $boundaryMatches
    final_ready = $false
    fake_data = $false
  })

  Add-Operation -Type 'boundary_artifact_inventory' -Status 'completed' -StageNo 3 -StageName 'boundary_inventory' -SourceName 'canonical F repository' -NumericValue $inventory.Count -Unit 'candidate files' -EvidencePath $inventoryRel
  foreach ($boundaryMatch in $boundaryMatches) {
    Add-Operation -Type 'real_boundary_match' -Status 'validated' -StageNo 3 -StageName 'boundary_inventory' -ParcelId ([string]$boundaryMatch.parcel_id) -SourceName 'local boundary artifact' -EvidencePath $boundaryRel
  }
  $boundaryStageStatus = if ($boundaryMatches.Count -eq 3) { 'completed' } else { 'partial' }
  Complete-Stage -StageNo 3 -Name 'boundary_artifact_inventory_and_match' -Status $boundaryStageStatus

  $catalogueBase = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
  $filterText = "contains(Name,'N51_00_W001') or contains(Name,'N51_W001')"
  $catalogueQuery = $catalogueBase + '?$filter=' + [uri]::EscapeDataString($filterText) + '&$top=100&$expand=Attributes'
  $catalogue = [ordered]@{
    url = $catalogueQuery
    reachable = $false
    result_count = 0
    matching_products = @()
    error = $null
  }
  try {
    $catalogueResponse = Invoke-RestMethod -Method Get -Uri $catalogueQuery -TimeoutSec 180 -Headers @{ 'User-Agent' = 'TerraYield-AAYS-Topography/1.0 CopDEM-primary-v2' }
    $catalogueProducts = @($catalogueResponse.value)
    $catalogue.reachable = $true
    $catalogue.result_count = $catalogueProducts.Count
    $catalogue.matching_products = @($catalogueProducts | Select-Object -First 20 Id, Name, ContentDate, PublicationDate, Footprint, Attributes)
  } catch {
    $catalogue.error = $_.Exception.Message
  }

  $catalogueStatus = if ($catalogue.reachable) { 'completed' } else { 'blocked_or_unavailable' }
  $catalogueBlocker = if ($catalogue.reachable) { '' } else { [string]$catalogue.error }
  Add-Operation -Type 'copernicus_catalogue_query' -Status $catalogueStatus -StageNo 4 -StageName 'copdem_catalogue' -SourceName 'Copernicus Data Space OData' -SourceUrl $catalogueBase -RequestUrl $catalogueQuery -NumericValue @($catalogue.matching_products).Count -Unit 'matching products' -EvidencePath $sourceRel -Blocker $catalogueBlocker
  Complete-Stage -StageNo 4 -Name 'copdem_catalogue_query' -Status $catalogueStatus

  $token = $null
  if ($env:CDSE_ACCESS_TOKEN) { $token = [string]$env:CDSE_ACCESS_TOKEN }
  elseif ($env:COPERNICUS_ACCESS_TOKEN) { $token = [string]$env:COPERNICUS_ACCESS_TOKEN }

  $firstProduct = @($catalogue.matching_products | Select-Object -First 1)
  $productFound = ($firstProduct.Count -gt 0)
  $downloadUrl = $null
  if ($productFound) { $downloadUrl = "https://download.dataspace.copernicus.eu/odata/v1/Products($($firstProduct[0].Id))/`$value" }

  $gateStatus = 'product_not_found'
  $gateBlocker = 'COPDEM_MATCHING_PRODUCT_NOT_FOUND'
  if ($productFound -and -not $token) {
    $gateStatus = 'auth_required'
    $gateBlocker = 'CDSE_ACCESS_TOKEN_NOT_AVAILABLE'
  } elseif ($productFound -and $token) {
    $gateStatus = 'download_ready'
    $gateBlocker = ''
  }
  $downloadGate = [ordered]@{
    token_configured = [bool]$token
    product_found = $productFound
    product_id = if ($productFound) { [string]$firstProduct[0].Id } else { $null }
    product_name = if ($productFound) { [string]$firstProduct[0].Name } else { $null }
    download_url = $downloadUrl
    status = $gateStatus
  }
  Add-Operation -Type 'primary_copdem_download_gate' -Status $gateStatus -StageNo 5 -StageName 'copdem_download_gate' -SourceName 'Copernicus DEM GLO-30' -SourceUrl $catalogueBase -RequestUrl $downloadUrl -EvidencePath $sourceRel -Blocker $gateBlocker
  Complete-Stage -StageNo 5 -Name 'primary_copdem_download_gate' -Status $gateStatus

  $localRasters = @()
  $configuredRoots = @(
    $env:AAYS_DATA_ROOT,
    $env:EA_LIDAR_ROOT,
    $env:OS_TERRAIN_ROOT,
    (Join-Path $repoRoot 'docs\chatgpt_status\topography\source_snapshots')
  ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

  foreach ($configuredRoot in $configuredRoots) {
    $rasterItems = @(Get-ChildItem -LiteralPath $configuredRoot -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Extension -match '(?i)^\.(tif|tiff|asc)$' -and
        $_.FullName -match '(?i)cop.?dem|lidar|terrain.?50|dtm'
      } |
      Select-Object -First 50)
    foreach ($rasterItem in $rasterItems) {
      $localRasters += [pscustomobject][ordered]@{
        path = $rasterItem.FullName
        extension = $rasterItem.Extension
        size_bytes = $rasterItem.Length
        last_write_utc = $rasterItem.LastWriteTimeUtc.ToString('o')
      }
    }
  }
  $localRasters = @($localRasters | Sort-Object path -Unique)
  Add-Operation -Type 'primary_raster_inventory' -Status 'completed' -StageNo 6 -StageName 'primary_raster_inventory' -SourceName 'canonical configured storage' -NumericValue $localRasters.Count -Unit 'raster files' -EvidencePath $sourceRel
  Complete-Stage -StageNo 6 -Name 'primary_raster_inventory'

  Write-JsonAtomic (Join-Path $repoRoot ($sourceRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    batch_id = $batchId
    generated_at = Now-Utc
    official_source_checks = $sourceChecks
    boundary_inventory_count = $inventory.Count
    real_boundary_rows = $boundaryMatches.Count
    copernicus_catalogue = $catalogue
    copdem_download_gate = $downloadGate
    local_primary_rasters = $localRasters
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })

  $realBoundaryCount = $boundaryMatches.Count
  $productCount = @($catalogue.matching_products).Count
  $completionPercent = 70
  if ($realBoundaryCount -eq 3 -and $productCount -gt 0) { $completionPercent = 74 }
  elseif ($realBoundaryCount -eq 3 -or $productCount -gt 0) { $completionPercent = 72 }

  $blockers = @()
  if ($realBoundaryCount -lt 3) { $blockers += 'real_parcel_boundary_required' }
  $blockers += 'primary_copdem_glo30_raster_sampling_required'
  $blockers += 'ea_lidar_or_os_terrain_numeric_validation_required'

  foreach ($parcelRow in $parcelRows) {
    $hasBoundary = (@($boundaryMatches | Where-Object { $_.parcel_id -eq $parcelRow.parcel_id }).Count -gt 0)
    Set-Prop $parcelRow 'real_boundary_validated' $hasBoundary
    Set-Prop $parcelRow 'real_boundary_evidence_path' $boundaryRel
    Set-Prop $parcelRow 'copdem_product_candidates' $productCount
    Set-Prop $parcelRow 'copdem_download_gate_status' $gateStatus
    Set-Prop $parcelRow 'task_id' $taskId
    Set-Prop $parcelRow 'updated_at' (Now-Utc)
    Set-Prop $parcelRow 'report_path' $reportRel
    Set-Prop $parcelRow 'status_path' $statusRel
    Set-Prop $parcelRow 'display_badge' 'PRIMARY_EVIDENCE_DISCOVERY_READY'
    Set-Prop $parcelRow 'accuracy_score_4' '2.5/4 fallback; numeric primary validation pending'
    Set-Prop $parcelRow 'blocker' ($blockers -join '; ')
  }
  Set-Prop $visible 'status' 'PRIMARY_EVIDENCE_DISCOVERY_VISIBLE_NOT_FINAL'
  Set-Prop $visible 'latest_task_id' $taskId
  Set-Prop $visible 'latest_batch_id' $batchId
  Set-Prop $visible 'updated_at' (Now-Utc)
  Set-Prop $visible 'rows' $parcelRows
  Set-Prop $visible 'final_ready' $false
  Set-Prop $visible 'fake_data' $false
  Write-JsonAtomic $visibleRowsPath $visible

  $statusPayload = [ordered]@{
    task_id = $taskId
    page_key = 'topography'
    batch_id = $batchId
    previous_batch_id = $previousBatchId
    status = 'PRIMARY_EVIDENCE_DISCOVERY_VISIBLE_NOT_FINAL'
    started_at = $startedAt
    completed_at = $null
    stages = $stageRows
    completed_stage_count = 7
    total_stage_count = 8
    candidate_rows = $parcelRows.Count
    official_sources_checked = $sourceChecks.Count
    official_sources_reachable = $reachableOfficialCount
    boundary_inventory_candidates = $inventory.Count
    real_boundary_rows = $realBoundaryCount
    copernicus_products_found = $productCount
    local_primary_raster_candidates = $localRasters.Count
    completion_percent = $completionPercent
    percent_increase = ($completionPercent - 70)
    accuracy_score_4 = '2.5/4 fallback'
    blockers = $blockers
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  Write-JsonAtomic (Join-Path $repoRoot ($statusRel -replace '/', '\')) $statusPayload
  Write-JsonAtomic (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\')) $statusPayload
  Write-JsonAtomic (Join-Path $repoRoot ($latestChangesRel -replace '/', '\')) ([ordered]@{
    layer = 'Topography'
    task_id = $taskId
    updated_at = Now-Utc
    summary = $statusPayload
    rows = $parcelRows
    final_ready = $false
    fake_data = $false
  })
  Complete-Stage -StageNo 7 -Name 'site_publication'
  Publish-LiveArtifacts

  $servedRowsResponse = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json' -TimeoutSec 30
  $servedOperationsResponse = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_operations_latest.json' -TimeoutSec 30
  if ($servedRowsResponse.StatusCode -ne 200 -or $servedOperationsResponse.StatusCode -ne 200) { throw 'TOPOGRAPHY_161_SITE_HTTP_READBACK_FAILED' }
  $servedRows = $servedRowsResponse.Content | ConvertFrom-Json
  $servedOperations = $servedOperationsResponse.Content | ConvertFrom-Json
  if ([string]$servedRows.latest_task_id -ne $taskId) { throw 'TOPOGRAPHY_161_SITE_ROWS_TASK_ID_MISMATCH' }
  if ([string]$servedOperations.task_id -ne $taskId) { throw 'TOPOGRAPHY_161_SITE_OPERATIONS_TASK_ID_MISMATCH' }

  Complete-Stage -StageNo 8 -Name 'http_readback' -Status 'PASS'

  $statusPayload.completed_at = Now-Utc
  $statusPayload.stages = $stageRows
  $statusPayload.completed_stage_count = 8
  Write-JsonAtomic (Join-Path $repoRoot ($statusRel -replace '/', '\')) $statusPayload
  Write-JsonAtomic (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\')) $statusPayload

  $reportText = @"
# Topography 161 Primary Evidence Acquisition

- Task: $taskId
- Official sources reachable: $reachableOfficialCount/4
- Boundary inventory candidates: $($inventory.Count)
- Real boundary rows: $realBoundaryCount/3
- Copernicus product matches: $productCount
- CopDEM download gate: $gateStatus
- Local primary raster candidates: $($localRasters.Count)
- New operation rows: $($operations.Count)
- Site HTTP readback: PASS
- Completion: $completionPercent%
- Increase: +$($completionPercent - 70)%
- Accuracy: 2.5/4 fallback
- final_ready: false
"@
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($reportRel -replace '/', '\')))
  [System.IO.File]::WriteAllText((Join-Path $repoRoot ($reportRel -replace '/', '\')), $reportText, [System.Text.UTF8Encoding]::new($false))

  Write-JsonAtomic (Join-Path $repoRoot ($outputRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    status = 'COMPLETED_VISIBLE_NOT_FINAL'
    completed_at = Now-Utc
    completion_percent = $completionPercent
    percent_increase = ($completionPercent - 70)
    completed_stage_count = 8
    total_stage_count = 8
    candidate_rows = $parcelRows.Count
    official_sources_reachable = $reachableOfficialCount
    boundary_inventory_candidates = $inventory.Count
    real_boundary_rows = $realBoundaryCount
    copernicus_products_found = $productCount
    copdem_download_gate_status = $gateStatus
    local_primary_raster_candidates = $localRasters.Count
    new_operation_rows = $operations.Count
    site_http_validation = 'PASS'
    blockers = $blockers
    accuracy_score_4 = '2.5/4 fallback'
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })

  Publish-Ledger -RunStatus 'COMPLETED_VISIBLE_NOT_FINAL'
  Publish-LiveArtifacts
} catch {
  $errorMessage = $_.Exception.Message
  Add-Operation -Type 'runner_failure' -Status 'blocked' -StageNo ([math]::Max(1, $completedStages + 1)) -StageName $currentStage -EvidencePath $statusRel -Blocker $errorMessage
  Publish-Ledger -RunStatus 'BLOCKED'

  $blockedPayload = [ordered]@{
    task_id = $taskId
    page_key = 'topography'
    batch_id = $batchId
    status = 'BLOCKED'
    error = $errorMessage
    current_stage = $currentStage
    completed_stage_count = $completedStages
    total_stage_count = $stageTotal
    stages = $stageRows
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  Write-JsonAtomic (Join-Path $repoRoot ($statusRel -replace '/', '\')) $blockedPayload
  Write-JsonAtomic (Join-Path $repoRoot ($outputRel -replace '/', '\')) $blockedPayload
  throw
}

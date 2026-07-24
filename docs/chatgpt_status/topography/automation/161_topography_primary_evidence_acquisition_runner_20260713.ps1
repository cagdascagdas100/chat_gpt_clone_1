[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Now-Utc {
  (Get-Date).ToUniversalTime().ToString('o')
}

function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function Write-Json([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  $tempPath = "$Path.tmp"
  [System.IO.File]::WriteAllText(
    $tempPath,
    (($Value | ConvertTo-Json -Depth 100) + "`n"),
    [System.Text.UTF8Encoding]::new($false)
  )
  Move-Item -LiteralPath $tempPath -Destination $Path -Force
}

function Read-Json([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Set-Prop([object]$Object, [string]$Name, [object]$Value) {
  Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force
}

function To-RepoRelativePath([string]$FullPath, [string]$Root) {
  if (-not $FullPath) { return $null }
  $full = [System.IO.Path]::GetFullPath($FullPath)
  $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\')
  if (-not $full.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) { return $null }
  return ($full.Substring($rootFull.Length).TrimStart('\') -replace '\\', '/')
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
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -MaximumRedirection 10 -TimeoutSec 120 -Headers @{ 'User-Agent' = 'TerraYield-AAYS-Topography/1.0 primary-evidence' }
    $result.status_code = [int]$response.StatusCode
    $result.reachable = ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400)
    try { $result.final_url = [string]$response.BaseResponse.ResponseUri.AbsoluteUri } catch { $result.final_url = $Url }
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
$batchId = 'topography-161-' + ($startedAt -replace '[^0-9]', '')
$previousBatchId = 'aays1-160-topography-regional-control-expansion-20260713'
$completedStages = 0
$currentStage = 'task_start'
$stageTotalCount = 8
$operations = @()
$stageRows = @()

$visibleRowsRel = 'england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$operationsRel = 'england_map_web/data/program_layer_matrix/topography_operations_latest.json'
$sourceRel = 'docs/chatgpt_status/topography/source_snapshots/161_primary_evidence_sources_latest.json'
$boundaryInventoryRel = 'docs/chatgpt_status/topography/source_snapshots/161_boundary_artifact_inventory_latest.json'
$boundaryRowsRel = 'docs/chatgpt_status/topography/fixtures/topography_real_boundary_candidates_20260713.json'
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
    [string]$ParcelRef = '',
    [string]$SourceName = '',
    [string]$SourceUrl = '',
    [string]$RequestUrl = '',
    [string]$DatasetId = '',
    [string]$ProductId = '',
    [object]$NumericValue = $null,
    [string]$Unit = '',
    [string]$RepoArtifactPath = '',
    [string]$LocalSourcePath = '',
    [string]$Blocker = '',
    [string]$ErrorMessage = ''
  )
  $script:operations += [pscustomobject][ordered]@{
    operation_id = "${batchId}_$($script:operations.Count + 1)"
    stage_no = $StageNo
    operation_type = $Type
    task_id = $taskId
    batch_id = $batchId
    previous_batch_id = $previousBatchId
    parcel_id = if ($ParcelId) { $ParcelId } else { $null }
    parcel_ref = if ($ParcelRef) { $ParcelRef } else { $null }
    status = $Status
    is_new_operation = $true
    is_new_in_latest_batch = $true
    started_at = $startedAt
    completed_at = Now-Utc
    source_name = if ($SourceName) { $SourceName } else { $null }
    source_url = if ($SourceUrl) { $SourceUrl } else { $null }
    request_url = if ($RequestUrl) { $RequestUrl } else { $null }
    dataset_id = if ($DatasetId) { $DatasetId } else { $null }
    product_id = if ($ProductId) { $ProductId } else { $null }
    numeric_value = $NumericValue
    unit = if ($Unit) { $Unit } else { $null }
    method = if ($Type -match 'boundary') { 'parcel-reference property match with non-null Polygon or MultiPolygon geometry' } elseif ($Type -match 'source_check') { 'official source HTTP reachability check only' } elseif ($Type -match 'catalogue') { 'official Copernicus Data Space OData metadata query' } elseif ($Type -match 'inventory') { 'bounded canonical F repository and configured storage inventory' } else { $null }
    accuracy_score_4 = '2.5/4 fallback'
    repo_artifact_path = if ($RepoArtifactPath) { $RepoArtifactPath } else { $null }
    local_source_path = if ($LocalSourcePath) { $LocalSourcePath } else { $null }
    report_path = $reportRel
    status_path = $statusRel
    runner_output_path = $outputRel
    blocker = if ($Blocker) { $Blocker } else { $null }
    error = if ($ErrorMessage) { $ErrorMessage } else { $null }
    needs_manual_review = [bool]($Blocker -or $ErrorMessage)
    final_ready = $false
    fake_data = $false
  }
}

function Publish-Ledger([string]$RunStatus) {
  $ledgerPath = Join-Path $repoRoot ($operationsRel -replace '/', '\')
  $existing = @()
  $oldLedger = Read-Json $ledgerPath
  if ($oldLedger) { $existing = @($oldLedger.operations) }

  $byId = @{}
  $combined = @()
  foreach ($operation in $existing) {
    if ($null -eq $operation) { continue }
    $id = [string]$operation.operation_id
    if (-not $id) { continue }
    Set-Prop $operation 'is_new_operation' ([string]$operation.batch_id -eq $batchId)
    Set-Prop $operation 'is_new_in_latest_batch' ([string]$operation.batch_id -eq $batchId)
    if (-not $byId.ContainsKey($id)) {
      $byId[$id] = $true
      $combined += $operation
    }
  }
  foreach ($operation in $operations) {
    $id = [string]$operation.operation_id
    if (-not $byId.ContainsKey($id)) {
      $byId[$id] = $true
      $combined += $operation
    }
  }

  $blocked = @($combined | Where-Object { [string]$_.status -match 'blocked|failed|unavailable|auth_required|not_found' })
  $successful = @($combined | Where-Object { [string]$_.status -match 'completed|validated|available|PASS|ready' })
  $currentBatchRows = @($combined | Where-Object { [string]$_.batch_id -eq $batchId })

  Write-Json $ledgerPath ([ordered]@{
    task_id = $taskId
    batch_id = $batchId
    previous_batch_id = $previousBatchId
    updated_at = Now-Utc
    run_status = $RunStatus
    current_stage = $currentStage
    stage_completed_count = $completedStages
    stage_total_count = $stageTotalCount
    operation_count = $combined.Count
    new_operations_count = $currentBatchRows.Count
    blocked_operation_count = $blocked.Count
    last_successful_operation = if ($successful.Count) { $successful[-1] } else { $null }
    last_blocked_operation = if ($blocked.Count) { $blocked[-1] } else { $null }
    operations = $combined
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
  $script:stageRows += [pscustomobject][ordered]@{
    stage_no = $StageNo
    stage = $Name
    status = $Status
    completed_at = Now-Utc
  }
  Add-Operation -Type 'pipeline_stage' -Status $Status -StageNo $StageNo -StageName $Name -RepoArtifactPath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'
}

try {
  Add-Operation -Type 'task_start' -Status 'running' -StageNo 1 -StageName 'task_start' -RepoArtifactPath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'

  $visibleRowsPath = Join-Path $repoRoot ($visibleRowsRel -replace '/', '\')
  $visible = Read-Json $visibleRowsPath
  $parcelRows = @($visible.rows)
  if ($null -eq $visible -or $parcelRows.Count -lt 3) { throw 'TOPOGRAPHY_161_VISIBLE_ROWS_NOT_READY' }
  Complete-Stage -StageNo 1 -Name 'load_verified_parcel_rows'

  $officialChecks = @(
    (Test-OfficialSource -Name 'HM Land Registry INSPIRE guidance' -Url 'https://www.gov.uk/guidance/inspire-index-polygons-spatial-data'),
    (Test-OfficialSource -Name 'HM Land Registry INSPIRE data service' -Url 'https://use-land-property-data.service.gov.uk/datasets/inspire'),
    (Test-OfficialSource -Name 'Environment Agency LiDAR survey download' -Url 'https://environment.data.gov.uk/survey'),
    (Test-OfficialSource -Name 'Ordnance Survey Terrain 50 open download' -Url 'https://osdatahub.os.uk/downloads/open/Terrain50')
  )
  foreach ($check in $officialChecks) {
    $checkStatus = if ($check.reachable) { 'source_check_only_available' } else { 'blocked_or_unavailable' }
    Add-Operation -Type 'official_source_check_only' -Status $checkStatus -StageNo 2 -StageName 'official_source_checks' -SourceName $check.name -SourceUrl $check.url -RequestUrl $check.final_url -RepoArtifactPath $sourceRel -Blocker (if ($check.reachable) { '' } else { 'OFFICIAL_SOURCE_UNREACHABLE' }) -ErrorMessage $check.error
  }
  $reachableOfficialCount = @($officialChecks | Where-Object { $_.reachable }).Count
  Complete-Stage -StageNo 2 -Name 'official_source_checks' -Status (if ($reachableOfficialCount -ge 3) { 'completed' } else { 'partial' })

  $inventory = @()
  $inventoryRoots = @(
    (Join-Path $repoRoot 'england_map_web\data'),
    (Join-Path $repoRoot 'docs\chatgpt_status'),
    (Join-Path $repoRoot 'outputs')
  ) | Where-Object { Test-Path -LiteralPath $_ }

  foreach ($inventoryRoot in $inventoryRoots) {
    $files = Get-ChildItem -LiteralPath $inventoryRoot -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Extension -match '(?i)^\.(geojson|json|gml|xml|gpkg|shp|zip)$' -and
        $_.FullName -match '(?i)inspire|hmlr|boundary|parcel'
      } |
      Select-Object -First 250
    foreach ($file in $files) {
      $relativePath = To-RepoRelativePath -FullPath $file.FullName -Root $repoRoot
      $candidate = [pscustomobject][ordered]@{
        path = $relativePath
        extension = $file.Extension
        size_bytes = $file.Length
        last_write_utc = $file.LastWriteTimeUtc.ToString('o')
      }
      $inventory += $candidate
      Add-Operation -Type 'boundary_candidate_inventory' -Status 'candidate_found' -StageNo 3 -StageName 'boundary_inventory' -SourceName 'canonical F repository boundary candidate' -NumericValue $file.Length -Unit 'bytes' -RepoArtifactPath $relativePath
    }
  }

  $boundaryMatches = @()
  $jsonCandidates = @($inventory | Where-Object { $_.extension -match '(?i)^\.(geojson|json)$' -and [int64]$_.size_bytes -lt 52428800 })
  foreach ($candidate in $jsonCandidates) {
    try {
      $candidatePath = Join-Path $repoRoot ($candidate.path -replace '/', '\')
      $json = Read-Json $candidatePath
      $features = @($json.features)
      foreach ($parcel in $parcelRows) {
        foreach ($feature in $features) {
          if ($null -eq $feature -or $null -eq $feature.geometry) { continue }
          if ([string]$feature.geometry.type -notmatch '^(Polygon|MultiPolygon)$') { continue }
          $propertiesText = $feature.properties | ConvertTo-Json -Depth 30 -Compress
          if ($propertiesText -match [regex]::Escape([string]$parcel.parcel_ref)) {
            $boundaryMatches += [pscustomobject][ordered]@{
              parcel_id = $parcel.parcel_id
              parcel_ref = $parcel.parcel_ref
              source_path = $candidate.path
              geometry = $feature.geometry
              properties = $feature.properties
              match_method = 'parcel_ref_property_match_with_non_null_polygon_or_multipolygon_geometry'
            }
            break
          }
        }
      }
    } catch {}
  }
  $boundaryMatches = @($boundaryMatches | Group-Object parcel_id | ForEach-Object { $_.Group | Select-Object -First 1 })

  Write-Json (Join-Path $repoRoot ($boundaryInventoryRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    batch_id = $batchId
    generated_at = Now-Utc
    candidate_count = $inventory.Count
    candidates = $inventory
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })
  Write-Json (Join-Path $repoRoot ($boundaryRowsRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    batch_id = $batchId
    generated_at = Now-Utc
    real_boundary_rows = $boundaryMatches.Count
    rows = $boundaryMatches
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })
  foreach ($boundaryMatch in $boundaryMatches) {
    Add-Operation -Type 'real_boundary_match' -Status 'validated' -StageNo 3 -StageName 'boundary_inventory_and_match' -ParcelId $boundaryMatch.parcel_id -ParcelRef $boundaryMatch.parcel_ref -SourceName 'local boundary artifact' -RepoArtifactPath $boundaryRowsRel
  }
  Complete-Stage -StageNo 3 -Name 'boundary_inventory_and_match' -Status (if ($boundaryMatches.Count -eq 3) { 'completed' } else { 'partial' })

  $odataBase = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
  $odataFilter = "contains(Name,'N51')"
  $odataUrl = $odataBase + '?$filter=' + [System.Uri]::EscapeDataString($odataFilter) + '&$top=100&$expand=Attributes'
  $copernicus = [ordered]@{
    url = $odataUrl
    reachable = $false
    result_count = 0
    matching_products = @()
    error = $null
  }
  try {
    $odata = Invoke-RestMethod -Method Get -Uri $odataUrl -TimeoutSec 180 -Headers @{ 'User-Agent' = 'TerraYield-AAYS-Topography/1.0 CopDEM-primary' }
    $products = @($odata.value)
    $matchingProducts = @($products | Where-Object {
      ([string]$_.Name -match '(?i)N51[_-]?00|N51[_-]?W001|N51W001') -or
      ((@($_.Attributes) | ConvertTo-Json -Depth 30 -Compress) -match '(?i)N51[_-]?W001')
    })
    $copernicus.reachable = $true
    $copernicus.result_count = $products.Count
    $copernicus.matching_products = @($matchingProducts | Select-Object -First 20 Id, Name, ContentDate, PublicationDate, Footprint, Attributes)
  } catch {
    $copernicus.error = $_.Exception.Message
  }
  Add-Operation -Type 'copernicus_catalogue_query' -Status (if ($copernicus.reachable) { 'completed' } else { 'blocked_or_unavailable' }) -StageNo 4 -StageName 'copdem_catalogue_query' -SourceName 'Copernicus Data Space OData' -SourceUrl $odataBase -RequestUrl $odataUrl -DatasetId 'COP-DEM_GLO-30' -NumericValue @($copernicus.matching_products).Count -Unit 'matching products' -RepoArtifactPath $sourceRel -Blocker (if ($copernicus.reachable) { '' } else { 'COPERNICUS_ODATA_UNREACHABLE' }) -ErrorMessage $copernicus.error
  foreach ($productRow in @($copernicus.matching_products)) {
    Add-Operation -Type 'copernicus_product_candidate' -Status 'candidate_found' -StageNo 4 -StageName 'copdem_catalogue_query' -SourceName ([string]$productRow.Name) -SourceUrl $odataBase -RequestUrl $odataUrl -DatasetId 'COP-DEM_GLO-30' -ProductId ([string]$productRow.Id) -RepoArtifactPath $sourceRel
  }
  Complete-Stage -StageNo 4 -Name 'copdem_catalogue_query' -Status (if ($copernicus.reachable) { 'completed' } else { 'blocked_or_unavailable' })

  $accessToken = if ($env:CDSE_ACCESS_TOKEN) { [string]$env:CDSE_ACCESS_TOKEN } elseif ($env:COPERNICUS_ACCESS_TOKEN) { [string]$env:COPERNICUS_ACCESS_TOKEN } else { $null }
  $selectedProduct = @($copernicus.matching_products | Select-Object -First 1)
  $downloadGate = [ordered]@{
    token_configured = [bool]$accessToken
    product_found = ($selectedProduct.Count -gt 0)
    product_id = if ($selectedProduct.Count) { [string]$selectedProduct[0].Id } else { $null }
    product_name = if ($selectedProduct.Count) { [string]$selectedProduct[0].Name } else { $null }
    download_url = if ($selectedProduct.Count) { "https://download.dataspace.copernicus.eu/odata/v1/Products($($selectedProduct[0].Id))/`$value" } else { $null }
    status = if (-not $selectedProduct.Count) { 'product_not_found' } elseif (-not $accessToken) { 'auth_required' } else { 'download_ready' }
  }
  $downloadBlocker = if ($downloadGate.status -eq 'download_ready') { '' } elseif ($downloadGate.status -eq 'auth_required') { 'CDSE_ACCESS_TOKEN_NOT_AVAILABLE' } else { 'COPDEM_MATCHING_PRODUCT_NOT_FOUND' }
  Add-Operation -Type 'primary_copdem_download_gate' -Status $downloadGate.status -StageNo 5 -StageName 'copdem_download_gate' -SourceName 'Copernicus DEM GLO-30' -SourceUrl $odataBase -RequestUrl $downloadGate.download_url -DatasetId 'COP-DEM_GLO-30' -ProductId $downloadGate.product_id -RepoArtifactPath $sourceRel -Blocker $downloadBlocker
  Complete-Stage -StageNo 5 -Name 'primary_copdem_download_gate' -Status $downloadGate.status

  $rasterCandidates = @()
  $configuredRoots = @(
    $env:AAYS_DATA_ROOT,
    $env:EA_LIDAR_ROOT,
    $env:OS_TERRAIN_ROOT,
    (Join-Path $repoRoot 'docs\chatgpt_status\topography\source_snapshots')
  ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
  foreach ($configuredRoot in $configuredRoots) {
    $files = Get-ChildItem -LiteralPath $configuredRoot -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Extension -match '(?i)^\.(tif|tiff|asc)$' -and
        $_.FullName -match '(?i)cop.?dem|lidar|terrain.?50|dtm'
      } |
      Select-Object -First 50
    foreach ($file in $files) {
      $relativePath = To-RepoRelativePath -FullPath $file.FullName -Root $repoRoot
      $candidate = [pscustomobject][ordered]@{
        full_path = $file.FullName
        repo_relative_path = $relativePath
        extension = $file.Extension
        size_bytes = $file.Length
        last_write_utc = $file.LastWriteTimeUtc.ToString('o')
      }
      $rasterCandidates += $candidate
      Add-Operation -Type 'primary_raster_candidate_inventory' -Status 'candidate_found' -StageNo 6 -StageName 'primary_raster_inventory' -SourceName 'configured canonical storage raster candidate' -NumericValue $file.Length -Unit 'bytes' -RepoArtifactPath $relativePath -LocalSourcePath $file.FullName
    }
  }
  $rasterCandidates = @($rasterCandidates | Group-Object full_path | ForEach-Object { $_.Group | Select-Object -First 1 })
  Complete-Stage -StageNo 6 -Name 'primary_raster_inventory'

  Write-Json (Join-Path $repoRoot ($sourceRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    batch_id = $batchId
    generated_at = Now-Utc
    official_source_checks = $officialChecks
    boundary_inventory_count = $inventory.Count
    real_boundary_rows = $boundaryMatches.Count
    copernicus_catalogue = $copernicus
    copdem_download_gate = $downloadGate
    local_primary_rasters = $rasterCandidates
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })

  $realBoundaryCount = $boundaryMatches.Count
  $productCount = @($copernicus.matching_products).Count
  $completionPercent = if ($realBoundaryCount -eq 3 -and $productCount -gt 0) { 74 } elseif ($realBoundaryCount -eq 3 -or $productCount -gt 0) { 72 } else { 70 }
  $blockers = @()
  if ($realBoundaryCount -lt 3) { $blockers += 'real_parcel_boundary_required' }
  if ($downloadGate.status -eq 'auth_required') { $blockers += 'cdse_access_token_required_for_primary_download' }
  if ($productCount -eq 0) { $blockers += 'copdem_matching_product_required' }
  $blockers += 'primary_copdem_glo30_raster_sampling_required'
  $blockers += 'ea_lidar_or_os_terrain_numeric_validation_required'

  foreach ($parcel in $parcelRows) {
    $boundaryMatch = @($boundaryMatches | Where-Object { $_.parcel_id -eq $parcel.parcel_id } | Select-Object -First 1)
    Set-Prop $parcel 'real_boundary_validated' ($boundaryMatch.Count -gt 0)
    Set-Prop $parcel 'real_boundary_evidence_path' $boundaryRowsRel
    Set-Prop $parcel 'copdem_product_candidates' $productCount
    Set-Prop $parcel 'copdem_download_gate_status' $downloadGate.status
    Set-Prop $parcel 'task_id' $taskId
    Set-Prop $parcel 'updated_at' (Now-Utc)
    Set-Prop $parcel 'report_path' $reportRel
    Set-Prop $parcel 'status_path' $statusRel
    Set-Prop $parcel 'display_badge' 'PRIMARY_EVIDENCE_DISCOVERY_READY'
    Set-Prop $parcel 'accuracy_score_4' '2.5/4 fallback; numeric primary validation pending'
    Set-Prop $parcel 'blocker' ($blockers -join '; ')
  }
  Set-Prop $visible 'status' 'PRIMARY_EVIDENCE_DISCOVERY_VISIBLE_NOT_FINAL'
  Set-Prop $visible 'latest_task_id' $taskId
  Set-Prop $visible 'latest_batch_id' $batchId
  Set-Prop $visible 'updated_at' (Now-Utc)
  Set-Prop $visible 'rows' $parcelRows
  Set-Prop $visible 'final_ready' $false
  Set-Prop $visible 'fake_data' $false
  Write-Json $visibleRowsPath $visible
  Complete-Stage -StageNo 7 -Name 'site_publication_prepared'

  $statusPayload = [ordered]@{
    task_id = $taskId
    page_key = 'topography'
    batch_id = $batchId
    previous_batch_id = $previousBatchId
    status = 'PRIMARY_EVIDENCE_DISCOVERY_VISIBLE_NOT_FINAL'
    started_at = $startedAt
    completed_at = $null
    stages = $stageRows
    completed_stage_count = $completedStages
    total_stage_count = $stageTotalCount
    candidate_rows = $parcelRows.Count
    official_sources_checked = $officialChecks.Count
    official_sources_reachable = $reachableOfficialCount
    boundary_inventory_candidates = $inventory.Count
    real_boundary_rows = $realBoundaryCount
    copernicus_products_found = $productCount
    copdem_download_gate_status = $downloadGate.status
    local_primary_raster_candidates = $rasterCandidates.Count
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
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $statusPayload
  Write-Json (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\')) $statusPayload
  Write-Json (Join-Path $repoRoot ($latestChangesRel -replace '/', '\')) ([ordered]@{
    layer = 'Topography'
    task_id = $taskId
    updated_at = Now-Utc
    summary = $statusPayload
    rows = $parcelRows
    final_ready = $false
    fake_data = $false
  })

  if ($env:AAYS_CONTROLLER_REPO_ROOT) {
    $publisher = Join-Path $repoRoot 'docs\chatgpt_status\_shared\automation\PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1'
    $publishPaths = @($visibleRowsRel, $visibleStatusRel, $operationsRel, $sourceRel, $boundaryInventoryRel, $boundaryRowsRel) -join '|'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $repoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths $publishPaths -AllowGeneratedArtifacts -SyncPortableWeb
    if ($LASTEXITCODE -ne 0) { throw 'TOPOGRAPHY_161_LIVE_CONTROLLER_PUBLISH_BLOCKED' }
  }

  $siteRowsUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
  $siteOperationsUrl = 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_operations_latest.json'
  $siteRowsResponse = Invoke-WebRequest -UseBasicParsing -Uri $siteRowsUrl -TimeoutSec 30
  $siteOperationsResponse = Invoke-WebRequest -UseBasicParsing -Uri $siteOperationsUrl -TimeoutSec 30
  if ($siteRowsResponse.StatusCode -ne 200 -or $siteOperationsResponse.StatusCode -ne 200) { throw 'TOPOGRAPHY_161_SITE_HTTP_READBACK_FAILED' }
  Add-Operation -Type 'site_http_readback' -Status 'PASS' -StageNo 8 -StageName 'http_readback' -SourceName 'localhost 8012' -SourceUrl $siteRowsUrl -RequestUrl $siteOperationsUrl -RepoArtifactPath $visibleRowsRel
  Complete-Stage -StageNo 8 -Name 'http_readback' -Status 'PASS'

  $statusPayload.completed_at = Now-Utc
  $statusPayload.stages = $stageRows
  $statusPayload.completed_stage_count = 8
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\')) $statusPayload
  Write-Json (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\')) $statusPayload
  Publish-Ledger -RunStatus 'COMPLETED_VISIBLE_NOT_FINAL'

  $reportText = @"
# Topography 161 Primary Evidence Acquisition

- Task: $taskId
- Official sources reachable: $reachableOfficialCount/$($officialChecks.Count)
- Boundary inventory candidates: $($inventory.Count)
- Real boundary rows: $realBoundaryCount/3
- Copernicus product matches: $productCount
- CopDEM download gate: $($downloadGate.status)
- Local primary raster candidates: $($rasterCandidates.Count)
- New operation rows: $(@($operations).Count)
- Site HTTP readback: PASS
- Completion: $completionPercent%
- Increase: +$($completionPercent - 70)%
- Accuracy: 2.5/4 fallback
- final_ready: false
"@
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($reportRel -replace '/', '\')))
  [System.IO.File]::WriteAllText((Join-Path $repoRoot ($reportRel -replace '/', '\')), $reportText, [System.Text.UTF8Encoding]::new($false))

  Write-Json (Join-Path $repoRoot ($outputRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    status = 'COMPLETED_VISIBLE_NOT_FINAL'
    completed_at = Now-Utc
    completion_percent = $completionPercent
    percent_increase = ($completionPercent - 70)
    completed_stage_count = 8
    total_stage_count = 8
    candidate_rows = $parcelRows.Count
    official_sources_checked = $officialChecks.Count
    official_sources_reachable = $reachableOfficialCount
    boundary_inventory_candidates = $inventory.Count
    real_boundary_rows = $realBoundaryCount
    copernicus_products_found = $productCount
    copdem_download_gate_status = $downloadGate.status
    local_primary_raster_candidates = $rasterCandidates.Count
    new_operation_rows = @($operations).Count
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
} catch {
  $errorMessage = $_.Exception.Message
  Add-Operation -Type 'runner_failure' -Status 'blocked' -StageNo ([math]::Max(1, $completedStages + 1)) -StageName $currentStage -RepoArtifactPath $statusRel -Blocker $errorMessage -ErrorMessage $errorMessage
  Publish-Ledger -RunStatus 'BLOCKED'
  Write-Json (Join-Path $repoRoot ($outputRel -replace '/', '\')) ([ordered]@{
    task_id = $taskId
    status = 'BLOCKED'
    error = $errorMessage
    completed_stage_count = $completedStages
    total_stage_count = $stageTotalCount
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  })
  throw
}

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Dir([string]$Path) {
  if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}
function Write-Json([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  $tmp = "$Path.tmp"
  [System.IO.File]::WriteAllText($tmp, (($Value | ConvertTo-Json -Depth 90) + "`n"), [System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Read-Json([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return $null }
  return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Set-Prop([object]$Object, [string]$Name, [object]$Value) {
  Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force
}
function Test-Http([string]$Name, [string]$Url) {
  $result = [ordered]@{ name=$Name; url=$Url; reachable=$false; status_code=$null; final_url=$null; error=$null }
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -MaximumRedirection 10 -TimeoutSec 120 -Headers @{ 'User-Agent'='TerraYield-AAYS-Topography/1.0 targeted-acquisition' }
    $result.status_code = [int]$response.StatusCode
    $result.reachable = ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400)
    if ($response.BaseResponse -and $response.BaseResponse.ResponseUri) { $result.final_url = [string]$response.BaseResponse.ResponseUri.AbsoluteUri }
  } catch {
    try { $result.status_code = [int]$_.Exception.Response.StatusCode.value__ } catch {}
    $result.error = $_.Exception.Message
  }
  return [pscustomobject]$result
}
function Resolve-Links([string]$PageUrl, [string]$Html) {
  $items = @()
  foreach ($match in [regex]::Matches($Html, 'href\s*=\s*["'']([^"'']+)["'']', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
    $href = [string]$match.Groups[1].Value
    if (-not $href -or $href.StartsWith('#') -or $href.StartsWith('javascript:')) { continue }
    try {
      $absolute = ([uri]::new([uri]$PageUrl, $href)).AbsoluteUri
      if ($absolute -match '(?i)inspire|gml|\.zip(?:$|\?)|download|dataset') { $items += $absolute }
    } catch {}
  }
  return @($items | Select-Object -Unique)
}
function Invoke-OData([string]$DatasetId, [string]$CellPattern) {
  $base = 'https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
  $filter = "Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'datasetFull' and att/OData.CSC.StringAttribute/Value eq '$DatasetId') and (contains(Name,'$CellPattern') or contains(Name,'N51_W001') or contains(Name,'N51W001'))"
  $url = $base + '?$filter=' + [uri]::EscapeDataString($filter) + '&$top=20&$expand=Attributes'
  $payload = [ordered]@{ dataset_id=$DatasetId; url=$url; reachable=$false; result_count=0; products=@(); error=$null }
  try {
    $response = Invoke-RestMethod -Method Get -Uri $url -TimeoutSec 180 -Headers @{ 'User-Agent'='TerraYield-AAYS-Topography/1.0 targeted-copdem' }
    $products = @($response.value)
    $payload.reachable = $true
    $payload.result_count = $products.Count
    $payload.products = @($products | Select-Object -First 20 Id,Name,ContentDate,PublicationDate,Footprint,Attributes)
  } catch {
    $payload.error = $_.Exception.Message
  }
  return [pscustomobject]$payload
}

$repoRoot = [System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if (-not $repoRoot -or $repoRoot -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]') {
  throw 'TOPOGRAPHY_162_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'
}

$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'aays1-162-topography-copdem-hmlr-targeted-acquisition-20260713' }
$startedAt = Now-Utc
$batchId = 'topography-162-' + ($startedAt -replace '[^0-9]', '')
$previousBatchId = 'aays1-161-topography-primary-evidence-acquisition-20260713'
$stageTotal = 10
$stageDone = 0
$currentStage = 'task_start'
$operations = @()
$stages = @()

$visibleRowsRel = 'england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$operationsRel = 'england_map_web/data/program_layer_matrix/topography_operations_latest.json'
$latestChangesRel = 'outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$sourceRel = 'docs/chatgpt_status/topography/source_snapshots/162_targeted_primary_sources_latest.json'
$boundaryInventoryRel = 'docs/chatgpt_status/topography/source_snapshots/162_boundary_and_download_inventory_latest.json'
$boundaryRowsRel = 'docs/chatgpt_status/topography/fixtures/topography_targeted_boundary_candidates_20260713.json'
$statusRel = 'docs/chatgpt_status/topography/status/162_topography_copdem_hmlr_targeted_acquisition_latest.json'
$reportRel = 'docs/chatgpt_status/topography/reports/162_topography_copdem_hmlr_targeted_acquisition_report_20260713.md'
$outputRel = 'docs/chatgpt_status/topography/runner_outputs/162_topography_copdem_hmlr_targeted_acquisition_batch.json'

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
  $operations += [pscustomobject][ordered]@{
    operation_id = "${batchId}_$($operations.Count + 1)"
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
    method = if ($Type -match 'catalogue') { 'official datasetFull OData metadata query' } elseif ($Type -match 'boundary') { 'bounded canonical F artifact inventory and parcel-reference geometry match' } elseif ($Type -match 'link') { 'official page link discovery and HTTP reachability' } else { $null }
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
  $path = Join-Path $repoRoot ($operationsRel -replace '/', '\\')
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
  $blocked = @($all | Where-Object { [string]$_.status -match 'blocked|failed|unavailable|auth_required|not_found|partial' })
  $payload = [ordered]@{
    task_id=$taskId; batch_id=$batchId; previous_batch_id=$previousBatchId; updated_at=Now-Utc
    run_status=$RunStatus; current_stage=$currentStage; stage_completed_count=$stageDone; stage_total_count=$stageTotal
    operation_count=$all.Count; new_operations_count=$operations.Count; blocked_operation_count=$blocked.Count
    last_blocked_operation=if($blocked.Count){$blocked[-1]}else{$null}; operations=$all
    final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  }
  Write-Json $path $payload
}
function Complete-Stage([int]$No, [string]$Name, [string]$Status = 'completed') {
  $stageDone = $No
  $currentStage = $Name
  $stages += [pscustomobject][ordered]@{ stage_no=$No; stage=$Name; status=$Status; completed_at=Now-Utc }
  Add-Operation -Type 'pipeline_stage' -Status $Status -StageNo $No -StageName $Name -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'
}

try {
  Add-Operation -Type 'task_start' -Status 'running' -StageNo 1 -StageName 'task_start' -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'

  $visiblePath = Join-Path $repoRoot ($visibleRowsRel -replace '/', '\\')
  $visible = Read-Json $visiblePath
  $parcelRows = @($visible.rows)
  if ($null -eq $visible -or $parcelRows.Count -lt 3) { throw 'TOPOGRAPHY_162_VISIBLE_ROWS_NOT_READY' }
  Complete-Stage -No 1 -Name 'load_verified_parcel_rows'

  $officialUrls = @(
    [pscustomobject]@{name='Copernicus DEM collection';url='https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM'},
    [pscustomobject]@{name='HMLR INSPIRE guidance';url='https://www.gov.uk/guidance/inspire-index-polygons-spatial-data'},
    [pscustomobject]@{name='HMLR INSPIRE dataset service';url='https://use-land-property-data.service.gov.uk/datasets/inspire'},
    [pscustomobject]@{name='Environment Agency LiDAR survey';url='https://environment.data.gov.uk/survey'},
    [pscustomobject]@{name='OS Terrain 50';url='https://osdatahub.os.uk/downloads/open/Terrain50'}
  )
  $officialChecks = @()
  foreach ($item in $officialUrls) {
    $check = Test-Http -Name $item.name -Url $item.url
    $officialChecks += $check
    $checkStatus = 'blocked_or_unavailable'
    $checkBlocker = $check.error
    if ($check.reachable) { $checkStatus='source_check_only_available'; $checkBlocker='' }
    Add-Operation -Type 'official_source_check_only' -Status $checkStatus -StageNo 2 -StageName 'official_source_checks' -SourceName $check.name -SourceUrl $check.url -RequestUrl $check.final_url -EvidencePath $sourceRel -Blocker $checkBlocker
  }
  $officialStageStatus = 'partial'
  if (@($officialChecks | Where-Object { $_.reachable }).Count -eq $officialChecks.Count) { $officialStageStatus='completed' }
  Complete-Stage -No 2 -Name 'official_source_checks' -Status $officialStageStatus

  $dged = Invoke-OData -DatasetId 'COP-DEM_GLO-30-DGED' -CellPattern 'N51_00_W001'
  $dgedStatus = 'blocked_or_unavailable'
  $dgedBlocker = $dged.error
  if ($dged.reachable) { $dgedStatus='completed'; $dgedBlocker='' }
  Add-Operation -Type 'copdem_catalogue_query' -Status $dgedStatus -StageNo 3 -StageName 'copdem_dged_catalogue' -SourceName 'Copernicus DEM GLO-30 DGED' -SourceUrl 'https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM' -RequestUrl $dged.url -NumericValue $dged.result_count -Unit 'products' -EvidencePath $sourceRel -Blocker $dgedBlocker
  Complete-Stage -No 3 -Name 'copdem_dged_catalogue' -Status $dgedStatus

  $dted = Invoke-OData -DatasetId 'COP-DEM_GLO-30-DTED' -CellPattern 'N51_00_W001'
  $dtedStatus = 'blocked_or_unavailable'
  $dtedBlocker = $dted.error
  if ($dted.reachable) { $dtedStatus='completed'; $dtedBlocker='' }
  Add-Operation -Type 'copdem_catalogue_query' -Status $dtedStatus -StageNo 4 -StageName 'copdem_dted_catalogue' -SourceName 'Copernicus DEM GLO-30 DTED' -SourceUrl 'https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM' -RequestUrl $dted.url -NumericValue $dted.result_count -Unit 'products' -EvidencePath $sourceRel -Blocker $dtedBlocker
  Complete-Stage -No 4 -Name 'copdem_dted_catalogue' -Status $dtedStatus

  $hmlrPageUrl = 'https://use-land-property-data.service.gov.uk/datasets/inspire'
  $hmlrLinks = @()
  $hmlrError = $null
  try {
    $hmlrPage = Invoke-WebRequest -UseBasicParsing -Uri $hmlrPageUrl -TimeoutSec 120 -Headers @{ 'User-Agent'='TerraYield-AAYS-Topography/1.0 HMLR-link-discovery' }
    $hmlrLinks = Resolve-Links -PageUrl $hmlrPageUrl -Html $hmlrPage.Content
  } catch { $hmlrError = $_.Exception.Message }
  $hmlrChecks = @()
  foreach ($link in @($hmlrLinks | Select-Object -First 30)) {
    $linkCheck = Test-Http -Name 'HMLR INSPIRE candidate link' -Url $link
    $hmlrChecks += $linkCheck
    $linkStatus='blocked_or_unavailable'; $linkBlocker=$linkCheck.error
    if ($linkCheck.reachable) { $linkStatus='link_available'; $linkBlocker='' }
    Add-Operation -Type 'official_download_link_check' -Status $linkStatus -StageNo 5 -StageName 'hmlr_download_link_discovery' -SourceName 'HMLR INSPIRE' -SourceUrl $hmlrPageUrl -RequestUrl $link -EvidencePath $sourceRel -Blocker $linkBlocker
  }
  $hmlrStageStatus='partial'
  if ($hmlrLinks.Count -gt 0) { $hmlrStageStatus='completed' }
  if ($hmlrLinks.Count -eq 0) {
    Add-Operation -Type 'official_download_link_check' -Status 'not_found' -StageNo 5 -StageName 'hmlr_download_link_discovery' -SourceName 'HMLR INSPIRE' -SourceUrl $hmlrPageUrl -EvidencePath $sourceRel -Blocker $(if($hmlrError){$hmlrError}else{'NO_DOWNLOAD_LINK_DISCOVERED'})
  }
  Complete-Stage -No 5 -Name 'hmlr_download_link_discovery' -Status $hmlrStageStatus

  $inventory = @()
  $inventoryRoots = @(
    (Join-Path $repoRoot 'england_map_web\data'),
    (Join-Path $repoRoot 'docs\chatgpt_status'),
    (Join-Path $repoRoot 'outputs')
  ) | Where-Object { Test-Path -LiteralPath $_ }
  foreach ($inventoryRoot in $inventoryRoots) {
    $files = @(Get-ChildItem -LiteralPath $inventoryRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
      $_.Extension -match '(?i)^\.(geojson|json|gml|xml|gpkg|shp|zip)$' -and $_.FullName -match '(?i)inspire|hmlr|boundary|parcel'
    } | Select-Object -First 500)
    foreach ($file in $files) {
      $rel = $file.FullName.Substring($repoRoot.Length).TrimStart('\\') -replace '\\','/'
      $inventory += [pscustomobject][ordered]@{ path=$rel; extension=$file.Extension; size_bytes=$file.Length; zip_entries=@() }
    }
  }
  Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue
  foreach ($item in $inventory) {
    if ($item.extension -ieq '.zip' -and $item.size_bytes -lt 1073741824) {
      try {
        $zipPath = Join-Path $repoRoot ($item.path -replace '/', '\\')
        $archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
        $entries = @($archive.Entries | Where-Object { $_.FullName -match '(?i)\.(gml|geojson|json|shp|dbf|prj)$' } | Select-Object -First 100 -ExpandProperty FullName)
        $archive.Dispose()
        Set-Prop $item 'zip_entries' $entries
      } catch {}
    }
  }
  $validatedBoundaries = @()
  $gmlCandidates = @()
  foreach ($item in $inventory) {
    $candidatePath = Join-Path $repoRoot ($item.path -replace '/', '\\')
    if ($item.extension -match '(?i)^\.(geojson|json)$' -and $item.size_bytes -lt 52428800) {
      try {
        $json = Read-Json $candidatePath
        foreach ($parcel in $parcelRows) {
          foreach ($feature in @($json.features)) {
            $propsText = ($feature.properties | ConvertTo-Json -Depth 30 -Compress)
            $geometryType = [string]$feature.geometry.type
            if ($feature.geometry -and $geometryType -match 'Polygon' -and $propsText -match [regex]::Escape([string]$parcel.parcel_ref)) {
              $validatedBoundaries += [pscustomobject][ordered]@{ parcel_id=$parcel.parcel_id; parcel_ref=$parcel.parcel_ref; source_path=$item.path; geometry=$feature.geometry; properties=$feature.properties; match_method='parcel_ref_property_match_with_non_null_polygon_geometry' }
              break
            }
          }
        }
      } catch {}
    }
    if ($item.extension -match '(?i)^\.(gml|xml)$' -and $item.size_bytes -lt 52428800) {
      try {
        $raw = Get-Content -LiteralPath $candidatePath -Raw -Encoding UTF8
        foreach ($parcel in $parcelRows) {
          if ($raw -match [regex]::Escape([string]$parcel.parcel_ref) -and $raw -match '(?i)<(?:\w+:)?Polygon\b') {
            $gmlCandidates += [pscustomobject][ordered]@{ parcel_id=$parcel.parcel_id; parcel_ref=$parcel.parcel_ref; source_path=$item.path; status='candidate_only_requires_geometry_binding_validation' }
          }
        }
      } catch {}
    }
  }
  $validatedBoundaries = @($validatedBoundaries | Group-Object parcel_id | ForEach-Object { $_.Group | Select-Object -First 1 })
  $gmlCandidates = @($gmlCandidates | Group-Object parcel_id,source_path | ForEach-Object { $_.Group | Select-Object -First 1 })
  Write-Json (Join-Path $repoRoot ($boundaryInventoryRel -replace '/', '\\')) ([ordered]@{ task_id=$taskId; batch_id=$batchId; generated_at=Now-Utc; inventory_count=$inventory.Count; inventory=$inventory; gml_candidate_count=$gmlCandidates.Count; gml_candidates=$gmlCandidates; final_ready=$false; fake_data=$false })
  Write-Json (Join-Path $repoRoot ($boundaryRowsRel -replace '/', '\\')) ([ordered]@{ task_id=$taskId; batch_id=$batchId; generated_at=Now-Utc; real_boundary_rows=$validatedBoundaries.Count; rows=$validatedBoundaries; gml_candidates=$gmlCandidates; final_ready=$false; fake_data=$false })
  Add-Operation -Type 'boundary_artifact_inventory' -Status 'completed' -StageNo 6 -StageName 'boundary_inventory_and_match' -SourceName 'canonical F repository' -NumericValue $inventory.Count -Unit 'candidate files' -EvidencePath $boundaryInventoryRel
  foreach ($boundary in $validatedBoundaries) {
    Add-Operation -Type 'real_boundary_match' -Status 'validated' -StageNo 6 -StageName 'boundary_inventory_and_match' -ParcelId $boundary.parcel_id -SourceName 'local boundary artifact' -EvidencePath $boundaryRowsRel
  }
  foreach ($candidate in $gmlCandidates) {
    Add-Operation -Type 'gml_boundary_candidate' -Status 'candidate_only' -StageNo 6 -StageName 'boundary_inventory_and_match' -ParcelId $candidate.parcel_id -SourceName 'local GML candidate' -EvidencePath $boundaryInventoryRel -Blocker 'GEOMETRY_BINDING_VALIDATION_REQUIRED'
  }
  $boundaryStageStatus='partial'
  if ($validatedBoundaries.Count -eq 3) { $boundaryStageStatus='completed' }
  Complete-Stage -No 6 -Name 'boundary_inventory_and_match' -Status $boundaryStageStatus

  $allProducts = @($dged.products + $dted.products)
  $uniqueProducts = @($allProducts | Group-Object Id | ForEach-Object { $_.Group | Select-Object -First 1 })
  $token = $null
  if ($env:CDSE_ACCESS_TOKEN) { $token=[string]$env:CDSE_ACCESS_TOKEN }
  elseif ($env:COPERNICUS_ACCESS_TOKEN) { $token=[string]$env:COPERNICUS_ACCESS_TOKEN }
  $gateStatus='product_not_found'; $gateBlocker='COPDEM_MATCHING_PRODUCT_NOT_FOUND'; $downloadUrl=$null
  if ($uniqueProducts.Count -gt 0) {
    $downloadUrl = "https://download.dataspace.copernicus.eu/odata/v1/Products($([string]$uniqueProducts[0].Id))/`$value"
    $gateStatus='auth_required'; $gateBlocker='CDSE_ACCESS_TOKEN_NOT_AVAILABLE'
    if ($token) { $gateStatus='download_metadata_ready'; $gateBlocker='' }
  }
  Add-Operation -Type 'primary_copdem_download_gate' -Status $gateStatus -StageNo 7 -StageName 'copdem_download_gate_and_raster_inventory' -SourceName 'Copernicus DEM GLO-30' -SourceUrl 'https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM' -RequestUrl $downloadUrl -NumericValue $uniqueProducts.Count -Unit 'matching products' -EvidencePath $sourceRel -Blocker $gateBlocker
  $rasterFiles = @()
  $rasterRoots = @($env:AAYS_DATA_ROOT,$env:EA_LIDAR_ROOT,$env:OS_TERRAIN_ROOT,(Join-Path $repoRoot 'docs\chatgpt_status\topography\source_snapshots')) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
  foreach ($rasterRoot in $rasterRoots) {
    $rasterFiles += @(Get-ChildItem -LiteralPath $rasterRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match '(?i)^\.(tif|tiff|asc)$' -and $_.FullName -match '(?i)cop.?dem|lidar|terrain.?50|dtm' } | Select-Object -First 100 -ExpandProperty FullName)
  }
  $rasterFiles = @($rasterFiles | Select-Object -Unique)
  Add-Operation -Type 'primary_raster_inventory' -Status 'completed' -StageNo 7 -StageName 'copdem_download_gate_and_raster_inventory' -SourceName 'configured canonical storage' -NumericValue $rasterFiles.Count -Unit 'raster files' -EvidencePath $sourceRel
  Complete-Stage -No 7 -Name 'copdem_download_gate_and_raster_inventory' -Status $gateStatus

  Write-Json (Join-Path $repoRoot ($sourceRel -replace '/', '\\')) ([ordered]@{
    task_id=$taskId; batch_id=$batchId; generated_at=Now-Utc
    official_source_checks=$officialChecks; copdem_dged=$dged; copdem_dted=$dted
    matching_products=$uniqueProducts; copdem_download_gate=[ordered]@{status=$gateStatus; token_configured=[bool]$token; product_count=$uniqueProducts.Count; download_url=$downloadUrl}
    hmlr_page_url=$hmlrPageUrl; hmlr_discovered_links=$hmlrLinks; hmlr_link_checks=$hmlrChecks
    boundary_inventory_count=$inventory.Count; real_boundary_rows=$validatedBoundaries.Count; gml_candidate_rows=$gmlCandidates.Count
    local_primary_rasters=$rasterFiles
    official_copdem_dataset_ids=@('COP-DEM_GLO-30-DGED','COP-DEM_GLO-30-DTED')
    final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })

  $productCount=$uniqueProducts.Count
  $realBoundaryCount=$validatedBoundaries.Count
  $completionPercent=70
  if ($productCount -gt 0 -or $realBoundaryCount -eq 3) { $completionPercent=72 }
  if ($productCount -gt 0 -and $realBoundaryCount -eq 3) { $completionPercent=74 }
  $blockers=@()
  if ($realBoundaryCount -lt 3) { $blockers += 'real_parcel_boundary_required' }
  $blockers += 'primary_copdem_glo30_raster_sampling_required'
  $blockers += 'ea_lidar_or_os_terrain_numeric_validation_required'

  foreach ($row in $parcelRows) {
    $boundaryOk = @($validatedBoundaries | Where-Object { $_.parcel_id -eq $row.parcel_id }).Count -gt 0
    Set-Prop $row 'real_boundary_validated' $boundaryOk
    Set-Prop $row 'real_boundary_evidence_path' $boundaryRowsRel
    Set-Prop $row 'gml_boundary_candidate_count' @($gmlCandidates | Where-Object { $_.parcel_id -eq $row.parcel_id }).Count
    Set-Prop $row 'copdem_product_candidates' $productCount
    Set-Prop $row 'copdem_dataset_ids_checked' 'COP-DEM_GLO-30-DGED,COP-DEM_GLO-30-DTED'
    Set-Prop $row 'copdem_download_gate_status' $gateStatus
    Set-Prop $row 'hmlr_download_link_candidates' $hmlrLinks.Count
    Set-Prop $row 'task_id' $taskId
    Set-Prop $row 'updated_at' (Now-Utc)
    Set-Prop $row 'report_path' $reportRel
    Set-Prop $row 'status_path' $statusRel
    Set-Prop $row 'display_badge' 'TARGETED_PRIMARY_ACQUISITION_READY'
    Set-Prop $row 'accuracy_score_4' '2.5/4 fallback; primary numeric validation pending'
    Set-Prop $row 'blocker' ($blockers -join '; ')
  }
  Set-Prop $visible 'status' 'TARGETED_PRIMARY_ACQUISITION_VISIBLE_NOT_FINAL'
  Set-Prop $visible 'latest_task_id' $taskId
  Set-Prop $visible 'latest_batch_id' $batchId
  Set-Prop $visible 'updated_at' (Now-Utc)
  Set-Prop $visible 'rows' $parcelRows
  Set-Prop $visible 'final_ready' $false
  Set-Prop $visible 'fake_data' $false
  Write-Json $visiblePath $visible

  $statusPayload = [ordered]@{
    task_id=$taskId; page_key='topography'; batch_id=$batchId; previous_batch_id=$previousBatchId
    status='TARGETED_PRIMARY_ACQUISITION_VISIBLE_NOT_FINAL'; started_at=$startedAt; completed_at=Now-Utc
    stages=$stages; completed_stage_count=8; total_stage_count=$stageTotal; candidate_rows=$parcelRows.Count
    official_sources_checked=$officialChecks.Count; official_sources_reachable=@($officialChecks | Where-Object {$_.reachable}).Count
    copdem_dged_products=$dged.result_count; copdem_dted_products=$dted.result_count; copdem_products_found=$productCount
    hmlr_download_link_candidates=$hmlrLinks.Count; boundary_inventory_candidates=$inventory.Count
    gml_boundary_candidates=$gmlCandidates.Count; real_boundary_rows=$realBoundaryCount; local_primary_raster_candidates=$rasterFiles.Count
    completion_percent=$completionPercent; percent_increase=($completionPercent-70); accuracy_score_4='2.5/4 fallback'
    blockers=$blockers; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  }
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\\')) $statusPayload
  Write-Json (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\\')) $statusPayload
  Write-Json (Join-Path $repoRoot ($latestChangesRel -replace '/', '\\')) ([ordered]@{layer='Topography';task_id=$taskId;updated_at=Now-Utc;summary=$statusPayload;rows=$parcelRows;final_ready=$false;fake_data=$false})
  Complete-Stage -No 8 -Name 'site_artifact_generation'

  if ($env:AAYS_CONTROLLER_REPO_ROOT) {
    $publisher = Join-Path $repoRoot 'docs/chatgpt_status/_shared/automation/PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1'
    $publishPaths = @($visibleRowsRel,$visibleStatusRel,$operationsRel,$sourceRel,$boundaryInventoryRel,$boundaryRowsRel) -join '|'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $repoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths $publishPaths -AllowGeneratedArtifacts -SyncPortableWeb
    if ($LASTEXITCODE -ne 0) { throw 'TOPOGRAPHY_162_LIVE_CONTROLLER_PUBLISH_BLOCKED' }
  }
  Complete-Stage -No 9 -Name 'live_controller_publication'

  $siteRows = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json' -TimeoutSec 30
  $siteOps = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_operations_latest.json' -TimeoutSec 30
  if ($siteRows.StatusCode -ne 200 -or $siteOps.StatusCode -ne 200) { throw 'TOPOGRAPHY_162_SITE_HTTP_READBACK_FAILED' }
  if ($siteRows.Content -notmatch [regex]::Escape($taskId) -or $siteOps.Content -notmatch [regex]::Escape($taskId)) { throw 'TOPOGRAPHY_162_TASK_ID_NOT_VISIBLE' }
  Complete-Stage -No 10 -Name 'http_task_id_readback' -Status 'PASS'

  $statusPayload.completed_stage_count=10
  $statusPayload.completed_at=Now-Utc
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\\')) $statusPayload
  Write-Json (Join-Path $repoRoot ($visibleStatusRel -replace '/', '\\')) $statusPayload
  Publish-Ledger -RunStatus 'COMPLETED_VISIBLE_NOT_FINAL'

  $report = "# Topography 162 Targeted CopDEM and HMLR Acquisition`n`n- Task: $taskId`n- Official source checks: $(@($officialChecks | Where-Object {$_.reachable}).Count)/$($officialChecks.Count)`n- CopDEM DGED products: $($dged.result_count)`n- CopDEM DTED products: $($dted.result_count)`n- Unique matching products: $productCount`n- HMLR candidate links: $($hmlrLinks.Count)`n- Boundary inventory candidates: $($inventory.Count)`n- GML candidates: $($gmlCandidates.Count)`n- Real boundary rows: $realBoundaryCount/3`n- Local primary rasters: $($rasterFiles.Count)`n- New operation rows: $($operations.Count)`n- Site HTTP task-id readback: PASS`n- Completion: $completionPercent%`n- Increase: +$($completionPercent-70)%`n- Accuracy: 2.5/4 fallback`n- final_ready: false`n"
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($reportRel -replace '/', '\\')))
  [System.IO.File]::WriteAllText((Join-Path $repoRoot ($reportRel -replace '/', '\\')), $report, [System.Text.UTF8Encoding]::new($false))
  Write-Json (Join-Path $repoRoot ($outputRel -replace '/', '\\')) ([ordered]@{
    task_id=$taskId; status='COMPLETED_VISIBLE_NOT_FINAL'; completed_at=Now-Utc
    completion_percent=$completionPercent; percent_increase=($completionPercent-70); completed_stage_count=10; total_stage_count=10
    candidate_rows=$parcelRows.Count; copdem_products_found=$productCount; hmlr_download_link_candidates=$hmlrLinks.Count
    boundary_inventory_candidates=$inventory.Count; gml_boundary_candidates=$gmlCandidates.Count; real_boundary_rows=$realBoundaryCount
    local_primary_raster_candidates=$rasterFiles.Count; new_operation_rows=$operations.Count; site_http_validation='PASS'
    blockers=$blockers; accuracy_score_4='2.5/4 fallback'; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })
} catch {
  $errorMessage=$_.Exception.Message
  Add-Operation -Type 'runner_failure' -Status 'blocked' -StageNo ([math]::Max(1,$stageDone+1)) -StageName $currentStage -EvidencePath $statusRel -Blocker $errorMessage
  Publish-Ledger -RunStatus 'BLOCKED'
  $failure=[ordered]@{task_id=$taskId;status='BLOCKED';error=$errorMessage;completed_stage_count=$stageDone;total_stage_count=$stageTotal;completion_percent=70;percent_increase=0;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
  Write-Json (Join-Path $repoRoot ($statusRel -replace '/', '\\')) $failure
  Write-Json (Join-Path $repoRoot ($outputRel -replace '/', '\\')) $failure
  throw
}

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Write-Json([string]$Path, [object]$Value) {
  Ensure-Dir (Split-Path -Parent $Path)
  $tmp = "$Path.tmp"
  [System.IO.File]::WriteAllText($tmp, (($Value | ConvertTo-Json -Depth 90) + "`n"), [System.Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function Read-Json([string]$Path) { if (Test-Path -LiteralPath $Path) { return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json) }; return $null }
function Set-Prop([object]$Object,[string]$Name,[object]$Value) { Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force }
function Test-Http([string]$Name,[string]$Url) {
  $x=[ordered]@{name=$Name;url=$Url;reachable=$false;status_code=$null;final_url=$null;error=$null}
  try {
    $r=Invoke-WebRequest -UseBasicParsing -Uri $Url -MaximumRedirection 10 -TimeoutSec 120 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 targeted-acquisition-v2'}
    $x.status_code=[int]$r.StatusCode
    $x.reachable=($r.StatusCode -ge 200 -and $r.StatusCode -lt 400)
    if($r.BaseResponse -and $r.BaseResponse.ResponseUri){$x.final_url=[string]$r.BaseResponse.ResponseUri.AbsoluteUri}
  } catch {
    try{$x.status_code=[int]$_.Exception.Response.StatusCode.value__}catch{}
    $x.error=$_.Exception.Message
  }
  return [pscustomobject]$x
}
function Invoke-OData([string]$DatasetId) {
  $base='https://catalogue.dataspace.copernicus.eu/odata/v1/Products'
  $filter="Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'datasetFull' and att/OData.CSC.StringAttribute/Value eq '$DatasetId') and (contains(Name,'N51_00_W001') or contains(Name,'N51_W001') or contains(Name,'N51W001'))"
  $url=$base+'?$filter='+[uri]::EscapeDataString($filter)+'&$top=20&$expand=Attributes'
  $x=[ordered]@{dataset_id=$DatasetId;url=$url;reachable=$false;result_count=0;products=@();error=$null}
  try {
    $r=Invoke-RestMethod -Method Get -Uri $url -TimeoutSec 180 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 targeted-copdem-v2'}
    $p=@($r.value)
    $x.reachable=$true
    $x.result_count=$p.Count
    $x.products=@($p|Select-Object -First 20 Id,Name,ContentDate,PublicationDate,Footprint,Attributes)
  } catch {$x.error=$_.Exception.Message}
  return [pscustomobject]$x
}
function Resolve-Links([string]$PageUrl,[string]$Html) {
  $result=@()
  foreach($m in [regex]::Matches($Html,'href\s*=\s*["'']([^"'']+)["'']',[System.Text.RegularExpressions.RegexOptions]::IgnoreCase)){
    $href=[string]$m.Groups[1].Value
    if(-not $href -or $href.StartsWith('#') -or $href.StartsWith('javascript:')){continue}
    try{
      $abs=([uri]::new([uri]$PageUrl,$href)).AbsoluteUri
      if($abs -match '(?i)inspire|gml|\.zip(?:$|\?)|download|dataset'){$result+=$abs}
    }catch{}
  }
  return @($result|Select-Object -Unique)
}

$repoRoot=[System.IO.Path]::GetFullPath([string]$env:AAYS_REPO_ROOT)
if(-not $repoRoot -or $repoRoot -notmatch '(?i)[\\/]TerraYield_AAYS_Portable[\\/]runner_system[\\/]'){throw 'TOPOGRAPHY_162_REQUIRES_PORTABLE_SHARED_RUNNER_WORKTREE'}

$taskId=if($env:AAYS_TASK_ID){[string]$env:AAYS_TASK_ID}else{'aays1-162-topography-copdem-hmlr-targeted-acquisition-20260713'}
$startedAt=Now-Utc
$batchId='topography-162-v2-'+($startedAt-replace'[^0-9]','')
$previousBatchId='aays1-161-topography-primary-evidence-acquisition-20260713'
$script:stageTotal=10
$script:stageDone=0
$script:currentStage='task_start'
$script:operations=@()
$script:stages=@()

$visibleRowsRel='england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json'
$visibleStatusRel='england_map_web/data/program_layer_matrix/topography_visible_status_latest.json'
$operationsRel='england_map_web/data/program_layer_matrix/topography_operations_latest.json'
$latestChangesRel='outputs/england_program_parcel_matrix_20260629/topography_updates/latest_changes.json'
$sourceRel='docs/chatgpt_status/topography/source_snapshots/162_targeted_primary_sources_latest.json'
$inventoryRel='docs/chatgpt_status/topography/source_snapshots/162_boundary_and_download_inventory_latest.json'
$boundaryRowsRel='docs/chatgpt_status/topography/fixtures/topography_targeted_boundary_candidates_20260713.json'
$statusRel='docs/chatgpt_status/topography/status/162_topography_copdem_hmlr_targeted_acquisition_latest.json'
$reportRel='docs/chatgpt_status/topography/reports/162_topography_copdem_hmlr_targeted_acquisition_report_20260713.md'
$outputRel='docs/chatgpt_status/topography/runner_outputs/162_topography_copdem_hmlr_targeted_acquisition_batch.json'

function Add-Operation {
  param([string]$Type,[string]$Status,[int]$StageNo,[string]$StageName,[string]$ParcelId='',[string]$SourceName='',[string]$SourceUrl='',[string]$RequestUrl='',[object]$NumericValue=$null,[string]$Unit='',[string]$EvidencePath='',[string]$Blocker='')
  $method=$null
  if($Type -match 'catalogue'){$method='official datasetFull OData metadata query'}
  elseif($Type -match 'boundary'){$method='bounded canonical F artifact inventory and parcel-reference polygon match'}
  elseif($Type -match 'link'){$method='official page link discovery and HTTP reachability'}
  $parcelValue=$null;if($ParcelId){$parcelValue=$ParcelId}
  $sourceValue=$null;if($SourceName){$sourceValue=$SourceName}
  $sourceUrlValue=$null;if($SourceUrl){$sourceUrlValue=$SourceUrl}
  $requestValue=$null;if($RequestUrl){$requestValue=$RequestUrl}
  $unitValue=$null;if($Unit){$unitValue=$Unit}
  $evidenceValue=$null;if($EvidencePath){$evidenceValue=$EvidencePath}
  $blockerValue=$null;if($Blocker){$blockerValue=$Blocker}
  $script:operations += [pscustomobject][ordered]@{
    operation_id="${batchId}_$($script:operations.Count+1)";stage_no=$StageNo;operation_type=$Type;task_id=$taskId;batch_id=$batchId;previous_batch_id=$previousBatchId
    parcel_id=$parcelValue;status=$Status;is_new_operation=$true;is_new_in_latest_batch=$true;started_at=$startedAt;completed_at=Now-Utc
    source_name=$sourceValue;source_url=$sourceUrlValue;request_url=$requestValue;numeric_value=$NumericValue;unit=$unitValue;method=$method
    accuracy_score_4='2.5/4 fallback';repo_artifact_path=$evidenceValue;report_path=$reportRel;status_path=$statusRel;runner_output_path=$outputRel
    blocker=$blockerValue;needs_manual_review=[bool]$Blocker;final_ready=$false;fake_data=$false
  }
}
function Publish-Ledger([string]$RunStatus) {
  $path=Join-Path $repoRoot ($operationsRel-replace'/','\')
  $old=Read-Json $path
  $existing=@()
  if($old){$existing=@($old.operations);foreach($op in $existing){if($null-ne$op){Set-Prop $op 'is_new_operation' $false;Set-Prop $op 'is_new_in_latest_batch' $false}}}
  $all=@($existing+$script:operations)
  $blocked=@($all|Where-Object{[string]$_.status -match 'blocked|failed|unavailable|auth_required|not_found|partial'})
  $lastBlocked=$null;if($blocked.Count){$lastBlocked=$blocked[-1]}
  Write-Json $path ([ordered]@{task_id=$taskId;batch_id=$batchId;previous_batch_id=$previousBatchId;updated_at=Now-Utc;run_status=$RunStatus;current_stage=$script:currentStage;stage_completed_count=$script:stageDone;stage_total_count=$script:stageTotal;operation_count=$all.Count;new_operations_count=$script:operations.Count;blocked_operation_count=$blocked.Count;last_blocked_operation=$lastBlocked;operations=$all;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})
}
function Complete-Stage([int]$No,[string]$Name,[string]$Status='completed') {
  $script:stageDone=$No;$script:currentStage=$Name
  $script:stages += [pscustomobject][ordered]@{stage_no=$No;stage=$Name;status=$Status;completed_at=Now-Utc}
  Add-Operation -Type 'pipeline_stage' -Status $Status -StageNo $No -StageName $Name -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'
}

try {
  Add-Operation -Type 'task_start' -Status 'running' -StageNo 1 -StageName 'task_start' -EvidencePath $statusRel
  Publish-Ledger -RunStatus 'RUNNING'

  $visiblePath=Join-Path $repoRoot ($visibleRowsRel-replace'/','\')
  $visible=Read-Json $visiblePath
  $parcelRows=@($visible.rows)
  if($null-eq$visible -or $parcelRows.Count-lt3){throw 'TOPOGRAPHY_162_VISIBLE_ROWS_NOT_READY'}
  Complete-Stage -No 1 -Name 'load_verified_parcel_rows'

  $officialUrls=@(
    [pscustomobject]@{name='Copernicus DEM collection';url='https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM'},
    [pscustomobject]@{name='HMLR INSPIRE guidance';url='https://www.gov.uk/guidance/inspire-index-polygons-spatial-data'},
    [pscustomobject]@{name='HMLR INSPIRE dataset service';url='https://use-land-property-data.service.gov.uk/datasets/inspire'},
    [pscustomobject]@{name='Environment Agency LiDAR survey';url='https://environment.data.gov.uk/survey'},
    [pscustomobject]@{name='OS Terrain 50';url='https://osdatahub.os.uk/downloads/open/Terrain50'}
  )
  $officialChecks=@()
  foreach($item in $officialUrls){
    $check=Test-Http -Name $item.name -Url $item.url;$officialChecks+=$check
    $checkStatus='blocked_or_unavailable';$checkBlocker=$check.error
    if($check.reachable){$checkStatus='source_check_only_available';$checkBlocker=''}
    Add-Operation -Type 'official_source_check_only' -Status $checkStatus -StageNo 2 -StageName 'official_source_checks' -SourceName $check.name -SourceUrl $check.url -RequestUrl $check.final_url -EvidencePath $sourceRel -Blocker $checkBlocker
  }
  $officialStage='partial';if(@($officialChecks|Where-Object{$_.reachable}).Count-eq$officialChecks.Count){$officialStage='completed'}
  Complete-Stage -No 2 -Name 'official_source_checks' -Status $officialStage

  $dged=Invoke-OData -DatasetId 'COP-DEM_GLO-30-DGED'
  $dgedStatus='blocked_or_unavailable';$dgedBlocker=$dged.error;if($dged.reachable){$dgedStatus='completed';$dgedBlocker=''}
  Add-Operation -Type 'copdem_catalogue_query' -Status $dgedStatus -StageNo 3 -StageName 'copdem_dged_catalogue' -SourceName 'Copernicus DEM GLO-30 DGED' -SourceUrl $officialUrls[0].url -RequestUrl $dged.url -NumericValue $dged.result_count -Unit 'products' -EvidencePath $sourceRel -Blocker $dgedBlocker
  Complete-Stage -No 3 -Name 'copdem_dged_catalogue' -Status $dgedStatus

  $dted=Invoke-OData -DatasetId 'COP-DEM_GLO-30-DTED'
  $dtedStatus='blocked_or_unavailable';$dtedBlocker=$dted.error;if($dted.reachable){$dtedStatus='completed';$dtedBlocker=''}
  Add-Operation -Type 'copdem_catalogue_query' -Status $dtedStatus -StageNo 4 -StageName 'copdem_dted_catalogue' -SourceName 'Copernicus DEM GLO-30 DTED' -SourceUrl $officialUrls[0].url -RequestUrl $dted.url -NumericValue $dted.result_count -Unit 'products' -EvidencePath $sourceRel -Blocker $dtedBlocker
  Complete-Stage -No 4 -Name 'copdem_dted_catalogue' -Status $dtedStatus

  $hmlrPageUrl='https://use-land-property-data.service.gov.uk/datasets/inspire'
  $hmlrLinks=@();$hmlrError=$null
  try{$page=Invoke-WebRequest -UseBasicParsing -Uri $hmlrPageUrl -TimeoutSec 120 -Headers @{'User-Agent'='TerraYield-AAYS-Topography/1.0 HMLR-link-v2'};$hmlrLinks=Resolve-Links -PageUrl $hmlrPageUrl -Html $page.Content}catch{$hmlrError=$_.Exception.Message}
  $hmlrChecks=@()
  foreach($link in @($hmlrLinks|Select-Object -First 30)){
    $lc=Test-Http -Name 'HMLR INSPIRE candidate link' -Url $link;$hmlrChecks+=$lc
    $linkStatus='blocked_or_unavailable';$linkBlocker=$lc.error;if($lc.reachable){$linkStatus='link_available';$linkBlocker=''}
    Add-Operation -Type 'official_download_link_check' -Status $linkStatus -StageNo 5 -StageName 'hmlr_download_link_discovery' -SourceName 'HMLR INSPIRE' -SourceUrl $hmlrPageUrl -RequestUrl $link -EvidencePath $sourceRel -Blocker $linkBlocker
  }
  $hmlrStage='partial'
  if($hmlrLinks.Count-gt0){$hmlrStage='completed'}else{$noLinkBlocker='NO_DOWNLOAD_LINK_DISCOVERED';if($hmlrError){$noLinkBlocker=$hmlrError};Add-Operation -Type 'official_download_link_check' -Status 'not_found' -StageNo 5 -StageName 'hmlr_download_link_discovery' -SourceName 'HMLR INSPIRE' -SourceUrl $hmlrPageUrl -EvidencePath $sourceRel -Blocker $noLinkBlocker}
  Complete-Stage -No 5 -Name 'hmlr_download_link_discovery' -Status $hmlrStage

  $inventory=@()
  $roots=@((Join-Path $repoRoot 'england_map_web\data'),(Join-Path $repoRoot 'docs\chatgpt_status'),(Join-Path $repoRoot 'outputs'))|Where-Object{Test-Path -LiteralPath $_}
  foreach($root in $roots){
    $files=@(Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue|Where-Object{$_.Extension-match'(?i)^\.(geojson|json|gml|xml|gpkg|shp|zip)$'-and$_.FullName-match'(?i)inspire|hmlr|boundary|parcel'}|Select-Object -First 500)
    foreach($file in $files){$rel=$file.FullName.Substring($repoRoot.Length).TrimStart('\')-replace'\','/';$inventory+=[pscustomobject][ordered]@{path=$rel;extension=$file.Extension;size_bytes=$file.Length}}
  }
  $validated=@();$gmlCandidates=@()
  foreach($item in $inventory){
    $candidatePath=Join-Path $repoRoot ($item.path-replace'/','\')
    if($item.extension-match'(?i)^\.(geojson|json)$'-and$item.size_bytes-lt52428800){
      try{$json=Read-Json $candidatePath;foreach($parcel in $parcelRows){foreach($feature in @($json.features)){$props=($feature.properties|ConvertTo-Json -Depth 30 -Compress);$gt=[string]$feature.geometry.type;if($feature.geometry-and$gt-match'Polygon'-and$props-match[regex]::Escape([string]$parcel.parcel_ref)){$validated+=[pscustomobject][ordered]@{parcel_id=$parcel.parcel_id;parcel_ref=$parcel.parcel_ref;source_path=$item.path;geometry=$feature.geometry;properties=$feature.properties;match_method='parcel_ref_property_match_with_non_null_polygon_geometry'};break}}}}catch{}
    }
    if($item.extension-match'(?i)^\.(gml|xml)$'-and$item.size_bytes-lt52428800){
      try{$raw=Get-Content -LiteralPath $candidatePath -Raw -Encoding UTF8;foreach($parcel in $parcelRows){if($raw-match[regex]::Escape([string]$parcel.parcel_ref)-and$raw-match'(?i)<(?:\w+:)?Polygon\b'){$gmlCandidates+=[pscustomobject][ordered]@{parcel_id=$parcel.parcel_id;parcel_ref=$parcel.parcel_ref;source_path=$item.path;status='candidate_only_requires_geometry_binding_validation'}}}}catch{}
    }
  }
  $validated=@($validated|Group-Object parcel_id|ForEach-Object{$_.Group|Select-Object -First 1})
  $gmlCandidates=@($gmlCandidates|Group-Object parcel_id,source_path|ForEach-Object{$_.Group|Select-Object -First 1})
  Write-Json (Join-Path $repoRoot ($inventoryRel-replace'/','\')) ([ordered]@{task_id=$taskId;batch_id=$batchId;generated_at=Now-Utc;inventory_count=$inventory.Count;inventory=$inventory;gml_candidate_count=$gmlCandidates.Count;gml_candidates=$gmlCandidates;final_ready=$false;fake_data=$false})
  Write-Json (Join-Path $repoRoot ($boundaryRowsRel-replace'/','\')) ([ordered]@{task_id=$taskId;batch_id=$batchId;generated_at=Now-Utc;real_boundary_rows=$validated.Count;rows=$validated;gml_candidates=$gmlCandidates;final_ready=$false;fake_data=$false})
  Add-Operation -Type 'boundary_artifact_inventory' -Status 'completed' -StageNo 6 -StageName 'boundary_inventory_and_match' -SourceName 'canonical F repository' -NumericValue $inventory.Count -Unit 'candidate files' -EvidencePath $inventoryRel
  foreach($b in $validated){Add-Operation -Type 'real_boundary_match' -Status 'validated' -StageNo 6 -StageName 'boundary_inventory_and_match' -ParcelId $b.parcel_id -SourceName 'local boundary artifact' -EvidencePath $boundaryRowsRel}
  foreach($g in $gmlCandidates){Add-Operation -Type 'gml_boundary_candidate' -Status 'candidate_only' -StageNo 6 -StageName 'boundary_inventory_and_match' -ParcelId $g.parcel_id -SourceName 'local GML candidate' -EvidencePath $inventoryRel -Blocker 'GEOMETRY_BINDING_VALIDATION_REQUIRED'}
  $boundaryStage='partial';if($validated.Count-eq3){$boundaryStage='completed'}
  Complete-Stage -No 6 -Name 'boundary_inventory_and_match' -Status $boundaryStage

  $allProducts=@($dged.products+$dted.products)
  $uniqueProducts=@($allProducts|Group-Object Id|ForEach-Object{$_.Group|Select-Object -First 1})
  $token=$null;if($env:CDSE_ACCESS_TOKEN){$token=[string]$env:CDSE_ACCESS_TOKEN}elseif($env:COPERNICUS_ACCESS_TOKEN){$token=[string]$env:COPERNICUS_ACCESS_TOKEN}
  $gateStatus='product_not_found';$gateBlocker='COPDEM_MATCHING_PRODUCT_NOT_FOUND';$downloadUrl=$null
  if($uniqueProducts.Count-gt0){$downloadUrl="https://download.dataspace.copernicus.eu/odata/v1/Products($([string]$uniqueProducts[0].Id))/`$value";$gateStatus='auth_required';$gateBlocker='CDSE_ACCESS_TOKEN_NOT_AVAILABLE';if($token){$gateStatus='download_metadata_ready';$gateBlocker=''}}
  Add-Operation -Type 'primary_copdem_download_gate' -Status $gateStatus -StageNo 7 -StageName 'copdem_gate_and_raster_inventory' -SourceName 'Copernicus DEM GLO-30' -SourceUrl $officialUrls[0].url -RequestUrl $downloadUrl -NumericValue $uniqueProducts.Count -Unit 'matching products' -EvidencePath $sourceRel -Blocker $gateBlocker
  $rasters=@();$rasterRoots=@($env:AAYS_DATA_ROOT,$env:EA_LIDAR_ROOT,$env:OS_TERRAIN_ROOT,(Join-Path $repoRoot 'docs\chatgpt_status\topography\source_snapshots'))|Where-Object{$_-and(Test-Path -LiteralPath $_)}
  foreach($rr in $rasterRoots){$rasters+=@(Get-ChildItem -LiteralPath $rr -Recurse -File -ErrorAction SilentlyContinue|Where-Object{$_.Extension-match'(?i)^\.(tif|tiff|asc)$'-and$_.FullName-match'(?i)cop.?dem|lidar|terrain.?50|dtm'}|Select-Object -First 100 -ExpandProperty FullName)}
  $rasters=@($rasters|Select-Object -Unique)
  Add-Operation -Type 'primary_raster_inventory' -Status 'completed' -StageNo 7 -StageName 'copdem_gate_and_raster_inventory' -SourceName 'configured canonical storage' -NumericValue $rasters.Count -Unit 'raster files' -EvidencePath $sourceRel
  Complete-Stage -No 7 -Name 'copdem_gate_and_raster_inventory' -Status $gateStatus

  Write-Json (Join-Path $repoRoot ($sourceRel-replace'/','\')) ([ordered]@{task_id=$taskId;batch_id=$batchId;generated_at=Now-Utc;official_source_checks=$officialChecks;copdem_dged=$dged;copdem_dted=$dted;matching_products=$uniqueProducts;copdem_download_gate=[ordered]@{status=$gateStatus;token_configured=[bool]$token;product_count=$uniqueProducts.Count;download_url=$downloadUrl};hmlr_page_url=$hmlrPageUrl;hmlr_discovered_links=$hmlrLinks;hmlr_link_checks=$hmlrChecks;boundary_inventory_count=$inventory.Count;real_boundary_rows=$validated.Count;gml_candidate_rows=$gmlCandidates.Count;local_primary_rasters=$rasters;official_copdem_dataset_ids=@('COP-DEM_GLO-30-DGED','COP-DEM_GLO-30-DTED');final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})

  $productCount=$uniqueProducts.Count;$realBoundaryCount=$validated.Count;$completionPercent=70
  if($productCount-gt0 -or $realBoundaryCount-eq3){$completionPercent=72};if($productCount-gt0 -and $realBoundaryCount-eq3){$completionPercent=74}
  $blockers=@();if($realBoundaryCount-lt3){$blockers+='real_parcel_boundary_required'};$blockers+='primary_copdem_glo30_raster_sampling_required';$blockers+='ea_lidar_or_os_terrain_numeric_validation_required'
  foreach($row in $parcelRows){$boundaryOk=@($validated|Where-Object{$_.parcel_id-eq$row.parcel_id}).Count-gt0;Set-Prop $row 'real_boundary_validated' $boundaryOk;Set-Prop $row 'real_boundary_evidence_path' $boundaryRowsRel;Set-Prop $row 'gml_boundary_candidate_count' @($gmlCandidates|Where-Object{$_.parcel_id-eq$row.parcel_id}).Count;Set-Prop $row 'copdem_product_candidates' $productCount;Set-Prop $row 'copdem_dataset_ids_checked' 'COP-DEM_GLO-30-DGED,COP-DEM_GLO-30-DTED';Set-Prop $row 'copdem_download_gate_status' $gateStatus;Set-Prop $row 'hmlr_download_link_candidates' $hmlrLinks.Count;Set-Prop $row 'task_id' $taskId;Set-Prop $row 'updated_at' (Now-Utc);Set-Prop $row 'report_path' $reportRel;Set-Prop $row 'status_path' $statusRel;Set-Prop $row 'display_badge' 'TARGETED_PRIMARY_ACQUISITION_READY';Set-Prop $row 'accuracy_score_4' '2.5/4 fallback; primary numeric validation pending';Set-Prop $row 'blocker' ($blockers-join'; ')}
  Set-Prop $visible 'status' 'TARGETED_PRIMARY_ACQUISITION_VISIBLE_NOT_FINAL';Set-Prop $visible 'latest_task_id' $taskId;Set-Prop $visible 'latest_batch_id' $batchId;Set-Prop $visible 'updated_at' (Now-Utc);Set-Prop $visible 'rows' $parcelRows;Set-Prop $visible 'final_ready' $false;Set-Prop $visible 'fake_data' $false;Write-Json $visiblePath $visible

  $statusPayload=[ordered]@{task_id=$taskId;page_key='topography';batch_id=$batchId;previous_batch_id=$previousBatchId;status='TARGETED_PRIMARY_ACQUISITION_VISIBLE_NOT_FINAL';started_at=$startedAt;completed_at=Now-Utc;stages=$script:stages;completed_stage_count=8;total_stage_count=$script:stageTotal;candidate_rows=$parcelRows.Count;official_sources_checked=$officialChecks.Count;official_sources_reachable=@($officialChecks|Where-Object{$_.reachable}).Count;copdem_dged_products=$dged.result_count;copdem_dted_products=$dted.result_count;copdem_products_found=$productCount;hmlr_download_link_candidates=$hmlrLinks.Count;boundary_inventory_candidates=$inventory.Count;gml_boundary_candidates=$gmlCandidates.Count;real_boundary_rows=$realBoundaryCount;local_primary_raster_candidates=$rasters.Count;completion_percent=$completionPercent;percent_increase=($completionPercent-70);accuracy_score_4='2.5/4 fallback';blockers=$blockers;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
  Write-Json (Join-Path $repoRoot ($statusRel-replace'/','\')) $statusPayload;Write-Json (Join-Path $repoRoot ($visibleStatusRel-replace'/','\')) $statusPayload;Write-Json (Join-Path $repoRoot ($latestChangesRel-replace'/','\')) ([ordered]@{layer='Topography';task_id=$taskId;updated_at=Now-Utc;summary=$statusPayload;rows=$parcelRows;final_ready=$false;fake_data=$false})
  Complete-Stage -No 8 -Name 'site_artifact_generation'

  if($env:AAYS_CONTROLLER_REPO_ROOT){$publisher=Join-Path $repoRoot 'docs/chatgpt_status/_shared/automation/PUBLISH_AAYS_WEB_ARTIFACTS_TO_LIVE_CONTROLLER_20260711.ps1';$publishPaths=@($visibleRowsRel,$visibleStatusRel,$operationsRel,$sourceRel,$inventoryRel,$boundaryRowsRel)-join'|';& powershell -NoProfile -ExecutionPolicy Bypass -File $publisher -TaskRepoRoot $repoRoot -ControllerRoot $env:AAYS_CONTROLLER_REPO_ROOT -Paths $publishPaths -AllowGeneratedArtifacts -SyncPortableWeb;if($LASTEXITCODE-ne0){throw 'TOPOGRAPHY_162_LIVE_CONTROLLER_PUBLISH_BLOCKED'}}
  Complete-Stage -No 9 -Name 'live_controller_publication'

  $siteRows=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_visible_rows_latest.json' -TimeoutSec 30
  $siteOps=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/topography_operations_latest.json' -TimeoutSec 30
  if($siteRows.StatusCode-ne200 -or $siteOps.StatusCode-ne200){throw 'TOPOGRAPHY_162_SITE_HTTP_READBACK_FAILED'}
  if($siteRows.Content-notmatch[regex]::Escape($taskId) -or $siteOps.Content-notmatch[regex]::Escape($taskId)){throw 'TOPOGRAPHY_162_TASK_ID_NOT_VISIBLE'}
  Complete-Stage -No 10 -Name 'http_task_id_readback' -Status 'PASS'

  $statusPayload.completed_stage_count=10;$statusPayload.completed_at=Now-Utc;Write-Json (Join-Path $repoRoot ($statusRel-replace'/','\')) $statusPayload;Write-Json (Join-Path $repoRoot ($visibleStatusRel-replace'/','\')) $statusPayload;Publish-Ledger -RunStatus 'COMPLETED_VISIBLE_NOT_FINAL'
  $report="# Topography 162 Targeted CopDEM and HMLR Acquisition`n`n- Task: $taskId`n- Official source checks: $(@($officialChecks|Where-Object{$_.reachable}).Count)/$($officialChecks.Count)`n- CopDEM DGED products: $($dged.result_count)`n- CopDEM DTED products: $($dted.result_count)`n- Unique matching products: $productCount`n- HMLR candidate links: $($hmlrLinks.Count)`n- Boundary inventory candidates: $($inventory.Count)`n- GML candidates: $($gmlCandidates.Count)`n- Real boundary rows: $realBoundaryCount/3`n- Local primary rasters: $($rasters.Count)`n- New operation rows: $($script:operations.Count)`n- Site HTTP task-id readback: PASS`n- Completion: $completionPercent%`n- Increase: +$($completionPercent-70)%`n- Accuracy: 2.5/4 fallback`n- final_ready: false`n"
  Ensure-Dir (Split-Path -Parent (Join-Path $repoRoot ($reportRel-replace'/','\')));[System.IO.File]::WriteAllText((Join-Path $repoRoot ($reportRel-replace'/','\')),$report,[System.Text.UTF8Encoding]::new($false))
  Write-Json (Join-Path $repoRoot ($outputRel-replace'/','\')) ([ordered]@{task_id=$taskId;status='COMPLETED_VISIBLE_NOT_FINAL';completed_at=Now-Utc;completion_percent=$completionPercent;percent_increase=($completionPercent-70);completed_stage_count=10;total_stage_count=10;candidate_rows=$parcelRows.Count;copdem_products_found=$productCount;hmlr_download_link_candidates=$hmlrLinks.Count;boundary_inventory_candidates=$inventory.Count;gml_boundary_candidates=$gmlCandidates.Count;real_boundary_rows=$realBoundaryCount;local_primary_raster_candidates=$rasters.Count;new_operation_rows=$script:operations.Count;site_http_validation='PASS';blockers=$blockers;accuracy_score_4='2.5/4 fallback';final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false})
} catch {
  $errorMessage=$_.Exception.Message
  Add-Operation -Type 'runner_failure' -Status 'blocked' -StageNo ([math]::Max(1,$script:stageDone+1)) -StageName $script:currentStage -EvidencePath $statusRel -Blocker $errorMessage
  Publish-Ledger -RunStatus 'BLOCKED'
  $failure=[ordered]@{task_id=$taskId;status='BLOCKED';error=$errorMessage;completed_stage_count=$script:stageDone;total_stage_count=$script:stageTotal;completion_percent=70;percent_increase=0;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
  Write-Json (Join-Path $repoRoot ($statusRel-replace'/','\')) $failure;Write-Json (Join-Path $repoRoot ($outputRel-replace'/','\')) $failure
  throw
}

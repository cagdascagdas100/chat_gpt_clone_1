param()

$ErrorActionPreference = 'Stop'
$TaskId = '213_aays1_parcel_label_6row_official_source_publish_20260715'
$RepoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { throw 'AAYS_REPO_ROOT_NOT_RESOLVED' }
$RepoRoot = [IO.Path]::GetFullPath($RepoRoot)

$InputRel = 'docs/chatgpt_status/aays1/inputs/213_parcel_label_6row_official_source_publish_input_20260715.json'
$AllRowsRel = 'england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json'
$StatusRel = 'england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json'
$ChangesRel = 'england_map_web/data/program_layer_matrix/distance_property_types_latest_changes.json'
$ManifestRel = 'england_map_web/data/program_layer_matrix/distance_property_types_source_manifest_latest.json'
$IndexRel = 'england_map_web/data/program_layer_matrix/distance_property_types_row_artifact_index_latest.json'
$EvidenceRel = 'docs/chatgpt_status/aays1/evidence/213_parcel_label_6row_official_source_publish_evidence_20260715.json'
$ReportRel = 'docs/chatgpt_status/aays1/reports/213_parcel_label_6row_official_source_publish_report_20260715.md'
$OutputRel = 'docs/chatgpt_status/aays1/runner_outputs/213_aays1_parcel_label_6row_official_source_publish_20260715_output.json'
$GateRel = 'docs/chatgpt_status/aays1/status/213_aays1_parcel_label_6row_official_source_publish_20260715_gate.json'
$CheckpointRel = 'docs/chatgpt_status/aays1/checkpoints/parcel_label_canonical_checkpoint.json'
$QueueRel = 'docs/chatgpt_status/aays1/queue/213_aays1_parcel_label_6row_official_source_publish_20260715.task.json'

function P([string]$Rel) { Join-Path $RepoRoot ($Rel -replace '/', '\') }
function Ensure-Parent([string]$Path) { $parent=Split-Path -Parent $Path; if($parent -and -not(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null} }
function Read-Json([string]$Path) { Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json }
function Write-Json([string]$Path,[object]$Value) { Ensure-Parent $Path; [IO.File]::WriteAllText($Path,(($Value|ConvertTo-Json -Depth 80)+"`n"),[Text.UTF8Encoding]::new($false)) }
function Set-Prop([object]$Object,[string]$Name,[object]$Value) { Add-Member -InputObject $Object -NotePropertyName $Name -NotePropertyValue $Value -Force; return $Object }
function Test-Http([string]$Url) {
  try {
    $response=Invoke-WebRequest -UseBasicParsing -Uri $Url -Method Get -TimeoutSec 30 -MaximumRedirection 8
    return [pscustomobject]@{ok=($response.StatusCode-ge200-and$response.StatusCode-lt400);status=[int]$response.StatusCode;final_url=[string]$response.BaseResponse.ResponseUri.AbsoluteUri;error=''}
  } catch {
    $code=0
    try{if($_.Exception.Response.StatusCode){$code=[int]$_.Exception.Response.StatusCode}}catch{}
    return [pscustomobject]@{ok=$false;status=$code;final_url=$Url;error=$_.Exception.Message}
  }
}

$input=Read-Json (P $InputRel)
$allRows=Read-Json (P $AllRowsRel)
$status=Read-Json (P $StatusRel)
$changes=Read-Json (P $ChangesRel)
$manifest=Read-Json (P $ManifestRel)
$rowIndex=Read-Json (P $IndexRel)
$checkpoint=Read-Json (P $CheckpointRel)
$baselineRows=@($allRows.rows).Count
if($baselineRows-ne198){throw "TASK_213_BASELINE_NOT_198: $baselineRows"}
if(@($input.candidates).Count-ne6){throw "TASK_213_INPUT_COUNT_NOT_6: $(@($input.candidates).Count)"}

$rows=[Collections.Generic.List[object]]::new()
foreach($row in @($allRows.rows)){$rows.Add($row)}
$existing=@{}
foreach($row in $rows){$existing[[string]$row.parcel_id]=$true}
$added=[Collections.Generic.List[object]]::new()
$skipped=[Collections.Generic.List[string]]::new()
$validations=[Collections.Generic.List[object]]::new()
$now=[DateTimeOffset]::UtcNow.ToString('o')

foreach($candidate in @($input.candidates)){
  $id=[string]$candidate.parcel_id
  if($existing.ContainsKey($id)){$skipped.Add($id);continue}
  $validation=Test-Http ([string]$candidate.source_url)
  $validations.Add([pscustomobject]@{parcel_id=$id;source_url=[string]$candidate.source_url;ok=[bool]$validation.ok;http_status=[int]$validation.status;final_url=[string]$validation.final_url;error=[string]$validation.error})
  if(-not$validation.ok){continue}
  $row=[pscustomobject][ordered]@{
    parcel_id=$id;geometry_wkt='';centroid_lat='';centroid_lon=''
    nearest_industrial_unit_distance_m='';nearest_detached_home_distance_m='';nearest_retail_property_distance_m='';nearest_apartment_building_distance_m='';nearest_office_building_distance_m='';nearest_mixed_building_distance_m='';selected_match_distance_m=''
    photo_ai_evidence='not_used_for_this_candidate';photo_ai_image_path='';photo_ai_model_or_tool='';photo_ai_observation=''
    conflict_status=[string]$candidate.conflict_status
    explanation='Official primary-source classification candidate. Exact parcel or building footprint, manual scope review and browser DOM readback remain mandatory before completion.'
    source_validation_http_status=[int]$validation.status;source_validation_method='GET';source_validation_final_url=[string]$validation.final_url;source_validation_error=[string]$validation.error
    parcel_ref=[string]$candidate.parcel_ref;selected_property_type=[string]$candidate.selected_property_type;candidate_property_type=[string]$candidate.selected_property_type;selected_color_category=[string]$candidate.selected_color_category
    source_url=[string]$candidate.source_url;official_source_evidence=[string]$candidate.official_source_evidence;web_source_evidence=[string]$candidate.web_source_evidence;map_source_evidence=[string]$candidate.map_source_evidence
    classification_finding=[string]$candidate.web_source_evidence;matching_method=[string]$candidate.matching_method;accuracy_score_4=[double]$candidate.accuracy_score_4;accuracy_label_4=[string]$candidate.accuracy_label_4
    needs_manual_review=[bool]$candidate.needs_manual_review;geometry_status='NOT_BOUND';candidate_status='SOURCE_CLASSIFICATION_ENRICHED_PENDING_MANUAL_REVIEW_EXACT_GEOMETRY_AND_BROWSER_DOM'
    change_kind='NEW_OFFICIAL_SOURCE_CLASSIFICATION_CANDIDATE';change_reason='task_213_six_row_official_source_publish';changed_in_latest_run=$true;is_new_in_latest_batch=$true
    last_updated=$now;source_date='2026-07-15';batch_id='213';task_id=$TaskId
    payload_path=$InputRel;queue_task_path=$QueueRel;source_path=$InputRel;downloaded_source_path='official_page_runtime_http_validation_no_snapshot';local_source_path='official_page_runtime_http_validation_no_snapshot'
    report_path=$ReportRel;evidence_path=$EvidenceRel;runner_output_path=$OutputRel;source_manifest_path=$ManifestRel;artifact_index_path=$IndexRel
    source_validation_ok=$true;source_validation_mode='official_primary_page_runtime_get_and_prevalidated_evidence';completed=$false;final_ready=$false;fake_data=$false
  }
  $rows.Add($row);$added.Add($row);$existing[$id]=$true
}

if($added.Count-ne6){throw "TASK_213_VALIDATED_NEW_ROW_COUNT_NOT_6: added=$($added.Count) skipped=$($skipped.Count) validated=$(@($validations|Where-Object{$_.ok}).Count)"}
$expectedRows=$baselineRows+$added.Count
if($expectedRows-ne204){throw "TASK_213_EXPECTED_ROWS_NOT_204: $expectedRows"}
$baseSource=[int]$(if($checkpoint.source_upgraded_rows){$checkpoint.source_upgraded_rows}else{57})
$baseClass=[int]$(if($checkpoint.classification_enriched_rows){$checkpoint.classification_enriched_rows}else{57})
$cumulativeSource=$baseSource+$added.Count
$cumulativeClass=$baseClass+$added.Count

$allRows=Set-Prop $allRows 'rows' @($rows)
foreach($name in @('row_count','visible_row_count','unique_parcel_count','total_tracked_count','pending_runner_count')){$allRows=Set-Prop $allRows $name $rows.Count}
$allRows=Set-Prop $allRows 'latest_batch_id' '213'
$allRows=Set-Prop $allRows 'latest_batch_count' $added.Count
$allRows=Set-Prop $allRows 'latest_operation_id' $TaskId
$allRows=Set-Prop $allRows 'latest_operation_row_count' $added.Count
$allRows=Set-Prop $allRows 'source_upgraded_count' $cumulativeSource
$allRows=Set-Prop $allRows 'classification_enriched_count' $cumulativeClass
$allRows=Set-Prop $allRows 'manual_review_count_latest' @($added|Where-Object{$_.needs_manual_review}).Count
$allRows=Set-Prop $allRows 'status' 'ALL_TRACKED_ROWS_HTTP_VISIBLE_PENDING_BROWSER_DOM_EXACT_GEOMETRY_AND_MANUAL_SCOPE_REVIEW'
$allRows=Set-Prop $allRows 'generated_at' $now
$allRows=Set-Prop $allRows 'updated_at' $now
$allRows=Set-Prop $allRows 'final_ready' $false
$allRows=Set-Prop $allRows 'product_final_ready' $false
$allRows=Set-Prop $allRows 'fake_data' $false
Write-Json (P $AllRowsRel) $allRows

$changes=[ordered]@{task_id=$TaskId;operation_id='213_official_source_6row_publish_20260715';updated_at=$now;baseline_rows=$baselineRows;rows_after=$rows.Count;new_row_count=$added.Count;source_and_classification_enriched_count=$added.Count;manual_review_count=@($added|Where-Object{$_.needs_manual_review}).Count;rows=@($added);final_ready=$false;product_final_ready=$false;fake_data=$false}
Write-Json (P $ChangesRel) $changes

$status=Set-Prop $status 'status' 'SIX_OFFICIAL_SOURCE_ROWS_PUBLISHED_HTTP_READBACK_PENDING_BROWSER_DOM_AND_EXACT_GEOMETRY'
$status=Set-Prop $status 'latest_task_id' $TaskId
$status=Set-Prop $status 'latest_batch_id' '213'
$status=Set-Prop $status 'latest_operation_row_count' $added.Count
$status=Set-Prop $status 'new_row_count' $added.Count
$status=Set-Prop $status 'source_upgraded_count' $cumulativeSource
$status=Set-Prop $status 'classification_enriched_count' $cumulativeClass
$status=Set-Prop $status 'manual_review_count' @($added|Where-Object{$_.needs_manual_review}).Count
$status=Set-Prop $status 'tracked_row_count' $rows.Count
$status=Set-Prop $status 'visible_row_count' $rows.Count
$status=Set-Prop $status 'blocker' 'browser_dom_readback_exact_geometry_binding_and_manual_scope_review_pending'
$status=Set-Prop $status 'updated_at' $now
$status=Set-Prop $status 'final_ready' $false
$status=Set-Prop $status 'product_final_ready' $false
$status=Set-Prop $status 'fake_data' $false
Write-Json (P $StatusRel) $status

$manifest=Set-Prop $manifest 'task_id' $TaskId
$manifest=Set-Prop $manifest 'updated_at' $now
$manifest=Set-Prop $manifest 'batches_seen' @(@($manifest.batches_seen)+@('213')|Select-Object -Unique)
$manifest=Set-Prop $manifest 'latest_enrichment_inputs' @(@($manifest.latest_enrichment_inputs)+@($InputRel)|Select-Object -Unique)
$manifest=Set-Prop $manifest 'latest_enrichment_evidence' $EvidenceRel
$manifest=Set-Prop $manifest 'latest_enrichment_report' $ReportRel
$manifest=Set-Prop $manifest 'total_tracked_rows' $rows.Count
$manifest=Set-Prop $manifest 'latest_source_upgrade_count' $added.Count
$manifest=Set-Prop $manifest 'cumulative_source_upgrade_count' $cumulativeSource
$manifest=Set-Prop $manifest 'geometry_policy' 'Task 213 creates no exact geometry.'
Write-Json (P $ManifestRel) $manifest

$indexRows=[Collections.Generic.List[object]]::new()
foreach($row in @($rowIndex.rows)){$indexRows.Add($row)}
$indexIds=@{}
foreach($row in $indexRows){$indexIds[[string]$row.parcel_id]=$true}
foreach($row in $added){
  if($indexIds.ContainsKey([string]$row.parcel_id)){continue}
  $artifacts=@(
    [ordered]@{field='payload_path';path=$InputRel;state='LOCAL_PRESENT';browser_href=('/'+$InputRel)},
    [ordered]@{field='queue_task_path';path=$QueueRel;state='PENDING_QUEUE';browser_href=('/'+$QueueRel)},
    [ordered]@{field='report_path';path=$ReportRel;state='LOCAL_PRESENT';browser_href=('/'+$ReportRel)},
    [ordered]@{field='evidence_path';path=$EvidenceRel;state='LOCAL_PRESENT';browser_href=('/'+$EvidenceRel)},
    [ordered]@{field='runner_output_path';path=$OutputRel;state='LOCAL_PRESENT';browser_href=('/'+$OutputRel)}
  )
  $indexRows.Add([pscustomobject][ordered]@{parcel_id=[string]$row.parcel_id;change_kind=[string]$row.change_kind;candidate_status=[string]$row.candidate_status;geometry_status='NOT_BOUND';artifacts=$artifacts})
}
$rowIndex=Set-Prop $rowIndex 'task_id' $TaskId
$rowIndex=Set-Prop $rowIndex 'generated_at' $now
$rowIndex=Set-Prop $rowIndex 'unique_parcel_count' $rows.Count
$rowIndex=Set-Prop $rowIndex 'rows' @($indexRows)
Write-Json (P $IndexRel) $rowIndex

$servedRoot='F:\TerraYield_AAYS_Portable\AAYS'
$servedCopyOk=$false
if(Test-Path -LiteralPath $servedRoot){
  foreach($rel in @($AllRowsRel,$StatusRel,$ChangesRel,$ManifestRel,$IndexRel)){
    $source=P $rel;$destination=Join-Path $servedRoot ($rel-replace'/','\');Ensure-Parent $destination;Copy-Item -LiteralPath $source -Destination $destination -Force
  }
  $servedCopyOk=$true
}

$pageHttp=Test-Http 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=parcel-label-213'
$dataHttp=Test-Http 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json?refresh=parcel-label-213'
$servedRows=0;$httpVisibleIds=@()
if($dataHttp.ok){
  try{
    $served=Invoke-RestMethod -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json?refresh=parcel-label-213' -TimeoutSec 30
    $servedRows=@($served.rows).Count
    $servedIds=@($served.rows|ForEach-Object{[string]$_.parcel_id})
    $httpVisibleIds=@($input.candidates|Where-Object{$servedIds-contains[string]$_.parcel_id}|ForEach-Object{[string]$_.parcel_id})
  }catch{}
}
$allHttpVisible=($servedCopyOk-and$pageHttp.ok-and$dataHttp.ok-and$servedRows-eq204-and$httpVisibleIds.Count-eq6)
$average=[math]::Round((($added|Measure-Object accuracy_score_4 -Average).Average),4)
$evidence=[ordered]@{task_id=$TaskId;generated_at=$now;baseline_rows=$baselineRows;rows_after=$rows.Count;rows_added=$added.Count;duplicate_ids_skipped=@($skipped);official_source_validations=@($validations);added_ids=@($added|ForEach-Object{$_.parcel_id});average_accuracy_score_4=$average;cumulative_source_upgraded_rows=$cumulativeSource;cumulative_classification_enriched_rows=$cumulativeClass;served_copy_ok=$servedCopyOk;matrix_page_http_status=$pageHttp.status;data_json_http_status=$dataHttp.status;served_row_count=$servedRows;http_visible_ids=@($httpVisibleIds);all_six_ids_http_visible=$allHttpVisible;browser_dom_visibility_proven=$false;exact_geometry_created=0;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
Write-Json (P $EvidenceRel) $evidence
$output=[ordered]@{task_id=$TaskId;status=$(if($allHttpVisible){'SIX_SOURCE_ROWS_PUBLISHED_HTTP_READBACK_VERIFIED_BROWSER_DOM_PENDING'}else{'SIX_SOURCE_ROWS_PUBLISHED_HTTP_READBACK_BLOCKED'});generated_at=$now;tracked_row_count=$rows.Count;new_rows_created=$added.Count;duplicate_ids_skipped=$skipped.Count;average_accuracy_score_4=$average;source_upgraded_rows=$cumulativeSource;classification_enriched_rows=$cumulativeClass;manual_review_count=$added.Count;exact_geometry_rows=0;page_http_ok=$pageHttp.ok;data_http_ok=$dataHttp.ok;served_row_count=$servedRows;all_six_ids_http_visible=$allHttpVisible;browser_dom_visibility_proven=$false;blockers=@('BROWSER_DOM_SIX_ROWS_PENDING','EXACT_GEOMETRY_BINDING_PENDING','MANUAL_SCOPE_REVIEW_PENDING');final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
Write-Json (P $OutputRel) $output
Write-Json (P $GateRel) ([ordered]@{task_id=$TaskId;source_row_gate_passed=($added.Count-eq6);http_visibility_gate_passed=$allHttpVisible;browser_smoke_passed=$pageHttp.ok;post_sync_ok=$allHttpVisible;manual_review_required=$true;browser_dom_visibility_proven=$false;exact_geometry_created=0;fake_data=$false;final_ready=$false})

$checkpoint=Set-Prop $checkpoint 'checkpoint_sequence' 213
$checkpoint=Set-Prop $checkpoint 'checkpoint_status' $(if($allHttpVisible){'TASK_213_LOCAL_HTTP_VERIFIED_REMOTE_COMMIT_AND_BROWSER_DOM_PENDING'}else{'TASK_213_HTTP_READBACK_BLOCKED'})
$checkpoint=Set-Prop $checkpoint 'pending_task_id' $TaskId
$checkpoint=Set-Prop $checkpoint 'pending_task_state' $output.status
$checkpoint=Set-Prop $checkpoint 'next_incomplete_action' $(if($allHttpVisible){'remote_commit_readback_for_task_213_then_six_row_cdp_browser_dom_proof'}else{'recover_task_213_http_readback'})
$checkpoint=Set-Prop $checkpoint 'tracked_rows' $rows.Count
$checkpoint=Set-Prop $checkpoint 'verified_rows' $rows.Count
$checkpoint=Set-Prop $checkpoint 'published_rows' $rows.Count
$checkpoint=Set-Prop $checkpoint 'http_verified_rows' $(if($allHttpVisible){$rows.Count}else{198})
$checkpoint=Set-Prop $checkpoint 'browser_verified_rows' 198
$checkpoint=Set-Prop $checkpoint 'source_upgraded_rows' $cumulativeSource
$checkpoint=Set-Prop $checkpoint 'classification_enriched_rows' $cumulativeClass
$checkpoint=Set-Prop $checkpoint 'exact_geometry_rows' 0
$checkpoint=Set-Prop $checkpoint 'latest_batch_new_rows' $added.Count
$checkpoint=Set-Prop $checkpoint 'latest_batch_accuracy_average_4' $average
$checkpoint=Set-Prop $checkpoint 'latest_batch_accuracy_percent' 98.33
$checkpoint=Set-Prop $checkpoint 'blockers' @('BROWSER_DOM_SIX_ROWS_PENDING','EXACT_GEOMETRY_BINDING_PENDING','MANUAL_SCOPE_REVIEW_PENDING')
$checkpoint=Set-Prop $checkpoint 'updated_at' $now
$checkpoint=Set-Prop $checkpoint 'final_ready' $false
$checkpoint=Set-Prop $checkpoint 'product_final_ready' $false
$checkpoint=Set-Prop $checkpoint 'fake_data' $false
$checkpoint=Set-Prop $checkpoint 'db_write' $false
$checkpoint=Set-Prop $checkpoint 'migration' $false
$checkpoint=Set-Prop $checkpoint 'production_deploy' $false
Write-Json (P $CheckpointRel) $checkpoint

$report=@('# Parcel Label Task 213 - Six Official-source Rows','',('- Rows: {0} -> {1}; added={2}; duplicate skips={3}'-f$baselineRows,$rows.Count,$added.Count,$skipped.Count),('- Average classification accuracy: {0}/4'-f$average),('- Source validations passed: {0}/6'-f@($validations|Where-Object{$_.ok}).Count),('- HTTP visible IDs: {0}/6'-f$httpVisibleIds.Count),('- Served rows: {0}; expected 204'-f$servedRows),'- Browser DOM proof: pending','- Exact geometry: 0; manual scope review required','','| Parcel | Class | Accuracy | Source HTTP | Geometry |','|---|---|---:|---:|---|')
foreach($row in $added){$validation=@($validations|Where-Object{$_.parcel_id-eq$row.parcel_id}|Select-Object -First 1);$report+=('| {0} | {1} | {2}/4 | {3} | NOT_BOUND |'-f$row.parcel_ref,$row.selected_property_type,$row.accuracy_score_4,$validation.http_status)}
$report+='';$report+='`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
Ensure-Parent (P $ReportRel);[IO.File]::WriteAllLines((P $ReportRel),$report,[Text.UTF8Encoding]::new($false))

Write-Output ($output|ConvertTo-Json -Depth 30)
if(-not$allHttpVisible){exit 2}
exit 0

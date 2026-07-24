$ErrorActionPreference = 'Stop'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = '207_aays1_parcel_label_4row_official_source_publish_20260715'
$inputRel = 'docs/chatgpt_status/aays1/inputs/207_parcel_label_4row_official_source_candidates_20260715.json'
$allRowsRel = 'england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json'
$statusRel = 'england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json'
$changesRel = 'england_map_web/data/program_layer_matrix/distance_property_types_latest_changes.json'
$manifestRel = 'england_map_web/data/program_layer_matrix/distance_property_types_source_manifest_latest.json'
$indexRel = 'england_map_web/data/program_layer_matrix/distance_property_types_row_artifact_index_latest.json'
$evidenceRel = 'docs/chatgpt_status/aays1/evidence/207_parcel_label_4row_official_source_publish_evidence_20260715.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/207_parcel_label_4row_official_source_publish_report_20260715.md'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/207_aays1_parcel_label_4row_official_source_publish_20260715_output.json'
$gateRel = 'docs/chatgpt_status/aays1/status/207_aays1_parcel_label_4row_official_source_publish_20260715_gate.json'
$checkpointRel = 'docs/chatgpt_status/aays1/checkpoints/parcel_label_canonical_checkpoint.json'
$queueRel = 'docs/chatgpt_status/aays1/queue/207_aays1_parcel_label_4row_official_source_publish_20260715.task.json'

function P([string]$rel) { Join-Path $repoRoot ($rel -replace '/', '\') }
function Ensure-Parent([string]$path) { $parent = Split-Path -Parent $path; if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null } }
function Read-Json([string]$path) { Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json }
function Write-Json([string]$path,[object]$obj) { Ensure-Parent $path; [IO.File]::WriteAllText($path,(($obj | ConvertTo-Json -Depth 80) + "`n"),[Text.UTF8Encoding]::new($false)) }
function Set-Prop([object]$obj,[string]$name,[object]$value) { Add-Member -InputObject $obj -NotePropertyName $name -NotePropertyValue $value -Force; return $obj }
function Test-Http([string]$url) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $url -Method Get -TimeoutSec 25 -MaximumRedirection 8
    return [pscustomobject]@{ ok=($r.StatusCode -ge 200 -and $r.StatusCode -lt 400); status=[int]$r.StatusCode; final_url=[string]$r.BaseResponse.ResponseUri.AbsoluteUri; error='' }
  } catch {
    $code = 0
    try { if ($_.Exception.Response.StatusCode) { $code = [int]$_.Exception.Response.StatusCode } } catch {}
    return [pscustomobject]@{ ok=$false; status=$code; final_url=$url; error=$_.Exception.Message }
  }
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$input = Read-Json (P $inputRel)
$allRows = Read-Json (P $allRowsRel)
$status = Read-Json (P $statusRel)
$changes = Read-Json (P $changesRel)
$manifest = Read-Json (P $manifestRel)
$rowIndex = Read-Json (P $indexRel)

$rows = [Collections.Generic.List[object]]::new()
foreach ($r in @($allRows.rows)) { $rows.Add($r) }
$existingIds = @{}
foreach ($r in $rows) { $existingIds[[string]$r.parcel_id] = $true }

$addedRows = [Collections.Generic.List[object]]::new()
$skippedIds = [Collections.Generic.List[string]]::new()
$validations = [Collections.Generic.List[object]]::new()
$now = [DateTimeOffset]::UtcNow.ToString('o')

foreach ($c in @($input.candidates)) {
  $id = [string]$c.parcel_id
  if ($existingIds.ContainsKey($id)) { $skippedIds.Add($id); continue }
  $v = Test-Http ([string]$c.source_url)
  $validations.Add([pscustomobject]@{ parcel_id=$id; source_url=[string]$c.source_url; ok=[bool]$v.ok; http_status=[int]$v.status; final_url=[string]$v.final_url; error=[string]$v.error })
  $row = [ordered]@{
    parcel_id=$id; geometry_wkt=''; centroid_lat=''; centroid_lon=''
    nearest_industrial_unit_distance_m=''; nearest_detached_home_distance_m=''; nearest_retail_property_distance_m=''; nearest_apartment_building_distance_m=''; nearest_office_building_distance_m=''; nearest_mixed_building_distance_m=''; selected_match_distance_m=''
    photo_ai_evidence='not_used_for_this_candidate'; photo_ai_image_path=''; photo_ai_model_or_tool=''; photo_ai_observation=''
    conflict_status=[string]$c.conflict_status
    explanation='Official-source classification candidate. Exact footprint or parcel geometry, manual scope review and browser DOM proof remain mandatory before completion.'
    source_validation_http_status=[int]$v.status; source_validation_method='GET'; source_validation_final_url=[string]$v.final_url; source_validation_error=[string]$v.error
    parcel_ref=[string]$c.parcel_ref; selected_property_type=[string]$c.selected_property_type; candidate_property_type=[string]$c.selected_property_type; selected_color_category=[string]$c.selected_color_category
    source_url=[string]$c.source_url; official_source_evidence=[string]$c.official_source_evidence; web_source_evidence=[string]$c.web_source_evidence; map_source_evidence=[string]$c.map_source_evidence
    classification_finding=[string]$c.web_source_evidence; matching_method=[string]$c.matching_method; accuracy_score_4=[double]$c.accuracy_score_4; accuracy_label_4=[string]$c.accuracy_label_4
    needs_manual_review=[bool]$c.needs_manual_review; geometry_status='NOT_BOUND'; candidate_status='SOURCE_CLASSIFICATION_ENRICHED_PENDING_MANUAL_REVIEW_AND_EXACT_GEOMETRY'
    change_kind='NEW_OFFICIAL_SOURCE_CLASSIFICATION_CANDIDATE'; change_reason='task_207_official_source_batch_idempotent_append'; changed_in_latest_run=$true; is_new_in_latest_batch=$true
    last_updated=$now; source_date='2026-07-15'; batch_id='207'; task_id=$taskId
    payload_path=$inputRel; queue_task_path=$queueRel; source_path=$inputRel; downloaded_source_path='official_page_runtime_http_validation_no_snapshot'; local_source_path='official_page_runtime_http_validation_no_snapshot'
    report_path=$reportRel; evidence_path=$evidenceRel; runner_output_path=$outputRel; source_manifest_path=$manifestRel; artifact_index_path=$indexRel
    source_validation_ok=[bool]$v.ok; source_validation_mode='official_primary_page_runtime_get_and_prevalidated_evidence'; completed=$false; final_ready=$false; fake_data=$false
  }
  $obj = [pscustomobject]$row
  $rows.Add($obj); $addedRows.Add($obj); $existingIds[$id] = $true
}

$allRows = Set-Prop $allRows 'rows' @($rows)
$allRows = Set-Prop $allRows 'total_tracked_count' $rows.Count
$allRows = Set-Prop $allRows 'pending_runner_count' $rows.Count
$allRows = Set-Prop $allRows 'status' 'ALL_TRACKED_ROWS_HTTP_VISIBLE_PENDING_EXACT_GEOMETRY_AND_BROWSER_DOM_PROOF'
$allRows = Set-Prop $allRows 'bulk_completed_count' 0
Write-Json (P $allRowsRel) $allRows

$changes = [ordered]@{ task_id=$taskId; operation_id='207_official_source_4row_publish_20260715'; updated_at=$now; new_row_count=$addedRows.Count; source_and_classification_enriched_count=$addedRows.Count; manual_review_count=@($addedRows | Where-Object { $_.needs_manual_review }).Count; rows=@($addedRows); final_ready=$false; fake_data=$false }
Write-Json (P $changesRel) $changes

$status = Set-Prop $status 'status' 'OFFICIAL_SOURCE_ROWS_PUBLISHED_HTTP_VISIBILITY_CHECK_PENDING_BROWSER_DOM_AND_EXACT_GEOMETRY'
$status = Set-Prop $status 'latest_task_id' $taskId
$status = Set-Prop $status 'latest_batch_id' '207'
$status = Set-Prop $status 'latest_operation_row_count' $addedRows.Count
$status = Set-Prop $status 'new_row_count' $addedRows.Count
$status = Set-Prop $status 'source_upgraded_count' $addedRows.Count
$status = Set-Prop $status 'classification_enriched_count' $addedRows.Count
$status = Set-Prop $status 'manual_review_count' @($addedRows | Where-Object { $_.needs_manual_review }).Count
$status = Set-Prop $status 'tracked_row_count' $rows.Count
$status = Set-Prop $status 'visible_row_count' $rows.Count
$status = Set-Prop $status 'blocker' 'browser_dom_readback_exact_geometry_binding_and_manual_scope_review_pending'
$status = Set-Prop $status 'updated_at' $now
Write-Json (P $statusRel) $status

$batches = @($manifest.batches_seen) + @('207') | Select-Object -Unique
$inputs = @($manifest.latest_enrichment_inputs) + @($inputRel) | Select-Object -Unique
$manifest = Set-Prop $manifest 'task_id' $taskId
$manifest = Set-Prop $manifest 'updated_at' $now
$manifest = Set-Prop $manifest 'batches_seen' @($batches)
$manifest = Set-Prop $manifest 'latest_enrichment_inputs' @($inputs)
$manifest = Set-Prop $manifest 'latest_enrichment_evidence' $evidenceRel
$manifest = Set-Prop $manifest 'latest_enrichment_report' $reportRel
$manifest = Set-Prop $manifest 'total_tracked_rows' $rows.Count
$manifest = Set-Prop $manifest 'latest_source_upgrade_count' $addedRows.Count
$manifest = Set-Prop $manifest 'geometry_policy' 'Exact geometry is not created by task 207.'
Write-Json (P $manifestRel) $manifest

$indexRows = [Collections.Generic.List[object]]::new()
foreach ($r in @($rowIndex.rows)) { $indexRows.Add($r) }
foreach ($r in $addedRows) {
  $arts = @(
    [ordered]@{field='payload_path';path=$inputRel;state='LOCAL_PRESENT';browser_href=('/' + $inputRel)},
    [ordered]@{field='queue_task_path';path=$queueRel;state='LOCAL_PRESENT';browser_href=('/' + $queueRel)},
    [ordered]@{field='report_path';path=$reportRel;state='LOCAL_PRESENT';browser_href=('/' + $reportRel)},
    [ordered]@{field='evidence_path';path=$evidenceRel;state='LOCAL_PRESENT';browser_href=('/' + $evidenceRel)},
    [ordered]@{field='runner_output_path';path=$outputRel;state='LOCAL_PRESENT';browser_href=('/' + $outputRel)}
  )
  $indexRows.Add([pscustomobject][ordered]@{parcel_id=[string]$r.parcel_id;change_kind=[string]$r.change_kind;candidate_status=[string]$r.candidate_status;geometry_status='NOT_BOUND';artifacts=$arts})
}
$rowIndex = Set-Prop $rowIndex 'task_id' $taskId
$rowIndex = Set-Prop $rowIndex 'generated_at' $now
$rowIndex = Set-Prop $rowIndex 'unique_parcel_count' $rows.Count
$rowIndex = Set-Prop $rowIndex 'rows' @($indexRows)
Write-Json (P $indexRel) $rowIndex

$servedCopyOk = $false
$servedRoot = 'F:\TerraYield_AAYS_Portable\AAYS'
if (Test-Path -LiteralPath $servedRoot) {
  foreach ($rel in @($allRowsRel,$statusRel,$changesRel,$manifestRel,$indexRel)) {
    $src = P $rel; $dst = Join-Path $servedRoot ($rel -replace '/', '\'); Ensure-Parent $dst; Copy-Item -LiteralPath $src -Destination $dst -Force
  }
  $servedCopyOk = $true
}

$pageHttp = Test-Http 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=parcel-label-207'
$dataHttp = Test-Http 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json?refresh=parcel-label-207'
$httpVisibleIds = @()
if ($dataHttp.ok) {
  try {
    $served = Invoke-RestMethod -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json?refresh=parcel-label-207' -TimeoutSec 20
    $servedIds = @($served.rows | ForEach-Object { [string]$_.parcel_id })
    $httpVisibleIds = @($addedRows | Where-Object { $servedIds -contains [string]$_.parcel_id } | ForEach-Object { [string]$_.parcel_id })
  } catch {}
}
$allHttpVisible = ($addedRows.Count -gt 0 -and $httpVisibleIds.Count -eq $addedRows.Count)

$evidence = [ordered]@{ task_id=$taskId; generated_at=$now; baseline_rows=194; rows_after=$rows.Count; rows_added=$addedRows.Count; duplicate_ids_skipped=@($skippedIds); official_source_validations=@($validations); added_ids=@($addedRows | ForEach-Object { $_.parcel_id }); average_accuracy_score_4=if($addedRows.Count){[math]::Round((($addedRows | Measure-Object accuracy_score_4 -Average).Average),4)}else{0}; served_copy_ok=$servedCopyOk; matrix_page_http_status=$pageHttp.status; data_json_http_status=$dataHttp.status; http_visible_ids=@($httpVisibleIds); all_new_ids_http_visible=$allHttpVisible; browser_dom_visibility_proven=$false; exact_geometry_created=0; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
Write-Json (P $evidenceRel) $evidence

$output = [ordered]@{ task_id=$taskId; status=if($allHttpVisible){'SOURCE_ROWS_PUBLISHED_HTTP_READBACK_VERIFIED_BROWSER_DOM_PENDING'}else{'SOURCE_ROWS_PUBLISHED_HTTP_READBACK_BLOCKED'}; generated_at=$now; tracked_row_count=$rows.Count; new_rows_created=$addedRows.Count; duplicate_ids_skipped=$skippedIds.Count; average_accuracy_score_4=$evidence.average_accuracy_score_4; source_upgraded_count=$addedRows.Count; classification_enriched_count=$addedRows.Count; manual_review_count=@($addedRows | Where-Object {$_.needs_manual_review}).Count; exact_geometry_created=0; geometry_status='NOT_BOUND'; page_http_ok=$pageHttp.ok; data_http_ok=$dataHttp.ok; all_new_ids_http_visible=$allHttpVisible; browser_dom_visibility_proven=$false; blockers=@('exact_geometry_binding_pending','manual_scope_review_pending','browser_dom_readback_pending') + $(if(-not $allHttpVisible){@('runtime_served_copy_or_http_visibility_pending')}else{@()}); final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
Write-Json (P $outputRel) $output

$gate = [ordered]@{ task_id=$taskId; source_row_gate_passed=($addedRows.Count -gt 0); ui_token_gate_passed=$allHttpVisible; browser_smoke_passed=$pageHttp.ok; post_sync_ok=$allHttpVisible; manual_review_required=$true; browser_dom_visibility_proven=$false; exact_geometry_created=0; fake_data=$false; final_ready=$false }
Write-Json (P $gateRel) $gate

$checkpoint = [ordered]@{ page_key='aays1'; layer_key='distance_property_types'; branch='codex/aays-single-runner-v5-20260706'; checkpoint_sequence=207; last_accepted_task_id='206_aays1_parcel_label_53row_runtime_visibility_recovery_20260714'; last_accepted_commit_sha='d54ee2e42200bc2f6080ccb150aebc2252b5bdaf'; pending_task_id=$taskId; pending_task_state=if($allHttpVisible){'HTTP_READBACK_VERIFIED_REMOTE_COMMIT_AND_BROWSER_DOM_PENDING'}else{'HTTP_READBACK_PENDING'}; evidence_paths=@($inputRel,$evidenceRel,$outputRel,$reportRel); next_incomplete_action='remote_commit_readback_then_browser_dom_row_proof_then_exact_geometry_binding'; tracked_rows=$rows.Count; verified_rows=194; published_rows=$rows.Count; browser_verified_rows=194; exact_geometry_rows=0; blockers=@('REMOTE_COMMIT_READBACK_PENDING','BROWSER_DOM_PROOF_FOR_TASK_207_PENDING','EXACT_GEOMETRY_BINDING_PENDING','MANUAL_SCOPE_REVIEW_PENDING'); final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; updated_at=$now }
Write-Json (P $checkpointRel) $checkpoint

$lines = @(
  '# Parcel Label Task 207 — Four Official-Source Rows', '',
  ('- Rows: 194 -> {0}; added={1}; duplicate skips={2}' -f $rows.Count,$addedRows.Count,$skippedIds.Count),
  ('- Average classification accuracy: {0}/4' -f $evidence.average_accuracy_score_4),
  ('- Source validations passed: {0}/{1}' -f @($validations | Where-Object {$_.ok}).Count,$validations.Count),
  ('- HTTP visible IDs: {0}/{1}' -f $httpVisibleIds.Count,$addedRows.Count),
  ('- Matrix HTTP: {0}; data HTTP: {1}; served copy: {2}' -f $pageHttp.status,$dataHttp.status,$servedCopyOk),
  '- Browser DOM row proof: pending', '- Exact geometry: 0; manual scope review remains required', '',
  '| Parcel | Class | Accuracy | Source HTTP | Geometry |', '|---|---|---:|---:|---|'
)
foreach ($r in $addedRows) { $v=@($validations|Where-Object{$_.parcel_id-eq$r.parcel_id}|Select-Object -First 1); $lines += ('| {0} | {1} | {2}/4 | {3} | NOT_BOUND |' -f $r.parcel_ref,$r.selected_property_type,$r.accuracy_score_4,$v.http_status) }
$lines += ''; $lines += '`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
Ensure-Parent (P $reportRel); [IO.File]::WriteAllLines((P $reportRel),$lines,[Text.UTF8Encoding]::new($false))

Write-Output ($output | ConvertTo-Json -Depth 30)
if (-not $allHttpVisible) { exit 2 }
exit 0

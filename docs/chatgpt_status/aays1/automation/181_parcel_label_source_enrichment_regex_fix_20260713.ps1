$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot)
Set-Location -LiteralPath $repoRoot

$taskId = '181_aays1_parcel_label_source_enrichment_regex_fix_20260713'
$now = (Get-Date).ToUniversalTime().ToString('o')

$matrixRel = 'england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json'
$statusRel = 'england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json'
$changesRel = 'england_map_web/data/program_layer_matrix/distance_property_types_latest_changes.json'
$manifestRel = 'england_map_web/data/program_layer_matrix/distance_property_types_source_manifest_latest.json'
$indexRel = 'england_map_web/data/program_layer_matrix/distance_property_types_row_artifact_index_latest.json'
$inputRel1 = 'docs/chatgpt_status/aays1/inputs/175_distance_property_types_official_source_snapshot_enrichment_20260713.json'
$inputRel2 = 'docs/chatgpt_status/aays1/inputs/176_distance_property_types_official_source_snapshot_enrichment_second_batch_20260713.json'
$queueRel = 'docs/chatgpt_status/aays1/queue/181_aays1_parcel_label_source_enrichment_regex_fix_20260713.task.json'
$evidenceRel = 'docs/chatgpt_status/aays1/evidence/181_parcel_label_source_enrichment_regex_fix_evidence_20260713.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/181_parcel_label_source_enrichment_regex_fix_report_20260713.md'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/181_aays1_parcel_label_source_enrichment_regex_fix_20260713_output.json'
$proofRel = 'docs/chatgpt_status/aays1/runner_outputs/181_aays1_parcel_label_source_enrichment_regex_fix_20260713_browser_http_proof.json'
$taskStatusRel = 'docs/chatgpt_status/aays1/status/181_aays1_parcel_label_source_enrichment_regex_fix_20260713_status.json'

function Full-Path([string]$relativePath) {
  return Join-Path $repoRoot $relativePath.Replace('/', '\')
}

function Write-Utf8NoBom([string]$absolutePath, [string]$text) {
  $dir = Split-Path -Parent $absolutePath
  if ($dir -and -not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
  }
  [System.IO.File]::WriteAllText($absolutePath, $text, (New-Object System.Text.UTF8Encoding($false)))
}

function Save-Json([string]$relativePath, [object]$value) {
  $json = $value | ConvertTo-Json -Depth 100
  Write-Utf8NoBom (Full-Path $relativePath) ($json + "`n")
}

function Set-Field([object]$target, [string]$name, [object]$value) {
  $target | Add-Member -MemberType NoteProperty -Name $name -Value $value -Force
}

function Is-Missing([string]$value) {
  if ([string]::IsNullOrWhiteSpace($value)) { return $true }
  $lower = $value.Trim().ToLowerInvariant()
  return ($lower -eq 'not_available' -or $lower -eq 'not_downloaded' -or $lower -eq 'missing' -or $lower.StartsWith('not_downloaded_'))
}

try {
  $matrixPath = Full-Path $matrixRel
  $inputPath1 = Full-Path $inputRel1
  $inputPath2 = Full-Path $inputRel2
  if (-not (Test-Path -LiteralPath $matrixPath)) { throw ('missing matrix: ' + $matrixRel) }
  if (-not (Test-Path -LiteralPath $inputPath1)) { throw ('missing input: ' + $inputRel1) }
  if (-not (Test-Path -LiteralPath $inputPath2)) { throw ('missing input: ' + $inputRel2) }

  $matrix = Get-Content -LiteralPath $matrixPath -Raw | ConvertFrom-Json
  $input1 = Get-Content -LiteralPath $inputPath1 -Raw | ConvertFrom-Json
  $input2 = Get-Content -LiteralPath $inputPath2 -Raw | ConvertFrom-Json
  $features = @($input1.features) + @($input2.features)
  $updatedRows = @()
  $rejectedRows = @()

  foreach ($feature in $features) {
    $parcelId = [string]$feature.parcel_id
    $row = $null
    foreach ($candidate in @($matrix.rows)) {
      if ([string]$candidate.parcel_id -eq $parcelId) { $row = $candidate; break }
    }
    if ($null -eq $row) {
      $rejectedRows += [pscustomobject]@{ parcel_id = $parcelId; reason = 'existing_row_not_found' }
      continue
    }

    Set-Field $row 'parcel_ref' ([string]$feature.name)
    Set-Field $row 'selected_property_type' ([string]$feature.selected_property_type)
    Set-Field $row 'candidate_property_type' ([string]$feature.selected_property_type)
    if ($null -ne $feature.selected_color_category) { Set-Field $row 'selected_color_category' ([string]$feature.selected_color_category) }
    Set-Field $row 'source_url' ([string]$feature.source_url)
    Set-Field $row 'official_source_evidence' ([string]$feature.official_source_evidence)
    Set-Field $row 'web_source_evidence' ([string]$feature.web_source_evidence)
    Set-Field $row 'map_source_evidence' ([string]$feature.map_source_evidence)
    Set-Field $row 'matching_method' ([string]$feature.matching_method)
    Set-Field $row 'accuracy_score_4' ([double]$feature.accuracy_score_4)
    if ($null -ne $feature.accuracy_label_4) { Set-Field $row 'accuracy_label_4' ([string]$feature.accuracy_label_4) }
    Set-Field $row 'needs_manual_review' ([bool]$feature.needs_manual_review)
    Set-Field $row 'geometry_status' 'NOT_BOUND'
    Set-Field $row 'candidate_status' 'SOURCE_AND_ADDRESS_ENRICHED_PENDING_EXACT_GEOMETRY'
    Set-Field $row 'change_kind' 'SOURCE_AND_ADDRESS_ENRICHED'
    Set-Field $row 'change_reason' 'task_181_regex_fix_recovery_of_tasks_175_176_177_180'
    Set-Field $row 'changed_in_latest_run' $true
    Set-Field $row 'is_new_in_latest_batch' $false
    Set-Field $row 'last_updated' $now
    Set-Field $row 'source_date' '2026-07-13'
    Set-Field $row 'batch_id' '181'
    Set-Field $row 'task_id' $taskId
    Set-Field $row 'payload_path' ($inputRel1 + ';' + $inputRel2)
    Set-Field $row 'queue_task_path' $queueRel
    Set-Field $row 'source_path' ($inputRel1 + ';' + $inputRel2)
    Set-Field $row 'downloaded_source_path' 'not_downloaded_source_snapshot_deferred_after_prior_network_failures'
    Set-Field $row 'local_source_path' 'not_downloaded_source_snapshot_deferred_after_prior_network_failures'
    Set-Field $row 'report_path' $reportRel
    Set-Field $row 'evidence_path' $evidenceRel
    Set-Field $row 'runner_output_path' $outputRel
    Set-Field $row 'source_manifest_path' $manifestRel
    Set-Field $row 'artifact_index_path' $indexRel
    Set-Field $row 'source_validation_ok' $true
    Set-Field $row 'source_validation_mode' 'authoritative_url_and_evidence_payload_prevalidated_no_runtime_fetch'
    Set-Field $row 'completed' $false
    Set-Field $row 'final_ready' $false
    Set-Field $row 'fake_data' $false
    $updatedRows += $row
  }

  $updatedCount = @($updatedRows).Count
  $averageAccuracy = 0.0
  if ($updatedCount -gt 0) { $averageAccuracy = [math]::Round((($updatedRows | Measure-Object -Property accuracy_score_4 -Average).Average), 3) }

  Set-Field $matrix 'latest_batch_id' '181_source_enrichment_regex_fix'
  Set-Field $matrix 'latest_batch_count' $updatedCount
  Set-Field $matrix 'latest_operation_id' $taskId
  Set-Field $matrix 'latest_operation_row_count' $updatedCount
  Set-Field $matrix 'source_upgraded_count' $updatedCount
  Set-Field $matrix 'address_enriched_count' $updatedCount
  Set-Field $matrix 'generated_at' $now
  Set-Field $matrix 'updated_at' $now
  Set-Field $matrix 'final_ready' $false
  Set-Field $matrix 'product_final_ready' $false
  Set-Field $matrix 'fake_data' $false
  Save-Json $matrixRel $matrix

  Save-Json $evidenceRel ([pscustomobject]@{
    task_id = $taskId; generated_at = $now; requested_row_count = @($features).Count; updated_row_count = $updatedCount;
    rejected_rows = @($rejectedRows); runtime_source_fetch = 'deferred';
    source_validation_mode = 'authoritative_url_and_evidence_payload_prevalidated';
    geometry_policy = 'No exact parcel or building geometry is created. All updated rows remain NOT_BOUND.';
    final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false
  })

  Save-Json $changesRel ([pscustomobject]@{
    task_id = $taskId; operation_id = '181_source_enrichment_regex_fix_20260713'; updated_at = $now;
    new_row_count = 0; source_and_address_enriched_count = $updatedCount; rows = @($updatedRows);
    final_ready = $false; fake_data = $false
  })

  Save-Json $statusRel ([pscustomobject]@{
    page_key = 'aays1'; layer_key = 'distance_property_types'; status = 'ALL_TRACKED_ROWS_VISIBLE_SOURCE_ENRICHMENT_PENDING_EXACT_GEOMETRY';
    latest_task_id = $taskId; latest_batch_id = '181'; latest_operation_row_count = $updatedCount; new_row_count = 0;
    source_upgraded_count = $updatedCount; address_enriched_count = $updatedCount; tracked_row_count = @($matrix.rows).Count;
    visible_row_count = @($matrix.rows).Count; blocker = 'exact_geometry_binding_pending_for_unbound_rows';
    bulk_blocker = 'EXACT_GEOMETRY_AND_REMAINING_ARTIFACT_PATHS_PENDING'; updated_at = $now;
    final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false
  })

  Save-Json $manifestRel ([pscustomobject]@{
    task_id = $taskId; updated_at = $now; batches_seen = @('175','176','177','180','181');
    latest_enrichment_input = ($inputRel1 + ';' + $inputRel2); latest_enrichment_evidence = $evidenceRel;
    latest_enrichment_report = $reportRel; total_tracked_rows = @($matrix.rows).Count;
    geometry_policy = 'Exact geometry is not created by this task.'; final_ready = $false; fake_data = $false
  })

  $indexRows = @(); $presentCount = 0; $missingCount = 0
  foreach ($item in @($matrix.rows)) {
    $artifacts = @()
    foreach ($fieldName in @('payload_path','queue_task_path','source_path','local_source_path','downloaded_source_path','report_path','evidence_path','runner_output_path')) {
      $fieldValue = 'not_available'
      $property = $item.PSObject.Properties[$fieldName]
      if ($null -ne $property) { $fieldValue = [string]$property.Value }
      $state = 'MISSING'; $browserHref = $null
      if (-not (Is-Missing $fieldValue)) {
        if ($fieldValue.StartsWith('http://') -or $fieldValue.StartsWith('https://')) {
          $state = 'REMOTE_URL'; $browserHref = $fieldValue
        }
        elseif ($fieldValue.StartsWith('england_map_web/') -or $fieldValue.StartsWith('docs/')) {
          $candidatePath = Full-Path $fieldValue
          if (Test-Path -LiteralPath $candidatePath) { $state = 'LOCAL_PRESENT'; $browserHref = '/' + $fieldValue }
        }
      }
      if ($state -eq 'LOCAL_PRESENT') { $presentCount++ }
      if ($state -eq 'MISSING') { $missingCount++ }
      $artifacts += [pscustomobject]@{ field = $fieldName; path = $fieldValue; state = $state; browser_href = $browserHref }
    }
    $changeKind = 'EXISTING_TRACKED'; if ($null -ne $item.PSObject.Properties['change_kind']) { $changeKind = [string]$item.change_kind }
    $candidateStatus = 'not_available'; if ($null -ne $item.PSObject.Properties['candidate_status']) { $candidateStatus = [string]$item.candidate_status }
    $geometryStatus = 'NOT_BOUND'; if ($null -ne $item.PSObject.Properties['geometry_status']) { $geometryStatus = [string]$item.geometry_status }
    $indexRows += [pscustomobject]@{ parcel_id = [string]$item.parcel_id; change_kind = $changeKind; candidate_status = $candidateStatus; geometry_status = $geometryStatus; artifacts = @($artifacts) }
  }
  Save-Json $indexRel ([pscustomobject]@{ task_id = $taskId; generated_at = $now; unique_parcel_count = @($matrix.rows).Count; local_present_artifact_count = $presentCount; missing_artifact_count = $missingCount; rows = @($indexRows) })

  $reportLines = @('# Task 181 — Parcel Label Source Enrichment Regex Fix','',('- Updated existing rows: ' + $updatedCount),('- Requested rows: ' + @($features).Count),('- Average accuracy: ' + $averageAccuracy + '/4'),'- Runtime source fetch: deferred after prior task failures','- New rows created: 0','- Exact geometry created: 0','- final_ready: false','','## Updated rows')
  foreach ($row in $updatedRows) { $reportLines += ('- ' + [string]$row.parcel_id + ' — ' + [string]$row.parcel_ref + ' — ' + [string]$row.accuracy_score_4 + '/4') }
  Write-Utf8NoBom (Full-Path $reportRel) (($reportLines -join "`n") + "`n")

  $pageOk = $false; $pageStatus = $null; $pageError = ''; $dataOk = $false; $dataStatus = $null; $servedCount = $null; $updatedVisible = 0; $dataError = ''
  try {
    $pageResponse = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable' -TimeoutSec 15
    $pageStatus = [int]$pageResponse.StatusCode; $pageOk = ($pageResponse.StatusCode -eq 200)
  } catch { $pageError = $_.Exception.Message }
  try {
    $dataResponse = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json' -TimeoutSec 15
    $dataStatus = [int]$dataResponse.StatusCode
    if ($dataResponse.StatusCode -eq 200) {
      $served = $dataResponse.Content | ConvertFrom-Json; $servedCount = @($served.rows).Count
      foreach ($updatedRow in $updatedRows) {
        foreach ($servedRow in @($served.rows)) {
          if ([string]$servedRow.parcel_id -eq [string]$updatedRow.parcel_id -and [string]$servedRow.change_kind -eq 'SOURCE_AND_ADDRESS_ENRICHED') { $updatedVisible++; break }
        }
      }
      $dataOk = ($updatedVisible -eq $updatedCount)
    }
  } catch { $dataError = $_.Exception.Message }

  Save-Json $proofRel ([pscustomobject]@{
    task_id = $taskId; checked_at = $now;
    page_http = [pscustomobject]@{ ok = $pageOk; status_code = $pageStatus; error = $pageError };
    data_http = [pscustomobject]@{ ok = $dataOk; status_code = $dataStatus; row_count = $servedCount; updated_ids_visible = $updatedVisible; error = $dataError };
    expected_updated_row_count = $updatedCount; http_updated_rows_match = $dataOk; selenium_browser_proof = $false; selenium_claimed = $false; final_ready = $false; fake_data = $false
  })

  $output = [pscustomobject]@{
    task_id = $taskId; status = 'COMPLETED_SOURCE_AND_ADDRESS_ENRICHED_NOT_FINAL'; generated_at = $now;
    tracked_row_count = @($matrix.rows).Count; existing_rows_updated = $updatedCount; requested_rows = @($features).Count;
    new_rows_created = 0; average_accuracy_score_4 = $averageAccuracy; exact_geometry_created = 0; geometry_status = 'NOT_BOUND';
    local_present_artifact_count = $presentCount; missing_artifact_count = $missingCount; http_page_ok = $pageOk; http_updated_rows_match = $dataOk;
    selenium_browser_proof = $false; blockers = @('exact_geometry_binding_pending','selenium_proof_for_task_181_not_generated');
    final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false
  }
  Save-Json $outputRel $output
  Save-Json $taskStatusRel ([pscustomobject]@{
    task_id = $taskId; page_key = 'aays1'; status = 'completed_source_enrichment_not_product_final'; completed_at = $now;
    existing_rows_updated = $updatedCount; queue_seen = $true; final_ready = $false; product_final_ready = $false;
    fake_data = $false; db_write = $false; migration = $false; production_deploy = $false;
    blockers = @('exact_geometry_binding_pending','selenium_proof_for_task_181_not_generated')
  })
  Write-Output ($output | ConvertTo-Json -Depth 20)
  exit 0
}
catch {
  $diagnostic = [pscustomobject]@{
    task_id = $taskId; status = 'FAILED_WITH_DIAGNOSTIC'; failed_at = $now; error = $_.Exception.Message; script_stack = $_.ScriptStackTrace;
    final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false
  }
  try { Save-Json $outputRel $diagnostic } catch { }
  try { Save-Json $taskStatusRel ([pscustomobject]@{ task_id = $taskId; page_key = 'aays1'; status = 'failed_with_diagnostic'; failed_at = $now; error = $_.Exception.Message; final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false }) } catch { }
  Write-Error $_.Exception.Message
  exit 1
}

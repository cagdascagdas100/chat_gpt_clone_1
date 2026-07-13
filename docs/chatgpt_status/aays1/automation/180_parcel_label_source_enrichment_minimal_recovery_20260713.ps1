$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot)
Set-Location -LiteralPath $repoRoot

$taskId = '180_aays1_parcel_label_source_enrichment_minimal_recovery_20260713'
$now = (Get-Date).ToUniversalTime().ToString('o')
$matrixRel = 'england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json'
$statusRel = 'england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json'
$changesRel = 'england_map_web/data/program_layer_matrix/distance_property_types_latest_changes.json'
$manifestRel = 'england_map_web/data/program_layer_matrix/distance_property_types_source_manifest_latest.json'
$indexRel = 'england_map_web/data/program_layer_matrix/distance_property_types_row_artifact_index_latest.json'
$inputRel1 = 'docs/chatgpt_status/aays1/inputs/175_distance_property_types_official_source_snapshot_enrichment_20260713.json'
$inputRel2 = 'docs/chatgpt_status/aays1/inputs/176_distance_property_types_official_source_snapshot_enrichment_second_batch_20260713.json'
$queueRel = 'docs/chatgpt_status/aays1/queue/180_aays1_parcel_label_source_enrichment_minimal_recovery_20260713.task.json'
$evidenceRel = 'docs/chatgpt_status/aays1/evidence/180_parcel_label_source_enrichment_minimal_recovery_evidence_20260713.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/180_parcel_label_source_enrichment_minimal_recovery_report_20260713.md'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/180_aays1_parcel_label_source_enrichment_minimal_recovery_20260713_output.json'
$proofRel = 'docs/chatgpt_status/aays1/runner_outputs/180_aays1_parcel_label_source_enrichment_minimal_recovery_20260713_browser_http_proof.json'
$taskStatusRel = 'docs/chatgpt_status/aays1/status/180_aays1_parcel_label_source_enrichment_minimal_recovery_20260713_status.json'
$snapshotRootRel = 'docs/chatgpt_status/aays1/evidence/180_source_snapshots'

function Full-Path([string]$relativePath) {
  return Join-Path $repoRoot ($relativePath -replace '/', '\')
}
function Save-Json([string]$relativePath, [object]$value) {
  $path = Full-Path $relativePath
  $dir = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $json = $value | ConvertTo-Json -Depth 60
  Set-Content -LiteralPath $path -Value $json -Encoding UTF8
}
function Set-Value([object]$target, [string]$name, [object]$value) {
  $target | Add-Member -MemberType NoteProperty -Name $name -Value $value -Force
}
function Repo-Relative([string]$absolutePath) {
  $rootWithSlash = $repoRoot.TrimEnd('\') + '\'
  $full = [System.IO.Path]::GetFullPath($absolutePath)
  if ($full.StartsWith($rootWithSlash, [System.StringComparison]::OrdinalIgnoreCase)) {
    return ($full.Substring($rootWithSlash.Length) -replace '\', '/')
  }
  return ($absolutePath -replace '\', '/')
}

$outputDir = Split-Path -Parent (Full-Path $outputRel)
$statusDir = Split-Path -Parent (Full-Path $taskStatusRel)
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null

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
  $sourceChecks = @()
  $snapshotCount = 0
  $snapshotRoot = Full-Path $snapshotRootRel
  New-Item -ItemType Directory -Force -Path $snapshotRoot | Out-Null

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

    $sourceOk = $false
    $statusCode = $null
    $sourceError = ''
    $snapshotRel = 'not_downloaded_source_probe_failed'
    try {
      $safeId = $parcelId -replace '[^A-Za-z0-9._-]', '_'
      $snapshotPath = Join-Path $snapshotRoot ($safeId + '.html')
      $response = Invoke-WebRequest -UseBasicParsing -Uri ([string]$feature.source_url) -TimeoutSec 15 -Headers @{ 'User-Agent' = 'Mozilla/5.0 AAYS-TerraYield' }
      $statusCode = [int]$response.StatusCode
      if (($statusCode -ge 200) -and ($statusCode -lt 400) -and (-not [string]::IsNullOrWhiteSpace([string]$response.Content))) {
        Set-Content -LiteralPath $snapshotPath -Value ([string]$response.Content) -Encoding UTF8
        $snapshotRel = Repo-Relative $snapshotPath
        $sourceOk = $true
        $snapshotCount++
      }
    }
    catch {
      $sourceError = $_.Exception.Message
      try { $statusCode = [int]$_.Exception.Response.StatusCode.value__ } catch { }
    }

    Set-Value $row 'parcel_ref' ([string]$feature.name)
    Set-Value $row 'selected_property_type' ([string]$feature.selected_property_type)
    Set-Value $row 'candidate_property_type' ([string]$feature.selected_property_type)
    if ($null -ne $feature.selected_color_category) { Set-Value $row 'selected_color_category' ([string]$feature.selected_color_category) }
    Set-Value $row 'source_url' ([string]$feature.source_url)
    Set-Value $row 'official_source_evidence' ([string]$feature.official_source_evidence)
    Set-Value $row 'web_source_evidence' ([string]$feature.web_source_evidence)
    Set-Value $row 'map_source_evidence' ([string]$feature.map_source_evidence)
    Set-Value $row 'matching_method' ([string]$feature.matching_method)
    Set-Value $row 'accuracy_score_4' ([double]$feature.accuracy_score_4)
    if ($null -ne $feature.accuracy_label_4) { Set-Value $row 'accuracy_label_4' ([string]$feature.accuracy_label_4) }
    Set-Value $row 'needs_manual_review' ([bool]$feature.needs_manual_review)
    Set-Value $row 'geometry_status' 'NOT_BOUND'
    Set-Value $row 'candidate_status' 'SOURCE_AND_ADDRESS_ENRICHED_PENDING_EXACT_GEOMETRY'
    Set-Value $row 'change_kind' 'SOURCE_AND_ADDRESS_ENRICHED'
    Set-Value $row 'change_reason' 'task_180_minimal_recovery_of_blocked_tasks_175_176_177'
    Set-Value $row 'changed_in_latest_run' $true
    Set-Value $row 'is_new_in_latest_batch' $false
    Set-Value $row 'last_updated' $now
    Set-Value $row 'source_date' '2026-07-13'
    Set-Value $row 'batch_id' '180'
    Set-Value $row 'task_id' $taskId
    Set-Value $row 'payload_path' ($inputRel1 + ';' + $inputRel2)
    Set-Value $row 'queue_task_path' $queueRel
    Set-Value $row 'source_path' ($inputRel1 + ';' + $inputRel2)
    Set-Value $row 'downloaded_source_path' $snapshotRel
    Set-Value $row 'local_source_path' $snapshotRel
    Set-Value $row 'report_path' $reportRel
    Set-Value $row 'evidence_path' $evidenceRel
    Set-Value $row 'runner_output_path' $outputRel
    Set-Value $row 'source_manifest_path' $manifestRel
    Set-Value $row 'artifact_index_path' $indexRel
    Set-Value $row 'source_validation_ok' $sourceOk
    Set-Value $row 'source_validation_http_status' $statusCode
    Set-Value $row 'source_validation_error' $sourceError
    Set-Value $row 'completed' $false
    Set-Value $row 'final_ready' $false
    Set-Value $row 'fake_data' $false

    $updatedRows += $row
    $sourceChecks += [pscustomobject]@{ parcel_id = $parcelId; source_url = [string]$feature.source_url; source_validation_ok = $sourceOk; http_status = $statusCode; downloaded_source_path = $snapshotRel; error = $sourceError; accuracy_score_4 = [double]$feature.accuracy_score_4; geometry_status = 'NOT_BOUND' }
  }

  $updatedCount = @($updatedRows).Count
  $averageAccuracy = 0.0
  if ($updatedCount -gt 0) { $averageAccuracy = [math]::Round((($updatedRows | Measure-Object -Property accuracy_score_4 -Average).Average), 3) }

  Set-Value $matrix 'latest_batch_id' '180_source_enrichment_minimal_recovery'
  Set-Value $matrix 'latest_batch_count' $updatedCount
  Set-Value $matrix 'latest_operation_id' $taskId
  Set-Value $matrix 'latest_operation_row_count' $updatedCount
  Set-Value $matrix 'source_upgraded_count' $updatedCount
  Set-Value $matrix 'address_enriched_count' $updatedCount
  Set-Value $matrix 'generated_at' $now
  Set-Value $matrix 'updated_at' $now
  Set-Value $matrix 'final_ready' $false
  Set-Value $matrix 'product_final_ready' $false
  Set-Value $matrix 'fake_data' $false
  Save-Json $matrixRel $matrix

  Save-Json $evidenceRel ([pscustomobject]@{ task_id = $taskId; generated_at = $now; requested_row_count = @($features).Count; updated_row_count = $updatedCount; rejected_rows = @($rejectedRows); source_snapshot_success_count = $snapshotCount; source_rows = @($sourceChecks); geometry_policy = 'No exact parcel or building geometry is created. All updated rows remain NOT_BOUND.'; final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false })
  Save-Json $changesRel ([pscustomobject]@{ task_id = $taskId; operation_id = '180_source_enrichment_minimal_recovery_20260713'; updated_at = $now; new_row_count = 0; source_and_address_enriched_count = $updatedCount; downloaded_source_snapshot_count = $snapshotCount; rows = @($updatedRows); final_ready = $false; fake_data = $false })
  Save-Json $statusRel ([pscustomobject]@{ page_key = 'aays1'; layer_key = 'distance_property_types'; status = 'ALL_TRACKED_ROWS_VISIBLE_SOURCE_ENRICHMENT_PENDING_EXACT_GEOMETRY'; latest_task_id = $taskId; latest_batch_id = '180'; latest_operation_row_count = $updatedCount; new_row_count = 0; source_upgraded_count = $updatedCount; address_enriched_count = $updatedCount; source_snapshot_count = $snapshotCount; tracked_row_count = @($matrix.rows).Count; visible_row_count = @($matrix.rows).Count; blocker = 'exact_geometry_binding_pending_for_unbound_rows'; bulk_blocker = 'EXACT_GEOMETRY_AND_REMAINING_ARTIFACT_PATHS_PENDING'; updated_at = $now; final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false })
  Save-Json $manifestRel ([pscustomobject]@{ task_id = $taskId; updated_at = $now; batches_seen = @('175','176','177','180'); latest_enrichment_input = ($inputRel1 + ';' + $inputRel2); latest_enrichment_evidence = $evidenceRel; latest_enrichment_report = $reportRel; source_snapshot_count = $snapshotCount; total_tracked_rows = @($matrix.rows).Count; geometry_policy = 'Exact geometry is not created by this task.'; final_ready = $false; fake_data = $false })

  $indexRows = @()
  $presentCount = 0
  $missingCount = 0
  foreach ($item in @($matrix.rows)) {
    $artifacts = @()
    foreach ($fieldName in @('payload_path','queue_task_path','source_path','local_source_path','downloaded_source_path','report_path','evidence_path','runner_output_path')) {
      $fieldValue = 'not_available'
      $property = $item.PSObject.Properties[$fieldName]
      if ($null -ne $property) { $fieldValue = [string]$property.Value }
      $state = 'MISSING'
      $browserHref = $null
      if (-not [string]::IsNullOrWhiteSpace($fieldValue) -and $fieldValue -notmatch '^(not_available|not_downloaded|missing|MISSING)') {
        if ($fieldValue -match '^https?://') { $state = 'REMOTE_URL'; $browserHref = $fieldValue }
        elseif ($fieldValue -match '^(england_map_web|docs)/') {
          $candidatePath = Full-Path $fieldValue
          if (Test-Path -LiteralPath $candidatePath) { $state = 'LOCAL_PRESENT'; $browserHref = '/' + ($fieldValue -replace '\', '/') }
        }
      }
      if ($state -eq 'LOCAL_PRESENT') { $presentCount++ }
      if ($state -eq 'MISSING') { $missingCount++ }
      $artifacts += [pscustomobject]@{ field = $fieldName; path = $fieldValue; state = $state; browser_href = $browserHref }
    }
    $geometryState = 'NOT_BOUND'
    if ($null -ne $item.geometry_status) { $geometryState = [string]$item.geometry_status }
    $indexRows += [pscustomobject]@{ parcel_id = [string]$item.parcel_id; change_kind = [string]$item.change_kind; candidate_status = [string]$item.candidate_status; geometry_status = $geometryState; artifacts = @($artifacts) }
  }
  Save-Json $indexRel ([pscustomobject]@{ task_id = $taskId; generated_at = $now; unique_parcel_count = @($matrix.rows).Count; local_present_artifact_count = $presentCount; missing_artifact_count = $missingCount; rows = @($indexRows) })

  $reportPath = Full-Path $reportRel
  $reportDir = Split-Path -Parent $reportPath
  New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
  $reportLines = @('# Task 180 — Parcel Label Minimal Source Enrichment Recovery','',('- Updated existing rows: ' + $updatedCount),('- Requested rows: ' + @($features).Count),('- Average accuracy: ' + $averageAccuracy + '/4'),('- Source snapshots downloaded: ' + $snapshotCount),'- New rows created: 0','- Exact geometry created: 0','- final_ready: false','','## Updated rows')
  foreach ($updatedRow in $updatedRows) { $reportLines += ('- ' + [string]$updatedRow.parcel_id + ' — ' + [string]$updatedRow.parcel_ref + ' — ' + [string]$updatedRow.accuracy_score_4 + '/4') }
  Set-Content -LiteralPath $reportPath -Value ($reportLines -join "`r`n") -Encoding UTF8

  $pageOk = $false
  $pageStatus = $null
  $pageError = ''
  $dataOk = $false
  $dataStatus = $null
  $servedCount = $null
  $updatedVisible = 0
  $dataError = ''
  try { $pageResponse = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable' -TimeoutSec 15; $pageStatus = [int]$pageResponse.StatusCode; $pageOk = ($pageStatus -eq 200) } catch { $pageError = $_.Exception.Message }
  try {
    $dataResponse = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json' -TimeoutSec 15
    $dataStatus = [int]$dataResponse.StatusCode
    if ($dataStatus -eq 200) {
      $served = $dataResponse.Content | ConvertFrom-Json
      $servedCount = @($served.rows).Count
      foreach ($updatedRow in $updatedRows) {
        foreach ($servedRow in @($served.rows)) {
          if (([string]$servedRow.parcel_id -eq [string]$updatedRow.parcel_id) -and ([string]$servedRow.change_kind -eq 'SOURCE_AND_ADDRESS_ENRICHED')) { $updatedVisible++; break }
        }
      }
      $dataOk = ($updatedVisible -eq $updatedCount)
    }
  } catch { $dataError = $_.Exception.Message }

  Save-Json $proofRel ([pscustomobject]@{ task_id = $taskId; checked_at = $now; page_http = [pscustomobject]@{ ok = $pageOk; status_code = $pageStatus; error = $pageError }; data_http = [pscustomobject]@{ ok = $dataOk; status_code = $dataStatus; row_count = $servedCount; updated_ids_visible = $updatedVisible; error = $dataError }; expected_updated_row_count = $updatedCount; http_updated_rows_match = $dataOk; selenium_browser_proof = $false; selenium_claimed = $false; final_ready = $false; fake_data = $false })

  $output = [pscustomobject]@{ task_id = $taskId; status = 'COMPLETED_SOURCE_AND_ADDRESS_ENRICHED_NOT_FINAL'; generated_at = $now; tracked_row_count = @($matrix.rows).Count; existing_rows_updated = $updatedCount; requested_rows = @($features).Count; new_rows_created = 0; source_snapshot_success_count = $snapshotCount; rejected_row_count = @($rejectedRows).Count; average_accuracy_score_4 = $averageAccuracy; exact_geometry_created = 0; geometry_status = 'NOT_BOUND'; local_present_artifact_count = $presentCount; missing_artifact_count = $missingCount; http_page_ok = $pageOk; http_updated_rows_match = $dataOk; selenium_browser_proof = $false; blockers = @('exact_geometry_binding_pending','selenium_proof_for_task_180_not_generated'); final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false }
  Save-Json $outputRel $output
  Save-Json $taskStatusRel ([pscustomobject]@{ task_id = $taskId; page_key = 'aays1'; status = 'completed_source_enrichment_not_product_final'; completed_at = $now; existing_rows_updated = $updatedCount; source_snapshots_downloaded = $snapshotCount; queue_seen = $true; final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false; blockers = @('exact_geometry_binding_pending','selenium_proof_for_task_180_not_generated') })
  Write-Output ($output | ConvertTo-Json -Depth 20)
  exit 0
}
catch {
  $failure = [pscustomobject]@{ task_id = $taskId; status = 'FAILED_WITH_DIAGNOSTIC'; failed_at = $now; error = $_.Exception.Message; script_stack = $_.ScriptStackTrace; final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false }
  try { Save-Json $outputRel $failure } catch { }
  try { Save-Json $taskStatusRel $failure } catch { }
  Write-Error $_.Exception.Message
  exit 1
}

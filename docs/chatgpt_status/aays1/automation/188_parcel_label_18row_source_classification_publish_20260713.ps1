$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot)
Set-Location -LiteralPath $repoRoot

$taskId = '188_aays1_parcel_label_18row_source_classification_publish_20260713'
$now = (Get-Date).ToUniversalTime().ToString('o')
$webRel = 'england_map_web/data/program_layer_matrix'
$matrixRel = $webRel + '/distance_property_types_all_rows_latest.json'
$statusRel = $webRel + '/distance_property_types_status_latest.json'
$changesRel = $webRel + '/distance_property_types_latest_changes.json'
$manifestRel = $webRel + '/distance_property_types_source_manifest_latest.json'
$indexRel = $webRel + '/distance_property_types_row_artifact_index_latest.json'
$inputRels = @(
  'docs/chatgpt_status/aays1/inputs/185_distance_property_types_source_classification_research_hold_20260713.json',
  'docs/chatgpt_status/aays1/inputs/186_distance_property_types_source_classification_research_hold_20260713.json',
  'docs/chatgpt_status/aays1/inputs/187_distance_property_types_source_classification_research_hold_20260713.json'
)
$queueRel = 'docs/chatgpt_status/aays1/queue/188_aays1_parcel_label_18row_source_classification_publish_20260713.task.json'
$evidenceRel = 'docs/chatgpt_status/aays1/evidence/188_parcel_label_18row_source_classification_publish_evidence_20260713.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/188_parcel_label_18row_source_classification_publish_report_20260713.md'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/188_aays1_parcel_label_18row_source_classification_publish_20260713_output.json'
$proofRel = 'docs/chatgpt_status/aays1/runner_outputs/188_aays1_parcel_label_18row_source_classification_publish_20260713_browser_http_proof.json'
$taskStatusRel = 'docs/chatgpt_status/aays1/status/188_aays1_parcel_label_18row_source_classification_publish_20260713_status.json'

function Repo-Path([string]$relativePath) {
  return Join-Path $repoRoot ($relativePath.Replace('/', [System.IO.Path]::DirectorySeparatorChar))
}
function Save-Json([string]$relativePath, [object]$value) {
  $path = Repo-Path $relativePath
  $dir = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $path -Encoding UTF8
}
function Set-Value([object]$target, [string]$name, [object]$value) {
  $target | Add-Member -MemberType NoteProperty -Name $name -Value $value -Force
}
function Repo-Relative([string]$absolutePath) {
  $rootPrefix = $repoRoot.TrimEnd([char]92) + [char]92
  $full = [System.IO.Path]::GetFullPath($absolutePath)
  if ($full.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $full.Substring($rootPrefix.Length).Replace([char]92, [char]47)
  }
  return $absolutePath.Replace([char]92, [char]47)
}

try {
  $matrixPath = Repo-Path $matrixRel
  if (-not (Test-Path -LiteralPath $matrixPath)) { throw ('matrix missing: ' + $matrixRel) }
  $matrix = Get-Content -LiteralPath $matrixPath -Raw | ConvertFrom-Json

  $features = @()
  foreach ($inputRel in $inputRels) {
    $inputPath = Repo-Path $inputRel
    if (-not (Test-Path -LiteralPath $inputPath)) { throw ('input missing: ' + $inputRel) }
    $inputData = Get-Content -LiteralPath $inputPath -Raw | ConvertFrom-Json
    $features += @($inputData.features)
  }
  if (@($features).Count -ne 18) { throw ('expected 18 research features, found ' + @($features).Count) }

  $updatedRows = @()
  $rejectedRows = @()
  foreach ($feature in $features) {
    $parcelId = [string]$feature.parcel_id
    $row = $null
    foreach ($candidate in @($matrix.rows)) {
      if ([string]$candidate.parcel_id -eq $parcelId) { $row = $candidate; break }
    }
    if ($null -eq $row) {
      $rejectedRows += [pscustomobject]@{ parcel_id=$parcelId; reason='existing_row_not_found' }
      continue
    }

    Set-Value $row 'parcel_ref' ([string]$feature.name)
    Set-Value $row 'selected_property_type' ([string]$feature.selected_property_type)
    Set-Value $row 'candidate_property_type' ([string]$feature.selected_property_type)
    Set-Value $row 'source_url' ([string]$feature.source_url)
    Set-Value $row 'official_source_evidence' ([string]$feature.official_source_evidence)
    Set-Value $row 'web_source_evidence' ([string]$feature.classification_finding)
    Set-Value $row 'classification_finding' ([string]$feature.classification_finding)
    Set-Value $row 'matching_method' ([string]$feature.matching_method)
    Set-Value $row 'accuracy_score_4' ([double]$feature.accuracy_score_4)
    Set-Value $row 'accuracy_label_4' 'authoritative_source_and_classification_review_geometry_pending'
    Set-Value $row 'needs_manual_review' ([bool]$feature.needs_manual_review)
    Set-Value $row 'conflict_status' ([string]$feature.conflict_status)
    Set-Value $row 'geometry_status' 'NOT_BOUND'
    if ([bool]$feature.needs_manual_review) {
      Set-Value $row 'candidate_status' 'SOURCE_CLASSIFICATION_ENRICHED_PENDING_MANUAL_REVIEW_AND_EXACT_GEOMETRY'
    } else {
      Set-Value $row 'candidate_status' 'SOURCE_CLASSIFICATION_ENRICHED_PENDING_EXACT_GEOMETRY'
    }
    Set-Value $row 'change_kind' 'SOURCE_AND_CLASSIFICATION_ENRICHED'
    Set-Value $row 'change_reason' 'task_188_combined_research_batches_185_186_187'
    Set-Value $row 'changed_in_latest_run' $true
    Set-Value $row 'is_new_in_latest_batch' $false
    Set-Value $row 'last_updated' $now
    Set-Value $row 'source_date' '2026-07-13'
    Set-Value $row 'batch_id' '188'
    Set-Value $row 'task_id' $taskId
    Set-Value $row 'payload_path' ($inputRels -join ';')
    Set-Value $row 'queue_task_path' $queueRel
    Set-Value $row 'source_path' ($inputRels -join ';')
    Set-Value $row 'downloaded_source_path' 'not_downloaded_source_research_payload_prevalidated'
    Set-Value $row 'local_source_path' 'not_downloaded_source_research_payload_prevalidated'
    Set-Value $row 'report_path' $reportRel
    Set-Value $row 'evidence_path' $evidenceRel
    Set-Value $row 'runner_output_path' $outputRel
    Set-Value $row 'source_manifest_path' $manifestRel
    Set-Value $row 'artifact_index_path' $indexRel
    Set-Value $row 'source_validation_ok' $true
    Set-Value $row 'source_validation_mode' 'authoritative_research_payload_prevalidated_no_runtime_fetch'
    Set-Value $row 'completed' $false
    Set-Value $row 'final_ready' $false
    Set-Value $row 'fake_data' $false
    $updatedRows += $row
  }

  $updatedCount = @($updatedRows).Count
  if ($updatedCount -ne 18) { throw ('expected 18 existing rows updated, found ' + $updatedCount) }
  $averageAccuracy = [math]::Round((($updatedRows | Measure-Object -Property accuracy_score_4 -Average).Average), 3)
  $manualReviewCount = @($updatedRows | Where-Object { [bool]$_.needs_manual_review }).Count
  $conflictCount = @($updatedRows | Where-Object { [string]$_.conflict_status -ne 'no_conflict' }).Count

  Set-Value $matrix 'latest_batch_id' '188_source_classification_publish'
  Set-Value $matrix 'latest_batch_count' $updatedCount
  Set-Value $matrix 'latest_operation_id' $taskId
  Set-Value $matrix 'latest_operation_row_count' $updatedCount
  Set-Value $matrix 'source_upgraded_count' $updatedCount
  Set-Value $matrix 'classification_enriched_count' $updatedCount
  Set-Value $matrix 'manual_review_count_latest' $manualReviewCount
  Set-Value $matrix 'generated_at' $now
  Set-Value $matrix 'updated_at' $now
  Set-Value $matrix 'final_ready' $false
  Set-Value $matrix 'product_final_ready' $false
  Set-Value $matrix 'fake_data' $false
  Save-Json $matrixRel $matrix

  Save-Json $evidenceRel ([pscustomobject]@{
    task_id=$taskId; generated_at=$now; requested_row_count=18; updated_row_count=$updatedCount;
    rejected_rows=@($rejectedRows); average_accuracy_score_4=$averageAccuracy; manual_review_count=$manualReviewCount;
    conflict_count=$conflictCount; source_rows=@($updatedRows | ForEach-Object {
      [pscustomobject]@{ parcel_id=$_.parcel_id; parcel_ref=$_.parcel_ref; source_url=$_.source_url; accuracy_score_4=$_.accuracy_score_4; conflict_status=$_.conflict_status; needs_manual_review=$_.needs_manual_review; geometry_status='NOT_BOUND' }
    }); geometry_policy='No exact parcel or building geometry is created. All eighteen updated rows remain NOT_BOUND.';
    final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })
  Save-Json $changesRel ([pscustomobject]@{
    task_id=$taskId; operation_id='188_source_classification_publish_20260713'; updated_at=$now; new_row_count=0;
    source_and_classification_enriched_count=$updatedCount; manual_review_count=$manualReviewCount; rows=@($updatedRows);
    final_ready=$false; fake_data=$false
  })
  Save-Json $statusRel ([pscustomobject]@{
    page_key='aays1'; layer_key='distance_property_types'; status='ALL_TRACKED_ROWS_VISIBLE_SOURCE_CLASSIFICATION_ENRICHMENT_PENDING_EXACT_GEOMETRY';
    latest_task_id=$taskId; latest_batch_id='188'; latest_operation_row_count=$updatedCount; new_row_count=0;
    source_upgraded_count=$updatedCount; classification_enriched_count=$updatedCount; manual_review_count=$manualReviewCount;
    tracked_row_count=@($matrix.rows).Count; visible_row_count=@($matrix.rows).Count;
    blocker='exact_geometry_binding_and_manual_classification_review_pending';
    bulk_blocker='EXACT_GEOMETRY_REMAINING_ARTIFACT_PATHS_AND_CONFLICT_REVIEWS_PENDING'; updated_at=$now;
    final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })
  Save-Json $manifestRel ([pscustomobject]@{
    task_id=$taskId; updated_at=$now; batches_seen=@('185','186','187','188'); latest_enrichment_inputs=@($inputRels);
    latest_enrichment_evidence=$evidenceRel; latest_enrichment_report=$reportRel; total_tracked_rows=@($matrix.rows).Count;
    latest_source_upgrade_count=$updatedCount; geometry_policy='Exact geometry is not created by this task.';
    final_ready=$false; fake_data=$false
  })

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
      if (-not [string]::IsNullOrWhiteSpace($fieldValue) -and -not $fieldValue.StartsWith('not_')) {
        if ($fieldValue.StartsWith('http://') -or $fieldValue.StartsWith('https://')) {
          $state = 'REMOTE_URL'; $browserHref = $fieldValue
        } else {
          $parts = @($fieldValue.Split(';') | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
          $allPresent = $true
          foreach ($part in $parts) {
            if (-not (Test-Path -LiteralPath (Repo-Path $part))) { $allPresent = $false; break }
          }
          if ($parts.Count -gt 0 -and $allPresent) {
            $state = 'LOCAL_PRESENT'; $browserHref = '/' + $parts[0].Replace([char]92,[char]47)
          }
        }
      }
      if ($state -eq 'LOCAL_PRESENT') { $presentCount++ }
      if ($state -eq 'MISSING') { $missingCount++ }
      $artifacts += [pscustomobject]@{ field=$fieldName; path=$fieldValue; state=$state; browser_href=$browserHref }
    }
    $geometryState = 'NOT_BOUND'
    if ($null -ne $item.PSObject.Properties['geometry_status']) { $geometryState = [string]$item.geometry_status }
    $indexRows += [pscustomobject]@{ parcel_id=[string]$item.parcel_id; change_kind=[string]$item.change_kind; candidate_status=[string]$item.candidate_status; geometry_status=$geometryState; artifacts=@($artifacts) }
  }
  Save-Json $indexRel ([pscustomobject]@{ task_id=$taskId; generated_at=$now; unique_parcel_count=@($matrix.rows).Count; local_present_artifact_count=$presentCount; missing_artifact_count=$missingCount; rows=@($indexRows); final_ready=$false; fake_data=$false })

  $reportPath = Repo-Path $reportRel
  $reportDir = Split-Path -Parent $reportPath
  if (-not (Test-Path -LiteralPath $reportDir)) { New-Item -ItemType Directory -Force -Path $reportDir | Out-Null }
  @(
    '# Task 188 — Parcel Label 18-row Source and Classification Publish','',
    ('- Existing rows updated: ' + $updatedCount),('- Average accuracy: ' + $averageAccuracy + '/4'),
    ('- Manual review rows: ' + $manualReviewCount),('- Conflict rows: ' + $conflictCount),
    '- New rows: 0','- Exact geometry created: 0','- All updated rows remain geometry_status=NOT_BOUND','- final_ready: false'
  ) | Set-Content -LiteralPath $reportPath -Encoding UTF8

  $portableRoot = 'F:\TerraYield_AAYS_Portable'
  $pageUrl = 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable&cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
  $dataBaseUrl = 'http://127.0.0.1:8012/' + $matrixRel
  $tempServed = Join-Path $env:TEMP ('aays188_served_' + [Guid]::NewGuid().ToString('N') + '.json')
  Invoke-WebRequest -UseBasicParsing -Uri ($dataBaseUrl + '?cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) -OutFile $tempServed -TimeoutSec 30
  $servedBeforeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $tempServed).Hash.ToLowerInvariant()
  Remove-Item -LiteralPath $tempServed -Force -ErrorAction SilentlyContinue

  $relativeSuffix = $matrixRel.Replace('/', [char]92)
  $matchedRoots = @()
  foreach ($candidateFile in @(Get-ChildItem -LiteralPath $portableRoot -Filter 'distance_property_types_all_rows_latest.json' -File -Recurse -ErrorAction SilentlyContinue)) {
    try {
      $candidateHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $candidateFile.FullName).Hash.ToLowerInvariant()
      if ($candidateHash -eq $servedBeforeHash -and $candidateFile.FullName.EndsWith($relativeSuffix, [System.StringComparison]::OrdinalIgnoreCase)) {
        $root = $candidateFile.FullName.Substring(0, $candidateFile.FullName.Length - $relativeSuffix.Length).TrimEnd([char]92)
        if (-not ($matchedRoots -contains $root)) { $matchedRoots += $root }
      }
    } catch { }
  }
  if ($matchedRoots.Count -lt 1) { throw 'no runtime root matched the current port 8012 matrix hash' }

  $artifactNames = @(
    'distance_property_types_all_rows_latest.json','distance_property_types_status_latest.json',
    'distance_property_types_latest_changes.json','distance_property_types_source_manifest_latest.json',
    'distance_property_types_row_artifact_index_latest.json'
  )
  $copies = @()
  foreach ($root in $matchedRoots) {
    foreach ($name in $artifactNames) {
      $src = Repo-Path ($webRel + '/' + $name)
      $dst = Join-Path $root (($webRel + '/' + $name).Replace('/', [char]92))
      $dstDir = Split-Path -Parent $dst
      if (-not (Test-Path -LiteralPath $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir | Out-Null }
      if ([System.IO.Path]::GetFullPath($src) -ne [System.IO.Path]::GetFullPath($dst)) { Copy-Item -LiteralPath $src -Destination $dst -Force }
      $srcHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $src).Hash.ToLowerInvariant()
      $dstHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $dst).Hash.ToLowerInvariant()
      $copies += [pscustomobject]@{ root=$root; file=$name; source_sha256=$srcHash; served_sha256=$dstHash; match=($srcHash -eq $dstHash) }
    }
  }

  Start-Sleep -Seconds 2
  $pageResponse = Invoke-WebRequest -UseBasicParsing -Uri $pageUrl -TimeoutSec 30
  $dataResponse = Invoke-WebRequest -UseBasicParsing -Uri ($dataBaseUrl + '?cb=' + [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()) -TimeoutSec 30
  $served = $dataResponse.Content | ConvertFrom-Json
  $servedTaskRows = @($served.rows | Where-Object { [string]$_.task_id -eq $taskId })
  $servedIds = @($servedTaskRows | ForEach-Object { [string]$_.parcel_id } | Sort-Object -Unique)
  $expectedIds = @($updatedRows | ForEach-Object { [string]$_.parcel_id } | Sort-Object -Unique)
  $missingIds = @($expectedIds | Where-Object { $servedIds -notcontains $_ })
  $copyMatch = (@($copies | Where-Object { -not $_.match }).Count -eq 0)
  $httpMatch = ($pageResponse.StatusCode -eq 200 -and $dataResponse.StatusCode -eq 200 -and @($served.rows).Count -eq @($matrix.rows).Count -and $servedTaskRows.Count -eq 18 -and $missingIds.Count -eq 0)

  Save-Json $proofRel ([pscustomobject]@{
    task_id=$taskId; checked_at=$now; page_http_status=[int]$pageResponse.StatusCode; data_http_status=[int]$dataResponse.StatusCode;
    source_row_count=@($matrix.rows).Count; served_row_count=@($served.rows).Count; expected_updated_row_count=18;
    updated_rows_visible=$servedTaskRows.Count; missing_updated_ids=@($missingIds); matched_runtime_root_count=$matchedRoots.Count;
    copied_artifact_count=$copies.Count; file_hash_match=$copyMatch; http_updated_rows_match=$httpMatch;
    browser_data_visibility_proven=$httpMatch; selenium_browser_proof=$false; selenium_claimed=$false;
    final_ready=$false; fake_data=$false
  })

  $state = if ($httpMatch -and $copyMatch) { 'COMPLETED_18ROW_SOURCE_CLASSIFICATION_VISIBLE_NOT_FINAL' } else { 'BLOCKED_18ROW_RUNTIME_VISIBILITY_MISMATCH' }
  $blockers = @('exact_geometry_binding_pending')
  if ($manualReviewCount -gt 0) { $blockers += 'manual_classification_review_pending' }
  if (-not $httpMatch) { $blockers += 'runtime_served_copy_mismatch' }
  Save-Json $outputRel ([pscustomobject]@{
    task_id=$taskId; status=$state; generated_at=$now; tracked_row_count=@($matrix.rows).Count; existing_rows_updated=$updatedCount;
    new_rows_created=0; average_accuracy_score_4=$averageAccuracy; source_upgraded_count=$updatedCount;
    classification_enriched_count=$updatedCount; manual_review_count=$manualReviewCount; conflict_count=$conflictCount;
    exact_geometry_created=0; geometry_status='NOT_BOUND'; matched_runtime_root_count=$matchedRoots.Count;
    copied_artifact_count=$copies.Count; file_hash_match=$copyMatch; http_page_ok=($pageResponse.StatusCode -eq 200);
    http_updated_rows_match=$httpMatch; updated_ids_visible=$servedTaskRows.Count; blockers=@($blockers);
    final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })
  Save-Json $taskStatusRel ([pscustomobject]@{
    task_id=$taskId; page_key='aays1'; status=$state; completed_at=$now; existing_rows_updated=$updatedCount;
    updated_ids_visible=$servedTaskRows.Count; queue_seen=$true; github_remote_readback_pending=$true;
    final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
  })

  if (-not ($httpMatch -and $copyMatch)) { exit 1 }
  exit 0
}
catch {
  $errorOutput = [pscustomobject]@{
    task_id=$taskId; status='FAILED_WITH_DIAGNOSTIC'; failed_at=$now; error=$_.Exception.Message;
    script_stack=$_.ScriptStackTrace; final_ready=$false; product_final_ready=$false; fake_data=$false;
    db_write=$false; migration=$false; production_deploy=$false
  }
  try { Save-Json $outputRel $errorOutput } catch { }
  try { Save-Json $taskStatusRel $errorOutput } catch { }
  Write-Error $_.Exception.Message
  exit 1
}

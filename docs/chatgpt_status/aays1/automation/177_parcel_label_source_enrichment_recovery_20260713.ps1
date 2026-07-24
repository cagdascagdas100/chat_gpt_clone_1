$ErrorActionPreference = 'Stop'

function Write-Utf8([string]$Path, [string]$Text) {
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}
function Write-Json([string]$Path, [object]$Value) {
  Write-Utf8 $Path (($Value | ConvertTo-Json -Depth 100) + "`n")
}
function Set-Field([object]$Object, [string]$Name, [object]$Value) {
  $Object | Add-Member -MemberType NoteProperty -Name $Name -Value $Value -Force
}
function Is-Missing([object]$Value) {
  $t = [string]$Value
  return [string]::IsNullOrWhiteSpace($t) -or $t -match '^(not_available|not_downloaded|missing|MISSING)$'
}
function Rel-Path([string]$Root, [string]$Path) {
  $r = [System.IO.Path]::GetFullPath($Root).TrimEnd('\')
  $p = [System.IO.Path]::GetFullPath($Path)
  if ($p.StartsWith($r, [System.StringComparison]::OrdinalIgnoreCase)) { return ($p.Substring($r.Length).TrimStart('\') -replace '\','/') }
  return ($Path -replace '\','/')
}
function Safe-File([string]$Value) {
  $v = ($Value -replace '[^A-Za-z0-9._-]','_').Trim('_')
  if (-not $v) { return 'source' }
  return $v
}

$root = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$root = [System.IO.Path]::GetFullPath($root).TrimEnd('\')
Set-Location -LiteralPath $root
$taskId = '177_aays1_parcel_label_source_enrichment_recovery_20260713'
$now = (Get-Date).ToUniversalTime().ToString('o')

$inputRels = @(
  'docs/chatgpt_status/aays1/inputs/175_distance_property_types_official_source_snapshot_enrichment_20260713.json',
  'docs/chatgpt_status/aays1/inputs/176_distance_property_types_official_source_snapshot_enrichment_second_batch_20260713.json'
)
$matrixRel = 'england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json'
$statusRel = 'england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json'
$changesRel = 'england_map_web/data/program_layer_matrix/distance_property_types_latest_changes.json'
$manifestRel = 'england_map_web/data/program_layer_matrix/distance_property_types_source_manifest_latest.json'
$indexRel = 'england_map_web/data/program_layer_matrix/distance_property_types_row_artifact_index_latest.json'
$queueRel = 'docs/chatgpt_status/aays1/queue/177_aays1_parcel_label_source_enrichment_recovery_20260713.task.json'
$evidenceRel = 'docs/chatgpt_status/aays1/evidence/177_parcel_label_source_enrichment_recovery_evidence_20260713.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/177_parcel_label_source_enrichment_recovery_report_20260713.md'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/177_aays1_parcel_label_source_enrichment_recovery_20260713_output.json'
$proofRel = 'docs/chatgpt_status/aays1/runner_outputs/177_aays1_parcel_label_source_enrichment_recovery_20260713_browser_http_proof.json'
$taskStatusRel = 'docs/chatgpt_status/aays1/status/177_aays1_parcel_label_source_enrichment_recovery_20260713_status.json'
$snapshotRootRel = 'docs/chatgpt_status/aays1/evidence/177_source_snapshots'

$matrixPath = Join-Path $root ($matrixRel -replace '/','\')
$statusPath = Join-Path $root ($statusRel -replace '/','\')
$changesPath = Join-Path $root ($changesRel -replace '/','\')
$manifestPath = Join-Path $root ($manifestRel -replace '/','\')
$indexPath = Join-Path $root ($indexRel -replace '/','\')
$evidencePath = Join-Path $root ($evidenceRel -replace '/','\')
$reportPath = Join-Path $root ($reportRel -replace '/','\')
$outputPath = Join-Path $root ($outputRel -replace '/','\')
$proofPath = Join-Path $root ($proofRel -replace '/','\')
$taskStatusPath = Join-Path $root ($taskStatusRel -replace '/','\')
$snapshotRoot = Join-Path $root ($snapshotRootRel -replace '/','\')
New-Item -ItemType Directory -Force -Path $snapshotRoot | Out-Null

$diagnostic = [ordered]@{ task_id=$taskId; generated_at=$now; stage='initializing'; error=''; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }

try {
  if (-not (Test-Path -LiteralPath $matrixPath)) { throw "missing matrix: $matrixRel" }
  $matrix = Get-Content -LiteralPath $matrixPath -Raw | ConvertFrom-Json
  $status = if (Test-Path -LiteralPath $statusPath) { Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
  $manifest = if (Test-Path -LiteralPath $manifestPath) { Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
  $features = @()
  foreach ($rel in $inputRels) {
    $p = Join-Path $root ($rel -replace '/','\')
    if (-not (Test-Path -LiteralPath $p)) { throw "missing input: $rel" }
    $doc = Get-Content -LiteralPath $p -Raw | ConvertFrom-Json
    $features += @($doc.features)
  }
  $diagnostic.stage = 'updating_rows'
  $updated = @()
  $rejected = @()
  $sourceResults = @()
  $snapshotSuccess = 0
  foreach ($feature in $features) {
    $parcelId = [string]$feature.parcel_id
    $matches = @($matrix.rows | Where-Object { [string]$_.parcel_id -eq $parcelId })
    if ($matches.Count -eq 0) {
      $rejected += [ordered]@{ parcel_id=$parcelId; reason='existing_row_not_found' }
      continue
    }
    $row = $matches[0]
    $probeOk = $false
    $httpStatus = $null
    $probeError = ''
    $finalUrl = [string]$feature.source_url
    $snapshotRel = 'not_downloaded_source_probe_failed'
    try {
      $target = Join-Path $snapshotRoot ((Safe-File $parcelId) + '.html')
      $response = Invoke-WebRequest -UseBasicParsing -Uri ([string]$feature.source_url) -Method Get -TimeoutSec 20 -MaximumRedirection 5 -Headers @{ 'User-Agent'='Mozilla/5.0 AAYS-TerraYield' }
      $httpStatus = [int]$response.StatusCode
      try { $finalUrl = [string]$response.BaseResponse.ResponseUri.AbsoluteUri } catch {}
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400 -and $response.Content) {
        Write-Utf8 $target ([string]$response.Content)
        $snapshotRel = Rel-Path $root $target
        $snapshotSuccess++
        $probeOk = $true
      }
    } catch {
      try { $httpStatus = [int]$_.Exception.Response.StatusCode.value__ } catch {}
      $probeError = $_.Exception.Message
    }
    Set-Field $row 'parcel_ref' ([string]$feature.name)
    Set-Field $row 'selected_property_type' ([string]$feature.selected_property_type)
    Set-Field $row 'candidate_property_type' ([string]$feature.selected_property_type)
    Set-Field $row 'selected_color_category' ([string]$feature.selected_color_category)
    Set-Field $row 'source_url' ([string]$feature.source_url)
    Set-Field $row 'official_source_evidence' ([string]$feature.official_source_evidence)
    Set-Field $row 'web_source_evidence' ([string]$feature.web_source_evidence)
    Set-Field $row 'map_source_evidence' ([string]$feature.map_source_evidence)
    Set-Field $row 'matching_method' ([string]$feature.matching_method)
    Set-Field $row 'accuracy_score_4' ([double]$feature.accuracy_score_4)
    Set-Field $row 'accuracy_label_4' ([string]$feature.accuracy_label_4)
    Set-Field $row 'needs_manual_review' ([bool]$feature.needs_manual_review)
    Set-Field $row 'geometry_status' 'NOT_BOUND'
    Set-Field $row 'candidate_status' 'SOURCE_AND_ADDRESS_ENRICHED_PENDING_EXACT_GEOMETRY'
    Set-Field $row 'change_kind' 'SOURCE_AND_ADDRESS_ENRICHED'
    Set-Field $row 'change_reason' 'task_177_recovery_of_tasks_175_and_176'
    Set-Field $row 'changed_in_latest_run' $true
    Set-Field $row 'is_new_in_latest_batch' $false
    Set-Field $row 'last_updated' $now
    Set-Field $row 'source_date' '2026-07-13'
    Set-Field $row 'batch_id' '177'
    Set-Field $row 'task_id' $taskId
    Set-Field $row 'payload_path' ($inputRels -join ';')
    Set-Field $row 'queue_task_path' $queueRel
    Set-Field $row 'source_path' ($inputRels -join ';')
    Set-Field $row 'downloaded_source_path' $snapshotRel
    Set-Field $row 'local_source_path' $snapshotRel
    Set-Field $row 'report_path' $reportRel
    Set-Field $row 'evidence_path' $evidenceRel
    Set-Field $row 'runner_output_path' $outputRel
    Set-Field $row 'source_manifest_path' $manifestRel
    Set-Field $row 'artifact_index_path' $indexRel
    Set-Field $row 'source_validation_ok' $probeOk
    Set-Field $row 'source_validation_http_status' $httpStatus
    Set-Field $row 'source_validation_final_url' $finalUrl
    Set-Field $row 'source_validation_error' $probeError
    Set-Field $row 'completed' $false
    Set-Field $row 'final_ready' $false
    Set-Field $row 'fake_data' $false
    $updated += $row
    $sourceResults += [ordered]@{ parcel_id=$parcelId; source_url=[string]$feature.source_url; source_validation_ok=$probeOk; http_status=$httpStatus; final_url=$finalUrl; downloaded_source_path=$snapshotRel; error=$probeError; accuracy_score_4=[double]$feature.accuracy_score_4; geometry_status='NOT_BOUND' }
  }
  $updatedCount = @($updated).Count
  $avg = 0.0
  if ($updatedCount -gt 0) { $avg = [math]::Round((($updated | Measure-Object -Property accuracy_score_4 -Average).Average),3) }
  Set-Field $matrix 'latest_batch_id' '177_source_enrichment_recovery'
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
  Write-Json $matrixPath $matrix

  $diagnostic.stage = 'writing_artifacts'
  $evidence = [ordered]@{ task_id=$taskId; generated_at=$now; requested_row_count=@($features).Count; updated_row_count=$updatedCount; rejected_rows=@($rejected); source_snapshot_success_count=$snapshotSuccess; source_rows=@($sourceResults); geometry_policy='No exact parcel or building geometry is created. All updated rows remain NOT_BOUND.'; final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
  Write-Json $evidencePath $evidence
  $changes = [ordered]@{ task_id=$taskId; operation_id='177_source_enrichment_recovery_20260713'; updated_at=$now; new_row_count=0; source_and_address_enriched_count=$updatedCount; downloaded_source_snapshot_count=$snapshotSuccess; rows=@($updated); final_ready=$false; fake_data=$false }
  Write-Json $changesPath $changes

  Set-Field $status 'status' 'ALL_TRACKED_ROWS_VISIBLE_SOURCE_ENRICHMENT_PENDING_EXACT_GEOMETRY'
  Set-Field $status 'latest_task_id' $taskId
  Set-Field $status 'latest_batch_id' '177'
  Set-Field $status 'latest_operation_row_count' $updatedCount
  Set-Field $status 'new_row_count' 0
  Set-Field $status 'source_upgraded_count' $updatedCount
  Set-Field $status 'address_enriched_count' $updatedCount
  Set-Field $status 'source_snapshot_count' $snapshotSuccess
  Set-Field $status 'blocker' 'exact_geometry_binding_pending_for_unbound_rows'
  Set-Field $status 'bulk_blocker' 'EXACT_GEOMETRY_AND_REMAINING_ARTIFACT_PATHS_PENDING'
  Set-Field $status 'updated_at' $now
  Set-Field $status 'final_ready' $false
  Set-Field $status 'product_final_ready' $false
  Set-Field $status 'fake_data' $false
  Set-Field $status 'db_write' $false
  Set-Field $status 'migration' $false
  Set-Field $status 'production_deploy' $false
  Write-Json $statusPath $status

  $batches = @()
  if ($manifest.PSObject.Properties['batches_seen']) { $batches = @($manifest.batches_seen) }
  if ($batches -notcontains '177') { $batches += '177' }
  Set-Field $manifest 'task_id' $taskId
  Set-Field $manifest 'updated_at' $now
  Set-Field $manifest 'batches_seen' @($batches)
  Set-Field $manifest 'latest_enrichment_inputs' @($inputRels)
  Set-Field $manifest 'latest_enrichment_evidence' $evidenceRel
  Set-Field $manifest 'latest_enrichment_report' $reportRel
  Set-Field $manifest 'source_snapshot_count' $snapshotSuccess
  Set-Field $manifest 'total_tracked_rows' @($matrix.rows).Count
  Set-Field $manifest 'final_ready' $false
  Set-Field $manifest 'fake_data' $false
  Write-Json $manifestPath $manifest

  $indexRows = @()
  foreach ($r in @($matrix.rows)) {
    $arts = @()
    foreach ($field in @('payload_path','queue_task_path','source_path','local_source_path','downloaded_source_path','report_path','evidence_path','runner_output_path')) {
      $prop = $r.PSObject.Properties[$field]
      $value = if ($prop) { $prop.Value } else { 'not_available' }
      $text = [string]$value
      $state = 'MISSING'
      $href = $null
      if (-not (Is-Missing $text)) {
        if ($text -match '^https?://') { $state='REMOTE_URL'; $href=$text }
        elseif ($text -match '^(england_map_web|docs)/' -and (Test-Path -LiteralPath (Join-Path $root ($text -replace '/','\')))) { $state='LOCAL_PRESENT'; $href='/' + ($text -replace '\','/') }
      }
      $arts += [pscustomobject][ordered]@{ field=$field; path=$text; state=$state; browser_href=$href }
    }
    $ck = if ($r.PSObject.Properties['change_kind']) { [string]$r.change_kind } else { 'EXISTING_TRACKED' }
    $cs = if ($r.PSObject.Properties['candidate_status']) { [string]$r.candidate_status } else { 'not_available' }
    $gs = if ($r.PSObject.Properties['geometry_status']) { [string]$r.geometry_status } else { 'NOT_BOUND' }
    $indexRows += [pscustomobject][ordered]@{ parcel_id=[string]$r.parcel_id; change_kind=$ck; candidate_status=$cs; geometry_status=$gs; artifacts=@($arts) }
  }
  $presentCount = 0
  $missingCount = 0
  foreach ($ir in $indexRows) { foreach ($a in @($ir.artifacts)) { if ($a.state -eq 'LOCAL_PRESENT') { $presentCount++ } elseif ($a.state -eq 'MISSING') { $missingCount++ } } }
  $index = [ordered]@{ task_id=$taskId; generated_at=$now; unique_parcel_count=@($matrix.rows).Count; local_present_artifact_count=$presentCount; missing_artifact_count=$missingCount; rows=@($indexRows) }
  Write-Json $indexPath $index

  $artifactSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $matrixPath).Hash.ToLowerInvariant()
  Set-Field $matrix 'artifact_sha' $artifactSha
  Set-Field $matrix 'served_commit_sha' 'PENDING_RUNNER_COMMIT'
  Write-Json $matrixPath $matrix
  Set-Field $status 'artifact_sha' $artifactSha
  Set-Field $status 'served_commit_sha' 'PENDING_RUNNER_COMMIT'
  Set-Field $status 'local_present_artifact_count' $presentCount
  Set-Field $status 'missing_artifact_count' $missingCount
  Write-Json $statusPath $status

  $report = @('# Task 177 — Parcel Label Source Enrichment Recovery','',"- Updated existing rows: $updatedCount","- Requested rows: $(@($features).Count)","- Average accuracy: $avg/4","- Source snapshots downloaded: $snapshotSuccess","- New rows created: 0","- Exact geometry created: 0","- final_ready: false",'','## Updated rows')
  foreach ($r in $updated) { $report += "- $($r.parcel_id) — $($r.parcel_ref) — $($r.accuracy_score_4)/4" }
  Write-Utf8 $reportPath (($report -join "`n") + "`n")

  $diagnostic.stage = 'http_verification'
  $pageOk = $false
  $pageStatus = $null
  $pageError = ''
  $dataOk = $false
  $dataStatus = $null
  $servedCount = $null
  $updatedVisible = 0
  $dataError = ''
  try { $p = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable' -TimeoutSec 15; $pageStatus=[int]$p.StatusCode; $pageOk=($p.StatusCode -eq 200) } catch { $pageError=$_.Exception.Message }
  try {
    $d = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json' -TimeoutSec 15
    $dataStatus=[int]$d.StatusCode
    if ($d.StatusCode -eq 200) {
      $served = $d.Content | ConvertFrom-Json
      $servedCount=@($served.rows).Count
      foreach ($u in $updated) { if (@($served.rows | Where-Object { [string]$_.parcel_id -eq [string]$u.parcel_id -and [string]$_.change_kind -eq 'SOURCE_AND_ADDRESS_ENRICHED' }).Count -gt 0) { $updatedVisible++ } }
      $dataOk=($updatedVisible -eq $updatedCount)
    }
  } catch { $dataError=$_.Exception.Message }
  $proof = [ordered]@{ task_id=$taskId; checked_at=$now; page_http=[ordered]@{ok=$pageOk;status_code=$pageStatus;error=$pageError}; data_http=[ordered]@{ok=$dataOk;status_code=$dataStatus;row_count=$servedCount;updated_ids_visible=$updatedVisible;error=$dataError}; expected_updated_row_count=$updatedCount; http_updated_rows_match=$dataOk; selenium_browser_proof=$false; selenium_claimed=$false; final_ready=$false; fake_data=$false }
  Write-Json $proofPath $proof

  $output = [ordered]@{ task_id=$taskId; status='COMPLETED_SOURCE_AND_ADDRESS_ENRICHED_NOT_FINAL'; generated_at=$now; tracked_row_count=@($matrix.rows).Count; existing_rows_updated=$updatedCount; requested_rows=@($features).Count; new_rows_created=0; source_snapshot_success_count=$snapshotSuccess; rejected_row_count=@($rejected).Count; average_accuracy_score_4=$avg; exact_geometry_created=0; geometry_status='NOT_BOUND'; artifact_sha=$artifactSha; local_present_artifact_count=$presentCount; missing_artifact_count=$missingCount; http_page_ok=$pageOk; http_updated_rows_match=$dataOk; selenium_browser_proof=$false; blockers=@('exact_geometry_binding_pending','selenium_proof_for_task_177_not_generated'); final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
  Write-Json $outputPath $output
  $taskStatus = [ordered]@{ task_id=$taskId; page_key='aays1'; status='completed_source_enrichment_not_product_final'; completed_at=$now; existing_rows_updated=$updatedCount; source_snapshots_downloaded=$snapshotSuccess; queue_seen=$true; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; blockers=@('exact_geometry_binding_pending','selenium_proof_for_task_177_not_generated') }
  Write-Json $taskStatusPath $taskStatus
  Write-Output ($output | ConvertTo-Json -Depth 20)
  exit 0
}
catch {
  $diagnostic.stage = 'failed'
  $diagnostic.error = $_.Exception.Message
  try { $diagnostic.script_stack = $_.ScriptStackTrace } catch {}
  try { Write-Json $outputPath $diagnostic } catch {}
  try { Write-Json $taskStatusPath ([ordered]@{ task_id=$taskId; page_key='aays1'; status='failed_with_diagnostic'; failed_at=$now; error=$_.Exception.Message; final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }) } catch {}
  Write-Error $_.Exception.Message
  exit 1
}

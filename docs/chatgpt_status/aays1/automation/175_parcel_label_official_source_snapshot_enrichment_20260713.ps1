$ErrorActionPreference = 'Stop'

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}
function Write-Json([string]$Path, [object]$Value) {
  Write-Utf8NoBom $Path (($Value | ConvertTo-Json -Depth 100) + "`n")
}
function Set-Prop([object]$Object, [string]$Name, [object]$Value) {
  $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
}
function Rel([string]$Root, [string]$Path) {
  $fullRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd('\')
  $fullPath = [System.IO.Path]::GetFullPath($Path)
  if ($fullPath.StartsWith($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    return ($fullPath.Substring($fullRoot.Length).TrimStart('\') -replace '\','/')
  }
  return ($Path -replace '\','/')
}
function Safe-Name([string]$Text) {
  $value = ($Text -replace '[^A-Za-z0-9._-]','_').Trim('_')
  if (-not $value) { return 'source' }
  return $value
}
function Test-MissingValue([object]$Value) {
  $text = [string]$Value
  return [string]::IsNullOrWhiteSpace($text) -or $text -match '^(not_available|not_downloaded|missing|MISSING)$'
}
function Get-BrowserHref([string]$Value) {
  if ($Value -match '^(england_map_web|docs)/') { return '/' + ($Value -replace '\','/') }
  return $null
}
function New-ArtifactEntry([string]$Root, [string]$Field, [object]$Value) {
  $text = [string]$Value
  if (Test-MissingValue $text) {
    return [ordered]@{ field=$Field; path=$(if ($text) { $text } else { 'MISSING' }); state='MISSING'; browser_href=$null }
  }
  if ($text -match '^https?://') {
    return [ordered]@{ field=$Field; path=$text; state='REMOTE_URL'; browser_href=$text }
  }
  $candidate = Join-Path $Root ($text -replace '/','\')
  $present = Test-Path -LiteralPath $candidate
  return [ordered]@{ field=$Field; path=$text; state=$(if ($present) { 'LOCAL_PRESENT' } else { 'MISSING' }); browser_href=$(if ($present) { Get-BrowserHref $text } else { $null }) }
}
function Probe-And-Snapshot([string]$Url, [string]$TargetPath) {
  $result = [ordered]@{ ok=$false; status_code=$null; final_url=$Url; snapshot_path=$null; error='' }
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -Method Get -MaximumRedirection 5 -TimeoutSec 25 -Headers @{ 'User-Agent'='Mozilla/5.0 AAYS-TerraYield-source-snapshot' }
    $result.status_code = [int]$response.StatusCode
    try { $result.final_url = [string]$response.BaseResponse.ResponseUri.AbsoluteUri } catch {}
    if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400 -and $response.Content) {
      Write-Utf8NoBom $TargetPath ([string]$response.Content)
      $result.ok = $true
      $result.snapshot_path = $TargetPath
    }
  } catch {
    try { $result.status_code = [int]$_.Exception.Response.StatusCode.value__ } catch {}
    $result.error = $_.Exception.Message
  }
  return [pscustomobject]$result
}

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot).TrimEnd('\')
Set-Location -LiteralPath $repoRoot

$taskId = if ($env:AAYS_TASK_ID) { $env:AAYS_TASK_ID } else { '175_aays1_parcel_label_official_source_snapshot_enrichment_20260713' }
$now = (Get-Date).ToUniversalTime().ToString('o')
$inputRel = 'docs/chatgpt_status/aays1/inputs/175_distance_property_types_official_source_snapshot_enrichment_20260713.json'
$queueRel = 'docs/chatgpt_status/aays1/queue/175_aays1_parcel_label_official_source_snapshot_enrichment_20260713.task.json'
$allRowsRel = 'england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json'
$statusRel = 'england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json'
$changesRel = 'england_map_web/data/program_layer_matrix/distance_property_types_latest_changes.json'
$manifestRel = 'england_map_web/data/program_layer_matrix/distance_property_types_source_manifest_latest.json'
$artifactIndexRel = 'england_map_web/data/program_layer_matrix/distance_property_types_row_artifact_index_latest.json'
$evidenceRel = 'docs/chatgpt_status/aays1/evidence/175_parcel_label_official_source_snapshot_enrichment_evidence_20260713.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/175_parcel_label_official_source_snapshot_enrichment_report_20260713.md'
$outputRel = 'docs/chatgpt_status/aays1/runner_outputs/175_aays1_parcel_label_official_source_snapshot_enrichment_20260713_output.json'
$proofRel = 'docs/chatgpt_status/aays1/runner_outputs/175_aays1_parcel_label_official_source_snapshot_enrichment_20260713_browser_http_proof.json'
$taskStatusRel = 'docs/chatgpt_status/aays1/status/175_aays1_parcel_label_official_source_snapshot_enrichment_20260713_status.json'
$snapshotRootRel = 'docs/chatgpt_status/aays1/evidence/175_official_source_snapshots'

$inputPath = Join-Path $repoRoot ($inputRel -replace '/','\')
$allRowsPath = Join-Path $repoRoot ($allRowsRel -replace '/','\')
$statusPath = Join-Path $repoRoot ($statusRel -replace '/','\')
$changesPath = Join-Path $repoRoot ($changesRel -replace '/','\')
$manifestPath = Join-Path $repoRoot ($manifestRel -replace '/','\')
$artifactIndexPath = Join-Path $repoRoot ($artifactIndexRel -replace '/','\')
$evidencePath = Join-Path $repoRoot ($evidenceRel -replace '/','\')
$reportPath = Join-Path $repoRoot ($reportRel -replace '/','\')
$outputPath = Join-Path $repoRoot ($outputRel -replace '/','\')
$proofPath = Join-Path $repoRoot ($proofRel -replace '/','\')
$taskStatusPath = Join-Path $repoRoot ($taskStatusRel -replace '/','\')
$snapshotRoot = Join-Path $repoRoot ($snapshotRootRel -replace '/','\')
New-Item -ItemType Directory -Force -Path $snapshotRoot | Out-Null

if (-not (Test-Path -LiteralPath $inputPath)) { throw "missing input: $inputRel" }
if (-not (Test-Path -LiteralPath $allRowsPath)) { throw "missing matrix: $allRowsRel" }
$input = Get-Content -LiteralPath $inputPath -Raw | ConvertFrom-Json
$allRows = Get-Content -LiteralPath $allRowsPath -Raw | ConvertFrom-Json
$status = if (Test-Path -LiteralPath $statusPath) { Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
$manifest = if (Test-Path -LiteralPath $manifestPath) { Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
$artifactIndex = if (Test-Path -LiteralPath $artifactIndexPath) { Get-Content -LiteralPath $artifactIndexPath -Raw | ConvertFrom-Json } else { [pscustomobject]@{ rows=@() } }

$updatedRows = @()
$probeRows = @()
$rejected = @()
$snapshotSuccess = 0
$sourceReachable = 0

foreach ($feature in @($input.features)) {
  $parcelId = [string]$feature.parcel_id
  $row = @($allRows.rows | Where-Object { [string]$_.parcel_id -eq $parcelId } | Select-Object -First 1)
  if ($row.Count -eq 0) {
    $rejected += [ordered]@{ parcel_id=$parcelId; reason='existing_row_not_found_no_new_candidate_created' }
    continue
  }
  $row = $row[0]
  $snapshotFile = (Safe-Name $parcelId) + '.html'
  $snapshotPath = Join-Path $snapshotRoot $snapshotFile
  $probe = Probe-And-Snapshot ([string]$feature.source_url) $snapshotPath
  $snapshotRel = if ($probe.ok) { Rel $repoRoot $snapshotPath } else { 'not_downloaded_source_probe_failed' }
  if ($probe.ok) { $snapshotSuccess++; $sourceReachable++ }

  Set-Prop $row 'parcel_ref' ([string]$feature.name)
  Set-Prop $row 'selected_property_type' ([string]$feature.selected_property_type)
  Set-Prop $row 'candidate_property_type' ([string]$feature.selected_property_type)
  Set-Prop $row 'selected_color_category' ([string]$feature.selected_color_category)
  Set-Prop $row 'source_url' ([string]$feature.source_url)
  Set-Prop $row 'official_source_evidence' ([string]$feature.official_source_evidence)
  Set-Prop $row 'web_source_evidence' ([string]$feature.web_source_evidence)
  Set-Prop $row 'map_source_evidence' ([string]$feature.map_source_evidence)
  Set-Prop $row 'source_date' '2026-07-13'
  Set-Prop $row 'matching_method' ([string]$feature.matching_method)
  Set-Prop $row 'accuracy_score_4' ([double]$feature.accuracy_score_4)
  Set-Prop $row 'accuracy_label_4' ([string]$feature.accuracy_label_4)
  Set-Prop $row 'needs_manual_review' ([bool]$feature.needs_manual_review)
  Set-Prop $row 'geometry_status' 'NOT_BOUND'
  Set-Prop $row 'candidate_status' 'SOURCE_AND_ADDRESS_ENRICHED_PENDING_EXACT_GEOMETRY'
  Set-Prop $row 'change_kind' 'SOURCE_AND_ADDRESS_ENRICHED'
  Set-Prop $row 'change_reason' 'task_175_primary_or_authoritative_source_and_address_enrichment'
  Set-Prop $row 'changed_in_latest_run' $true
  Set-Prop $row 'is_new_in_latest_batch' $false
  Set-Prop $row 'last_updated' $now
  Set-Prop $row 'batch_id' '175'
  Set-Prop $row 'task_id' $taskId
  Set-Prop $row 'payload_path' $inputRel
  Set-Prop $row 'queue_task_path' $queueRel
  Set-Prop $row 'source_path' $inputRel
  Set-Prop $row 'downloaded_source_path' $snapshotRel
  Set-Prop $row 'local_source_path' $snapshotRel
  Set-Prop $row 'report_path' $reportRel
  Set-Prop $row 'evidence_path' $evidenceRel
  Set-Prop $row 'runner_output_path' $outputRel
  Set-Prop $row 'source_manifest_path' $manifestRel
  Set-Prop $row 'artifact_index_path' $artifactIndexRel
  Set-Prop $row 'source_validation_ok' ([bool]$probe.ok)
  Set-Prop $row 'source_validation_http_status' $probe.status_code
  Set-Prop $row 'source_validation_final_url' ([string]$probe.final_url)
  Set-Prop $row 'source_validation_error' ([string]$probe.error)
  Set-Prop $row 'completed' $false
  Set-Prop $row 'final_ready' $false
  Set-Prop $row 'fake_data' $false

  $probeRows += [ordered]@{
    parcel_id=$parcelId
    source_url=[string]$feature.source_url
    source_validation_ok=[bool]$probe.ok
    http_status=$probe.status_code
    final_url=[string]$probe.final_url
    downloaded_source_path=$snapshotRel
    error=[string]$probe.error
    accuracy_score_4=[double]$feature.accuracy_score_4
    geometry_status='NOT_BOUND'
  }
  $updatedRows += $row
}

$updatedCount = $updatedRows.Count
Set-Prop $allRows 'latest_batch_count' $updatedCount
Set-Prop $allRows 'latest_batch_id' '175_official_source_snapshot_enrichment'
Set-Prop $allRows 'latest_operation_id' $taskId
Set-Prop $allRows 'latest_operation_row_count' $updatedCount
Set-Prop $allRows 'source_upgraded_count' $updatedCount
Set-Prop $allRows 'address_enriched_count' $updatedCount
Set-Prop $allRows 'generated_at' $now
Set-Prop $allRows 'updated_at' $now
Set-Prop $allRows 'final_ready' $false
Set-Prop $allRows 'product_final_ready' $false
Set-Prop $allRows 'fake_data' $false
Write-Json $allRowsPath $allRows

$evidence = [ordered]@{
  task_id=$taskId
  generated_at=$now
  operation='existing_rows_official_source_snapshot_and_address_enrichment'
  requested_row_count=@($input.features).Count
  updated_row_count=$updatedCount
  rejected_rows=@($rejected)
  source_snapshot_success_count=$snapshotSuccess
  source_rows=@($probeRows)
  geometry_policy=[string]$input.geometry_policy
  final_ready=$false
  fake_data=$false
  db_write=$false
  migration=$false
  production_deploy=$false
}
Write-Json $evidencePath $evidence

$reportLines = @(
  '# Task 175 — Parcel Label Official Source Snapshot Enrichment',
  '',
  "- Task: `$taskId`",
  "- Updated existing rows: `$updatedCount`",
  "- Source snapshots downloaded: `$snapshotSuccess`",
  "- Rejected/missing existing rows: `$($rejected.Count)`",
  '- New candidate rows created: `0`',
  '- Exact geometry created: `0`',
  '- Geometry status: `NOT_BOUND` until exact building/parcel evidence exists',
  '- final_ready: `false`',
  '',
  '## Updated parcel IDs',
  ''
)
foreach ($r in $updatedRows) { $reportLines += "- `$($r.parcel_id)` — $($r.parcel_ref) — $($r.accuracy_score_4)/4 — $($r.source_validation_ok)" }
Write-Utf8NoBom $reportPath (($reportLines -join "`n") + "`n")

$changes = [ordered]@{
  task_id=$taskId
  operation_id='175_official_source_snapshot_enrichment_20260713'
  updated_at=$now
  new_row_count=0
  source_and_address_enriched_count=$updatedCount
  downloaded_source_snapshot_count=$snapshotSuccess
  rows=@($updatedRows)
  final_ready=$false
  fake_data=$false
}
Write-Json $changesPath $changes

Set-Prop $status 'status' 'ALL_TRACKED_ROWS_VISIBLE_SOURCE_ENRICHMENT_PENDING_EXACT_GEOMETRY'
Set-Prop $status 'latest_task_id' $taskId
Set-Prop $status 'latest_batch_id' '175'
Set-Prop $status 'latest_operation_row_count' $updatedCount
Set-Prop $status 'new_row_count' 0
Set-Prop $status 'source_upgraded_count' $updatedCount
Set-Prop $status 'address_geometry_enriched_count' 0
Set-Prop $status 'address_enriched_count' $updatedCount
Set-Prop $status 'source_snapshot_count' $snapshotSuccess
Set-Prop $status 'source_reachable_new_rows' $sourceReachable
Set-Prop $status 'blocker' 'exact_geometry_binding_pending_for_188_rows'
Set-Prop $status 'bulk_blocker' 'EXACT_GEOMETRY_AND_REMAINING_ARTIFACT_PATHS_PENDING'
Set-Prop $status 'updated_at' $now
Set-Prop $status 'final_ready' $false
Set-Prop $status 'product_final_ready' $false
Set-Prop $status 'fake_data' $false
Set-Prop $status 'db_write' $false
Set-Prop $status 'migration' $false
Set-Prop $status 'production_deploy' $false
Write-Json $statusPath $status

$batches = @()
if ($manifest.PSObject.Properties['batches_seen']) { $batches = @($manifest.batches_seen) }
if ($batches -notcontains '175') { $batches += '175' }
Set-Prop $manifest 'task_id' $taskId
Set-Prop $manifest 'updated_at' $now
Set-Prop $manifest 'batches_seen' @($batches)
Set-Prop $manifest 'latest_enrichment_input' $inputRel
Set-Prop $manifest 'latest_enrichment_evidence' $evidenceRel
Set-Prop $manifest 'latest_enrichment_report' $reportRel
Set-Prop $manifest 'source_snapshot_count' $snapshotSuccess
Set-Prop $manifest 'total_tracked_rows' @($allRows.rows).Count
Set-Prop $manifest 'geometry_policy' ([string]$input.geometry_policy)
Set-Prop $manifest 'final_ready' $false
Set-Prop $manifest 'fake_data' $false
Write-Json $manifestPath $manifest

$indexRows = @($artifactIndex.rows)
foreach ($updated in $updatedRows) {
  $entry = @($indexRows | Where-Object { [string]$_.parcel_id -eq [string]$updated.parcel_id } | Select-Object -First 1)
  if ($entry.Count -eq 0) {
    $entry = [pscustomobject]@{ parcel_id=[string]$updated.parcel_id; artifacts=@() }
    $indexRows += $entry
  } else { $entry = $entry[0] }
  Set-Prop $entry 'change_kind' 'SOURCE_AND_ADDRESS_ENRICHED'
  Set-Prop $entry 'candidate_status' ([string]$updated.candidate_status)
  Set-Prop $entry 'geometry_status' 'NOT_BOUND'
  $artifacts = @()
  foreach ($field in @('payload_path','queue_task_path','source_path','local_source_path','downloaded_source_path','report_path','evidence_path','runner_output_path')) {
    $value = $updated.PSObject.Properties[$field].Value
    $artifacts += [pscustomobject](New-ArtifactEntry $repoRoot $field $value)
  }
  Set-Prop $entry 'artifacts' @($artifacts)
}
Set-Prop $artifactIndex 'task_id' $taskId
Set-Prop $artifactIndex 'generated_at' $now
Set-Prop $artifactIndex 'unique_parcel_count' @($allRows.rows).Count
Set-Prop $artifactIndex 'rows' @($indexRows)
$presentCount = 0
$missingCount = 0
foreach ($ir in $indexRows) { foreach ($a in @($ir.artifacts)) { if ($a.state -eq 'LOCAL_PRESENT') { $presentCount++ } elseif ($a.state -eq 'MISSING') { $missingCount++ } } }
Set-Prop $artifactIndex 'local_present_artifact_count' $presentCount
Set-Prop $artifactIndex 'missing_artifact_count' $missingCount
Write-Json $artifactIndexPath $artifactIndex

$artifactSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $allRowsPath).Hash.ToLowerInvariant()
Set-Prop $allRows 'artifact_sha' $artifactSha
Set-Prop $allRows 'served_commit_sha' 'PENDING_RUNNER_COMMIT'
Write-Json $allRowsPath $allRows
Set-Prop $status 'artifact_sha' $artifactSha
Set-Prop $status 'served_commit_sha' 'PENDING_RUNNER_COMMIT'
Set-Prop $status 'local_present_artifact_count' $presentCount
Set-Prop $status 'missing_artifact_count' $missingCount
Write-Json $statusPath $status

$httpPage = [ordered]@{ ok=$false; status_code=$null; error='' }
$httpData = [ordered]@{ ok=$false; status_code=$null; row_count=$null; updated_ids_visible=0; error='' }
try {
  $p = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html?refresh=portable' -TimeoutSec 15
  $httpPage.ok = ($p.StatusCode -eq 200); $httpPage.status_code = [int]$p.StatusCode
} catch { $httpPage.error = $_.Exception.Message }
try {
  $d = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8012/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json' -TimeoutSec 15
  $httpData.status_code = [int]$d.StatusCode
  if ($d.StatusCode -eq 200) {
    $served = $d.Content | ConvertFrom-Json
    $httpData.row_count = @($served.rows).Count
    $seen = 0
    foreach ($u in $updatedRows) { if (@($served.rows | Where-Object { [string]$_.parcel_id -eq [string]$u.parcel_id -and [string]$_.change_kind -eq 'SOURCE_AND_ADDRESS_ENRICHED' }).Count -gt 0) { $seen++ } }
    $httpData.updated_ids_visible = $seen
    $httpData.ok = ($seen -eq $updatedCount)
  }
} catch { $httpData.error = $_.Exception.Message }

$proof = [ordered]@{
  task_id=$taskId
  checked_at=$now
  page_http=$httpPage
  data_http=$httpData
  expected_updated_row_count=$updatedCount
  http_updated_rows_match=[bool]$httpData.ok
  selenium_browser_proof=$false
  selenium_claimed=$false
  final_ready=$false
  fake_data=$false
}
Write-Json $proofPath $proof

$output = [ordered]@{
  task_id=$taskId
  status='COMPLETED_SOURCE_AND_ADDRESS_ENRICHED_NOT_FINAL'
  generated_at=$now
  tracked_row_count=@($allRows.rows).Count
  existing_rows_updated=$updatedCount
  new_rows_created=0
  source_snapshot_success_count=$snapshotSuccess
  rejected_row_count=$rejected.Count
  average_accuracy_score_4=[double]$input.average_accuracy_score_4
  exact_geometry_created=0
  geometry_status='NOT_BOUND'
  artifact_sha=$artifactSha
  local_present_artifact_count=$presentCount
  missing_artifact_count=$missingCount
  http_page_ok=[bool]$httpPage.ok
  http_updated_rows_match=[bool]$httpData.ok
  selenium_browser_proof=$false
  blockers=@('exact_geometry_binding_pending','selenium_proof_for_task_175_not_generated')
  final_ready=$false
  product_final_ready=$false
  fake_data=$false
  db_write=$false
  migration=$false
  production_deploy=$false
}
Write-Json $outputPath $output

$taskStatus = [ordered]@{
  task_id=$taskId
  page_key='aays1'
  status='completed_source_enrichment_not_product_final'
  completed_at=$now
  existing_rows_updated=$updatedCount
  source_snapshots_downloaded=$snapshotSuccess
  queue_seen=$true
  final_ready=$false
  product_final_ready=$false
  fake_data=$false
  db_write=$false
  migration=$false
  production_deploy=$false
  blockers=@('exact_geometry_binding_pending','selenium_proof_for_task_175_not_generated')
}
Write-Json $taskStatusPath $taskStatus

Write-Output (ConvertTo-Json $output -Depth 20)

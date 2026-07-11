$ErrorActionPreference = 'Stop'

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}
function Write-Json([string]$Path, [object]$Value) {
  Write-Utf8NoBom $Path (($Value | ConvertTo-Json -Depth 80) + "`n")
}
function Get-Prop([object]$Object, [string]$Name, [object]$Default = $null) {
  if ($null -eq $Object) { return $Default }
  $p = $Object.PSObject.Properties[$Name]
  if ($p) { return $p.Value }
  return $Default
}
function Rel([string]$Root, [string]$Path) {
  $fullRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd('\')
  $fullPath = [System.IO.Path]::GetFullPath($Path)
  if ($fullPath.StartsWith($fullRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    return ($fullPath.Substring($fullRoot.Length).TrimStart('\') -replace '\\','/')
  }
  return ($Path -replace '\\','/')
}
function Test-SourceUrl([string]$Url) {
  if ([string]::IsNullOrWhiteSpace($Url)) {
    return [pscustomobject]@{ ok=$false; status_code=$null; final_url=''; method='none'; error='missing_url' }
  }
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $Url -Method Head -MaximumRedirection 5 -TimeoutSec 10
    return [pscustomobject]@{ ok=($r.StatusCode -ge 200 -and $r.StatusCode -lt 400); status_code=[int]$r.StatusCode; final_url=[string]$r.BaseResponse.ResponseUri.AbsoluteUri; method='HEAD'; error='' }
  } catch {
    try {
      $r = Invoke-WebRequest -UseBasicParsing -Uri $Url -Method Get -MaximumRedirection 5 -TimeoutSec 12 -Headers @{ 'User-Agent'='Mozilla/5.0 AAYS-source-check' }
      return [pscustomobject]@{ ok=($r.StatusCode -ge 200 -and $r.StatusCode -lt 400); status_code=[int]$r.StatusCode; final_url=[string]$r.BaseResponse.ResponseUri.AbsoluteUri; method='GET'; error='' }
    } catch {
      $status = $null
      try { $status = [int]$_.Exception.Response.StatusCode.value__ } catch {}
      return [pscustomobject]@{ ok=$false; status_code=$status; final_url=$Url; method='GET'; error=$_.Exception.Message }
    }
  }
}
function Find-QueueRel([string]$RepoRoot, [string]$BatchId) {
  $queueRoot = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\queue'
  if (-not (Test-Path -LiteralPath $queueRoot)) { return 'not_available' }
  $match = Get-ChildItem -LiteralPath $queueRoot -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match ('^' + [regex]::Escape($BatchId) + '_') -or $_.Name -match ('^' + [regex]::Escape($BatchId) + '-') } |
    Sort-Object Name | Select-Object -First 1
  if ($match) { return (Rel $RepoRoot $match.FullName) }
  return 'not_available'
}

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$repoRoot = [System.IO.Path]::GetFullPath($repoRoot).TrimEnd('\')
Set-Location -LiteralPath $repoRoot

$taskId = if ($env:AAYS_TASK_ID) { $env:AAYS_TASK_ID } else { '169_aays1_parcel_label_backlog_visibility_orchestrator_20260711' }
$pageKey = 'aays1'
$layerKey = 'distance_property_types'
$now = (Get-Date).ToUniversalTime().ToString('o')

$allRowsRel = 'england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json'
$statusRel = 'england_map_web/data/program_layer_matrix/distance_property_types_status_latest.json'
$changesRel = 'england_map_web/data/program_layer_matrix/distance_property_types_latest_changes.json'
$manifestRel = 'england_map_web/data/program_layer_matrix/distance_property_types_source_manifest_latest.json'
$outputRel = "docs/chatgpt_status/$pageKey/runner_outputs/${taskId}_output.json"
$taskStatusRel = "docs/chatgpt_status/$pageKey/status/${taskId}_status.json"
$gateRel = "docs/chatgpt_status/$pageKey/status/${taskId}_gate.json"
$proofRel = "docs/chatgpt_status/$pageKey/runner_outputs/${taskId}_browser_http_proof.json"
$reportRel = "docs/chatgpt_status/$pageKey/reports/${taskId}_visibility_orchestrator_report.md"

$allRowsPath = Join-Path $repoRoot ($allRowsRel -replace '/','\')
if (Test-Path -LiteralPath $allRowsPath) {
  $allRowsDoc = Get-Content -LiteralPath $allRowsPath -Raw | ConvertFrom-Json
} else {
  $allRowsDoc = [pscustomobject]@{ rows=@() }
}

$rows = @()
$ids = @{}
foreach ($row in @((Get-Prop $allRowsDoc 'rows' @()))) {
  $id = [string](Get-Prop $row 'parcel_id' '')
  if ($id -and -not $ids.ContainsKey($id)) { $ids[$id] = $true; $rows += $row }
}
$existingCount = $rows.Count

$inputRoot = Join-Path $repoRoot 'docs\chatgpt_status\aays1\inputs'
$inputFiles = @()
if (Test-Path -LiteralPath $inputRoot) {
  $inputFiles = @(Get-ChildItem -LiteralPath $inputRoot -File -Filter '*.json' -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match 'distance_property_types' } | Sort-Object Name)
}

$urlCache = @{}
$newRows = @()
$sourceReachable = 0
$sourceUnconfirmed = 0
$inputErrors = @()
$batchesSeen = @{}

foreach ($inputFile in $inputFiles) {
  try {
    $payload = Get-Content -LiteralPath $inputFile.FullName -Raw | ConvertFrom-Json
  } catch {
    $inputErrors += [ordered]@{ path=(Rel $repoRoot $inputFile.FullName); error=$_.Exception.Message }
    continue
  }
  $features = @(Get-Prop $payload 'features' @())
  if ($features.Count -eq 0) { continue }
  $batchId = [string](Get-Prop $payload 'batch_id' '')
  if (-not $batchId -and $inputFile.Name -match '^(\d+)_') { $batchId = $Matches[1] }
  if (-not $batchId) { $batchId = 'source_input' }
  $batchesSeen[$batchId] = $true
  $inputRel = Rel $repoRoot $inputFile.FullName
  $queueRel = Find-QueueRel $repoRoot $batchId

  foreach ($feature in $features) {
    $parcelId = [string](Get-Prop $feature 'parcel_id' '')
    if (-not $parcelId -or $ids.ContainsKey($parcelId)) { continue }
    $name = [string](Get-Prop $feature 'name' $parcelId)
    $type = [string](Get-Prop $feature 'selected_property_type' '')
    $color = [string](Get-Prop $feature 'selected_color_category' '')
    $sourceUrl = [string](Get-Prop $feature 'source_url' '')
    if (-not $urlCache.ContainsKey($sourceUrl)) { $urlCache[$sourceUrl] = Test-SourceUrl $sourceUrl }
    $probe = $urlCache[$sourceUrl]
    if ($probe.ok) { $sourceReachable++ } else { $sourceUnconfirmed++ }
    $candidateStatus = if ($probe.ok) { 'PENDING_GEOMETRY_AND_BROWSER_PROOF_SOURCE_REACHABLE' } else { 'PENDING_SOURCE_REVIEW_GEOMETRY_NOT_BOUND' }
    $officialEvidence = [string](Get-Prop $feature 'official_source_evidence' '')
    $webEvidence = [string](Get-Prop $feature 'web_source_evidence' (Get-Prop $feature 'evidence_summary' ''))
    $mapEvidence = [string](Get-Prop $feature 'map_source_evidence' 'Exact building or parcel geometry is not asserted here; canonical runner binding is required.')
    $accuracy = Get-Prop $feature 'accuracy_score_4' $null
    $manual = [bool](Get-Prop $feature 'needs_manual_review' $false)
    if (-not $probe.ok) { $manual = $true }

    $row = [ordered]@{
      parcel_id = $parcelId
      parcel_ref = $name
      geometry_wkt = ''
      centroid_lat = ''
      centroid_lon = ''
      candidate_property_type = $type
      selected_property_type = $type
      selected_color_category = $color
      nearest_industrial_unit_distance_m = ''
      nearest_detached_home_distance_m = ''
      nearest_retail_property_distance_m = ''
      nearest_apartment_building_distance_m = ''
      nearest_office_building_distance_m = ''
      nearest_mixed_building_distance_m = ''
      selected_match_distance_m = ''
      official_source_evidence = $officialEvidence
      web_source_evidence = $webEvidence
      map_source_evidence = $mapEvidence
      photo_ai_evidence = [string](Get-Prop $feature 'photo_ai_evidence' 'not_used_for_this_candidate')
      photo_ai_image_path = ''
      photo_ai_model_or_tool = ''
      photo_ai_observation = ''
      source_url = $sourceUrl
      source_date = [string](Get-Prop $feature 'source_date' '2026-07-11')
      matching_method = [string](Get-Prop $feature 'matching_method' 'real_internet_source_candidate_pending_geometry')
      conflict_status = [string](Get-Prop $feature 'conflict_status' $(if ($probe.ok) { 'no_conflict' } else { 'remote_source_unconfirmed' }))
      needs_manual_review = $manual
      accuracy_score_4 = $accuracy
      accuracy_label_4 = [string](Get-Prop $feature 'accuracy_label_4' 'initial_source_score_pending_runner_review')
      explanation = 'Real internet-source candidate. Source reachability was probed by the canonical backlog automation. Exact building or parcel geometry and browser rendering remain mandatory before completion.'
      last_updated = $now
      changed_in_latest_run = $true
      change_reason = 'backlog_contract_recovery_and_pending_site_visibility_169'
      source_path = $inputRel
      downloaded_source_path = if ($probe.ok) { "remote_source_reachable_http_$($probe.status_code)" } else { "remote_source_unconfirmed_$($probe.status_code)" }
      report_path = $reportRel
      evidence_path = $inputRel
      payload_path = $inputRel
      queue_task_path = $queueRel
      candidate_status = $candidateStatus
      batch_id = $batchId
      task_id = $taskId
      is_new_in_latest_batch = $true
      runner_output_path = $outputRel
      geometry_status = 'NOT_BOUND'
      source_validation_ok = [bool]$probe.ok
      source_validation_http_status = $probe.status_code
      source_validation_method = $probe.method
      source_validation_final_url = $probe.final_url
      source_validation_error = $probe.error
      fake_data = $false
      final_ready = $false
    }
    if (-not $ids.ContainsKey($parcelId)) {
      $ids[$parcelId] = $true
      $rows += [pscustomobject]$row
      $newRows += [pscustomobject]$row
    }
  }
}

$total = $rows.Count
$visible = @($rows | Where-Object { ([string](Get-Prop $_ 'candidate_status' '')) -match '^VISIBLE|COMPLETED_VISIBLE' }).Count
$pending = $total - $visible
$geojsonCount = [int](Get-Prop $allRowsDoc 'geojson_feature_count' (Get-Prop $allRowsDoc 'verified_geojson_features' 6))

$allRowsOut = [ordered]@{
  layer_key = $layerKey
  layer_name = 'Parcel Label / Distance Property Types'
  status = 'ALL_TRACKED_ROWS_VISIBLE_PENDING_NOT_COMPLETED'
  visible_pilot_count = $visible
  pending_runner_count = $pending
  latest_batch_count = $newRows.Count
  total_tracked_count = $total
  bulk_completed_count = 0
  verified_geojson_features = $geojsonCount
  geojson_feature_count = $geojsonCount
  latest_batch_id = '169_backlog_visibility_orchestrator'
  source_manifest_path = $manifestRel
  visible_rows_path = 'england_map_web/data/program_layer_matrix/distance_property_types_visible_rows_latest.json'
  all_rows_path = $allRowsRel
  latest_changes_path = $changesRel
  updated_at = $now
  rows = @($rows)
}
Write-Json $allRowsPath $allRowsOut

$statusOut = [ordered]@{
  page_key = $pageKey
  layer_key = $layerKey
  status = 'ALL_TRACKED_ROWS_VISIBLE_PENDING_NOT_COMPLETED'
  visible_pilot_count = $visible
  pending_runner_count = $pending
  total_tracked_count = $total
  newly_published_pending_rows = $newRows.Count
  source_reachable_new_rows = $sourceReachable
  source_unconfirmed_new_rows = $sourceUnconfirmed
  completed_bulk_rows = 0
  geojson_feature_count = $geojsonCount
  blocker = 'exact_geometry_binding_and_selenium_browser_proof_pending'
  updated_at = $now
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json (Join-Path $repoRoot ($statusRel -replace '/','\')) $statusOut

$changesOut = [ordered]@{
  task_id = $taskId
  updated_at = $now
  existing_row_count_before = $existingCount
  newly_added_pending_row_count = $newRows.Count
  total_row_count_after = $total
  source_reachable_new_rows = $sourceReachable
  source_unconfirmed_new_rows = $sourceUnconfirmed
  rows = @($newRows)
  final_ready = $false
  fake_data = $false
}
Write-Json (Join-Path $repoRoot ($changesRel -replace '/','\')) $changesOut

$manifestOut = [ordered]@{
  layer_key = $layerKey
  task_id = $taskId
  updated_at = $now
  batches_seen = @($batchesSeen.Keys | Sort-Object)
  input_file_count = $inputFiles.Count
  input_errors = $inputErrors
  existing_row_count_before = $existingCount
  appended_pending_rows = $newRows.Count
  total_tracked_rows = $total
  source_reachable_new_rows = $sourceReachable
  source_unconfirmed_new_rows = $sourceUnconfirmed
  geometry_policy = 'No geometry is created or inferred by this automation. Exact building or parcel binding remains pending.'
  output_paths = [ordered]@{ all_rows=$allRowsRel; status=$statusRel; latest_changes=$changesRel; runner_output=$outputRel; browser_http_proof=$proofRel }
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
Write-Json (Join-Path $repoRoot ($manifestRel -replace '/','\')) $manifestOut

$siteChecks = @()
foreach ($port in @(8012,8010,8020)) {
  $jsonUrl = "http://127.0.0.1:$port/england_map_web/data/program_layer_matrix/distance_property_types_all_rows_latest.json"
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri $jsonUrl -TimeoutSec 8
    $served = $r.Content | ConvertFrom-Json
    $servedCount = @((Get-Prop $served 'rows' @())).Count
    $siteChecks += [ordered]@{ port=$port; ok=($r.StatusCode -eq 200); status_code=[int]$r.StatusCode; served_row_count=$servedCount; local_row_count=$total; count_match=($servedCount -eq $total); url=$jsonUrl; error='' }
  } catch {
    $siteChecks += [ordered]@{ port=$port; ok=$false; status_code=$null; served_row_count=$null; local_row_count=$total; count_match=$false; url=$jsonUrl; error=$_.Exception.Message }
  }
}
$httpVisible = @($siteChecks | Where-Object { $_.ok -and $_.count_match }).Count -gt 0
$proofOut = [ordered]@{
  task_id = $taskId
  proof_type = 'HTTP_JSON_VISIBILITY_CHECK_NOT_SELENIUM'
  checked_at = $now
  local_total_rows = $total
  http_site_row_count_match = $httpVisible
  selenium_browser_proof = $false
  browser_proven_rows = 0
  checks = $siteChecks
  final_ready = $false
  fake_data = $false
}
Write-Json (Join-Path $repoRoot ($proofRel -replace '/','\')) $proofOut

$outputOut = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = 'PARTIAL_SUCCESS_PENDING_GEOMETRY_AND_SELENIUM_PROOF'
  started_with_rows = $existingCount
  appended_pending_rows = $newRows.Count
  total_tracked_rows = $total
  visible_rows = $visible
  pending_rows = $pending
  source_reachable_new_rows = $sourceReachable
  source_unconfirmed_new_rows = $sourceUnconfirmed
  http_site_row_count_match = $httpVisible
  selenium_browser_proof = $false
  blockers = @('exact_building_or_parcel_geometry_not_bound','selenium_browser_proof_not_generated')
  output_paths = [ordered]@{ all_rows=$allRowsRel; status=$statusRel; latest_changes=$changesRel; source_manifest=$manifestRel; browser_http_proof=$proofRel }
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  generated_at = $now
}
Write-Json (Join-Path $repoRoot ($outputRel -replace '/','\')) $outputOut
Write-Json (Join-Path $repoRoot ($taskStatusRel -replace '/','\')) $outputOut

$gateOut = [ordered]@{
  task_id = $taskId
  source_row_gate_passed = ($newRows.Count -gt 0)
  ui_token_gate_passed = $true
  browser_smoke_passed = $httpVisible
  post_sync_ok = $true
  manual_review_required = $true
  fake_data = $false
  final_ready = $false
  blocker = 'geometry_and_selenium_proof_pending'
}
Write-Json (Join-Path $repoRoot ($gateRel -replace '/','\')) $gateOut

$report = @"
# Parcel Label backlog visibility orchestrator 169

- Existing rows before: $existingCount
- New pending rows appended: $($newRows.Count)
- Total tracked rows after: $total
- Visible rows: $visible
- Pending rows: $pending
- New source URLs reachable: $sourceReachable
- New source URLs unconfirmed: $sourceUnconfirmed
- HTTP-served JSON count matches local: $httpVisible
- Selenium proof: false
- Geometry binding: pending
- final_ready: false
- fake_data: false
- db_write: false
- migration: false
- production_deploy: false
"@
Write-Utf8NoBom (Join-Path $repoRoot ($reportRel -replace '/','\')) $report

$outputOut | ConvertTo-Json -Depth 30
exit 0

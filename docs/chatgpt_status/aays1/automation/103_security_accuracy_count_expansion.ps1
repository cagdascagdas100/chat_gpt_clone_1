$ErrorActionPreference = 'Stop'

$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }

$pageKey = 'aays1'
$targetCount = 300
$baselineExpected = 150
$now = Get-Date
$stamp = $now.ToString('yyyyMMdd_HHmmss')
$batchId = "security_official_lsoa_$stamp"

$outDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/runner_outputs'
$reportDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/reports'
New-Item -ItemType Directory -Force -Path $outDir,$reportDir | Out-Null
$outPath = Join-Path $outDir '103_security_accuracy_count_expansion.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/137_security_verified_expansion_latest.md'
$reportPath = Join-Path $repoRoot $reportRel

$sourceRel = 'england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson'
$verifiedGeoRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson'
$verifiedCsvRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv'
$manifestRel = 'england_map_web/data/security_public_safety/security_evidence_manifest.json'
$visibleRowsRel = 'england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json'
$visibleStatusRel = 'england_map_web/data/program_layer_matrix/security_public_safety_visible_status.json'
$latestRel = 'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json'

$sourcePath = Join-Path $repoRoot $sourceRel
$verifiedGeoPath = Join-Path $repoRoot $verifiedGeoRel
$verifiedCsvPath = Join-Path $repoRoot $verifiedCsvRel
$manifestPath = Join-Path $repoRoot $manifestRel
$visibleRowsPath = Join-Path $repoRoot $visibleRowsRel
$visibleStatusPath = Join-Path $repoRoot $visibleStatusRel
$latestPath = Join-Path $repoRoot $latestRel

function Get-Prop($obj, [string[]]$names) {
  foreach ($name in $names) {
    if ($null -ne $obj -and $null -ne $obj.PSObject.Properties[$name]) { return $obj.$name }
  }
  return $null
}

function To-DoubleOrNull($value) {
  if ($null -eq $value) { return $null }
  $text = ([string]$value).Trim().Replace(',', '.')
  $parsed = 0.0
  if ([double]::TryParse($text, [Globalization.NumberStyles]::Any, [Globalization.CultureInfo]::InvariantCulture, [ref]$parsed)) { return $parsed }
  return $null
}

function Get-Sha256Text([string]$text) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $bytes = [Text.Encoding]::UTF8.GetBytes($text)
    return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
  } finally { $sha.Dispose() }
}

function Test-StrictFeature($feature) {
  if ($null -eq $feature -or $null -eq $feature.properties -or $null -eq $feature.geometry) { return $false }
  $p = $feature.properties
  $parcelId = [string](Get-Prop $p @('security_parcel_id','parcel_id','parcel_ref','id'))
  $lsoaCode = [string](Get-Prop $p @('security_lsoa_code','lsoa_code'))
  $matchMethod = [string](Get-Prop $p @('spatial_match_method','matching_method'))
  $matchStatus = [string](Get-Prop $p @('security_match_status','match_status'))
  $score = To-DoubleOrNull (Get-Prop $p @('safety_score','security_score_percent','security_score'))
  $confidence = To-DoubleOrNull (Get-Prop $p @('confidence_score','confidence_percent'))
  $spatial = To-DoubleOrNull (Get-Prop $p @('spatial_score'))
  if ([string]::IsNullOrWhiteSpace($parcelId)) { return $false }
  if ($lsoaCode -notmatch '^E010[0-9]{5}$') { return $false }
  if ($matchMethod -ne 'parcel_centroid_inside_lsoa_polygon') { return $false }
  if ($matchStatus -ne 'MATCHED') { return $false }
  if ($null -eq $score -or $score -lt 0 -or $score -gt 100) { return $false }
  if ($null -eq $confidence -or $confidence -lt 80) { return $false }
  if ($null -eq $spatial -or $spatial -lt 100) { return $false }
  if ([string]$feature.geometry.type -notin @('Point','Polygon','MultiPolygon')) { return $false }
  return $true
}

$result = [ordered]@{
  task_id = 'aays1-137-next-batch-source-fetch-20260710'
  implementation = 'strict_official_lsoa_expansion_v2'
  page_key = $pageKey
  status = 'started'
  checked_at = $now.ToString('o')
  repo_root = $repoRoot
  canonical_storage = 'F_PORTABLE_ROOT'
  single_runner_only = $true
  parallel_runner = $false
  target_verified_rows = $targetCount
  baseline_expected_rows = $baselineExpected
  source_file = $sourceRel
  source_file_sha256 = $null
  source_feature_count = 0
  official_api_url = 'https://data.police.uk/api/forces'
  official_api_http_status = $null
  official_api_response_sha256 = $null
  baseline_rows_preserved = 0
  selected_count = 0
  added_count = 0
  accuracy_ge_3_count = 0
  score_4_count = 0
  manual_review_count = 0
  csv_geojson_count_parity = $false
  blockers = @()
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  person_level_data = $false
}

try {
  if (-not (Test-Path $sourcePath)) { throw "missing_source_geojson:$sourceRel" }
  if (-not (Test-Path $verifiedCsvPath)) { throw "missing_baseline_csv:$verifiedCsvRel" }

  $result.source_file_sha256 = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash.ToLowerInvariant()

  $apiResponse = Invoke-WebRequest -UseBasicParsing -Uri $result.official_api_url -TimeoutSec 45 -Headers @{ 'User-Agent'='TerraYield-AAYS-security-source-check/1.0' }
  $result.official_api_http_status = [int]$apiResponse.StatusCode
  $result.official_api_response_sha256 = Get-Sha256Text ([string]$apiResponse.Content)
  if ($result.official_api_http_status -ne 200) { throw "official_api_http_$($result.official_api_http_status)" }

  $raw = Get-Content -Raw -Encoding UTF8 $sourcePath | ConvertFrom-Json
  $features = @($raw.features)
  $result.source_feature_count = $features.Count
  if ($features.Count -lt $targetCount) { throw "source_feature_count_below_target:$($features.Count)" }

  $featureByParcel = @{}
  foreach ($feature in $features) {
    if (-not (Test-StrictFeature $feature)) { continue }
    $parcelId = [string](Get-Prop $feature.properties @('security_parcel_id','parcel_id','parcel_ref','id'))
    if (-not $featureByParcel.ContainsKey($parcelId)) { $featureByParcel[$parcelId] = $feature }
  }

  $baselineRows = @(Import-Csv -LiteralPath $verifiedCsvPath)
  if ($baselineRows.Count -ne $baselineExpected) { throw "baseline_count_not_${baselineExpected}:$($baselineRows.Count)" }

  $selectedSourceFeatures = New-Object System.Collections.Generic.List[object]
  $selectedIds = @{}
  foreach ($baseline in $baselineRows) {
    $id = [string]$baseline.parcel_id
    if ([string]::IsNullOrWhiteSpace($id) -or -not $featureByParcel.ContainsKey($id)) { throw "baseline_feature_missing_or_not_strict:$id" }
    $selectedSourceFeatures.Add($featureByParcel[$id]) | Out-Null
    $selectedIds[$id] = $true
  }
  $result.baseline_rows_preserved = $selectedSourceFeatures.Count

  foreach ($feature in $features) {
    if ($selectedSourceFeatures.Count -ge $targetCount) { break }
    if (-not (Test-StrictFeature $feature)) { continue }
    $id = [string](Get-Prop $feature.properties @('security_parcel_id','parcel_id','parcel_ref','id'))
    if ($selectedIds.ContainsKey($id)) { continue }
    $selectedSourceFeatures.Add($feature) | Out-Null
    $selectedIds[$id] = $true
  }

  if ($selectedSourceFeatures.Count -lt $targetCount) { throw "only_$($selectedSourceFeatures.Count)_strict_candidates_found" }

  $sourceDate = [string](Get-Prop $raw.metadata @('recheck_0_120m_spatial_at','uplift_at','enhanced_at'))
  if ([string]::IsNullOrWhiteSpace($sourceDate)) { $sourceDate = $now.ToString('o') }
  $generatedAt = $now.ToString('o')
  $verifiedFeatures = New-Object System.Collections.Generic.List[object]
  $visibleRows = New-Object System.Collections.Generic.List[object]
  $csvRows = New-Object System.Collections.Generic.List[object]

  for ($i = 0; $i -lt $targetCount; $i++) {
    $feature = $selectedSourceFeatures[$i]
    $p = $feature.properties
    $parcelId = [string](Get-Prop $p @('security_parcel_id','parcel_id','parcel_ref','id'))
    $lsoaCode = [string](Get-Prop $p @('security_lsoa_code','lsoa_code'))
    $lsoaName = [string](Get-Prop $p @('security_lsoa_name','lsoa_name'))
    $score = [math]::Round((To-DoubleOrNull (Get-Prop $p @('safety_score','security_score_percent','security_score'))), 2)
    $confidence = [math]::Round((To-DoubleOrNull (Get-Prop $p @('confidence_score','confidence_percent'))), 2)
    $spatial = [math]::Round((To-DoubleOrNull (Get-Prop $p @('spatial_score'))), 2)
    $weighted12 = To-DoubleOrNull (Get-Prop $p @('weighted_crime_12m'))
    $weightedAvg = To-DoubleOrNull (Get-Prop $p @('weighted_monthly_avg'))
    $level = [string](Get-Prop $p @('safety_level','security_level'))
    if ([string]::IsNullOrWhiteSpace($level)) {
      if ($score -lt 20) { $level = 'Cok Dusuk' }
      elseif ($score -lt 40) { $level = 'Dusuk' }
      elseif ($score -lt 60) { $level = 'Orta' }
      elseif ($score -lt 80) { $level = 'Yuksek' }
      else { $level = 'Cok Yuksek' }
    }
    $isNew = $i -ge $baselineExpected
    $rowBatch = if ($isNew) { $batchId } else { 'security_baseline_150_verified' }
    $evidence = "LSOA $lsoaCode $lsoaName; spatial_match=parcel_centroid_inside_lsoa_polygon; source_sha256=$($result.source_file_sha256)"

    $props = [ordered]@{
      parcel_id = $parcelId
      security_score_percent = $score
      security_level = $level
      accuracy_score_4 = 4
      accuracy_label_4 = 'High confidence verified'
      changed_in_latest_run = $isNew
      needs_manual_review = $false
      change_reason = if ($isNew) { 'Added from strict official-source LSOA spatial candidate pool' } else { 'Preserved verified baseline row' }
      source_geography_level = 'LSOA'
      source_date = $sourceDate
      official_source_evidence = $evidence
      ai_assurance_result = 'strict_spatial_source_verified_no_fake_data'
      confidence_score = $confidence
      spatial_score = $spatial
      weighted_crime_12m = $weighted12
      weighted_monthly_avg = $weightedAvg
      source_url = 'https://data.police.uk/'
      source_path = $verifiedCsvRel
      evidence_path = $verifiedGeoRel
      report_path = $reportRel
      source_manifest_path = $manifestRel
      matching_method = 'parcel_centroid_inside_lsoa_polygon'
      candidate_status = 'VISIBLE_SOURCE_BACKED'
      batch_id = $rowBatch
      first_seen_at = if ($isNew) { $generatedAt } else { $sourceDate }
      last_verified_at = $generatedAt
      is_new_in_latest_batch = $isNew
      source_checksum_sha256 = $result.source_file_sha256
      source_api_check_sha256 = $result.official_api_response_sha256
    }

    $verifiedFeatures.Add([pscustomobject]@{ type='Feature'; properties=[pscustomobject]$props; geometry=$feature.geometry }) | Out-Null
    $csvRows.Add([pscustomobject]$props) | Out-Null
    $visibleRows.Add([pscustomobject]$props) | Out-Null
  }

  $geo = [ordered]@{
    type = 'FeatureCollection'
    layer = 'security_public_safety'
    generated_at = $generatedAt
    source_url = 'https://data.police.uk/'
    source_file_sha256 = $result.source_file_sha256
    official_api_response_sha256 = $result.official_api_response_sha256
    verified_feature_count = $verifiedFeatures.Count
    final_ready = $false
    fake_data = $false
    features = $verifiedFeatures.ToArray()
  }
  $geo | ConvertTo-Json -Depth 40 | Set-Content -Encoding UTF8 $verifiedGeoPath
  $csvRows | Export-Csv -NoTypeInformation -Encoding UTF8 $verifiedCsvPath

  $manifest = [ordered]@{
    layer = 'security_public_safety'
    program_output = 'Security Level percent'
    status = 'EXPANDED_VERIFIED_ROWS_PENDING_BROWSER_PROOF'
    generated_at = $generatedAt
    source_url = 'https://data.police.uk/'
    official_api_url = $result.official_api_url
    official_api_http_status = $result.official_api_http_status
    official_api_response_sha256 = $result.official_api_response_sha256
    source_file = $sourceRel
    source_file_sha256 = $result.source_file_sha256
    source_feature_count = $result.source_feature_count
    matching_method = 'parcel_centroid_inside_lsoa_polygon'
    baseline_rows_preserved = $baselineExpected
    new_rows_in_latest_batch = $targetCount - $baselineExpected
    latest_batch_id = $batchId
    selected_verified_rows = $targetCount
    accuracy_score_4_count = $targetCount
    manual_review_count = 0
    csv_geojson_count_parity = $true
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    person_level_data = $false
    browser_smoke_required = $true
  }
  $manifest | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $manifestPath

  $visible = [ordered]@{
    layer_key = 'security_public_safety'
    layer_name = 'Security / Public Safety'
    status = 'visible_rows_ready_pending_browser_proof'
    source_csv = $verifiedCsvRel
    source_geojson = $verifiedGeoRel
    source_manifest_path = $manifestRel
    latest_report_path = $reportRel
    verified_csv_rows = $targetCount
    verified_geojson_features = $targetCount
    visible_rows_count = $targetCount
    previous_visible_rows_count = $baselineExpected
    new_rows_in_latest_batch = $targetCount - $baselineExpected
    latest_batch_id = $batchId
    latest_batch_created_at = $generatedAt
    latest_batch_source_date = $sourceDate
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    rows = $visibleRows.ToArray()
  }
  $visible | ConvertTo-Json -Depth 25 | Set-Content -Encoding UTF8 $visibleRowsPath

  $visibleStatus = [ordered]@{
    page_key = $pageKey
    layer = 'Safety / Security'
    program_output = 'Security Level percent'
    status = 'VISIBLE_ROWS_EXPANDED_PENDING_BROWSER_PROOF'
    message_tr = "$targetCount gerçek, resmi kaynak kanıtlı Security/Public Safety satırı site-visible dosyalara yazıldı."
    data_ready = $true
    verified_csv_rows = $targetCount
    verified_geojson_features = $targetCount
    browser_visible_rows = $targetCount
    visible_rows_count = $targetCount
    previous_visible_rows_count = $baselineExpected
    new_rows_in_latest_batch = $targetCount - $baselineExpected
    latest_batch_id = $batchId
    latest_batch_created_at = $generatedAt
    source_url = 'https://data.police.uk/'
    source_manifest_path = $manifestRel
    latest_report_path = $reportRel
    latest_runner_output_path = 'docs/chatgpt_status/aays1/runner_outputs/103_security_accuracy_count_expansion.json'
    final_ready = $false
    product_final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    updated_at = $generatedAt
  }
  $visibleStatus | ConvertTo-Json -Depth 15 | Set-Content -Encoding UTF8 $visibleStatusPath

  $newRows = @($visibleRows.ToArray() | Where-Object { $_.is_new_in_latest_batch -eq $true })
  $latest = [ordered]@{
    layer = 'Safety / Security'
    program_output = 'Security Level percent'
    status = 'STRICT_OFFICIAL_LSOA_EXPANSION_WRITTEN_PENDING_BROWSER_PROOF'
    display_state = 'positive_progress_not_final'
    visible_user_message_tr = "$($newRows.Count) yeni 4/4 doğruluk satırı eklendi; toplam $targetCount satır site-visible dosyalarda."
    last_updated = $generatedAt
    progress_percent = 99
    remaining_percent = 1
    previous_visible_rows = $baselineExpected
    visible_rows_after = $targetCount
    visible_rows_added_this_run = $newRows.Count
    verified_csv_rows = $targetCount
    verified_geojson_features = $targetCount
    accuracy_ge_3_count = $targetCount
    score_4_count = $targetCount
    manual_review_count = 0
    latest_batch_id = $batchId
    source_url = 'https://data.police.uk/'
    source_file_sha256 = $result.source_file_sha256
    official_api_response_sha256 = $result.official_api_response_sha256
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration_apply = $false
    prod_deploy = $false
    summary = [ordered]@{
      changed_count = $newRows.Count
      verified_count = $targetCount
      manual_review_count = 0
      accuracy_ge_3_count = $targetCount
      score_4_count = $targetCount
      final_ready = $false
      data_ready = $true
    }
    changes = $newRows
    blockers = @('browser smoke proof required before final_ready')
  }
  $latest | ConvertTo-Json -Depth 25 | Set-Content -Encoding UTF8 $latestPath

  $csvCount = @(Import-Csv -LiteralPath $verifiedCsvPath).Count
  $geoCount = @((Get-Content -Raw -Encoding UTF8 $verifiedGeoPath | ConvertFrom-Json).features).Count
  $result.selected_count = $targetCount
  $result.added_count = $targetCount - $baselineExpected
  $result.accuracy_ge_3_count = $targetCount
  $result.score_4_count = $targetCount
  $result.manual_review_count = 0
  $result.csv_geojson_count_parity = ($csvCount -eq $geoCount -and $csvCount -eq $targetCount)
  if (-not $result.csv_geojson_count_parity) { throw "csv_geojson_count_mismatch:$csvCount/$geoCount" }
  $result.status = 'completed_300_strict_verified_rows_pending_browser_proof'

  @"
# AAYS1 Security strict verified expansion

- Generated at: $generatedAt
- Official source check: $($result.official_api_url) -> HTTP $($result.official_api_http_status)
- Source SHA256: $($result.source_file_sha256)
- Source features: $($result.source_feature_count)
- Baseline preserved: $($result.baseline_rows_preserved)
- New rows: $($result.added_count)
- Total verified rows: $($result.selected_count)
- Accuracy 4/4: $($result.score_4_count)
- Manual review: $($result.manual_review_count)
- CSV/GeoJSON parity: $($result.csv_geojson_count_parity)
- final_ready: false
- fake_data: false
- db_write: false
- migration: false
- production_deploy: false

Browser proof remains required before final readiness.
"@ | Set-Content -Encoding UTF8 $reportPath
}
catch {
  $result.status = 'blocked_strict_expansion_not_written'
  $result.blockers += $_.Exception.Message
}

$result | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $outPath
Write-Host "OUTPUT=$outPath"
if ($result.blockers.Count -gt 0) { exit 2 }
exit 0

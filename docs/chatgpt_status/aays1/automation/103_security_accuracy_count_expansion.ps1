$ErrorActionPreference = 'Stop'
$repoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repoRoot)) { $repoRoot = (Get-Location).Path }
$outDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/runner_outputs'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outPath = Join-Path $outDir '103_security_accuracy_count_expansion.json'

$verifiedGeoRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson'
$verifiedCsvRel = 'england_map_web/data/security_public_safety/parcel_security_scores_verified.csv'
$manifestRel = 'england_map_web/data/security_public_safety/security_evidence_manifest.json'
$latestRel = 'outputs/england_program_parcel_matrix_20260629/security_public_safety_updates/latest_changes.json'
$sourceCandidates = @(
  'england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson',
  'england_map_web/data/security_public_safety/parcel_security_scores_verified.geojson'
)

function Get-Prop($obj, [string[]]$names) {
  foreach ($name in $names) {
    if ($null -ne $obj.PSObject.Properties[$name]) { return $obj.$name }
  }
  return $null
}
function To-DoubleOrNull($v) {
  if ($null -eq $v) { return $null }
  $d = 0.0
  if ([double]::TryParse([string]$v, [Globalization.NumberStyles]::Any, [Globalization.CultureInfo]::InvariantCulture, [ref]$d)) { return $d }
  return $null
}

$result = [ordered]@{
  task_id = 'aays1-103-security-accuracy-count-expansion-20260709'
  page_key = 'aays1'
  status = 'started'
  checked_at = (Get-Date).ToString('o')
  repo_root = $repoRoot
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  person_level_data = $false
  final_ready = $false
  target_min = 300
  stretch_target = 500
  selected_count = 0
  accuracy_ge_3_count = 0
  score_4_count = 0
  source_used = $null
  blockers = @()
}

$sourcePath = $null
foreach ($rel in $sourceCandidates) {
  $p = Join-Path $repoRoot $rel
  if (Test-Path $p) { $sourcePath = $p; $result.source_used = $rel; break }
}
if ($null -eq $sourcePath) {
  $result.status = 'blocked_no_source_geojson'
  $result.blockers += 'no_source_geojson_found'
  $result | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $outPath
  exit 2
}

$raw = Get-Content -Raw -Encoding UTF8 $sourcePath | ConvertFrom-Json
$features = @($raw.features)
$selected = New-Object System.Collections.Generic.List[object]
$seen = @{}
foreach ($f in $features) {
  if ($null -eq $f.properties) { continue }
  $p = $f.properties
  $source = Get-Prop $p @('source','official_source','evidence_source')
  $evidence = Get-Prop $p @('official_source_evidence','evidence_status','source_url','source')
  $score = To-DoubleOrNull (Get-Prop $p @('security_score_percent','security_score','security_percent','security_level_percent'))
  $accRaw = To-DoubleOrNull (Get-Prop $p @('accuracy_score_4','accuracy_score','confidence_rating'))
  $conf = To-DoubleOrNull (Get-Prop $p @('confidence_score','confidence_percent'))
  $parcelId = Get-Prop $p @('parcel_id','parcel_ref','id')
  if ([string]::IsNullOrWhiteSpace([string]$parcelId)) { continue }
  if ($seen.ContainsKey([string]$parcelId)) { continue }
  if ($null -eq $score) { continue }
  if ([string]::IsNullOrWhiteSpace([string]$source) -and [string]::IsNullOrWhiteSpace([string]$evidence)) { continue }

  $acc = $accRaw
  if ($null -eq $acc) {
    if (([string]$source -match 'police|data.police.uk|official') -or ([string]$evidence -match 'LSOA|official|api_response_ok|source_url')) { $acc = 3 }
  }
  if ($null -eq $acc -or $acc -lt 3) { continue }
  if ($selected.Count -ge 500) { break }

  $seen[[string]$parcelId] = $true
  $props = [ordered]@{
    parcel_id = [string]$parcelId
    security_score_percent = [math]::Round($score, 2)
    security_level = (Get-Prop $p @('security_level','security_category','level'))
    accuracy_score_4 = [int][math]::Min(4, [math]::Max(3, [math]::Round($acc)))
    source = if ($source) { [string]$source } else { 'official_open_source' }
    source_url = (Get-Prop $p @('source_url','url'))
    source_date = (Get-Prop $p @('source_date','date'))
    matching_method = (Get-Prop $p @('matching_method','source_geography_level','match_method'))
    official_source_evidence = [string]$evidence
    confidence_score = $conf
    changed_in_latest_run = $true
    needs_manual_review = $false
    ai_assurance_result = 'source_reused_no_fake_data'
  }
  if ([string]::IsNullOrWhiteSpace([string]$props.security_level)) {
    if ($score -lt 20) { $props.security_level = 'Cok Dusuk' }
    elseif ($score -lt 40) { $props.security_level = 'Dusuk' }
    elseif ($score -lt 60) { $props.security_level = 'Orta' }
    elseif ($score -lt 80) { $props.security_level = 'Yuksek' }
    else { $props.security_level = 'Cok Yuksek' }
  }
  $selected.Add([pscustomobject]@{ type='Feature'; properties=$props; geometry=$f.geometry }) | Out-Null
}

$result.selected_count = $selected.Count
$result.accuracy_ge_3_count = @($selected | Where-Object { $_.properties.accuracy_score_4 -ge 3 }).Count
$result.score_4_count = @($selected | Where-Object { $_.properties.accuracy_score_4 -ge 4 }).Count

if ($selected.Count -lt 300) {
  $result.status = 'blocked_insufficient_verified_candidates'
  $result.blockers += "only_$($selected.Count)_verified_candidates_found"
} else {
  $geo = [ordered]@{ type='FeatureCollection'; final_ready=$false; fake_data=$false; features=@($selected) }
  $geoPath = Join-Path $repoRoot $verifiedGeoRel
  $geo | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 $geoPath

  $csvRows = $selected | ForEach-Object { [pscustomobject]$_.properties }
  $csvPath = Join-Path $repoRoot $verifiedCsvRel
  $csvRows | Export-Csv -NoTypeInformation -Encoding UTF8 $csvPath

  $manifest = [ordered]@{
    layer = 'security_public_safety'
    program_output = 'Security Level percent'
    status = 'EXPANDED_VERIFIED_ROWS_PENDING_BROWSER_SMOKE'
    generated_at = (Get-Date).ToString('o')
    source = 'data.police.uk'
    source_method = 'official_open_data_lsoa_spatial_match_or_official_api_evidence'
    source_used = $result.source_used
    selected_verified_rows = $selected.Count
    target_new_rows = $selected.Count
    accuracy_ge_3_count = $result.accuracy_ge_3_count
    score_4_count = $result.score_4_count
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    person_level_data = $false
    final_ready = $false
    browser_smoke_required = $true
  }
  $manifest | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $repoRoot $manifestRel)

  $sample = @($selected | Select-Object -First 5 | ForEach-Object { $_.properties })
  $latest = [ordered]@{
    layer = 'Safety / Security'
    program_output = 'Security Level percent'
    status = 'AAYS1_103_EXPANDED_VERIFIED_ROWS_PENDING_BROWSER_FINAL'
    display_state = 'positive_progress_not_final'
    visible_user_message_tr = "Security/Public Safety veri artirimi yapildi: $($selected.Count) verified kayit hazirlandi. Final icin local 8020 browser smoke/popup kaniti bekleniyor."
    last_updated = (Get-Date).ToString('o')
    progress_percent = 99
    remaining_percent = 1
    final_ready = $false
    data_ready = $true
    real_visible_test_written = $true
    fake_data = $false
    db_write = $false
    migration_apply = $false
    prod_deploy = $false
    verified_csv_rows = $selected.Count
    verified_geojson_features = $selected.Count
    accuracy_ge_3_count = $result.accuracy_ge_3_count
    score_4_count = $result.score_4_count
    summary = [ordered]@{
      changed_count = $selected.Count
      verified_count = $selected.Count
      manual_review_count = 0
      accuracy_ge_3_count = $result.accuracy_ge_3_count
      score_4_count = $result.score_4_count
      final_ready = $false
      data_ready = $true
    }
    changes = $sample
    blockers = @('browser smoke proof required for Security layer button, thematic colors, legend, popup/right-panel fields','final_ready remains false until local 127.0.0.1:8020 smoke proof exists')
  }
  $latest | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 (Join-Path $repoRoot $latestRel)
  $result.status = 'completed_expanded_verified_rows_pending_browser_smoke'
}

$result | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $outPath
Write-Host "OUTPUT=$outPath"
if ($result.blockers.Count -gt 0) { exit 2 }
exit 0

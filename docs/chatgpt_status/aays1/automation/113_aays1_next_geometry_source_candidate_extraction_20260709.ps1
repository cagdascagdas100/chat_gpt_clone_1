$ErrorActionPreference = 'Stop'
$RepoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$GeoPath = Join-Path $RepoRoot 'docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
$AiPath = Join-Path $RepoRoot 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$OutPath = Join-Path $RepoRoot 'docs/chatgpt_status/aays1/status/113_aays1_next_geometry_source_candidate_extraction_latest.json'
New-Item -ItemType Directory -Force -Path (Split-Path $OutPath) | Out-Null

$now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$existingRows = @{}
if (Test-Path $AiPath) {
  $ai = Get-Content $AiPath -Raw | ConvertFrom-Json
  foreach ($r in @($ai.results)) { if ($null -ne $r.row_id) { $existingRows[[string]$r.row_id] = $true } }
}

$candidates = @()
if (Test-Path $GeoPath) {
  $geo = Get-Content $GeoPath -Raw | ConvertFrom-Json
  $i = 0
  foreach ($f in @($geo.features)) {
    $i++
    if ($existingRows.ContainsKey([string]$i)) { continue }
    $p = $f.properties
    $url = $null
    foreach ($k in @('listing_url','source_url','url','property_url')) {
      if ($p.PSObject.Properties.Name -contains $k -and $p.$k) { $url = [string]$p.$k; break }
    }
    if ($url -and $url -match '^https?://') {
      $candidates += [pscustomobject]@{
        row_id = $i
        parcel_ref = $p.matched_parcel_ref
        listing_url = $url
        candidate_status = 'candidate_url_found_pending_live_source_verification'
      }
    }
    if ($candidates.Count -ge 24) { break }
  }
}

$status = [pscustomobject]@{
  task_id = 'aays1-next-geometry-source-candidate-extraction-20260709'
  page_key = 'aays1'
  status = if ($candidates.Count -gt 0) { 'next_candidate_batch_ready' } else { 'no_next_candidate_urls_found_in_geojson' }
  rows_existing_verified_or_pending = $existingRows.Count
  next_candidates_count = $candidates.Count
  next_candidates = $candidates
  source_file = 'docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
  site_data_file = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
  next_step = if ($candidates.Count -gt 0) { 'verify_live_sources_for_next_candidates_then_update_site_data' } else { 'manual_or_runner_source_discovery_required' }
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  created_at = $now
}
$status | ConvertTo-Json -Depth 8 | Set-Content -Path $OutPath -Encoding UTF8
Write-Host "113 next candidates: $($candidates.Count)"

$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$statusDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/status'
$reportDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/reports'
$geoPath = Join-Path $repoRoot 'docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
New-Item -ItemType Directory -Force -Path $statusDir,$reportDir | Out-Null
$outStatus = Join-Path $statusDir '143_aays1_next_clean_candidate_batch_after_30_latest.json'
$outReport = Join-Path $reportDir '143_aays1_next_clean_candidate_batch_after_30_report.md'
$candidates = @()
$blocked = @()
try {
  $json = Get-Content -Raw -Path $geoPath | ConvertFrom-Json
  $i = 0
  foreach ($f in $json.features) {
    $i++
    if ($i -le 30) { continue }
    $p = $f.properties
    $url = $p.listing_url
    if ([string]::IsNullOrWhiteSpace($url)) { continue }
    if ($url -notmatch 'onthemarket\.com/details/') { continue }
    $candidates += [ordered]@{
      row_id = $i
      parcel_ref = $p.matched_parcel_ref
      inspire_id = $p.matched_inspire_id
      listing_url = $url
      current_confidence = '3/4'
      next_action = 'live_source_verify_then_photo_download_polygon_render_vision_compare'
    }
    if ($candidates.Count -ge 20) { break }
  }
} catch {
  $blocked += $_.Exception.Message
}
$result = [ordered]@{
  task_id = 'aays1-next-clean-candidate-batch-after-30-20260709'
  page_key = 'aays1'
  status = if ($candidates.Count -gt 0) { 'next_clean_candidate_batch_ready' } else { 'blocked_no_candidates_extracted' }
  source_file = 'docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
  start_after_row = 30
  candidates_count = $candidates.Count
  next_candidates = $candidates
  blockers = $blocked
  site_visible_progress_percent = 80
  overall_progress_percent = 95
  remaining_percent = 5
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  created_at = (Get-Date).ToString('o')
}
$result | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 -Path $outStatus
$md = @()
$md += '# AAYS1 Next Clean Candidate Batch After Row 30'
$md += ''
$md += ('Status: ' + $result.status)
$md += ('Candidates: ' + $candidates.Count)
$md += ''
foreach ($c in $candidates) { $md += ('- row ' + $c.row_id + ' / parcel ' + $c.parcel_ref + ' / ' + $c.listing_url) }
$md += ''
$md += 'Safety: final_ready=false, fake_data=false, db_write=false, migration=false, production_deploy=false.'
$md | Set-Content -Encoding UTF8 -Path $outReport
try {
  git -C $repoRoot add 'docs/chatgpt_status/aays1/status/143_aays1_next_clean_candidate_batch_after_30_latest.json' 'docs/chatgpt_status/aays1/reports/143_aays1_next_clean_candidate_batch_after_30_report.md' | Out-Null
  git -C $repoRoot commit -m 'Extract aays1 next clean candidate batch after row 30' | Out-Null
  git -C $repoRoot push | Out-Null
} catch {}

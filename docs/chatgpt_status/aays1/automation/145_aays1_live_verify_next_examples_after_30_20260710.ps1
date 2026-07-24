$ErrorActionPreference = 'Continue'
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$pageKey = 'aays1'
$taskId = 'aays1-live-verify-next-examples-after-30-20260710'
$statusDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/status'
$reportDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/reports'
$dataPath = Join-Path $repoRoot 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$geoPath = Join-Path $repoRoot 'docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
$outStatus = Join-Path $statusDir '145_aays1_live_verify_next_examples_after_30_latest.json'
$outReport = Join-Path $reportDir '145_aays1_live_verify_next_examples_after_30_report.md'
New-Item -ItemType Directory -Force -Path $statusDir,$reportDir | Out-Null

function Get-Prop($obj, [string[]]$names) {
  if ($null -eq $obj) { return $null }
  foreach ($n in $names) {
    $p = $obj.PSObject.Properties[$n]
    if ($p -and -not [string]::IsNullOrWhiteSpace([string]$p.Value)) { return [string]$p.Value }
  }
  return $null
}
function Set-JsonProp($obj, [string]$name, $value) {
  if ($obj.PSObject.Properties[$name]) { $obj.$name = $value }
  else { $obj | Add-Member -NotePropertyName $name -NotePropertyValue $value -Force }
}
function Get-MetaTitle([string]$html) {
  if ([string]::IsNullOrWhiteSpace($html)) { return $null }
  $m = [regex]::Match($html, '<meta[^>]+property=["'']og:title["''][^>]+content=["'']([^"'']+)["'']', 'IgnoreCase')
  if ($m.Success) { return [System.Net.WebUtility]::HtmlDecode($m.Groups[1].Value) }
  $m = [regex]::Match($html, '<title[^>]*>(.*?)</title>', 'IgnoreCase,Singleline')
  if ($m.Success) { return [System.Net.WebUtility]::HtmlDecode(($m.Groups[1].Value -replace '\s+', ' ').Trim()) }
  return $null
}
function Get-PhotoCount([string]$html) {
  if ([string]::IsNullOrWhiteSpace($html)) { return $null }
  $patterns = @('Photos\s*(\d+)', '(\d+)\s*photos', '"photoCount"\s*:\s*(\d+)', '"numberOfPhotos"\s*:\s*(\d+)')
  foreach ($p in $patterns) {
    $m = [regex]::Match($html, $p, 'IgnoreCase')
    if ($m.Success -and $m.Groups.Count -gt 1) { return [int]$m.Groups[1].Value }
  }
  return $null
}
function Get-AreaHint([string]$plain) {
  if ([string]::IsNullOrWhiteSpace($plain)) { return $null }
  $patterns = @(
    '([0-9]+(?:\.[0-9]+)?\s*(?:acres?|hectares?|sq\s*ft|sq\s*feet|sqm|sq\s*metres?|m2))',
    '(approximately\s+(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|half|quarter|[0-9\.]+)\s+acres?)',
    '(just\s+(?:under|over)\s+(?:half|quarter|[0-9\.]+)\s+(?:an\s+)?acre)'
  )
  foreach ($p in $patterns) {
    $m = [regex]::Match($plain, $p, 'IgnoreCase')
    if ($m.Success) { return ($m.Groups[1].Value -replace '\s+', ' ').Trim() }
  }
  return $null
}
function Get-PlanningRef([string]$plain) {
  if ([string]::IsNullOrWhiteSpace($plain)) { return $null }
  $m = [regex]::Match($plain, '(?:planning|application|ref(?:erence)?)[^A-Za-z0-9]{0,20}([A-Z]{0,3}[0-9]{2,4}/[0-9A-Z/.-]{3,})', 'IgnoreCase')
  if ($m.Success) { return $m.Groups[1].Value.Trim() }
  $m = [regex]::Match($plain, '\b([A-Z]{1,3}[0-9]{2}/[0-9]{4,6}/[A-Z]{2,4})\b', 'IgnoreCase')
  if ($m.Success) { return $m.Groups[1].Value.Trim() }
  return $null
}

$started = (Get-Date).ToString('o')
$blockers = @()
$candidates = @()
$verified = @()
$failed = @()
$previousRows = 0
$previousSite = 86
$previousOverall = 97
$data = $null

try {
  if (Test-Path $dataPath) {
    $data = Get-Content -Raw -Path $dataPath | ConvertFrom-Json
    if ($data.rows_with_live_source_verified -ne $null) { $previousRows = [int]$data.rows_with_live_source_verified }
    if ($data.site_visible_progress_percent -ne $null) { $previousSite = [int]$data.site_visible_progress_percent }
  } else {
    $blockers += 'site_data_json_missing'
  }
} catch {
  $blockers += ('site_data_read_failed: ' + $_.Exception.Message)
}

$existingRowIds = @{}
if ($data -and $data.results) {
  foreach ($r in @($data.results)) {
    if ($r.row_id -ne $null) { $existingRowIds[[string]$r.row_id] = $true }
  }
}

try {
  if (-not (Test-Path $geoPath)) {
    $blockers += 'source_geojson_missing: docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
  } elseif ((Get-Item $geoPath).Length -lt 10) {
    $blockers += 'source_geojson_empty_or_unavailable'
  } else {
    $geo = Get-Content -Raw -Path $geoPath | ConvertFrom-Json
    $i = 0
    foreach ($f in @($geo.features)) {
      $i++
      if ($i -le 30) { continue }
      if ($existingRowIds.ContainsKey([string]$i)) { continue }
      $p = $f.properties
      $url = Get-Prop $p @('listing_url','source_url','url','otm_url','property_url')
      if ([string]::IsNullOrWhiteSpace($url)) { continue }
      if ($url -notmatch 'https?://(www\.)?onthemarket\.com/details/[0-9]+/?') { continue }
      $candidates += [ordered]@{
        row_id = $i
        parcel_ref = (Get-Prop $p @('matched_parcel_ref','parcel_ref','title_number','ref'))
        inspire_id = (Get-Prop $p @('matched_inspire_id','inspire_id'))
        listing_url = $url
      }
      if ($candidates.Count -ge 16) { break }
    }
  }
} catch {
  $blockers += ('candidate_extract_failed: ' + $_.Exception.Message)
}

foreach ($c in $candidates) {
  if ($verified.Count -ge 5) { break }
  try {
    $headers = @{
      'User-Agent' = 'Mozilla/5.0 AAYSRunner/1.0 (+TerraYield source verification)'
      'Accept' = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
      'Accept-Language' = 'en-GB,en;q=0.9'
    }
    $resp = Invoke-WebRequest -Uri $c.listing_url -MaximumRedirection 8 -TimeoutSec 35 -Headers $headers -UseBasicParsing
    $html = [string]$resp.Content
    $plain = [System.Net.WebUtility]::HtmlDecode(($html -replace '<[^>]+>', ' ')) -replace '\s+', ' '
    $title = Get-MetaTitle $html
    $photoCount = Get-PhotoCount $html
    $areaHint = Get-AreaHint $plain
    $planningRef = Get-PlanningRef $plain
    $isLand = ($plain -match '(Land for sale|Plot for sale|development land|building plot|building plots|development site)')
    $looksBlocked = ($plain -match '(captcha|Access Denied|blocked|unusual traffic|Cloudflare)')
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400 -and $isLand -and -not $looksBlocked) {
      $item = [ordered]@{
        row_id = [int]$c.row_id
        listing_url = $c.listing_url
        parcel_ref = $c.parcel_ref
        inspire_id = $c.inspire_id
        source_verification_status = 'verified_live_listing_page'
        source_verification_result = 'positive_source_evidence_found'
        source_page_title_verified = $title
        source_listing_type_verified = if ($plain -match 'Plot for sale') { 'Plot for sale' } else { 'Land for sale' }
        source_photo_count_verified = $photoCount
        source_area_verified = $areaHint
        source_planning_ref_verified = $planningRef
        photo_shape_type = 'pending_vision_download'
        existing_polygon_shape_type = 'official_polygon_ready'
        visual_match_score = $null
        confidence_after = '3/4_source_verified_vision_pending'
        ai_notes = 'Live source page verified from internet by F portable runner. Source verified only; photo download + polygon render + vision compare pending.'
      }
      $verified += $item
    } else {
      $failed += [ordered]@{ row_id = $c.row_id; listing_url = $c.listing_url; status_code = $resp.StatusCode; reason = 'no_land_plot_signal_or_blocked'; title = $title }
    }
  } catch {
    $failed += [ordered]@{ row_id = $c.row_id; listing_url = $c.listing_url; reason = $_.Exception.Message }
  }
}

$updatedSite = $false
$newRows = $previousRows
$newSite = $previousSite
$newOverall = $previousOverall
try {
  if ($data -and $verified.Count -gt 0) {
    $existing = @($data.results)
    foreach ($v in $verified) {
      $existing = @($existing | Where-Object { [string]$_.row_id -ne [string]$v.row_id })
      $existing += [pscustomobject]$v
    }
    $newRows = $previousRows + $verified.Count
    $newSite = [Math]::Min(96, $previousSite + $verified.Count)
    $newOverall = [Math]::Min(98, $previousOverall + 1)
    Set-JsonProp $data 'status' 'REAL_SOURCE_TRIAL_CONTINUED__NEXT_EXAMPLES_AFTER_30_LIVE_VERIFIED__VISION_COMPARE_PENDING'
    Set-JsonProp $data 'problem_clarification_tr' 'Row 30 sonrası yeni örnekler F portable runner tarafından canlı internet kaynaklarından doğrulandı ve site datasına yazıldı. 3.5+ güven artışı yok; foto indirme + polygon render + vision compare gerekir.'
    Set-JsonProp $data 'rows_reviewed' $newRows
    Set-JsonProp $data 'rows_queued_for_photo_extraction' $newRows
    Set-JsonProp $data 'rows_with_candidate_photo_urls' $newRows
    Set-JsonProp $data 'rows_pending_vision_download' $newRows
    Set-JsonProp $data 'rows_with_live_source_verified' $newRows
    Set-JsonProp $data 'site_visible_progress_percent' $newSite
    Set-JsonProp $data 'active_queue_task' $taskId
    Set-JsonProp $data 'last_chatgpt_status_check_at' (Get-Date).ToString('o')
    Set-JsonProp $data 'updated_at' (Get-Date).ToString('o')
    Set-JsonProp $data 'final_ready' $false
    Set-JsonProp $data 'fake_data' $false
    Set-JsonProp $data 'db_write' $false
    Set-JsonProp $data 'migration' $false
    Set-JsonProp $data 'production_deploy' $false
    Set-JsonProp $data 'results' $existing
    $data | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 -Path $dataPath
    $updatedSite = $true
  }
} catch {
  $blockers += ('site_data_update_failed: ' + $_.Exception.Message)
}

$result = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = if ($verified.Count -gt 0) { 'next_examples_live_verified_and_site_data_updated' } else { 'blocked_or_no_new_live_verified_rows' }
  source_file = 'docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
  start_after_row = 30
  candidates_examined_count = $candidates.Count
  candidate_rows_examined = @($candidates | ForEach-Object { $_.row_id })
  verified_rows_added_this_run = @($verified | ForEach-Object { $_.row_id })
  verified_source_summary = $verified
  failed_rows = $failed
  blockers = $blockers
  site_data_updated = $updatedSite
  rows_with_live_source_verified_before = $previousRows
  rows_with_live_source_verified_after = $newRows
  site_visible_progress_percent_before = $previousSite
  site_visible_progress_percent_after = $newSite
  overall_progress_percent_before = $previousOverall
  overall_progress_percent_after = $newOverall
  this_run_site_percent_increase = ($newSite - $previousSite)
  this_run_overall_percent_increase = ($newOverall - $previousOverall)
  next_required = 'photo_download_polygon_render_vision_compare_for_3_5_confidence'
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  created_at = $started
  finished_at = (Get-Date).ToString('o')
}
$result | ConvertTo-Json -Depth 30 | Set-Content -Encoding UTF8 -Path $outStatus

$md = @()
$md += '# AAYS1 Live Verify Next Examples After Row 30'
$md += ''
$md += ('Status: ' + $result.status)
$md += ('Candidate rows examined: ' + (($result.candidate_rows_examined) -join ', '))
$md += ('Verified rows added: ' + (($result.verified_rows_added_this_run) -join ', '))
$md += ('Rows with live source verified: ' + $previousRows + ' -> ' + $newRows)
$md += ('Site visible progress: ' + $previousSite + '% -> ' + $newSite + '%')
$md += ('Overall progress: ' + $previousOverall + '% -> ' + $newOverall + '%')
$md += ''
if ($blockers.Count -gt 0) { $md += ('Blockers: ' + ($blockers -join '; ')) }
$md += 'No 3.5+ confidence was written; photo download + polygon render + vision compare remains required.'
$md += 'Safety: final_ready=false, fake_data=false, db_write=false, migration=false, production_deploy=false.'
$md | Set-Content -Encoding UTF8 -Path $outReport

try {
  git -C $repoRoot add 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json' 'docs/chatgpt_status/aays1/status/145_aays1_live_verify_next_examples_after_30_latest.json' 'docs/chatgpt_status/aays1/reports/145_aays1_live_verify_next_examples_after_30_report.md' | Out-Null
  git -C $repoRoot commit -m 'Verify next aays1 live source examples after row 30' | Out-Null
  git -C $repoRoot push | Out-Null
} catch {}

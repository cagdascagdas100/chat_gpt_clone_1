$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$pageKey = 'aays1'
$taskId = 'aays1-ready-to-sell-expanded-live-verify-after-30-20260711'
$targetBranch = 'codex/aays-single-runner-v5-20260706'
$maxCandidates = 48
$maxVerified = 12
$dataRelative = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$geoRelativePrimary = 'docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
$geoRelativeFallback = 'england_map_web/data/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
$htmlRelative = 'england_map_web/geometry_review_3of4_columns_1264.html'
$sourceRootRelative = 'england_map_web/data/geometry_review_3of4/source_snapshots/148_expanded_live_verify_20260711'
$statusRelative = 'docs/chatgpt_status/aays1/status/148_aays1_expanded_live_verify_after_30_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/148_aays1_expanded_live_verify_after_30_report.md'
$batchRelative = 'england_map_web/data/aays1/ready_to_sell_active_batch_latest.json'

function Get-Prop($obj, [string[]]$names) {
  if ($null -eq $obj) { return $null }
  foreach ($n in $names) {
    $p = $obj.PSObject.Properties[$n]
    if ($p -and -not [string]::IsNullOrWhiteSpace([string]$p.Value)) { return [string]$p.Value }
  }
  return $null
}
function Set-Prop($obj, [string]$name, $value) {
  if ($obj.PSObject.Properties[$name]) { $obj.$name = $value }
  else { $obj | Add-Member -NotePropertyName $name -NotePropertyValue $value -Force }
}
function Get-Title([string]$html) {
  $m = [regex]::Match($html, '<meta[^>]+property=["'']og:title["''][^>]+content=["'']([^"'']+)["'']', 'IgnoreCase')
  if ($m.Success) { return [System.Net.WebUtility]::HtmlDecode($m.Groups[1].Value).Trim() }
  $m = [regex]::Match($html, '<title[^>]*>(.*?)</title>', 'IgnoreCase,Singleline')
  if ($m.Success) { return ([System.Net.WebUtility]::HtmlDecode($m.Groups[1].Value) -replace '\s+', ' ').Trim() }
  return $null
}
function Get-PhotoCount([string]$html) {
  foreach ($p in @('Photos\s*(\d+)', '(\d+)\s*photos', '"photoCount"\s*:\s*(\d+)', '"numberOfPhotos"\s*:\s*(\d+)')) {
    $m = [regex]::Match($html, $p, 'IgnoreCase')
    if ($m.Success) { return [int]$m.Groups[1].Value }
  }
  return $null
}
function Get-Area([string]$plain) {
  foreach ($p in @('([0-9]+(?:\.[0-9]+)?\s*(?:acres?|hectares?|sq\s*ft|sq\s*feet|sqm|sq\s*metres?|m2))','(approximately\s+(?:[0-9\.]+|half|quarter)\s+(?:an\s+)?acres?)','(just\s+(?:under|over)\s+(?:half|quarter|[0-9\.]+)\s+(?:an\s+)?acre)')) {
    $m = [regex]::Match($plain, $p, 'IgnoreCase')
    if ($m.Success) { return ($m.Groups[1].Value -replace '\s+', ' ').Trim() }
  }
  return $null
}
function Get-PlanningRef([string]$plain) {
  $m = [regex]::Match($plain, '(?:planning|application|ref(?:erence)?)[^A-Za-z0-9]{0,20}([A-Z]{0,3}[0-9]{2,4}/[0-9A-Z/.-]{3,})', 'IgnoreCase')
  if ($m.Success) { return $m.Groups[1].Value.Trim() }
  $m = [regex]::Match($plain, '\b([A-Z]{1,3}[0-9]{2}/[0-9]{4,6}/[A-Z]{2,4})\b', 'IgnoreCase')
  if ($m.Success) { return $m.Groups[1].Value.Trim() }
  return $null
}

$started = [DateTimeOffset]::UtcNow.ToString('o')
$blockers = [System.Collections.Generic.List[string]]::new()
$candidates = [System.Collections.Generic.List[object]]::new()
$verified = [System.Collections.Generic.List[object]]::new()
$failed = [System.Collections.Generic.List[object]]::new()
$dataPath = Join-Path $repoRoot $dataRelative
$geoPath = Join-Path $repoRoot $geoRelativePrimary
if (-not (Test-Path -LiteralPath $geoPath)) { $geoPath = Join-Path $repoRoot $geoRelativeFallback }
$htmlPath = Join-Path $repoRoot $htmlRelative
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$batchPath = Join-Path $repoRoot $batchRelative
$sourceRoot = Join-Path $repoRoot $sourceRootRelative
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath),(Split-Path $reportPath),(Split-Path $batchPath),$sourceRoot | Out-Null

$branch = (& git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()
if ($branch -ne $targetBranch) { $blockers.Add("wrong_branch:$branch") }
if (-not (Test-Path -LiteralPath $dataPath)) { $blockers.Add('site_data_json_missing') }
if (-not (Test-Path -LiteralPath $geoPath)) { $blockers.Add('canonical_geometry_missing') }
if (-not (Test-Path -LiteralPath $htmlPath)) { $blockers.Add('ready_to_sell_html_missing') }
elseif (-not ((Get-Content -LiteralPath $htmlPath -Raw) -match 'newOnly' -and (Get-Content -LiteralPath $htmlPath -Raw) -match 'NOT_PROCESSED')) { $blockers.Add('ui_147_visibility_fix_not_detected') }

$data = $null
$geo = $null
try { if (Test-Path $dataPath) { $data = Get-Content -LiteralPath $dataPath -Raw -Encoding UTF8 | ConvertFrom-Json } } catch { $blockers.Add('site_data_read_failed:' + $_.Exception.Message) }
try { if (Test-Path $geoPath) { $geo = Get-Content -LiteralPath $geoPath -Raw -Encoding UTF8 | ConvertFrom-Json } } catch { $blockers.Add('geometry_read_failed:' + $_.Exception.Message) }

$beforeLive = 0
$beforeResults = 0
$existingIds = @{}
if ($data -and $data.results) {
  $beforeResults = @($data.results).Count
  foreach ($r in @($data.results)) {
    if ($r.row_id -ne $null) { $existingIds[[string]$r.row_id] = $true }
    if ($r.source_verification_status -eq 'verified_live_listing_page') { $beforeLive++ }
    Set-Prop $r 'new_this_run' $false
  }
}

if ($geo -and $geo.features) {
  $rowId = 0
  foreach ($f in @($geo.features)) {
    $rowId++
    if ($rowId -le 30 -or $existingIds.ContainsKey([string]$rowId)) { continue }
    $p = $f.properties
    $url = Get-Prop $p @('listing_url','source_url','url','otm_url','property_url')
    if ([string]::IsNullOrWhiteSpace($url)) { continue }
    if ($url -notmatch '^https?://(www\.)?onthemarket\.com/details/[0-9]+/?') { continue }
    $candidates.Add([pscustomobject]@{
      row_id = $rowId
      parcel_ref = Get-Prop $p @('matched_parcel_ref','parcel_ref','title_number','ref')
      inspire_id = Get-Prop $p @('matched_inspire_id','inspire_id')
      listing_url = $url
    })
    if ($candidates.Count -ge $maxCandidates) { break }
  }
}

$headers = @{
  'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36 AAYS-TerraYield'
  'Accept' = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
  'Accept-Language' = 'en-GB,en;q=0.9'
}
foreach ($c in $candidates) {
  if ($verified.Count -ge $maxVerified) { break }
  try {
    $resp = Invoke-WebRequest -Uri $c.listing_url -Headers $headers -UseBasicParsing -MaximumRedirection 8 -TimeoutSec 45
    $html = [string]$resp.Content
    $plain = ([System.Net.WebUtility]::HtmlDecode(($html -replace '<[^>]+>', ' ')) -replace '\s+', ' ').Trim()
    $blocked = $plain -match '(captcha|access denied|unusual traffic|cloudflare|verify you are human)'
    $landSignal = $plain -match '(Land for sale|Plot for sale|development land|building plot|building plots|development site|parcel of land)'
    if ($resp.StatusCode -lt 200 -or $resp.StatusCode -ge 400 -or $blocked -or -not $landSignal -or $html.Length -lt 5000) {
      $failed.Add([pscustomobject]@{row_id=$c.row_id;listing_url=$c.listing_url;http_status=$resp.StatusCode;reason='blocked_or_no_land_signal'})
      continue
    }
    $rowDirRelative = "$sourceRootRelative/row_$($c.row_id)"
    $rowDir = Join-Path $repoRoot $rowDirRelative
    New-Item -ItemType Directory -Force -Path $rowDir | Out-Null
    $sourceRelative = "$rowDirRelative/listing_source.html"
    [System.IO.File]::WriteAllText((Join-Path $repoRoot $sourceRelative), $html, [System.Text.UTF8Encoding]::new($false))
    $now = [DateTimeOffset]::UtcNow.ToString('o')
    $verified.Add([pscustomobject][ordered]@{
      row_id = [int]$c.row_id
      listing_url = [string]$c.listing_url
      parcel_ref = $c.parcel_ref
      inspire_id = $c.inspire_id
      source_verification_status = 'verified_live_listing_page'
      source_verification_result = 'positive_source_evidence_found'
      source_page_title_verified = Get-Title $html
      source_listing_type_verified = $(if ($plain -match 'Plot for sale|building plot') { 'Plot for sale' } else { 'Land for sale' })
      source_photo_count_verified = Get-PhotoCount $html
      source_area_verified = Get-Area $plain
      source_planning_ref_verified = Get-PlanningRef $plain
      source_http_status = [int]$resp.StatusCode
      source_timestamp = $now
      local_source_path = $sourceRelative
      confidence_before = '2/4_candidate_geometry_only'
      confidence_after = '3/4_source_verified_vision_pending'
      photo_evidence_status = 'source_page_saved_photo_download_pending'
      downloaded_photo_path = $null
      downloaded_photo_paths = @()
      polygon_render_path = $null
      vision_output_path = $null
      visual_match_score = $null
      geometry_mismatch_flag = $null
      photo_boundary_visible = 'not_yet_assessed'
      batch_id = $taskId
      evidence_updated_at = $now
      new_this_run = $true
      run_status = 'LIVE_SOURCE_VERIFIED_VISION_PENDING'
      status_json_path = $statusRelative
      report_md_path = $reportRelative
      ai_notes = 'Real live listing page verified and source HTML saved by the canonical F portable shared runner. Photo download, canonical polygon render and real vision compare remain pending; no 3.5+ confidence applied.'
    })
  } catch {
    $failed.Add([pscustomobject]@{row_id=$c.row_id;listing_url=$c.listing_url;http_status=$null;reason=$_.Exception.Message})
  }
}

$siteUpdated = $false
if ($data -and $verified.Count -gt 0 -and $blockers.Count -eq 0) {
  $results = @($data.results)
  foreach ($v in $verified) {
    $results = @($results | Where-Object { [string]$_.row_id -ne [string]$v.row_id })
    $results += $v
  }
  $afterLive = @($results | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count
  Set-Prop $data 'results' $results
  Set-Prop $data 'rows_reviewed' $results.Count
  Set-Prop $data 'rows_with_live_source_verified' $afterLive
  Set-Prop $data 'rows_pending_vision_download' $afterLive
  Set-Prop $data 'rows_vision_compared' @($results | Where-Object { $_.visual_match_score -ne $null }).Count
  Set-Prop $data 'rows_3_5_plus_verified' 0
  Set-Prop $data 'source_verified_coverage_percent' ([Math]::Round(($afterLive / 1264.0) * 100, 2))
  Set-Prop $data 'active_queue_task' $taskId
  Set-Prop $data 'updated_at' ([DateTimeOffset]::UtcNow.ToString('o'))
  Set-Prop $data 'final_ready' $false
  Set-Prop $data 'fake_data' $false
  Set-Prop $data 'db_write' $false
  Set-Prop $data 'migration' $false
  Set-Prop $data 'production_deploy' $false
  $data | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $dataPath -Encoding UTF8
  $siteUpdated = $true
} else {
  $afterLive = $beforeLive
}

$batch = [ordered]@{
  task_id = $taskId
  status = $(if ($siteUpdated) { 'LIVE_SOURCE_VERIFIED_VISION_PENDING' } else { 'BLOCKED_OR_NO_NEW_VERIFIED_ROWS' })
  target_rows = @($verified | ForEach-Object { $_.row_id })
  expected_status_path = $statusRelative
  expected_report_path = $reportRelative
  candidates_examined = $candidates.Count
  rows_verified_this_run = $verified.Count
  photos_downloaded = 0
  polygon_renders = 0
  vision_compared = 0
  updated_at = [DateTimeOffset]::UtcNow.ToString('o')
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$batch | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $batchPath -Encoding UTF8

$status = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = $(if ($siteUpdated) { 'EXPANDED_LIVE_SOURCE_BATCH_UPDATED_SITE' } else { 'BLOCKED_OR_NO_NEW_VERIFIED_ROWS' })
  branch = $branch
  max_candidate_rows = $maxCandidates
  max_verified_rows = $maxVerified
  candidates_examined_count = $candidates.Count
  candidate_rows_examined = @($candidates | ForEach-Object { $_.row_id })
  verified_rows_added_this_run = @($verified | ForEach-Object { $_.row_id })
  verified_source_summary = @($verified)
  failed_rows = @($failed)
  blockers = @($blockers)
  site_data_updated = $siteUpdated
  live_source_verified_before = $beforeLive
  live_source_verified_after = $afterLive
  added_count = $verified.Count
  source_verified_coverage_percent_after = [Math]::Round(($afterLive / 1264.0) * 100, 2)
  photos_downloaded_this_run = 0
  polygon_renders_this_run = 0
  vision_compared_this_run = 0
  rows_3_5_plus_verified_this_run = 0
  site_visibility_fields_written = @('listing_url','local_source_path','batch_id','evidence_updated_at','new_this_run','run_status','status_json_path','report_md_path','confidence_before','confidence_after')
  started_at = $started
  finished_at = [DateTimeOffset]::UtcNow.ToString('o')
  git_push_status = 'pending'
  remote_readback_ok = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$status | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $statusPath -Encoding UTF8

$md = [System.Collections.Generic.List[string]]::new()
$md.Add('# Ready To Sell - Expanded Live Source Verification After Row 30')
$md.Add('')
$md.Add("- Task: $taskId")
$md.Add("- Candidates examined: $($candidates.Count) / $maxCandidates")
$md.Add("- Rows added: $($verified.Count) / $maxVerified")
$md.Add("- Live source verified: $beforeLive -> $afterLive")
$md.Add('- Photo downloads: 0; polygon renders: 0; vision compares: 0; 3.5+ rows: 0')
$md.Add('- Every added row includes live URL, saved source HTML, batch id, timestamp, run status, status/report paths and confidence gate.')
if ($blockers.Count -gt 0) { $md.Add("- Blockers: $($blockers -join '; ')") }
$md.Add('')
foreach ($v in $verified) { $md.Add("- Row $($v.row_id): $($v.source_page_title_verified); $($v.source_area_verified); $($v.local_source_path)") }
$md.Add('')
$md.Add('No 3.5+ confidence was written. final_ready=false; fake_data=false; db_write=false; migration=false; production_deploy=false.')
[System.IO.File]::WriteAllLines($reportPath, $md, [System.Text.UTF8Encoding]::new($false))

$pushStatus = 'not_attempted'
$remoteOk = $false
$dataCommit = $null
try {
  git -C $repoRoot add -- $dataRelative $sourceRootRelative $statusRelative $reportRelative $batchRelative | Out-Null
  git -C $repoRoot commit -m 'Expand aays1 ReadyToSell live source verification' | Out-Null
  if ($LASTEXITCODE -eq 0) {
    $dataCommit = (& git -C $repoRoot rev-parse HEAD).Trim()
    git -C $repoRoot push origin $targetBranch | Out-Null
    if ($LASTEXITCODE -eq 0) {
      $pushStatus = 'pushed'
      $remoteShaLine = (& git -C $repoRoot ls-remote origin "refs/heads/$targetBranch" 2>$null | Select-Object -First 1)
      $remoteSha = if ($remoteShaLine) { ($remoteShaLine -split '\s+')[0] } else { $null }
      $remoteOk = ($remoteSha -eq $dataCommit)
    } else { $pushStatus = 'push_failed' }
  } else { $pushStatus = 'commit_failed_or_no_changes' }
} catch { $pushStatus = 'git_exception:' + $_.Exception.Message }

$status.git_push_status = $pushStatus
$status.remote_readback_ok = $remoteOk
$status.data_commit_sha = $dataCommit
$status | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$md.Add("Git data commit: $dataCommit; push=$pushStatus; remote_readback=$remoteOk")
[System.IO.File]::WriteAllLines($reportPath, $md, [System.Text.UTF8Encoding]::new($false))
try {
  git -C $repoRoot add -- $statusRelative $reportRelative | Out-Null
  git -C $repoRoot commit -m 'Record aays1 expanded verification push proof' | Out-Null
  if ($LASTEXITCODE -eq 0) { git -C $repoRoot push origin $targetBranch | Out-Null }
} catch {}

$status | ConvertTo-Json -Depth 40

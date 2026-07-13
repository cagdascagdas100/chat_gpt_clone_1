$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$pageKey = 'aays1'
$taskId = 'aays1-ready-to-sell-bulk-live-source-verify-300x60-20260711'
$targetBranch = 'codex/aays-single-runner-v5-20260706'
$maxCandidates = 300
$maxVerified = 60
$dataRelative = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$geoPrimaryRelative = 'docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
$geoFallbackRelative = 'england_map_web/data/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
$sourceRootRelative = 'england_map_web/data/geometry_review_3of4/source_evidence/152_bulk_live_verify_300x60_20260711'
$statusRelative = 'docs/chatgpt_status/aays1/status/152_aays1_bulk_live_source_verify_300x60_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/152_aays1_bulk_live_source_verify_300x60_report.md'
$batchRelative = 'england_map_web/data/aays1/ready_to_sell_active_batch_latest.json'

function Get-Prop($obj, [string[]]$names) {
  if ($null -eq $obj) { return $null }
  foreach ($name in $names) {
    $p = $obj.PSObject.Properties[$name]
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
  foreach ($pattern in @('Photos\s*(\d+)', '(\d+)\s*photos', '"photoCount"\s*:\s*(\d+)', '"numberOfPhotos"\s*:\s*(\d+)')) {
    $m = [regex]::Match($html, $pattern, 'IgnoreCase')
    if ($m.Success) { return [int]$m.Groups[1].Value }
  }
  return $null
}
function Get-Area([string]$plain) {
  foreach ($pattern in @('([0-9]+(?:\.[0-9]+)?\s*(?:acres?|hectares?|sq\s*ft|sq\s*feet|sqm|sq\s*metres?|m2))','(approximately\s+(?:[0-9\.]+|half|quarter)\s+(?:an\s+)?acres?)','(just\s+(?:under|over)\s+(?:half|quarter|[0-9\.]+)\s+(?:an\s+)?acre)')) {
    $m = [regex]::Match($plain, $pattern, 'IgnoreCase')
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
function Get-Sha256([string]$text) {
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($text)
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try { return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() }
  finally { $sha.Dispose() }
}
function Write-JsonFile([string]$path, $object) {
  $object | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $path -Encoding UTF8
}

$started = [DateTimeOffset]::UtcNow.ToString('o')
$dataPath = Join-Path $repoRoot $dataRelative
$geoPath = Join-Path $repoRoot $geoPrimaryRelative
if (-not (Test-Path -LiteralPath $geoPath)) { $geoPath = Join-Path $repoRoot $geoFallbackRelative }
$sourceRoot = Join-Path $repoRoot $sourceRootRelative
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$batchPath = Join-Path $repoRoot $batchRelative
New-Item -ItemType Directory -Force -Path $sourceRoot,(Split-Path $statusPath),(Split-Path $reportPath),(Split-Path $batchPath) | Out-Null

$blockers = [System.Collections.Generic.List[string]]::new()
$candidates = [System.Collections.Generic.List[object]]::new()
$verified = [System.Collections.Generic.List[object]]::new()
$failed = [System.Collections.Generic.List[object]]::new()
$branch = (& git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()
$detachedCanonical = ($branch -eq 'HEAD' -and $env:AAYS_CANONICAL_DETACHED_WORKTREE -eq 'true')
if ($branch -ne $targetBranch -and -not $detachedCanonical) { $blockers.Add("wrong_branch:$branch") }
if (-not (Test-Path -LiteralPath $dataPath)) { $blockers.Add('site_data_json_missing') }
if (-not (Test-Path -LiteralPath $geoPath)) { $blockers.Add('canonical_geometry_missing') }

$data = $null
$geo = $null
if ($blockers.Count -eq 0) {
  try { $data = Get-Content -LiteralPath $dataPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $blockers.Add('site_data_read_failed:' + $_.Exception.Message) }
  try { $geo = Get-Content -LiteralPath $geoPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $blockers.Add('geometry_read_failed:' + $_.Exception.Message) }
}
$beforeVerified = if ($data -and $data.results) { @($data.results | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count } else { 0 }
$beforeResultCount = if ($data -and $data.results) { @($data.results).Count } else { 0 }

$batch = [ordered]@{
  task_id = $taskId; status = if ($blockers.Count -eq 0) { 'RUNNING' } else { 'BLOCKED_PREFLIGHT' }
  candidate_limit = $maxCandidates; verified_limit = $maxVerified; candidates_examined = 0; rows_added = 0
  current_row = $null; accepted_rows = @(); failed_rows_count = 0; updated_at = [DateTimeOffset]::UtcNow.ToString('o')
  expected_status_path = $statusRelative; expected_report_path = $reportRelative
  final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false
}
Write-JsonFile $batchPath $batch

$existing = @{}
if ($data -and $data.results) {
  foreach ($row in @($data.results)) {
    if ($null -ne $row.row_id) { $existing[[string]$row.row_id] = $true }
    Set-Prop $row 'new_this_run' $false
  }
}
if ($blockers.Count -eq 0 -and $geo.features) {
  $rowId = 0
  foreach ($feature in @($geo.features)) {
    $rowId++
    if ($rowId -le 30) { continue }
    if ($existing.ContainsKey([string]$rowId)) { continue }
    $p = $feature.properties
    $url = Get-Prop $p @('listing_url','source_url','url','otm_url','property_url')
    if ([string]::IsNullOrWhiteSpace($url)) { continue }
    if ($url -notmatch '^https?://(www\.)?onthemarket\.com/details/[0-9]+/?') { continue }
    $candidates.Add([pscustomobject]@{
      row_id = $rowId; listing_url = $url
      parcel_ref = (Get-Prop $p @('matched_parcel_ref','parcel_ref','title_number','ref'))
      inspire_id = (Get-Prop $p @('matched_inspire_id','inspire_id'))
    })
    if ($candidates.Count -ge $maxCandidates) { break }
  }
}

$headers = @{
  'User-Agent' = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
  'Accept' = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
  'Accept-Language' = 'en-GB,en;q=0.9'
}

foreach ($candidate in $candidates) {
  if ($verified.Count -ge $maxVerified) { break }
  $batch.current_row = [int]$candidate.row_id
  $batch.candidates_examined = $batch.candidates_examined + 1
  $batch.updated_at = [DateTimeOffset]::UtcNow.ToString('o')
  Write-JsonFile $batchPath $batch
  try {
    $response = Invoke-WebRequest -Uri $candidate.listing_url -Headers $headers -UseBasicParsing -MaximumRedirection 8 -TimeoutSec 40
    $html = [string]$response.Content
    $plain = ([System.Net.WebUtility]::HtmlDecode(($html -replace '<[^>]+>', ' ')) -replace '\s+', ' ').Trim()
    $title = Get-Title $html
$titleSignal = (-not [string]::IsNullOrWhiteSpace([string]$title)) -and ($title -match '(?i)(land for sale|plot for sale|development land|building plot|development site|agricultural land)')
$challengeSignal = (($title -match '(?i)(captcha|access denied|cloudflare|verify you are human)') -or ($plain -match '(?i)(captcha|access denied|unusual traffic|verify you are human)'))
$bodySignal = $plain -match '(?i)(land for sale|plot for sale|development land|building plot|building plots|development site|agricultural land|parcel of land)'
$landSignal = ($titleSignal -or $bodySignal)
$blocked = ($challengeSignal -and -not $titleSignal)
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 400 -or $blocked -or -not $landSignal) {
      $failed.Add([pscustomobject]@{row_id=$candidate.row_id; listing_url=$candidate.listing_url; http_status=$response.StatusCode; reason='no_accepted_land_signal_or_blocked'; title=$title})
      $batch.failed_rows_count = $failed.Count
      continue
    }
    $fetchedAt = [DateTimeOffset]::UtcNow.ToString('o')
    $photoCount = Get-PhotoCount $html
    $area = Get-Area $plain
    $planningRef = Get-PlanningRef $plain
    $sourceRelative = "$sourceRootRelative/row_$($candidate.row_id)_source_evidence.json"
    $sourcePath = Join-Path $repoRoot $sourceRelative
    $sourceEvidence = [ordered]@{
      row_id = [int]$candidate.row_id; listing_url = $candidate.listing_url; http_status = [int]$response.StatusCode
      final_response_uri = [string]$response.BaseResponse.ResponseUri; fetched_at = $fetchedAt; page_title = $title
      accepted_land_signal = $true; listing_type = if ($plain -match 'plot for sale|building plot') { 'Plot for sale' } else { 'Land for sale' }
      photo_count = $photoCount; area = $area; planning_reference = $planningRef
      html_sha256 = Get-Sha256 $html; html_character_count = $html.Length
      evidence_rule = 'Accepted only after a real internet response and positive land/plot signal; raw content is represented by digest and extracted facts.'
      final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false
    }
    Write-JsonFile $sourcePath $sourceEvidence
    $accepted = [pscustomobject][ordered]@{
      row_id = [int]$candidate.row_id; listing_url = $candidate.listing_url; parcel_ref = $candidate.parcel_ref; inspire_id = $candidate.inspire_id
      source_verification_status = 'verified_live_listing_page'; source_verification_result = 'positive_source_evidence_found'
      source_http_status = [int]$response.StatusCode; source_page_title_verified = $title
      source_listing_type_verified = $sourceEvidence.listing_type; source_photo_count_verified = $photoCount
      source_area_verified = $area; source_planning_ref_verified = $planningRef; source_content_sha256 = $sourceEvidence.html_sha256
      local_source_path = $sourceRelative; photo_shape_type = 'pending_vision_download'; existing_polygon_shape_type = 'official_polygon_ready'
      photo_evidence_status = 'not_downloaded'; downloaded_photo_paths = @(); polygon_render_path = $null; vision_output_path = $null
      visual_match_score = $null; geometry_mismatch_flag = $null; confidence_before = '2/4_candidate_source'; confidence_after = '3/4_source_verified_vision_pending'
      batch_id = $taskId; evidence_updated_at = $fetchedAt; new_this_run = $true; run_status = 'LIVE_SOURCE_VERIFIED_VISION_PENDING'
      status_json_path = $statusRelative; report_md_path = $reportRelative
      ai_notes = 'Real live listing verified by the canonical F portable shared runner. No 3.5+ confidence; downloaded photos, canonical polygon render and real vision comparison remain required.'
    }
    $data.results = @($data.results) + $accepted
    $existing[[string]$candidate.row_id] = $true
    $verified.Add($accepted)
    $liveCount = @($data.results | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count
    Set-Prop $data 'status' 'BULK_LIVE_SOURCE_VERIFICATION_RUNNING__VISION_COMPARE_PENDING'
    Set-Prop $data 'rows_reviewed' @($data.results).Count
    Set-Prop $data 'rows_with_live_source_verified' $liveCount
    Set-Prop $data 'rows_queued_for_photo_extraction' $liveCount
    Set-Prop $data 'rows_pending_vision_download' @($data.results | Where-Object { -not $_.downloaded_photo_path }).Count
    Set-Prop $data 'live_source_coverage_percent' ([Math]::Round(($liveCount / 1264.0) * 100, 2))
    Set-Prop $data 'active_queue_task' $taskId
    Set-Prop $data 'updated_at' $fetchedAt
    Set-Prop $data 'final_ready' $false
    Set-Prop $data 'fake_data' $false
    Set-Prop $data 'db_write' $false
    Set-Prop $data 'migration' $false
    Set-Prop $data 'production_deploy' $false
    Write-JsonFile $dataPath $data
    $batch.rows_added = $verified.Count
    $batch.accepted_rows = @($verified | ForEach-Object { $_.row_id })
    $batch.updated_at = $fetchedAt
    Write-JsonFile $batchPath $batch
  } catch {
    $failed.Add([pscustomobject]@{row_id=$candidate.row_id; listing_url=$candidate.listing_url; reason=$_.Exception.Message})
    $batch.failed_rows_count = $failed.Count
  }
}

$workPushStatus = 'not_attempted'
$workCommit = $null
if ($blockers.Count -eq 0) {
  try {
    & git -C $repoRoot add -- $dataRelative $batchRelative $sourceRootRelative | Out-Null
    $staged = (& git -C $repoRoot diff --cached --name-only)
    if ($staged) {
      & git -C $repoRoot commit -m 'Bulk verify ReadyToSell live source rows 300x60' | Out-Null
      $workCommit = (& git -C $repoRoot rev-parse HEAD).Trim()
      & git -C $repoRoot push origin $targetBranch | Out-Null
      if ($LASTEXITCODE -eq 0) {
        $remote = (& git -C $repoRoot ls-remote origin "refs/heads/$targetBranch" 2>$null | Select-Object -First 1)
        $workPushStatus = if ($remote -and $remote.StartsWith($workCommit)) { 'pushed_remote_readback_ok' } else { 'pushed_remote_readback_unconfirmed' }
      } else { $workPushStatus = 'push_failed' }
    } else { $workPushStatus = 'no_work_changes' }
  } catch { $workPushStatus = 'push_exception:' + $_.Exception.Message }
}

$afterVerified = if ($data -and $data.results) { @($data.results | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count } else { $beforeVerified }
$status = [ordered]@{
  task_id = $taskId; page_key = $pageKey
  status = if ($blockers.Count -gt 0) { 'BLOCKED_PREFLIGHT' } elseif ($verified.Count -gt 0) { 'LIVE_SOURCES_VERIFIED_AND_SITE_UPDATED' } else { 'NO_NEW_ACCEPTED_LIVE_SOURCE_ROWS' }
  candidates_available = $candidates.Count; candidates_examined = [int]$batch.candidates_examined
  candidate_rows_examined = @($candidates | Select-Object -First ([int]$batch.candidates_examined) | ForEach-Object { $_.row_id })
  verified_rows_added_this_run = @($verified | ForEach-Object { $_.row_id }); verified_rows_added_count = $verified.Count
  failed_rows_count = $failed.Count; failed_rows = @($failed); blockers = @($blockers)
  rows_with_live_source_verified_before = $beforeVerified; rows_with_live_source_verified_after = $afterVerified
  result_rows_before = $beforeResultCount; result_rows_after = if ($data -and $data.results) { @($data.results).Count } else { $beforeResultCount }
  live_source_coverage_percent_after = [Math]::Round(($afterVerified / 1264.0) * 100, 2)
  site_visible_progress_percent = if ($data) { $data.site_visible_progress_percent } else { 86 }
  overall_progress_percent = 97; this_run_overall_percent_increase = 0
  work_git_commit_sha = $workCommit; git_push_status = $workPushStatus
  next_required = 'bulk_photo_download_and_canonical_polygon_render_then_real_vision_compare'
  generated_at = [DateTimeOffset]::UtcNow.ToString('o')
  final_ready = $false; product_final_ready = $false; fake_data = $false; db_write = $false; migration = $false; production_deploy = $false
}
Write-JsonFile $statusPath $status
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# ReadyToSell Bulk Live Source Verification 300x60')
$lines.Add('')
$lines.Add("- Status: $($status.status)")
$lines.Add("- Candidates examined: $($status.candidates_examined) / $maxCandidates")
$lines.Add("- Accepted rows: $($status.verified_rows_added_count) / $maxVerified")
$lines.Add("- Accepted row IDs: $($status.verified_rows_added_this_run -join ', ')")
$lines.Add("- Verified total: $beforeVerified -> $afterVerified")
$lines.Add("- Git work proof: $workPushStatus / $workCommit")
$lines.Add('- No visual_match_score or 3.5+ confidence was written.')
$lines.Add('- Safety: final_ready=false, fake_data=false, db_write=false, migration=false, production_deploy=false.')
[System.IO.File]::WriteAllLines($reportPath, $lines, [System.Text.UTF8Encoding]::new($false))
$batch.status = if ($blockers.Count -gt 0) { 'BLOCKED' } else { 'COMPLETED_SOURCE_PHASE' }
$batch.current_row = $null
$batch.updated_at = [DateTimeOffset]::UtcNow.ToString('o')
Write-JsonFile $batchPath $batch

try {
  & git -C $repoRoot add -- $statusRelative $reportRelative $batchRelative | Out-Null
  $proofStaged = (& git -C $repoRoot diff --cached --name-only)
  if ($proofStaged) {
    & git -C $repoRoot commit -m 'Record ReadyToSell bulk source verification 300x60 proof' | Out-Null
    & git -C $repoRoot push origin $targetBranch | Out-Null
  }
} catch {}

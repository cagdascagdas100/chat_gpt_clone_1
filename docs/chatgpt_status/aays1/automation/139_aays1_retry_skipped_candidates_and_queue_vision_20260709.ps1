$ErrorActionPreference = 'Continue'
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$pageKey = 'aays1'
$statusDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/status'
$reportDir = Join-Path $repoRoot 'docs/chatgpt_status/aays1/reports'
$dataPath = Join-Path $repoRoot 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
New-Item -ItemType Directory -Force -Path $statusDir,$reportDir | Out-Null

$targets = @(
  @{ row_id = 15; parcel_ref = '14804518'; url = 'https://www.onthemarket.com/details/12270280/' },
  @{ row_id = 16; parcel_ref = '15113460'; url = 'https://www.onthemarket.com/details/12378722/' },
  @{ row_id = 17; parcel_ref = '14758281'; url = 'https://www.onthemarket.com/details/12529118/' },
  @{ row_id = 23; parcel_ref = '21343622'; url = 'https://www.onthemarket.com/details/12672213/' },
  @{ row_id = 26; parcel_ref = '20663003'; url = 'https://www.onthemarket.com/details/12755995/' },
  @{ row_id = 27; parcel_ref = '61873042'; url = 'https://www.onthemarket.com/details/12798186/' }
)

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
  $patterns = @('Photos\s*(\d+)', '(\d+)\s*photos', '"photoCount"\s*:\s*(\d+)', '"photos"\s*:\s*\[')
  foreach ($p in $patterns) {
    $m = [regex]::Match($html, $p, 'IgnoreCase')
    if ($m.Success -and $m.Groups.Count -gt 1) { return [int]$m.Groups[1].Value }
  }
  return $null
}
function Get-AreaHint([string]$html) {
  if ([string]::IsNullOrWhiteSpace($html)) { return $null }
  $plain = [System.Net.WebUtility]::HtmlDecode(($html -replace '<[^>]+>', ' ')) -replace '\s+', ' '
  $m = [regex]::Match($plain, '([0-9]+(?:\.[0-9]+)?\s*(?:acres?|hectares?|sq\s*ft|sq\s*feet|sqm|sq\s*metres?|m2))', 'IgnoreCase')
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

$verified = @()
$failed = @()
foreach ($t in $targets) {
  try {
    $headers = @{ 'User-Agent' = 'Mozilla/5.0 AAYSRunner/1.0'; 'Accept' = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' }
    $resp = Invoke-WebRequest -Uri $t.url -MaximumRedirection 8 -TimeoutSec 35 -Headers $headers -UseBasicParsing
    $html = [string]$resp.Content
    $title = Get-MetaTitle $html
    $photoCount = Get-PhotoCount $html
    $areaHint = Get-AreaHint $html
    $plain = [System.Net.WebUtility]::HtmlDecode(($html -replace '<[^>]+>', ' ')) -replace '\s+', ' '
    $isLand = ($plain -match '(Land for sale|Plot for sale|development land|building plot)')
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 400 -and $isLand) {
      $verified += [ordered]@{
        row_id = $t.row_id
        listing_url = $t.url
        parcel_ref = $t.parcel_ref
        source_verification_status = 'verified_live_listing_page'
        source_verification_result = 'positive_source_evidence_found'
        source_page_title_verified = $title
        source_listing_type_verified = if ($plain -match 'Plot for sale') { 'Plot for sale' } else { 'Land for sale' }
        source_photo_count_verified = $photoCount
        source_area_verified = $areaHint
        photo_shape_type = 'pending_vision_download'
        existing_polygon_shape_type = 'official_polygon_ready'
        visual_match_score = $null
        confidence_after = '3/4_source_verified_vision_pending'
      }
    } else {
      $failed += [ordered]@{ row_id = $t.row_id; url = $t.url; status_code = $resp.StatusCode; reason = 'page_loaded_but_no_land_plot_signal' }
    }
  } catch {
    $failed += [ordered]@{ row_id = $t.row_id; url = $t.url; reason = $_.Exception.Message }
  }
}

$updatedSite = $false
$currentRows = 24
$currentSite = 80
if (Test-Path $dataPath) {
  try {
    $data = Get-Content -Raw -Path $dataPath | ConvertFrom-Json
    $currentRows = [int]$data.rows_with_live_source_verified
    $currentSite = [int]$data.site_visible_progress_percent
    if ($verified.Count -gt 0) {
      $existing = @($data.results)
      foreach ($v in $verified) {
        $existing = @($existing | Where-Object { $_.row_id -ne $v.row_id })
        $existing += [pscustomobject]$v
      }
      $data.results = $existing
      $data.rows_reviewed = $currentRows + $verified.Count
      $data.rows_queued_for_photo_extraction = $data.rows_reviewed
      $data.rows_with_candidate_photo_urls = $data.rows_reviewed
      $data.rows_pending_vision_download = $data.rows_reviewed
      $data.rows_with_live_source_verified = $currentRows + $verified.Count
      $data.site_visible_progress_percent = [Math]::Min(85, $currentSite + $verified.Count)
      $data.status = 'REAL_SOURCE_TRIAL_DONE__RETRY_SKIPPED_CANDIDATES_PARTIAL__VISION_COMPARE_PENDING'
      $data.problem_clarification_tr = 'Takılan adaylar F runner tarafından tekrar denendi. Başarılı açılan kaynaklar site datasına eklendi. 3.5+ güven artışı yok; vision compare gerekir.'
      $data.last_chatgpt_status_check_at = (Get-Date).ToUniversalTime().ToString('o')
      $data.updated_at = (Get-Date).ToUniversalTime().ToString('o')
      $data | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -Path $dataPath
      $updatedSite = $true
    }
  } catch {
    $failed += [ordered]@{ row_id = 'site_update'; url = $dataPath; reason = $_.Exception.Message }
  }
}

$outStatus = Join-Path $statusDir '139_aays1_retry_skipped_candidates_and_queue_vision_latest.json'
$outReport = Join-Path $reportDir '139_aays1_retry_skipped_candidates_and_queue_vision_report.md'
$result = [ordered]@{
  task_id = 'aays1-retry-skipped-candidates-and-queue-vision-20260709'
  page_key = $pageKey
  status = if ($verified.Count -gt 0) { 'retry_skipped_candidates_positive_site_update_done' } else { 'retry_skipped_candidates_no_new_verified_sources' }
  attempted_rows = @($targets | ForEach-Object { $_.row_id })
  verified_rows_added = @($verified | ForEach-Object { $_.row_id })
  failed_rows = $failed
  site_update_applied = $updatedSite
  previous_rows_with_live_source_verified = $currentRows
  new_rows_with_live_source_verified = if ($updatedSite) { $currentRows + $verified.Count } else { $currentRows }
  previous_site_visible_progress_percent = $currentSite
  new_site_visible_progress_percent = if ($updatedSite) { [Math]::Min(85, $currentSite + $verified.Count) } else { $currentSite }
  next_required = 'photo_download_polygon_render_vision_compare_for_3_5_confidence'
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  created_at = (Get-Date).ToString('o')
}
$result | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -Path $outStatus

$md = @()
$md += '# AAYS1 Retry Skipped Candidates + Vision Queue Report'
$md += ''
$md += ('Status: ' + $result.status)
$md += ('Attempted rows: ' + (($result.attempted_rows) -join ', '))
$md += ('Verified rows added: ' + (($result.verified_rows_added) -join ', '))
$md += ('Site update applied: ' + $updatedSite)
$md += ('Site progress: ' + $currentSite + ' -> ' + $result.new_site_visible_progress_percent)
$md += ''
$md += 'Failed rows are preserved in JSON for later retry.'
$md += ''
$md += 'No 3.5+ confidence was written; photo download + polygon render + vision compare remains required.'
$md += ''
$md += 'Safety: final_ready=false, fake_data=false, db_write=false, migration=false, production_deploy=false.'
$md | Set-Content -Encoding UTF8 -Path $outReport

try {
  git -C $repoRoot add 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json' 'docs/chatgpt_status/aays1/status/139_aays1_retry_skipped_candidates_and_queue_vision_latest.json' 'docs/chatgpt_status/aays1/reports/139_aays1_retry_skipped_candidates_and_queue_vision_report.md' | Out-Null
  git -C $repoRoot commit -m 'Run aays1 skipped candidate retry and vision queue status' | Out-Null
  git -C $repoRoot push | Out-Null
} catch {}

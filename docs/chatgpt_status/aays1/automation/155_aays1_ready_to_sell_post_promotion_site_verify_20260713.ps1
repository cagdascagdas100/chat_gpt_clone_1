$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$canonicalRoot = if ($env:AAYS_CANONICAL_REPO_ROOT) { $env:AAYS_CANONICAL_REPO_ROOT } else { 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707' }
$branch = 'codex/aays-single-runner-v5-20260706'
$taskId = 'aays1-ready-to-sell-second-wave-dispatch-20260711'
$statusRelative = 'docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/155_aays1_ready_to_sell_second_wave_dispatch_report.md'
$dataRelative = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$htmlRelative = 'england_map_web/geometry_review_3of4_columns_1264.html'
$activeBatchRelative = 'england_map_web/data/aays1/ready_to_sell_active_batch_latest.json'
$paths = @('england_map_web/data/geometry_review_3of4','england_map_web/data/aays1','england_map_web/geometry_review_3of4_columns_1264.html')
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMdd_HHmmss')
$backupRelative = "docs/chatgpt_status/aays1/runner_outputs/155_canonical_site_sync_backup_$stamp"
$backupRoot = Join-Path $repoRoot $backupRelative
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath),(Split-Path $reportPath),$backupRoot | Out-Null

function Read-JsonFile([string]$path) {
  $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
  if ($text.Length -gt 0 -and [int]$text[0] -eq 65279) { $text = $text.Substring(1) }
  return ($text | ConvertFrom-Json)
}
function Get-Counts($data) {
  $rows = if ($data -and $data.results) { @($data.results) } else { @() }
  return [pscustomobject]@{
    rows = $rows.Count
    live = @($rows | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count
    photos = @($rows | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 }).Count
    polygons = @($rows | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
    ready = @($rows | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
    vision = @($rows | Where-Object { $null -ne $_.visual_match_score }).Count
    new_rows = @($rows | Where-Object { $_.new_this_run -eq $true }).Count
    links = @($rows | Where-Object {
      -not [string]::IsNullOrWhiteSpace([string]$_.listing_url) -and
      -not [string]::IsNullOrWhiteSpace([string]$_.status_json_path) -and
      -not [string]::IsNullOrWhiteSpace([string]$_.report_md_path)
    }).Count
  }
}
function Decode-HttpJson($response) {
  try { $text = [System.Text.Encoding]::UTF8.GetString($response.RawContentStream.ToArray()) }
  catch { $text = [string]$response.Content }
  if ($text.Length -gt 0 -and [int]$text[0] -eq 65279) { $text = $text.Substring(1) }
  $moji = ([char]239).ToString() + ([char]187).ToString() + ([char]191).ToString()
  if ($text.StartsWith($moji)) { $text = $text.Substring(3) }
  return ($text | ConvertFrom-Json)
}
function Backup-CanonicalState {
  param([string]$Root,[string]$Backup,[string[]]$AllowedPaths)
  try { @(& git -C $Root status --porcelain -- $AllowedPaths 2>$null) | Set-Content -LiteralPath (Join-Path $Backup 'site_paths_status_before.txt') -Encoding UTF8 } catch {}
  try { @(& git -C $Root diff --binary -- $AllowedPaths 2>$null) | Set-Content -LiteralPath (Join-Path $Backup 'site_paths_unstaged_before.patch') -Encoding UTF8 } catch {}
  try { @(& git -C $Root diff --cached --binary -- $AllowedPaths 2>$null) | Set-Content -LiteralPath (Join-Path $Backup 'site_paths_staged_before.patch') -Encoding UTF8 } catch {}
  foreach ($rel in @($dataRelative,$htmlRelative,$activeBatchRelative)) {
    $src = Join-Path $Root $rel
    if (Test-Path -LiteralPath $src) {
      $name = ($rel -replace '[/\\]','__')
      Copy-Item -LiteralPath $src -Destination (Join-Path $Backup $name) -Force -ErrorAction SilentlyContinue
    }
  }
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$blockers = [System.Collections.Generic.List[string]]::new()
$sourceData = $null; $sourceCounts = $null; $canonicalCounts = $null; $servedCounts = $null
$syncMode = 'not_run'; $canonicalBeforeSha = $null; $canonicalAfterSha = $null; $remoteSha = $null
$sourceDataPath = Join-Path $repoRoot $dataRelative

try {
  if (-not (Test-Path -LiteralPath $sourceDataPath)) { throw 'source_data_missing' }
  $sourceData = Read-JsonFile $sourceDataPath
  $sourceCounts = Get-Counts $sourceData
  if ($sourceCounts.rows -lt 115) { $blockers.Add("source_rows_below_expected:$($sourceCounts.rows)") }
} catch { $blockers.Add('source_data_read_failed:' + $_.Exception.Message) }

if (-not (Test-Path -LiteralPath $canonicalRoot)) {
  $blockers.Add('canonical_repo_root_missing')
} elseif (-not (Test-Path -LiteralPath (Join-Path $canonicalRoot '.git'))) {
  $blockers.Add('canonical_repo_git_missing')
} else {
  $canonicalBeforeSha = (& git -C $canonicalRoot rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
  Backup-CanonicalState -Root $canonicalRoot -Backup $backupRoot -AllowedPaths $paths
  & git -C $canonicalRoot fetch origin $branch 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) {
    $blockers.Add('canonical_fetch_failed')
  } else {
    $remoteSha = (& git -C $canonicalRoot rev-parse "origin/$branch" 2>$null | Select-Object -First 1).Trim()
    $archivePath = Join-Path ([System.IO.Path]::GetTempPath()) ("aays155_site_{0}_{1}.zip" -f $PID,[guid]::NewGuid().ToString('N'))
    $extractRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("aays155_site_{0}_{1}" -f $PID,[guid]::NewGuid().ToString('N'))
    try {
      & git -C $canonicalRoot archive --format=zip -o $archivePath "origin/$branch" -- $paths 2>$null
      if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $archivePath)) { throw 'remote_site_archive_failed' }
      Expand-Archive -LiteralPath $archivePath -DestinationPath $extractRoot -Force
      foreach ($rel in $paths) {
        $src = Join-Path $extractRoot $rel
        $dst = Join-Path $canonicalRoot $rel
        if (-not (Test-Path -LiteralPath $src)) { throw "archive_path_missing:$rel" }
        if ((Get-Item -LiteralPath $src).PSIsContainer) {
          New-Item -ItemType Directory -Force -Path $dst | Out-Null
          Copy-Item -Path (Join-Path $src '*') -Destination $dst -Recurse -Force
        } else {
          New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
          Copy-Item -LiteralPath $src -Destination $dst -Force
        }
      }
      $syncMode = 'selective_remote_archive_overlay_with_backup'
    } catch {
      $blockers.Add('canonical_selective_site_sync_failed:' + $_.Exception.Message)
    } finally {
      Remove-Item -LiteralPath $archivePath -Force -ErrorAction SilentlyContinue
      Remove-Item -LiteralPath $extractRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
  $canonicalAfterSha = (& git -C $canonicalRoot rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
}

try {
  $canonicalDataPath = Join-Path $canonicalRoot $dataRelative
  if (-not (Test-Path -LiteralPath $canonicalDataPath)) { throw 'canonical_data_missing_after_sync' }
  $canonicalData = Read-JsonFile $canonicalDataPath
  $canonicalCounts = Get-Counts $canonicalData
  if ($sourceCounts -and ($canonicalCounts.rows -ne $sourceCounts.rows -or $canonicalCounts.live -ne $sourceCounts.live -or $canonicalCounts.photos -ne $sourceCounts.photos -or $canonicalCounts.polygons -ne $sourceCounts.polygons)) {
    $blockers.Add('canonical_counts_do_not_match_source_branch')
  }
} catch { $blockers.Add('canonical_data_read_failed:' + $_.Exception.Message) }

Start-Sleep -Seconds 3
$healthStatus = $null; $pageStatus = $null; $jsonStatus = $null; $htmlContractOk = $false; $servedMatchesSource = $false
try {
  $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8012/health' -UseBasicParsing -TimeoutSec 25
  $healthStatus = [int]$r.StatusCode
  if ($healthStatus -ne 200) { $blockers.Add("health_http_$healthStatus") }
} catch { $blockers.Add('health_probe_failed:' + $_.Exception.Message) }
try {
  $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html' -UseBasicParsing -TimeoutSec 35
  $pageStatus = [int]$r.StatusCode
  $htmlText = [string]$r.Content
  $htmlContractOk = $pageStatus -eq 200 -and $htmlText.Contains('newOnly') -and $htmlText.Contains('NOT_PROCESSED') -and $htmlText.Contains('status_json_path') -and $htmlText.Contains('report_md_path') -and $htmlText.Contains('downloaded_photo_paths') -and $htmlText.Contains('polygon_render_path')
  if (-not $htmlContractOk) { $blockers.Add('served_html_contract_incomplete') }
} catch { $blockers.Add('page_probe_failed:' + $_.Exception.Message) }
try {
  $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8012/england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json' -UseBasicParsing -TimeoutSec 35
  $jsonStatus = [int]$r.StatusCode
  $servedData = Decode-HttpJson $r
  $servedCounts = Get-Counts $servedData
  $servedMatchesSource = $jsonStatus -eq 200 -and $sourceCounts -and $servedCounts.rows -eq $sourceCounts.rows -and $servedCounts.live -eq $sourceCounts.live -and $servedCounts.photos -eq $sourceCounts.photos -and $servedCounts.polygons -eq $sourceCounts.polygons
  if (-not $servedMatchesSource) { $blockers.Add('served_json_still_not_synced_with_source_branch') }
} catch { $blockers.Add('json_probe_failed:' + $_.Exception.Message) }

$uniqueBlockers = @($blockers | Select-Object -Unique)
$statusName = if ($uniqueBlockers.Count -eq 0 -and $servedMatchesSource -and $htmlContractOk) { 'SECOND_WAVE_SITE_VISIBILITY_VERIFIED' } else { 'SECOND_WAVE_SITE_VISIBILITY_PARTIAL_OR_BLOCKED' }
$status = [ordered]@{
  task_id=$taskId; page_key='aays1'; status=$statusName; runner_mode='single_shared_runner_sequential'
  canonical_sync_mode=$syncMode; canonical_root=$canonicalRoot; canonical_backup_path=$backupRelative
  canonical_before_sha=$canonicalBeforeSha; canonical_after_sha=$canonicalAfterSha; remote_branch_sha=$remoteSha
  health_http_status=$healthStatus; page_http_status=$pageStatus; json_http_status=$jsonStatus
  html_contract_ok=[bool]$htmlContractOk; served_json_matches_source=[bool]$servedMatchesSource
  source_counts=$sourceCounts; canonical_counts=$canonicalCounts; served_counts=$servedCounts
  live_source_verified_rows=if($sourceCounts){$sourceCounts.live}else{$null}; new_this_run_rows=if($sourceCounts){$sourceCounts.new_rows}else{$null}
  rows_with_downloaded_photos=if($sourceCounts){$sourceCounts.photos}else{$null}; rows_with_polygon_render=if($sourceCounts){$sourceCounts.polygons}else{$null}
  rows_evidence_ready=if($sourceCounts){$sourceCounts.ready}else{$null}; rows_with_real_vision_score=if($sourceCounts){$sourceCounts.vision}else{0}
  rows_with_listing_status_report_links=if($sourceCounts){$sourceCounts.links}else{$null}; blockers=$uniqueBlockers
  started_at=$startedAt; finished_at=[DateTimeOffset]::UtcNow.ToString('o')
  final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
$status | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$lines = @(
  '# AAYS1 ReadyToSell Canonical Site Sync and Verification','',
  "- Status: $statusName","- Sync mode: $syncMode","- Backup: $backupRelative",
  "- Source rows/live/photo/polygon/ready/vision: $($sourceCounts.rows) / $($sourceCounts.live) / $($sourceCounts.photos) / $($sourceCounts.polygons) / $($sourceCounts.ready) / $($sourceCounts.vision)",
  "- Canonical rows/live/photo/polygon: $($canonicalCounts.rows) / $($canonicalCounts.live) / $($canonicalCounts.photos) / $($canonicalCounts.polygons)",
  "- Served rows/live/photo/polygon: $($servedCounts.rows) / $($servedCounts.live) / $($servedCounts.photos) / $($servedCounts.polygons)",
  "- HTTP health/page/json: $healthStatus / $pageStatus / $jsonStatus","- HTML contract: $htmlContractOk","- Served matches source: $servedMatchesSource",
  "- Blockers: $($uniqueBlockers -join '; ')",'',
  '`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
)
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))

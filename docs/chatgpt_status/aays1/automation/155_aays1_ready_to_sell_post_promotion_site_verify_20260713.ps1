$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$portableRoot = if ($env:AAYS_PORTABLE_ROOT) {
  $env:AAYS_PORTABLE_ROOT
} elseif ($repoRoot -match '^(.*?)[\\/]+runner_system[\\/]') {
  $Matches[1]
} else {
  $null
}
$portableAppRoot = if ($portableRoot) { Join-Path $portableRoot 'AAYS' } else { $null }
$canonicalRoot = if ($env:AAYS_LIVE_APP_ROOT) {
  $env:AAYS_LIVE_APP_ROOT
} elseif ($portableAppRoot -and (Test-Path -LiteralPath (Join-Path $portableAppRoot 'england_map_web'))) {
  $portableAppRoot
} elseif ($env:AAYS_CANONICAL_REPO_ROOT) {
  $env:AAYS_CANONICAL_REPO_ROOT
} else {
  $repoRoot
}
$taskId = 'aays1-ready-to-sell-second-wave-dispatch-20260711'
$statusRelative = 'docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/155_aays1_ready_to_sell_second_wave_dispatch_report.md'
$dataRelative = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$htmlRelative = 'england_map_web/geometry_review_3of4_columns_1264.html'
$activeBatchRelative = 'england_map_web/data/aays1/ready_to_sell_active_batch_latest.json'
$allowedPaths = @('england_map_web/data/geometry_review_3of4','england_map_web/data/aays1','england_map_web/geometry_review_3of4_columns_1264.html')
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
    rows=$rows.Count
    live=@($rows | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count
    photos=@($rows | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 }).Count
    polygons=@($rows | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
    ready=@($rows | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
    vision=@($rows | Where-Object { $null -ne $_.visual_match_score }).Count
    new_rows=@($rows | Where-Object { $_.new_this_run -eq $true }).Count
    links=@($rows | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.listing_url) -and -not [string]::IsNullOrWhiteSpace([string]$_.status_json_path) -and -not [string]::IsNullOrWhiteSpace([string]$_.report_md_path) }).Count
  }
}
function Decode-HttpJson($response) {
  try { $text = [System.Text.Encoding]::UTF8.GetString($response.RawContentStream.ToArray()) } catch { $text = [string]$response.Content }
  if ($text.Length -gt 0 -and [int]$text[0] -eq 65279) { $text = $text.Substring(1) }
  $moji = ([char]239).ToString() + ([char]187).ToString() + ([char]191).ToString()
  if ($text.StartsWith($moji)) { $text = $text.Substring(3) }
  return ($text | ConvertFrom-Json)
}
function Backup-CanonicalState([string]$Root,[string]$Backup,[string[]]$Paths) {
  $flatRoot = Join-Path $Backup 'dirty_files_flat'
  New-Item -ItemType Directory -Force -Path $flatRoot | Out-Null
  $statusLines = @(& git -C $Root status --porcelain -- $Paths 2>$null)
  $statusLines | Set-Content -LiteralPath (Join-Path $Backup 'site_paths_status_before.txt') -Encoding UTF8
  try { @(& git -C $Root diff --binary -- $Paths 2>$null) | Set-Content -LiteralPath (Join-Path $Backup 'site_paths_unstaged_before.patch') -Encoding UTF8 } catch {}
  try { @(& git -C $Root diff --cached --binary -- $Paths 2>$null) | Set-Content -LiteralPath (Join-Path $Backup 'site_paths_staged_before.patch') -Encoding UTF8 } catch {}
  $manifest = [System.Collections.Generic.List[object]]::new(); $i = 0
  foreach ($line in $statusLines) {
    if ([string]::IsNullOrWhiteSpace($line) -or $line.Length -lt 4) { continue }
    $rel = $line.Substring(3).Trim('"')
    if ($rel -match ' -> ') { $rel = ($rel -split ' -> ')[-1].Trim('"') }
    $src = Join-Path $Root $rel
    if (-not (Test-Path -LiteralPath $src)) { continue }
    $i++; $leaf = (Split-Path $rel -Leaf); if ([string]::IsNullOrWhiteSpace($leaf)) { $leaf = 'item' }
    $safeLeaf = ($leaf -replace '[^A-Za-z0-9._-]','_')
    $dst = Join-Path $flatRoot ('{0:D4}_{1}' -f $i,$safeLeaf)
    if ((Get-Item -LiteralPath $src).PSIsContainer) { Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force }
    else { Copy-Item -LiteralPath $src -Destination $dst -Force }
    $manifest.Add([pscustomobject]@{ original=$rel; backup=(Resolve-Path -LiteralPath $dst).Path })
  }
  $manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $Backup 'dirty_files_manifest.json') -Encoding UTF8
  foreach ($rel in @($dataRelative,$htmlRelative,$activeBatchRelative)) {
    $src = Join-Path $Root $rel
    if (Test-Path -LiteralPath $src) {
      $flatName = ($rel -replace '[/\\]','__')
      Copy-Item -LiteralPath $src -Destination (Join-Path $Backup $flatName) -Force
    }
  }
}
function Overlay-AllowedPaths([string]$SourceRoot,[string]$TargetRoot,[string[]]$Paths) {
  foreach ($rel in $Paths) {
    $src = Join-Path $SourceRoot $rel; $dst = Join-Path $TargetRoot $rel
    if (-not (Test-Path -LiteralPath $src)) { throw "source_overlay_path_missing:$rel" }
    if ((Get-Item -LiteralPath $src).PSIsContainer) {
      if (Test-Path -LiteralPath $dst) { Remove-Item -LiteralPath $dst -Recurse -Force }
      New-Item -ItemType Directory -Force -Path $dst | Out-Null
      Get-ChildItem -LiteralPath $src -Force | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $dst -Recurse -Force }
    } else {
      New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
      Copy-Item -LiteralPath $src -Destination $dst -Force
    }
  }
}

$startedAt=[DateTimeOffset]::UtcNow.ToString('o'); $blockers=[System.Collections.Generic.List[string]]::new()
$sourceData=$null; $sourceCounts=$null; $canonicalCounts=$null; $servedCounts=$null; $syncMode='not_run'
$sourceDataPath=Join-Path $repoRoot $dataRelative
try {
  if (-not (Test-Path -LiteralPath $sourceDataPath)) { throw 'source_data_missing' }
  $sourceData=Read-JsonFile $sourceDataPath; $sourceCounts=Get-Counts $sourceData
  if ($sourceCounts.rows -lt 115) { $blockers.Add("source_rows_below_expected:$($sourceCounts.rows)") }
} catch { $blockers.Add('source_data_read_failed:' + $_.Exception.Message) }

if (-not (Test-Path -LiteralPath $canonicalRoot)) { $blockers.Add('canonical_repo_root_missing') }
else {
  try {
    Backup-CanonicalState -Root $canonicalRoot -Backup $backupRoot -Paths $allowedPaths
    Overlay-AllowedPaths -SourceRoot $repoRoot -TargetRoot $canonicalRoot -Paths $allowedPaths
    $syncMode='selective_task_worktree_overlay_with_flat_dirty_backup'
  } catch { $blockers.Add('canonical_selective_site_sync_failed:' + $_.Exception.Message) }
}
try {
  $canonicalDataPath=Join-Path $canonicalRoot $dataRelative
  if (-not (Test-Path -LiteralPath $canonicalDataPath)) { throw 'canonical_data_missing_after_sync' }
  $canonicalCounts=Get-Counts (Read-JsonFile $canonicalDataPath)
  if ($sourceCounts -and ($canonicalCounts.rows -ne $sourceCounts.rows -or $canonicalCounts.live -ne $sourceCounts.live -or $canonicalCounts.photos -ne $sourceCounts.photos -or $canonicalCounts.polygons -ne $sourceCounts.polygons)) { $blockers.Add('canonical_counts_do_not_match_source_worktree') }
} catch { $blockers.Add('canonical_data_read_failed:' + $_.Exception.Message) }

Start-Sleep -Seconds 3
$healthStatus=$null; $pageStatus=$null; $jsonStatus=$null; $htmlContractOk=$false; $servedMatchesSource=$false
try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:8012/health' -UseBasicParsing -TimeoutSec 25; $healthStatus=[int]$r.StatusCode; if($healthStatus-ne 200){$blockers.Add("health_http_$healthStatus")} } catch { $blockers.Add('health_probe_failed:' + $_.Exception.Message) }
try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html' -UseBasicParsing -TimeoutSec 35; $pageStatus=[int]$r.StatusCode; $h=[string]$r.Content; $htmlContractOk=$pageStatus-eq 200 -and $h.Contains('newOnly') -and $h.Contains('NOT_PROCESSED') -and $h.Contains('status_json_path') -and $h.Contains('report_md_path') -and $h.Contains('downloaded_photo_paths') -and $h.Contains('polygon_render_path'); if(-not $htmlContractOk){$blockers.Add('served_html_contract_incomplete')} } catch { $blockers.Add('page_probe_failed:' + $_.Exception.Message) }
try { $r=Invoke-WebRequest -Uri 'http://127.0.0.1:8012/england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json' -UseBasicParsing -TimeoutSec 35; $jsonStatus=[int]$r.StatusCode; $servedCounts=Get-Counts (Decode-HttpJson $r); $servedMatchesSource=$jsonStatus-eq 200 -and $sourceCounts -and $servedCounts.rows-eq $sourceCounts.rows -and $servedCounts.live-eq $sourceCounts.live -and $servedCounts.photos-eq $sourceCounts.photos -and $servedCounts.polygons-eq $sourceCounts.polygons; if(-not $servedMatchesSource){$blockers.Add('served_json_still_not_synced_with_source_worktree')} } catch { $blockers.Add('json_probe_failed:' + $_.Exception.Message) }

$uniqueBlockers=@($blockers|Select-Object -Unique)
$statusName=if($uniqueBlockers.Count-eq 0 -and $servedMatchesSource -and $htmlContractOk){'SECOND_WAVE_SITE_VISIBILITY_VERIFIED'}else{'SECOND_WAVE_SITE_VISIBILITY_PARTIAL_OR_BLOCKED'}
$status=[ordered]@{
 task_id=$taskId; page_key='aays1'; status=$statusName; runner_mode='single_shared_runner_sequential'; canonical_sync_mode=$syncMode; canonical_root=$canonicalRoot; canonical_backup_path=$backupRelative
 health_http_status=$healthStatus; page_http_status=$pageStatus; json_http_status=$jsonStatus; html_contract_ok=[bool]$htmlContractOk; served_json_matches_source=[bool]$servedMatchesSource
 source_counts=$sourceCounts; canonical_counts=$canonicalCounts; served_counts=$servedCounts
 live_source_verified_rows=if($sourceCounts){$sourceCounts.live}else{$null}; new_this_run_rows=if($sourceCounts){$sourceCounts.new_rows}else{$null}; rows_with_downloaded_photos=if($sourceCounts){$sourceCounts.photos}else{$null}; rows_with_polygon_render=if($sourceCounts){$sourceCounts.polygons}else{$null}; rows_evidence_ready=if($sourceCounts){$sourceCounts.ready}else{$null}; rows_with_real_vision_score=if($sourceCounts){$sourceCounts.vision}else{0}; rows_with_listing_status_report_links=if($sourceCounts){$sourceCounts.links}else{$null}
 blockers=$uniqueBlockers; started_at=$startedAt; finished_at=[DateTimeOffset]::UtcNow.ToString('o'); final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
$status|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $statusPath -Encoding UTF8
$lines=@('# AAYS1 ReadyToSell Canonical Site Sync and Verification','',"- Status: $statusName","- Sync mode: $syncMode","- Backup: $backupRelative","- Source rows/live/photo/polygon/ready/vision: $($sourceCounts.rows) / $($sourceCounts.live) / $($sourceCounts.photos) / $($sourceCounts.polygons) / $($sourceCounts.ready) / $($sourceCounts.vision)","- Canonical rows/live/photo/polygon: $($canonicalCounts.rows) / $($canonicalCounts.live) / $($canonicalCounts.photos) / $($canonicalCounts.polygons)","- Served rows/live/photo/polygon: $($servedCounts.rows) / $($servedCounts.live) / $($servedCounts.photos) / $($servedCounts.polygons)","- HTTP health/page/json: $healthStatus / $pageStatus / $jsonStatus","- HTML contract: $htmlContractOk","- Served matches source: $servedMatchesSource","- Blockers: $($uniqueBlockers -join '; ')",'','`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))

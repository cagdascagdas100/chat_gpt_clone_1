$ErrorActionPreference = 'Stop'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = '208_aays1_ready_to_sell_short_backup_geometry_recovery_20260714'
$siteScriptRel = 'docs/chatgpt_status/aays1/automation/155_aays1_ready_to_sell_post_promotion_site_verify_20260713.ps1'
$chainScriptRel = 'docs/chatgpt_status/aays1/automation/166_aays1_ready_to_sell_eight_wave_continuation_20260713.ps1'
$chainStatusRel = 'docs/chatgpt_status/aays1/status/166_aays1_ready_to_sell_eight_wave_continuation_latest.json'
$dataRel = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$geoPrimaryRel = 'docs/chatgpt_status/aays1/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
$geoFallbackRel = 'england_map_web/data/geometry_review_3of4/all_1264_real_geometry_3of4.geojson'
$outRel = 'docs/chatgpt_status/aays1/runner_outputs/208_ready_to_sell_short_backup_geometry_recovery_20260714.json'
$reportRel = 'docs/chatgpt_status/aays1/reports/208_ready_to_sell_short_backup_geometry_recovery_20260714.md'

$siteScriptPath = Join-Path $repoRoot $siteScriptRel
$chainScriptPath = Join-Path $repoRoot $chainScriptRel
$chainStatusPath = Join-Path $repoRoot $chainStatusRel
$dataPath = Join-Path $repoRoot $dataRel
$geoPrimaryPath = Join-Path $repoRoot $geoPrimaryRel
$geoFallbackPath = Join-Path $repoRoot $geoFallbackRel
$outPath = Join-Path $repoRoot $outRel
$reportPath = Join-Path $repoRoot $reportRel
New-Item -ItemType Directory -Force -Path (Split-Path $outPath),(Split-Path $reportPath) | Out-Null

function Read-JsonSafe([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
  if ($text.Length -gt 0 -and [int]$text[0] -eq 65279) { $text = $text.Substring(1) }
  return ($text | ConvertFrom-Json)
}
function Get-Counts([string]$path) {
  $data = Read-JsonSafe $path
  $rows = if ($data -and $data.results) { @($data.results) } else { @() }
  return [ordered]@{
    rows = $rows.Count
    live = @($rows | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count
    photos = @($rows | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 }).Count
    polygons = @($rows | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
    ready = @($rows | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
  }
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$blockers = [System.Collections.Generic.List[string]]::new()
$patchApplied = $false
$before = Get-Counts $dataPath
$after = $before
$child = $null
$childExit = $null

try {
  if (-not (Test-Path -LiteralPath $siteScriptPath)) { throw "missing_site_script:$siteScriptRel" }
  if (-not (Test-Path -LiteralPath $chainScriptPath)) { throw "missing_chain_script:$chainScriptRel" }
  if (-not (Test-Path -LiteralPath $dataPath)) { throw "missing_ready_to_sell_data:$dataRel" }
  if (-not (Test-Path -LiteralPath $geoPrimaryPath) -and -not (Test-Path -LiteralPath $geoFallbackPath)) { throw 'canonical_geometry_missing_from_task_worktree' }

  $siteText = (Get-Content -LiteralPath $siteScriptPath -Raw -Encoding UTF8) -replace "`r`n","`n"
  $old = @'
$backupRelative = "docs/chatgpt_status/aays1/runner_outputs/155_canonical_site_sync_backup_$stamp"
$backupRoot = Join-Path $repoRoot $backupRelative
'@
  $replacement = @'
$backupRelative = "runner_system/recovery/155_canonical_site_sync_backup_$stamp"
$backupRoot = if ($portableRoot) { Join-Path $portableRoot $backupRelative } else { Join-Path ([System.IO.Path]::GetTempPath()) ("AAYS_155_" + $stamp) }
'@
  if ($siteText.Contains($old.Trim())) {
    $siteText = $siteText.Replace($old.Trim(),$replacement.Trim())
    [System.IO.File]::WriteAllText($siteScriptPath,$siteText,[System.Text.UTF8Encoding]::new($false))
    $patchApplied = $true
  } elseif ($siteText -match 'runner_system/recovery/155_canonical_site_sync_backup_' -or $siteText -match 'docs/chatgpt_status/aays1/runner_outputs/155b_\$stamp') {
    $patchApplied = $false
  } else {
    throw 'site_backup_path_contract_not_found'
  }

  $previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE
  try {
    $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $chainScriptPath
    $childExit = $LASTEXITCODE
    if ($null -eq $childExit) { $childExit = 0 }
  } finally {
    $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
  }

  $child = Read-JsonSafe $chainStatusPath
  if ($null -eq $child) { $blockers.Add('missing_or_invalid_chain_status') }
  else {
    foreach ($b in @($child.blockers)) { if ($b) { $blockers.Add([string]$b) } }
    if (-not [bool]$child.site_visibility_verified) { $blockers.Add('site_visibility_not_verified') }
  }
  if ($childExit -ne 0) { $blockers.Add("chain_exit_$childExit") }
  $after = Get-Counts $dataPath
} catch {
  $blockers.Add($_.Exception.Message)
}

$uniqueBlockers = @($blockers | Where-Object { $_ } | Select-Object -Unique)
$result = [ordered]@{
  task_id = $taskId
  page_key = 'aays1'
  status = if ($uniqueBlockers.Count -eq 0) { 'completed_ready_to_sell_site_and_geometry_chain_verified' } else { 'blocked_ready_to_sell_recovery' }
  started_at = $startedAt
  completed_at = [DateTimeOffset]::UtcNow.ToString('o')
  short_backup_patch_applied = [bool]$patchApplied
  canonical_geometry_present = [bool]((Test-Path -LiteralPath $geoPrimaryPath) -or (Test-Path -LiteralPath $geoFallbackPath))
  child_exit_code = $childExit
  child_status = if ($child) { [string]$child.status } else { $null }
  candidates_examined = if ($child) { [int]$child.candidates_examined } else { 0 }
  accepted_count = if ($child) { [int]$child.accepted_count } else { 0 }
  counts_before = $before
  counts_after = $after
  source_verified_delta = ([int]$after.live - [int]$before.live)
  photo_rows_delta = ([int]$after.photos - [int]$before.photos)
  polygon_rows_delta = ([int]$after.polygons - [int]$before.polygons)
  evidence_ready_delta = ([int]$after.ready - [int]$before.ready)
  site_visibility_verified = if ($child) { [bool]$child.site_visibility_verified } else { $false }
  blockers = $uniqueBlockers
  single_runner_only = $true
  parallel_runner = $false
  five_by_five_plan_applied = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$result | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $outPath -Encoding UTF8

$lines = @(
  '# Ready to Sell Short-Backup and Geometry Recovery','',
  "- Status: $($result.status)",
  "- Candidates examined / accepted: $($result.candidates_examined) / $($result.accepted_count)",
  "- Rows before/after: $($before.rows) / $($after.rows)",
  "- Live delta: $($result.source_verified_delta)",
  "- Photo delta: $($result.photo_rows_delta)",
  "- Polygon delta: $($result.polygon_rows_delta)",
  "- Evidence-ready delta: $($result.evidence_ready_delta)",
  "- Site visibility verified: $($result.site_visibility_verified)",
  "- Blockers: $($uniqueBlockers -join '; ')",'',
  '- single_runner_only=true',
  '- parallel_runner=false',
  '- five_by_five_plan_applied=false',
  '- final_ready=false'
)
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))

Write-Host "OUTPUT=$outPath"
if ($uniqueBlockers.Count -gt 0) { exit 2 }
exit 0

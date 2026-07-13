$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = 'aays1-ready-to-sell-second-wave-dispatch-20260711'
$statusRelative = 'docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/155_aays1_ready_to_sell_second_wave_dispatch_report.md'
$childScriptRelative = 'docs/chatgpt_status/aays1/automation/154_aays1_ready_to_sell_site_row_visibility_verify_20260711.ps1'
$childStatusRelative = 'docs/chatgpt_status/aays1/status/154_aays1_ready_to_sell_site_row_visibility_verify_latest.json'
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$childScriptPath = Join-Path $repoRoot $childScriptRelative
$childStatusPath = Join-Path $repoRoot $childStatusRelative
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath),(Split-Path $reportPath) | Out-Null

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$blockers = [System.Collections.Generic.List[string]]::new()
$childHeadBefore = (& git -C $repoRoot rev-parse HEAD 2>$null).Trim()
$childHeadAfter = $childHeadBefore
$exitCode = 1
$childCommitUnwound = $false
$previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE
try {
  if (-not (Test-Path -LiteralPath $childScriptPath)) { throw "missing_script:$childScriptRelative" }
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $childScriptPath
  $exitCode = $LASTEXITCODE
  if ($null -eq $exitCode) { $exitCode = 0 }
  $childHeadAfter = (& git -C $repoRoot rev-parse HEAD 2>$null).Trim()
  if ($childHeadAfter -and $childHeadBefore -and $childHeadAfter -ne $childHeadBefore) {
    & git -C $repoRoot reset --mixed $childHeadBefore | Out-Null
    if ($LASTEXITCODE -eq 0) { $childCommitUnwound = $true }
    else { $blockers.Add("child_commit_unwind_failed:$childHeadAfter") }
  }
  if ($exitCode -ne 0) { $blockers.Add("site_visibility_job_exit_$exitCode") }
  if (-not (Test-Path -LiteralPath $childStatusPath)) { $blockers.Add('site_visibility_status_missing') }
} catch {
  $blockers.Add($_.Exception.Message)
} finally {
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
}

$childStatus = $null
try { if (Test-Path -LiteralPath $childStatusPath) { $childStatus = Get-Content -LiteralPath $childStatusPath -Raw -Encoding UTF8 | ConvertFrom-Json } } catch { $blockers.Add('site_visibility_status_parse_failed') }
$status = [ordered]@{
  task_id = $taskId
  page_key = 'aays1'
  status = if ($blockers.Count -eq 0 -and $childStatus -and $childStatus.status -eq 'SITE_ROW_VISIBILITY_VERIFIED') { 'SECOND_WAVE_SITE_VISIBILITY_VERIFIED' } else { 'SECOND_WAVE_SITE_VISIBILITY_PARTIAL_OR_BLOCKED' }
  runner_mode = 'single_shared_runner_sequential'
  child_task = '154'
  child_status = if ($childStatus) { $childStatus.status } else { $null }
  live_source_verified_rows = if ($childStatus) { $childStatus.live_source_verified_rows } else { $null }
  new_this_run_rows = if ($childStatus) { $childStatus.new_this_run_rows } else { $null }
  rows_with_downloaded_photos = if ($childStatus) { $childStatus.rows_with_downloaded_photos } else { $null }
  rows_with_polygon_render = if ($childStatus) { $childStatus.rows_with_polygon_render } else { $null }
  rows_evidence_ready = if ($childStatus) { $childStatus.rows_evidence_ready } else { $null }
  rows_with_real_vision_score = if ($childStatus) { $childStatus.rows_with_real_vision_score } else { 0 }
  child_head_before = $childHeadBefore
  child_head_after = $childHeadAfter
  child_detached_commit_unwound = $childCommitUnwound
  blockers = @($blockers)
  started_at = $startedAt
  finished_at = [DateTimeOffset]::UtcNow.ToString('o')
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$status | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$lines = @(
  '# AAYS1 ReadyToSell Post-Promotion Site Verification',
  '',
  "- Status: $($status.status)",
  "- Child 154: $($status.child_status)",
  "- Live source rows: $($status.live_source_verified_rows)",
  "- Photo rows: $($status.rows_with_downloaded_photos)",
  "- Polygon rows: $($status.rows_with_polygon_render)",
  "- Evidence-ready rows: $($status.rows_evidence_ready)",
  "- Real vision rows: $($status.rows_with_real_vision_score)",
  "- Blockers: $($blockers -join '; ')",
  '',
  '`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
)
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))

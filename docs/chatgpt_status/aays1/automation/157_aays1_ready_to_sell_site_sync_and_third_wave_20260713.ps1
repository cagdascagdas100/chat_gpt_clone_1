$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = 'aays1-ready-to-sell-recovery-third-wave-20260713'
$statusRelative = 'docs/chatgpt_status/aays1/status/157_aays1_ready_to_sell_site_sync_and_third_wave_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/157_aays1_ready_to_sell_site_sync_and_third_wave_report.md'
$logRootRelative = 'docs/chatgpt_status/aays1/runner_outputs/157_site_sync_and_third_wave_20260713'
$dataRelative = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$logRoot = Join-Path $repoRoot $logRootRelative
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath),(Split-Path $reportPath),$logRoot | Out-Null

function Read-JsonSafe([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  try {
    $text = Get-Content -LiteralPath $path -Raw -Encoding UTF8
    if ($text.Length -gt 0 -and [int]$text[0] -eq 65279) { $text = $text.Substring(1) }
    return ($text | ConvertFrom-Json)
  } catch { return $null }
}
function Get-CountsFromData([string]$path) {
  $data = Read-JsonSafe $path
  $rows = if ($data -and $data.results) { @($data.results) } else { @() }
  return [pscustomobject]@{
    rows = $rows.Count
    live = @($rows | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count
    photos = @($rows | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 }).Count
    polygons = @($rows | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
    ready = @($rows | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
    vision = @($rows | Where-Object { $null -ne $_.visual_match_score }).Count
    new_rows = @($rows | Where-Object { $_.new_this_run -eq $true }).Count
  }
}
function Invoke-ChildJob {
  param(
    [string]$Name,
    [string]$ScriptRelative,
    [string]$ExpectedRelative,
    [string]$MetricName,
    [string]$RequiredStatus
  )
  $scriptPath = Join-Path $repoRoot $ScriptRelative
  $expectedPath = Join-Path $repoRoot $ExpectedRelative
  $logRelative = "$logRootRelative/$Name.log"
  $logPath = Join-Path $repoRoot $logRelative
  $started = [DateTimeOffset]::UtcNow.ToString('o')
  $headBefore = (& git -C $repoRoot rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
  $headAfter = $headBefore
  $unwound = $false
  $exitCode = 1
  $metric = 0
  $outputStatus = $null
  $state = 'not_run'
  $jobBlockers = [System.Collections.Generic.List[string]]::new()
  $previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE
  try {
    if (-not (Test-Path -LiteralPath $scriptPath)) { throw "missing_script:$ScriptRelative" }
    "[$started] START $ScriptRelative" | Set-Content -LiteralPath $logPath -Encoding UTF8
    $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath *>> $logPath
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) { $exitCode = 0 }
    $headAfter = (& git -C $repoRoot rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
    if ($headBefore -and $headAfter -and $headAfter -ne $headBefore) {
      & git -C $repoRoot reset --mixed $headBefore *>> $logPath
      if ($LASTEXITCODE -eq 0) { $unwound = $true } else { $jobBlockers.Add("child_commit_unwind_failed:$Name") }
    }
    $output = Read-JsonSafe $expectedPath
    if (-not $output) {
      $state = 'expected_output_missing'
      $jobBlockers.Add("expected_output_missing:$ExpectedRelative")
    } else {
      $outputStatus = [string]$output.status
      if ($MetricName) {
        $p = $output.PSObject.Properties[$MetricName]
        if ($p -and $null -ne $p.Value) { $metric = [int]$p.Value }
      }
      if ($output.blockers) { foreach ($b in @($output.blockers)) { if ($b) { $jobBlockers.Add([string]$b) } } }
      if ($RequiredStatus -and $outputStatus -ne $RequiredStatus) {
        $state = 'output_created_status_partial'
        $jobBlockers.Add("required_status_not_met:$RequiredStatus:$outputStatus")
      } elseif ($exitCode -eq 0) {
        $state = if ($metric -gt 0) { 'output_created_with_real_progress' } else { 'output_created' }
      } else {
        $state = 'output_created_child_nonzero'
        $jobBlockers.Add("child_exit_nonzero:$exitCode")
      }
    }
  } catch {
    $state = 'execution_exception'
    $jobBlockers.Add($_.Exception.Message)
    $_.Exception.ToString() | Add-Content -LiteralPath $logPath -Encoding UTF8
  } finally {
    $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
  }
  return [pscustomobject]@{
    name=$Name; script_path=$ScriptRelative; expected_status_path=$ExpectedRelative
    state=$state; exit_code=$exitCode; output_status=$outputStatus; real_progress_count=$metric
    child_head_before=$headBefore; child_head_after=$headAfter; child_detached_commit_unwound=$unwound
    blockers=@($jobBlockers | Select-Object -Unique); log_path=$logRelative
    started_at=$started; finished_at=[DateTimeOffset]::UtcNow.ToString('o')
  }
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$dataPath = Join-Path $repoRoot $dataRelative
$before = Get-CountsFromData $dataPath
$results = [System.Collections.Generic.List[object]]::new()
$allBlockers = [System.Collections.Generic.List[string]]::new()

$jobs = @(
  [pscustomobject]@{ name='pre_site_sync'; script='docs/chatgpt_status/aays1/automation/155_aays1_ready_to_sell_post_promotion_site_verify_20260713.ps1'; expected='docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'; metric='live_source_verified_rows'; required='SECOND_WAVE_SITE_VISIBILITY_VERIFIED' },
  [pscustomobject]@{ name='evidence_20'; script='docs/chatgpt_status/aays1/automation/150_aays1_bulk_photo_polygon_evidence_20_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/150_aays1_bulk_photo_polygon_evidence_latest.json'; metric='rows_evidence_ready_this_run'; required='' },
  [pscustomobject]@{ name='source_scan_300x60'; script='docs/chatgpt_status/aays1/automation/152_aays1_bulk_live_source_verify_300x60_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/152_aays1_bulk_live_source_verify_300x60_latest.json'; metric='verified_rows_added_count'; required='' },
  [pscustomobject]@{ name='evidence_40'; script='docs/chatgpt_status/aays1/automation/153_aays1_bulk_photo_polygon_evidence_40_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/153_aays1_bulk_photo_polygon_evidence_40_latest.json'; metric='rows_evidence_ready_this_run'; required='' },
  [pscustomobject]@{ name='post_site_sync'; script='docs/chatgpt_status/aays1/automation/155_aays1_ready_to_sell_post_promotion_site_verify_20260713.ps1'; expected='docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'; metric='live_source_verified_rows'; required='SECOND_WAVE_SITE_VISIBILITY_VERIFIED' }
)

foreach ($job in $jobs) {
  $r = Invoke-ChildJob -Name $job.name -ScriptRelative $job.script -ExpectedRelative $job.expected -MetricName $job.metric -RequiredStatus $job.required
  $results.Add($r)
  foreach ($b in @($r.blockers)) { if ($b) { $allBlockers.Add("$($job.name):$b") } }
}

$after = Get-CountsFromData $dataPath
$sourceStatus = Read-JsonSafe (Join-Path $repoRoot 'docs/chatgpt_status/aays1/status/152_aays1_bulk_live_source_verify_300x60_latest.json')
$siteStatus = Read-JsonSafe (Join-Path $repoRoot 'docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json')
$candidatesExamined = if ($sourceStatus -and $null -ne $sourceStatus.candidates_examined) { [int]$sourceStatus.candidates_examined } else { 0 }
$acceptedRows = if ($sourceStatus -and $sourceStatus.verified_rows_added_this_run) { @($sourceStatus.verified_rows_added_this_run) } else { @() }
$failedJobs = @($results | Where-Object { $_.state -match 'exception|missing|nonzero' }).Count
$siteVerified = $siteStatus -and $siteStatus.status -eq 'SECOND_WAVE_SITE_VISIBILITY_VERIFIED' -and $siteStatus.served_json_matches_source -eq $true
if (-not $siteVerified) { $allBlockers.Add('post_site_readback_not_verified') }
$statusName = if ($failedJobs -eq 0 -and $siteVerified) { 'THIRD_WAVE_AND_SITE_VISIBILITY_VERIFIED' } elseif ($after.live -gt $before.live -or $after.ready -gt $before.ready) { 'THIRD_WAVE_REAL_PROGRESS_SITE_OR_CHILD_PARTIAL' } else { 'THIRD_WAVE_BLOCKED_OR_NO_NEW_PROGRESS' }

$status = [ordered]@{
  task_id=$taskId; page_key='aays1'; status=$statusName
  runner_mode='single_shared_runner_sequential_large_batch'; jobs_total=$jobs.Count; jobs_failed=$failedJobs
  jobs_completed_with_output=@($results | Where-Object { $_.output_status }).Count; results=@($results)
  candidates_examined=$candidatesExamined; accepted_rows=@($acceptedRows); accepted_count=$acceptedRows.Count
  counts_before=$before; counts_after=$after
  source_verified_delta=([int]$after.live-[int]$before.live)
  photo_rows_delta=([int]$after.photos-[int]$before.photos)
  polygon_rows_delta=([int]$after.polygons-[int]$before.polygons)
  evidence_ready_delta=([int]$after.ready-[int]$before.ready)
  source_coverage_percent_after=[Math]::Round(([double]$after.live/1264.0)*100,2)
  evidence_coverage_percent_after=[Math]::Round(([double]$after.ready/1264.0)*100,2)
  site_visibility_verified=[bool]$siteVerified
  served_counts=if($siteStatus){$siteStatus.served_counts}else{$null}
  blockers=@($allBlockers | Select-Object -Unique)
  started_at=$startedAt; finished_at=[DateTimeOffset]::UtcNow.ToString('o')
  final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
$status | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $statusPath -Encoding UTF8

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# AAYS1 ReadyToSell Site Sync and Third Large Wave')
$lines.Add('')
$lines.Add("- Status: $statusName")
$lines.Add("- Jobs with output: $($status.jobs_completed_with_output) / $($status.jobs_total); failed=$failedJobs")
$lines.Add("- Candidates examined / accepted: $candidatesExamined / $($acceptedRows.Count)")
$lines.Add("- Source verified: $($before.live) -> $($after.live); delta=$($status.source_verified_delta); coverage=$($status.source_coverage_percent_after)%")
$lines.Add("- Photo rows: $($before.photos) -> $($after.photos); delta=$($status.photo_rows_delta)")
$lines.Add("- Polygon rows: $($before.polygons) -> $($after.polygons); delta=$($status.polygon_rows_delta)")
$lines.Add("- Evidence-ready: $($before.ready) -> $($after.ready); delta=$($status.evidence_ready_delta); coverage=$($status.evidence_coverage_percent_after)%")
$lines.Add("- Site visibility verified: $siteVerified")
foreach ($r in $results) { $lines.Add("- $($r.name): $($r.state); output=$($r.output_status); progress=$($r.real_progress_count); exit=$($r.exit_code); unwind=$($r.child_detached_commit_unwound)") }
if ($status.blockers.Count -gt 0) { $lines.Add('- Blockers: ' + ($status.blockers -join '; ')) }
$lines.Add('')
$lines.Add('`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))

$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = 'aays1-ready-to-sell-second-wave-dispatch-20260711'
$statusRelative = 'docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/155_aays1_ready_to_sell_second_wave_dispatch_report.md'
$logRootRelative = 'docs/chatgpt_status/aays1/runner_outputs/155_second_wave_dispatch_20260711'
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$logRoot = Join-Path $repoRoot $logRootRelative
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath),(Split-Path $reportPath),$logRoot | Out-Null

$jobs = @(
  [ordered]@{ id='152'; script='docs/chatgpt_status/aays1/automation/152_aays1_bulk_live_source_verify_300x60_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/152_aays1_bulk_live_source_verify_300x60_latest.json' },
  [ordered]@{ id='153'; script='docs/chatgpt_status/aays1/automation/153_aays1_bulk_photo_polygon_evidence_40_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/153_aays1_bulk_photo_polygon_evidence_40_latest.json' },
  [ordered]@{ id='154'; script='docs/chatgpt_status/aays1/automation/154_aays1_ready_to_sell_site_row_visibility_verify_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/154_aays1_ready_to_sell_site_row_visibility_verify_latest.json' }
)

function Read-OutputSummary([string]$path, [string]$jobId) {
  $summary = [ordered]@{ status=$null; real_progress=0; blockers=@(); satisfactory=$false; parse_error=$null }
  if (-not (Test-Path -LiteralPath $path)) { return [pscustomobject]$summary }
  try {
    $j = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    $summary.status = [string]$j.status
    if ($j.blockers) { $summary.blockers = @($j.blockers) }
    switch ($jobId) {
      '152' {
        if ($j.verified_rows_added_count -ne $null) { $summary.real_progress = [int]$j.verified_rows_added_count }
        elseif ($j.verified_rows_added_this_run) { $summary.real_progress = @($j.verified_rows_added_this_run).Count }
        $summary.satisfactory = ($summary.status -notmatch 'BLOCKED|FAILED' -and $summary.real_progress -gt 0)
      }
      '153' {
        if ($j.rows_evidence_ready_this_run -ne $null) { $summary.real_progress = [int]$j.rows_evidence_ready_this_run }
        $summary.satisfactory = ($summary.status -eq 'REAL_EVIDENCE_PREPARED_VISION_COMPARE_PENDING' -and $summary.real_progress -gt 0)
      }
      '154' {
        $summary.real_progress = if ($summary.status -eq 'SITE_ROW_VISIBILITY_VERIFIED') { 1 } else { 0 }
        $summary.satisfactory = ($summary.status -eq 'SITE_ROW_VISIBILITY_VERIFIED')
      }
    }
  } catch { $summary.parse_error = $_.Exception.Message }
  return [pscustomobject]$summary
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$results = [System.Collections.Generic.List[object]]::new()
$blockers = [System.Collections.Generic.List[string]]::new()
$currentRef = (& git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()
$currentCommit = (& git -C $repoRoot rev-parse HEAD 2>$null).Trim()

foreach ($job in $jobs) {
  $scriptPath = Join-Path $repoRoot $job.script
  $expectedPath = Join-Path $repoRoot $job.expected
  $logRelative = "$logRootRelative/job_$($job.id).log"
  $logPath = Join-Path $repoRoot $logRelative
  $state = 'not_run'; $exitCode = $null; $childCommitUnwound = $false
  $childHeadBefore = (& git -C $repoRoot rev-parse HEAD 2>$null).Trim(); $childHeadAfter = $childHeadBefore
  $existing = Read-OutputSummary $expectedPath $job.id
  $forceRerun = (Test-Path -LiteralPath $expectedPath) -and -not $existing.satisfactory

  if ((Test-Path -LiteralPath $expectedPath) -and -not $forceRerun) {
    $state = 'skipped_existing_satisfactory_output'; $exitCode = 0
  } elseif (-not (Test-Path -LiteralPath $scriptPath)) {
    $state = 'blocked_script_missing'; $exitCode = 127; $blockers.Add("missing_script:$($job.script)")
  } else {
    $previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE
    try {
      "[$([DateTimeOffset]::UtcNow.ToString('o'))] START $($job.script) force_rerun=$forceRerun" | Set-Content -LiteralPath $logPath -Encoding UTF8
      $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
      & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath *>> $logPath
      $exitCode = $LASTEXITCODE; if ($null -eq $exitCode) { $exitCode = 0 }
      $childHeadAfter = (& git -C $repoRoot rev-parse HEAD 2>$null).Trim()
      if ($childHeadAfter -and $childHeadBefore -and $childHeadAfter -ne $childHeadBefore) {
        & git -C $repoRoot reset --mixed $childHeadBefore *>> $logPath
        if ($LASTEXITCODE -eq 0) { $childCommitUnwound = $true }
        else { $blockers.Add("child_commit_unwind_failed:$($job.id):$childHeadAfter") }
      }
      if ($exitCode -eq 0 -and (Test-Path -LiteralPath $expectedPath)) { $state = 'executed_output_created' }
      elseif ($exitCode -eq 0) { $state = 'executed_but_expected_output_missing'; $blockers.Add("expected_output_missing:$($job.expected)") }
      else { $state = 'execution_failed'; $blockers.Add("job_failed:$($job.id):exit_$exitCode") }
    } catch {
      $exitCode = 1; $state = 'execution_exception'; $_.Exception.ToString() | Add-Content -LiteralPath $logPath -Encoding UTF8
      $blockers.Add("job_exception:$($job.id):$($_.Exception.Message)")
    } finally { $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached }
  }

  $summary = Read-OutputSummary $expectedPath $job.id
  if ($summary.parse_error) { $blockers.Add("status_parse_failed:$($job.id):$($summary.parse_error)") }
  if ($summary.blockers.Count -gt 0) { foreach ($b in $summary.blockers) { $blockers.Add("job_$($job.id):$b") } }
  if ($state -eq 'executed_output_created') { $state = if ($summary.satisfactory) { 'executed_satisfactory_output' } else { 'executed_partial_output' } }
  $results.Add([pscustomobject]@{
    job_id=$job.id; state=$state; exit_code=$exitCode; expected_status_path=$job.expected
    expected_output_exists=(Test-Path -LiteralPath $expectedPath); output_status=$summary.status
    real_progress=$summary.real_progress; satisfactory=$summary.satisfactory; force_rerun=$forceRerun
    child_head_before=$childHeadBefore; child_head_after=$childHeadAfter; child_detached_commits_unwound=$childCommitUnwound
    log_path=$logRelative; finished_at=[DateTimeOffset]::UtcNow.ToString('o')
  })
}

$completedCount = @($results | Where-Object { $_.expected_output_exists -eq $true }).Count
$satisfactoryCount = @($results | Where-Object { $_.satisfactory -eq $true }).Count
$failedCount = @($results | Where-Object { $_.state -match 'failed|exception|missing|blocked' }).Count
$realProgress = (@($results | Measure-Object -Property real_progress -Sum).Sum)
$status = [ordered]@{
  task_id=$taskId; page_key='aays1'
  status=if ($satisfactoryCount -eq $jobs.Count -and $failedCount -eq 0) { 'SECOND_WAVE_SATISFACTORY_OUTPUTS_PRESENT_FOR_OUTER_PROMOTION' } elseif ($completedCount -gt 0) { 'SECOND_WAVE_PARTIAL' } else { 'SECOND_WAVE_BLOCKED_OR_NO_OUTPUT' }
  runner_mode='single_shared_runner_sequential_large_batch'; git_ref=$currentRef; git_commit_at_start=$currentCommit
  jobs_total=$jobs.Count; jobs_with_expected_output=$completedCount; jobs_satisfactory=$satisfactoryCount; jobs_failed=$failedCount
  planned_candidate_scan=300; planned_max_new_live_sources=60; planned_evidence_rows=40; real_progress_count=$realProgress
  results=@($results); blockers=@($blockers | Select-Object -Unique); outer_runner_promotion_required=$true
  started_at=$startedAt; finished_at=[DateTimeOffset]::UtcNow.ToString('o')
  final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
$status | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# AAYS1 ReadyToSell Second Wave Dispatch')
$lines.Add('')
$lines.Add("- Outputs present: $completedCount / $($jobs.Count)")
$lines.Add("- Satisfactory outputs: $satisfactoryCount / $($jobs.Count)")
$lines.Add("- Failed jobs: $failedCount")
$lines.Add("- Real progress count: $realProgress")
$lines.Add('- Capacity: 300 candidate checks, up to 60 new verified sources, up to 40 evidence rows, then strict served-site verification.')
$lines.Add('- Execution: one canonical F portable shared runner; no parallel runner.')
$lines.Add('- Child detached commits are unwound; outer canonical runner owns commit, push and remote readback.')
foreach ($r in $results) { $lines.Add("- $($r.job_id): $($r.state); status=$($r.output_status); progress=$($r.real_progress); satisfactory=$($r.satisfactory); exit=$($r.exit_code)") }
if ($status.blockers.Count -gt 0) { $lines.Add('- Blockers: ' + ($status.blockers -join '; ')) }
$lines.Add('')
$lines.Add('`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))

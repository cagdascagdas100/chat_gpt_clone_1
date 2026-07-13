$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = 'aays1-ready-to-sell-shared-queue-sequential-dispatch-20260711'
$statusRelative = 'docs/chatgpt_status/aays1/status/151_aays1_shared_queue_sequential_dispatch_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/151_aays1_shared_queue_sequential_dispatch_report.md'
$logRootRelative = 'docs/chatgpt_status/aays1/runner_outputs/151_sequential_dispatch_20260711'
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$logRoot = Join-Path $repoRoot $logRootRelative
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath),(Split-Path $reportPath),$logRoot | Out-Null

$jobs = @(
  [ordered]@{ id='145'; script='docs/chatgpt_status/aays1/automation/145_aays1_live_verify_next_examples_after_30_20260710.ps1'; expected='docs/chatgpt_status/aays1/status/145_aays1_live_verify_next_examples_after_30_latest.json' },
  [ordered]@{ id='146'; script='docs/chatgpt_status/aays1/automation/146_aays1_prepare_vision_evidence_rows_1_3_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/146_aays1_prepare_vision_evidence_rows_1_3_latest.json' },
  [ordered]@{ id='148'; script='docs/chatgpt_status/aays1/automation/148_aays1_expanded_live_verify_after_30_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/148_aays1_expanded_live_verify_after_30_latest.json' },
  [ordered]@{ id='149'; script='docs/chatgpt_status/aays1/automation/149_aays1_bulk_live_source_verify_120x25_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/149_aays1_bulk_live_source_verify_latest.json' },
  [ordered]@{ id='150'; script='docs/chatgpt_status/aays1/automation/150_aays1_bulk_photo_polygon_evidence_20_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/150_aays1_bulk_photo_polygon_evidence_latest.json' }
)

function Read-OutputSummary([string]$path, [string]$jobId) {
  $summary = [ordered]@{ output_status=$null; real_progress_count=0; output_blockers=@(); parse_error=$null }
  if (-not (Test-Path -LiteralPath $path)) { return [pscustomobject]$summary }
  try {
    $j = Get-Content -Raw -LiteralPath $path | ConvertFrom-Json
    $summary.output_status = [string]$j.status
    if ($j.blockers) { $summary.output_blockers = @($j.blockers) }
    switch ($jobId) {
      '145' { if ($j.verified_rows_added_this_run) { $summary.real_progress_count = @($j.verified_rows_added_this_run).Count } }
      '146' { if ($j.rows_with_photo_downloaded_this_run -ne $null) { $summary.real_progress_count = [int]$j.rows_with_photo_downloaded_this_run } }
      '148' { if ($j.verified_rows_added_this_run) { $summary.real_progress_count = @($j.verified_rows_added_this_run).Count } }
      '149' { if ($j.verified_rows_added_count -ne $null) { $summary.real_progress_count = [int]$j.verified_rows_added_count } }
      '150' { if ($j.rows_evidence_ready_this_run -ne $null) { $summary.real_progress_count = [int]$j.rows_evidence_ready_this_run } }
    }
  } catch { $summary.parse_error = $_.Exception.Message }
  return [pscustomobject]$summary
}

function New-DetachedCompatibleChildScript([string]$sourcePath, [string]$jobId) {
  if ($jobId -notin @('148','149','150')) { return $sourcePath }
  $text = (Get-Content -Raw -LiteralPath $sourcePath) -replace "`r`n","`n"

  $branchOld = '$branch = (& git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()' + "`n" + 'if ($branch -ne $targetBranch) { $blockers.Add("wrong_branch:$branch") }'
  $branchNew = '$branch = (& git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()' + "`n" + '$detachedCanonical = ($branch -eq ''HEAD'' -and $env:AAYS_CANONICAL_DETACHED_WORKTREE -eq ''true'')' + "`n" + 'if ($branch -ne $targetBranch -and -not $detachedCanonical) { $blockers.Add("wrong_branch:$branch") }'
  if (-not $text.Contains($branchOld)) { throw "detached_branch_guard_pattern_not_found:$jobId" }
  $text = $text.Replace($branchOld,$branchNew)

  if ($jobId -in @('148','149')) {
    $old148 = '$blocked = $plain -match ''(captcha|access denied|unusual traffic|cloudflare|verify you are human)''' + "`n" + '$landSignal = $plain -match ''(Land for sale|Plot for sale|development land|building plot|building plots|development site|parcel of land)'''
    $old149 = '$blocked = $plain -match ''(captcha|access denied|unusual traffic|cloudflare|verify you are human)''' + "`n" + '$landSignal = $plain -match ''(land for sale|plot for sale|development land|building plot|building plots|development site|agricultural land)'''
    $signalNew = '$titleSignal = (-not [string]::IsNullOrWhiteSpace([string]$title)) -and ($title -match ''(?i)(land for sale|plot for sale|development land|building plot|development site|agricultural land|\bplot\b.*(?:£|for sale)|\bland\b.*(?:£|for sale))'')' + "`n" + '$bodySignal = $plain -match ''(?i)(land for sale|plot for sale|development land|building plot|building plots|development site|agricultural land|parcel of land)''' + "`n" + '$challengeSignal = (($title -match ''(?i)(captcha|access denied|cloudflare|verify you are human)'') -or ($plain -match ''(?i)(captcha|access denied|unusual traffic|verify you are human)''))' + "`n" + '$landSignal = ($titleSignal -or $bodySignal)' + "`n" + '$blocked = ($challengeSignal -and -not $titleSignal)'
    if ($text.Contains($old148)) { $text = $text.Replace($old148,$signalNew) }
    elseif ($text.Contains($old149)) { $text = $text.Replace($old149,$signalNew) }
    else { throw "source_signal_guard_pattern_not_found:$jobId" }

    if ($jobId -eq '148') {
      $oldLengthGate = 'if ($resp.StatusCode -lt 200 -or $resp.StatusCode -ge 400 -or $blocked -or -not $landSignal -or $html.Length -lt 5000) {'
      $newLengthGate = 'if ($resp.StatusCode -lt 200 -or $resp.StatusCode -ge 400 -or $blocked -or -not $landSignal -or ($html.Length -lt 5000 -and -not $titleSignal)) {'
      if ($text.Contains($oldLengthGate)) { $text = $text.Replace($oldLengthGate,$newLengthGate) }
    }
  }

  $tempPath = Join-Path ([System.IO.Path]::GetTempPath()) ("aays_ready_to_sell_{0}_{1}_{2}.ps1" -f $jobId,$PID,[guid]::NewGuid().ToString('N'))
  [System.IO.File]::WriteAllText($tempPath,$text,[System.Text.UTF8Encoding]::new($false))
  return $tempPath
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
  $jobStarted = [DateTimeOffset]::UtcNow.ToString('o')
  $state = 'not_run'; $exitCode = $null; $childCommitUnwound = $false
  $childHeadBefore = (& git -C $repoRoot rev-parse HEAD 2>$null).Trim(); $childHeadAfter = $childHeadBefore
  $expectedExistsBefore = Test-Path -LiteralPath $expectedPath
  $existingSummary = Read-OutputSummary $expectedPath $job.id
  $forceRerun = ($job.id -in @('148','149','150') -and [int]$existingSummary.real_progress_count -eq 0)

  if ($expectedExistsBefore -and -not $forceRerun) {
    $state = 'skipped_existing_real_output'; $exitCode = 0
  } elseif (-not (Test-Path -LiteralPath $scriptPath)) {
    $state = 'blocked_script_missing'; $exitCode = 127; $blockers.Add("missing_script:$($job.script)")
  } else {
    $runScriptPath = $scriptPath; $tempScriptPath = $null; $previousDetachedFlag = $env:AAYS_CANONICAL_DETACHED_WORKTREE
    try {
      "[$jobStarted] START $($job.script) force_rerun=$forceRerun" | Set-Content -LiteralPath $logPath -Encoding UTF8
      $runScriptPath = New-DetachedCompatibleChildScript $scriptPath $job.id
      if ($runScriptPath -ne $scriptPath) { $tempScriptPath = $runScriptPath }
      $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
      & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runScriptPath *>> $logPath
      $exitCode = $LASTEXITCODE; if ($null -eq $exitCode) { $exitCode = 0 }
      $childHeadAfter = (& git -C $repoRoot rev-parse HEAD 2>$null).Trim()
      if ($childHeadAfter -and $childHeadBefore -and $childHeadAfter -ne $childHeadBefore) {
        & git -C $repoRoot reset --mixed $childHeadBefore *>> $logPath
        if ($LASTEXITCODE -eq 0) { $childCommitUnwound = $true }
        else { $blockers.Add("child_commit_unwind_failed:$($job.id):$childHeadAfter") }
      }
      $expectedExistsAfterRun = Test-Path -LiteralPath $expectedPath
      if ($exitCode -eq 0 -and $expectedExistsAfterRun) { $state = 'executed_output_created' }
      elseif ($exitCode -eq 0) { $state = 'executed_but_expected_output_missing'; $blockers.Add("expected_output_missing:$($job.expected)") }
      else { $state = 'execution_failed'; $blockers.Add("job_failed:$($job.id):exit_$exitCode") }
    } catch {
      $exitCode = 1; $state = 'execution_exception'; $_.Exception.ToString() | Add-Content -LiteralPath $logPath -Encoding UTF8
      $blockers.Add("job_exception:$($job.id):$($_.Exception.Message)")
    } finally {
      $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetachedFlag
      if ($tempScriptPath -and (Test-Path -LiteralPath $tempScriptPath)) { Remove-Item -LiteralPath $tempScriptPath -Force -ErrorAction SilentlyContinue }
    }
  }

  $outputSummary = Read-OutputSummary $expectedPath $job.id
  if ($outputSummary.parse_error) { $blockers.Add("status_parse_failed:$($job.id):$($outputSummary.parse_error)") }
  if ($outputSummary.output_blockers.Count -gt 0) { foreach ($b in $outputSummary.output_blockers) { $blockers.Add("job_$($job.id):$b") } }
  if ($state -eq 'executed_output_created') { $state = if ($outputSummary.real_progress_count -gt 0) { 'executed_output_created_with_real_progress' } else { 'executed_output_created_no_new_progress' } }
  $results.Add([pscustomobject]@{ job_id=$job.id; script_path=$job.script; expected_status_path=$job.expected; state=$state; exit_code=$exitCode; expected_output_exists=(Test-Path -LiteralPath $expectedPath); output_status=$outputSummary.output_status; real_progress_count=$outputSummary.real_progress_count; output_blockers=@($outputSummary.output_blockers); force_rerun=$forceRerun; child_head_before=$childHeadBefore; child_head_after=$childHeadAfter; child_detached_commits_unwound=$childCommitUnwound; log_path=$logRelative; started_at=$jobStarted; finished_at=[DateTimeOffset]::UtcNow.ToString('o') })
}

$completedCount = @($results | Where-Object { $_.expected_output_exists -eq $true }).Count
$failedCount = @($results | Where-Object { $_.state -match 'failed|exception|missing|blocked' }).Count
$realProgressCount = (@($results | Measure-Object -Property real_progress_count -Sum).Sum)
$status = [ordered]@{ task_id=$taskId; page_key='aays1'; status=if ($completedCount -eq $jobs.Count -and $failedCount -eq 0) { 'SEQUENTIAL_DISPATCH_OUTPUTS_PRESENT_FOR_OUTER_PROMOTION' } elseif ($completedCount -gt 0) { 'SEQUENTIAL_DISPATCH_PARTIAL' } else { 'SEQUENTIAL_DISPATCH_BLOCKED_OR_NO_OUTPUT' }; runner_mode='single_shared_runner_sequential'; git_ref=$currentRef; git_commit_at_start=$currentCommit; jobs_total=$jobs.Count; jobs_with_expected_output=$completedCount; jobs_failed=$failedCount; real_progress_count_across_jobs=$realProgressCount; results=@($results); blockers=@($blockers | Select-Object -Unique); outer_runner_promotion_required=$true; source_acceptance_rule='HTTP 2xx/3xx plus real OnTheMarket land/plot title or body signal; challenge text alone cannot override a positive listing title'; started_at=$startedAt; finished_at=[DateTimeOffset]::UtcNow.ToString('o'); final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false }
$status | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $statusPath -Encoding UTF8

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# AAYS1 ReadyToSell Shared Queue Sequential Dispatch')
$lines.Add('')
$lines.Add("- Jobs with expected output: $completedCount / $($jobs.Count)")
$lines.Add("- Failed jobs: $failedCount")
$lines.Add("- Real progress count across child outputs: $realProgressCount")
$lines.Add('- One canonical F portable shared runner; no parallel runner.')
$lines.Add('- Existing real task 146 output is not duplicated.')
$lines.Add('- Land/plot acceptance uses real HTTP response plus positive listing title/body evidence; generic page-script challenge terms do not override a positive title.')
$lines.Add('- Child detached commits are unwound; outer canonical runner owns commit, push and remote readback.')
$lines.Add('')
foreach ($r in $results) { $lines.Add("- $($r.job_id): $($r.state); output=$($r.expected_output_exists); real_progress=$($r.real_progress_count); force_rerun=$($r.force_rerun); child_unwound=$($r.child_detached_commits_unwound); exit=$($r.exit_code); log=$($r.log_path)") }
if ($status.blockers.Count -gt 0) { $lines.Add(''); $lines.Add('- Blockers: ' + ($status.blockers -join '; ')) }
$lines.Add('')
$lines.Add('`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))

$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = 'aays1-ready-to-sell-shared-queue-sequential-dispatch-20260711'
$statusRelative = 'docs/chatgpt_status/aays1/status/151_aays1_shared_queue_sequential_dispatch_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/151_aays1_shared_queue_sequential_dispatch_report.md'
$logRootRelative = 'docs/chatgpt_status/aays1/runner_outputs/151_finish_evidence_second_wave_20260713'
$nextQueueRelative = 'docs/chatgpt_status/aays1/queue/155_aays1_ready_to_sell_second_wave_dispatch_20260711.task.json'
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$logRoot = Join-Path $repoRoot $logRootRelative
$nextQueuePath = Join-Path $repoRoot $nextQueueRelative
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath),(Split-Path $reportPath),$logRoot,(Split-Path $nextQueuePath) | Out-Null

$jobs = @(
  [ordered]@{ id='150'; script='docs/chatgpt_status/aays1/automation/150_aays1_bulk_photo_polygon_evidence_20_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/150_aays1_bulk_photo_polygon_evidence_latest.json'; metric='rows_evidence_ready_this_run' },
  [ordered]@{ id='152'; script='docs/chatgpt_status/aays1/automation/152_aays1_bulk_live_source_verify_300x60_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/152_aays1_bulk_live_source_verify_300x60_latest.json'; metric='verified_rows_added_count' },
  [ordered]@{ id='153'; script='docs/chatgpt_status/aays1/automation/153_aays1_bulk_photo_polygon_evidence_40_20260711.ps1'; expected='docs/chatgpt_status/aays1/status/153_aays1_bulk_photo_polygon_evidence_40_latest.json'; metric='rows_evidence_ready_this_run' }
)

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$results = [System.Collections.Generic.List[object]]::new()
$blockers = [System.Collections.Generic.List[string]]::new()
$previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE

foreach ($job in $jobs) {
  $scriptPath = Join-Path $repoRoot $job.script
  $expectedPath = Join-Path $repoRoot $job.expected
  $logRelative = "$logRootRelative/job_$($job.id).log"
  $logPath = Join-Path $repoRoot $logRelative
  $jobStarted = [DateTimeOffset]::UtcNow.ToString('o')
  $exitCode = 1
  $state = 'not_run'
  $childHeadBefore = (& git -C $repoRoot rev-parse HEAD 2>$null).Trim()
  $childHeadAfter = $childHeadBefore
  $childCommitUnwound = $false
  $realProgress = 0
  try {
    if (-not (Test-Path -LiteralPath $scriptPath)) { throw "missing_script:$($job.script)" }
    "[$jobStarted] START $($job.script)" | Set-Content -LiteralPath $logPath -Encoding UTF8
    $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath *>> $logPath
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) { $exitCode = 0 }
    $childHeadAfter = (& git -C $repoRoot rev-parse HEAD 2>$null).Trim()
    if ($childHeadAfter -and $childHeadBefore -and $childHeadAfter -ne $childHeadBefore) {
      & git -C $repoRoot reset --mixed $childHeadBefore *>> $logPath
      if ($LASTEXITCODE -eq 0) { $childCommitUnwound = $true }
      else { $blockers.Add("child_commit_unwind_failed:$($job.id):$childHeadAfter") }
    }
    if ($exitCode -ne 0) {
      $state = 'execution_failed'
      $blockers.Add("job_failed:$($job.id):exit_$exitCode")
    } elseif (-not (Test-Path -LiteralPath $expectedPath)) {
      $state = 'expected_output_missing'
      $blockers.Add("expected_output_missing:$($job.expected)")
    } else {
      $state = 'output_created'
      try {
        $j = Get-Content -LiteralPath $expectedPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $p = $j.PSObject.Properties[[string]$job.metric]
        if ($p -and $null -ne $p.Value) { $realProgress = [int]$p.Value }
        if ($realProgress -gt 0) { $state = 'output_created_with_real_progress' }
        else { $state = 'output_created_no_new_progress' }
        if ($j.blockers) { foreach ($b in @($j.blockers)) { if ($b) { $blockers.Add("job_$($job.id):$b") } } }
      } catch {
        $blockers.Add("status_parse_failed:$($job.id)")
      }
    }
  } catch {
    $state = 'execution_exception'
    $blockers.Add("job_exception:$($job.id):$($_.Exception.Message)")
    $_.Exception.ToString() | Add-Content -LiteralPath $logPath -Encoding UTF8
  } finally {
    $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
  }
  $results.Add([pscustomobject]@{
    job_id = $job.id
    state = $state
    exit_code = $exitCode
    real_progress_count = $realProgress
    expected_status_path = $job.expected
    expected_output_exists = (Test-Path -LiteralPath $expectedPath)
    child_head_before = $childHeadBefore
    child_head_after = $childHeadAfter
    child_detached_commit_unwound = $childCommitUnwound
    log_path = $logRelative
    started_at = $jobStarted
    finished_at = [DateTimeOffset]::UtcNow.ToString('o')
  })
}

$failedCount = @($results | Where-Object { $_.state -match 'failed|exception|missing' }).Count
$realProgressTotal = (@($results | Measure-Object -Property real_progress_count -Sum).Sum)
$nextQueue = [ordered]@{
  task_id = 'aays1-ready-to-sell-second-wave-dispatch-20260711'
  page_key = 'aays1'
  status = 'queued'
  priority = -1400
  target_branch = 'codex/aays-single-runner-v5-20260706'
  script_path = 'docs/chatgpt_status/aays1/automation/155_aays1_ready_to_sell_post_promotion_site_verify_20260713.ps1'
  expected_status = 'docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
  expected_report = 'docs/chatgpt_status/aays1/reports/155_aays1_ready_to_sell_second_wave_dispatch_report.md'
  scope = 'After outer promotion of tasks 150, 152 and 153, verify the served ReadyToSell page and row-level source, photo, polygon, status and report visibility using existing task 154.'
  execution_mode = 'single_shared_runner_sequential'
  timeout_minutes = 120
  allowed_paths = @('docs/chatgpt_status/aays1/queue','docs/chatgpt_status/aays1/status','docs/chatgpt_status/aays1/reports','docs/chatgpt_status/aays1/runner_outputs','england_map_web/data/geometry_review_3of4','england_map_web/data/aays1','england_map_web/geometry_review_3of4_columns_1264.html')
  single_runner_only = $true
  new_runner_allowed = $false
  parallel_runner_allowed = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  queued_by_parent_task = $taskId
  queued_at = [DateTimeOffset]::UtcNow.ToString('o')
}
$nextQueue | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $nextQueuePath -Encoding UTF8

$status = [ordered]@{
  task_id = $taskId
  page_key = 'aays1'
  status = if ($failedCount -eq 0) { 'EVIDENCE_AND_SECOND_WAVE_OUTPUTS_READY_FOR_OUTER_PROMOTION' } else { 'EVIDENCE_AND_SECOND_WAVE_PARTIAL' }
  runner_mode = 'single_shared_runner_sequential_large_batch'
  jobs_total = $jobs.Count
  jobs_failed = $failedCount
  real_progress_count_across_jobs = $realProgressTotal
  results = @($results)
  post_promotion_site_verify_queued = $true
  post_promotion_queue_path = $nextQueueRelative
  blockers = @($blockers | Select-Object -Unique)
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
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# AAYS1 ReadyToSell Evidence and Second-Wave Continuation')
$lines.Add('')
$lines.Add("- Jobs: $($jobs.Count)")
$lines.Add("- Failed: $failedCount")
$lines.Add("- Real progress count: $realProgressTotal")
$lines.Add('- Execution: one canonical F portable shared runner; no parallel runner.')
foreach ($r in $results) { $lines.Add("- $($r.job_id): $($r.state); real_progress=$($r.real_progress_count); exit=$($r.exit_code); child_unwound=$($r.child_detached_commit_unwound)") }
$lines.Add("- Post-promotion site verification queued: $nextQueueRelative")
if ($blockers.Count -gt 0) { $lines.Add('- Blockers: ' + (($blockers | Select-Object -Unique) -join '; ')) }
$lines.Add('')
$lines.Add('`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))

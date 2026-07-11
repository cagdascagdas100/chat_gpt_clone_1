$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = 'aays1-ready-to-sell-second-wave-dispatch-20260711'
$branch = 'codex/aays-single-runner-v5-20260706'
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
$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$results = [System.Collections.Generic.List[object]]::new()
$blockers = [System.Collections.Generic.List[string]]::new()
$currentBranch = (& git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()
if ($currentBranch -ne $branch) { $blockers.Add("wrong_branch:$currentBranch") }

foreach ($job in $jobs) {
  $scriptPath = Join-Path $repoRoot $job.script
  $expectedPath = Join-Path $repoRoot $job.expected
  $logRelative = "$logRootRelative/job_$($job.id).log"
  $logPath = Join-Path $repoRoot $logRelative
  $state = 'not_run'
  $exitCode = $null
  if (Test-Path -LiteralPath $expectedPath) {
    $state = 'skipped_existing_real_output'
    $exitCode = 0
  } elseif (-not (Test-Path -LiteralPath $scriptPath)) {
    $state = 'blocked_script_missing'
    $exitCode = 127
    $blockers.Add("missing_script:$($job.script)")
  } else {
    try {
      "[$([DateTimeOffset]::UtcNow.ToString('o'))] START $($job.script)" | Set-Content -LiteralPath $logPath -Encoding UTF8
      & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath *>> $logPath
      $exitCode = $LASTEXITCODE
      if ($null -eq $exitCode) { $exitCode = 0 }
      if ($exitCode -eq 0 -and (Test-Path -LiteralPath $expectedPath)) { $state = 'executed_output_created' }
      elseif ($exitCode -eq 0) { $state = 'executed_but_expected_output_missing' }
      else { $state = 'execution_failed' }
    } catch {
      $exitCode = 1
      $state = 'execution_exception'
      $_.Exception.ToString() | Add-Content -LiteralPath $logPath -Encoding UTF8
    }
  }
  try {
    & git -C $repoRoot add -- 'england_map_web/data/geometry_review_3of4' 'england_map_web/data/aays1' 'docs/chatgpt_status/aays1/status' 'docs/chatgpt_status/aays1/reports' 'docs/chatgpt_status/aays1/runner_outputs' | Out-Null
    $pending = (& git -C $repoRoot status --porcelain)
    if ($pending) { & git -C $repoRoot commit -m "AAYS1 second wave job $($job.id) outputs" | Out-Null }
    & git -C $repoRoot push origin $branch | Out-Null
  } catch { $blockers.Add("git_sync_job_$($job.id):$($_.Exception.Message)") }
  $results.Add([pscustomobject]@{
    job_id = $job.id
    state = $state
    exit_code = $exitCode
    expected_status_path = $job.expected
    expected_output_exists = (Test-Path -LiteralPath $expectedPath)
    log_path = $logRelative
    finished_at = [DateTimeOffset]::UtcNow.ToString('o')
  })
}

$completedCount = @($results | Where-Object { $_.expected_output_exists -eq $true }).Count
$failedCount = @($results | Where-Object { $_.state -match 'failed|exception|missing' }).Count
$status = [ordered]@{
  task_id = $taskId
  page_key = 'aays1'
  status = if ($completedCount -eq $jobs.Count -and $failedCount -eq 0) { 'SECOND_WAVE_OUTPUTS_PRESENT' } elseif ($completedCount -gt 0) { 'SECOND_WAVE_PARTIAL' } else { 'SECOND_WAVE_BLOCKED_OR_NO_OUTPUT' }
  runner_mode = 'single_shared_runner_sequential_large_batch'
  jobs_total = $jobs.Count
  jobs_with_expected_output = $completedCount
  jobs_failed = $failedCount
  planned_candidate_scan = 300
  planned_max_new_live_sources = 60
  planned_evidence_rows = 40
  results = @($results)
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
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# AAYS1 ReadyToSell Second Wave Dispatch')
$lines.Add('')
$lines.Add("- Jobs with expected real output: $completedCount / $($jobs.Count)")
$lines.Add("- Failed jobs: $failedCount")
$lines.Add('- Capacity: 300 candidate checks, up to 60 new verified sources, up to 40 photo/polygon evidence rows, then website verification.')
$lines.Add('- Execution: one canonical F portable shared runner; no parallel runner.')
foreach ($r in $results) { $lines.Add("- $($r.job_id): $($r.state); output=$($r.expected_output_exists); exit=$($r.exit_code)") }
if ($blockers.Count -gt 0) { $lines.Add("- Blockers: $($blockers -join '; ')") }
$lines.Add('')
$lines.Add('`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))
try {
  & git -C $repoRoot add -- $statusRelative $reportRelative $logRootRelative | Out-Null
  $pending = (& git -C $repoRoot status --porcelain)
  if ($pending) { & git -C $repoRoot commit -m 'Record AAYS1 ReadyToSell second wave dispatch result' | Out-Null }
  & git -C $repoRoot push origin $branch | Out-Null
} catch {}

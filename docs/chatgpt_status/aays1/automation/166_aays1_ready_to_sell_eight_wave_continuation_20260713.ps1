$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = 'aays1-ready-to-sell-eight-wave-continuation-20260713'
$childScriptRelative = 'docs/chatgpt_status/aays1/automation/159_aays1_ready_to_sell_four_wave_pickup_recovery_20260713.ps1'
$childStatusRelative = 'docs/chatgpt_status/aays1/status/159_aays1_ready_to_sell_four_wave_pickup_recovery_latest.json'
$dataRelative = 'england_map_web/data/geometry_review_3of4/photo_ai_boundary_review_results.json'
$statusRelative = 'docs/chatgpt_status/aays1/status/166_aays1_ready_to_sell_eight_wave_continuation_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/166_aays1_ready_to_sell_eight_wave_continuation_report.md'
$logRootRelative = 'docs/chatgpt_status/aays1/runner_outputs/166_eight_wave_continuation_20260713'

$childScriptPath = Join-Path $repoRoot $childScriptRelative
$childStatusPath = Join-Path $repoRoot $childStatusRelative
$dataPath = Join-Path $repoRoot $dataRelative
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

function Get-HashSafe([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  try { return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash } catch { return $null }
}

function Get-Counts([string]$path) {
  $data = Read-JsonSafe $path
  $rows = if ($data -and $data.results) { @($data.results) } else { @() }
  return [pscustomobject]@{
    rows = $rows.Count
    live = @($rows | Where-Object { $_.source_verification_status -eq 'verified_live_listing_page' }).Count
    photos = @($rows | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 }).Count
    polygons = @($rows | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
    ready = @($rows | Where-Object { $_.downloaded_photo_paths -and @($_.downloaded_photo_paths).Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$_.polygon_render_path) }).Count
    vision = @($rows | Where-Object { $null -ne $_.visual_match_score }).Count
  }
}

function Get-Prop($obj,[string]$name,$fallback) {
  if ($null -eq $obj) { return $fallback }
  $p = $obj.PSObject.Properties[$name]
  if ($p -and $null -ne $p.Value) { return $p.Value }
  return $fallback
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$countsBefore = Get-Counts $dataPath
$cycleResults = [System.Collections.Generic.List[object]]::new()
$allBlockers = [System.Collections.Generic.List[string]]::new()
$acceptedRowsAll = [System.Collections.Generic.List[object]]::new()
$evidenceRowsAll = [System.Collections.Generic.List[object]]::new()
$totalCandidatesExamined = 0
$previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE

for ($cycle = 1; $cycle -le 2; $cycle++) {
  $cycleStarted = [DateTimeOffset]::UtcNow
  $beforeCounts = Get-Counts $dataPath
  $beforeHash = Get-HashSafe $childStatusPath
  $beforeWrite = if (Test-Path -LiteralPath $childStatusPath) { (Get-Item -LiteralPath $childStatusPath).LastWriteTimeUtc.ToString('o') } else { $null }
  $logRelative = "$logRootRelative/cycle_$cycle.log"
  $logPath = Join-Path $repoRoot $logRelative
  $exitCode = 1
  $state = 'not_run'
  $child = $null
  $fresh = $false
  try {
    if (-not (Test-Path -LiteralPath $childScriptPath)) { throw ('missing_child_script:' + $childScriptRelative) }
    "[$($cycleStarted.ToString('o'))] START cycle=$cycle $childScriptRelative" | Set-Content -LiteralPath $logPath -Encoding UTF8
    $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $childScriptPath *>> $logPath
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) { $exitCode = 0 }
    $afterHash = Get-HashSafe $childStatusPath
    if (Test-Path -LiteralPath $childStatusPath) {
      $item = Get-Item -LiteralPath $childStatusPath
      $fresh = ($item.LastWriteTimeUtc -ge $cycleStarted.UtcDateTime.AddSeconds(-2)) -and $afterHash -and ($afterHash -ne $beforeHash)
    }
    if ($fresh) {
      $child = Read-JsonSafe $childStatusPath
      if ($child) {
        $state = if ($exitCode -eq 0) { 'fresh_output' } else { 'fresh_output_child_nonzero' }
      } else {
        $state = 'fresh_file_parse_failed'
      }
    } else {
      $state = 'child_output_missing_or_stale'
    }
  } catch {
    $state = 'execution_exception'
    $_.Exception.ToString() | Add-Content -LiteralPath $logPath -Encoding UTF8
    $allBlockers.Add("cycle_${cycle}:$($_.Exception.Message)")
  } finally {
    $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
  }

  $afterCounts = Get-Counts $dataPath
  $candidateCount = [int](Get-Prop $child 'candidates_examined' 0)
  $accepted = @((Get-Prop $child 'accepted_rows' @()))
  $evidenceRows = @((Get-Prop $child 'evidence_rows_targeted' @()))
  $totalCandidatesExamined += $candidateCount
  foreach ($row in $accepted) { $acceptedRowsAll.Add($row) }
  foreach ($row in $evidenceRows) { $evidenceRowsAll.Add($row) }
  foreach ($b in @((Get-Prop $child 'blockers' @()))) { if ($b) { $allBlockers.Add("cycle_${cycle}:$b") } }
  if (-not $fresh) { $allBlockers.Add("cycle_${cycle}:child_output_not_fresh") }
  if ($exitCode -ne 0) { $allBlockers.Add("cycle_${cycle}:child_exit_$exitCode") }

  $cycleResults.Add([pscustomobject]@{
    cycle=$cycle; state=$state; exit_code=$exitCode; output_fresh=[bool]$fresh
    child_status=if($child){[string]$child.status}else{$null}
    jobs_total=[int](Get-Prop $child 'jobs_total' 13)
    jobs_completed_with_fresh_output=[int](Get-Prop $child 'jobs_completed_with_fresh_output' 0)
    jobs_failed=[int](Get-Prop $child 'jobs_failed' 0)
    candidates_examined=$candidateCount; accepted_rows=@($accepted); evidence_rows_targeted=@($evidenceRows)
    counts_before=$beforeCounts; counts_after=$afterCounts
    source_delta=([int]$afterCounts.live-[int]$beforeCounts.live)
    photo_delta=([int]$afterCounts.photos-[int]$beforeCounts.photos)
    polygon_delta=([int]$afterCounts.polygons-[int]$beforeCounts.polygons)
    evidence_ready_delta=([int]$afterCounts.ready-[int]$beforeCounts.ready)
    site_visibility_verified=[bool](Get-Prop $child 'site_visibility_verified' $false)
    served_counts=Get-Prop $child 'served_counts' $null
    child_status_write_before=$beforeWrite
    child_status_write_after=if(Test-Path -LiteralPath $childStatusPath){(Get-Item -LiteralPath $childStatusPath).LastWriteTimeUtc.ToString('o')}else{$null}
    log_path=$logRelative
    started_at=$cycleStarted.ToString('o'); finished_at=[DateTimeOffset]::UtcNow.ToString('o')
  })
}

$countsAfter = Get-Counts $dataPath
$acceptedRows = @($acceptedRowsAll | Select-Object -Unique)
$evidenceRows = @($evidenceRowsAll | Select-Object -Unique)
$freshCycles = @($cycleResults | Where-Object { $_.output_fresh }).Count
$failedCycles = @($cycleResults | Where-Object { $_.state -ne 'fresh_output' }).Count
$finalCycle = if ($cycleResults.Count -gt 0) { $cycleResults[$cycleResults.Count-1] } else { $null }
$siteVerified = $finalCycle -and $finalCycle.site_visibility_verified
$statusName = if ($freshCycles -eq 2 -and $failedCycles -eq 0 -and $siteVerified) {
  'EIGHT_WAVES_AND_SITE_VISIBILITY_VERIFIED'
} elseif ($countsAfter.live -gt $countsBefore.live -or $countsAfter.ready -gt $countsBefore.ready) {
  'EIGHT_WAVES_REAL_PROGRESS_SITE_OR_CHILD_PARTIAL'
} else {
  'EIGHT_WAVES_BLOCKED_OR_NO_NEW_PROGRESS'
}

$status = [ordered]@{
  task_id=$taskId; page_key='aays1'; status=$statusName
  runner_mode='single_shared_runner_sequential_eight_waves'; cycles_total=2; cycles_with_fresh_output=$freshCycles; cycles_failed=$failedCycles
  jobs_total=26; jobs_completed_with_fresh_output=[int](($cycleResults | Measure-Object -Property jobs_completed_with_fresh_output -Sum).Sum)
  cycle_results=@($cycleResults)
  planned_candidates=2400; planned_max_new_sources=480; planned_evidence_operations=320; site_checkpoint_count=10
  candidates_examined=$totalCandidatesExamined; accepted_rows=@($acceptedRows); accepted_count=$acceptedRows.Count
  evidence_rows_targeted=@($evidenceRows); evidence_rows_targeted_count=$evidenceRows.Count
  counts_before=$countsBefore; counts_after=$countsAfter
  source_verified_delta=([int]$countsAfter.live-[int]$countsBefore.live)
  photo_rows_delta=([int]$countsAfter.photos-[int]$countsBefore.photos)
  polygon_rows_delta=([int]$countsAfter.polygons-[int]$countsBefore.polygons)
  evidence_ready_delta=([int]$countsAfter.ready-[int]$countsBefore.ready)
  source_coverage_percent_after=[math]::Round(([double]$countsAfter.live/1264.0)*100,2)
  evidence_coverage_percent_after=[math]::Round(([double]$countsAfter.ready/1264.0)*100,2)
  site_visibility_verified=[bool]$siteVerified
  served_counts=if($finalCycle){$finalCycle.served_counts}else{$null}
  blockers=@($allBlockers | Select-Object -Unique)
  started_at=$startedAt; finished_at=[DateTimeOffset]::UtcNow.ToString('o')
  final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
$status | ConvertTo-Json -Depth 80 | Set-Content -LiteralPath $statusPath -Encoding UTF8

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# AAYS1 ReadyToSell Eight-Wave Continuation')
$lines.Add('')
$lines.Add('- Status: ' + $statusName)
$lines.Add(('- Fresh cycles: {0} / 2; failed={1}' -f $freshCycles,$failedCycles))
$lines.Add(('- Jobs with fresh output: {0} / 26' -f $status.jobs_completed_with_fresh_output))
$lines.Add(('- Candidates examined / accepted: {0} / {1}' -f $totalCandidatesExamined,$acceptedRows.Count))
$lines.Add(('- Accepted row IDs: {0}' -f ($acceptedRows -join ', ')))
$lines.Add(('- Source verified: {0} -> {1}; delta={2}; coverage={3}%' -f $countsBefore.live,$countsAfter.live,$status.source_verified_delta,$status.source_coverage_percent_after))
$lines.Add(('- Photo rows: {0} -> {1}; delta={2}' -f $countsBefore.photos,$countsAfter.photos,$status.photo_rows_delta))
$lines.Add(('- Polygon rows: {0} -> {1}; delta={2}' -f $countsBefore.polygons,$countsAfter.polygons,$status.polygon_rows_delta))
$lines.Add(('- Evidence-ready: {0} -> {1}; delta={2}; coverage={3}%' -f $countsBefore.ready,$countsAfter.ready,$status.evidence_ready_delta,$status.evidence_coverage_percent_after))
$lines.Add('- Site visibility verified: ' + $siteVerified)
foreach ($r in $cycleResults) { $lines.Add(('- Cycle {0}: {1}; fresh_jobs={2}/{3}; candidates={4}; accepted={5}; source_delta={6}; evidence_delta={7}; exit={8}' -f $r.cycle,$r.state,$r.jobs_completed_with_fresh_output,$r.jobs_total,$r.candidates_examined,@($r.accepted_rows).Count,$r.source_delta,$r.evidence_ready_delta,$r.exit_code)) }
if ($status.blockers.Count -gt 0) { $lines.Add('- Blockers: ' + ($status.blockers -join '; ')) }
$lines.Add('')
$lines.Add('`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))

if ($freshCycles -eq 0 -and $status.source_verified_delta -eq 0 -and $status.evidence_ready_delta -eq 0) { exit 1 }
exit 0

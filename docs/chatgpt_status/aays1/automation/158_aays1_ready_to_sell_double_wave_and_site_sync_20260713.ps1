$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = 'aays1-ready-to-sell-double-wave-continuation-20260713'
$statusRelative = 'docs/chatgpt_status/aays1/status/158_aays1_ready_to_sell_double_wave_and_site_sync_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/158_aays1_ready_to_sell_double_wave_and_site_sync_report.md'
$logRootRelative = 'docs/chatgpt_status/aays1/runner_outputs/158_double_wave_and_site_sync_20260713'
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

function Get-HashSafe([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return $null }
  try { return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash } catch { return $null }
}

function Get-PropertyValue($object,[string]$name,$fallback) {
  if ($null -eq $object) { return $fallback }
  $p = $object.PSObject.Properties[$name]
  if ($p -and $null -ne $p.Value) { return $p.Value }
  return $fallback
}

function Invoke-BatchJob {
  param(
    [string]$Name,
    [string]$ScriptRelative,
    [string]$ExpectedRelative,
    [string]$RequiredStatus,
    [string]$Kind
  )
  $dataPath = Join-Path $repoRoot $dataRelative
  $before = Get-Counts $dataPath
  $scriptPath = Join-Path $repoRoot $ScriptRelative
  $expectedPath = Join-Path $repoRoot $ExpectedRelative
  $beforeOutputHash = Get-HashSafe $expectedPath
  $logRelative = "$logRootRelative/$Name.log"
  $logPath = Join-Path $repoRoot $logRelative
  $started = [DateTimeOffset]::UtcNow.ToString('o')
  $headBefore = (& git -C $repoRoot rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
  $headAfter = $headBefore
  $unwound = $false
  $exitCode = 1
  $outputStatus = $null
  $state = 'not_run'
  $jobBlockers = [System.Collections.Generic.List[string]]::new()
  $candidatesExamined = 0
  $acceptedRows = @()
  $evidenceRows = @()
  $evidenceReadyThisRun = 0
  $previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE
  try {
    if (-not (Test-Path -LiteralPath $scriptPath)) { throw ('missing_script:' + $ScriptRelative) }
    "[$started] START $ScriptRelative" | Set-Content -LiteralPath $logPath -Encoding UTF8
    $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scriptPath *>> $logPath
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) { $exitCode = 0 }
    $headAfter = (& git -C $repoRoot rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
    if ($headBefore -and $headAfter -and $headAfter -ne $headBefore) {
      & git -C $repoRoot reset --mixed $headBefore *>> $logPath
      if ($LASTEXITCODE -eq 0) { $unwound = $true } else { $jobBlockers.Add('child_commit_unwind_failed:' + $Name) }
    }
    $afterOutputHash = Get-HashSafe $expectedPath
    $outputFresh = $afterOutputHash -and ($afterOutputHash -ne $beforeOutputHash)
    $output = Read-JsonSafe $expectedPath
    if ($output -and $outputFresh) {
      $outputStatus = [string]$output.status
      if ($output.blockers) { foreach ($b in @($output.blockers)) { if ($b) { $jobBlockers.Add([string]$b) } } }
      $candidatesExamined = [int](Get-PropertyValue $output 'candidates_examined' 0)
      $acceptedRows = @((Get-PropertyValue $output 'verified_rows_added_this_run' @()))
      $evidenceRows = @((Get-PropertyValue $output 'rows_targeted' @()))
      $evidenceReadyThisRun = [int](Get-PropertyValue $output 'rows_evidence_ready_this_run' 0)
      if ($RequiredStatus -and $outputStatus -ne $RequiredStatus) {
        $state = 'output_created_status_partial'
        $jobBlockers.Add(('required_status_not_met:{0}:{1}' -f $RequiredStatus,$outputStatus))
      } elseif ($exitCode -eq 0) {
        $state = 'output_created'
      } else {
        $state = 'output_created_child_nonzero'
        $jobBlockers.Add('child_exit_nonzero:' + $exitCode)
      }
    } elseif ($output -and -not $outputFresh) {
      $state = 'expected_output_stale'
      $jobBlockers.Add('expected_output_not_refreshed:' + $ExpectedRelative)
    } else {
      $state = 'expected_output_missing'
      $jobBlockers.Add('expected_output_missing:' + $ExpectedRelative)
    }
  } catch {
    $state = 'execution_exception'
    $jobBlockers.Add($_.Exception.Message)
    $_.Exception.ToString() | Add-Content -LiteralPath $logPath -Encoding UTF8
  } finally {
    $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
  }
  $after = Get-Counts $dataPath
  return [pscustomobject]@{
    name=$Name; kind=$Kind; script_path=$ScriptRelative; expected_status_path=$ExpectedRelative
    state=$state; exit_code=$exitCode; output_status=$outputStatus; output_fresh=[bool]$outputFresh
    candidates_examined=$candidatesExamined; accepted_rows=@($acceptedRows)
    evidence_rows=@($evidenceRows); evidence_ready_this_run=$evidenceReadyThisRun
    source_delta=([int]$after.live-[int]$before.live)
    photo_delta=([int]$after.photos-[int]$before.photos)
    polygon_delta=([int]$after.polygons-[int]$before.polygons)
    evidence_ready_delta=([int]$after.ready-[int]$before.ready)
    counts_before=$before; counts_after=$after
    child_head_before=$headBefore; child_head_after=$headAfter; child_detached_commit_unwound=$unwound
    blockers=@($jobBlockers | Select-Object -Unique); log_path=$logRelative
    started_at=$started; finished_at=[DateTimeOffset]::UtcNow.ToString('o')
  }
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$dataPath = Join-Path $repoRoot $dataRelative
$beforeAll = Get-Counts $dataPath
$results = [System.Collections.Generic.List[object]]::new()
$allBlockers = [System.Collections.Generic.List[string]]::new()

$siteScript = 'docs/chatgpt_status/aays1/automation/155_aays1_ready_to_sell_post_promotion_site_verify_20260713.ps1'
$siteExpected = 'docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
$sourceScript = 'docs/chatgpt_status/aays1/automation/152_aays1_bulk_live_source_verify_300x60_20260711.ps1'
$sourceExpected = 'docs/chatgpt_status/aays1/status/152_aays1_bulk_live_source_verify_300x60_latest.json'
$evidenceScript = 'docs/chatgpt_status/aays1/automation/153_aays1_bulk_photo_polygon_evidence_40_20260711.ps1'
$evidenceExpected = 'docs/chatgpt_status/aays1/status/153_aays1_bulk_photo_polygon_evidence_40_latest.json'

$jobs = @(
  [pscustomobject]@{ name='pre_site_sync'; kind='site'; script=$siteScript; expected=$siteExpected; required='SECOND_WAVE_SITE_VISIBILITY_VERIFIED' },
  [pscustomobject]@{ name='source_scan_300x60_a'; kind='source'; script=$sourceScript; expected=$sourceExpected; required='' },
  [pscustomobject]@{ name='evidence_40_a'; kind='evidence'; script=$evidenceScript; expected=$evidenceExpected; required='' },
  [pscustomobject]@{ name='checkpoint_site_sync_a'; kind='site'; script=$siteScript; expected=$siteExpected; required='SECOND_WAVE_SITE_VISIBILITY_VERIFIED' },
  [pscustomobject]@{ name='source_scan_300x60_b'; kind='source'; script=$sourceScript; expected=$sourceExpected; required='' },
  [pscustomobject]@{ name='evidence_40_b'; kind='evidence'; script=$evidenceScript; expected=$evidenceExpected; required='' },
  [pscustomobject]@{ name='checkpoint_site_sync_b'; kind='site'; script=$siteScript; expected=$siteExpected; required='SECOND_WAVE_SITE_VISIBILITY_VERIFIED' },
  [pscustomobject]@{ name='source_scan_300x60_c'; kind='source'; script=$sourceScript; expected=$sourceExpected; required='' },
  [pscustomobject]@{ name='evidence_40_c'; kind='evidence'; script=$evidenceScript; expected=$evidenceExpected; required='' },
  [pscustomobject]@{ name='checkpoint_site_sync_c'; kind='site'; script=$siteScript; expected=$siteExpected; required='SECOND_WAVE_SITE_VISIBILITY_VERIFIED' },
  [pscustomobject]@{ name='source_scan_300x60_d'; kind='source'; script=$sourceScript; expected=$sourceExpected; required='' },
  [pscustomobject]@{ name='evidence_40_d'; kind='evidence'; script=$evidenceScript; expected=$evidenceExpected; required='' },
  [pscustomobject]@{ name='post_site_sync_readback'; kind='site'; script=$siteScript; expected=$siteExpected; required='SECOND_WAVE_SITE_VISIBILITY_VERIFIED' }
)

foreach ($job in $jobs) {
  $r = Invoke-BatchJob -Name $job.name -ScriptRelative $job.script -ExpectedRelative $job.expected -RequiredStatus $job.required -Kind $job.kind
  $results.Add($r)
  foreach ($b in @($r.blockers)) { if ($b) { $allBlockers.Add(('{0}:{1}' -f $job.name,$b)) } }
}

$afterAll = Get-Counts $dataPath
$siteStatus = Read-JsonSafe (Join-Path $repoRoot $siteExpected)
$siteVerified = $siteStatus -and $siteStatus.status -eq 'SECOND_WAVE_SITE_VISIBILITY_VERIFIED' -and $siteStatus.served_json_matches_source -eq $true
if (-not $siteVerified) { $allBlockers.Add('post_site_readback_not_verified') }
$failedJobs = @($results | Where-Object { $_.state -match 'exception|missing|nonzero|stale' }).Count
$totalCandidatesExamined = [int](($results | Where-Object { $_.kind -eq 'source' } | Measure-Object -Property candidates_examined -Sum).Sum)
$acceptedRows = @($results | Where-Object { $_.kind -eq 'source' } | ForEach-Object { @($_.accepted_rows) } | Select-Object -Unique)
$evidenceRows = @($results | Where-Object { $_.kind -eq 'evidence' } | ForEach-Object { @($_.evidence_rows) } | Select-Object -Unique)
$statusName = if ($failedJobs -eq 0 -and $siteVerified) { 'FOUR_WAVES_AND_SITE_VISIBILITY_VERIFIED' } elseif ($afterAll.live -gt $beforeAll.live -or $afterAll.ready -gt $beforeAll.ready) { 'FOUR_WAVES_REAL_PROGRESS_SITE_OR_CHILD_PARTIAL' } else { 'FOUR_WAVES_BLOCKED_OR_NO_NEW_PROGRESS' }

$status = [ordered]@{
  task_id=$taskId; page_key='aays1'; status=$statusName
  runner_mode='single_shared_runner_sequential_four_waves'; jobs_total=$jobs.Count; jobs_failed=$failedJobs
  jobs_completed_with_fresh_output=@($results | Where-Object { $_.output_fresh }).Count; results=@($results)
  planned_candidates=1200; planned_max_new_sources=240; planned_evidence_operations=160
  candidates_examined=$totalCandidatesExamined; accepted_rows=@($acceptedRows); accepted_count=$acceptedRows.Count
  evidence_rows_targeted=@($evidenceRows); evidence_rows_targeted_count=$evidenceRows.Count
  counts_before=$beforeAll; counts_after=$afterAll
  source_verified_delta=([int]$afterAll.live-[int]$beforeAll.live)
  photo_rows_delta=([int]$afterAll.photos-[int]$beforeAll.photos)
  polygon_rows_delta=([int]$afterAll.polygons-[int]$beforeAll.polygons)
  evidence_ready_delta=([int]$afterAll.ready-[int]$beforeAll.ready)
  source_coverage_percent_after=[Math]::Round(([double]$afterAll.live/1264.0)*100,2)
  evidence_coverage_percent_after=[Math]::Round(([double]$afterAll.ready/1264.0)*100,2)
  site_visibility_verified=[bool]$siteVerified
  served_counts=if($siteStatus){$siteStatus.served_counts}else{$null}
  blockers=@($allBlockers | Select-Object -Unique)
  started_at=$startedAt; finished_at=[DateTimeOffset]::UtcNow.ToString('o')
  final_ready=$false; product_final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
}
$status | ConvertTo-Json -Depth 60 | Set-Content -LiteralPath $statusPath -Encoding UTF8

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# AAYS1 ReadyToSell Four Waves and Site Checkpoints')
$lines.Add('')
$lines.Add('- Status: ' + $statusName)
$lines.Add(('- Jobs with fresh output: {0} / {1}; failed={2}' -f $status.jobs_completed_with_fresh_output,$status.jobs_total,$failedJobs))
$lines.Add(('- Candidates examined / accepted: {0} / {1}' -f $totalCandidatesExamined,$acceptedRows.Count))
$lines.Add(('- Accepted row IDs: {0}' -f ($acceptedRows -join ', ')))
$lines.Add(('- Source verified: {0} -> {1}; delta={2}; coverage={3}%' -f $beforeAll.live,$afterAll.live,$status.source_verified_delta,$status.source_coverage_percent_after))
$lines.Add(('- Photo rows: {0} -> {1}; delta={2}' -f $beforeAll.photos,$afterAll.photos,$status.photo_rows_delta))
$lines.Add(('- Polygon rows: {0} -> {1}; delta={2}' -f $beforeAll.polygons,$afterAll.polygons,$status.polygon_rows_delta))
$lines.Add(('- Evidence-ready: {0} -> {1}; delta={2}; coverage={3}%' -f $beforeAll.ready,$afterAll.ready,$status.evidence_ready_delta,$status.evidence_coverage_percent_after))
$lines.Add('- Site visibility verified: ' + $siteVerified)
foreach ($r in $results) { $lines.Add(('- {0}: {1}; candidates={2}; accepted={3}; source_delta={4}; evidence_delta={5}; exit={6}' -f $r.name,$r.state,$r.candidates_examined,@($r.accepted_rows).Count,$r.source_delta,$r.evidence_ready_delta,$r.exit_code)) }
if ($status.blockers.Count -gt 0) { $lines.Add('- Blockers: ' + ($status.blockers -join '; ')) }
$lines.Add('')
$lines.Add('`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))

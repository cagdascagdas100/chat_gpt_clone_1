$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (& git rev-parse --show-toplevel 2>$null).Trim() }
$taskId = 'aays1-ready-to-sell-site-visibility-dom-resume-20260715'
$childScriptRelative = 'docs/chatgpt_status/aays1/automation/155_aays1_ready_to_sell_post_promotion_site_verify_20260713.ps1'
$childStatusRelative = 'docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
$statusRelative = 'docs/chatgpt_status/aays1/status/167_aays1_ready_to_sell_site_visibility_dom_resume_latest.json'
$reportRelative = 'docs/chatgpt_status/aays1/reports/167_aays1_ready_to_sell_site_visibility_dom_resume_report.md'
$outputRootRelative = 'docs/chatgpt_status/aays1/runner_outputs/167_site_visibility_dom_resume_20260715'
$pageUrl = 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html'

$childScriptPath = Join-Path $repoRoot $childScriptRelative
$childStatusPath = Join-Path $repoRoot $childStatusRelative
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$outputRoot = Join-Path $repoRoot $outputRootRelative
$domPath = Join-Path $outputRoot 'browser_dom.html'
$stderrPath = Join-Path $outputRoot 'browser_stderr.txt'
$childLogPath = Join-Path $outputRoot 'child_155.log'
New-Item -ItemType Directory -Force -Path (Split-Path $statusPath),(Split-Path $reportPath),$outputRoot | Out-Null

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
function Read-IntAttribute([string]$html,[string]$name) {
  $match = [regex]::Match($html,($name + '=["'']([0-9]+)["'']'),'IgnoreCase')
  if ($match.Success) { return [int]$match.Groups[1].Value }
  return 0
}

$started = [DateTimeOffset]::UtcNow
$startedAt = $started.ToString('o')
$blockers = [System.Collections.Generic.List[string]]::new()
$childHashBefore = Get-HashSafe $childStatusPath
$childExitCode = 1
$previousDetached = $env:AAYS_CANONICAL_DETACHED_WORKTREE

try {
  if (-not (Test-Path -LiteralPath $childScriptPath)) { throw ('missing_child_script:' + $childScriptRelative) }
  "[$startedAt] START resume child=$childScriptRelative" | Set-Content -LiteralPath $childLogPath -Encoding UTF8
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = 'true'
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $childScriptPath *>> $childLogPath
  $childExitCode = $LASTEXITCODE
  if ($null -eq $childExitCode) { $childExitCode = 0 }
} catch {
  $blockers.Add('child_155_execution_exception:' + $_.Exception.Message)
  $_.Exception.ToString() | Add-Content -LiteralPath $childLogPath -Encoding UTF8
} finally {
  $env:AAYS_CANONICAL_DETACHED_WORKTREE = $previousDetached
}

$childHashAfter = Get-HashSafe $childStatusPath
$childFresh = $false
if (Test-Path -LiteralPath $childStatusPath) {
  $childItem = Get-Item -LiteralPath $childStatusPath
  $childFresh = $childItem.LastWriteTimeUtc -ge $started.UtcDateTime.AddSeconds(-2) -and $childHashAfter -and ($childHashAfter -ne $childHashBefore)
}
$childStatus = Read-JsonSafe $childStatusPath
$childVerified = $childFresh -and $childStatus -and $childStatus.status -eq 'SECOND_WAVE_SITE_VISIBILITY_VERIFIED' -and $childStatus.served_json_matches_source -eq $true
if (-not $childFresh) { $blockers.Add('child_155_status_not_fresh_this_run') }
if (-not $childVerified) { $blockers.Add('child_155_terminal_site_visibility_pass_not_proven') }
if ($childExitCode -ne 0) { $blockers.Add('child_155_exit_' + $childExitCode) }

$browserCandidates = @(
  (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
  (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
  (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
  (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$browser = $browserCandidates | Select-Object -First 1
$browserExitCode = $null
$dom = ''
if (-not $browser) {
  $blockers.Add('headless_browser_not_found')
} else {
  try {
    & $browser '--headless=new' '--disable-gpu' '--no-first-run' '--no-default-browser-check' '--virtual-time-budget=20000' '--dump-dom' $pageUrl 2> $stderrPath | Set-Content -LiteralPath $domPath -Encoding UTF8
    $browserExitCode = $LASTEXITCODE
    if ($null -eq $browserExitCode) { $browserExitCode = 0 }
    if (Test-Path -LiteralPath $domPath) { $dom = Get-Content -LiteralPath $domPath -Raw -Encoding UTF8 }
  } catch {
    $blockers.Add('browser_dom_execution_exception:' + $_.Exception.Message)
  }
}

$loadReady = $dom -match 'data-load-state=["'']ready["'']'
$modeMatch = [regex]::Match($dom,'data-load-mode=["''](canonical_geometry|ai_evidence_fallback)["'']','IgnoreCase')
$loadMode = if ($modeMatch.Success) { $modeMatch.Groups[1].Value } else { $null }
$visibleRowCount = Read-IntAttribute $dom 'data-visible-row-count'
$liveSourceCount = Read-IntAttribute $dom 'data-live-source-count'
$renderedEvidenceRows = [regex]::Matches($dom,'data-evidence-row=').Count
$renderedProgressEvents = [regex]::Matches($dom,'data-progress-sequence=').Count
$renderedResearchCandidates = [regex]::Matches($dom,'data-research-candidate=').Count
$domProofOk = $browser -and $browserExitCode -eq 0 -and $loadReady -and $loadMode -and $visibleRowCount -ge 655 -and $liveSourceCount -eq 655 -and $renderedEvidenceRows -gt 0 -and $renderedProgressEvents -ge 5 -and $renderedResearchCandidates -ge 5
if (-not $loadReady) { $blockers.Add('browser_dom_load_state_not_ready') }
if (-not $loadMode) { $blockers.Add('browser_dom_load_mode_missing') }
if ($visibleRowCount -lt 655) { $blockers.Add('browser_dom_visible_row_count_below_655:' + $visibleRowCount) }
if ($liveSourceCount -ne 655) { $blockers.Add('browser_dom_live_source_count_not_655:' + $liveSourceCount) }
if ($renderedEvidenceRows -lt 1) { $blockers.Add('browser_dom_no_evidence_rows_rendered') }
if ($renderedProgressEvents -lt 5) { $blockers.Add('browser_dom_progress_events_below_5:' + $renderedProgressEvents) }
if ($renderedResearchCandidates -lt 5) { $blockers.Add('browser_dom_research_candidates_below_5:' + $renderedResearchCandidates) }

$uniqueBlockers = @($blockers | Select-Object -Unique)
$statusName = if ($childVerified -and $domProofOk -and $uniqueBlockers.Count -eq 0) { 'SITE_VISIBILITY_AND_BROWSER_DOM_VERIFIED' } else { 'SITE_VISIBILITY_OR_BROWSER_DOM_PARTIAL_OR_BLOCKED' }
$status = [ordered]@{
  task_id = $taskId
  page_key = 'aays1'
  status = $statusName
  runner_mode = 'single_shared_runner_sequential_resume_only'
  resumed_from_task_id = 'aays1-ready-to-sell-eight-wave-continuation-20260713'
  resume_job = '155_post_promotion_site_verify'
  source_scan_reexecution = $false
  task_146_reexecution = $false
  child_155_exit_code = $childExitCode
  child_155_status_fresh = [bool]$childFresh
  child_155_status = if ($childStatus) { [string]$childStatus.status } else { $null }
  child_155_terminal_pass = [bool]$childVerified
  browser_path = $browser
  browser_exit_code = $browserExitCode
  browser_dom_path = "$outputRootRelative/browser_dom.html"
  browser_stderr_path = "$outputRootRelative/browser_stderr.txt"
  browser_dom_load_ready = [bool]$loadReady
  browser_dom_load_mode = $loadMode
  browser_dom_visible_row_count = $visibleRowCount
  browser_dom_live_source_count = $liveSourceCount
  browser_dom_rendered_evidence_rows = $renderedEvidenceRows
  browser_dom_rendered_progress_events = $renderedProgressEvents
  browser_dom_rendered_research_candidates = $renderedResearchCandidates
  browser_dom_proof = [bool]$domProofOk
  blockers = $uniqueBlockers
  started_at = $startedAt
  finished_at = [DateTimeOffset]::UtcNow.ToString('o')
  single_runner_only = $true
  new_runner = $false
  parallel_runner = $false
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
}
$status | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$lines = @(
  '# AAYS1 ReadyToSell Site Visibility and Browser DOM Resume',
  '',
  "- Status: $statusName",
  "- Child 155 fresh / terminal pass: $childFresh / $childVerified",
  "- Browser DOM ready / mode: $loadReady / $loadMode",
  "- DOM visible rows / live sources: $visibleRowCount / $liveSourceCount",
  "- DOM rendered evidence rows / progress events / research candidates: $renderedEvidenceRows / $renderedProgressEvents / $renderedResearchCandidates",
  "- Source scan reexecution: false",
  "- Task 146 reexecution: false",
  "- Blockers: $($uniqueBlockers -join '; ')",
  '',
  '`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
)
[System.IO.File]::WriteAllLines($reportPath,$lines,[System.Text.UTF8Encoding]::new($false))
if ($statusName -eq 'SITE_VISIBILITY_AND_BROWSER_DOM_VERIFIED') { exit 0 }
exit 1

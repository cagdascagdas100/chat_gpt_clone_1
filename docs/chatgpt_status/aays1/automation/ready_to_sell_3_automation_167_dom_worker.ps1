$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$slotId = if ($env:AAYS_SLOT_ID) { [string]$env:AAYS_SLOT_ID } else { 'ready_to_sell_3' }
$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'aays1-ready-to-sell-3-automation-167-dom-proof-20260720' }
if ($slotId -ne 'ready_to_sell_3') {
    Write-Error "SLOT_ID_MISMATCH:$slotId"
    exit 2
}

$repoRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
if (-not $repoRoot) {
    Write-Error 'REPO_ROOT_UNAVAILABLE'
    exit 2
}

$slotRootRelative = 'docs/chatgpt_status/aays1/shards/ready_to_sell_3'
$slotRoot = Join-Path $repoRoot $slotRootRelative
$runStamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMdd_HHmmss')
$outputRootRelative = "$slotRootRelative/runner_outputs/automation_167_dom_proof_$runStamp"
$outputRoot = Join-Path $repoRoot $outputRootRelative
$statusRelative = "$slotRootRelative/status/automation_167_dom_proof_latest.json"
$reportRelative = "$slotRootRelative/reports/automation_167_dom_proof_latest.md"
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$domRelative = "$outputRootRelative/browser_dom.html"
$stderrRelative = "$outputRootRelative/browser_stderr.txt"
$businessSnapshotRelative = "$outputRootRelative/remote_business_state_snapshot.json"
$domPath = Join-Path $repoRoot $domRelative
$stderrPath = Join-Path $repoRoot $stderrRelative
$businessSnapshotPath = Join-Path $repoRoot $businessSnapshotRelative

New-Item -ItemType Directory -Force -Path $outputRoot,(Split-Path $statusPath),(Split-Path $reportPath) | Out-Null

function Write-Utf8NoBom([string]$Path,[string]$Text) {
    $parent = Split-Path $Path
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [System.IO.File]::WriteAllText($Path,$Text,[System.Text.UTF8Encoding]::new($false))
}

function Write-JsonNoBom([string]$Path,$Value) {
    Write-Utf8NoBom -Path $Path -Text (($Value | ConvertTo-Json -Depth 40) + "`n")
}

function Read-JsonSafe([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        if ($raw.Length -gt 0 -and [int]$raw[0] -eq 65279) { $raw = $raw.Substring(1) }
        return ($raw | ConvertFrom-Json)
    } catch {
        return $null
    }
}

function Get-HashSafe([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash } catch { return $null }
}

function Read-IntAttribute([string]$Html,[string]$Name) {
    $match = [regex]::Match($Html,($Name + '=["'']([0-9]+)["'']'),'IgnoreCase')
    if ($match.Success) { return [int]$match.Groups[1].Value }
    return 0
}

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$blockers = [System.Collections.Generic.List[string]]::new()
$pageUrl = 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html'
$healthUrl = 'http://127.0.0.1:8012/health'
$statusRoot = Join-Path $repoRoot 'docs/chatgpt_status/aays1/status'
$automation167Path = Join-Path $repoRoot 'docs/chatgpt_status/aays1/automation/167_aays1_ready_to_sell_site_visibility_dom_resume_20260715.ps1'
$terminal155Path = Join-Path $statusRoot '155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
$terminal155 = Read-JsonSafe $terminal155Path
$terminal166Item = Get-ChildItem -LiteralPath $statusRoot -Filter '166*ready_to_sell*.json' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
$terminal166Path = if ($terminal166Item) { $terminal166Item.FullName } else { $null }
$terminal166 = if ($terminal166Path) { Read-JsonSafe $terminal166Path } else { $null }
$existing167StatusPath = Join-Path $statusRoot '167_aays1_ready_to_sell_site_visibility_dom_resume_latest.json'

$terminal155Verified = $terminal155 -and [string]$terminal155.status -eq 'SECOND_WAVE_SITE_VISIBILITY_VERIFIED' -and $terminal155.served_json_matches_source -eq $true
if (-not $terminal155Verified) { $blockers.Add('REMOTE_BUSINESS_STATE_155_NOT_TERMINAL_VERIFIED') }
if (-not (Test-Path -LiteralPath $automation167Path)) { $blockers.Add('AUTOMATION_167_SCRIPT_MISSING') }

$businessSnapshot = [ordered]@{
    task_id = $taskId
    slot_id = $slotId
    read_at = [DateTimeOffset]::UtcNow.ToString('o')
    terminal_reexecution = $false
    source_scan_reexecution = $false
    terminal_155_path = 'docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
    terminal_155_sha256 = Get-HashSafe $terminal155Path
    terminal_155_status = if ($terminal155) { [string]$terminal155.status } else { $null }
    terminal_155_served_json_matches_source = if ($terminal155) { [bool]$terminal155.served_json_matches_source } else { $false }
    terminal_155_live_source_verified_rows = if ($terminal155) { [int]$terminal155.live_source_verified_rows } else { 0 }
    terminal_166_path = if ($terminal166Path) { $terminal166Path.Substring($repoRoot.Length + 1).Replace('\','/') } else { $null }
    terminal_166_sha256 = if ($terminal166Path) { Get-HashSafe $terminal166Path } else { $null }
    terminal_166_status = if ($terminal166) { [string]$terminal166.status } else { $null }
    automation_167_script_sha256 = Get-HashSafe $automation167Path
    preexisting_automation_167_status_present = Test-Path -LiteralPath $existing167StatusPath
    final_ready = $false
}
Write-JsonNoBom -Path $businessSnapshotPath -Value $businessSnapshot

$healthStatus = 0
$pageHttpStatus = 0
try {
    $healthResponse = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 10
    $healthStatus = [int]$healthResponse.StatusCode
} catch {
    $blockers.Add('PORT_8012_HEALTH_UNAVAILABLE:' + $_.Exception.Message)
}
try {
    $pageResponse = Invoke-WebRequest -UseBasicParsing -Uri $pageUrl -TimeoutSec 20
    $pageHttpStatus = [int]$pageResponse.StatusCode
} catch {
    $blockers.Add('AUTOMATION_167_PAGE_HTTP_UNAVAILABLE:' + $_.Exception.Message)
}

$candidatePaths = [System.Collections.Generic.List[string]]::new()
$portableRoot = [string]$env:AAYS_PORTABLE_ROOT
if ($portableRoot) {
    foreach ($relative in @('runtime/browser/chrome.exe','runtime/chrome/chrome.exe','runtime/chromium/chrome.exe','runtime/msedge/msedge.exe')) {
        $candidatePaths.Add((Join-Path $portableRoot $relative))
    }
}
if (${env:ProgramFiles(x86)}) {
    $candidatePaths.Add((Join-Path ${env:ProgramFiles(x86)} 'Microsoft/Edge/Application/msedge.exe'))
    $candidatePaths.Add((Join-Path ${env:ProgramFiles(x86)} 'Google/Chrome/Application/chrome.exe'))
}
if ($env:ProgramFiles) {
    $candidatePaths.Add((Join-Path $env:ProgramFiles 'Microsoft/Edge/Application/msedge.exe'))
    $candidatePaths.Add((Join-Path $env:ProgramFiles 'Google/Chrome/Application/chrome.exe'))
}
$browserCandidates = @($candidatePaths | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique)
$browser = $browserCandidates | Select-Object -First 1
$browserExitCode = $null
$dom = ''
if (-not $browser) {
    $blockers.Add('HEADLESS_BROWSER_NOT_FOUND')
} else {
    try {
        & $browser '--headless=new' '--disable-gpu' '--disable-extensions' '--no-first-run' '--no-default-browser-check' '--virtual-time-budget=25000' '--dump-dom' $pageUrl 2> $stderrPath | Set-Content -LiteralPath $domPath -Encoding UTF8
        $browserExitCode = $LASTEXITCODE
        if ($null -eq $browserExitCode) { $browserExitCode = 0 }
        if (Test-Path -LiteralPath $domPath) { $dom = Get-Content -LiteralPath $domPath -Raw -Encoding UTF8 }
    } catch {
        $blockers.Add('BROWSER_DOM_EXECUTION_EXCEPTION:' + $_.Exception.Message)
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
$stderrText = if (Test-Path -LiteralPath $stderrPath) { Get-Content -LiteralPath $stderrPath -Raw -Encoding UTF8 } else { '' }
$browserErrorLineCount = @($stderrText -split "`r?`n" | Where-Object { $_ -match '\b(ERROR|FATAL)\b' }).Count

if ($healthStatus -ne 200) { $blockers.Add('HEALTH_HTTP_STATUS_NOT_200:' + $healthStatus) }
if ($pageHttpStatus -ne 200) { $blockers.Add('PAGE_HTTP_STATUS_NOT_200:' + $pageHttpStatus) }
if ($browser -and $browserExitCode -ne 0) { $blockers.Add('BROWSER_EXIT_NONZERO:' + $browserExitCode) }
if (-not $loadReady) { $blockers.Add('BROWSER_DOM_LOAD_STATE_NOT_READY') }
if (-not $loadMode) { $blockers.Add('BROWSER_DOM_LOAD_MODE_MISSING') }
if ($visibleRowCount -lt 655) { $blockers.Add('BROWSER_DOM_VISIBLE_ROW_COUNT_BELOW_655:' + $visibleRowCount) }
if ($liveSourceCount -ne 655) { $blockers.Add('BROWSER_DOM_LIVE_SOURCE_COUNT_NOT_655:' + $liveSourceCount) }
if ($renderedEvidenceRows -lt 1) { $blockers.Add('BROWSER_DOM_NO_EVIDENCE_ROWS_RENDERED') }
if ($renderedProgressEvents -lt 5) { $blockers.Add('BROWSER_DOM_PROGRESS_EVENTS_BELOW_5:' + $renderedProgressEvents) }
if ($renderedResearchCandidates -lt 5) { $blockers.Add('BROWSER_DOM_RESEARCH_CANDIDATES_BELOW_5:' + $renderedResearchCandidates) }

$uniqueBlockers = @($blockers | Select-Object -Unique)
$acceptancePass = $terminal155Verified -and $healthStatus -eq 200 -and $pageHttpStatus -eq 200 -and $browser -and $browserExitCode -eq 0 -and $loadReady -and $loadMode -and $visibleRowCount -ge 655 -and $liveSourceCount -eq 655 -and $renderedEvidenceRows -gt 0 -and $renderedProgressEvents -ge 5 -and $renderedResearchCandidates -ge 5 -and $uniqueBlockers.Count -eq 0
$statusName = if ($acceptancePass) { 'AUTOMATION_167_DOM_PROOF_VERIFIED' } else { 'AUTOMATION_167_DOM_PROOF_BLOCKED' }

$status = [ordered]@{
    schema_version = 3
    architecture_version = 3
    workstream_id = 'AAYS_21_SLOT_SAFE_PARALLEL_V1'
    task_id = $taskId
    slot_id = $slotId
    base_slot_id = 'ready_to_sell'
    shard_index = 3
    parcel_partition = [ordered]@{ start = 61523; end = 92283; count = 30761; canonical_count = 92283 }
    status = $statusName
    acceptance_pass = [bool]$acceptancePass
    first_unverified_step = if ($acceptancePass) { $null } else { 'AUTOMATION_167_DOM_PROOF' }
    terminal_reexecution = $false
    source_scan_reexecution = $false
    terminal_155_verified = [bool]$terminal155Verified
    health_http_status = $healthStatus
    page_http_status = $pageHttpStatus
    browser_path = $browser
    browser_exit_code = $browserExitCode
    browser_dom_path = $domRelative
    browser_stderr_path = $stderrRelative
    remote_business_state_snapshot_path = $businessSnapshotRelative
    browser_dom_load_ready = [bool]$loadReady
    browser_dom_load_mode = $loadMode
    browser_dom_visible_row_count = $visibleRowCount
    browser_dom_live_source_count = $liveSourceCount
    browser_dom_rendered_evidence_rows = $renderedEvidenceRows
    browser_dom_rendered_progress_events = $renderedProgressEvents
    browser_dom_rendered_research_candidates = $renderedResearchCandidates
    browser_error_line_count_diagnostic_only = $browserErrorLineCount
    blockers = $uniqueBlockers
    started_at = $startedAt
    finished_at = [DateTimeOffset]::UtcNow.ToString('o')
    evidence_publish_exit_zero = $true
    evidence_publish_exit_zero_reason = 'Coordinator publishes declared shard outputs only after worker exit code zero; acceptance truth is acceptance_pass/status.'
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
Write-JsonNoBom -Path $statusPath -Value $status

$reportLines = @(
    '# ReadyToSell Shard 3 — Automation 167 DOM Proof',
    '',
    "- Task: ``$taskId``",
    "- Slot: ``$slotId`` (61523-92283)",
    "- Status: ``$statusName``",
    "- Acceptance pass: ``$acceptancePass``",
    "- Terminal 155 remote business state verified: ``$terminal155Verified``",
    '- Terminal/source task replay: `false`',
    "- Health/page HTTP: ``$healthStatus / $pageHttpStatus``",
    "- Browser exit: ``$browserExitCode``",
    "- DOM load ready/mode: ``$loadReady / $loadMode``",
    "- Visible rows/live sources: ``$visibleRowCount / $liveSourceCount``",
    "- Evidence rows/progress events/research candidates: ``$renderedEvidenceRows / $renderedProgressEvents / $renderedResearchCandidates``",
    "- Browser error lines (diagnostic only): ``$browserErrorLineCount``",
    "- Blockers: ``$($uniqueBlockers -join '; ')``",
    '',
    "- DOM: ``$domRelative``",
    "- Browser stderr: ``$stderrRelative``",
    "- Remote business snapshot: ``$businessSnapshotRelative``",
    '',
    '`final_ready=false`; `product_final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.'
)
Write-Utf8NoBom -Path $reportPath -Text (($reportLines -join "`n") + "`n")

# Exit zero publishes truthful PASS/BLOCKED evidence through the single serial publisher.
exit 0

$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$slotId = if ($env:AAYS_SLOT_ID) { [string]$env:AAYS_SLOT_ID } else { 'ready_to_sell_2' }
$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'aays1-ready-to-sell-2-automation-167-dom-proof-20260720' }
if ($slotId -ne 'ready_to_sell_2') { Write-Error "SLOT_ID_MISMATCH:$slotId"; exit 2 }

$repoRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
if (-not $repoRoot) { Write-Error 'REPO_ROOT_UNAVAILABLE'; exit 2 }

$slotRootRelative = 'docs/chatgpt_status/aays1/shards/ready_to_sell_2'
$webRootRelative = 'england_map_web/data/aays_21_slots/ready_to_sell_2'
$slotRoot = Join-Path $repoRoot $slotRootRelative
$webRoot = Join-Path $repoRoot $webRootRelative
$runStamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMdd_HHmmss')
$outputRootRelative = "$slotRootRelative/runner_outputs/automation_167_dom_proof_$runStamp"
$outputRoot = Join-Path $repoRoot $outputRootRelative
$statusRelative = "$slotRootRelative/status/automation_167_dom_proof_latest.json"
$reportRelative = "$slotRootRelative/reports/automation_167_dom_proof_latest.md"
$webProgressRelative = "$webRootRelative/progress_latest.json"
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$webProgressPath = Join-Path $repoRoot $webProgressRelative
$domRelative = "$outputRootRelative/browser_dom.html"
$stderrRelative = "$outputRootRelative/browser_stderr.txt"
$businessSnapshotRelative = "$outputRootRelative/remote_business_state_snapshot.json"
$domPath = Join-Path $repoRoot $domRelative
$stderrPath = Join-Path $repoRoot $stderrRelative
$businessSnapshotPath = Join-Path $repoRoot $businessSnapshotRelative
New-Item -ItemType Directory -Force -Path $outputRoot,(Split-Path $statusPath),(Split-Path $reportPath),$webRoot | Out-Null

function Write-Utf8NoBom([string]$Path,[string]$Text) {
    $parent = Split-Path $Path
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [System.IO.File]::WriteAllText($Path,$Text,[System.Text.UTF8Encoding]::new($false))
}
function Write-JsonNoBom([string]$Path,$Value) { Write-Utf8NoBom -Path $Path -Text (($Value | ConvertTo-Json -Depth 50) + "`n") }
function Read-JsonSafe([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    try { $raw=Get-Content -LiteralPath $Path -Raw -Encoding UTF8; if($raw.Length -gt 0 -and [int]$raw[0]-eq 65279){$raw=$raw.Substring(1)}; return ($raw|ConvertFrom-Json) } catch { return $null }
}
function Get-HashSafe([string]$Path) { if(Test-Path -LiteralPath $Path){try{return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash}catch{}}; return $null }
function Read-IntAttribute([string]$Html,[string]$Name) { $m=[regex]::Match($Html,($Name+'=["'']([0-9]+)["'']'),'IgnoreCase'); if($m.Success){return [int]$m.Groups[1].Value}; return 0 }

$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
$blockers = [System.Collections.Generic.List[string]]::new()
$pageUrl = 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html'
$healthUrl = 'http://127.0.0.1:8012/health'
$statusRoot = Join-Path $repoRoot 'docs/chatgpt_status/aays1/status'
$terminal155Path = Join-Path $statusRoot '155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
$terminal155 = Read-JsonSafe $terminal155Path
$terminal155Verified = $terminal155 -and [string]$terminal155.status -eq 'SECOND_WAVE_SITE_VISIBILITY_VERIFIED' -and $terminal155.served_json_matches_source -eq $true
if (-not $terminal155Verified) { $blockers.Add('REMOTE_BUSINESS_STATE_155_NOT_TERMINAL_VERIFIED') }
$requiredLiveSources = if ($terminal155Verified -and [int]$terminal155.live_source_verified_rows -gt 0) { [int]$terminal155.live_source_verified_rows } else { 655 }
$requiredVisibleRows = [Math]::Max(655,$requiredLiveSources)

$businessSnapshot = [ordered]@{
    task_id=$taskId; slot_id=$slotId; read_at=[DateTimeOffset]::UtcNow.ToString('o'); terminal_reexecution=$false; source_scan_reexecution=$false
    terminal_155_path='docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
    terminal_155_sha256=Get-HashSafe $terminal155Path
    terminal_155_status=if($terminal155){[string]$terminal155.status}else{$null}
    terminal_155_served_json_matches_source=if($terminal155){[bool]$terminal155.served_json_matches_source}else{$false}
    terminal_155_live_source_verified_rows=if($terminal155){[int]$terminal155.live_source_verified_rows}else{0}
    terminal_155_photo_rows=if($terminal155){[int]$terminal155.rows_with_downloaded_photos}else{0}
    terminal_155_polygon_rows=if($terminal155){[int]$terminal155.rows_with_polygon_render}else{0}
    terminal_155_evidence_ready_rows=if($terminal155){[int]$terminal155.rows_evidence_ready}else{0}
    required_visible_rows=$requiredVisibleRows; required_live_source_count=$requiredLiveSources; final_ready=$false
}
Write-JsonNoBom -Path $businessSnapshotPath -Value $businessSnapshot

$healthStatus=0; $pageHttpStatus=0
try{$r=Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 10;$healthStatus=[int]$r.StatusCode}catch{$blockers.Add('PORT_8012_HEALTH_UNAVAILABLE:'+ $_.Exception.Message)}
try{$r=Invoke-WebRequest -UseBasicParsing -Uri $pageUrl -TimeoutSec 20;$pageHttpStatus=[int]$r.StatusCode}catch{$blockers.Add('AUTOMATION_167_PAGE_HTTP_UNAVAILABLE:'+ $_.Exception.Message)}

$candidates=[System.Collections.Generic.List[string]]::new()
if($env:AAYS_PORTABLE_ROOT){foreach($r in @('runtime/browser/chrome.exe','runtime/chrome/chrome.exe','runtime/chromium/chrome.exe','runtime/msedge/msedge.exe')){$candidates.Add((Join-Path $env:AAYS_PORTABLE_ROOT $r))}}
if(${env:ProgramFiles(x86)}){$candidates.Add((Join-Path ${env:ProgramFiles(x86)} 'Microsoft/Edge/Application/msedge.exe'));$candidates.Add((Join-Path ${env:ProgramFiles(x86)} 'Google/Chrome/Application/chrome.exe'))}
if($env:ProgramFiles){$candidates.Add((Join-Path $env:ProgramFiles 'Microsoft/Edge/Application/msedge.exe'));$candidates.Add((Join-Path $env:ProgramFiles 'Google/Chrome/Application/chrome.exe'))}
$browser=@($candidates|Where-Object{$_ -and (Test-Path -LiteralPath $_)}|Select-Object -Unique)|Select-Object -First 1
$browserExitCode=$null; $dom=''
if(-not $browser){$blockers.Add('HEADLESS_BROWSER_NOT_FOUND')}else{try{& $browser '--headless=new' '--disable-gpu' '--disable-extensions' '--no-first-run' '--no-default-browser-check' '--virtual-time-budget=25000' '--dump-dom' $pageUrl 2> $stderrPath | Set-Content -LiteralPath $domPath -Encoding UTF8;$browserExitCode=$LASTEXITCODE;if($null-eq$browserExitCode){$browserExitCode=0};if(Test-Path -LiteralPath $domPath){$dom=Get-Content -LiteralPath $domPath -Raw -Encoding UTF8}}catch{$blockers.Add('BROWSER_DOM_EXECUTION_EXCEPTION:'+ $_.Exception.Message)}}

$loadReady=$dom -match 'data-load-state=["'']ready["'']'
$modeMatch=[regex]::Match($dom,'data-load-mode=["''](canonical_geometry|ai_evidence_fallback)["'']','IgnoreCase')
$loadMode=if($modeMatch.Success){$modeMatch.Groups[1].Value}else{$null}
$visibleRows=Read-IntAttribute $dom 'data-visible-row-count'
$liveSources=Read-IntAttribute $dom 'data-live-source-count'
$evidenceRows=[regex]::Matches($dom,'data-evidence-row=').Count
$progressEvents=[regex]::Matches($dom,'data-progress-sequence=').Count
$researchCandidates=[regex]::Matches($dom,'data-research-candidate=').Count
if($healthStatus-ne200){$blockers.Add('HEALTH_HTTP_STATUS_NOT_200:'+ $healthStatus)}
if($pageHttpStatus-ne200){$blockers.Add('PAGE_HTTP_STATUS_NOT_200:'+ $pageHttpStatus)}
if($browser -and $browserExitCode-ne0){$blockers.Add('BROWSER_EXIT_NONZERO:'+ $browserExitCode)}
if(-not $loadReady){$blockers.Add('BROWSER_DOM_LOAD_STATE_NOT_READY')}
if(-not $loadMode){$blockers.Add('BROWSER_DOM_LOAD_MODE_MISSING')}
if($visibleRows-lt$requiredVisibleRows){$blockers.Add('BROWSER_DOM_VISIBLE_ROW_COUNT_BELOW_REQUIRED:'+ $visibleRows+'/'+$requiredVisibleRows)}
if($liveSources-ne$requiredLiveSources){$blockers.Add('BROWSER_DOM_LIVE_SOURCE_COUNT_MISMATCH:'+ $liveSources+'/'+$requiredLiveSources)}
if($evidenceRows-lt1){$blockers.Add('BROWSER_DOM_NO_EVIDENCE_ROWS_RENDERED')}
if($progressEvents-lt5){$blockers.Add('BROWSER_DOM_PROGRESS_EVENTS_BELOW_5:'+ $progressEvents)}
if($researchCandidates-lt4){$blockers.Add('BROWSER_DOM_RESEARCH_CANDIDATES_BELOW_4:'+ $researchCandidates)}
$unique=@($blockers|Select-Object -Unique)
$pass=$terminal155Verified -and $healthStatus-eq200 -and $pageHttpStatus-eq200 -and $browser -and $browserExitCode-eq0 -and $loadReady -and $loadMode -and $visibleRows-ge$requiredVisibleRows -and $liveSources-eq$requiredLiveSources -and $evidenceRows-gt0 -and $progressEvents-ge5 -and $researchCandidates-ge4 -and $unique.Count-eq0
$statusName=if($pass){'AUTOMATION_167_DOM_PROOF_VERIFIED'}else{'AUTOMATION_167_DOM_PROOF_BLOCKED'}

$status=[ordered]@{
 schema_version=3;architecture_version=3;workstream_id='AAYS_21_SLOT_SAFE_PARALLEL_V1';task_id=$taskId;slot_id=$slotId;base_slot_id='ready_to_sell';shard_index=2
 parcel_partition=[ordered]@{start=30762;end=61522;count=30761;canonical_count=92283};status=$statusName;acceptance_pass=[bool]$pass
 first_unverified_step=if($pass){$null}else{'AUTOMATION_167_DOM_PROOF'};terminal_reexecution=$false;source_scan_reexecution=$false;terminal_155_verified=[bool]$terminal155Verified
 required_visible_rows=$requiredVisibleRows;required_live_source_count=$requiredLiveSources;health_http_status=$healthStatus;page_http_status=$pageHttpStatus;browser_path=$browser;browser_exit_code=$browserExitCode
 browser_dom_path=$domRelative;browser_stderr_path=$stderrRelative;remote_business_state_snapshot_path=$businessSnapshotRelative;browser_dom_load_ready=[bool]$loadReady;browser_dom_load_mode=$loadMode
 browser_dom_visible_row_count=$visibleRows;browser_dom_live_source_count=$liveSources;browser_dom_rendered_evidence_rows=$evidenceRows;browser_dom_rendered_progress_events=$progressEvents;browser_dom_rendered_research_candidates=$researchCandidates
 blockers=$unique;started_at=$startedAt;finished_at=[DateTimeOffset]::UtcNow.ToString('o');single_runner_only=$true;new_runner=$false;parallel_runner=$false;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
}
Write-JsonNoBom -Path $statusPath -Value $status

$web=Read-JsonSafe $webProgressPath
if(-not $web){$web=[ordered]@{schema_version=1;slot_id=$slotId;events=@()}}
$events=@($web.events)
$events=@($events|Where-Object{[string]$_.event -ne 'canonical_runner_dom_execution_and_remote_readback'})
$events+= [ordered]@{sequence=$events.Count+1;event='canonical_runner_dom_execution_and_remote_readback';result=if($pass){'pass'}else{'blocked'};detail="status=$statusName health=$healthStatus page=$pageHttpStatus visible=$visibleRows/$requiredVisibleRows live=$liveSources/$requiredLiveSources evidence=$evidenceRows progress=$progressEvents candidates=$researchCandidates blockers=$($unique -join ';')";accuracy_score=100}
$completed=@($events|Where-Object{$_.result-eq'pass'}).Count;$total=$events.Count
$web.events=$events;$web.completed_operations=$completed;$web.total_operations=$total;$web.batch_progress_percent=[Math]::Round(($completed/[Math]::Max(1,$total))*100,2);$web.status=$statusName;$web.updated_at=[DateTimeOffset]::UtcNow.ToString('o');$web.automation_167_status_path=$statusRelative;$web.automation_167_report_path=$reportRelative;$web.blockers=$unique;$web.final_ready=$false
Write-JsonNoBom -Path $webProgressPath -Value $web

$lines=@('# ReadyToSell Shard 2 — Automation 167 DOM Proof','',"- Task: `$taskId`","- Status: `$statusName`","- Acceptance pass: `$pass`","- Required/observed visible rows: `$requiredVisibleRows / $visibleRows`","- Required/observed live sources: `$requiredLiveSources / $liveSources`","- HTTP health/page: `$healthStatus / $pageHttpStatus`","- DOM ready/mode: `$loadReady / $loadMode`","- Evidence/progress/candidates: `$evidenceRows / $progressEvents / $researchCandidates`","- Blockers: `$($unique -join '; ')`",'','`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
Write-Utf8NoBom -Path $reportPath -Text (($lines -join "`n")+"`n")
exit 0

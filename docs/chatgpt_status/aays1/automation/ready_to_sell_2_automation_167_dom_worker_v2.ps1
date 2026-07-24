$ErrorActionPreference = 'Continue'
Set-StrictMode -Off

$slotId = if ($env:AAYS_SLOT_ID) { [string]$env:AAYS_SLOT_ID } else { 'ready_to_sell_2' }
$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'aays1-ready-to-sell-2-automation-167-dom-proof-20260720' }
if ($slotId -ne 'ready_to_sell_2') { Write-Error "SLOT_ID_MISMATCH:$slotId"; exit 2 }

$repoRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
if (-not $repoRoot) { Write-Error 'REPO_ROOT_UNAVAILABLE'; exit 2 }

$slotRootRelative = 'docs/chatgpt_status/aays1/shards/ready_to_sell_2'
$webRootRelative = 'england_map_web/data/aays_21_slots/ready_to_sell_2'
$runStamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMdd_HHmmss')
$outputRootRelative = "$slotRootRelative/runner_outputs/automation_167_dom_proof_v2_$runStamp"
$outputRoot = Join-Path $repoRoot $outputRootRelative
$statusRelative = "$slotRootRelative/status/automation_167_dom_proof_latest.json"
$reportRelative = "$slotRootRelative/reports/automation_167_dom_proof_latest.md"
$progressRelative = "$webRootRelative/progress_latest.json"
$fullProgressRelative = "$webRootRelative/progress_wave_47_latest.json"
$statusPath = Join-Path $repoRoot $statusRelative
$reportPath = Join-Path $repoRoot $reportRelative
$progressPath = Join-Path $repoRoot $progressRelative
$fullProgressPath = Join-Path $repoRoot $fullProgressRelative
$domRelative = "$outputRootRelative/browser_dom.html"
$stderrRelative = "$outputRootRelative/browser_stderr.txt"
$domPath = Join-Path $repoRoot $domRelative
$stderrPath = Join-Path $repoRoot $stderrRelative
$browserProfilePath = Join-Path ([IO.Path]::GetTempPath()) ("aays_automation167_browser_" + $runStamp)
New-Item -ItemType Directory -Force -Path $outputRoot,(Split-Path $statusPath),(Split-Path $reportPath) | Out-Null

function Write-Utf8NoBom([string]$Path,[string]$Text){$parent=Split-Path $Path;if($parent){New-Item -ItemType Directory -Force -Path $parent|Out-Null};[IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))}
function Write-JsonNoBom([string]$Path,$Value){Write-Utf8NoBom $Path (($Value|ConvertTo-Json -Depth 60)+"`n")}
function Read-JsonSafe([string]$Path){if(-not(Test-Path -LiteralPath $Path)){return $null};try{$raw=Get-Content -LiteralPath $Path -Raw -Encoding UTF8;if($raw.Length -gt 0 -and [int]$raw[0]-eq 65279){$raw=$raw.Substring(1)};return($raw|ConvertFrom-Json)}catch{return $null}}
function Read-IntAttribute([string]$Html,[string]$Name){$m=[regex]::Match($Html,($Name+'=["'']([0-9]+)["'']'),'IgnoreCase');if($m.Success){return[int]$m.Groups[1].Value};return 0}
function Set-Prop($Object,[string]$Name,$Value){if($null -eq $Object){return};$Object|Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force}
function Get-MaxEventSequence($Events){$max=0;foreach($event in @($Events)){try{$sequence=[int]$event.sequence;if($sequence -gt $max){$max=$sequence}}catch{}};return $max}
function Get-UniqueEventSequenceCount($PrimaryEvents,$SecondaryEvents){
 $seen=@{};$all=@();$all+=@($PrimaryEvents);$all+=@($SecondaryEvents)
 foreach($event in $all){$sequence=$null;try{$sequence=[string]$event.sequence}catch{};if(-not ([string]::IsNullOrWhiteSpace($sequence))){$seen[$sequence]=$true}}
 return $seen.Count
}
function Test-Automation167ProgressBlocker([string]$Code){
 if([string]::IsNullOrWhiteSpace($Code)){return $false}
 return ($Code -eq 'SAFE_F_HOST_SINGLE_RUNNER_NOT_CURRENTLY_HEARTBEATING' -or $Code -eq 'AUTOMATION_167_CANONICAL_PORT_8012_HEADLESS_DOM_EXECUTION_PENDING' -or $Code -match '^(AUTOMATION_167_|PORT_8012_|HEALTH_HTTP_STATUS_|PAGE_HTTP_STATUS_|BROWSER_|HEADLESS_BROWSER_|PROGRESS_BASELINE_|SLOT_STATUS_|REMOTE_BUSINESS_STATE_155_)')
}

$startedAt=[DateTimeOffset]::UtcNow.ToString('o')
$blockers=[Collections.Generic.List[string]]::new()
$pageUrl='http://127.0.0.1:8012/england_map_web/ready_to_sell_2_automation_167_acceptance.html'
$healthUrl='http://127.0.0.1:8012/health'
$terminal155Path=Join-Path $repoRoot 'docs/chatgpt_status/aays1/status/155_aays1_ready_to_sell_second_wave_dispatch_latest.json'
$slotStatusPath=Join-Path $repoRoot 'docs/chatgpt_status/_shared/slots_21/ready_to_sell_2/status_latest.json'
$terminal155=Read-JsonSafe $terminal155Path
$slotStatus=Read-JsonSafe $slotStatusPath
$terminal155Verified=$terminal155 -and [string]$terminal155.status -eq 'SECOND_WAVE_SITE_VISIBILITY_VERIFIED' -and $terminal155.served_json_matches_source -eq $true
if(-not $terminal155Verified){$blockers.Add('REMOTE_BUSINESS_STATE_155_NOT_TERMINAL_VERIFIED')}
$slotStatusValue=if($slotStatus -and -not [string]::IsNullOrWhiteSpace([string]$slotStatus.state)){[string]$slotStatus.state}elseif($slotStatus -and -not [string]::IsNullOrWhiteSpace([string]$slotStatus.status)){[string]$slotStatus.status}else{$null}
$slotStatusValid=-not [string]::IsNullOrWhiteSpace($slotStatusValue)
if(-not $slotStatusValid){$blockers.Add('SLOT_STATUS_EMPTY_OR_UNAVAILABLE')}
if($slotStatus -and -not [string]::IsNullOrWhiteSpace([string]$slotStatus.task_id) -and [string]$slotStatus.task_id -ne $taskId){$slotStatusValid=$false;$blockers.Add('SLOT_STATUS_TASK_ID_MISMATCH:'+ [string]$slotStatus.task_id+'/'+$taskId)}
$requiredLiveSources=if($terminal155Verified -and [int]$terminal155.live_source_verified_rows -gt 0){[int]$terminal155.live_source_verified_rows}else{655}
$requiredVisibleRows=[Math]::Max(655,$requiredLiveSources)
$existing=Read-JsonSafe $progressPath
$fullProgress=Read-JsonSafe $fullProgressPath
if(-not $existing){$blockers.Add('PROGRESS_BASELINE_UNAVAILABLE')}
if(-not $fullProgress){$blockers.Add('PROGRESS_BASELINE_FULL_FEED_UNAVAILABLE')}
$expectedProgressEvents=if($existing -and $fullProgress){Get-UniqueEventSequenceCount $fullProgress.events $existing.events}else{0}
if($expectedProgressEvents-lt 5){$blockers.Add('PROGRESS_BASELINE_UNIQUE_EVENT_COUNT_BELOW_5:'+ $expectedProgressEvents)}
$baselineCompleted=if($existing){[int]$existing.completed_operations}else{0}
$baselineTotal=if($existing){[int]$existing.total_operations}else{0}
$baselineBatchPercent=if($existing){[double]$existing.batch_progress_percent}else{0.0}
$baselineOverallCompleted=if($existing){[int]$existing.overall_completed_evidence_events}else{0}
$baselineOverallTotal=if($existing){[int]$existing.overall_total_evidence_events}else{0}
$baselineOverallPercent=if($existing){[double]$existing.overall_progress_percent}else{0.0}
$candidateSummary=if($existing){$existing.candidate_summary}else{$null}
$baselineResearched=if($candidateSummary){[int]$candidateSummary.researched_total}else{0}
$baselineOpen=if($candidateSummary){[int]$candidateSummary.current_upcoming_or_available_count}else{0}
$baselineDuplicates=if($candidateSummary){[int]$candidateSummary.cumulative_duplicates_removed}else{0}
$baselineSourceUpgrades=if($candidateSummary){[int]$candidateSummary.cumulative_source_upgrade_rows}else{0}
$baselineCorrections=if($candidateSummary){[int]$candidateSummary.cumulative_corrected_prior_rows}else{0}
$baselineRepairs=if($candidateSummary){[int]$candidateSummary.cumulative_integrity_repairs}else{0}
$baselineHighConfidence=if($candidateSummary){[int]$candidateSummary.high_source_confidence}else{0}
$baselineNonRegression=$existing -and $baselineCompleted-ge 869 -and $baselineCompleted-le 870 -and $baselineTotal-eq 870 -and $baselineBatchPercent-ge 99.89 -and $baselineOverallCompleted-ge 883 -and $baselineOverallCompleted-le 884 -and $baselineOverallTotal-eq 884 -and $baselineOverallPercent-ge 99.89 -and $baselineResearched-ge 514 -and $baselineOpen-ge 511 -and $baselineDuplicates-ge 13 -and $baselineSourceUpgrades-ge 477 -and $baselineCorrections-ge 4 -and $baselineRepairs-ge 14 -and $baselineHighConfidence-ge 514
if($existing){
 if($baselineCompleted-lt 869 -or $baselineCompleted-gt 870){$blockers.Add('PROGRESS_BASELINE_COMPLETED_OPERATIONS_REGRESSION:'+ $baselineCompleted+'/869-870')}
 if($baselineTotal-ne 870){$blockers.Add('PROGRESS_BASELINE_TOTAL_OPERATIONS_MISMATCH:'+ $baselineTotal+'/870')}
 if($baselineBatchPercent-lt 99.89){$blockers.Add('PROGRESS_BASELINE_BATCH_PERCENT_REGRESSION:'+ $baselineBatchPercent+'/99.89')}
 if($baselineOverallCompleted-lt 883 -or $baselineOverallCompleted-gt 884){$blockers.Add('PROGRESS_BASELINE_OVERALL_COMPLETED_REGRESSION:'+ $baselineOverallCompleted+'/883-884')}
 if($baselineOverallTotal-ne 884){$blockers.Add('PROGRESS_BASELINE_OVERALL_TOTAL_MISMATCH:'+ $baselineOverallTotal+'/884')}
 if($baselineOverallPercent-lt 99.89){$blockers.Add('PROGRESS_BASELINE_OVERALL_PERCENT_REGRESSION:'+ $baselineOverallPercent+'/99.89')}
 if($baselineResearched-lt 514){$blockers.Add('PROGRESS_BASELINE_RESEARCHED_CANDIDATES_REGRESSION:'+ $baselineResearched+'/514')}
 if($baselineOpen-lt 511){$blockers.Add('PROGRESS_BASELINE_OPEN_CANDIDATES_REGRESSION:'+ $baselineOpen+'/511')}
 if($baselineDuplicates-lt 13){$blockers.Add('PROGRESS_BASELINE_DUPLICATES_REMOVED_REGRESSION:'+ $baselineDuplicates+'/13')}
 if($baselineSourceUpgrades-lt 477){$blockers.Add('PROGRESS_BASELINE_SOURCE_UPGRADES_REGRESSION:'+ $baselineSourceUpgrades+'/477')}
 if($baselineCorrections-lt 4){$blockers.Add('PROGRESS_BASELINE_CORRECTIONS_REGRESSION:'+ $baselineCorrections+'/4')}
 if($baselineRepairs-lt 14){$blockers.Add('PROGRESS_BASELINE_INTEGRITY_REPAIRS_REGRESSION:'+ $baselineRepairs+'/14')}
 if($baselineHighConfidence-lt 514){$blockers.Add('PROGRESS_BASELINE_HIGH_CONFIDENCE_REGRESSION:'+ $baselineHighConfidence+'/514')}
}
$preservedProgressBlockers=@()
if($existing -and $existing.blockers){$preservedProgressBlockers=@($existing.blockers|Where-Object{-not(Test-Automation167ProgressBlocker([string]$_))})}

$healthStatus=0;$pageHttpStatus=0;$httpAttempts=0;$httpAttemptLimit=30
for($attempt=1;$attempt -le $httpAttemptLimit;$attempt++){
 $httpAttempts=$attempt
 try{$r=Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 10;$healthStatus=[int]$r.StatusCode}catch{$healthStatus=0}
 try{$r=Invoke-WebRequest -UseBasicParsing -Uri $pageUrl -TimeoutSec 20;$pageHttpStatus=[int]$r.StatusCode}catch{$pageHttpStatus=0}
 if($healthStatus -eq 200 -and $pageHttpStatus -eq 200){break}
 if($attempt -lt $httpAttemptLimit){Start-Sleep -Seconds 10}
}
if($healthStatus -ne 200){$blockers.Add('PORT_8012_HEALTH_UNAVAILABLE_AFTER_RETRY:'+ $healthStatus)}
if($pageHttpStatus -ne 200){$blockers.Add('AUTOMATION_167_PAGE_HTTP_UNAVAILABLE_AFTER_RETRY:'+ $pageHttpStatus)}

$portableRoot=if($env:AAYS_PORTABLE_ROOT){[string]$env:AAYS_PORTABLE_ROOT}else{$null}
if(-not $portableRoot){
 $cursor=$repoRoot
 while($cursor -and (Split-Path -Leaf $cursor) -ne 'runner_system'){$parent=Split-Path -Parent $cursor;if(-not $parent -or $parent -eq $cursor){break};$cursor=$parent}
 if($cursor -and (Split-Path -Leaf $cursor) -eq 'runner_system'){$portableRoot=Split-Path -Parent $cursor}
}

$browserPaths=[Collections.Generic.List[string]]::new()
if($portableRoot){foreach($rel in @('runtime/browser/chrome.exe','runtime/chrome/chrome.exe','runtime/chromium/chrome.exe','runtime/msedge/msedge.exe')){$browserPaths.Add((Join-Path $portableRoot $rel))}}
if(${env:ProgramFiles(x86)}){$browserPaths.Add((Join-Path ${env:ProgramFiles(x86)} 'Microsoft/Edge/Application/msedge.exe'));$browserPaths.Add((Join-Path ${env:ProgramFiles(x86)} 'Google/Chrome/Application/chrome.exe'))}
if($env:ProgramFiles){$browserPaths.Add((Join-Path $env:ProgramFiles 'Microsoft/Edge/Application/msedge.exe'));$browserPaths.Add((Join-Path $env:ProgramFiles 'Google/Chrome/Application/chrome.exe'))}
$browser=@($browserPaths|Where-Object{$_ -and(Test-Path -LiteralPath $_)}|Select-Object -Unique)|Select-Object -First 1
$browserExitCode=$null;$dom=''
if(-not $browser){$blockers.Add('HEADLESS_BROWSER_NOT_FOUND')}elseif($healthStatus -eq 200 -and $pageHttpStatus -eq 200){
 try{
  New-Item -ItemType Directory -Force -Path $browserProfilePath | Out-Null
  & $browser '--headless=new' '--disable-gpu' '--disable-extensions' '--disable-background-networking' '--no-first-run' '--no-default-browser-check' ("--user-data-dir=$browserProfilePath") '--virtual-time-budget=30000' '--dump-dom' $pageUrl 2> $stderrPath | Set-Content -LiteralPath $domPath -Encoding UTF8
  $browserExitCode=$LASTEXITCODE
  if($null -eq $browserExitCode){$browserExitCode=0}
  if(Test-Path -LiteralPath $domPath){$dom=Get-Content -LiteralPath $domPath -Raw -Encoding UTF8}
 }catch{$blockers.Add('BROWSER_DOM_EXECUTION_EXCEPTION:'+ $_.Exception.Message)}
 finally{if(Test-Path -LiteralPath $browserProfilePath){Remove-Item -LiteralPath $browserProfilePath -Recurse -Force -ErrorAction SilentlyContinue}}
}

$renderedDom=[regex]::Replace($dom,'(?is)<script\b[^>]*>.*?</script>','')
$loadReady=$dom -match 'data-load-state=["'']ready["'']'
$modeMatch=[regex]::Match($dom,'data-load-mode=["''](canonical_geometry|ai_evidence_fallback)["'']','IgnoreCase')
$loadMode=if($modeMatch.Success){$modeMatch.Groups[1].Value}else{$null}
$visibleRows=Read-IntAttribute $dom 'data-visible-row-count'
$liveSources=Read-IntAttribute $dom 'data-live-source-count'
$evidenceRows=[regex]::Matches($renderedDom,'data-evidence-row=').Count
$progressEventCards=[regex]::Matches($renderedDom,'data-progress-sequence=').Count
$progressEvents=Read-IntAttribute $dom 'data-progress-event-count'
$researchCandidateCards=[regex]::Matches($renderedDom,'data-research-candidate=').Count
$researchCandidates=Read-IntAttribute $dom 'data-research-candidate-count'
$duplicateResearchCandidates=Read-IntAttribute $dom 'data-research-candidate-duplicate-count'
$missingResearchCandidateIds=Read-IntAttribute $dom 'data-research-candidate-missing-id-count'
if($healthStatus-ne 200){$blockers.Add('HEALTH_HTTP_STATUS_NOT_200:'+ $healthStatus)}
if($pageHttpStatus-ne 200){$blockers.Add('PAGE_HTTP_STATUS_NOT_200:'+ $pageHttpStatus)}
if($browser -and $browserExitCode-ne 0){$blockers.Add('BROWSER_EXIT_NONZERO:'+ $browserExitCode)}
if(-not $loadReady){$blockers.Add('BROWSER_DOM_LOAD_STATE_NOT_READY')}
if(-not $loadMode){$blockers.Add('BROWSER_DOM_LOAD_MODE_MISSING')}
if($visibleRows-lt $requiredVisibleRows){$blockers.Add('BROWSER_DOM_VISIBLE_ROW_COUNT_BELOW_REQUIRED:'+ $visibleRows+'/'+$requiredVisibleRows)}
if($liveSources-ne $requiredLiveSources){$blockers.Add('BROWSER_DOM_LIVE_SOURCE_COUNT_MISMATCH:'+ $liveSources+'/'+$requiredLiveSources)}
if($evidenceRows-lt 1){$blockers.Add('BROWSER_DOM_NO_EVIDENCE_ROWS_RENDERED')}
if($progressEvents-lt 5){$blockers.Add('BROWSER_DOM_PROGRESS_EVENTS_BELOW_5:'+ $progressEvents)}
if($progressEvents-ne $expectedProgressEvents){$blockers.Add('BROWSER_DOM_PROGRESS_EVENT_COUNT_MISMATCH:'+ $progressEvents+'/'+$expectedProgressEvents)}
if($progressEventCards-ne $progressEvents){$blockers.Add('BROWSER_DOM_PROGRESS_EVENT_CARD_COUNT_MISMATCH:'+ $progressEventCards+'/'+$progressEvents)}
if($researchCandidates-lt 30){$blockers.Add('BROWSER_DOM_UNIQUE_RESEARCH_CANDIDATES_BELOW_30:'+ $researchCandidates)}
if($researchCandidateCards-ne $researchCandidates){$blockers.Add('BROWSER_DOM_RESEARCH_CANDIDATE_CARD_COUNT_MISMATCH:'+ $researchCandidateCards+'/'+$researchCandidates)}
if($duplicateResearchCandidates-ne 0){$blockers.Add('BROWSER_DOM_DUPLICATE_RESEARCH_CANDIDATES_PRESENT:'+ $duplicateResearchCandidates)}
if($missingResearchCandidateIds-ne 0){$blockers.Add('BROWSER_DOM_RESEARCH_CANDIDATE_IDS_MISSING:'+ $missingResearchCandidateIds)}
$unique=@($blockers|Select-Object -Unique)
$progressBlockers=@($preservedProgressBlockers)
foreach($code in @($unique)){if($code -and -not($progressBlockers -contains [string]$code)){$progressBlockers+=[string]$code}}
$pass=$terminal155Verified -and $slotStatusValid -and $baselineNonRegression -and $healthStatus-eq 200 -and $pageHttpStatus-eq 200 -and $browser -and $browserExitCode-eq 0 -and $loadReady -and $loadMode -and $visibleRows-ge $requiredVisibleRows -and $liveSources-eq $requiredLiveSources -and $evidenceRows-gt 0 -and $expectedProgressEvents-ge 5 -and $progressEvents-eq $expectedProgressEvents -and $progressEventCards-eq $progressEvents -and $researchCandidates-ge 30 -and $researchCandidateCards-eq $researchCandidates -and $duplicateResearchCandidates-eq 0 -and $missingResearchCandidateIds-eq 0 -and $unique.Count-eq 0
$statusName=if($pass){'AUTOMATION_167_DOM_PROOF_VERIFIED'}else{'AUTOMATION_167_DOM_PROOF_BLOCKED'}

$status=[ordered]@{schema_version=3;architecture_version=3;workstream_id='AAYS_21_SLOT_SAFE_PARALLEL_V1';task_id=$taskId;slot_id=$slotId;status=$statusName;acceptance_pass=[bool]$pass;first_unverified_step=if($pass){$null}else{'AUTOMATION_167_DOM_PROOF'};slot_status_value=$slotStatusValue;slot_status_valid=[bool]$slotStatusValid;baseline_non_regression_verified=[bool]$baselineNonRegression;baseline_completed_operations=$baselineCompleted;baseline_total_operations=$baselineTotal;baseline_batch_progress_percent=$baselineBatchPercent;baseline_overall_completed_evidence_events=$baselineOverallCompleted;baseline_overall_total_evidence_events=$baselineOverallTotal;baseline_overall_progress_percent=$baselineOverallPercent;baseline_researched_candidates=$baselineResearched;baseline_open_candidates=$baselineOpen;baseline_duplicates_removed=$baselineDuplicates;baseline_source_upgrades=$baselineSourceUpgrades;baseline_corrected_rows=$baselineCorrections;baseline_integrity_repairs=$baselineRepairs;baseline_high_confidence_candidates=$baselineHighConfidence;required_visible_rows=$requiredVisibleRows;required_live_source_count=$requiredLiveSources;required_progress_event_count=$expectedProgressEvents;health_http_status=$healthStatus;page_http_status=$pageHttpStatus;http_retry_attempts=$httpAttempts;http_retry_attempt_limit=$httpAttemptLimit;portable_root=$portableRoot;browser_path=$browser;browser_exit_code=$browserExitCode;browser_profile_isolated=$true;browser_dom_script_content_excluded_from_card_counts=$true;browser_dom_path=$domRelative;browser_stderr_path=$stderrRelative;browser_dom_load_ready=[bool]$loadReady;browser_dom_load_mode=$loadMode;browser_dom_visible_row_count=$visibleRows;browser_dom_live_source_count=$liveSources;browser_dom_rendered_evidence_rows=$evidenceRows;browser_dom_progress_event_count=$progressEvents;browser_dom_rendered_progress_event_cards=$progressEventCards;browser_dom_rendered_progress_events=$progressEvents;browser_dom_rendered_research_candidate_cards=$researchCandidateCards;browser_dom_unique_research_candidates=$researchCandidates;browser_dom_duplicate_research_candidates=$duplicateResearchCandidates;browser_dom_missing_research_candidate_ids=$missingResearchCandidateIds;browser_dom_rendered_research_candidates=$researchCandidates;blockers=$unique;preserved_non_automation_blockers=$preservedProgressBlockers;progress_blockers_after_update=$progressBlockers;started_at=$startedAt;finished_at=[DateTimeOffset]::UtcNow.ToString('o');single_runner_only=$true;new_runner=$false;parallel_runner=$false;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
Write-JsonNoBom $statusPath $status

if($existing){
 $priorBatch=[double]$existing.batch_progress_percent
 $priorOverall=[double]$existing.overall_progress_percent
 $priorDomEvent=@($existing.events|Where-Object{[string]$_.event-eq'canonical_runner_dom_execution_and_remote_readback'}|Select-Object -First 1)
 $eventSequence=if($priorDomEvent -and $priorDomEvent.sequence){[int]$priorDomEvent.sequence}else{(Get-MaxEventSequence $existing.events)+1}
 $events=@($existing.events|Where-Object{[string]$_.event-ne'canonical_runner_dom_execution_and_remote_readback'})
 $events+=[ordered]@{sequence=$eventSequence;event='canonical_runner_dom_execution_and_remote_readback';result=if($pass){'pass'}else{'blocked'};detail="status=$statusName slot_status=$slotStatusValue baseline_ok=$baselineNonRegression completed=$baselineCompleted/$baselineTotal overall=$baselineOverallCompleted/$baselineOverallTotal researched=$baselineResearched open=$baselineOpen source_upgrades=$baselineSourceUpgrades health=$healthStatus page=$pageHttpStatus retries=$httpAttempts/$httpAttemptLimit visible=$visibleRows/$requiredVisibleRows live=$liveSources/$requiredLiveSources evidence=$evidenceRows progress=$progressEvents/$expectedProgressEvents progress_cards=$progressEventCards unique_candidates=$researchCandidates cards=$researchCandidateCards duplicates=$duplicateResearchCandidates missing_ids=$missingResearchCandidateIds isolated_profile=true script_content_excluded=true blockers=$($unique -join ';') preserved_non_automation=$($preservedProgressBlockers -join ';')";accuracy_score=100}
 $events=@($events|Sort-Object sequence)
 $completed=[int]$existing.completed_operations;$total=[int]$existing.total_operations
 if($pass){$completed=[Math]::Min($total,$completed+1)}
 $batch=[Math]::Round(($completed/[Math]::Max(1,$total))*100,2)
 $overallCompleted=[int]$existing.overall_completed_evidence_events;$overallTotal=[int]$existing.overall_total_evidence_events
 if($pass){$overallCompleted=[Math]::Min($overallTotal,$overallCompleted+1)}
 $overall=[Math]::Round(($overallCompleted/[Math]::Max(1,$overallTotal))*100,2)
 Set-Prop $existing 'status' $statusName
 Set-Prop $existing 'updated_at' ([DateTimeOffset]::UtcNow.ToString('o'))
 Set-Prop $existing 'events' $events
 Set-Prop $existing 'completed_operations' $completed
 Set-Prop $existing 'batch_progress_percent' $batch
 Set-Prop $existing 'batch_progress_percent_increase' ([Math]::Round($batch-$priorBatch,2))
 Set-Prop $existing 'overall_completed_evidence_events' $overallCompleted
 Set-Prop $existing 'overall_progress_percent' $overall
 Set-Prop $existing 'overall_progress_percent_increase' ([Math]::Round($overall-$priorOverall,2))
 Set-Prop $existing 'automation_167_status_path' $statusRelative
 Set-Prop $existing 'automation_167_report_path' $reportRelative
 Set-Prop $existing 'blockers' $progressBlockers
 Write-JsonNoBom $progressPath $existing
}
$report=@('# ReadyToSell Shard 2 — Automation 167 DOM Proof v2','',"- Status: ``$statusName``","- Acceptance pass: ``$pass``","- Slot status: ``$slotStatusValue``","- Baseline non-regression: ``$baselineNonRegression``","- Operations baseline: ``$baselineCompleted / $baselineTotal``","- Overall evidence baseline: ``$baselineOverallCompleted / $baselineOverallTotal``","- Candidate/open/source-upgrade baselines: ``$baselineResearched / $baselineOpen / $baselineSourceUpgrades``","- HTTP retry attempts: ``$httpAttempts / $httpAttemptLimit``","- Isolated browser profile: ``true``","- Script content excluded from card counts: ``true``","- Visible rows: ``$visibleRows / $requiredVisibleRows``","- Live sources: ``$liveSources / $requiredLiveSources``","- Evidence rows: ``$evidenceRows``","- Progress events/cards: ``$progressEvents / $progressEventCards``","- Required progress events: ``$expectedProgressEvents``","- Unique candidate IDs: ``$researchCandidates``","- Rendered candidate cards: ``$researchCandidateCards``","- Duplicate candidate IDs: ``$duplicateResearchCandidates``","- Missing candidate IDs: ``$missingResearchCandidateIds``","- Automation blockers: ``$($unique -join '; ')``","- Preserved non-automation blockers: ``$($preservedProgressBlockers -join '; ')``",'','`final_ready=false`; `fake_data=false`; `db_write=false`; `migration=false`; `production_deploy=false`.')
Write-Utf8NoBom $reportPath (($report-join"`n")+"`n")
if($pass){exit 0}else{exit 3}

[CmdletBinding()]
param(
  [string]$RepoRoot='F:\chatgpt\chat_gpt_clone_1_main',
  [string]$BridgeRoot='F:\AAYS_GITHUB_BRIDGE_CLEAN2',
  [string]$SourceBranch='codex/aays-single-runner-v5-20260706',
  [int]$WaitSeconds=180,
  [int]$PollSeconds=5,
  [string]$OutputPath
)
$ErrorActionPreference='Stop'
$TaskId='height-difference-1-official-boundary-elevation-samples-20260720'
$PayloadRevision=9
$IdempotencyKey='height_difference_1-004-20260720'
$ScriptRel='docs/chatgpt_status/topography/shards/height_difference_1/automation/013_height_difference_1_revision_9_height_difference_metric_20260721.py'
$HeartbeatRel='docs/chatgpt_status/aays1/status/061_repo_to_bridge_watch_heartbeat_latest.txt'
$LocalHeartbeat=Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1\heartbeat.txt'
$SlotHeartbeat=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\slots_21\height_difference_1\heartbeat_latest.json'
$ExpectedOutput=Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\011_height_difference_metric_gate_latest.json'
$WebOutput=Join-Path $RepoRoot 'england_map_web\data\aays_21_slots\height_difference_1\existing_watcher_revision_aware_v4_readback_latest.json'
if(-not$OutputPath){$OutputPath=Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\018_revision_aware_recovery_readback_latest.json'}
function ParseKvText([string]$Text){$h=@{};foreach($line in($Text-split"`r?`n")){if($line-match'^\s*([^=]+)=(.*)$'){$h[$matches[1].Trim()]=$matches[2].Trim()}};return$h}
function ParseKvFile([string]$Path){if(!(Test-Path -LiteralPath $Path)){return@{}};return ParseKvText(Get-Content -LiteralPath $Path -Raw -Encoding UTF8)}
function ParseTime([string]$Value){if(!$Value){return$null};try{return[datetime]::ParseExact($Value,'yyyyMMdd_HHmmss',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeLocal)}catch{return$null}}
function Identity([string]$Path){try{$j=Get-Content -LiteralPath $Path -Raw -Encoding UTF8|ConvertFrom-Json;return[ordered]@{task_id=[string]$j.task_id;payload_revision=if($null-ne$j.payload_revision){[int]$j.payload_revision}else{-1};script_path=[string]$j.script_path;idempotency_key=[string]$j.idempotency_key}}catch{return$null}}
function Match($i){return($null-ne$i-and$i.task_id-eq$TaskId-and$i.payload_revision-eq$PayloadRevision-and$i.script_path-eq$ScriptRel-and$i.idempotency_key-eq$IdempotencyKey)}
function Markers{$a=@();foreach($state in@('pending','running','done','processed','failed','error')){$d=Join-Path $BridgeRoot "ai-queue\$state";if(Test-Path $d){foreach($f in@(Get-ChildItem $d -File -ErrorAction SilentlyContinue)){$i=Identity $f.FullName;if($null-ne$i-and$i.task_id-eq$TaskId){$a+=[ordered]@{state=$state;path=$f.FullName;identity=$i;current_revision=(Match $i)}}}}};return@($a)}
function RemoteHb{&git -C $RepoRoot fetch origin $SourceBranch 2>$null|Out-Null;if($LASTEXITCODE-ne0){return@{}};$t=&git -C $RepoRoot show "origin/$SourceBranch`:$HeartbeatRel" 2>$null;if($LASTEXITCODE-ne0){return@{}};return ParseKvText($t-join"`n")}
function HbFacts([hashtable]$h){$t=ParseTime([string]$h['updated_at']);$age=if($t){[math]::Max(0,[int]((Get-Date)-$t).TotalSeconds)}else{$null};return[ordered]@{status=$h['status'];age_seconds=$age;fresh=($age-ne$null-and$age-le180-and[string]$h['status']-eq'WATCHING');source_branch=$h['source_branch'];source_branch_matches=([string]$h['source_branch']-eq$SourceBranch);task_id=$h['task_id'];task_matches=([string]$h['task_id']-eq$TaskId);payload_revision=$h['payload_revision'];revision_matches=([int]$h['payload_revision']-eq$PayloadRevision);script_path=$h['script_path'];script_matches=([string]$h['script_path']-eq$ScriptRel);idempotency_key=$h['idempotency_key'];idempotency_matches=([string]$h['idempotency_key']-eq$IdempotencyKey)}}
function Snapshot{
  $watchers=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.CommandLine-match'aays_repo_to_bridge_watch_aays1\.ps1'})
  $runners=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.CommandLine-match'portable_queue_runner\.ps1'})
  $local=HbFacts(ParseKvFile $LocalHeartbeat);$remote=HbFacts(RemoteHb);$markers=@(Markers)
  $currentActive=@($markers|Where-Object{$_.current_revision-and$_.state-in@('pending','running')})
  $currentSuccess=@($markers|Where-Object{$_.current_revision-and$_.state-in@('done','processed')})
  $currentFailed=@($markers|Where-Object{$_.current_revision-and$_.state-in@('failed','error')})
  $old=@($markers|Where-Object{!$_.current_revision})
  $slot=$null;if(Test-Path $SlotHeartbeat){try{$slot=Get-Content $SlotHeartbeat -Raw -Encoding UTF8|ConvertFrom-Json}catch{}}
  $slotClaimed=($null-ne$slot-and[string]$slot.current_task_id-eq$TaskId-and[string]$slot.state-in@('claimed','running'))
  $output=Test-Path $ExpectedOutput
  $signatureHb=($local.fresh-and$remote.fresh-and$local.source_branch_matches-and$remote.source_branch_matches-and$local.task_matches-and$remote.task_matches-and$local.revision_matches-and$remote.revision_matches-and$local.script_matches-and$remote.script_matches-and$local.idempotency_matches-and$remote.idempotency_matches)
  $blockers=@();if($watchers.Count-ne1){$blockers+='WATCHER_PROCESS_COUNT_NOT_ONE'};if($runners.Count-ne1){$blockers+='RUNNER_PROCESS_COUNT_NOT_ONE'};if(!$signatureHb){$blockers+='LOCAL_OR_REMOTE_HEARTBEAT_SIGNATURE_NOT_FRESH'};if($currentFailed.Count-gt0){$blockers+='CURRENT_REVISION_FAILED_OR_ERROR_MARKER'};if($currentSuccess.Count-gt0-and!$output){$blockers+='CURRENT_REVISION_TERMINAL_MARKER_WITHOUT_OUTPUT'};if($currentActive.Count-eq0-and$currentSuccess.Count-eq0-and!$output){$blockers+='CURRENT_REVISION_NOT_VISIBLE_IN_BRIDGE'}
  $status=if($output){'OFFICIAL_RESULT_AVAILABLE'}elseif($slotClaimed){'SINGLE_RUNNER_CLAIM_OBSERVED'}elseif($blockers.Count-eq0){'REVISION_AWARE_RECOVERY_VERIFIED'}else{'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED'}
  return[ordered]@{schema_version=3;slot_id='height_difference_1';task_id=$TaskId;payload_revision=$PayloadRevision;checked_at=(Get-Date).ToString('o');status=$status;blockers=$blockers;watcher_process_count=$watchers.Count;runner_process_count=$runners.Count;local_heartbeat=$local;remote_heartbeat=$remote;bridge_markers=$markers;current_revision_active_markers=$currentActive;current_revision_success_markers=$currentSuccess;current_revision_failed_markers=$currentFailed;old_revision_markers_ignored=$old;slot_claimed_for_expected_task=$slotClaimed;expected_output_present=$output;new_runner=$false;parallel_runner=$false;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
}
$deadline=(Get-Date).AddSeconds([math]::Max(0,$WaitSeconds));do{$payload=Snapshot;if($payload.status-ne'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED'){break};if((Get-Date)-ge$deadline){break};Start-Sleep -Seconds([math]::Max(1,$PollSeconds))}while($true)
foreach($path in@($OutputPath,$WebOutput)){New-Item -ItemType Directory -Force -Path(Split-Path -Parent $path)|Out-Null;$payload|ConvertTo-Json -Depth 20|Set-Content -LiteralPath $path -Encoding UTF8}
Write-Output($payload|ConvertTo-Json -Depth 20)
if($payload.status-eq'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED'){exit 2};exit 0

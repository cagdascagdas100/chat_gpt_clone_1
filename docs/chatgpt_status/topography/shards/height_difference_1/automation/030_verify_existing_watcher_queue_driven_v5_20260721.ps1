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
$QueueRel='docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json'
$HeartbeatRel='docs/chatgpt_status/aays1/status/061_repo_to_bridge_watch_heartbeat_latest.txt'
$LocalHeartbeat=Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1\heartbeat.txt'
$SlotHeartbeat=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\slots_21\height_difference_1\heartbeat_latest.json'
$IntegrityValidator=Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\automation\028_validate_revision_10_output_integrity_20260721.py'
$IntegrityReadback=Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\020_revision_10_output_integrity_readback_latest.json'
$WebOutput=Join-Path $RepoRoot 'england_map_web\data\aays_21_slots\height_difference_1\queue_driven_watcher_recovery_v5_readback_latest.json'
if(-not$OutputPath){$OutputPath=Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\022_queue_driven_watcher_recovery_readback_latest.json'}
function ParseKvText([string]$Text){$h=@{};foreach($line in($Text-split"`r?`n")){if($line-match'^\s*([^=]+)=(.*)$'){$h[$matches[1].Trim()]=$matches[2].Trim()}};return$h}
function ParseKvFile([string]$Path){if(!(Test-Path -LiteralPath $Path)){return@{}};return ParseKvText(Get-Content -LiteralPath $Path -Raw -Encoding UTF8)}
function ParseTime([string]$Value){if(!$Value){return$null};try{return[datetime]::ParseExact($Value,'yyyyMMdd_HHmmss',[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeLocal)}catch{return$null}}
function QueueIdentity($j){if($null-eq$j){return$null};return[ordered]@{task_id=[string]$j.task_id;payload_revision=if($null-ne$j.payload_revision){[int]$j.payload_revision}else{-1};attempt_id=[string]$j.attempt_id;idempotency_key=[string]$j.idempotency_key;script_path=[string]$j.script_path;script_blob_sha=[string]$j.script_blob_sha}}
function Same($a,$b){return($null-ne$a-and$null-ne$b-and$a.task_id-eq$b.task_id-and$a.payload_revision-eq$b.payload_revision-and$a.attempt_id-eq$b.attempt_id-and$a.idempotency_key-eq$b.idempotency_key-and$a.script_path-eq$b.script_path-and$a.script_blob_sha-eq$b.script_blob_sha)}
function ReadId($p){try{return QueueIdentity(Get-Content -LiteralPath $p -Raw -Encoding UTF8|ConvertFrom-Json)}catch{return$null}}
function Markers($expected){$a=@();foreach($state in@('pending','running','done','processed','failed','error')){$d=Join-Path $BridgeRoot "ai-queue\$state";if(Test-Path $d){foreach($f in@(Get-ChildItem $d -File -ErrorAction SilentlyContinue)){$i=ReadId $f.FullName;if($null-ne$i-and$i.task_id-eq$expected.task_id){$a+=[ordered]@{state=$state;path=$f.FullName;identity=$i;current_revision=(Same $i $expected)}}}}};return@($a)}
function RemoteHb{&git -C $RepoRoot fetch origin $SourceBranch 2>$null|Out-Null;if($LASTEXITCODE-ne0){return@{}};$t=&git -C $RepoRoot show "origin/$SourceBranch`:$HeartbeatRel" 2>$null;if($LASTEXITCODE-ne0){return@{}};return ParseKvText($t-join"`n")}
function HbFacts([hashtable]$h,$expected){$t=ParseTime([string]$h['updated_at']);$age=if($t){[math]::Max(0,[int]((Get-Date)-$t).TotalSeconds)}else{$null};return[ordered]@{status=$h['status'];updated_at=$h['updated_at'];age_seconds=$age;fresh=($age-ne$null-and$age-le180-and[string]$h['status']-eq'WATCHING');source_branch=$h['source_branch'];source_branch_matches=([string]$h['source_branch']-eq$SourceBranch);task_id=$h['task_id'];task_matches=([string]$h['task_id']-eq$expected.task_id);payload_revision=$h['payload_revision'];revision_matches=([int]$h['payload_revision']-eq$expected.payload_revision);attempt_id=$h['attempt_id'];attempt_matches=([string]$h['attempt_id']-eq$expected.attempt_id);idempotency_key=$h['idempotency_key'];idempotency_matches=([string]$h['idempotency_key']-eq$expected.idempotency_key);script_path=$h['script_path'];script_matches=([string]$h['script_path']-eq$expected.script_path);script_blob_sha=$h['script_blob_sha'];blob_matches=([string]$h['script_blob_sha']-eq$expected.script_blob_sha);script_sha256=$h['script_sha256']}}
function Snapshot{
  $queuePath=Join-Path $RepoRoot($QueueRel-replace'/','\')
  $queue=$null;try{$queue=Get-Content -LiteralPath $queuePath -Raw -Encoding UTF8|ConvertFrom-Json}catch{}
  $expected=QueueIdentity $queue
  $watchers=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.CommandLine-match'aays_repo_to_bridge_watch_aays1\.ps1'})
  $runners=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.CommandLine-match'portable_queue_runner\.ps1'})
  $markers=if($expected){@(Markers $expected)}else{@()}
  $active=@($markers|Where-Object{$_.current_revision-and$_.state-in@('pending','running')})
  $success=@($markers|Where-Object{$_.current_revision-and$_.state-in@('done','processed')})
  $failed=@($markers|Where-Object{$_.current_revision-and$_.state-in@('failed','error')})
  $local=if($expected){HbFacts(ParseKvFile $LocalHeartbeat)$expected}else{@{}}
  $remote=if($expected){HbFacts(RemoteHb)$expected}else{@{}}
  $scriptPath=if($expected){Join-Path $RepoRoot($expected.script_path-replace'/','\')}else{$null}
  $scriptBlob=if($scriptPath-and(Test-Path $scriptPath)){(git -C $RepoRoot hash-object -- $scriptPath|Select-Object -First 1).Trim()}else{$null}
  $scriptSha=if($scriptPath-and(Test-Path $scriptPath)){(Get-FileHash -Algorithm SHA256 -LiteralPath $scriptPath).Hash.ToLowerInvariant()}else{$null}
  $slot=$null;if(Test-Path $SlotHeartbeat){try{$slot=Get-Content $SlotHeartbeat -Raw -Encoding UTF8|ConvertFrom-Json}catch{}}
  $slotClaimed=($null-ne$slot-and$null-ne$expected-and[string]$slot.current_task_id-eq$expected.task_id-and[string]$slot.state-in@('claimed','running'))
  $expectedOutput=if($queue-and$queue.expected_outputs){Join-Path $RepoRoot([string]$queue.expected_outputs[0]-replace'/','\')}else{$null}
  $outputPresent=($expectedOutput-and(Test-Path $expectedOutput))
  $integrityStatus=$null;if(Test-Path $IntegrityReadback){try{$integrityStatus=[string](Get-Content $IntegrityReadback -Raw -Encoding UTF8|ConvertFrom-Json).status}catch{}}
  $blockers=@();if($null-eq$expected){$blockers+='ACTIVE_QUEUE_NOT_READABLE'};if($watchers.Count-ne1){$blockers+='WATCHER_PROCESS_COUNT_NOT_ONE'};if($runners.Count-ne1){$blockers+='RUNNER_PROCESS_COUNT_NOT_ONE'};if($expected-and$scriptBlob-ne$expected.script_blob_sha){$blockers+='ACTIVE_SCRIPT_BLOB_SHA_MISMATCH'};if($expected-and(!$local.fresh-or!$remote.fresh-or!$local.source_branch_matches-or!$remote.source_branch_matches-or!$local.task_matches-or!$remote.task_matches-or!$local.revision_matches-or!$remote.revision_matches-or!$local.attempt_matches-or!$remote.attempt_matches-or!$local.idempotency_matches-or!$remote.idempotency_matches-or!$local.script_matches-or!$remote.script_matches-or!$local.blob_matches-or!$remote.blob_matches-or$local.script_sha256-ne$scriptSha-or$remote.script_sha256-ne$scriptSha)){$blockers+='LOCAL_OR_REMOTE_HEARTBEAT_IDENTITY_NOT_FRESH'};if($failed.Count-gt0){$blockers+='CURRENT_REVISION_FAILED_OR_ERROR_MARKER'};if($success.Count-gt0-and!$outputPresent){$blockers+='CURRENT_REVISION_TERMINAL_WITHOUT_OUTPUT'};if($active.Count-eq0-and$success.Count-eq0-and!$outputPresent){$blockers+='CURRENT_REVISION_NOT_VISIBLE_IN_BRIDGE'};if($outputPresent-and$integrityStatus-ne'REVISION_10_OUTPUT_INTEGRITY_VERIFIED'){$blockers+='OUTPUT_PRESENT_BUT_INTEGRITY_NOT_VERIFIED'}
  $status=if($outputPresent-and$integrityStatus-eq'REVISION_10_OUTPUT_INTEGRITY_VERIFIED'){'OFFICIAL_RESULT_INTEGRITY_VERIFIED'}elseif($slotClaimed){'SINGLE_RUNNER_CLAIM_OBSERVED'}elseif($blockers.Count-eq0){'QUEUE_DRIVEN_RECOVERY_VERIFIED_TASK_VISIBLE'}else{'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED'}
  return[ordered]@{schema_version=5;slot_id='height_difference_1';checked_at=(Get-Date).ToString('o');status=$status;blockers=$blockers;queue_identity=$expected;script_blob_sha_actual=$scriptBlob;script_sha256_actual=$scriptSha;watcher_process_count=$watchers.Count;runner_process_count=$runners.Count;local_heartbeat=$local;remote_heartbeat=$remote;bridge_markers=$markers;current_revision_active_markers=$active;current_revision_success_markers=$success;current_revision_failed_markers=$failed;slot_claimed_for_expected_task=$slotClaimed;expected_output_present=$outputPresent;integrity_readback_status=$integrityStatus;process_started=$false;process_stopped=$false;queue_modified=$false;new_runner=$false;parallel_runner=$false;final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false}
}
$deadline=(Get-Date).AddSeconds([math]::Max(0,$WaitSeconds));do{$payload=Snapshot;if($payload.status-ne'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED'){break};if((Get-Date)-ge$deadline){break};Start-Sleep -Seconds([math]::Max(1,$PollSeconds))}while($true)
foreach($path in@($OutputPath,$WebOutput)){New-Item -ItemType Directory -Force -Path(Split-Path -Parent $path)|Out-Null;$payload|ConvertTo-Json -Depth 22|Set-Content -LiteralPath $path -Encoding UTF8}
Write-Output($payload|ConvertTo-Json -Depth 22)
if($payload.status-eq'RECOVERY_VERIFICATION_PENDING_OR_BLOCKED'){exit 2};exit 0

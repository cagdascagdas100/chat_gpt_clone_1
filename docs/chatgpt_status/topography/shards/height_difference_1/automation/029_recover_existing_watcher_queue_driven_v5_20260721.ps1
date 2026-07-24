[CmdletBinding()]
param(
  [string]$RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main',
  [string]$BridgeRoot = 'F:\AAYS_GITHUB_BRIDGE_CLEAN2',
  [string]$SourceBranch = 'codex/aays-single-runner-v5-20260706',
  [string]$WatchRepo = 'F:\chatgpt\aays1_repo_to_bridge_watch_worktree',
  [switch]$Apply,
  [switch]$RestoreRunner,
  [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$QueueRel = 'docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json'
$TopographyQueueRel = 'docs/chatgpt_status/topography/queue/height_difference_1_004_official_boundary_numeric_samples_20260720.v3.task.json'
$WatcherScript = Join-Path $BridgeRoot 'ai-task-scripts\aays_repo_to_bridge_watch_aays1.ps1'
$RunnerScript = Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1'
$StateDir = Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1'
$PendingDir = Join-Path $BridgeRoot 'ai-queue\pending'
$RunningDir = Join-Path $BridgeRoot 'ai-queue\running'
if (-not $OutputPath) {
  $OutputPath = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\021_queue_driven_watcher_recovery_preflight_latest.json'
}

function Git([string[]]$Args,[string]$Cwd=$RepoRoot) {
  $result = & git -C $Cwd @Args 2>&1
  if ($LASTEXITCODE -ne 0) { throw "git failed: git -C $Cwd $($Args -join ' ')`n$result" }
  return @($result)
}
function Read-JsonText([string]$Text) {
  try { return ($Text | ConvertFrom-Json) } catch { return $null }
}
function Read-QueueFromRef([string]$Ref) {
  $text = & git -C $RepoRoot show "$Ref`:$QueueRel" 2>$null
  if ($LASTEXITCODE -ne 0) { return $null }
  return Read-JsonText ($text -join "`n")
}
function Identity($Json) {
  if ($null -eq $Json) { return $null }
  return [ordered]@{
    task_id = [string]$Json.task_id
    payload_revision = if ($null -ne $Json.payload_revision) { [int]$Json.payload_revision } else { -1 }
    attempt_id = [string]$Json.attempt_id
    idempotency_key = [string]$Json.idempotency_key
    script_path = [string]$Json.script_path
    script_blob_sha = [string]$Json.script_blob_sha
  }
}
function Identity-Matches($A,$B) {
  return ($null -ne $A -and $null -ne $B -and
    $A.task_id -eq $B.task_id -and
    $A.payload_revision -eq $B.payload_revision -and
    $A.attempt_id -eq $B.attempt_id -and
    $A.idempotency_key -eq $B.idempotency_key -and
    $A.script_path -eq $B.script_path -and
    $A.script_blob_sha -eq $B.script_blob_sha)
}
function Read-IdentityFile([string]$Path) {
  try { return Identity (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json) } catch { return $null }
}
function Marker-Facts($Expected) {
  $facts = @()
  foreach ($state in @('pending','running','done','processed','failed','error')) {
    $dir = Join-Path $BridgeRoot "ai-queue\$state"
    if (!(Test-Path -LiteralPath $dir)) { continue }
    foreach ($file in @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue)) {
      $identity = Read-IdentityFile $file.FullName
      if ($null -ne $identity -and $identity.task_id -eq $Expected.task_id) {
        $facts += [ordered]@{state=$state;path=$file.FullName;identity=$identity;current_revision=(Identity-Matches $identity $Expected)}
      }
    }
  }
  return @($facts)
}
function Watchers { return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match 'aays_repo_to_bridge_watch_aays1\.ps1'} | Select-Object ProcessId,Name,CommandLine) }
function Runners { return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match 'portable_queue_runner\.ps1'} | Select-Object ProcessId,Name,CommandLine) }
function Emit([System.Collections.IDictionary]$Payload) {
  $Payload.output_path=$OutputPath
  $Payload.final_ready=$false;$Payload.product_final_ready=$false;$Payload.fake_data=$false;$Payload.db_write=$false;$Payload.migration=$false;$Payload.production_deploy=$false
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
  $Payload | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
  Write-Output ($Payload | ConvertTo-Json -Depth 20)
}

if (!(Test-Path -LiteralPath $RepoRoot)) { throw "Repo root not found: $RepoRoot" }
if (!(Test-Path -LiteralPath $BridgeRoot)) { throw "Bridge root not found: $BridgeRoot" }
Git @('fetch','origin',$SourceBranch) | Out-Null
$SourceRef = "origin/$SourceBranch"
$Queue = Read-QueueFromRef $SourceRef
if ($null -eq $Queue) { throw 'SOURCE_WATCHED_QUEUE_NOT_READABLE' }
$Expected = Identity $Queue
$ExpectedOutputRel = [string]$Queue.expected_outputs[0]
$RequiredFiles = @($QueueRel,$TopographyQueueRel,[string]$Queue.script_path,[string]$Queue.validation_path,[string]$Queue.output_integrity_validator,'docs/chatgpt_status/topography/shards/height_difference_1/automation/012_height_difference_1_revision_8_entry_20260721.py','docs/chatgpt_status/topography/shards/height_difference_1/automation/011_height_difference_1_revision_8_geometry_datum_quality_gate_20260721.py.gz.b64','docs/chatgpt_status/topography/shards/height_difference_1/automation/010_height_difference_1_revision_7_bulk_gml_gate_20260721.py')
$Presence=[ordered]@{}
foreach($rel in $RequiredFiles){& git -C $RepoRoot cat-file -e "$SourceRef`:$rel" 2>$null;$Presence[$rel]=($LASTEXITCODE -eq 0)}
$ScriptBlob = (& git -C $RepoRoot rev-parse "$SourceRef`:$($Expected.script_path)" 2>$null | Select-Object -First 1).Trim()
$watchers=@(Watchers);$runners=@(Runners)
$runningFiles=if(Test-Path -LiteralPath $RunningDir){@(Get-ChildItem -LiteralPath $RunningDir -File -ErrorAction SilentlyContinue)}else{@()}
$markers=@(Marker-Facts $Expected)
$currentFailed=@($markers|Where-Object{$_.current_revision-and$_.state-in@('failed','error')})
$currentTerminal=@($markers|Where-Object{$_.current_revision-and$_.state-in@('done','processed')})
$currentActive=@($markers|Where-Object{$_.current_revision-and$_.state-in@('pending','running')})
$ExpectedOutput=Join-Path $RepoRoot ($ExpectedOutputRel -replace '/','\')
$blockers=@()
foreach($rel in $RequiredFiles){if(!$Presence[$rel]){$blockers+="SOURCE_ASSET_MISSING:$rel"}}
if($ScriptBlob -ne $Expected.script_blob_sha){$blockers+='SOURCE_SCRIPT_BLOB_SHA_MISMATCH'}
if($watchers.Count -gt 1){$blockers+='MULTIPLE_WATCHER_PROCESSES_DETECTED'}
if($runners.Count -gt 1){$blockers+='MULTIPLE_RUNNER_PROCESSES_DETECTED'}
if($runningFiles.Count -gt 0){$blockers+='BRIDGE_RUNNING_TASK_PRESENT_RECOVERY_DEFERRED'}
if($currentFailed.Count -gt 0){$blockers+='CURRENT_REVISION_FAILED_OR_ERROR_MARKER_REQUIRES_OPERATOR_POLICY'}
if($currentTerminal.Count -gt 0 -and !(Test-Path -LiteralPath $ExpectedOutput)){$blockers+='CURRENT_REVISION_TERMINAL_MARKER_WITHOUT_EXPECTED_OUTPUT'}
if($RestoreRunner -and !(Test-Path -LiteralPath $RunnerScript)){$blockers+='CANONICAL_RUNNER_SCRIPT_MISSING'}
$preflight=[ordered]@{schema_version=5;slot_id='height_difference_1';source_branch=$SourceBranch;queue_path=$QueueRel;expected_identity=$Expected;source_script_blob_sha=$ScriptBlob;required_source_assets=$Presence;watcher_process_count=$watchers.Count;runner_process_count=$runners.Count;bridge_running_file_count=$runningFiles.Count;bridge_markers=$markers;current_active_markers=$currentActive;current_failed_markers=$currentFailed;current_terminal_markers=$currentTerminal;apply_requested=[bool]$Apply;restore_existing_runner_requested=[bool]$RestoreRunner;blockers=$blockers;queue_driven_identity=$true;all_queue_glob_copy=$false;shared_control_sync_forbidden=$true;existing_runner_stop_forbidden=$true;new_runner=$false;parallel_runner=$false}
if($blockers.Count -gt 0){$preflight.status='BLOCKED_QUEUE_DRIVEN_RECOVERY_PREFLIGHT';Emit $preflight;exit 2}
if(!$Apply){$preflight.status='READY_FOR_QUEUE_DRIVEN_RECOVERY_APPLY';$preflight.required_command="powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Apply";$preflight.restore_runner_command="powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Apply -RestoreRunner";Emit $preflight;exit 0}

foreach($p in $watchers){Stop-Process -Id $p.ProcessId -Force}
Start-Sleep -Seconds 2
if(!(Test-Path -LiteralPath $WatchRepo)){Git @('worktree','add','--detach',$WatchRepo,$SourceRef)|Out-Null}else{Git @('fetch','origin',$SourceBranch) $WatchRepo|Out-Null;Git @('reset','--hard',$SourceRef) $WatchRepo|Out-Null}
$restoreLiteral=if($RestoreRunner){'$true'}else{'$false'}
$template=@'
$ErrorActionPreference='Continue'
$RepoRoot='__REPO_ROOT__';$BridgeRoot='__BRIDGE_ROOT__';$WatchRepo='__WATCH_REPO__';$SourceBranch='__SOURCE_BRANCH__';$RestoreRunner=__RESTORE_RUNNER__
$QueueRel='docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json';$TopographyQueueRel='docs/chatgpt_status/topography/queue/height_difference_1_004_official_boundary_numeric_samples_20260720.v3.task.json'
$StateDir=Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1';$PendingDir=Join-Path $BridgeRoot 'ai-queue\pending';$RunnerScript=Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1';$HeartbeatRel='docs/chatgpt_status/aays1/status/061_repo_to_bridge_watch_heartbeat_latest.txt';$HeartbeatPushSeconds=300
New-Item -ItemType Directory -Force -Path $StateDir,$PendingDir|Out-Null
function QIdentity($j){if($null-eq$j){return$null};return[ordered]@{task_id=[string]$j.task_id;payload_revision=if($null-ne$j.payload_revision){[int]$j.payload_revision}else{-1};attempt_id=[string]$j.attempt_id;idempotency_key=[string]$j.idempotency_key;script_path=[string]$j.script_path;script_blob_sha=[string]$j.script_blob_sha}}
function Same($a,$b){return($null-ne$a-and$null-ne$b-and$a.task_id-eq$b.task_id-and$a.payload_revision-eq$b.payload_revision-and$a.attempt_id-eq$b.attempt_id-and$a.idempotency_key-eq$b.idempotency_key-and$a.script_path-eq$b.script_path-and$a.script_blob_sha-eq$b.script_blob_sha)}
function ReadId($p){try{return QIdentity(Get-Content -LiteralPath $p -Raw -Encoding UTF8|ConvertFrom-Json)}catch{return$null}}
function Markers($expected){$a=@();foreach($state in@('pending','running','done','processed','failed','error')){$d=Join-Path $BridgeRoot "ai-queue\$state";if(Test-Path $d){foreach($f in@(Get-ChildItem $d -File -ErrorAction SilentlyContinue)){$i=ReadId $f.FullName;if($null-ne$i-and$i.task_id-eq$expected.task_id){$a+=[ordered]@{state=$state;path=$f.FullName;identity=$i;current_revision=(Same $i $expected)}}}}};return@($a)}
function SyncDir($rel){$s=Join-Path $WatchRepo($rel-replace'/','\');$d=Join-Path $RepoRoot($rel-replace'/','\');if(!(Test-Path $s)){throw "SOURCE_DIRECTORY_MISSING:$rel"};New-Item -ItemType Directory -Force -Path $d|Out-Null;Copy-Item -Recurse -Force -ErrorAction Stop (Join-Path $s '*') $d}
function SyncFile($rel){$s=Join-Path $WatchRepo($rel-replace'/','\');$d=Join-Path $RepoRoot($rel-replace'/','\');if(!(Test-Path $s)){throw "SOURCE_FILE_MISSING:$rel"};New-Item -ItemType Directory -Force -Path(Split-Path -Parent $d)|Out-Null;Copy-Item -Force -ErrorAction Stop $s $d}
function EnsureRunner{$r=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.CommandLine-match'portable_queue_runner\.ps1'});if($r.Count-gt1){throw'MULTIPLE_RUNNER_PROCESSES_DETECTED'};if($r.Count-eq0-and$RestoreRunner){if(!(Test-Path $RunnerScript)){throw'CANONICAL_RUNNER_SCRIPT_MISSING'};Start-Process powershell -ArgumentList '-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File',$RunnerScript}}
function PushHb($text){$last=Join-Path $StateDir 'last_source_heartbeat_push.txt';$now=Get-Date;if(Test-Path $last){try{if(($now-[datetime](Get-Content $last -Raw)).TotalSeconds-lt$HeartbeatPushSeconds){return}}catch{}};for($n=1;$n-le2;$n++){git -C $WatchRepo fetch origin $SourceBranch|Out-Null;git -C $WatchRepo reset --hard "origin/$SourceBranch"|Out-Null;$sp=Join-Path $WatchRepo($HeartbeatRel-replace'/','\');New-Item -ItemType Directory -Force -Path(Split-Path -Parent $sp)|Out-Null;$text|Set-Content -LiteralPath $sp -Encoding UTF8;git -C $WatchRepo add -- $HeartbeatRel|Out-Null;$chg=git -C $WatchRepo status --porcelain -- $HeartbeatRel;if(!$chg){break};git -C $WatchRepo commit -m 'Update aays1 queue-driven watcher heartbeat'|Out-Null;git -C $WatchRepo push origin "HEAD:$SourceBranch"|Out-Null;if($LASTEXITCODE-eq0){break};if($n-eq2){throw'SOURCE_HEARTBEAT_PUSH_FAILED_AFTER_RETRY'}};$now.ToString('o')|Set-Content -LiteralPath $last -Encoding UTF8}
while($true){$stamp=Get-Date -Format'yyyyMMdd_HHmmss';$copied=0;try{git -C $WatchRepo fetch origin $SourceBranch|Out-Null;git -C $WatchRepo reset --hard "origin/$SourceBranch"|Out-Null;SyncDir 'docs/chatgpt_status/topography/shards/height_difference_1/automation';SyncDir 'docs/chatgpt_status/topography/shards/height_difference_1/validation';SyncFile $QueueRel;SyncFile $TopographyQueueRel;$queuePath=Join-Path $RepoRoot($QueueRel-replace'/','\');$q=Get-Content -LiteralPath $queuePath -Raw -Encoding UTF8|ConvertFrom-Json;$expected=QIdentity $q;$script=Join-Path $RepoRoot($expected.script_path-replace'/','\');if(!(Test-Path $script)){throw'ACTIVE_SCRIPT_MISSING'};$blob=(git -C $RepoRoot hash-object -- $script|Select-Object -First 1).Trim();if($blob-ne$expected.script_blob_sha){throw'ACTIVE_SCRIPT_BLOB_SHA_MISMATCH'};$m=@(Markers $expected);$failed=@($m|Where-Object{$_.current_revision-and$_.state-in@('failed','error')});$terminal=@($m|Where-Object{$_.current_revision-and$_.state-in@('done','processed')});$active=@($m|Where-Object{$_.current_revision-and$_.state-in@('pending','running')});$expectedOutput=Join-Path $RepoRoot([string]$q.expected_outputs[0]-replace'/','\');if($failed.Count-gt0){throw'CURRENT_REVISION_FAILED_OR_ERROR_MARKER'};if($terminal.Count-gt0-and!(Test-Path $expectedOutput)){throw'CURRENT_REVISION_TERMINAL_WITHOUT_OUTPUT'};if($active.Count-eq0-and$terminal.Count-eq0){Copy-Item -Force -ErrorAction Stop $queuePath (Join-Path $PendingDir([IO.Path]::GetFileName($queuePath)));$copied=1};EnsureRunner;$scriptSha=(Get-FileHash -Algorithm SHA256 -LiteralPath $script).Hash.ToLowerInvariant();$hb="status=WATCHING`npage_key=aays1`nsource_branch=$SourceBranch`ntask_id=$($expected.task_id)`npayload_revision=$($expected.payload_revision)`nattempt_id=$($expected.attempt_id)`nidempotency_key=$($expected.idempotency_key)`nscript_path=$($expected.script_path)`nscript_blob_sha=$($expected.script_blob_sha)`nscript_sha256=$scriptSha`nexact_task_filter=true`nqueue_driven_identity=true`ncopied_this_loop=$copied`nupdated_at=$stamp`nfinal_ready=false";$hb|Set-Content -LiteralPath(Join-Path $StateDir 'heartbeat.txt')-Encoding UTF8;PushHb $hb}catch{$err="status=WATCH_ERROR`npage_key=aays1`nsource_branch=$SourceBranch`nerror=$($_.Exception.Message)`nupdated_at=$stamp`nfinal_ready=false";$err|Set-Content -LiteralPath(Join-Path $StateDir 'last_error.txt')-Encoding UTF8;try{PushHb $err}catch{}};Start-Sleep -Seconds 60}
'@
$watcherText=$template.Replace('__REPO_ROOT__',$RepoRoot).Replace('__BRIDGE_ROOT__',$BridgeRoot).Replace('__WATCH_REPO__',$WatchRepo).Replace('__SOURCE_BRANCH__',$SourceBranch).Replace('__RESTORE_RUNNER__',$restoreLiteral)
New-Item -ItemType Directory -Force -Path(Split-Path -Parent $WatcherScript),$StateDir,$PendingDir|Out-Null
$watcherText|Set-Content -LiteralPath $WatcherScript -Encoding UTF8
$watcher=Start-Process powershell -ArgumentList '-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File',$WatcherScript -PassThru
$runnerAfter=@(Runners)
Emit([ordered]@{schema_version=5;slot_id='height_difference_1';status=if($runnerAfter.Count-eq1){'QUEUE_DRIVEN_WATCHER_AND_EXISTING_SINGLE_RUNNER_RECOVERED'}else{'QUEUE_DRIVEN_WATCHER_RECOVERED_EXISTING_RUNNER_RESTORE_PENDING'};expected_identity=$Expected;watcher_process_id=$watcher.Id;runner_process_count=$runnerAfter.Count;queue_driven_identity=$true;script_blob_verified=$true;existing_runner_stopped=$false;new_runner=$false;parallel_runner=$false})
exit 0

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
$TaskId = 'height-difference-1-official-boundary-elevation-samples-20260720'
$PayloadRevision = 9
$IdempotencyKey = 'height_difference_1-004-20260720'
$QueueRel = 'docs/chatgpt_status/aays1/queue/aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json'
$TopographyQueueRel = 'docs/chatgpt_status/topography/queue/height_difference_1_004_official_boundary_numeric_samples_20260720.v3.task.json'
$ScriptRel = 'docs/chatgpt_status/topography/shards/height_difference_1/automation/013_height_difference_1_revision_9_height_difference_metric_20260721.py'
$RequiredFiles = @(
  $QueueRel,
  $TopographyQueueRel,
  $ScriptRel,
  'docs/chatgpt_status/topography/shards/height_difference_1/automation/012_height_difference_1_revision_8_entry_20260721.py',
  'docs/chatgpt_status/topography/shards/height_difference_1/automation/011_height_difference_1_revision_8_geometry_datum_quality_gate_20260721.py.gz.b64',
  'docs/chatgpt_status/topography/shards/height_difference_1/automation/010_height_difference_1_revision_7_bulk_gml_gate_20260721.py'
)
$AssetDirs = @(
  'docs/chatgpt_status/topography/shards/height_difference_1/automation',
  'docs/chatgpt_status/topography/shards/height_difference_1/validation'
)
$QueueFiles = @($QueueRel,$TopographyQueueRel)
$ExpectedOutput = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\011_height_difference_metric_gate_latest.json'
$RunnerScript = Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1'
$WatcherScript = Join-Path $BridgeRoot 'ai-task-scripts\aays_repo_to_bridge_watch_aays1.ps1'
$StateDir = Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1'
$RunningDir = Join-Path $BridgeRoot 'ai-queue\running'
$PendingDir = Join-Path $BridgeRoot 'ai-queue\pending'
if (-not $OutputPath) { $OutputPath = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\017_revision_aware_recovery_preflight_latest.json' }

function Invoke-Git([string[]]$Args,[string]$Cwd=$RepoRoot) {
  $result = & git -C $Cwd @Args 2>&1
  if ($LASTEXITCODE -ne 0) { throw "git failed: git -C $Cwd $($Args -join ' ')`n$result" }
  return @($result)
}
function Test-GitPath([string]$Ref,[string]$Path) {
  & git -C $RepoRoot cat-file -e "$Ref`:$Path" 2>$null
  return ($LASTEXITCODE -eq 0)
}
function Read-Identity([string]$Path) {
  try {
    $j = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    return [ordered]@{
      task_id = [string]$j.task_id
      payload_revision = if ($null -ne $j.payload_revision) { [int]$j.payload_revision } else { -1 }
      script_path = [string]$j.script_path
      idempotency_key = [string]$j.idempotency_key
    }
  } catch { return $null }
}
function Identity-Matches($Identity) {
  return ($null -ne $Identity -and
    $Identity.task_id -eq $TaskId -and
    $Identity.payload_revision -eq $PayloadRevision -and
    $Identity.script_path -eq $ScriptRel -and
    $Identity.idempotency_key -eq $IdempotencyKey)
}
function Get-MarkerFacts {
  $facts = @()
  foreach ($state in @('pending','running','done','processed','failed','error')) {
    $dir = Join-Path $BridgeRoot "ai-queue\$state"
    if (!(Test-Path -LiteralPath $dir)) { continue }
    foreach ($file in @(Get-ChildItem -LiteralPath $dir -File -ErrorAction SilentlyContinue)) {
      $identity = Read-Identity $file.FullName
      if ($null -ne $identity -and $identity.task_id -eq $TaskId) {
        $facts += [ordered]@{ state=$state; path=$file.FullName; identity=$identity; current_revision=(Identity-Matches $identity) }
      }
    }
  }
  return @($facts)
}
function Emit([System.Collections.IDictionary]$Payload) {
  $Payload.output_path=$OutputPath; $Payload.final_ready=$false; $Payload.product_final_ready=$false
  $Payload.fake_data=$false; $Payload.db_write=$false; $Payload.migration=$false; $Payload.production_deploy=$false
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
  $Payload | ConvertTo-Json -Depth 18 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
  Write-Output ($Payload | ConvertTo-Json -Depth 18)
}
function Get-Watchers { return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'aays_repo_to_bridge_watch_aays1\.ps1' } | Select-Object ProcessId,Name,CommandLine) }
function Get-Runners { return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'portable_queue_runner\.ps1' } | Select-Object ProcessId,Name,CommandLine) }

if (!(Test-Path -LiteralPath $RepoRoot)) { throw "Repo root not found: $RepoRoot" }
if (!(Test-Path -LiteralPath $BridgeRoot)) { throw "Bridge root not found: $BridgeRoot" }
Invoke-Git @('fetch','origin',$SourceBranch) | Out-Null
$SourceRef = "origin/$SourceBranch"
$presence=[ordered]@{}; foreach($rel in $RequiredFiles){$presence[$rel]=Test-GitPath $SourceRef $rel}
$watchers=@(Get-Watchers); $runners=@(Get-Runners)
$runningFiles=if(Test-Path -LiteralPath $RunningDir){@(Get-ChildItem -LiteralPath $RunningDir -File -ErrorAction SilentlyContinue)}else{@()}
$markers=@(Get-MarkerFacts)
$currentFailed=@($markers | Where-Object { $_.current_revision -and $_.state -in @('failed','error') })
$currentTerminal=@($markers | Where-Object { $_.current_revision -and $_.state -in @('done','processed') })
$blockers=@()
foreach($rel in $RequiredFiles){if(!$presence[$rel]){$blockers+="SOURCE_ASSET_MISSING:$rel"}}
if($watchers.Count -gt 1){$blockers+='MULTIPLE_WATCHER_PROCESSES_DETECTED'}
if($runners.Count -gt 1){$blockers+='MULTIPLE_RUNNER_PROCESSES_DETECTED'}
if($runningFiles.Count -gt 0){$blockers+='BRIDGE_RUNNING_TASK_PRESENT_RECOVERY_DEFERRED'}
if($currentFailed.Count -gt 0){$blockers+='CURRENT_REVISION_FAILED_OR_ERROR_MARKER_REQUIRES_OPERATOR_POLICY'}
if($currentTerminal.Count -gt 0 -and !(Test-Path -LiteralPath $ExpectedOutput)){$blockers+='CURRENT_REVISION_TERMINAL_MARKER_WITHOUT_EXPECTED_OUTPUT'}
if($RestoreRunner -and !(Test-Path -LiteralPath $RunnerScript)){$blockers+='CANONICAL_RUNNER_SCRIPT_MISSING'}
$preflight=[ordered]@{
  schema_version=4; slot_id='height_difference_1'; task_id=$TaskId; payload_revision=$PayloadRevision
  idempotency_key=$IdempotencyKey; script_path=$ScriptRel; source_branch=$SourceBranch; source_ref=$SourceRef
  apply_requested=[bool]$Apply; restore_existing_runner_requested=[bool]$RestoreRunner
  required_source_assets=$presence; watcher_process_count=$watchers.Count; runner_process_count=$runners.Count
  bridge_running_file_count=$runningFiles.Count; bridge_markers=$markers; blockers=$blockers
  old_revision_markers_ignored=$true; current_failed_auto_retry_forbidden=$true
  terminal_without_output_forbidden=$true; shared_control_sync_forbidden=$true
  existing_runner_stop_forbidden=$true; new_runner=$false; parallel_runner=$false
}
if($blockers.Count -gt 0){$preflight.status='BLOCKED_REVISION_AWARE_RECOVERY_PREFLIGHT';Emit $preflight;exit 2}
if(!$Apply){$preflight.status='READY_FOR_REVISION_AWARE_RECOVERY_APPLY';$preflight.required_command="powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Apply";$preflight.restore_runner_command="powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Apply -RestoreRunner";Emit $preflight;exit 0}

foreach($p in $watchers){Stop-Process -Id $p.ProcessId -Force}
Start-Sleep -Seconds 2
if(!(Test-Path -LiteralPath $WatchRepo)){Invoke-Git @('worktree','add','--detach',$WatchRepo,$SourceRef)|Out-Null}else{Invoke-Git @('fetch','origin',$SourceBranch) $WatchRepo|Out-Null;Invoke-Git @('reset','--hard',$SourceRef) $WatchRepo|Out-Null}

$restoreLiteral=if($RestoreRunner){'$true'}else{'$false'}
$assetLiteral=($AssetDirs|ForEach-Object{"'$_'"})-join ','
$queueLiteral=($QueueFiles|ForEach-Object{"'$_'"})-join ','
$requiredLiteral=($RequiredFiles|ForEach-Object{"'$_'"})-join ','
$template=@'
$ErrorActionPreference='Continue'
$RepoRoot='__REPO_ROOT__';$BridgeRoot='__BRIDGE_ROOT__';$WatchRepo='__WATCH_REPO__';$SourceBranch='__SOURCE_BRANCH__'
$TaskId='__TASK_ID__';$PayloadRevision=__PAYLOAD_REVISION__;$IdempotencyKey='__IDEMPOTENCY_KEY__';$ScriptRel='__SCRIPT_REL__';$RestoreRunner=__RESTORE_RUNNER__
$AssetDirs=@(__ASSET_DIRS__);$QueueFiles=@(__QUEUE_FILES__);$RequiredFiles=@(__REQUIRED_FILES__)
$QueuePath=Join-Path $WatchRepo 'docs\chatgpt_status\aays1\queue\aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json'
$ExpectedOutput=Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_1\runner_outputs\011_height_difference_metric_gate_latest.json'
$RunnerScript=Join-Path $BridgeRoot 'ai-task-scripts\portable_queue_runner.ps1';$StateDir=Join-Path $BridgeRoot 'state\repo_to_bridge_watch\aays1';$PendingDir=Join-Path $BridgeRoot 'ai-queue\pending'
$HeartbeatRel='docs/chatgpt_status/aays1/status/061_repo_to_bridge_watch_heartbeat_latest.txt';$HeartbeatPushSeconds=300
New-Item -ItemType Directory -Force -Path $StateDir,$PendingDir|Out-Null
function Identity([string]$Path){try{$j=Get-Content -LiteralPath $Path -Raw -Encoding UTF8|ConvertFrom-Json;return [ordered]@{task_id=[string]$j.task_id;payload_revision=if($null-ne$j.payload_revision){[int]$j.payload_revision}else{-1};script_path=[string]$j.script_path;idempotency_key=[string]$j.idempotency_key}}catch{return $null}}
function Match($i){return($null-ne$i-and$i.task_id-eq$TaskId-and$i.payload_revision-eq$PayloadRevision-and$i.script_path-eq$ScriptRel-and$i.idempotency_key-eq$IdempotencyKey)}
function Markers{$a=@();foreach($state in @('pending','running','done','processed','failed','error')){$d=Join-Path $BridgeRoot "ai-queue\$state";if(Test-Path $d){foreach($f in @(Get-ChildItem $d -File -ErrorAction SilentlyContinue)){$i=Identity $f.FullName;if($null-ne$i-and$i.task_id-eq$TaskId){$a+=[ordered]@{state=$state;path=$f.FullName;identity=$i;current_revision=(Match $i)}}}}};return @($a)}
function SyncDir($rel){$s=Join-Path $WatchRepo($rel-replace'/','\');$d=Join-Path $RepoRoot($rel-replace'/','\');if(!(Test-Path $s)){throw "SOURCE_DIRECTORY_MISSING:$rel"};New-Item -ItemType Directory -Force -Path $d|Out-Null;Copy-Item -Recurse -Force -ErrorAction Stop (Join-Path $s '*') $d}
function SyncFile($rel){$s=Join-Path $WatchRepo($rel-replace'/','\');$d=Join-Path $RepoRoot($rel-replace'/','\');if(!(Test-Path $s)){throw "SOURCE_FILE_MISSING:$rel"};New-Item -ItemType Directory -Force -Path(Split-Path -Parent $d)|Out-Null;Copy-Item -Force -ErrorAction Stop $s $d}
function AssertAssets{foreach($rel in $RequiredFiles){if(!(Test-Path -LiteralPath(Join-Path $RepoRoot($rel-replace'/','\')))){throw "ACTIVE_ASSET_MISSING_AFTER_SYNC:$rel"}};if(!(Match(Identity(Join-Path $RepoRoot 'docs\chatgpt_status\aays1\queue\aays1_height_difference_1_official_boundary_elevation_samples_20260720.task.json')))){throw 'ACTIVE_QUEUE_SIGNATURE_MISMATCH'}}
function EnsureRunner{$r=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$_.CommandLine-match'portable_queue_runner\.ps1'});if($r.Count-gt1){throw'MULTIPLE_RUNNER_PROCESSES_DETECTED'};if($r.Count-eq0-and$RestoreRunner){if(!(Test-Path $RunnerScript)){throw'CANONICAL_RUNNER_SCRIPT_MISSING'};Start-Process powershell -ArgumentList '-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File',$RunnerScript}}
function PushHb($text){$last=Join-Path $StateDir 'last_source_heartbeat_push.txt';$now=Get-Date;if(Test-Path $last){try{if(($now-[datetime](Get-Content $last -Raw)).TotalSeconds-lt$HeartbeatPushSeconds){return}}catch{}};for($n=1;$n-le2;$n++){git -C $WatchRepo fetch origin $SourceBranch|Out-Null;git -C $WatchRepo reset --hard "origin/$SourceBranch"|Out-Null;$sp=Join-Path $WatchRepo($HeartbeatRel-replace'/','\');New-Item -ItemType Directory -Force -Path(Split-Path -Parent $sp)|Out-Null;$text|Set-Content -LiteralPath $sp -Encoding UTF8;git -C $WatchRepo add -- $HeartbeatRel|Out-Null;$chg=git -C $WatchRepo status --porcelain -- $HeartbeatRel;if(!$chg){break};git -C $WatchRepo commit -m 'Update aays1 revision-aware watcher heartbeat'|Out-Null;git -C $WatchRepo push origin "HEAD:$SourceBranch"|Out-Null;if($LASTEXITCODE-eq0){break};if($n-eq2){throw'SOURCE_HEARTBEAT_PUSH_FAILED_AFTER_RETRY'}};$now.ToString('o')|Set-Content -LiteralPath $last -Encoding UTF8}
while($true){$stamp=Get-Date -Format'yyyyMMdd_HHmmss';$copied=0;try{git -C $WatchRepo fetch origin $SourceBranch|Out-Null;git -C $WatchRepo reset --hard "origin/$SourceBranch"|Out-Null;foreach($r in $AssetDirs){SyncDir $r};foreach($r in $QueueFiles){SyncFile $r};AssertAssets;$m=@(Markers);$active=@($m|Where-Object{$_.current_revision-and$_.state-in@('pending','running')});$success=@($m|Where-Object{$_.current_revision-and$_.state-in@('done','processed')});$failed=@($m|Where-Object{$_.current_revision-and$_.state-in@('failed','error')});if($failed.Count-gt0){throw'CURRENT_REVISION_FAILED_OR_ERROR_MARKER_REQUIRES_OPERATOR_POLICY'};if($success.Count-gt0-and!(Test-Path $ExpectedOutput)){throw'CURRENT_REVISION_TERMINAL_MARKER_WITHOUT_EXPECTED_OUTPUT'};if($active.Count-eq0-and$success.Count-eq0){Copy-Item -Force -ErrorAction Stop $QueuePath(Join-Path $PendingDir([IO.Path]::GetFileName($QueuePath)));$copied=1};EnsureRunner;$hb="status=WATCHING`npage_key=aays1`nsource_branch=$SourceBranch`ntask_id=$TaskId`npayload_revision=$PayloadRevision`nscript_path=$ScriptRel`nidempotency_key=$IdempotencyKey`nrevision_aware=true`ncopied_this_loop=$copied`nupdated_at=$stamp`nfinal_ready=false";$hb|Set-Content -LiteralPath(Join-Path $StateDir 'heartbeat.txt')-Encoding UTF8;PushHb $hb}catch{$err="status=WATCH_ERROR`npage_key=aays1`nsource_branch=$SourceBranch`ntask_id=$TaskId`npayload_revision=$PayloadRevision`nerror=$($_.Exception.Message)`nupdated_at=$stamp`nfinal_ready=false";$err|Set-Content -LiteralPath(Join-Path $StateDir 'last_error.txt')-Encoding UTF8;try{PushHb $err}catch{}};Start-Sleep -Seconds 60}
'@
$watcherText=$template.Replace('__REPO_ROOT__',$RepoRoot).Replace('__BRIDGE_ROOT__',$BridgeRoot).Replace('__WATCH_REPO__',$WatchRepo).Replace('__SOURCE_BRANCH__',$SourceBranch).Replace('__TASK_ID__',$TaskId).Replace('__PAYLOAD_REVISION__',[string]$PayloadRevision).Replace('__IDEMPOTENCY_KEY__',$IdempotencyKey).Replace('__SCRIPT_REL__',$ScriptRel).Replace('__RESTORE_RUNNER__',$restoreLiteral).Replace('__ASSET_DIRS__',$assetLiteral).Replace('__QUEUE_FILES__',$queueLiteral).Replace('__REQUIRED_FILES__',$requiredLiteral)
New-Item -ItemType Directory -Force -Path(Split-Path -Parent $WatcherScript),$StateDir,$PendingDir|Out-Null
$watcherText|Set-Content -LiteralPath $WatcherScript -Encoding UTF8
$watcher=Start-Process powershell -ArgumentList '-NoExit','-NoProfile','-ExecutionPolicy','Bypass','-File',$WatcherScript -PassThru
$runnerAfter=@(Get-Runners)
Emit([ordered]@{schema_version=4;slot_id='height_difference_1';task_id=$TaskId;payload_revision=$PayloadRevision;status=if($runnerAfter.Count-eq1){'REVISION_AWARE_WATCHER_AND_EXISTING_SINGLE_RUNNER_RECOVERED'}else{'REVISION_AWARE_WATCHER_RECOVERED_EXISTING_RUNNER_RESTORE_PENDING'};watcher_process_id=$watcher.Id;runner_process_count=$runnerAfter.Count;old_revision_markers_ignored=$true;current_failed_auto_retry_forbidden=$true;terminal_without_output_forbidden=$true;existing_runner_stopped=$false;new_runner=$false;parallel_runner=$false})
exit 0

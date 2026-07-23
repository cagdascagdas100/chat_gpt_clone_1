[CmdletBinding()]
param([int]$StaleMinutes = 20)
$ErrorActionPreference='Stop'
$slotId='security_public_safety_2'
$taskId='security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId='attempt-005'
$portableRoot='F:\TerraYield_AAYS_Portable'
$repoRoot='F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$branch='codex/aays-single-runner-v5-20260706'
$launcher='F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd'
$repoEntry=Join-Path $repoRoot 'devam.ps1'
$signal=Join-Path $repoRoot 'docs\chatgpt_status\_shared\control\request_queue_refresh.json'
$heartbeat=Join-Path $repoRoot 'docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json'
$lock=Join-Path $repoRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
$scanLockPath=Join-Path $repoRoot 'docs\chatgpt_status\_shared\runner_lock\MULTI_PAGE.lock'
$output=Join-Path $repoRoot 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\001_retry5_existing_runner_recovery_latest.json'
$targets=30762..30773
$lastStopEvidence=@()
$scanLockEvidence=$null
$specs=@(
  [ordered]@{name='launcher';token='RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd';root=$portableRoot},
  [ordered]@{name='hotfix';token='RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709';root=$portableRoot},
  [ordered]@{name='repo_entry';token='devam.ps1';root=$repoRoot},
  [ordered]@{name='daemon';token='RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1';root=$repoRoot},
  [ordered]@{name='scan_worker';token='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1';root=$repoRoot}
)
function Atomic([string]$p,[string]$t){$d=Split-Path -Parent $p;if(-not(Test-Path -LiteralPath $d)){New-Item -ItemType Directory -Force -Path $d|Out-Null};$x="$p.tmp.$PID";[IO.File]::WriteAllText($x,$t,[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $x -Destination $p -Force}
function ReadJson([string]$p){try{if(Test-Path -LiteralPath $p -PathType Leaf){return Get-Content -LiteralPath $p -Raw -Encoding UTF8|ConvertFrom-Json}}catch{};return $null}
function Norm([string]$v){if($null-eq$v){return''};return(($v-replace'/','\').ToLowerInvariant())}
function AllProcs{@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{-not[string]::IsNullOrWhiteSpace([string]$_.CommandLine)})}
function MatchSpec([object]$p,[object]$s){$c=Norm([string]$p.CommandLine);return($c.Contains((Norm([string]$s.token)))-and$c.Contains((Norm([string]$s.root))))}
function RunnerLike([object]$p){$c=Norm([string]$p.CommandLine);foreach($s in $specs){if($c.Contains((Norm([string]$s.token)))){return$true}};return$false}
function MatchedSpecName([object]$p){foreach($s in $specs){if(MatchSpec $p $s){return[string]$s.name}};return''}
function Canonical([string[]]$names){$all=AllProcs;$out=@();foreach($p in $all){foreach($s in $specs){if(($names.Count-eq0-or$names-contains[string]$s.name)-and(MatchSpec $p $s)){$out+=$p;break}}};return@($out|Group-Object ProcessId|ForEach-Object{$_.Group[0]})}
function ForeignRunnerProcesses{$all=AllProcs;$out=@();foreach($p in $all){if(-not(RunnerLike $p)){continue};$ok=$false;foreach($s in $specs){if(MatchSpec $p $s){$ok=$true;break}};if(-not$ok){$out+=$p}};return@($out|Group-Object ProcessId|ForEach-Object{$_.Group[0]})}
function ProcAgeMinutes([int]$id){try{$p=Get-Process -Id $id -ErrorAction Stop;return[math]::Round(([DateTimeOffset]::UtcNow-[DateTimeOffset]$p.StartTime.ToUniversalTime()).TotalMinutes,2)}catch{return$null}}
function ProcessIdentityKey([object]$Process){return('{0}|{1}'-f([int]$Process.ProcessId),([string]$Process.CreationDate))}
function CurrentCimProcess([int]$Id){return@((Get-CimInstance Win32_Process -Filter ("ProcessId={0}"-f$Id) -ErrorAction SilentlyContinue)|Select-Object -First 1)}
function ResolveScanLockFile{if(Test-Path -LiteralPath $scanLockPath -PathType Leaf){return$scanLockPath};if(Test-Path -LiteralPath $scanLockPath -PathType Container){$owner=Join-Path $scanLockPath 'owner.json';if(Test-Path -LiteralPath $owner -PathType Leaf){return$owner}};return$null}
function InspectAndRepairScanLock{
  $exists=Test-Path -LiteralPath $scanLockPath;$lockFile=ResolveScanLockFile;$raw=if($lockFile){ReadJson $lockFile}else{$null};$pidValue=0;if($raw-and$raw.pid){$pidValue=[int]$raw.pid}
  $current=if($pidValue-gt0){@(CurrentCimProcess -Id $pidValue)}else{@()};$currentSpec=if($current.Count-eq1){MatchedSpecName $current[0]}else{''};$scopeMatch=($raw-and[string]$raw.lock_scope-eq'single_scan_worker');$repoMatch=($raw-and-not[string]::IsNullOrWhiteSpace([string]$raw.repo_root)-and(Norm([string]$raw.repo_root)-eq Norm $repoRoot));$instancePresent=($raw-and-not[string]::IsNullOrWhiteSpace([string]$raw.instance_id));$startPresent=($raw-and-not[string]::IsNullOrWhiteSpace([string]$raw.process_start_time));$startMatch=$false
  if($startPresent-and$current.Count-eq1){try{$expected=[DateTimeOffset]::Parse([string]$raw.process_start_time);$actual=[DateTimeOffset](Get-Process -Id $pidValue -ErrorAction Stop).StartTime.ToUniversalTime();$startMatch=([math]::Abs(($expected-$actual).TotalSeconds)-le2)}catch{}}
  $valid=($exists-and$raw-and$scopeMatch-and$repoMatch-and$instancePresent-and$startPresent-and$startMatch-and$currentSpec-eq'scan_worker');$scanWorkers=@(Canonical @('scan_worker'));$removed=$false;$status=if(-not$exists){'absent'}elseif($valid){'valid_live_scan_worker'}else{'invalid_or_stale'}
  if($exists-and-not$valid-and$scanWorkers.Count-eq0){Remove-Item -LiteralPath $scanLockPath -Force -Recurse -ErrorAction Stop;$removed=$true;$status='stale_lock_removed_no_exact_scan_worker'}elseif($exists-and-not$valid-and$scanWorkers.Count-gt0){$status='invalid_lock_preserved_exact_scan_worker_present'}
  return[ordered]@{path=$scanLockPath;lock_file=$lockFile;exists=$exists;parsed=($null-ne$raw);pid=$pidValue;scope_match=$scopeMatch;repo_root_match=$repoMatch;instance_id_present=$instancePresent;process_start_time_present=$startPresent;process_start_time_match=$startMatch;current_spec=$currentSpec;exact_scan_worker_count=$scanWorkers.Count;valid=$valid;removed=$removed;status=$status}
}
function HeartbeatInfo([int]$daemonPid){
  $h=ReadJson $heartbeat;$l=ReadJson $lock
  $age=$null;$pidMatch=$false;$timeOk=$false;$heartbeatRootPresent=$false;$heartbeatRootMatch=$false;$heartbeatBranchMatch=$false;$heartbeatProcessStartMatch=$false;$heartbeatStartField='none'
  $lockPidMatch=$false;$lockRootMatch=$false;$instanceMatch=$false;$startMatch=$false;$lockRealProcessStartMatch=$false;$lockHeartbeatFresh=$false;$lockScopeMatch=$false;$lockBranchMatch=$false
  $lockHeartbeatDeltaSeconds=$null;$rootSource='none'
  $processStart=$null;try{$processStart=[DateTimeOffset](Get-Process -Id $daemonPid -ErrorAction Stop).StartTime.ToUniversalTime()}catch{}
  if($h){
    $hp=0;if($h.supervisor_pid){$hp=[int]$h.supervisor_pid}elseif($h.daemon_pid){$hp=[int]$h.daemon_pid}elseif($h.pid){$hp=[int]$h.pid};$pidMatch=($hp-eq$daemonPid)
    $heartbeatRootPresent=(-not[string]::IsNullOrWhiteSpace([string]$h.repo_root));if($heartbeatRootPresent){$heartbeatRootMatch=((Norm([string]$h.repo_root))-eq(Norm $repoRoot))}
    $heartbeatBranchMatch=([string]$h.branch-eq$branch)
    $heartbeatStartValue=$null;if($h.supervisor_started_at){$heartbeatStartValue=[string]$h.supervisor_started_at;$heartbeatStartField='supervisor_started_at'}elseif($h.started_at){$heartbeatStartValue=[string]$h.started_at;$heartbeatStartField='started_at'}
    if($heartbeatStartValue-and$processStart){try{$hs=[DateTimeOffset]::Parse($heartbeatStartValue);$heartbeatProcessStartMatch=([math]::Abs(($hs-$processStart).TotalSeconds)-le2)}catch{}}
    if($h.heartbeat_at){try{$age=[math]::Round(([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse([string]$h.heartbeat_at)).TotalMinutes,2);$timeOk=$true}catch{}}
  }
  if($l){
    $lp=0;if($l.supervisor_pid){$lp=[int]$l.supervisor_pid}elseif($l.pid){$lp=[int]$l.pid};$lockPidMatch=($lp-eq$daemonPid)
    $lockRootMatch=((Norm([string]$l.repo_root))-eq(Norm $repoRoot));$lockBranchMatch=([string]$l.branch-eq$branch)
    $lockScopeMatch=(-not$l.lock_scope-or[string]$l.lock_scope-eq'single_shared_runner_daemon')
    if($h-and-not[string]::IsNullOrWhiteSpace([string]$h.instance_id)-and-not[string]::IsNullOrWhiteSpace([string]$l.instance_id)){$instanceMatch=([string]$h.instance_id-eq[string]$l.instance_id)}
    if($h-and$h.supervisor_started_at-and$l.process_start_time){try{$hs=[DateTimeOffset]::Parse([string]$h.supervisor_started_at);$ls=[DateTimeOffset]::Parse([string]$l.process_start_time);$startMatch=([math]::Abs(($hs-$ls).TotalSeconds)-le2)}catch{}}
    if($l.process_start_time-and$processStart){try{$ls=[DateTimeOffset]::Parse([string]$l.process_start_time);$lockRealProcessStartMatch=([math]::Abs(($ls-$processStart).TotalSeconds)-le2)}catch{}}
    if($h-and$h.heartbeat_at-and$l.updated_at){try{$ht=[DateTimeOffset]::Parse([string]$h.heartbeat_at);$lu=[DateTimeOffset]::Parse([string]$l.updated_at);$lockHeartbeatDeltaSeconds=[math]::Round([math]::Abs(($ht-$lu).TotalSeconds),3);$lockHeartbeatFresh=($lockHeartbeatDeltaSeconds-le60)}catch{}}
  }
  $boundHeartbeatMatch=$heartbeatRootMatch-and$heartbeatBranchMatch-and$heartbeatProcessStartMatch
  $boundLockMatch=$lockPidMatch-and$lockRootMatch-and$instanceMatch-and$startMatch-and$lockRealProcessStartMatch-and$lockHeartbeatFresh-and$lockScopeMatch-and$lockBranchMatch
  if($boundHeartbeatMatch){$rootSource='heartbeat_bound_process'}elseif($boundLockMatch){$rootSource='lock_bound_instance_and_process'}
  $rootMatch=$boundHeartbeatMatch-or$boundLockMatch
  return[pscustomobject]@{valid=($pidMatch-and$rootMatch-and$timeOk);pid_match=$pidMatch;repo_root_match=$rootMatch;repo_root_source=$rootSource;heartbeat_repo_root_present=$heartbeatRootPresent;heartbeat_repo_root_match=$heartbeatRootMatch;heartbeat_branch_match=$heartbeatBranchMatch;heartbeat_process_start_match=$heartbeatProcessStartMatch;heartbeat_start_field=$heartbeatStartField;bound_heartbeat_identity_match=$boundHeartbeatMatch;lock_pid_match=$lockPidMatch;lock_repo_root_match=$lockRootMatch;lock_instance_id_match=$instanceMatch;lock_process_start_match=$startMatch;lock_real_process_start_match=$lockRealProcessStartMatch;lock_updated_near_heartbeat=$lockHeartbeatFresh;lock_heartbeat_delta_seconds=$lockHeartbeatDeltaSeconds;lock_scope_match=$lockScopeMatch;lock_branch_match=$lockBranchMatch;bound_lock_identity_match=$boundLockMatch;age_minutes=$age;raw=$h;raw_lock=$l}
}
function StopCanonicalGeneration([object]$Expected){
  $id=[int]$Expected.ProcessId;$expectedKey=ProcessIdentityKey -Process $Expected;$expectedSpec=MatchedSpecName $Expected;$current=@(CurrentCimProcess -Id $id)
  if($current.Count-eq0){return[pscustomobject]@{process_id=$id;expected_identity_key=$expectedKey;current_identity_key=$null;expected_spec=$expectedSpec;current_spec=$null;generation_match=$true;canonical_match=$true;bound_process_start_match=$true;kill_attempted=$false;kill_exit_code=0;already_exited=$true;expected_generation_remaining=$false}}
  $currentKey=ProcessIdentityKey -Process $current[0];$currentSpec=MatchedSpecName $current[0];$sameGeneration=($currentKey-eq$expectedKey);$canonicalMatch=(-not[string]::IsNullOrWhiteSpace($expectedSpec)-and$currentSpec-eq$expectedSpec);$bound=$null;$boundStartMatch=$false
  try{$bound=Get-Process -Id $id -ErrorAction Stop;$cimStart=[DateTimeOffset]$current[0].CreationDate;$boundStart=[DateTimeOffset]$bound.StartTime.ToUniversalTime();$boundStartMatch=([math]::Abs(($cimStart-$boundStart).TotalSeconds)-le2)}catch{}
  if(-not($sameGeneration-and$canonicalMatch-and$boundStartMatch)){return[pscustomobject]@{process_id=$id;expected_identity_key=$expectedKey;current_identity_key=$currentKey;expected_spec=$expectedSpec;current_spec=$currentSpec;generation_match=$sameGeneration;canonical_match=$canonicalMatch;bound_process_start_match=$boundStartMatch;kill_attempted=$false;kill_exit_code=0;already_exited=(-not$sameGeneration);expected_generation_remaining=$sameGeneration}}
  $killExit=-1;$killAttempted=$false;try{$killAttempted=$true;Stop-Process -InputObject $bound -Force -ErrorAction Stop;$killExit=0}catch{$killExit=1}
  Start-Sleep -Milliseconds 250
  $after=@(CurrentCimProcess -Id $id);$expectedRemaining=$false;if($after.Count-eq1){$expectedRemaining=((ProcessIdentityKey -Process $after[0])-eq$expectedKey)}
  return[pscustomobject]@{process_id=$id;expected_identity_key=$expectedKey;current_identity_key=$currentKey;expected_spec=$expectedSpec;current_spec=$currentSpec;generation_match=$true;canonical_match=$true;bound_process_start_match=$true;kill_attempted=$killAttempted;kill_exit_code=$killExit;already_exited=$false;expected_generation_remaining=$expectedRemaining}
}
function Result([string]$status,[bool]$attempted,[bool]$started,[bool]$signalWritten,[bool]$staleRestart,[object]$hb,[string]$detail){$canonical=@(Canonical @());$daemons=@(Canonical @('daemon'));$foreign=@(ForeignRunnerProcesses);$o=[ordered]@{schema_version=15;slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;status=$status;checked_at=[DateTimeOffset]::UtcNow.ToString('o');stale_minutes_threshold=$StaleMinutes;start_attempted=$attempted;canonical_runner_started=$started;stale_verified_runner_restarted=$staleRestart;canonical_process_ids=@($canonical|ForEach-Object{[int]$_.ProcessId});canonical_daemon_ids=@($daemons|ForEach-Object{[int]$_.ProcessId});foreign_runner_process_ids=@($foreign|ForEach-Object{[int]$_.ProcessId});foreign_runner_command_lines=@($foreign|ForEach-Object{[string]$_.CommandLine});canonical_root_identity_required=$true;heartbeat_identity=$hb;direct_heartbeat_requires_repo_root_branch_and_process_start=$true;heartbeat_repo_root_optional_with_bound_lock_fallback=$true;lock_fallback_requires_pid_repo_root_instance_heartbeat_start_real_process_start_freshness_scope_branch=$true;kill_requires_immediate_pid_creation_date_and_canonical_command_recheck=$true;termination_uses_bound_process_object=$true;termination_uses_individual_verified_process_generations=$true;taskkill_tree_used=$false;scan_lock_generation_validation=$true;stale_scan_lock_removed_only_without_exact_scan_worker=$true;scan_lock_evidence=$scanLockEvidence;stale_stop_evidence=@($lastStopEvidence);queue_refresh_signal_written=$signalWritten;existing_shared_signal_preserved=(-not$signalWritten-and(Test-Path -LiteralPath $signal));exact_target_rows=@($targets);nearest_row_fallback_allowed=$false;existing_single_runner_architecture_reused=$true;new_runner_architecture_created=$false;parallel_runner_started=$false;transient_without_fresh_daemon_is_failure=$true;process_exit_before_kill_is_clean_stop=$true;task_claimed=$false;detail=$detail;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false};Atomic $output (($o|ConvertTo-Json -Depth 16)+"`n")}
function SignalIfAbsent{if(Test-Path -LiteralPath $signal){return$false};$o=[ordered]@{request_id='security-public-safety-2-retry5-refresh-20260722-001';page_key='aays1';slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;action='refresh_remote_queue_and_claim_retry5';target_branch=$branch;queue_path='docs/chatgpt_status/aays1/queue/000000_security_public_safety_2_wave1_retry5_20260722.v3.task.json';priority=-100;single_runner_only=$true;new_runner=$false;parallel_runner=$false;requested_at=[DateTimeOffset]::UtcNow.ToString('o');final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false};Atomic $signal (($o|ConvertTo-Json -Depth 8)+"`n");return$true}
function WaitFreshDaemon([int]$seconds){$end=(Get-Date).AddSeconds($seconds);do{$d=@(Canonical @('daemon'));if($d.Count-eq1){$h=HeartbeatInfo ([int]$d[0].ProcessId);if($h.valid-and$null-ne$h.age_minutes-and$h.age_minutes-le$StaleMinutes){return[pscustomobject]@{daemons=$d;heartbeat=$h}}};Start-Sleep -Seconds 2}while((Get-Date)-lt$end);$d=@(Canonical @('daemon'));$h=if($d.Count-eq1){HeartbeatInfo ([int]$d[0].ProcessId)}else{$null};return[pscustomobject]@{daemons=$d;heartbeat=$h}}
if(-not(Test-Path -LiteralPath $repoRoot -PathType Container)){throw"CANONICAL_F_REPO_ROOT_MISSING=$repoRoot"}
if(-not(Test-Path -LiteralPath $repoEntry -PathType Leaf)){Result 'BLOCKED_CANONICAL_REPO_ENTRY_MISSING' $false $false $false $false $null $repoEntry;exit 2}
$scanLockEvidence=InspectAndRepairScanLock
$foreign=@(ForeignRunnerProcesses)
if($foreign.Count-gt0){Result 'BLOCKED_FOREIGN_OR_NONCANONICAL_RUNNER_PROCESS_PRESENT' $false $false $false $false $null 'Same runner token found outside the exact canonical F root; no process was stopped or started.';exit 3}
$canonical=@(Canonical @());$daemons=@(Canonical @('daemon'))
if($daemons.Count-gt1){Result 'BLOCKED_MULTIPLE_PERSISTENT_DAEMONS' $false $false $false $false $null 'Fail closed; multiple exact canonical F daemon processes observed.';exit 3}
if($daemons.Count-eq1){
  $daemonSnapshot=$daemons[0];$daemonPid=[int]$daemonSnapshot.ProcessId;$hb=HeartbeatInfo $daemonPid;$procAge=ProcAgeMinutes $daemonPid
  if($hb.valid-and$null-ne$hb.age_minutes-and$hb.age_minutes-gt$StaleMinutes){
    if($canonical.Count-gt3){Result 'BLOCKED_AMBIGUOUS_STALE_CANONICAL_PROCESS_SET' $false $false $false $false $hb 'More than three exact canonical F processes observed.';exit 3}
    $staleSnapshot=@($canonical);$nonDaemons=@($staleSnapshot|Where-Object{(MatchedSpecName $_)-ne'daemon'});$daemonOnly=@($staleSnapshot|Where-Object{(MatchedSpecName $_)-eq'daemon'});$ordered=@($nonDaemons)+@($daemonOnly)
    $stopRows=@();foreach($proc in $ordered){$stopRows+=StopCanonicalGeneration -Expected $proc};$lastStopEvidence=@($stopRows);Start-Sleep -Seconds 3
    $expectedRemain=@($lastStopEvidence|Where-Object{$_.expected_generation_remaining});$remain=@(Canonical @())
    if($expectedRemain.Count-gt0-or$remain.Count-gt0){Result 'BLOCKED_STALE_CANONICAL_GENERATION_STOP_NOT_CONFIRMED' $true $false $false $false $hb ("expected_remaining=$($expectedRemain.Count) canonical_remaining="+(($remain|ForEach-Object{$_.ProcessId})-join','));exit 4}
    $p=Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c',('"'+$launcher+'"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal
    $fresh=WaitFreshDaemon 45
    if(@($fresh.daemons).Count-ne1-or-not$fresh.heartbeat-or-not$fresh.heartbeat.valid){Result 'BLOCKED_STALE_DAEMON_RESTART_FRESH_HEARTBEAT_NOT_CONFIRMED' $true $false $false $true $fresh.heartbeat "launcher_pid=$($p.Id)";exit 4}
    $signalWritten=SignalIfAbsent;Result 'STALE_CANONICAL_GENERATIONS_STOPPED_AND_DAEMON_RESTARTED_SINGLE_INSTANCE' $true $true $signalWritten $true $fresh.heartbeat "launcher_pid=$($p.Id);stopped_generations=$($lastStopEvidence.Count)";exit 0
  }
  if($hb.valid){$signalWritten=SignalIfAbsent;Result 'CANONICAL_DAEMON_ACTIVE_VERIFIED_REFRESH_AVAILABLE' $false $false $signalWritten $false $hb 'Exact canonical daemon and matching fresh heartbeat preserved.';exit 0}
  if($null-ne$procAge-and$procAge-le$StaleMinutes){$signalWritten=SignalIfAbsent;Result 'CANONICAL_DAEMON_STARTUP_GRACE_REFRESH_AVAILABLE' $false $false $signalWritten $false $hb "process_age_minutes=$procAge";exit 0}
  Result 'BLOCKED_CANONICAL_DAEMON_HEARTBEAT_IDENTITY_UNVERIFIED' $false $false $false $false $hb "process_age_minutes=$procAge; no restart attempted";exit 3
}
if($canonical.Count-gt1){Result 'BLOCKED_MULTIPLE_NON_DAEMON_CANONICAL_PROCESSES' $false $false $false $false $null 'Fail closed';exit 3}
if($canonical.Count-eq1){$fresh=WaitFreshDaemon 45;if(@($fresh.daemons).Count-eq1-and$fresh.heartbeat-and$fresh.heartbeat.valid){$signalWritten=SignalIfAbsent;Result 'CANONICAL_DAEMON_APPEARED_FRESH_HEARTBEAT_NO_SECOND_PROCESS' $false $false $signalWritten $false $fresh.heartbeat 'Existing launcher completed daemon startup.';exit 0};Result 'BLOCKED_CANONICAL_TRANSIENT_PROCESS_DID_NOT_PRODUCE_FRESH_DAEMON' $false $false $false $false $fresh.heartbeat 'Existing exact canonical transient process was preserved; no second process started and no fresh daemon appeared within 45 seconds.';exit 4}
$detail='';if(Test-Path -LiteralPath $launcher -PathType Leaf){$p=Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c',('"'+$launcher+'"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal;$detail="canonical_cmd_pid=$($p.Id)"}
$fresh=WaitFreshDaemon 45
if(@($fresh.daemons).Count-eq0-and@(Canonical @()).Count-eq0){$p=Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$repoEntry+'"')) -WorkingDirectory $repoRoot -PassThru -WindowStyle Normal;$detail=($detail+';repo_devam_pid='+$p.Id).TrimStart(';');$fresh=WaitFreshDaemon 45}
if(@($fresh.daemons).Count-gt1){Result 'BLOCKED_MULTIPLE_DAEMONS_AFTER_START' $true $false $false $false $fresh.heartbeat $detail;exit 3}
if(@($fresh.daemons).Count-eq0-or-not$fresh.heartbeat-or-not$fresh.heartbeat.valid){Result 'BLOCKED_CANONICAL_RUNNER_START_FRESH_HEARTBEAT_NOT_OBSERVED' $true $false $false $false $fresh.heartbeat $detail;exit 4}
$signalWritten=SignalIfAbsent;Result 'EXISTING_CANONICAL_DAEMON_STARTED_SINGLE_INSTANCE_FRESH_HEARTBEAT' $true $true $signalWritten $false $fresh.heartbeat $detail
exit 0

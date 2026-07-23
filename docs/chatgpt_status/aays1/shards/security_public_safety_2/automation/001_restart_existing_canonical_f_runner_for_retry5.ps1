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
$output=Join-Path $repoRoot 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\001_retry5_existing_runner_recovery_latest.json'
$targets=30762..30773
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
function Canonical([string[]]$names){$all=AllProcs;$out=@();foreach($p in $all){foreach($s in $specs){if(($names.Count-eq0-or$names-contains[string]$s.name)-and(MatchSpec $p $s)){$out+=$p;break}}};return@($out|Group-Object ProcessId|ForEach-Object{$_.Group[0]})}
function ForeignRunnerProcesses{$all=AllProcs;$out=@();foreach($p in $all){if(-not(RunnerLike $p)){continue};$ok=$false;foreach($s in $specs){if(MatchSpec $p $s){$ok=$true;break}};if(-not$ok){$out+=$p}};return@($out|Group-Object ProcessId|ForEach-Object{$_.Group[0]})}
function ProcAgeMinutes([int]$id){try{$p=Get-Process -Id $id -ErrorAction Stop;return[math]::Round(([DateTimeOffset]::UtcNow-[DateTimeOffset]$p.StartTime.ToUniversalTime()).TotalMinutes,2)}catch{return$null}}
function HeartbeatInfo([int]$daemonPid){
  $h=ReadJson $heartbeat;$l=ReadJson $lock
  $age=$null;$pidMatch=$false;$timeOk=$false;$heartbeatRootPresent=$false;$heartbeatRootMatch=$false
  $lockPidMatch=$false;$lockRootMatch=$false;$instanceMatch=$false;$startMatch=$false;$lockHeartbeatFresh=$false;$lockScopeMatch=$false;$lockBranchMatch=$false
  $lockHeartbeatDeltaSeconds=$null;$rootSource='none'
  if($h){
    $hp=0;if($h.supervisor_pid){$hp=[int]$h.supervisor_pid}elseif($h.daemon_pid){$hp=[int]$h.daemon_pid}elseif($h.pid){$hp=[int]$h.pid};$pidMatch=($hp-eq$daemonPid)
    $heartbeatRootPresent=(-not[string]::IsNullOrWhiteSpace([string]$h.repo_root));if($heartbeatRootPresent){$heartbeatRootMatch=((Norm([string]$h.repo_root))-eq(Norm $repoRoot))}
    if($h.heartbeat_at){try{$age=[math]::Round(([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse([string]$h.heartbeat_at)).TotalMinutes,2);$timeOk=$true}catch{}}
  }
  if($l){
    $lp=0;if($l.supervisor_pid){$lp=[int]$l.supervisor_pid}elseif($l.pid){$lp=[int]$l.pid};$lockPidMatch=($lp-eq$daemonPid)
    $lockRootMatch=((Norm([string]$l.repo_root))-eq(Norm $repoRoot));$lockBranchMatch=([string]$l.branch-eq$branch)
    $lockScopeMatch=(-not$l.lock_scope-or[string]$l.lock_scope-eq'single_shared_runner_daemon')
    if($h-and-not[string]::IsNullOrWhiteSpace([string]$h.instance_id)-and-not[string]::IsNullOrWhiteSpace([string]$l.instance_id)){$instanceMatch=([string]$h.instance_id-eq[string]$l.instance_id)}
    if($h-and$h.supervisor_started_at-and$l.process_start_time){try{$hs=[DateTimeOffset]::Parse([string]$h.supervisor_started_at);$ls=[DateTimeOffset]::Parse([string]$l.process_start_time);$startMatch=([math]::Abs(($hs-$ls).TotalSeconds)-le2)}catch{}}
    if($h-and$h.heartbeat_at-and$l.updated_at){try{$ht=[DateTimeOffset]::Parse([string]$h.heartbeat_at);$lu=[DateTimeOffset]::Parse([string]$l.updated_at);$lockHeartbeatDeltaSeconds=[math]::Round([math]::Abs(($ht-$lu).TotalSeconds),3);$lockHeartbeatFresh=($lockHeartbeatDeltaSeconds-le60)}catch{}}
  }
  $boundLockMatch=$lockPidMatch-and$lockRootMatch-and$instanceMatch-and$startMatch-and$lockHeartbeatFresh-and$lockScopeMatch-and$lockBranchMatch
  if($heartbeatRootMatch){$rootSource='heartbeat'}elseif($boundLockMatch){$rootSource='lock_bound_instance'}
  $rootMatch=$heartbeatRootMatch-or$boundLockMatch
  return[pscustomobject]@{valid=($pidMatch-and$rootMatch-and$timeOk);pid_match=$pidMatch;repo_root_match=$rootMatch;repo_root_source=$rootSource;heartbeat_repo_root_present=$heartbeatRootPresent;heartbeat_repo_root_match=$heartbeatRootMatch;lock_pid_match=$lockPidMatch;lock_repo_root_match=$lockRootMatch;lock_instance_id_match=$instanceMatch;lock_process_start_match=$startMatch;lock_updated_near_heartbeat=$lockHeartbeatFresh;lock_heartbeat_delta_seconds=$lockHeartbeatDeltaSeconds;lock_scope_match=$lockScopeMatch;lock_branch_match=$lockBranchMatch;bound_lock_identity_match=$boundLockMatch;age_minutes=$age;raw=$h;raw_lock=$l}
}
function Result([string]$status,[bool]$attempted,[bool]$started,[bool]$signalWritten,[bool]$staleRestart,[object]$hb,[string]$detail){$canonical=@(Canonical @());$daemons=@(Canonical @('daemon'));$foreign=@(ForeignRunnerProcesses);$o=[ordered]@{schema_version=10;slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;status=$status;checked_at=[DateTimeOffset]::UtcNow.ToString('o');stale_minutes_threshold=$StaleMinutes;start_attempted=$attempted;canonical_runner_started=$started;stale_verified_runner_restarted=$staleRestart;canonical_process_ids=@($canonical|ForEach-Object{[int]$_.ProcessId});canonical_daemon_ids=@($daemons|ForEach-Object{[int]$_.ProcessId});foreign_runner_process_ids=@($foreign|ForEach-Object{[int]$_.ProcessId});foreign_runner_command_lines=@($foreign|ForEach-Object{[string]$_.CommandLine});canonical_root_identity_required=$true;heartbeat_identity=$hb;heartbeat_repo_root_optional_with_bound_lock_fallback=$true;lock_fallback_requires_pid_repo_root_instance_start_freshness_scope_branch=$true;queue_refresh_signal_written=$signalWritten;existing_shared_signal_preserved=(-not$signalWritten-and(Test-Path -LiteralPath $signal));exact_target_rows=@($targets);nearest_row_fallback_allowed=$false;existing_single_runner_architecture_reused=$true;new_runner_architecture_created=$false;parallel_runner_started=$false;transient_without_fresh_daemon_is_failure=$true;process_exit_before_kill_is_clean_stop=$true;task_claimed=$false;detail=$detail;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false};Atomic $output (($o|ConvertTo-Json -Depth 16)+"`n")}
function SignalIfAbsent{if(Test-Path -LiteralPath $signal){return$false};$o=[ordered]@{request_id='security-public-safety-2-retry5-refresh-20260722-001';page_key='aays1';slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;action='refresh_remote_queue_and_claim_retry5';target_branch=$branch;queue_path='docs/chatgpt_status/aays1/queue/000000_security_public_safety_2_wave1_retry5_20260722.v3.task.json';priority=-100;single_runner_only=$true;new_runner=$false;parallel_runner=$false;requested_at=[DateTimeOffset]::UtcNow.ToString('o');final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false};Atomic $signal (($o|ConvertTo-Json -Depth 8)+"`n");return$true}
function WaitFreshDaemon([int]$seconds){$end=(Get-Date).AddSeconds($seconds);do{$d=@(Canonical @('daemon'));if($d.Count-eq1){$h=HeartbeatInfo ([int]$d[0].ProcessId);if($h.valid-and$null-ne$h.age_minutes-and$h.age_minutes-le$StaleMinutes){return[pscustomobject]@{daemons=$d;heartbeat=$h}}};Start-Sleep -Seconds 2}while((Get-Date)-lt$end);$d=@(Canonical @('daemon'));$h=if($d.Count-eq1){HeartbeatInfo ([int]$d[0].ProcessId)}else{$null};return[pscustomobject]@{daemons=$d;heartbeat=$h}}
function StopCanonicalTree([int]$id){$tk=Get-Command taskkill.exe -ErrorAction SilentlyContinue;if($tk){& $tk.Source /PID $id /T /F|Out-Null;return$LASTEXITCODE};try{Stop-Process -Id $id -Force -ErrorAction Stop;return 0}catch{if(-not(Get-Process -Id $id -ErrorAction SilentlyContinue)){return 0};return 1}}
if(-not(Test-Path -LiteralPath $repoRoot -PathType Container)){throw"CANONICAL_F_REPO_ROOT_MISSING=$repoRoot"}
if(-not(Test-Path -LiteralPath $repoEntry -PathType Leaf)){Result 'BLOCKED_CANONICAL_REPO_ENTRY_MISSING' $false $false $false $false $null $repoEntry;exit 2}
$foreign=@(ForeignRunnerProcesses)
if($foreign.Count-gt0){Result 'BLOCKED_FOREIGN_OR_NONCANONICAL_RUNNER_PROCESS_PRESENT' $false $false $false $false $null 'Same runner token found outside the exact canonical F root; no process was stopped or started.';exit 3}
$canonical=@(Canonical @());$daemons=@(Canonical @('daemon'))
if($daemons.Count-gt1){Result 'BLOCKED_MULTIPLE_PERSISTENT_DAEMONS' $false $false $false $false $null 'Fail closed; multiple exact canonical F daemon processes observed.';exit 3}
if($daemons.Count-eq1){
  $daemonPid=[int]$daemons[0].ProcessId;$hb=HeartbeatInfo $daemonPid;$procAge=ProcAgeMinutes $daemonPid
  if($hb.valid-and$null-ne$hb.age_minutes-and$hb.age_minutes-gt$StaleMinutes){
    if($canonical.Count-gt3){Result 'BLOCKED_AMBIGUOUS_STALE_CANONICAL_PROCESS_SET' $false $false $false $false $hb 'More than three exact canonical F processes observed.';exit 3}
    $killExit=StopCanonicalTree $daemonPid;Start-Sleep -Seconds 3
    $remain=@(Canonical @())
    if($remain.Count-gt0){Result 'BLOCKED_STALE_CANONICAL_PROCESS_TREE_STOP_NOT_CONFIRMED' $true $false $false $false $hb ("kill_exit=$killExit remaining="+(($remain|ForEach-Object{$_.ProcessId})-join','));exit 4}
    $p=Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c',('"'+$launcher+'"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal
    $fresh=WaitFreshDaemon 45
    if(@($fresh.daemons).Count-ne1-or-not$fresh.heartbeat-or-not$fresh.heartbeat.valid){Result 'BLOCKED_STALE_DAEMON_RESTART_FRESH_HEARTBEAT_NOT_CONFIRMED' $true $false $false $true $fresh.heartbeat "launcher_pid=$($p.Id)";exit 4}
    $signalWritten=SignalIfAbsent;Result 'STALE_CANONICAL_DAEMON_RESTARTED_SINGLE_INSTANCE_FRESH_HEARTBEAT' $true $true $signalWritten $true $fresh.heartbeat "launcher_pid=$($p.Id);kill_exit=$killExit";exit 0
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

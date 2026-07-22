[CmdletBinding()]
param([int]$StaleMinutes = 20)
$ErrorActionPreference='Stop'
$slotId='security_public_safety_2'
$taskId='security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId='attempt-005'
$portableRoot='F:\TerraYield_AAYS_Portable'
$repoRoot='F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$launcher='F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd'
$repoEntry=Join-Path $repoRoot 'devam.ps1'
$signal=Join-Path $repoRoot 'docs\chatgpt_status\_shared\control\request_queue_refresh.json'
$heartbeat=Join-Path $repoRoot 'docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json'
$output=Join-Path $repoRoot 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\001_retry5_existing_runner_recovery_latest.json'
$targets=30762..30773
function Atomic([string]$p,[string]$t){$d=Split-Path -Parent $p;if(-not(Test-Path -LiteralPath $d)){New-Item -ItemType Directory -Force -Path $d|Out-Null};$x="$p.tmp.$PID";[IO.File]::WriteAllText($x,$t,[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $x -Destination $p -Force}
function ReadJson([string]$p){try{if(Test-Path -LiteralPath $p -PathType Leaf){return Get-Content -LiteralPath $p -Raw -Encoding UTF8|ConvertFrom-Json}}catch{};return $null}
function Procs([string[]]$patterns){@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$c=[string]$_.CommandLine;if(-not$c){return $false};foreach($p in $patterns){if($c-match$p){return $true}};return $false})}
function Result([string]$status,[bool]$attempted,[bool]$started,[int]$before,[int]$after,[int]$daemons,[bool]$signalWritten,[bool]$staleRestart,[object]$heartbeatAge,[string]$detail){$o=[ordered]@{schema_version=6;slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;status=$status;checked_at=[DateTimeOffset]::UtcNow.ToString('o');stale_minutes_threshold=$StaleMinutes;local_heartbeat_age_minutes=$heartbeatAge;start_attempted=$attempted;canonical_runner_started=$started;stale_verified_runner_restarted=$staleRestart;existing_process_count_before=$before;existing_process_count_after=$after;persistent_daemon_count_after=$daemons;queue_refresh_signal_written=$signalWritten;existing_shared_signal_preserved=(-not$signalWritten-and(Test-Path -LiteralPath $signal));exact_target_rows=@($targets);nearest_row_fallback_allowed=$false;existing_single_runner_architecture_reused=$true;new_runner_architecture_created=$false;parallel_runner_started=$false;task_claimed=$false;detail=$detail;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false};Atomic $output (($o|ConvertTo-Json -Depth 8)+"`n")}
function SignalIfAbsent{if(Test-Path -LiteralPath $signal){return $false};$o=[ordered]@{request_id='security-public-safety-2-retry5-refresh-20260722-001';page_key='aays1';slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;action='refresh_remote_queue_and_claim_retry5';target_branch='codex/aays-single-runner-v5-20260706';queue_path='docs/chatgpt_status/aays1/queue/000000_security_public_safety_2_wave1_retry5_20260722.v3.task.json';priority=-100;single_runner_only=$true;new_runner=$false;parallel_runner=$false;requested_at=[DateTimeOffset]::UtcNow.ToString('o');final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false};Atomic $signal (($o|ConvertTo-Json -Depth 8)+"`n");return $true}
function WaitDaemon([int]$seconds){$end=(Get-Date).AddSeconds($seconds);do{$d=@(Procs @('RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707'));if($d.Count-gt0){return$d};Start-Sleep -Seconds 2}while((Get-Date)-lt$end);return@(Procs @('RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707'))}
function HeartbeatAgeMinutes{$h=ReadJson $heartbeat;if(-not$h-or-not$h.heartbeat_at){return $null};try{return [math]::Round(([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse([string]$h.heartbeat_at)).TotalMinutes,2)}catch{return $null}}
if(-not(Test-Path -LiteralPath $repoRoot -PathType Container)){throw"CANONICAL_F_REPO_ROOT_MISSING=$repoRoot"}
if(-not(Test-Path -LiteralPath $repoEntry -PathType Leaf)){Result 'BLOCKED_CANONICAL_REPO_ENTRY_MISSING' $false $false 0 0 0 $false $false $null $repoEntry;exit 2}
$patterns=@([regex]::Escape($launcher),[regex]::Escape($repoEntry),'RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK','RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709','RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707','RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707')
$before=@(Procs $patterns);$daemons=@(Procs @('RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707'));$age=HeartbeatAgeMinutes
if($daemons.Count-gt1){Result 'BLOCKED_MULTIPLE_PERSISTENT_DAEMONS' $false $false $before.Count $before.Count $daemons.Count $false $false $age 'Fail closed; multiple daemon processes observed.';exit 3}
if($daemons.Count-eq1){
  if($null-ne$age-and$age-gt$StaleMinutes){
    if($before.Count-gt3){Result 'BLOCKED_AMBIGUOUS_STALE_CANONICAL_PROCESS_SET' $false $false $before.Count $before.Count 1 $false $false $age 'More than three matching canonical processes observed.';exit 3}
    $workers=@(Procs @('RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707'))
    foreach($p in $workers){if([int]$p.ProcessId-ne[int]$daemons[0].ProcessId){Stop-Process -Id ([int]$p.ProcessId) -Force -ErrorAction SilentlyContinue}}
    Stop-Process -Id ([int]$daemons[0].ProcessId) -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    $remain=@(Procs $patterns)
    if($remain.Count-gt0){Result 'BLOCKED_STALE_CANONICAL_PROCESS_STOP_NOT_CONFIRMED' $true $false $before.Count $remain.Count 0 $false $false $age (($remain|ForEach-Object{$_.ProcessId})-join ',');exit 4}
    $p=Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c',('"'+$launcher+'"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal
    $newDaemons=@(WaitDaemon 45);$after=@(Procs $patterns)
    if($newDaemons.Count-ne1){Result 'BLOCKED_STALE_DAEMON_RESTART_NOT_CONFIRMED' $true $false $before.Count $after.Count $newDaemons.Count $false $true $age "launcher_pid=$($p.Id)";exit 4}
    $signalWritten=SignalIfAbsent
    Result 'STALE_CANONICAL_DAEMON_RESTARTED_SINGLE_INSTANCE' $true $true $before.Count $after.Count 1 $signalWritten $true $age "launcher_pid=$($p.Id)";exit 0
  }
  $signalWritten=SignalIfAbsent
  Result 'CANONICAL_DAEMON_ACTIVE_REFRESH_REQUEST_AVAILABLE' $false $false $before.Count $before.Count 1 $signalWritten $false $age 'Existing daemon preserved; an existing shared signal also triggers a full queue refresh.';exit 0
}
if($before.Count-gt1){Result 'BLOCKED_MULTIPLE_NON_DAEMON_CANONICAL_PROCESSES' $false $false $before.Count $before.Count 0 $false $false $age 'Fail closed';exit 3}
if($before.Count-eq1){
  $waited=@(WaitDaemon 30)
  if($waited.Count-eq1){$signalWritten=SignalIfAbsent;Result 'CANONICAL_DAEMON_APPEARED_NO_SECOND_PROCESS' $false $false 1 (@(Procs $patterns).Count) 1 $signalWritten $false $age 'Existing launcher completed daemon startup.';exit 0}
  Result 'CANONICAL_TRANSIENT_PROCESS_ACTIVE_NO_SECOND_PROCESS' $false $false 1 1 0 $false $false $age 'Existing process preserved; no second process started.';exit 0
}
$detail='';if(Test-Path -LiteralPath $launcher -PathType Leaf){$p=Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c',('"'+$launcher+'"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal;$detail="canonical_cmd_pid=$($p.Id)"}
$daemons=@(WaitDaemon 45);$after=@(Procs $patterns)
if($daemons.Count-eq0-and$after.Count-eq0){$p=Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$repoEntry+'"')) -WorkingDirectory $repoRoot -PassThru -WindowStyle Normal;$detail=($detail+';repo_devam_pid='+$p.Id).TrimStart(';');$daemons=@(WaitDaemon 45);$after=@(Procs $patterns)}
if($daemons.Count-gt1){Result 'BLOCKED_MULTIPLE_DAEMONS_AFTER_START' $true $false 0 $after.Count $daemons.Count $false $false $age $detail;exit 3}
if($daemons.Count-eq0){Result 'BLOCKED_CANONICAL_RUNNER_START_NOT_OBSERVED' $true $false 0 $after.Count 0 $false $false $age $detail;exit 4}
$signalWritten=SignalIfAbsent
Result 'EXISTING_CANONICAL_DAEMON_STARTED_SINGLE_INSTANCE' $true $true 0 $after.Count 1 $signalWritten $false $age $detail
exit 0

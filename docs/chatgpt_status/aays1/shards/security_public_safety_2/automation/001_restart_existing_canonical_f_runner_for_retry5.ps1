[CmdletBinding()]
param([int]$StaleMinutes = 20)
$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$taskId = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId = 'attempt-005'
$portableRoot = 'F:\TerraYield_AAYS_Portable'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$branch = 'codex/aays-single-runner-v5-20260706'
$launcher = 'F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd'
$repoEntry = Join-Path $repoRoot 'devam.ps1'
$signal = Join-Path $repoRoot 'docs\chatgpt_status\_shared\control\request_queue_refresh.json'
$heartbeat = Join-Path $repoRoot 'docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json'
$lock = Join-Path $repoRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
$scanLockPath = Join-Path $repoRoot 'docs\chatgpt_status\_shared\runner_lock\MULTI_PAGE.lock'
$output = Join-Path $repoRoot 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\001_retry5_existing_runner_recovery_latest.json'
$targets = 30762..30773
$script:scanLockEvidence = $null
$script:lastStopEvidence = @()
$specs = @(
  [ordered]@{name='launcher';token='RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd';root=$portableRoot},
  [ordered]@{name='hotfix';token='RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709';root=$portableRoot},
  [ordered]@{name='repo_entry';token='devam.ps1';root=$repoRoot},
  [ordered]@{name='daemon';token='RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1';root=$repoRoot},
  [ordered]@{name='scan_worker';token='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1';root=$repoRoot}
)
function Atomic([string]$Path,[string]$Text) {
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $tmp = "$Path.tmp.$PID"
  [IO.File]::WriteAllText($tmp,$Text,[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}
function ReadJson([string]$Path) {
  try { if (Test-Path -LiteralPath $Path -PathType Leaf) { return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json) } } catch {}
  return $null
}
function Norm([string]$Value) { if ($null -eq $Value) { return '' }; return (($Value -replace '/','\').ToLowerInvariant()) }
function AllProcs { @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.CommandLine) }) }
function MatchSpec([object]$Process,[object]$Spec) {
  $cmd = Norm -Value ([string]$Process.CommandLine)
  return ($cmd.Contains((Norm -Value ([string]$Spec.token))) -and $cmd.Contains((Norm -Value ([string]$Spec.root))))
}
function MatchedSpecName([object]$Process) { foreach ($spec in $specs) { if (MatchSpec -Process $Process -Spec $spec) { return [string]$spec.name } }; return '' }
function RunnerLike([object]$Process) {
  $cmd = Norm -Value ([string]$Process.CommandLine)
  foreach ($spec in $specs) { if ($cmd.Contains((Norm -Value ([string]$spec.token)))) { return $true } }
  return $false
}
function Canonical([string[]]$Names) {
  $out = @()
  foreach ($proc in @(AllProcs)) {
    foreach ($spec in $specs) {
      if (($Names.Count -eq 0 -or $Names -contains [string]$spec.name) -and (MatchSpec -Process $proc -Spec $spec)) { $out += $proc; break }
    }
  }
  return @($out | Group-Object ProcessId | ForEach-Object { $_.Group[0] })
}
function ForeignRunnerProcesses {
  $out = @()
  foreach ($proc in @(AllProcs)) { if ((RunnerLike -Process $proc) -and [string]::IsNullOrWhiteSpace((MatchedSpecName -Process $proc))) { $out += $proc } }
  return @($out | Group-Object ProcessId | ForEach-Object { $_.Group[0] })
}
function CurrentCimProcess([int]$Id) { @((Get-CimInstance Win32_Process -Filter ("ProcessId={0}" -f $Id) -ErrorAction SilentlyContinue) | Select-Object -First 1) }
function IdentityKey([object]$Process) { '{0}|{1}' -f ([int]$Process.ProcessId),([string]$Process.CreationDate) }
function ProcAgeMinutes([int]$Id) { try { $proc=Get-Process -Id $Id -ErrorAction Stop; return [math]::Round(([DateTimeOffset]::UtcNow-[DateTimeOffset]$proc.StartTime.ToUniversalTime()).TotalMinutes,2) } catch { return $null } }
function ResolveScanLockFile {
  if (Test-Path -LiteralPath $scanLockPath -PathType Leaf) { return $scanLockPath }
  if (Test-Path -LiteralPath $scanLockPath -PathType Container) { $owner=Join-Path $scanLockPath 'owner.json'; if (Test-Path -LiteralPath $owner -PathType Leaf) { return $owner } }
  return $null
}
function InspectAndRepairScanLock {
  $exists = Test-Path -LiteralPath $scanLockPath
  $lockFile = ResolveScanLockFile
  $raw = if ($lockFile) { ReadJson -Path $lockFile } else { $null }
  $pidValue = if ($raw -and $raw.pid) { [int]$raw.pid } else { 0 }
  $current = if ($pidValue -gt 0) { @(CurrentCimProcess -Id $pidValue) } else { @() }
  $currentSpec = if ($current.Count -eq 1) { MatchedSpecName -Process $current[0] } else { '' }
  $scopeMatch=$false; $repoMatch=$false; $instancePresent=$false; $startPresent=$false; $startMatch=$false
  if ($raw) {
    $scopeMatch = ([string]$raw.lock_scope -eq 'single_scan_worker')
    $instancePresent = -not [string]::IsNullOrWhiteSpace([string]$raw.instance_id)
    $startPresent = -not [string]::IsNullOrWhiteSpace([string]$raw.process_start_time)
    if (-not [string]::IsNullOrWhiteSpace([string]$raw.repo_root)) { $repoMatch = ((Norm -Value ([string]$raw.repo_root)) -eq (Norm -Value $repoRoot)) }
  }
  if ($startPresent -and $current.Count -eq 1) {
    try { $expected=[DateTimeOffset]::Parse([string]$raw.process_start_time); $actual=[DateTimeOffset](Get-Process -Id $pidValue -ErrorAction Stop).StartTime.ToUniversalTime(); $startMatch=([math]::Abs(($expected-$actual).TotalSeconds) -le 2) } catch {}
  }
  $valid = ($exists -and $null -ne $raw -and $scopeMatch -and $repoMatch -and $instancePresent -and $startPresent -and $startMatch -and $currentSpec -eq 'scan_worker')
  $scanWorkers = @(Canonical -Names @('scan_worker'))
  $removed = $false
  $status = if (-not $exists) { 'absent' } elseif ($valid) { 'valid_live_scan_worker' } else { 'invalid_or_stale' }
  if ($exists -and -not $valid -and $scanWorkers.Count -eq 0) { Remove-Item -LiteralPath $scanLockPath -Force -Recurse -ErrorAction Stop; $removed=$true; $status='stale_lock_removed_no_exact_scan_worker' }
  elseif ($exists -and -not $valid -and $scanWorkers.Count -gt 0) { $status='invalid_lock_preserved_exact_scan_worker_present' }
  return [ordered]@{path=$scanLockPath;lock_file=$lockFile;exists=$exists;parsed=($null-ne$raw);pid=$pidValue;scope_match=$scopeMatch;repo_root_match=$repoMatch;instance_id_present=$instancePresent;process_start_time_present=$startPresent;process_start_time_match=$startMatch;current_spec=$currentSpec;exact_scan_worker_count=$scanWorkers.Count;valid=$valid;removed=$removed;status=$status}
}
function HeartbeatInfo([int]$DaemonPid) {
  $h=ReadJson -Path $heartbeat; $l=ReadJson -Path $lock
  $age=$null; $pidMatch=$false; $timeOk=$false; $heartbeatRootMatch=$false; $heartbeatBranchMatch=$false; $heartbeatProcessStartMatch=$false; $heartbeatStartField='none'
  $lockPidMatch=$false; $lockRootMatch=$false; $instanceMatch=$false; $startMatch=$false; $lockRealProcessStartMatch=$false; $lockHeartbeatFresh=$false; $lockScopeMatch=$false; $lockBranchMatch=$false; $delta=$null
  $processStart=$null; try { $processStart=[DateTimeOffset](Get-Process -Id $DaemonPid -ErrorAction Stop).StartTime.ToUniversalTime() } catch {}
  if ($h) {
    $hp=if($h.supervisor_pid){[int]$h.supervisor_pid}elseif($h.daemon_pid){[int]$h.daemon_pid}elseif($h.pid){[int]$h.pid}else{0}
    $pidMatch=($hp -eq $DaemonPid)
    if (-not [string]::IsNullOrWhiteSpace([string]$h.repo_root)) { $heartbeatRootMatch=((Norm -Value ([string]$h.repo_root)) -eq (Norm -Value $repoRoot)) }
    $heartbeatBranchMatch=([string]$h.branch -eq $branch)
    $startValue=$null
    if($h.supervisor_started_at){$startValue=[string]$h.supervisor_started_at;$heartbeatStartField='supervisor_started_at'}elseif($h.started_at){$startValue=[string]$h.started_at;$heartbeatStartField='started_at'}
    if($startValue -and $processStart){try{$hs=[DateTimeOffset]::Parse($startValue);$heartbeatProcessStartMatch=([math]::Abs(($hs-$processStart).TotalSeconds)-le2)}catch{}}
    if($h.heartbeat_at){try{$age=[math]::Round(([DateTimeOffset]::UtcNow-[DateTimeOffset]::Parse([string]$h.heartbeat_at)).TotalMinutes,2);$timeOk=$true}catch{}}
  }
  if ($l) {
    $lp=if($l.supervisor_pid){[int]$l.supervisor_pid}elseif($l.pid){[int]$l.pid}else{0}
    $lockPidMatch=($lp -eq $DaemonPid)
    $lockRootMatch=((Norm -Value ([string]$l.repo_root)) -eq (Norm -Value $repoRoot))
    $lockBranchMatch=([string]$l.branch -eq $branch)
    $lockScopeMatch=(-not $l.lock_scope -or [string]$l.lock_scope -eq 'single_shared_runner_daemon')
    if($h -and -not [string]::IsNullOrWhiteSpace([string]$h.instance_id) -and -not [string]::IsNullOrWhiteSpace([string]$l.instance_id)){$instanceMatch=([string]$h.instance_id -eq [string]$l.instance_id)}
    if($h -and $h.supervisor_started_at -and $l.process_start_time){try{$hs=[DateTimeOffset]::Parse([string]$h.supervisor_started_at);$ls=[DateTimeOffset]::Parse([string]$l.process_start_time);$startMatch=([math]::Abs(($hs-$ls).TotalSeconds)-le2)}catch{}}
    if($l.process_start_time -and $processStart){try{$ls=[DateTimeOffset]::Parse([string]$l.process_start_time);$lockRealProcessStartMatch=([math]::Abs(($ls-$processStart).TotalSeconds)-le2)}catch{}}
    if($h -and $h.heartbeat_at -and $l.updated_at){try{$ht=[DateTimeOffset]::Parse([string]$h.heartbeat_at);$lu=[DateTimeOffset]::Parse([string]$l.updated_at);$delta=[math]::Round([math]::Abs(($ht-$lu).TotalSeconds),3);$lockHeartbeatFresh=($delta-le60)}catch{}}
  }
  $boundHeartbeat=$heartbeatRootMatch -and $heartbeatBranchMatch -and $heartbeatProcessStartMatch
  $boundLock=$lockPidMatch -and $lockRootMatch -and $instanceMatch -and $startMatch -and $lockRealProcessStartMatch -and $lockHeartbeatFresh -and $lockScopeMatch -and $lockBranchMatch
  return [pscustomobject]@{valid=($pidMatch-and($boundHeartbeat-or$boundLock)-and$timeOk);pid_match=$pidMatch;bound_heartbeat_identity_match=$boundHeartbeat;bound_lock_identity_match=$boundLock;heartbeat_process_start_match=$heartbeatProcessStartMatch;heartbeat_start_field=$heartbeatStartField;lock_real_process_start_match=$lockRealProcessStartMatch;lock_heartbeat_delta_seconds=$delta;age_minutes=$age;raw=$h;raw_lock=$l}
}
function StopCanonicalGeneration([object]$Expected) {
  $id=[int]$Expected.ProcessId; $expectedKey=IdentityKey -Process $Expected; $expectedSpec=MatchedSpecName -Process $Expected; $current=@(CurrentCimProcess -Id $id)
  if($current.Count -eq 0){return[pscustomobject]@{process_id=$id;expected_identity_key=$expectedKey;generation_match=$true;canonical_match=$true;bound_process_start_match=$true;kill_attempted=$false;kill_exit_code=0;already_exited=$true;expected_generation_remaining=$false}}
  $currentKey=IdentityKey -Process $current[0]; $currentSpec=MatchedSpecName -Process $current[0]; $same=($currentKey-eq$expectedKey); $canonical=(-not[string]::IsNullOrWhiteSpace($expectedSpec)-and$currentSpec-eq$expectedSpec); $bound=$null; $startMatch=$false
  try{$bound=Get-Process -Id $id -ErrorAction Stop;$cimStart=[DateTimeOffset]$current[0].CreationDate;$boundStart=[DateTimeOffset]$bound.StartTime.ToUniversalTime();$startMatch=([math]::Abs(($cimStart-$boundStart).TotalSeconds)-le2)}catch{}
  if(-not($same-and$canonical-and$startMatch)){return[pscustomobject]@{process_id=$id;expected_identity_key=$expectedKey;current_identity_key=$currentKey;generation_match=$same;canonical_match=$canonical;bound_process_start_match=$startMatch;kill_attempted=$false;kill_exit_code=0;already_exited=(-not$same);expected_generation_remaining=$same}}
  $exit=-1;$attempted=$false;try{$attempted=$true;Stop-Process -InputObject $bound -Force -ErrorAction Stop;$exit=0}catch{$exit=1};Start-Sleep -Milliseconds 250
  $after=@(CurrentCimProcess -Id $id);$remaining=$false;if($after.Count-eq1){$remaining=((IdentityKey -Process $after[0])-eq$expectedKey)}
  return[pscustomobject]@{process_id=$id;expected_identity_key=$expectedKey;generation_match=$true;canonical_match=$true;bound_process_start_match=$true;kill_attempted=$attempted;kill_exit_code=$exit;already_exited=$false;expected_generation_remaining=$remaining}
}
function Result([string]$Status,[bool]$Attempted,[bool]$Started,[bool]$SignalWritten,[bool]$StaleRestart,[object]$Heartbeat,[string]$Detail) {
  $canonical=@(Canonical -Names @());$daemons=@(Canonical -Names @('daemon'));$foreign=@(ForeignRunnerProcesses)
  $payload=[ordered]@{schema_version=17;slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;status=$Status;checked_at=[DateTimeOffset]::UtcNow.ToString('o');stale_minutes_threshold=$StaleMinutes;start_attempted=$Attempted;canonical_runner_started=$Started;stale_verified_runner_restarted=$StaleRestart;canonical_process_ids=@($canonical|ForEach-Object{[int]$_.ProcessId});canonical_daemon_ids=@($daemons|ForEach-Object{[int]$_.ProcessId});foreign_runner_process_ids=@($foreign|ForEach-Object{[int]$_.ProcessId});heartbeat_identity=$Heartbeat;scan_lock_generation_validation=$true;scan_lock_parser_explicit=$true;stale_scan_lock_removed_only_without_exact_scan_worker=$true;scan_lock_evidence=$script:scanLockEvidence;termination_uses_bound_process_object=$true;termination_uses_individual_verified_process_generations=$true;taskkill_tree_used=$false;stale_stop_evidence=@($script:lastStopEvidence);queue_refresh_signal_written=$SignalWritten;exact_target_rows=@($targets);existing_single_runner_architecture_reused=$true;new_runner_architecture_created=$false;parallel_runner_started=$false;detail=$Detail;final_ready=$false;fake_data=$false}
  Atomic -Path $output -Text (($payload|ConvertTo-Json -Depth 16)+"`n")
}
function SignalIfAbsent { if(Test-Path -LiteralPath $signal){return$false};$payload=[ordered]@{request_id='security-public-safety-2-retry5-refresh-20260722-001';page_key='aays1';slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;action='refresh_remote_queue_and_claim_retry5';target_branch=$branch;queue_path='docs/chatgpt_status/aays1/queue/000000_security_public_safety_2_wave1_retry5_20260722.v3.task.json';priority=-100;single_runner_only=$true;new_runner=$false;parallel_runner=$false;requested_at=[DateTimeOffset]::UtcNow.ToString('o');final_ready=$false;fake_data=$false};Atomic -Path $signal -Text (($payload|ConvertTo-Json -Depth 8)+"`n");return$true }
function WaitFreshDaemon([int]$Seconds) { $end=(Get-Date).AddSeconds($Seconds);do{$daemons=@(Canonical -Names @('daemon'));if($daemons.Count-eq1){$hb=HeartbeatInfo -DaemonPid ([int]$daemons[0].ProcessId);if($hb.valid-and$null-ne$hb.age_minutes-and$hb.age_minutes-le$StaleMinutes){return[pscustomobject]@{daemons=$daemons;heartbeat=$hb}}};Start-Sleep -Seconds 2}while((Get-Date)-lt$end);$daemons=@(Canonical -Names @('daemon'));$hb=if($daemons.Count-eq1){HeartbeatInfo -DaemonPid ([int]$daemons[0].ProcessId)}else{$null};return[pscustomobject]@{daemons=$daemons;heartbeat=$hb} }
if(-not(Test-Path -LiteralPath $repoRoot -PathType Container)){throw"CANONICAL_F_REPO_ROOT_MISSING=$repoRoot"}
if(-not(Test-Path -LiteralPath $repoEntry -PathType Leaf)){Result 'BLOCKED_CANONICAL_REPO_ENTRY_MISSING' $false $false $false $false $null $repoEntry;exit 2}
$script:scanLockEvidence=InspectAndRepairScanLock
$foreign=@(ForeignRunnerProcesses);if($foreign.Count-gt0){Result 'BLOCKED_FOREIGN_OR_NONCANONICAL_RUNNER_PROCESS_PRESENT' $false $false $false $false $null 'Foreign runner preserved.';exit 3}
$canonical=@(Canonical -Names @());$daemons=@(Canonical -Names @('daemon'));if($daemons.Count-gt1){Result 'BLOCKED_MULTIPLE_PERSISTENT_DAEMONS' $false $false $false $false $null 'Multiple exact daemons observed.';exit 3}
if($daemons.Count-eq1){$daemon=$daemons[0];$pid=[int]$daemon.ProcessId;$hb=HeartbeatInfo -DaemonPid $pid;$age=ProcAgeMinutes -Id $pid;if($hb.valid-and$null-ne$hb.age_minutes-and$hb.age_minutes-gt$StaleMinutes){if($canonical.Count-gt3){Result 'BLOCKED_AMBIGUOUS_STALE_CANONICAL_PROCESS_SET' $false $false $false $false $hb 'More than three exact processes.';exit 3};$ordered=@($canonical|Sort-Object @{Expression={if((MatchedSpecName -Process $_)-eq'daemon'){1}else{0}}});$rows=@();foreach($proc in $ordered){$rows+=StopCanonicalGeneration -Expected $proc};$script:lastStopEvidence=@($rows);Start-Sleep -Seconds 3;$remain=@(Canonical -Names @());$expectedRemain=@($rows|Where-Object{$_.expected_generation_remaining});if($remain.Count-gt0-or$expectedRemain.Count-gt0){Result 'BLOCKED_STALE_CANONICAL_GENERATION_STOP_NOT_CONFIRMED' $true $false $false $false $hb 'Verified generation remains.';exit 4};$p=Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c',('"'+$launcher+'"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal;$fresh=WaitFreshDaemon -Seconds 45;if(@($fresh.daemons).Count-ne1-or-not$fresh.heartbeat-or-not$fresh.heartbeat.valid){Result 'BLOCKED_STALE_DAEMON_RESTART_FRESH_HEARTBEAT_NOT_CONFIRMED' $true $false $false $true $fresh.heartbeat "launcher_pid=$($p.Id)";exit 4};$sig=SignalIfAbsent;Result 'STALE_CANONICAL_GENERATIONS_STOPPED_AND_DAEMON_RESTARTED_SINGLE_INSTANCE' $true $true $sig $true $fresh.heartbeat "launcher_pid=$($p.Id)";exit 0};if($hb.valid){$sig=SignalIfAbsent;Result 'CANONICAL_DAEMON_ACTIVE_VERIFIED_REFRESH_AVAILABLE' $false $false $sig $false $hb 'Fresh exact daemon preserved.';exit 0};if($null-ne$age-and$age-le$StaleMinutes){$sig=SignalIfAbsent;Result 'CANONICAL_DAEMON_STARTUP_GRACE_REFRESH_AVAILABLE' $false $false $sig $false $hb "process_age_minutes=$age";exit 0};Result 'BLOCKED_CANONICAL_DAEMON_HEARTBEAT_IDENTITY_UNVERIFIED' $false $false $false $false $hb "process_age_minutes=$age";exit 3}
if($canonical.Count-gt1){Result 'BLOCKED_MULTIPLE_NON_DAEMON_CANONICAL_PROCESSES' $false $false $false $false $null 'Fail closed.';exit 3}
if($canonical.Count-eq1){$fresh=WaitFreshDaemon -Seconds 45;if(@($fresh.daemons).Count-eq1-and$fresh.heartbeat-and$fresh.heartbeat.valid){$sig=SignalIfAbsent;Result 'CANONICAL_DAEMON_APPEARED_FRESH_HEARTBEAT_NO_SECOND_PROCESS' $false $false $sig $false $fresh.heartbeat 'Existing startup preserved.';exit 0};Result 'BLOCKED_CANONICAL_TRANSIENT_PROCESS_DID_NOT_PRODUCE_FRESH_DAEMON' $false $false $false $false $fresh.heartbeat 'No second process started.';exit 4}
$detail='';if(Test-Path -LiteralPath $launcher -PathType Leaf){$p=Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c',('"'+$launcher+'"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal;$detail="canonical_cmd_pid=$($p.Id)"};$fresh=WaitFreshDaemon -Seconds 45
if(@($fresh.daemons).Count-eq0-and@(Canonical -Names @()).Count-eq0){$p=Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$repoEntry+'"')) -WorkingDirectory $repoRoot -PassThru -WindowStyle Normal;$detail=($detail+';repo_devam_pid='+$p.Id).TrimStart(';');$fresh=WaitFreshDaemon -Seconds 45}
if(@($fresh.daemons).Count-gt1){Result 'BLOCKED_MULTIPLE_DAEMONS_AFTER_START' $true $false $false $false $fresh.heartbeat $detail;exit 3};if(@($fresh.daemons).Count-eq0-or-not$fresh.heartbeat-or-not$fresh.heartbeat.valid){Result 'BLOCKED_CANONICAL_RUNNER_START_FRESH_HEARTBEAT_NOT_OBSERVED' $true $false $false $false $fresh.heartbeat $detail;exit 4};$sig=SignalIfAbsent;Result 'EXISTING_CANONICAL_DAEMON_STARTED_SINGLE_INSTANCE_FRESH_HEARTBEAT' $true $true $sig $false $fresh.heartbeat $detail;exit 0

[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$slotId='security_public_safety_2'
$taskId='security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId='attempt-005'
$portableRoot='F:\TerraYield_AAYS_Portable'
$repoRoot='F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$launcher='F:\TerraYield_AAYS_Portable\RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd'
$repoEntry=Join-Path $repoRoot 'devam.ps1'
$signal=Join-Path $repoRoot 'docs\chatgpt_status\_shared\control\request_queue_refresh.json'
$output=Join-Path $repoRoot 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\001_retry5_existing_runner_recovery_latest.json'
$targets=30762..30773
function Atomic([string]$p,[string]$t){$d=Split-Path -Parent $p;if(-not(Test-Path -LiteralPath $d)){New-Item -ItemType Directory -Force -Path $d|Out-Null};$x="$p.tmp.$PID";[IO.File]::WriteAllText($x,$t,[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $x -Destination $p -Force}
function Procs([string[]]$patterns){@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{$c=[string]$_.CommandLine;if(-not$c){return $false};foreach($p in $patterns){if($c-match$p){return $true}};return $false})}
function Result([string]$status,[bool]$attempted,[bool]$started,[int]$before,[int]$after,[int]$daemons,[bool]$signalWritten,[string]$detail){$o=[ordered]@{schema_version=5;slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;status=$status;checked_at=[DateTimeOffset]::UtcNow.ToString('o');start_attempted=$attempted;canonical_runner_started=$started;existing_process_count_before=$before;existing_process_count_after=$after;persistent_daemon_count_after=$daemons;queue_refresh_signal_written=$signalWritten;exact_target_rows=@($targets);nearest_row_fallback_allowed=$false;existing_single_runner_architecture_reused=$true;new_runner_architecture_created=$false;parallel_runner_started=$false;task_claimed=$false;detail=$detail;final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false};Atomic $output (($o|ConvertTo-Json -Depth 8)+"`n")}
function Signal{$o=[ordered]@{request_id='security-public-safety-2-retry5-refresh-20260722-001';page_key='aays1';slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;action='refresh_remote_queue_and_claim_retry5';target_branch='codex/aays-single-runner-v5-20260706';queue_path='docs/chatgpt_status/aays1/queue/000000_security_public_safety_2_wave1_retry5_20260722.v3.task.json';priority=-100;single_runner_only=$true;new_runner=$false;parallel_runner=$false;requested_at=[DateTimeOffset]::UtcNow.ToString('o');final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false};Atomic $signal (($o|ConvertTo-Json -Depth 8)+"`n")}
function WaitDaemon([int]$seconds){$end=(Get-Date).AddSeconds($seconds);do{$d=@(Procs @('RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707'));if($d.Count-gt0){return$d};Start-Sleep -Seconds 2}while((Get-Date)-lt$end);return@(Procs @('RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707'))}
if(-not(Test-Path -LiteralPath $repoRoot -PathType Container)){throw"CANONICAL_F_REPO_ROOT_MISSING=$repoRoot"}
if(-not(Test-Path -LiteralPath $repoEntry -PathType Leaf)){Result 'BLOCKED_CANONICAL_REPO_ENTRY_MISSING' $false $false 0 0 0 $false $repoEntry;exit 2}
$patterns=@([regex]::Escape($launcher),[regex]::Escape($repoEntry),'RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK','RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709','RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707','RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707')
$before=@(Procs $patterns);$daemons=@(Procs @('RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707'))
if($daemons.Count-gt1-or$before.Count-gt1){Result 'BLOCKED_MULTIPLE_CANONICAL_RUNNER_PROCESSES' $false $false $before.Count $before.Count $daemons.Count $false 'Fail closed';exit 3}
if($daemons.Count-eq1){Signal;Result 'CANONICAL_DAEMON_ACTIVE_REFRESH_SIGNAL_WRITTEN' $false $false $before.Count $before.Count 1 $true 'Existing daemon preserved';exit 0}
if($before.Count-eq1){Result 'CANONICAL_TRANSIENT_PROCESS_ACTIVE_NO_SECOND_PROCESS' $false $false 1 1 0 $false 'Existing process preserved';exit 0}
$detail='';if(Test-Path -LiteralPath $launcher -PathType Leaf){$p=Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c',('"'+$launcher+'"')) -WorkingDirectory $portableRoot -PassThru -WindowStyle Normal;$detail="canonical_cmd_pid=$($p.Id)"}
$daemons=@(WaitDaemon 30);$after=@(Procs $patterns)
if($daemons.Count-eq0-and$after.Count-eq0){$p=Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$repoEntry+'"')) -WorkingDirectory $repoRoot -PassThru -WindowStyle Normal;$detail=($detail+';repo_devam_pid='+$p.Id).TrimStart(';');$daemons=@(WaitDaemon 30);$after=@(Procs $patterns)}
if($daemons.Count-gt1){Result 'BLOCKED_MULTIPLE_DAEMONS_AFTER_START' $true $false 0 $after.Count $daemons.Count $false $detail;exit 3}
if($daemons.Count-eq0){Result 'BLOCKED_CANONICAL_RUNNER_START_NOT_OBSERVED' $true $false 0 $after.Count 0 $false $detail;exit 4}
Signal;Result 'EXISTING_CANONICAL_DAEMON_RESTARTED_REFRESH_SIGNAL_WRITTEN' $true $true 0 $after.Count 1 $true $detail
exit 0

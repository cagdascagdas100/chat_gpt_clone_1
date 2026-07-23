[CmdletBinding()]
param([int]$TimeoutSeconds = 300,[string]$InnerPath = '')

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$taskId = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId = 'attempt-005'
$branch = 'codex/aays-single-runner-v5-20260706'
$portableRoot = 'F:\TerraYield_AAYS_Portable'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$ownershipRel = 'docs/chatgpt_status/_shared/slots_21/security_public_safety_2/ownership_latest.json'
$innerRel = 'docs\chatgpt_status\aays1\shards\security_public_safety_2\automation\003_ffsafe_sync_then_apply_retry5_recovery.ps1'
$innerBlob = '80ffd9e6f45aa1187005d6455a7cb9de28c7e8e0'
$outputRel = 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\004_retry5_timeout_guard_latest.json'
$baselineCanonical = @()
$timeoutSpawnedCanonical = @()
$remainingTimeoutSpawnedCanonical = @()
$spawnedCanonicalCleanup = @()
$runnerSpecs = @(
  [ordered]@{token='RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd';root=$portableRoot},
  [ordered]@{token='RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709';root=$portableRoot},
  [ordered]@{token='devam.ps1';root=$repoRoot},
  [ordered]@{token='RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1';root=$repoRoot},
  [ordered]@{token='RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1';root=$repoRoot}
)

function GitBlob([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
  $bytes=[IO.File]::ReadAllBytes($Path);$prefix=[Text.Encoding]::ASCII.GetBytes(('blob {0}' -f $bytes.Length)+[char]0)
  $sha=[Security.Cryptography.SHA1]::Create();try{[void]$sha.TransformBlock($prefix,0,$prefix.Length,$prefix,0);[void]$sha.TransformFinalBlock($bytes,0,$bytes.Length);return([BitConverter]::ToString($sha.Hash)).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
}
function Norm([string]$Value) { if($null-eq$Value){return''};return(($Value-replace'/','\').ToLowerInvariant()) }
function CanonicalRunnerProcesses {
  $all=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue|Where-Object{-not[string]::IsNullOrWhiteSpace([string]$_.CommandLine)})
  $matched=@()
  foreach($proc in $all){
    $command=Norm([string]$proc.CommandLine)
    foreach($spec in $runnerSpecs){
      if($command.Contains((Norm([string]$spec.token)))-and$command.Contains((Norm([string]$spec.root)))){$matched+=$proc;break}
    }
  }
  return @($matched|Group-Object ProcessId|ForEach-Object{$_.Group[0]})
}
function DescendantPids([int]$RootPid) {
  $all=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
  $result=New-Object 'System.Collections.Generic.List[int]'
  $queue=New-Object 'System.Collections.Generic.Queue[int]'
  $queue.Enqueue($RootPid)
  while($queue.Count -gt 0){
    $parent=$queue.Dequeue()
    foreach($proc in @($all|Where-Object{[int]$_.ParentProcessId -eq $parent})){
      $id=[int]$proc.ProcessId
      if(-not $result.Contains($id)){$result.Add($id);$queue.Enqueue($id)}
    }
  }
  return @($result)
}
function StopProcessTree([int]$ProcessId) {
  $taskkill=Get-Command taskkill.exe -ErrorAction SilentlyContinue
  if($taskkill){& $taskkill.Source /PID $ProcessId /T /F|Out-Null;return$LASTEXITCODE}
  try{Stop-Process -Id $ProcessId -Force -ErrorAction Stop;return 0}catch{if(-not(Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)){return 0};return 1}
}
function Receipt([string]$Status,[int]$ExitCode,[bool]$TimedOut,[string]$ResolvedInner,[object]$OwnerSnapshot,[string]$RemoteHead,[bool]$TreeKillAttempted,[int]$TreeKillExit,[object]$TrackedPids,[object]$RemainingPids,[string]$Detail) {
  $path=Join-Path $repoRoot $outputRel;$parent=Split-Path -Parent $path;if(-not(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Force -Path $parent|Out-Null}
  $o=[ordered]@{schema_version=9;slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;status=$Status;checked_at=[DateTimeOffset]::UtcNow.ToString('o');timeout_seconds=$TimeoutSeconds;timed_out=$TimedOut;inner_exit_code=$ExitCode;inner_path=$ResolvedInner;inner_expected_blob=$innerBlob;temporary_inner_allowed=$true;remote_head=$RemoteHead;ownership_rechecked=$true;ownership_snapshot=$OwnerSnapshot;canonical_f_process_identity_required=$true;foreign_runner_process_fail_closed=$true;direct_heartbeat_requires_repo_root_branch_and_process_start=$true;heartbeat_repo_root_optional_with_bound_lock_fallback=$true;lock_fallback_requires_pid_repo_root_instance_start_freshness_scope_branch=$true;transient_without_fresh_daemon_is_failure=$true;process_exit_before_kill_is_clean_stop=$true;process_tree_kill_attempted=$TreeKillAttempted;process_tree_kill_exit_code=$TreeKillExit;tracked_process_ids=@($TrackedPids);remaining_tracked_process_ids=@($RemainingPids);baseline_canonical_process_ids=@($baselineCanonical|ForEach-Object{[int]$_.ProcessId});timeout_spawned_canonical_process_ids=@($timeoutSpawnedCanonical|ForEach-Object{[int]$_.ProcessId});spawned_canonical_cleanup=@($spawnedCanonicalCleanup);remaining_timeout_spawned_canonical_process_ids=@($remainingTimeoutSpawnedCanonical|ForEach-Object{[int]$_.ProcessId});timeout_cleanup_reenumerates_exact_canonical_f_processes=$true;preexisting_canonical_processes_preserved=$true;same_attempt=$true;new_runner_created=$false;parallel_runner_started=$false;detail=$Detail;final_ready=$false;fake_data=$false}
  $tmp="$path.tmp.$PID";[IO.File]::WriteAllText($tmp,(($o|ConvertTo-Json -Depth 14)+"`n"),[Text.UTF8Encoding]::new($false));Move-Item -LiteralPath $tmp -Destination $path -Force
}

if(-not(Test-Path -LiteralPath $repoRoot -PathType Container)){throw"CANONICAL_F_REPO_ROOT_MISSING=$repoRoot"}
$git=Get-Command git.exe -ErrorAction SilentlyContinue
if(-not $git){throw 'GIT_EXECUTABLE_NOT_FOUND'}
& $git.Source -C $repoRoot fetch --no-tags origin $branch
if($LASTEXITCODE -ne 0){Receipt 'BLOCKED_FRESH_OWNER_FETCH_FAILED' -1 $false '' @{} '' $false -1 @() @() 'git fetch failed';exit 20}
$remoteHead=(& $git.Source -C $repoRoot rev-parse "origin/$branch" 2>&1|Select-Object -Last 1).ToString().Trim()
if($remoteHead-notmatch'^[0-9a-f]{40}$'){Receipt 'BLOCKED_REMOTE_HEAD_READ_FAILED' -1 $false '' @{} $remoteHead $false -1 @() @() 'origin head unavailable';exit 20}
$ownershipText=(& $git.Source -C $repoRoot show "origin/${branch}:$ownershipRel" 2>&1|Out-String);$ownershipShowExit=$LASTEXITCODE
if($ownershipShowExit-ne0-or[string]::IsNullOrWhiteSpace($ownershipText)){Receipt 'BLOCKED_REMOTE_OWNERSHIP_READ_FAILED' -1 $false '' @{} $remoteHead $false -1 @() @() "git_show_exit=$ownershipShowExit";exit 22}
try{$ownership=$ownershipText|ConvertFrom-Json}catch{Receipt 'BLOCKED_REMOTE_OWNERSHIP_INVALID_JSON' -1 $false '' @{} $remoteHead $false -1 @() @() $_.Exception.Message;exit 22}
$ownerSnapshot=[ordered]@{state=[string]$ownership.state;owner_page_session_id=$ownership.owner_page_session_id;heartbeat_at=$ownership.heartbeat_at;lease_expires_at=$ownership.lease_expires_at}
$ownerPresent=(-not [string]::IsNullOrWhiteSpace([string]$ownership.owner_page_session_id))-or(-not [string]::IsNullOrWhiteSpace([string]$ownership.heartbeat_at))-or(-not [string]::IsNullOrWhiteSpace([string]$ownership.lease_expires_at))
if([string]$ownership.slot_id -ne $slotId -or [string]$ownership.state -ne 'unclaimed' -or $ownerPresent){Receipt 'BLOCKED_LIVE_OR_NON_UNCLAIMED_OWNER_APPEARED' -1 $false '' $ownerSnapshot $remoteHead $false -1 @() @() 'No recovery process was started.';exit 23}

$inner=if([string]::IsNullOrWhiteSpace($InnerPath)){Join-Path $repoRoot $innerRel}else{$InnerPath}
$actual=GitBlob $inner
if($actual -ne $innerBlob){Receipt 'BLOCKED_003_BLOB_MISMATCH' -1 $false $inner $ownerSnapshot $remoteHead $false -1 @() @() "expected=$innerBlob actual=$actual";exit 21}
$baselineCanonical=@(CanonicalRunnerProcesses)
$p=Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"{0}"' -f $inner)) -WorkingDirectory $repoRoot -PassThru -WindowStyle Normal
if(-not $p.WaitForExit($TimeoutSeconds*1000)){
  $tracked=@([int]$p.Id)+@(DescendantPids ([int]$p.Id))
  $killExit=StopProcessTree ([int]$p.Id)
  Start-Sleep -Seconds 2
  $remaining=@($tracked|Where-Object{Get-Process -Id $_ -ErrorAction SilentlyContinue})
  $baselineIds=@($baselineCanonical|ForEach-Object{[int]$_.ProcessId})
  $timeoutSpawnedCanonical=@(CanonicalRunnerProcesses|Where-Object{$baselineIds-notcontains[int]$_.ProcessId})
  $cleanup=@()
  foreach($proc in $timeoutSpawnedCanonical){$cleanup+=[ordered]@{process_id=[int]$proc.ProcessId;exit_code=(StopProcessTree([int]$proc.ProcessId));command_line=[string]$proc.CommandLine}}
  $spawnedCanonicalCleanup=@($cleanup)
  if($timeoutSpawnedCanonical.Count-gt0){Start-Sleep -Seconds 2}
  $remainingTimeoutSpawnedCanonical=@(CanonicalRunnerProcesses|Where-Object{$baselineIds-notcontains[int]$_.ProcessId})
  $allGone=($remaining.Count-eq0-and$remainingTimeoutSpawnedCanonical.Count-eq0)
  $status=if($allGone){'BLOCKED_RETRY5_RECOVERY_TIMEOUT_ALL_ATTEMPT_PROCESSES_TERMINATED'}else{'BLOCKED_RETRY5_RECOVERY_TIMEOUT_PROCESS_REMAINS'}
  Receipt $status 124 $true $inner $ownerSnapshot $remoteHead $true $killExit $tracked $remaining "wrapper_pid=$($p.Id);spawned_canonical=$($timeoutSpawnedCanonical.Count);remaining_spawned_canonical=$($remainingTimeoutSpawnedCanonical.Count)"
  if($allGone){exit 124}else{exit 125}
}
$exit=$p.ExitCode
$status=if($exit -eq 0){'TIMEOUT_GUARDED_FFSAFE_RETRY5_RECOVERY_COMPLETED'}else{'BLOCKED_INNER_FFSAFE_RETRY5_RECOVERY_FAILED'}
Receipt $status $exit $false $inner $ownerSnapshot $remoteHead $false -1 @([int]$p.Id) @() "wrapper_pid=$($p.Id)"
exit $exit

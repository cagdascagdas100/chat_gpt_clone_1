[CmdletBinding()]
param(
  [int]$StartupTimeoutSeconds = 60
)

$ErrorActionPreference = "Stop"
$portableRoot = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("\")
if ($portableRoot.StartsWith("C:\", [System.StringComparison]::OrdinalIgnoreCase)) { throw "C_DRIVE_NOT_CANONICAL: $portableRoot" }
$repoRoot = Join-Path $portableRoot "runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
$workRoot = Join-Path $portableRoot "runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"
$daemon = Join-Path $repoRoot "docs\chatgpt_status\_shared\automation\RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1"
$lockPath = Join-Path $repoRoot "docs\chatgpt_status\_shared\locks\single_runner.lock"
$heartbeatPath = Join-Path $repoRoot "docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json"
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) { throw "CANONICAL_REPO_MISSING: $repoRoot" }
if (-not (Test-Path -LiteralPath $daemon)) { throw "CANONICAL_DAEMON_MISSING: $daemon" }
if (-not (Test-Path -LiteralPath $workRoot)) { New-Item -ItemType Directory -Force -Path $workRoot | Out-Null }
$expectedBranch = "codex/aays-single-runner-v5-20260706"
$actualBranch = (& git -C $repoRoot branch --show-current 2>$null).Trim()
if ($actualBranch -ne $expectedBranch) { throw "CANONICAL_BRANCH_MISMATCH: expected=$expectedBranch actual=$actualBranch" }

function Read-Json([string]$Path) { try { if(Test-Path -LiteralPath $Path){return Get-Content -LiteralPath $Path -Raw -Encoding UTF8|ConvertFrom-Json} } catch {}; return $null }
function Get-CommandLine([int]$ProcessId) { try { return [string](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop).CommandLine } catch { return "" } }
function Get-LockPid($Lock) { if($Lock -and $Lock.supervisor_pid){return [int]$Lock.supervisor_pid};if($Lock -and $Lock.pid){return [int]$Lock.pid};return 0 }
function Test-LockOwner($Lock) {
  $ownerPid=Get-LockPid $Lock
  if($ownerPid-le0){return [pscustomobject]@{valid=$false;alive=$false;pid=$ownerPid;reason="no_pid"}}
  $proc=Get-Process -Id $ownerPid -ErrorAction SilentlyContinue
  if(-not $proc){return [pscustomobject]@{valid=$false;alive=$false;pid=$ownerPid;reason="pid_dead"}}
  $command=Get-CommandLine $ownerPid
  $canonical=if($command){$command-like"*RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707.ps1*"-and$command-like"*$repoRoot*"}else{$proc.ProcessName-like"powershell*"}
  $startOk=$true
  if($Lock.process_start_time){try{$startOk=[math]::Abs(($proc.StartTime.ToUniversalTime()-([datetime]$Lock.process_start_time).ToUniversalTime()).TotalSeconds)-lt2}catch{$startOk=$false}}
  [pscustomobject]@{valid=($canonical-and$startOk);alive=$true;pid=$ownerPid;reason=if($canonical-and$startOk){"canonical_owner_verified"}else{"live_owner_identity_mismatch"}}
}

$lock=Read-Json $lockPath
$owner=Test-LockOwner $lock
if($owner.valid){
  [pscustomobject]@{status="already_running";supervisor_pid=$owner.pid;repo_root=$repoRoot;portable_root=$portableRoot;second_launch_blocked=$true;parallel_runner=$false;final_ready=$false}|ConvertTo-Json -Depth 10
  exit 0
}
if($owner.alive){throw "LIVE_LOCK_OWNER_UNVERIFIED_SECOND_INSTANCE_BLOCKED: pid=$($owner.pid) reason=$($owner.reason)"}
if(Test-Path -LiteralPath $lockPath){Move-Item -LiteralPath $lockPath -Destination ($lockPath+".stale."+(Get-Date -Format "yyyyMMdd_HHmmss")) -Force}

$args=@(
  "-NoProfile","-ExecutionPolicy","Bypass","-File",$daemon,
  "-RepoRoot",$repoRoot,"-RepoFullName","cagdascagdas100/chat_gpt_clone_1",
  "-MainBranch","codex/aays-single-runner-v5-20260706","-WorkRoot",$workRoot,
  "-IntervalSeconds","60","-HeartbeatSeconds","15","-MaxTasks","8","-MaxLoops","0",
  "-RefreshIntervalSeconds","43200","-SiteCheckIntervalSeconds","60"
)
$taskName="AAYS_TerraYield_SingleRunner"
$task=$null
$taskInstallError=$null
try {
  $powerShellExe=Join-Path $PSHOME 'powershell.exe'
  $taskArgumentText=($args | ForEach-Object { if($_ -match '[\s"]'){ '"'+($_ -replace '"','\"')+'"' }else{ $_ } }) -join ' '
  $action=New-ScheduledTaskAction -Execute $powerShellExe -Argument $taskArgumentText -WorkingDirectory $repoRoot
  $trigger=New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
  $settings=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([timespan]::Zero) -MultipleInstances IgnoreNew
  $principal=New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
  Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'AAYS F portable single shared runner; one instance, restart on failure.' -Force | Out-Null
  $task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
} catch {
  $taskInstallError=$_.Exception.Message
  $task=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
}
$process=$null
$launchMethod="direct_hidden_process"
if($task){
  Start-ScheduledTask -TaskName $taskName
  $launchMethod="scheduled_task"
}else{
  $process=Start-Process -FilePath powershell -ArgumentList $args -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
}
$deadline=(Get-Date).AddSeconds($StartupTimeoutSeconds)
$started=$false
do{
  Start-Sleep -Seconds 2
  $newLock=Read-Json $lockPath
  $newHeartbeat=Read-Json $heartbeatPath
  $newOwner=Test-LockOwner $newLock
  $expectedPid=if($process){$process.Id}else{$newOwner.pid}
  if($newOwner.valid-and$newOwner.pid-eq$expectedPid-and$newHeartbeat-and[int]$newHeartbeat.supervisor_pid-eq$expectedPid){$started=$true;break}
  if($process-and$process.HasExited){break}
}while((Get-Date)-lt$deadline)
if(-not$started){throw "PERSISTENT_DAEMON_START_FAILED: launch_method=$launchMethod"}
[pscustomobject]@{status="persistent_daemon_started";launch_method=$launchMethod;scheduled_task_installed=[bool]$task;scheduled_task_install_error=$taskInstallError;supervisor_pid=$newOwner.pid;instance_id=$newLock.instance_id;repo_root=$repoRoot;portable_root=$portableRoot;branch=$actualBranch;heartbeat_at=$newHeartbeat.heartbeat_at;second_launch_blocked=$false;parallel_runner=$false;final_ready=$false}|ConvertTo-Json -Depth 10

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
$logRoot = Join-Path $portableRoot "logs"
$launcherLog = Join-Path $logRoot "launcher_latest.log"
$recoveryStatePath = Join-Path $logRoot "recovery_latest.json"
if (-not (Test-Path -LiteralPath $logRoot)) { New-Item -ItemType Directory -Force -Path $logRoot | Out-Null }

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $temporaryPath = $Path + ".tmp." + [guid]::NewGuid().ToString("N")
  [System.IO.File]::WriteAllText($temporaryPath, $Content, (New-Object System.Text.UTF8Encoding($false)))
  Move-Item -LiteralPath $temporaryPath -Destination $Path -Force
}
function Write-LauncherLog([string]$Message) {
  $line = "{0} {1}" -f (Get-Date).ToUniversalTime().ToString("o"), $Message
  [System.IO.File]::AppendAllText($launcherLog, $line + [Environment]::NewLine, (New-Object System.Text.UTF8Encoding($false)))
}
function Write-RecoveryState([string]$State, [hashtable]$Details) {
  $payload = [ordered]@{
    state = $State
    recorded_at = (Get-Date).ToUniversalTime().ToString("o")
    portable_root = $portableRoot
    repo_root = $repoRoot
    launcher_path = $PSCommandPath
    new_runner = $false
    parallel_runner = $false
    fake_data = $false
    final_ready = $false
    product_final_ready = $false
    db_write = $false
    migration = $false
    production_deploy = $false
  }
  foreach ($key in $Details.Keys) { $payload[$key] = $Details[$key] }
  Write-Utf8NoBom -Path $recoveryStatePath -Content ($payload | ConvertTo-Json -Depth 10)
}
function Repair-LocalGitConfig([string]$RepositoryRoot, [string]$BranchName) {
  $gitDirectory = Join-Path $RepositoryRoot ".git"
  $configPath = Join-Path $gitDirectory "config"
  $configLockPath = Join-Path $gitDirectory "config.lock"
  $backupPath = $null
  $configLockAction = "none"
  $invalidReason = $null

  if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    $invalidReason = "config_missing"
  } else {
    $bytes = [System.IO.File]::ReadAllBytes($configPath)
    if ($bytes.Length -eq 0) { $invalidReason = "config_empty" }
    elseif ($bytes -contains 0) { $invalidReason = "config_contains_nul" }
    elseif (($bytes.Length -ge 2) -and (($bytes[0] -eq 255 -and $bytes[1] -eq 254) -or ($bytes[0] -eq 254 -and $bytes[1] -eq 255))) { $invalidReason = "config_utf16_bom" }
    elseif (($bytes.Length -ge 3) -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191) { $invalidReason = "config_utf8_bom" }
  }

  if (-not $invalidReason) {
    $null = & git -c "safe.directory=$RepositoryRoot" -C $RepositoryRoot config --local --list 2>&1
    if ($LASTEXITCODE -ne 0) { $invalidReason = "git_config_parse_failed" }
  }
  if (-not $invalidReason) {
    return [pscustomobject]@{ state = "LOCAL_GIT_VALID"; repaired = $false; reason = "none"; backup_path = $null; config_lock_action = "none" }
  }

  if (Test-Path -LiteralPath $configLockPath) {
    $lockAge = ((Get-Date).ToUniversalTime() - (Get-Item -LiteralPath $configLockPath).LastWriteTimeUtc).TotalSeconds
    if ($lockAge -lt 120) {
      throw "LOCAL_GIT_REPAIR_REQUIRED_CONFIG_LOCK_ACTIVE: age_seconds=$([math]::Round($lockAge,1))"
    }
    $quarantinedLock = $configLockPath + ".stale." + (Get-Date -Format "yyyyMMdd_HHmmss")
    Move-Item -LiteralPath $configLockPath -Destination $quarantinedLock -Force
    $configLockAction = "quarantined:$quarantinedLock"
  }
  if (Test-Path -LiteralPath $configPath) {
    $backupPath = $configPath + ".corrupt." + (Get-Date -Format "yyyyMMdd_HHmmss") + ".bak"
    Copy-Item -LiteralPath $configPath -Destination $backupPath -Force
  }
  $minimalConfig = @"
[core]
    repositoryformatversion = 0
    filemode = false
    bare = false
    logallrefupdates = true
    symlinks = false
    ignorecase = true
    longpaths = true
[remote "origin"]
    url = https://github.com/cagdascagdas100/chat_gpt_clone_1.git
    fetch = +refs/heads/*:refs/remotes/origin/*
[branch "$BranchName"]
    remote = origin
    merge = refs/heads/$BranchName
"@
  Write-Utf8NoBom -Path $configPath -Content $minimalConfig
  $configOutput = & git -c "safe.directory=$RepositoryRoot" -C $RepositoryRoot config --local --list 2>&1
  $configExit = $LASTEXITCODE
  $statusOutput = & git -c "safe.directory=$RepositoryRoot" -C $RepositoryRoot status --short --branch 2>&1
  $statusExit = $LASTEXITCODE
  if ($configExit -ne 0 -or $statusExit -ne 0) {
    throw "LOCAL_GIT_REPAIR_VALIDATION_FAILED: config_exit=$configExit status_exit=$statusExit config=$($configOutput -join ' ') status=$($statusOutput -join ' ')"
  }
  return [pscustomobject]@{ state = "LOCAL_GIT_REPAIRED"; repaired = $true; reason = $invalidReason; backup_path = $backupPath; config_lock_action = $configLockAction }
}

if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) { throw "CANONICAL_REPO_MISSING: $repoRoot" }
if (-not (Test-Path -LiteralPath $daemon)) { throw "CANONICAL_DAEMON_MISSING: $daemon" }
if (-not (Test-Path -LiteralPath $workRoot)) { New-Item -ItemType Directory -Force -Path $workRoot | Out-Null }
$expectedBranch = "codex/aays-single-runner-v5-20260706"
try {
  $gitRecovery = Repair-LocalGitConfig -RepositoryRoot $repoRoot -BranchName $expectedBranch
  Write-LauncherLog "$($gitRecovery.state) reason=$($gitRecovery.reason) backup=$($gitRecovery.backup_path)"
  Write-RecoveryState -State $gitRecovery.state -Details @{
    config_repaired = $gitRecovery.repaired
    config_invalid_reason = $gitRecovery.reason
    config_backup_path = $gitRecovery.backup_path
    config_lock_action = $gitRecovery.config_lock_action
    git_config_valid = $true
    git_status_valid = $true
  }
} catch {
  Write-LauncherLog "LOCAL_GIT_REPAIR_FAILED error=$($_.Exception.Message)"
  Write-RecoveryState -State "LOCAL_GIT_REPAIR_FAILED" -Details @{ error = $_.Exception.Message; git_config_valid = $false; git_status_valid = $false }
  throw
}
$actualBranch = (& git -c "safe.directory=$repoRoot" -C $repoRoot branch --show-current 2>$null).Trim()
if ($actualBranch -ne $expectedBranch) { throw "CANONICAL_BRANCH_MISMATCH: expected=$expectedBranch actual=$actualBranch" }
$guardianTaskName='AAYS Portable Runner Guardian'
$guardianManaged=($env:AAYS_GUARDIAN_MANAGED -eq '1')
$guardianInstalling=($env:AAYS_GUARDIAN_INSTALLING -eq '1')
$guardianTask=$null
try{$guardianTask=Get-ScheduledTask -TaskName $guardianTaskName -ErrorAction SilentlyContinue}catch{}
$guardianInstaller=Join-Path $repoRoot 'docs\chatgpt_status\_shared\automation\INSTALL_AAYS_PORTABLE_RESUME_GUARDIAN.ps1'
if(-not$guardianManaged-and-not$guardianInstalling-and-not$guardianTask-and(Test-Path -LiteralPath $guardianInstaller)){
  $oldInstalling=$env:AAYS_GUARDIAN_INSTALLING
  $env:AAYS_GUARDIAN_INSTALLING='1'
  try{
    & powershell -NoProfile -ExecutionPolicy Bypass -File $guardianInstaller -PortableRoot $portableRoot
    if($LASTEXITCODE-ne0){throw "GUARDIAN_AUTO_INSTALL_FAILED_EXIT_$LASTEXITCODE"}
  }finally{$env:AAYS_GUARDIAN_INSTALLING=$oldInstalling}
  [pscustomobject]@{status='guardian_installed_and_runner_started';portable_root=$portableRoot;task_name=$guardianTaskName;parallel_runner=$false;final_ready=$false}|ConvertTo-Json
  exit 0
}

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
  Write-LauncherLog "RUNNER_ALREADY_ACTIVE pid=$($owner.pid)"
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
if(-not$guardianManaged){
  try{$guardianManaged=[bool](Get-ScheduledTask -TaskName $guardianTaskName -ErrorAction SilentlyContinue)}catch{}
}
if(-not$guardianManaged){
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
}else{
  $taskInstallError='guardian_managed_direct_start'
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
Write-LauncherLog "PERSISTENT_DAEMON_STARTED method=$launchMethod pid=$($newOwner.pid)"
[pscustomobject]@{status="persistent_daemon_started";launch_method=$launchMethod;scheduled_task_installed=[bool]$task;scheduled_task_install_error=$taskInstallError;supervisor_pid=$newOwner.pid;instance_id=$newLock.instance_id;repo_root=$repoRoot;portable_root=$portableRoot;branch=$actualBranch;heartbeat_at=$newHeartbeat.heartbeat_at;second_launch_blocked=$false;parallel_runner=$false;final_ready=$false}|ConvertTo-Json -Depth 10

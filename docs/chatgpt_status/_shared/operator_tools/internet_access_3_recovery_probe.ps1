[CmdletBinding()]
param(
  [string]$RepoRoot = '',
  [string]$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1',
  [string]$CanonicalBranch = 'codex/aays-single-runner-v5-20260706',
  [string]$ProbeBranch = 'operator/internet-access-3-recovery-probe-20260723-6d92b4'
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$slotId = 'internet_access_3'
$taskId = 'aays1-internet-access-3-migrate-existing-then-no-data-20260722'
$attemptId = 'internet-access-3-20260722-001'
$continuationKey = 'd4b44f265a8ba0ff5fdd1f76f07a20f1f41c8023ed1f6bce91061f5ea94d0c0c'
$reportRel = 'docs/chatgpt_status/_shared/operator_reports/internet_access_3/recovery_probe_latest.json'
$manifestRel = 'docs/chatgpt_status/_shared/operator_reports/internet_access_3/recovery_probe_manifest_latest.json'
$runId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Force -Path $Path | Out-Null } }
function Read-Json([string]$Path) { try { if (Test-Path -LiteralPath $Path -PathType Leaf) { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } } catch {}; return $null }
function Prop($Object,[string]$Name) { if ($null -eq $Object) { return $null }; $p=$Object.PSObject.Properties[$Name]; if ($p) { return $p.Value }; return $null }
function Sanitize([string]$Text) {
  if ($null -eq $Text) { return '' }
  $x = $Text -replace '(?i)(ghp_|github_pat_)[A-Za-z0-9_]+','[REDACTED_TOKEN]'
  $x = $x -replace '(?i)(Authorization:\s*Bearer\s+)\S+','$1[REDACTED]'
  $x = $x -replace '(https?://)[^/@\s]+:[^/@\s]+@','$1[REDACTED]@'
  return $x
}
function Invoke-GitBounded([string]$Cwd,[string[]]$Arguments,[int]$TimeoutSeconds=300) {
  $out=[IO.Path]::GetTempFileName(); $err=[IO.Path]::GetTempFileName()
  try {
    $args=@('-c',"safe.directory=$Cwd",'-C',$Cwd)+$Arguments
    $p=Start-Process -FilePath $script:GitExe -ArgumentList $args -WorkingDirectory $Cwd -PassThru -NoNewWindow -RedirectStandardOutput $out -RedirectStandardError $err
    try { Wait-Process -Id $p.Id -Timeout $TimeoutSeconds -ErrorAction Stop } catch { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; throw "GIT_TIMEOUT=$($Arguments -join ' ')" }
    $p.Refresh()
    [pscustomobject]@{ code=[int]$p.ExitCode; stdout=(Get-Content -LiteralPath $out -Raw -ErrorAction SilentlyContinue); stderr=(Get-Content -LiteralPath $err -Raw -ErrorAction SilentlyContinue) }
  } finally { Remove-Item -LiteralPath $out,$err -Force -ErrorAction SilentlyContinue }
}
function Assert-Git($Result,[string]$Code) { if ($Result.code -ne 0) { throw "$Code=$((Sanitize ($Result.stderr + ' ' + $Result.stdout)).Trim())" } }
function Test-Http200([string]$Url) { try { $r=Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10; return [int]$r.StatusCode -eq 200 } catch { return $false } }
function Get-Daemons([string]$Root) {
  @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $c=[string]$_.CommandLine
    $c -and $c -match 'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707\.ps1' -and $c.IndexOf($Root,[StringComparison]::OrdinalIgnoreCase) -ge 0
  })
}
function Get-Heartbeat([string]$Path) {
  $h=Read-Json $Path
  if (-not $h) { return $null }
  try { $at=[DateTimeOffset]::Parse([string](Prop $h 'heartbeat_at')).ToUniversalTime() } catch { return $null }
  [pscustomobject]@{ data=$h; at=$at.ToString('o'); age_seconds=[math]::Round(([DateTimeOffset]::UtcNow-$at).TotalSeconds,1) }
}
function Read-RemoteJson([string]$RelativePath) {
  $r=Invoke-GitBounded $script:RepoRoot @('show',("origin/$CanonicalBranch`:$RelativePath")) 120
  if ($r.code -ne 0) { return $null }
  try { return $r.stdout | ConvertFrom-Json } catch { return $null }
}

if (-not $RepoRoot) {
  $candidates=@()
  foreach ($drive in @(Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
    $candidates += Join-Path $drive.Root 'TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
    $candidates += Join-Path $drive.Root 'TerraYield_AAYS_Portable\runner_system\adaptive_v2\publisher'
  }
  $RepoRoot = @($candidates | Where-Object { Test-Path -LiteralPath (Join-Path $_ '.git') -and Test-Path -LiteralPath (Join-Path $_ 'docs\chatgpt_status\_shared') } | Select-Object -First 1)
}
if (-not $RepoRoot) { throw 'CANONICAL_REPO_NOT_FOUND' }
$script:RepoRoot=[IO.Path]::GetFullPath([string]$RepoRoot).TrimEnd('\')

$gitCmd=Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $gitCmd) { $gitCmd=Get-Command git -ErrorAction SilentlyContinue }
if (-not $gitCmd) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$script:GitExe=$gitCmd.Source

$remote=Invoke-GitBounded $script:RepoRoot @('remote','get-url','origin') 60
Assert-Git $remote 'REMOTE_READ_FAILED'
if ($remote.stdout -notmatch 'cagdascagdas100/chat_gpt_clone_1') { throw 'REMOTE_REPOSITORY_MISMATCH' }

$fetchArgs=@('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','origin',("+refs/heads/$CanonicalBranch`:refs/remotes/origin/$CanonicalBranch"))
$fetch=Invoke-GitBounded $script:RepoRoot $fetchArgs 300
Assert-Git $fetch 'CANONICAL_FETCH_FAILED'
$head=Invoke-GitBounded $script:RepoRoot @('rev-parse',"origin/$CanonicalBranch") 60
Assert-Git $head 'CANONICAL_HEAD_READ_FAILED'
$canonicalHead=$head.stdout.Trim()

$status=Invoke-GitBounded $script:RepoRoot @('status','--porcelain=v1','-uall') 120
Assert-Git $status 'LOCAL_STATUS_FAILED'
$dirtyPaths=@($status.stdout -split "`r?`n" | Where-Object { $_ } | ForEach-Object { if ($_.Length -gt 3) { $_.Substring(3).Trim() } } | Select-Object -First 200)

$lockPath=Join-Path $script:RepoRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
$heartbeatPath=Join-Path $script:RepoRoot 'docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json'
$launcher=Join-Path $script:RepoRoot 'docs\chatgpt_status\_shared\automation\START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1'
$workRoot=Join-Path (Split-Path -Parent $script:RepoRoot) 'AAYS_STABLE_RUNNER_WORKTREES'
Ensure-Dir $workRoot

$beforeDaemons=@(Get-Daemons $script:RepoRoot)
$beforeHeartbeat=Get-Heartbeat $heartbeatPath
$lock=Read-Json $lockPath
$lockPid=0
if ($lock) { if (Prop $lock 'supervisor_pid') { $lockPid=[int](Prop $lock 'supervisor_pid') } elseif (Prop $lock 'pid') { $lockPid=[int](Prop $lock 'pid') } }
$lockProcess=if($lockPid -gt 0){Get-Process -Id $lockPid -ErrorAction SilentlyContinue}else{$null}
$lockIdentityValid=$false
if ($lock -and $lockProcess) {
  $startOk=$true
  if (Prop $lock 'process_start_time') { try { $startOk=[math]::Abs(($lockProcess.StartTime.ToUniversalTime()-([datetime](Prop $lock 'process_start_time')).ToUniversalTime()).TotalSeconds)-lt2 } catch { $startOk=$false } }
  $scopeOk=([string](Prop $lock 'lock_scope') -eq 'single_shared_runner_daemon')
  $lockIdentityValid=($startOk -and $scopeOk)
}

$launcherAttempted=$false; $launcherExit=$null; $launcherTail=''; $action='none'
if ($beforeDaemons.Count -gt 1) {
  $action='blocked_multiple_canonical_daemons'
} elseif ($beforeDaemons.Count -eq 1) {
  $action='existing_canonical_daemon_preserved'
} elseif ($lockProcess -and -not $lockIdentityValid) {
  $action='blocked_live_lock_owner_unverified'
} else {
  if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { throw 'SHARED_LAUNCHER_MISSING' }
  $launcherAttempted=$true
  $out=[IO.Path]::GetTempFileName(); $err=[IO.Path]::GetTempFileName()
  try {
    $args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$launcher,'-RepoRoot',$script:RepoRoot,'-RepoFullName',$RepoFullName,'-MainBranch',$CanonicalBranch,'-WorkRoot',$workRoot,'-MaxTasks','1','-StaleMinutes','20','-NoPanel')
    $p=Start-Process -FilePath 'powershell.exe' -ArgumentList $args -WorkingDirectory $script:RepoRoot -PassThru -NoNewWindow -RedirectStandardOutput $out -RedirectStandardError $err
    try { Wait-Process -Id $p.Id -Timeout 180 -ErrorAction Stop } catch { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; $launcherExit=124 }
    $p.Refresh(); if ($null -eq $launcherExit) { $launcherExit=[int]$p.ExitCode }
    $text=((Get-Content -LiteralPath $out -ErrorAction SilentlyContinue)+(Get-Content -LiteralPath $err -ErrorAction SilentlyContinue))
    $launcherTail=(Sanitize (($text | Select-Object -Last 80) -join "`n"))
  } finally { Remove-Item -LiteralPath $out,$err -Force -ErrorAction SilentlyContinue }
  $action=if($launcherExit -eq 0){'shared_launcher_invoked'}else{'shared_launcher_failed'}
}

$runnerFresh=$false; $freshHeartbeat=$null
$deadline=(Get-Date).AddSeconds(180)
do {
  $ds=@(Get-Daemons $script:RepoRoot); $hb=Get-Heartbeat $heartbeatPath
  if ($ds.Count -eq 1 -and $hb -and $hb.age_seconds -ge 0 -and $hb.age_seconds -le 90 -and [bool](Prop $hb.data 'single_runner_only') -and -not [bool](Prop $hb.data 'parallel_runner')) { $runnerFresh=$true; $freshHeartbeat=$hb; break }
  Start-Sleep -Seconds 3
} while ((Get-Date) -lt $deadline)

$refreshSignalCreated=$false
if ($runnerFresh) {
  $controlDir=Join-Path $script:RepoRoot 'docs\chatgpt_status\_shared\control'; Ensure-Dir $controlDir
  $signal=Join-Path $controlDir 'request_queue_refresh.json'; $temp="$signal.tmp.$PID"
  [ordered]@{schema_version=1;requested_at=Now-Utc;requested_by='internet_access_3_recovery_probe';slot_id=$slotId;continuation_key=$continuationKey;force_push=$false;reset_hard=$false;data_delete=$false}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $temp -Encoding UTF8
  Move-Item -LiteralPath $temp -Destination $signal -Force
  $refreshSignalCreated=$true
  Start-Sleep -Seconds 45
}

$fetch2=Invoke-GitBounded $script:RepoRoot $fetchArgs 300
$fetchAfterOk=($fetch2.code -eq 0)
$afterDaemons=@(Get-Daemons $script:RepoRoot)
$afterHeartbeat=Get-Heartbeat $heartbeatPath
$remoteManual=Read-RemoteJson 'docs/chatgpt_status/_shared/manual_actions/internet_access_3.json'
$remoteSlotStatus=Read-RemoteJson 'docs/chatgpt_status/_shared/slots_21/internet_access_3/status_latest.json'
$remoteCurrent=Read-RemoteJson 'docs/chatgpt_status/_shared/slots_21/internet_access_3/current_task_latest.json'

$healthOk=Test-Http200 'http://127.0.0.1:8012/health'
$openApiOk=Test-Http200 'http://127.0.0.1:8012/openapi.json'
$readyPageOk=Test-Http200 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html'
$currentTaskId=if($afterHeartbeat){[string](Prop $afterHeartbeat.data 'current_task_id')}else{''}
$lastPickupTaskId=if($afterHeartbeat){[string](Prop $afterHeartbeat.data 'last_pickup_task_id')}else{''}
$manualState=[string](Prop $remoteManual 'state')
$pickupObserved=[bool](Prop $remoteCurrent 'runner_pickup_observed')

$result=if($beforeDaemons.Count -gt 1){'BLOCKED_MULTIPLE_CANONICAL_DAEMONS'}elseif($action -eq 'blocked_live_lock_owner_unverified'){'BLOCKED_LIVE_LOCK_OWNER_UNVERIFIED'}elseif(-not $runnerFresh){'RUNNER_RECOVERY_FAILED_NO_FRESH_HEARTBEAT'}elseif($manualState -eq 'RESOLVED'){'RECOVERY_CONFIRMED_MANUAL_ACTION_RESOLVED'}elseif($pickupObserved -or $currentTaskId -eq $taskId -or $lastPickupTaskId -eq $taskId){'RUNNER_HEALTHY_INTERNET_ACCESS_3_ACTIVE'}else{'RUNNER_HEALTHY_SEQUENTIAL_QUEUE_PENDING'}

$report=[ordered]@{
  schema_version=1;probe_id='internet-access-3-20260723-6d92b4';captured_at=Now-Utc;result=$result
  slot_id=$slotId;task_id=$taskId;attempt_id=$attemptId;continuation_key=$continuationKey
  repo_root=$script:RepoRoot;repo_full_name=$RepoFullName;canonical_branch=$CanonicalBranch;canonical_head=$canonicalHead;probe_branch=$ProbeBranch
  local_dirty_path_count=$dirtyPaths.Count;local_dirty_paths=$dirtyPaths
  daemon_count_before=$beforeDaemons.Count;daemon_pids_before=@($beforeDaemons|ForEach-Object{$_.ProcessId});daemon_count_after=$afterDaemons.Count;daemon_pids_after=@($afterDaemons|ForEach-Object{$_.ProcessId})
  lock_present=(Test-Path -LiteralPath $lockPath);lock_pid=$lockPid;lock_process_alive=($null-ne$lockProcess);lock_identity_valid=$lockIdentityValid
  heartbeat_before_at=if($beforeHeartbeat){$beforeHeartbeat.at}else{$null};heartbeat_before_age_seconds=if($beforeHeartbeat){$beforeHeartbeat.age_seconds}else{$null}
  heartbeat_after_at=if($afterHeartbeat){$afterHeartbeat.at}else{$null};heartbeat_after_age_seconds=if($afterHeartbeat){$afterHeartbeat.age_seconds}else{$null};heartbeat_state=if($afterHeartbeat){[string](Prop $afterHeartbeat.data 'state')}else{$null}
  current_task_id=$currentTaskId;last_pickup_task_id=$lastPickupTaskId;runner_fresh=$runnerFresh;single_runner_only=if($afterHeartbeat){[bool](Prop $afterHeartbeat.data 'single_runner_only')}else{$false};parallel_runner=if($afterHeartbeat){[bool](Prop $afterHeartbeat.data 'parallel_runner')}else{$false}
  action=$action;launcher_attempted=$launcherAttempted;launcher_exit_code=$launcherExit;launcher_output_tail=$launcherTail;refresh_signal_created=$refreshSignalCreated
  health_http_200=$healthOk;openapi_http_200=$openApiOk;ready_page_http_200=$readyPageOk;fetch_after_recovery_ok=$fetchAfterOk
  remote_manual_action_state=$manualState;remote_manual_requires_user_action=[bool](Prop $remoteManual 'requires_user_action');remote_slot_state=[string](Prop $remoteSlotStatus 'state');remote_pickup_observed=$pickupObserved;remote_first_unverified_step=[string](Prop $remoteCurrent 'first_unverified_step')
  force_push_used=$false;reset_hard_used=$false;git_clean_used=$false;user_data_deleted=$false;new_task_created=$false;second_runner_requested=$false;report_part_limit_bytes=50331648;final_ready=$false
}

$tempRoot=Join-Path ([IO.Path]::GetTempPath()) "aays_probe_$runId"; Ensure-Dir $tempRoot
$tempReport=Join-Path $tempRoot 'recovery_probe_latest.json'
$tempManifest=Join-Path $tempRoot 'recovery_probe_manifest_latest.json'
[IO.File]::WriteAllText($tempReport,(($report|ConvertTo-Json -Depth 30)+"`n"),[Text.UTF8Encoding]::new($false))
$reportItem=Get-Item -LiteralPath $tempReport
if($reportItem.Length -ge 48MB){throw 'REPORT_EXCEEDS_48_MIB'}
$reportSha=(Get-FileHash -LiteralPath $tempReport -Algorithm SHA256).Hash.ToLowerInvariant()
$manifest=[ordered]@{schema_version=1;generated_at=Now-Utc;probe_id='internet-access-3-20260723-6d92b4';part_limit='less_than_48_MiB';files=@([ordered]@{path=$reportRel;size_bytes=$reportItem.Length;sha256=$reportSha;below_48_mib=$true});force_push_used=$false;user_data_deleted=$false}
[IO.File]::WriteAllText($tempManifest,(($manifest|ConvertTo-Json -Depth 12)+"`n"),[Text.UTF8Encoding]::new($false))

$fetchProbe=Invoke-GitBounded $script:RepoRoot @('fetch','--no-tags','origin',("+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch")) 300
if($fetchProbe.code -ne 0){throw "PROBE_BRANCH_FETCH_FAILED=$((Sanitize $fetchProbe.stderr).Trim())"}
$publishRoot=Join-Path (Split-Path -Parent $script:RepoRoot) "AAYS_OPERATOR_PROBE_WORKTREE_$runId"
$add=Invoke-GitBounded $script:RepoRoot @('worktree','add','--detach',$publishRoot,"origin/$ProbeBranch") 300
Assert-Git $add 'PROBE_WORKTREE_ADD_FAILED'
Invoke-GitBounded $publishRoot @('config','user.name','AAYS Operator Probe') 60 | Out-Null
Invoke-GitBounded $publishRoot @('config','user.email','aays-operator@users.noreply.github.com') 60 | Out-Null
$reportPath=Join-Path $publishRoot ($reportRel -replace '/','\'); $manifestPath=Join-Path $publishRoot ($manifestRel -replace '/','\')
Ensure-Dir (Split-Path -Parent $reportPath)
Copy-Item -LiteralPath $tempReport -Destination $reportPath -Force
Copy-Item -LiteralPath $tempManifest -Destination $manifestPath -Force
$addFiles=Invoke-GitBounded $publishRoot @('add','--',$reportRel,$manifestRel) 120; Assert-Git $addFiles 'REPORT_STAGE_FAILED'
$commit=Invoke-GitBounded $publishRoot @('commit','-m',("AAYS internet_access_3 recovery probe $runId")) 120
if($commit.code -ne 0 -and ($commit.stdout+$commit.stderr) -notmatch 'nothing to commit'){throw "REPORT_COMMIT_FAILED=$((Sanitize ($commit.stderr+$commit.stdout)).Trim())"}

$pushOk=$false
for($i=1;$i-le5;$i++){
  $push=Invoke-GitBounded $publishRoot @('push','origin',("HEAD:refs/heads/$ProbeBranch")) 300
  if($push.code -eq0){$pushOk=$true;break}
  $fr=Invoke-GitBounded $publishRoot @('fetch','--no-tags','origin',("+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch")) 300
  if($fr.code -ne0){continue}
  $merge=Invoke-GitBounded $publishRoot @('merge','--no-edit',"origin/$ProbeBranch") 180
  if($merge.code -ne0){Invoke-GitBounded $publishRoot @('merge','--abort') 60|Out-Null;break}
}
if(-not$pushOk){throw "REPORT_PUSH_FAILED_LOCAL_COPY=$tempReport"}

$readbackFetch=Invoke-GitBounded $script:RepoRoot @('fetch','--no-tags','origin',("+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch")) 300
Assert-Git $readbackFetch 'REPORT_READBACK_FETCH_FAILED'
$localBlob=Invoke-GitBounded $publishRoot @('hash-object','--',$reportPath) 60; Assert-Git $localBlob 'LOCAL_REPORT_BLOB_FAILED'
$remoteBlob=Invoke-GitBounded $script:RepoRoot @('rev-parse',("origin/$ProbeBranch`:$reportRel")) 60; Assert-Git $remoteBlob 'REMOTE_REPORT_BLOB_FAILED'
if($localBlob.stdout.Trim() -ne $remoteBlob.stdout.Trim()){throw 'REPORT_REMOTE_READBACK_MISMATCH'}

Write-Output "AAYS_PROBE_PUBLISHED=true"
Write-Output "PROBE_BRANCH=$ProbeBranch"
Write-Output "REPORT_PATH=$reportRel"
Write-Output "RESULT=$result"
Write-Output "FORCE_PUSH_USED=false"
Write-Output "RESET_HARD_USED=false"
Write-Output "USER_DATA_DELETED=false"

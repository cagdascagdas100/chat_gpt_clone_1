[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RepoRoot,
    [Parameter(Mandatory=$true)][string]$GitExe,
    [string]$CanonicalBranch = 'codex/aays-single-runner-v5-20260706',
    [string]$ProbeBranch = 'operator/internet-access-3-recovery-probe-20260723-6d92b4'
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$RepoRoot = [IO.Path]::GetFullPath($RepoRoot).TrimEnd('\')
$SlotId = 'internet_access_3'
$TaskId = 'aays1-internet-access-3-migrate-existing-then-no-data-20260722'
$AttemptId = 'internet-access-3-20260722-001'
$ContinuationKey = 'd4b44f265a8ba0ff5fdd1f76f07a20f1f41c8023ed1f6bce91061f5ea94d0c0c'
$ReportRel = 'docs/chatgpt_status/_shared/operator_reports/internet_access_3/recovery_probe_latest.json'
$ManifestRel = 'docs/chatgpt_status/_shared/operator_reports/internet_access_3/recovery_probe_manifest_latest.json'
$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Dir([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null } }
function Read-JsonSafe([string]$Path) { try { if (Test-Path -LiteralPath $Path -PathType Leaf) { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } } catch {}; return $null }
function Prop($Object,[string]$Name) { if ($null -eq $Object) { return $null }; $P=$Object.PSObject.Properties[$Name]; if ($P) { return $P.Value }; return $null }
function Sanitize([string]$Text) {
    if ($null -eq $Text) { return '' }
    $X=$Text -replace '(?i)(ghp_|github_pat_)[A-Za-z0-9_]+','[REDACTED_TOKEN]'
    $X=$X -replace '(?i)(Authorization:\s*Bearer\s+)\S+','$1[REDACTED]'
    $X=$X -replace '(https?://)[^/@\s]+:[^/@\s]+@','$1[REDACTED]@'
    return $X
}
function Invoke-GitBounded([string]$Cwd,[string[]]$Args,[int]$TimeoutSeconds=300) {
    $Out=[IO.Path]::GetTempFileName(); $Err=[IO.Path]::GetTempFileName()
    try {
        $Full=@('-c',"safe.directory=$Cwd",'-C',$Cwd)+$Args
        $P=Start-Process -FilePath $GitExe -ArgumentList $Full -WorkingDirectory $Cwd -PassThru -NoNewWindow -RedirectStandardOutput $Out -RedirectStandardError $Err
        $Finished=$P.WaitForExit($TimeoutSeconds*1000)
        if (-not $Finished) { Stop-Process -Id $P.Id -Force -ErrorAction SilentlyContinue; return [pscustomobject]@{Code=124;StdOut='';StdErr="GIT_TIMEOUT=$($Args -join ' ')"} }
        $P.Refresh()
        return [pscustomobject]@{Code=[int]$P.ExitCode;StdOut=[string](Get-Content -LiteralPath $Out -Raw -ErrorAction SilentlyContinue);StdErr=[string](Get-Content -LiteralPath $Err -Raw -ErrorAction SilentlyContinue)}
    } finally { Remove-Item -LiteralPath $Out,$Err -Force -ErrorAction SilentlyContinue }
}
function Assert-Git($R,[string]$Code) { if ($R.Code -ne 0) { throw "$Code=$(Sanitize (($R.StdErr+' '+$R.StdOut).Trim()))" } }
function Get-Daemons {
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $C=[string]$_.CommandLine
        $C -and $C -match 'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707\.ps1' -and $C.IndexOf($RepoRoot,[StringComparison]::OrdinalIgnoreCase) -ge 0
    })
}
function Get-Heartbeat([string]$Path) {
    $H=Read-JsonSafe $Path; if ($null -eq $H) { return $null }
    try { $At=[DateTimeOffset]::Parse([string](Prop $H 'heartbeat_at')).ToUniversalTime() } catch { return $null }
    return [pscustomobject]@{Data=$H;At=$At.ToString('o');AgeSeconds=[math]::Round(([DateTimeOffset]::UtcNow-$At).TotalSeconds,1)}
}
function Test-Http200([string]$Url) { try { $R=Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10; return ([int]$R.StatusCode -eq 200) } catch { return $false } }
function Read-RemoteJson([string]$Path) {
    $R=Invoke-GitBounded $RepoRoot @('show',("origin/$CanonicalBranch`:$Path")) 120
    if ($R.Code -ne 0) { return $null }
    try { return $R.StdOut | ConvertFrom-Json } catch { return $null }
}

$CapturedError=$null
$Action='none'
$LauncherExitCode=$null
$LauncherOutputTail=''
$RunnerFresh=$false
$RefreshSignalCreated=$false
$CanonicalHead=''
$DirtyPaths=@()
$BeforeDaemons=@()
$AfterDaemons=@()
$BeforeHeartbeat=$null
$AfterHeartbeat=$null
$LockPid=0
$LockAlive=$false
$LockIdentityValid=$false
$HealthOk=$false
$OpenApiOk=$false
$ReadyPageOk=$false
$RemoteManual=$null
$RemoteStatus=$null
$RemoteCurrent=$null

try {
    if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw 'REPO_ROOT_MISSING' }
    if (-not (Test-Path -LiteralPath $GitExe -PathType Leaf)) { throw 'GIT_EXECUTABLE_MISSING' }
    $Remote=Invoke-GitBounded $RepoRoot @('remote','get-url','origin') 60; Assert-Git $Remote 'REMOTE_READ_FAILED'
    if ($Remote.StdOut -notmatch 'cagdascagdas100/chat_gpt_clone_1') { throw 'REMOTE_REPOSITORY_MISMATCH' }

    $FetchArgs=@('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','origin',("+refs/heads/$CanonicalBranch`:refs/remotes/origin/$CanonicalBranch"))
    $Fetch=Invoke-GitBounded $RepoRoot $FetchArgs 300; Assert-Git $Fetch 'CANONICAL_FETCH_FAILED'
    $Head=Invoke-GitBounded $RepoRoot @('rev-parse',"origin/$CanonicalBranch") 60; Assert-Git $Head 'CANONICAL_HEAD_READ_FAILED'; $CanonicalHead=$Head.StdOut.Trim()
    $Status=Invoke-GitBounded $RepoRoot @('status','--porcelain=v1','-uall') 120; Assert-Git $Status 'LOCAL_STATUS_FAILED'
    foreach ($Line in @($Status.StdOut -split "`r?`n" | Where-Object { $_ })) { if ($Line.Length -gt 3) { $DirtyPaths += $Line.Substring(3).Trim() }; if ($DirtyPaths.Count -ge 200) { break } }

    $LockPath=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
    $HeartbeatPath=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json'
    $Launcher=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\automation\START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1'
    $WorkRoot=Join-Path (Split-Path -Parent $RepoRoot) 'AAYS_STABLE_RUNNER_WORKTREES'; Ensure-Dir $WorkRoot

    $BeforeDaemons=@(Get-Daemons); $BeforeHeartbeat=Get-Heartbeat $HeartbeatPath
    $Lock=Read-JsonSafe $LockPath
    if ($Lock) { $V=Prop $Lock 'supervisor_pid'; if ($null -eq $V) { $V=Prop $Lock 'pid' }; if ($null -ne $V) { $LockPid=[int]$V } }
    $LockProcess=$null; if ($LockPid -gt 0) { $LockProcess=Get-Process -Id $LockPid -ErrorAction SilentlyContinue }
    $LockAlive=($null -ne $LockProcess)
    if ($Lock -and $LockProcess) {
        $StartOk=$true; $Expected=Prop $Lock 'process_start_time'
        if ($Expected) { try { $StartOk=[math]::Abs(($LockProcess.StartTime.ToUniversalTime()-([datetime]$Expected).ToUniversalTime()).TotalSeconds)-lt 2 } catch { $StartOk=$false } }
        $ScopeOk=([string](Prop $Lock 'lock_scope') -eq 'single_shared_runner_daemon')
        $LockIdentityValid=($StartOk -and $ScopeOk)
    }

    if ($BeforeDaemons.Count -gt 1) { $Action='blocked_multiple_canonical_daemons' }
    elseif ($BeforeDaemons.Count -eq 1) { $Action='existing_canonical_daemon_preserved' }
    elseif ($LockAlive -and -not $LockIdentityValid) { $Action='blocked_live_lock_owner_unverified' }
    else {
        if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) { throw 'SHARED_LAUNCHER_MISSING' }
        $Out=[IO.Path]::GetTempFileName(); $Err=[IO.Path]::GetTempFileName()
        try {
            $Args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$Launcher,'-RepoRoot',$RepoRoot,'-RepoFullName','cagdascagdas100/chat_gpt_clone_1','-MainBranch',$CanonicalBranch,'-WorkRoot',$WorkRoot,'-MaxTasks','1','-StaleMinutes','20','-NoPanel')
            $P=Start-Process -FilePath 'powershell.exe' -ArgumentList $Args -WorkingDirectory $RepoRoot -PassThru -NoNewWindow -RedirectStandardOutput $Out -RedirectStandardError $Err
            $Done=$P.WaitForExit(180000)
            if (-not $Done) { Stop-Process -Id $P.Id -Force -ErrorAction SilentlyContinue; $LauncherExitCode=124 } else { $P.Refresh(); $LauncherExitCode=[int]$P.ExitCode }
            $Lines=@(); $Lines+=Get-Content -LiteralPath $Out -ErrorAction SilentlyContinue; $Lines+=Get-Content -LiteralPath $Err -ErrorAction SilentlyContinue
            $LauncherOutputTail=Sanitize (($Lines|Select-Object -Last 80)-join "`n")
        } finally { Remove-Item -LiteralPath $Out,$Err -Force -ErrorAction SilentlyContinue }
        if ($LauncherExitCode -eq 0) { $Action='shared_launcher_invoked' } else { $Action='shared_launcher_failed' }
    }

    $Deadline=(Get-Date).AddSeconds(180)
    do {
        $D=@(Get-Daemons); $H=Get-Heartbeat $HeartbeatPath
        if (($D.Count -eq 1) -and $H) {
            $Single=[bool](Prop $H.Data 'single_runner_only'); $Parallel=[bool](Prop $H.Data 'parallel_runner')
            if (($H.AgeSeconds -ge 0) -and ($H.AgeSeconds -le 90) -and $Single -and (-not $Parallel)) { $RunnerFresh=$true; break }
        }
        Start-Sleep -Seconds 3
    } while ((Get-Date) -lt $Deadline)

    if ($RunnerFresh) {
        $Control=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\control'; Ensure-Dir $Control
        $Signal=Join-Path $Control 'request_queue_refresh.json'; $Temp="$Signal.tmp.$PID"
        $Payload=[ordered]@{schema_version=1;requested_at=Now-Utc;requested_by='internet_access_3_recovery_probe_v4';slot_id=$SlotId;continuation_key=$ContinuationKey;force_push=$false;reset_hard=$false;data_delete=$false}
        [IO.File]::WriteAllText($Temp,(($Payload|ConvertTo-Json -Depth 8)+"`n"),$Utf8NoBom); Move-Item -LiteralPath $Temp -Destination $Signal -Force
        $RefreshSignalCreated=$true; Start-Sleep -Seconds 45
    }

    $Fetch2=Invoke-GitBounded $RepoRoot $FetchArgs 300
    $AfterDaemons=@(Get-Daemons); $AfterHeartbeat=Get-Heartbeat $HeartbeatPath
    $RemoteManual=Read-RemoteJson 'docs/chatgpt_status/_shared/manual_actions/internet_access_3.json'
    $RemoteStatus=Read-RemoteJson 'docs/chatgpt_status/_shared/slots_21/internet_access_3/status_latest.json'
    $RemoteCurrent=Read-RemoteJson 'docs/chatgpt_status/_shared/slots_21/internet_access_3/current_task_latest.json'
    $HealthOk=Test-Http200 'http://127.0.0.1:8012/health'
    $OpenApiOk=Test-Http200 'http://127.0.0.1:8012/openapi.json'
    $ReadyPageOk=Test-Http200 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html'
} catch { $CapturedError=Sanitize $_.Exception.Message }

$CurrentTaskId=''; $LastPickupTaskId=''
if ($AfterHeartbeat) { $CurrentTaskId=[string](Prop $AfterHeartbeat.Data 'current_task_id'); $LastPickupTaskId=[string](Prop $AfterHeartbeat.Data 'last_pickup_task_id') }
$ManualState=[string](Prop $RemoteManual 'state'); $PickupObserved=[bool](Prop $RemoteCurrent 'runner_pickup_observed')
$Result='RUNNER_HEALTHY_SEQUENTIAL_QUEUE_PENDING'
if ($CapturedError) { $Result='PROBE_ERROR_REPORTED' }
elseif ($BeforeDaemons.Count -gt 1) { $Result='BLOCKED_MULTIPLE_CANONICAL_DAEMONS' }
elseif ($Action -eq 'blocked_live_lock_owner_unverified') { $Result='BLOCKED_LIVE_LOCK_OWNER_UNVERIFIED' }
elseif (-not $RunnerFresh) { $Result='RUNNER_RECOVERY_FAILED_NO_FRESH_HEARTBEAT' }
elseif ($ManualState -eq 'RESOLVED') { $Result='RECOVERY_CONFIRMED_MANUAL_ACTION_RESOLVED' }
elseif ($PickupObserved -or ($CurrentTaskId -eq $TaskId) -or ($LastPickupTaskId -eq $TaskId)) { $Result='RUNNER_HEALTHY_INTERNET_ACCESS_3_ACTIVE' }

$Report=[ordered]@{
    schema_version=4;probe_id='internet-access-3-v4';captured_at=Now-Utc;result=$Result;captured_error=$CapturedError;slot_id=$SlotId;task_id=$TaskId;attempt_id=$AttemptId;continuation_key=$ContinuationKey;repo_root=$RepoRoot;git_executable=$GitExe;canonical_branch=$CanonicalBranch;canonical_head=$CanonicalHead;probe_branch=$ProbeBranch;local_dirty_path_count=$DirtyPaths.Count;local_dirty_paths=$DirtyPaths;daemon_count_before=$BeforeDaemons.Count;daemon_pids_before=@($BeforeDaemons|ForEach-Object{$_.ProcessId});daemon_count_after=$AfterDaemons.Count;daemon_pids_after=@($AfterDaemons|ForEach-Object{$_.ProcessId});lock_pid=$LockPid;lock_process_alive=$LockAlive;lock_identity_valid=$LockIdentityValid;heartbeat_before_at=$(if($BeforeHeartbeat){$BeforeHeartbeat.At}else{$null});heartbeat_before_age_seconds=$(if($BeforeHeartbeat){$BeforeHeartbeat.AgeSeconds}else{$null});heartbeat_after_at=$(if($AfterHeartbeat){$AfterHeartbeat.At}else{$null});heartbeat_after_age_seconds=$(if($AfterHeartbeat){$AfterHeartbeat.AgeSeconds}else{$null});heartbeat_state=$(if($AfterHeartbeat){[string](Prop $AfterHeartbeat.Data 'state')}else{$null});current_task_id=$CurrentTaskId;last_pickup_task_id=$LastPickupTaskId;runner_fresh=$RunnerFresh;single_runner_only=$(if($AfterHeartbeat){[bool](Prop $AfterHeartbeat.Data 'single_runner_only')}else{$false});parallel_runner=$(if($AfterHeartbeat){[bool](Prop $AfterHeartbeat.Data 'parallel_runner')}else{$false});action=$Action;launcher_exit_code=$LauncherExitCode;launcher_output_tail=$LauncherOutputTail;refresh_signal_created=$RefreshSignalCreated;health_http_200=$HealthOk;openapi_http_200=$OpenApiOk;ready_page_http_200=$ReadyPageOk;remote_manual_action_state=$ManualState;remote_manual_requires_user_action=[bool](Prop $RemoteManual 'requires_user_action');remote_slot_state=[string](Prop $RemoteStatus 'state');remote_pickup_observed=$PickupObserved;remote_first_unverified_step=[string](Prop $RemoteCurrent 'first_unverified_step');force_push_used=$false;reset_hard_used=$false;git_clean_used=$false;user_data_deleted=$false;new_task_created=$false;second_runner_requested=$false;final_ready=$false
}

$TempRoot=Join-Path $env:TEMP "aays_probe_v4_$RunId"; Ensure-Dir $TempRoot
$TempReport=Join-Path $TempRoot 'recovery_probe_latest.json'; $TempManifest=Join-Path $TempRoot 'recovery_probe_manifest_latest.json'
[IO.File]::WriteAllText($TempReport,(($Report|ConvertTo-Json -Depth 30)+"`n"),$Utf8NoBom)
$Item=Get-Item -LiteralPath $TempReport; if ($Item.Length -ge 48MB) { throw 'REPORT_EXCEEDS_48_MIB' }
$Sha=(Get-FileHash -LiteralPath $TempReport -Algorithm SHA256).Hash.ToLowerInvariant()
$Manifest=[ordered]@{schema_version=1;generated_at=Now-Utc;probe_id='internet-access-3-v4';part_limit='less_than_48_MiB';files=@([ordered]@{path=$ReportRel;size_bytes=$Item.Length;sha256=$Sha;below_48_mib=$true});force_push_used=$false;user_data_deleted=$false}
[IO.File]::WriteAllText($TempManifest,(($Manifest|ConvertTo-Json -Depth 12)+"`n"),$Utf8NoBom)

$ProbeFetch=Invoke-GitBounded $RepoRoot @('fetch','--no-tags','origin',("+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch")) 300; Assert-Git $ProbeFetch 'PROBE_BRANCH_FETCH_FAILED'
$PublishRoot=Join-Path (Split-Path -Parent $RepoRoot) "AAYS_OPERATOR_PROBE_V4_$RunId"
$Add=Invoke-GitBounded $RepoRoot @('worktree','add','--detach',$PublishRoot,"origin/$ProbeBranch") 300; Assert-Git $Add 'PROBE_WORKTREE_ADD_FAILED'
$null=Invoke-GitBounded $PublishRoot @('config','user.name','AAYS Operator Probe') 60; $null=Invoke-GitBounded $PublishRoot @('config','user.email','aays-operator@users.noreply.github.com') 60
$ReportPath=Join-Path $PublishRoot ($ReportRel -replace '/','\'); $ManifestPath=Join-Path $PublishRoot ($ManifestRel -replace '/','\'); Ensure-Dir (Split-Path -Parent $ReportPath)
Copy-Item -LiteralPath $TempReport -Destination $ReportPath -Force; Copy-Item -LiteralPath $TempManifest -Destination $ManifestPath -Force
Assert-Git (Invoke-GitBounded $PublishRoot @('add','--',$ReportRel,$ManifestRel) 120) 'REPORT_STAGE_FAILED'
$Commit=Invoke-GitBounded $PublishRoot @('commit','-m',"AAYS internet_access_3 recovery probe v4 $RunId") 120; if (($Commit.Code -ne 0) -and (($Commit.StdOut+$Commit.StdErr) -notmatch 'nothing to commit')) { throw "REPORT_COMMIT_FAILED=$(Sanitize (($Commit.StdErr+$Commit.StdOut).Trim()))" }
$Pushed=$false
for($I=1;$I -le 5;$I++) {
    $Push=Invoke-GitBounded $PublishRoot @('push','origin',"HEAD:refs/heads/$ProbeBranch") 300
    if($Push.Code -eq 0){$Pushed=$true;break}
    $Refresh=Invoke-GitBounded $PublishRoot @('fetch','--no-tags','origin',("+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch")) 300
    if($Refresh.Code -ne 0){continue}
    $Merge=Invoke-GitBounded $PublishRoot @('merge','--no-edit',"origin/$ProbeBranch") 180
    if($Merge.Code -ne 0){$null=Invoke-GitBounded $PublishRoot @('merge','--abort') 60;break}
}
if(-not $Pushed){throw 'REPORT_PUSH_FAILED'}
$Readback=Invoke-GitBounded $RepoRoot @('fetch','--no-tags','origin',("+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch")) 300; Assert-Git $Readback 'READBACK_FETCH_FAILED'
$RemoteBlob=Invoke-GitBounded $RepoRoot @('rev-parse',"origin/$ProbeBranch`:$ReportRel") 60; Assert-Git $RemoteBlob 'REMOTE_REPORT_BLOB_FAILED'
Write-Output 'AAYS_PROBE_V4_PUBLISHED=true'
Write-Output "AAYS_PROBE_RESULT=$Result"
Write-Output "AAYS_REMOTE_REPORT_BLOB=$($RemoteBlob.StdOut.Trim())"

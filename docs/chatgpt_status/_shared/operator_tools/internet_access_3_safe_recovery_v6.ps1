[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RepoRoot,
    [Parameter(Mandatory=$true)][string]$GitExe,
    [string]$CanonicalBranch = 'codex/aays-single-runner-v5-20260706',
    [string]$OperatorBranch = 'operator/internet-access-3-recovery-probe-20260723-6d92b4'
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$SlotId = 'internet_access_3'
$TaskId = 'aays1-internet-access-3-migrate-existing-then-no-data-20260722'
$AttemptId = 'internet-access-3-20260722-001'
$ContinuationKey = 'd4b44f265a8ba0ff5fdd1f76f07a20f1f41c8023ed1f6bce91061f5ea94d0c0c'
$ReportRel = 'docs/chatgpt_status/_shared/operator_reports/internet_access_3/recovery_execute_latest.json'
$ManifestRel = 'docs/chatgpt_status/_shared/operator_reports/internet_access_3/recovery_execute_manifest_latest.json'
$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function UtcNow { (Get-Date).ToUniversalTime().ToString('o') }
function Prop($Object,[string]$Name) {
    if ($null -eq $Object) { return $null }
    $p = $Object.PSObject.Properties[$Name]
    if ($p) { return $p.Value }
    return $null
}
function ReadJson([string]$Path) {
    try {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    } catch {}
    return $null
}
function SafeText([string]$Text) {
    if ($null -eq $Text) { return '' }
    $x = $Text -replace '(?i)(ghp_|github_pat_)[A-Za-z0-9_]+','[REDACTED_TOKEN]'
    $x = $x -replace '(?i)(Authorization:\s*Bearer\s+)\S+','$1[REDACTED]'
    $x = $x -replace '(https?://)[^/@\s]+:[^/@\s]+@','$1[REDACTED]@'
    return $x
}
function RunGit([string]$Cwd,[string[]]$Arguments,[int]$TimeoutSeconds=300) {
    $out = [IO.Path]::GetTempFileName()
    $err = [IO.Path]::GetTempFileName()
    try {
        $full = @('-c',"safe.directory=$Cwd",'-C',$Cwd) + $Arguments
        $p = Start-Process -FilePath $GitExe -ArgumentList $full -WorkingDirectory $Cwd -PassThru -NoNewWindow -RedirectStandardOutput $out -RedirectStandardError $err
        if (-not $p.WaitForExit($TimeoutSeconds * 1000)) {
            Stop-Process -Id $p.Id -ErrorAction SilentlyContinue
            throw "GIT_TIMEOUT=$($Arguments -join ' ')"
        }
        $p.Refresh()
        return [pscustomobject]@{
            Code = [int]$p.ExitCode
            Out = [string](Get-Content -LiteralPath $out -Raw -ErrorAction SilentlyContinue)
            Err = [string](Get-Content -LiteralPath $err -Raw -ErrorAction SilentlyContinue)
        }
    } finally {
        Remove-Item -LiteralPath $out,$err -Force -ErrorAction SilentlyContinue
    }
}
function AssertGit($Result,[string]$Code) {
    if ($Result.Code -ne 0) { throw "$Code=$(SafeText (($Result.Err+' '+$Result.Out).Trim()))" }
}
function Daemons([string]$Root) {
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $c = [string]$_.CommandLine
        $c -and $c -match 'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707\.ps1' -and $c.IndexOf($Root,[StringComparison]::OrdinalIgnoreCase) -ge 0
    })
}
function Heartbeat([string]$Path) {
    $h = ReadJson $Path
    if ($null -eq $h) { return $null }
    try { $at = [DateTimeOffset]::Parse([string](Prop $h 'heartbeat_at')).ToUniversalTime() } catch { return $null }
    return [pscustomobject]@{ Data=$h; At=$at.ToString('o'); Age=[math]::Round(([DateTimeOffset]::UtcNow-$at).TotalSeconds,1) }
}
function Http200([string]$Url) {
    try { return ([int](Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10).StatusCode -eq 200) } catch { return $false }
}
function WriteJson([string]$Path,$Value,[int]$Depth=30) {
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    [IO.File]::WriteAllText($Path,(($Value|ConvertTo-Json -Depth $Depth)+"`n"),$Utf8NoBom)
}
function ReadRemoteJson([string]$RelativePath) {
    $r = RunGit $RepoRoot @('show',"origin/$CanonicalBranch`:$RelativePath") 120
    if ($r.Code -ne 0) { return $null }
    try { return $r.Out | ConvertFrom-Json } catch { return $null }
}

$RepoRoot = [IO.Path]::GetFullPath($RepoRoot).TrimEnd('\')
$Report = [ordered]@{
    schema_version=6; captured_at=UtcNow; run_id=$RunId; slot_id=$SlotId; task_id=$TaskId; attempt_id=$AttemptId; continuation_key=$ContinuationKey
    result='RECOVERY_STARTED'; action='none'; error=$null; repo_root=$RepoRoot; canonical_branch=$CanonicalBranch; canonical_head=$null
    dirty_path_count=0; dirty_paths=@(); daemon_count_before=0; daemon_pids_before=@(); daemon_count_after=0; daemon_pids_after=@()
    lock_present=$false; lock_pid=0; lock_identity_valid=$false; heartbeat_before_at=$null; heartbeat_before_age_seconds=$null
    heartbeat_after_at=$null; heartbeat_after_age_seconds=$null; runner_fresh=$false; single_runner_only=$false; parallel_runner=$false
    launcher_invoked=$false; launcher_exit_code=$null; refresh_signal_created=$false; current_task_id=''; last_pickup_task_id=''
    remote_global_current_task_id=''; remote_slot_state=''; remote_pickup_observed=$false; remote_manual_action_state=''
    health_http_200=$false; map_http_200=$false; openapi_http_200=$false
    force_push_used=$false; reset_hard_used=$false; git_clean_used=$false; user_data_deleted=$false; new_task_created=$false; second_runner_started=$false; final_ready=$false
}

try {
    Write-Output 'AAYS_STAGE=VERIFY_REPOSITORY'
    AssertGit (RunGit $RepoRoot @('remote','get-url','origin') 60) 'REMOTE_READ_FAILED'
    $fetchArgs = @('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','fetch','--no-tags','origin',"+refs/heads/$CanonicalBranch`:refs/remotes/origin/$CanonicalBranch")
    AssertGit (RunGit $RepoRoot $fetchArgs 300) 'CANONICAL_FETCH_FAILED'
    $head = RunGit $RepoRoot @('rev-parse',"origin/$CanonicalBranch") 60
    AssertGit $head 'CANONICAL_HEAD_FAILED'
    $Report.canonical_head = $head.Out.Trim()

    $status = RunGit $RepoRoot @('status','--porcelain=v1','-uall') 120
    AssertGit $status 'STATUS_FAILED'
    $dirty = @($status.Out -split "`r?`n" | Where-Object { $_ } | ForEach-Object { if ($_.Length -gt 3) { $_.Substring(3).Trim() } } | Select-Object -First 200)
    $Report.dirty_path_count = $dirty.Count
    $Report.dirty_paths = $dirty

    $gitDirResult = RunGit $RepoRoot @('rev-parse','--git-dir') 60
    AssertGit $gitDirResult 'GIT_DIR_FAILED'
    $gitDir = $gitDirResult.Out.Trim()
    if (-not [IO.Path]::IsPathRooted($gitDir)) { $gitDir = Join-Path $RepoRoot $gitDir }
    $activeOps = @('MERGE_HEAD','CHERRY_PICK_HEAD','REVERT_HEAD','rebase-merge','rebase-apply') | ForEach-Object { Join-Path $gitDir $_ } | Where-Object { Test-Path -LiteralPath $_ }
    if ($activeOps.Count -gt 0) { $Report.result='BLOCKED_ACTIVE_GIT_OPERATION'; $Report.action='preserved'; throw "ACTIVE_GIT_OPERATION=$($activeOps -join ',')" }

    $lockPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
    $hbPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json'
    $launcher = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\automation\START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1'
    $workRoot = Join-Path (Split-Path -Parent $RepoRoot) 'AAYS_STABLE_RUNNER_WORKTREES'
    if (-not (Test-Path -LiteralPath $workRoot)) { New-Item -ItemType Directory -Path $workRoot -Force | Out-Null }

    $before = @(Daemons $RepoRoot)
    $Report.daemon_count_before = $before.Count
    $Report.daemon_pids_before = @($before | ForEach-Object { [int]$_.ProcessId })
    $hbBefore = Heartbeat $hbPath
    if ($hbBefore) { $Report.heartbeat_before_at=$hbBefore.At; $Report.heartbeat_before_age_seconds=$hbBefore.Age }

    $lock = ReadJson $lockPath
    $lockPid = 0
    if ($lock) {
        $sp = Prop $lock 'supervisor_pid'; $pp = Prop $lock 'pid'
        if ($sp) { $lockPid=[int]$sp } elseif ($pp) { $lockPid=[int]$pp }
    }
    $Report.lock_present = Test-Path -LiteralPath $lockPath -PathType Leaf
    $Report.lock_pid = $lockPid
    $lockProc = if ($lockPid -gt 0) { Get-CimInstance Win32_Process -Filter "ProcessId=$lockPid" -ErrorAction SilentlyContinue } else { $null }
    $lockValid = $false
    if ($lock -and $lockProc) {
        $cmd = [string]$lockProc.CommandLine
        $lockValid = ([string](Prop $lock 'lock_scope') -eq 'single_shared_runner_daemon') -and $cmd -match 'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707\.ps1' -and $cmd.IndexOf($RepoRoot,[StringComparison]::OrdinalIgnoreCase) -ge 0
    }
    $Report.lock_identity_valid = $lockValid

    if ($before.Count -gt 1) { $Report.result='BLOCKED_MULTIPLE_CANONICAL_DAEMONS'; $Report.action='no_process_terminated'; throw 'MULTIPLE_CANONICAL_DAEMONS' }

    $invokeLauncher = $false
    if ($before.Count -eq 0) {
        if ($lockProc -and -not $lockValid) { $Report.result='BLOCKED_LIVE_LOCK_OWNER_UNVERIFIED'; $Report.action='preserved'; throw 'LIVE_LOCK_OWNER_UNVERIFIED' }
        $invokeLauncher = $true
        $Report.action = 'start_missing_runner'
    } else {
        $fresh = $false
        if ($hbBefore) {
            $fresh = $hbBefore.Age -ge 0 -and $hbBefore.Age -le 120 -and [bool](Prop $hbBefore.Data 'single_runner_only') -and -not [bool](Prop $hbBefore.Data 'parallel_runner')
        }
        if ($fresh) {
            $Report.action = 'preserve_fresh_runner'
        } else {
            $pid = [int]$before[0].ProcessId
            if (-not $lockValid -or $lockPid -ne $pid) { $Report.result='BLOCKED_STALE_RUNNER_IDENTITY_UNVERIFIED'; $Report.action='preserved'; throw 'STALE_RUNNER_IDENTITY_UNVERIFIED' }
            $children = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { [int]$_.ParentProcessId -eq $pid })
            if ($children.Count -gt 0) { $Report.result='BLOCKED_STALE_RUNNER_HAS_CHILDREN'; $Report.action='preserved'; throw "STALE_RUNNER_CHILDREN=$(@($children|ForEach-Object{$_.ProcessId}) -join ',')" }
            Write-Output "AAYS_STAGE=STOP_VERIFIED_STALE_RUNNER PID=$pid"
            Stop-Process -Id $pid -ErrorAction Stop
            $deadline=(Get-Date).AddSeconds(20)
            do { Start-Sleep -Milliseconds 500 } while ((Get-Process -Id $pid -ErrorAction SilentlyContinue) -and (Get-Date)-lt$deadline)
            if (Get-Process -Id $pid -ErrorAction SilentlyContinue) { $Report.result='BLOCKED_STALE_RUNNER_DID_NOT_STOP'; throw 'STALE_RUNNER_DID_NOT_STOP' }
            $invokeLauncher=$true
            $Report.action='restart_verified_stale_runner'
        }
    }

    if ($invokeLauncher) {
        if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) { $Report.result='BLOCKED_LAUNCHER_MISSING'; throw 'LAUNCHER_MISSING' }
        Write-Output 'AAYS_STAGE=START_CANONICAL_RUNNER'
        $o=[IO.Path]::GetTempFileName(); $e=[IO.Path]::GetTempFileName()
        try {
            $args=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$launcher,'-RepoRoot',$RepoRoot,'-RepoFullName','cagdascagdas100/chat_gpt_clone_1','-MainBranch',$CanonicalBranch,'-WorkRoot',$workRoot,'-MaxTasks','1','-StaleMinutes','20','-NoPanel')
            $p=Start-Process -FilePath 'powershell.exe' -ArgumentList $args -WorkingDirectory $RepoRoot -PassThru -NoNewWindow -RedirectStandardOutput $o -RedirectStandardError $e
            if (-not $p.WaitForExit(180000)) { Stop-Process -Id $p.Id -ErrorAction SilentlyContinue; $Report.launcher_exit_code=124 } else { $p.Refresh(); $Report.launcher_exit_code=[int]$p.ExitCode }
            $Report.launcher_invoked=$true
        } finally { Remove-Item -LiteralPath $o,$e -Force -ErrorAction SilentlyContinue }
    }

    Write-Output 'AAYS_STAGE=VERIFY_FRESH_HEARTBEAT'
    $runnerFresh=$false; $hbAfter=$null; $deadline=(Get-Date).AddSeconds(180)
    do {
        $ds=@(Daemons $RepoRoot); $h=Heartbeat $hbPath
        if ($ds.Count -eq 1 -and $h -and $h.Age -ge 0 -and $h.Age -le 90 -and [bool](Prop $h.Data 'single_runner_only') -and -not [bool](Prop $h.Data 'parallel_runner')) { $runnerFresh=$true; $hbAfter=$h; break }
        Start-Sleep -Seconds 3
    } while ((Get-Date)-lt$deadline)
    $Report.runner_fresh=$runnerFresh

    if ($runnerFresh) {
        $control=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\control'
        if (-not (Test-Path -LiteralPath $control)) { New-Item -ItemType Directory -Path $control -Force | Out-Null }
        $signal=Join-Path $control 'request_queue_refresh.json'; $tmp="$signal.tmp.$PID"
        WriteJson $tmp ([ordered]@{schema_version=1;requested_at=UtcNow;requested_by='internet_access_3_safe_recovery_v6';slot_id=$SlotId;task_id=$TaskId;attempt_id=$AttemptId;continuation_key=$ContinuationKey;force_push=$false;reset_hard=$false;data_delete=$false;parallel_runner=$false}) 10
        Move-Item -LiteralPath $tmp -Destination $signal -Force
        $Report.refresh_signal_created=$true
        Start-Sleep -Seconds 20
    }

    [void](RunGit $RepoRoot $fetchArgs 300)
    $after=@(Daemons $RepoRoot); $hbAfter=Heartbeat $hbPath
    $Report.daemon_count_after=$after.Count; $Report.daemon_pids_after=@($after|ForEach-Object{[int]$_.ProcessId})
    if ($hbAfter) {
        $Report.heartbeat_after_at=$hbAfter.At; $Report.heartbeat_after_age_seconds=$hbAfter.Age
        $Report.single_runner_only=[bool](Prop $hbAfter.Data 'single_runner_only'); $Report.parallel_runner=[bool](Prop $hbAfter.Data 'parallel_runner')
        $Report.current_task_id=[string](Prop $hbAfter.Data 'current_task_id'); $Report.last_pickup_task_id=[string](Prop $hbAfter.Data 'last_pickup_task_id')
    }
    $Report.health_http_200=Http200 'http://127.0.0.1:8012/health'
    $Report.map_http_200=Http200 'http://127.0.0.1:8012/england_map_web/'
    $Report.openapi_http_200=Http200 'http://127.0.0.1:8012/openapi.json'

    $global=ReadRemoteJson 'docs/chatgpt_status/aays1/queue/current.task.json'
    $slot=ReadRemoteJson 'docs/chatgpt_status/_shared/slots_21/internet_access_3/current_task_latest.json'
    $statusRemote=ReadRemoteJson 'docs/chatgpt_status/_shared/slots_21/internet_access_3/status_latest.json'
    $manual=ReadRemoteJson 'docs/chatgpt_status/_shared/manual_actions/internet_access_3.json'
    $Report.remote_global_current_task_id=[string](Prop $global 'task_id')
    $Report.remote_slot_state=[string](Prop $statusRemote 'state')
    $Report.remote_pickup_observed=[bool](Prop $slot 'runner_pickup_observed')
    $Report.remote_manual_action_state=[string](Prop $manual 'state')

    if (-not $runnerFresh) { $Report.result='RUNNER_RECOVERY_FAILED_NO_FRESH_HEARTBEAT' }
    elseif ($after.Count -ne 1 -or -not $Report.single_runner_only -or $Report.parallel_runner) { $Report.result='RUNNER_RECOVERY_FAILED_SINGLE_RUNNER_CONTRACT' }
    elseif ($Report.remote_manual_action_state -eq 'RESOLVED') { $Report.result='RECOVERY_CONFIRMED_MANUAL_ACTION_RESOLVED' }
    elseif ($Report.remote_pickup_observed -or $Report.current_task_id -eq $TaskId -or $Report.last_pickup_task_id -eq $TaskId) { $Report.result='RUNNER_HEALTHY_INTERNET_ACCESS_3_ACTIVE' }
    else { $Report.result='RUNNER_HEALTHY_SEQUENTIAL_QUEUE_PENDING' }
} catch {
    $Report.error=SafeText $_.Exception.Message
    if ($Report.result -eq 'RECOVERY_STARTED') { $Report.result='RECOVERY_EXCEPTION' }
} finally {
    $Report.captured_at=UtcNow
    $localDir=Join-Path (Split-Path -Parent $RepoRoot) 'AAYS_OPERATOR_REPORTS\internet_access_3'
    if (-not (Test-Path -LiteralPath $localDir)) { New-Item -ItemType Directory -Path $localDir -Force | Out-Null }
    $localReport=Join-Path $localDir 'recovery_execute_latest.json'; $localManifest=Join-Path $localDir 'recovery_execute_manifest_latest.json'
    WriteJson $localReport $Report 40
    $item=Get-Item -LiteralPath $localReport
    $sha=(Get-FileHash -LiteralPath $localReport -Algorithm SHA256).Hash.ToLowerInvariant()
    WriteJson $localManifest ([ordered]@{schema_version=1;generated_at=UtcNow;files=@([ordered]@{path=$ReportRel;size_bytes=$item.Length;sha256=$sha;below_48_mib=($item.Length-lt48MB)});force_push_used=$false;reset_hard_used=$false;user_data_deleted=$false}) 12

    $published=$false; $readback=$false
    try {
        $opFetch=@('fetch','--no-tags','origin',"+refs/heads/$OperatorBranch`:refs/remotes/origin/$OperatorBranch")
        AssertGit (RunGit $RepoRoot $opFetch 300) 'OPERATOR_FETCH_FAILED'
        $pub=Join-Path (Split-Path -Parent $RepoRoot) "AAYS_OPERATOR_RECOVERY_$RunId"
        AssertGit (RunGit $RepoRoot @('worktree','add','--detach',$pub,"origin/$OperatorBranch") 300) 'WORKTREE_ADD_FAILED'
        [void](RunGit $pub @('config','user.name','AAYS Safe Recovery') 60)
        [void](RunGit $pub @('config','user.email','aays-safe-recovery@users.noreply.github.com') 60)
        $rp=Join-Path $pub ($ReportRel-replace'/','\'); $mp=Join-Path $pub ($ManifestRel-replace'/','\')
        $pd=Split-Path -Parent $rp; if (-not(Test-Path -LiteralPath $pd)){New-Item -ItemType Directory -Path $pd -Force|Out-Null}
        Copy-Item -LiteralPath $localReport -Destination $rp -Force; Copy-Item -LiteralPath $localManifest -Destination $mp -Force
        AssertGit (RunGit $pub @('add','--',$ReportRel,$ManifestRel) 120) 'STAGE_FAILED'
        $commit=RunGit $pub @('commit','-m',"AAYS_internet_access_3_recovery_$RunId") 120
        if ($commit.Code -ne 0 -and ($commit.Out+$commit.Err)-notmatch'nothing to commit'){throw "COMMIT_FAILED=$(SafeText($commit.Err+$commit.Out))"}
        AssertGit (RunGit $pub @('push','origin',"HEAD:refs/heads/$OperatorBranch") 300) 'PUSH_FAILED'
        $published=$true
        AssertGit (RunGit $RepoRoot $opFetch 300) 'READBACK_FETCH_FAILED'
        $lb=RunGit $pub @('hash-object','--',$rp) 60; $rb=RunGit $RepoRoot @('rev-parse',"origin/$OperatorBranch`:$ReportRel") 60
        AssertGit $lb 'LOCAL_BLOB_FAILED'; AssertGit $rb 'REMOTE_BLOB_FAILED'
        $readback=($lb.Out.Trim()-eq$rb.Out.Trim())
    } catch { Write-Output "AAYS_REPORT_PUBLISH_ERROR=$(SafeText $_.Exception.Message)" }

    Write-Output "AAYS_RECOVERY_RESULT=$($Report.result)"
    Write-Output "AAYS_RECOVERY_ACTION=$($Report.action)"
    Write-Output "AAYS_RECOVERY_ERROR=$($Report.error)"
    Write-Output "AAYS_RUNNER_FRESH=$($Report.runner_fresh)"
    Write-Output "AAYS_RUNNER_COUNT=$($Report.daemon_count_after)"
    Write-Output "AAYS_RUNNER_PIDS=$(@($Report.daemon_pids_after)-join ',')"
    Write-Output "AAYS_HEARTBEAT_AT=$($Report.heartbeat_after_at)"
    Write-Output "AAYS_HEARTBEAT_AGE_SECONDS=$($Report.heartbeat_after_age_seconds)"
    Write-Output "AAYS_CURRENT_TASK_ID=$($Report.current_task_id)"
    Write-Output "AAYS_GLOBAL_CURRENT_TASK_ID=$($Report.remote_global_current_task_id)"
    Write-Output "AAYS_SLOT_PICKUP_OBSERVED=$($Report.remote_pickup_observed)"
    Write-Output "AAYS_MANUAL_ACTION_STATE=$($Report.remote_manual_action_state)"
    Write-Output "AAYS_REPORT_PUBLISHED=$published"
    Write-Output "AAYS_REPORT_READBACK_VERIFIED=$readback"
    Write-Output 'AAYS_FORCE_PUSH_USED=false'
    Write-Output 'AAYS_RESET_HARD_USED=false'
    Write-Output 'AAYS_USER_DATA_DELETED=false'
    Write-Output 'AAYS_SECOND_RUNNER_STARTED=false'
}

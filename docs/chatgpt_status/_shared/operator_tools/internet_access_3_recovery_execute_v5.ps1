[CmdletBinding()]
param(
    [string]$RepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707',
    [string]$GitExe = '',
    [string]$CanonicalBranch = 'codex/aays-single-runner-v5-20260706',
    [string]$ProbeBranch = 'operator/internet-access-3-recovery-probe-20260723-6d92b4'
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

function Now-Utc { return (Get-Date).ToUniversalTime().ToString('o') }
function Ensure-Directory([string]$Path) { if ($Path -and -not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null } }
function Read-JsonSafe([string]$Path) { try { if (Test-Path -LiteralPath $Path -PathType Leaf) { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } } catch {}; return $null }
function Get-PropertyValue($Object,[string]$Name) { if ($null -eq $Object) { return $null }; $Property=$Object.PSObject.Properties[$Name]; if ($Property) { return $Property.Value }; return $null }
function Sanitize-Text([string]$Text) {
    if ($null -eq $Text) { return '' }
    $Result=$Text -replace '(?i)(ghp_|github_pat_)[A-Za-z0-9_]+','[REDACTED_TOKEN]'
    $Result=$Result -replace '(?i)(Authorization:\s*Bearer\s+)\S+','$1[REDACTED]'
    $Result=$Result -replace '(https?://)[^/@\s]+:[^/@\s]+@','$1[REDACTED]@'
    return $Result
}
function Invoke-GitBounded([string]$WorkingDirectory,[string[]]$Arguments,[int]$TimeoutSeconds=300) {
    $StdOutPath=[IO.Path]::GetTempFileName(); $StdErrPath=[IO.Path]::GetTempFileName()
    try {
        $FullArguments=@('-c',"safe.directory=$WorkingDirectory",'-C',$WorkingDirectory)+$Arguments
        $Process=Start-Process -FilePath $script:GitExe -ArgumentList $FullArguments -WorkingDirectory $WorkingDirectory -PassThru -NoNewWindow -RedirectStandardOutput $StdOutPath -RedirectStandardError $StdErrPath
        if (-not $Process.WaitForExit($TimeoutSeconds*1000)) { Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue; throw "GIT_TIMEOUT=$($Arguments -join ' ')" }
        $Process.Refresh()
        return [pscustomobject]@{ Code=[int]$Process.ExitCode; StdOut=[string](Get-Content -LiteralPath $StdOutPath -Raw -ErrorAction SilentlyContinue); StdErr=[string](Get-Content -LiteralPath $StdErrPath -Raw -ErrorAction SilentlyContinue) }
    } finally { Remove-Item -LiteralPath $StdOutPath,$StdErrPath -Force -ErrorAction SilentlyContinue }
}
function Assert-GitSuccess($Result,[string]$Code) { if ($Result.Code -ne 0) { throw "$Code=$(Sanitize-Text (($Result.StdErr+' '+$Result.StdOut).Trim()))" } }
function Get-CanonicalDaemons([string]$Root) {
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $CommandLine=[string]$_.CommandLine
        $CommandLine -and $CommandLine -match 'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707\.ps1' -and $CommandLine.IndexOf($Root,[StringComparison]::OrdinalIgnoreCase) -ge 0
    })
}
function Get-HeartbeatProof([string]$Path) {
    $Data=Read-JsonSafe $Path
    if ($null -eq $Data) { return $null }
    try { $At=[DateTimeOffset]::Parse([string](Get-PropertyValue $Data 'heartbeat_at')).ToUniversalTime() } catch { return $null }
    return [pscustomobject]@{ Data=$Data; At=$At.ToString('o'); AgeSeconds=[math]::Round(([DateTimeOffset]::UtcNow-$At).TotalSeconds,1) }
}
function Test-Http200([string]$Url) { try { $Response=Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10; return ([int]$Response.StatusCode -eq 200) } catch { return $false } }

$OperatorRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..')).TrimEnd('\')
$RepoRoot = [IO.Path]::GetFullPath($RepoRoot).TrimEnd('\')
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) { throw "CANONICAL_REPO_NOT_FOUND=$RepoRoot" }
if (-not (Test-Path -LiteralPath (Join-Path $OperatorRoot '.git'))) { throw "OPERATOR_WORKTREE_NOT_FOUND=$OperatorRoot" }

if ([string]::IsNullOrWhiteSpace($GitExe)) {
    $GitCommand=Get-Command git.exe -ErrorAction SilentlyContinue
    if (-not $GitCommand) { $GitCommand=Get-Command git -ErrorAction SilentlyContinue }
    if ($GitCommand) { $GitExe=$GitCommand.Source }
    else {
        $PortableRoot='F:\TerraYield_AAYS_Portable'
        foreach ($Candidate in @((Join-Path $PortableRoot 'runtime\git\cmd\git.exe'),(Join-Path $PortableRoot 'runtime\PortableGit\cmd\git.exe'),(Join-Path $PortableRoot 'runtime\git\bin\git.exe'))) {
            if (Test-Path -LiteralPath $Candidate -PathType Leaf) { $GitExe=$Candidate; break }
        }
    }
}
if ([string]::IsNullOrWhiteSpace($GitExe) -or -not (Test-Path -LiteralPath $GitExe -PathType Leaf)) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$script:GitExe=$GitExe

$Payload=[ordered]@{
    schema_version=1; captured_at=Now-Utc; run_id=$RunId; slot_id=$SlotId; task_id=$TaskId; attempt_id=$AttemptId; continuation_key=$ContinuationKey
    result='NOT_STARTED'; error=$null; repo_root=$RepoRoot; operator_root=$OperatorRoot; canonical_branch=$CanonicalBranch; probe_branch=$ProbeBranch
    canonical_head=$null; local_branch=$null; local_dirty_path_count=$null; daemon_count_before=$null; daemon_count_after=$null; daemon_pids_after=@()
    lock_present=$false; lock_pid=$null; lock_identity_valid=$false; heartbeat_before_at=$null; heartbeat_before_age_seconds=$null; heartbeat_after_at=$null; heartbeat_after_age_seconds=$null
    heartbeat_state=$null; heartbeat_current_task_id=$null; heartbeat_last_pickup_task_id=$null; launcher_attempted=$false; launcher_exit_code=$null; launcher_output_tail=''
    refresh_signal_created=$false; health_http_200=$false; openapi_http_200=$false; ready_page_http_200=$false
    force_push_used=$false; reset_hard_used=$false; git_clean_used=$false; user_data_deleted=$false; new_task_created=$false; second_runner_requested=$false; final_ready=$false
}

try {
    $Remote=Invoke-GitBounded $RepoRoot @('remote','get-url','origin') 60; Assert-GitSuccess $Remote 'REMOTE_READ_FAILED'
    if ($Remote.StdOut -notmatch 'cagdascagdas100/chat_gpt_clone_1') { throw 'REMOTE_REPOSITORY_MISMATCH' }

    $FetchArgs=@('-c','pack.windowMemory=8m','-c','pack.packSizeLimit=20m','-c','pack.threads=1','-c','core.compression=0','fetch','--no-tags','origin',("+refs/heads/$CanonicalBranch`:refs/remotes/origin/$CanonicalBranch"))
    $Fetch=Invoke-GitBounded $RepoRoot $FetchArgs 300; Assert-GitSuccess $Fetch 'CANONICAL_FETCH_FAILED'
    $Head=Invoke-GitBounded $RepoRoot @('rev-parse',"origin/$CanonicalBranch") 60; Assert-GitSuccess $Head 'CANONICAL_HEAD_READ_FAILED'; $Payload.canonical_head=$Head.StdOut.Trim()
    $Branch=Invoke-GitBounded $RepoRoot @('rev-parse','--abbrev-ref','HEAD') 60; Assert-GitSuccess $Branch 'LOCAL_BRANCH_READ_FAILED'; $Payload.local_branch=$Branch.StdOut.Trim()
    $Status=Invoke-GitBounded $RepoRoot @('status','--porcelain=v1','-uall') 120; Assert-GitSuccess $Status 'LOCAL_STATUS_FAILED'
    $Dirty=@($Status.StdOut -split "`r?`n" | Where-Object { $_ }); $Payload.local_dirty_path_count=$Dirty.Count

    $LockPath=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
    $HeartbeatPath=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json'
    $LauncherPath=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\automation\START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1'
    $WorkRoot=Join-Path (Split-Path -Parent $RepoRoot) 'AAYS_STABLE_RUNNER_WORKTREES'; Ensure-Directory $WorkRoot

    $BeforeDaemons=@(Get-CanonicalDaemons $RepoRoot); $Payload.daemon_count_before=$BeforeDaemons.Count
    $BeforeHeartbeat=Get-HeartbeatProof $HeartbeatPath
    if ($BeforeHeartbeat) { $Payload.heartbeat_before_at=$BeforeHeartbeat.At; $Payload.heartbeat_before_age_seconds=$BeforeHeartbeat.AgeSeconds }

    $LockData=Read-JsonSafe $LockPath; $Payload.lock_present=(Test-Path -LiteralPath $LockPath)
    $LockPid=0
    if ($LockData) {
        $SupervisorPid=Get-PropertyValue $LockData 'supervisor_pid'; $PidValue=Get-PropertyValue $LockData 'pid'
        if ($null -ne $SupervisorPid) { $LockPid=[int]$SupervisorPid } elseif ($null -ne $PidValue) { $LockPid=[int]$PidValue }
    }
    $Payload.lock_pid=$LockPid
    $LockProcess=$null; if ($LockPid -gt 0) { $LockProcess=Get-Process -Id $LockPid -ErrorAction SilentlyContinue }
    $LockIdentityValid=$false
    if ($LockData -and $LockProcess) {
        $StartMatches=$true; $ExpectedStart=Get-PropertyValue $LockData 'process_start_time'
        if ($ExpectedStart) { try { $StartMatches=[math]::Abs(($LockProcess.StartTime.ToUniversalTime()-([datetime]$ExpectedStart).ToUniversalTime()).TotalSeconds)-lt 2 } catch { $StartMatches=$false } }
        $ScopeMatches=([string](Get-PropertyValue $LockData 'lock_scope') -eq 'single_shared_runner_daemon')
        $LockIdentityValid=($StartMatches -and $ScopeMatches)
    }
    $Payload.lock_identity_valid=$LockIdentityValid

    if ($BeforeDaemons.Count -gt 1) { $Payload.result='BLOCKED_MULTIPLE_CANONICAL_DAEMONS' }
    elseif (($null -ne $LockProcess) -and (-not $LockIdentityValid)) { $Payload.result='BLOCKED_LIVE_LOCK_OWNER_UNVERIFIED' }
    else {
        if ($BeforeDaemons.Count -eq 0) {
            if (-not (Test-Path -LiteralPath $LauncherPath -PathType Leaf)) { throw 'SHARED_LAUNCHER_MISSING' }
            $Payload.launcher_attempted=$true
            $Out=[IO.Path]::GetTempFileName(); $Err=[IO.Path]::GetTempFileName()
            try {
                $Arguments=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$LauncherPath,'-RepoRoot',$RepoRoot,'-RepoFullName','cagdascagdas100/chat_gpt_clone_1','-MainBranch',$CanonicalBranch,'-WorkRoot',$WorkRoot,'-MaxTasks','1','-StaleMinutes','20','-NoPanel')
                $Process=Start-Process -FilePath 'powershell.exe' -ArgumentList $Arguments -WorkingDirectory $RepoRoot -PassThru -NoNewWindow -RedirectStandardOutput $Out -RedirectStandardError $Err
                if (-not $Process.WaitForExit(180000)) { Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue; $Payload.launcher_exit_code=124 } else { $Process.Refresh(); $Payload.launcher_exit_code=[int]$Process.ExitCode }
                $Lines=@(); $Lines+=Get-Content -LiteralPath $Out -ErrorAction SilentlyContinue; $Lines+=Get-Content -LiteralPath $Err -ErrorAction SilentlyContinue
                $Payload.launcher_output_tail=Sanitize-Text (($Lines|Select-Object -Last 80)-join "`n")
            } finally { Remove-Item -LiteralPath $Out,$Err -Force -ErrorAction SilentlyContinue }
        }

        $RunnerFresh=$false; $Deadline=(Get-Date).AddSeconds(180)
        do {
            $Daemons=@(Get-CanonicalDaemons $RepoRoot); $Heartbeat=Get-HeartbeatProof $HeartbeatPath
            if (($Daemons.Count -eq 1) -and $Heartbeat) {
                $Single=[bool](Get-PropertyValue $Heartbeat.Data 'single_runner_only'); $Parallel=[bool](Get-PropertyValue $Heartbeat.Data 'parallel_runner')
                if (($Heartbeat.AgeSeconds -ge 0) -and ($Heartbeat.AgeSeconds -le 90) -and $Single -and (-not $Parallel)) { $RunnerFresh=$true; break }
            }
            Start-Sleep -Seconds 3
        } while ((Get-Date) -lt $Deadline)

        if ($RunnerFresh) {
            $ControlDir=Join-Path $RepoRoot 'docs\chatgpt_status\_shared\control'; Ensure-Directory $ControlDir
            $SignalPath=Join-Path $ControlDir 'request_queue_refresh.json'; $TempSignal="$SignalPath.tmp.$PID"
            [ordered]@{schema_version=1;requested_at=Now-Utc;requested_by='internet_access_3_recovery_execute_v5';slot_id=$SlotId;continuation_key=$ContinuationKey;force_push=$false;reset_hard=$false;data_delete=$false}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $TempSignal -Encoding UTF8
            Move-Item -LiteralPath $TempSignal -Destination $SignalPath -Force; $Payload.refresh_signal_created=$true
            Start-Sleep -Seconds 45
            $FinalHeartbeat=Get-HeartbeatProof $HeartbeatPath
            $FinalDaemons=@(Get-CanonicalDaemons $RepoRoot)
            $Payload.daemon_count_after=$FinalDaemons.Count; $Payload.daemon_pids_after=@($FinalDaemons|ForEach-Object{$_.ProcessId})
            if ($FinalHeartbeat) {
                $Payload.heartbeat_after_at=$FinalHeartbeat.At; $Payload.heartbeat_after_age_seconds=$FinalHeartbeat.AgeSeconds
                $Payload.heartbeat_state=[string](Get-PropertyValue $FinalHeartbeat.Data 'state')
                $Payload.heartbeat_current_task_id=[string](Get-PropertyValue $FinalHeartbeat.Data 'current_task_id')
                $Payload.heartbeat_last_pickup_task_id=[string](Get-PropertyValue $FinalHeartbeat.Data 'last_pickup_task_id')
            }
            if (($Payload.heartbeat_current_task_id -eq $TaskId) -or ($Payload.heartbeat_last_pickup_task_id -eq $TaskId)) { $Payload.result='RUNNER_HEALTHY_INTERNET_ACCESS_3_ACTIVE' }
            else { $Payload.result='RUNNER_HEALTHY_SEQUENTIAL_QUEUE_PENDING' }
        } else { $Payload.result='RUNNER_RECOVERY_FAILED_NO_FRESH_HEARTBEAT' }
    }

    $Payload.health_http_200=Test-Http200 'http://127.0.0.1:8012/health'
    $Payload.openapi_http_200=Test-Http200 'http://127.0.0.1:8012/openapi.json'
    $Payload.ready_page_http_200=Test-Http200 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html'
} catch {
    $Payload.error=Sanitize-Text $_.Exception.Message
    if ($Payload.result -eq 'NOT_STARTED') { $Payload.result='RECOVERY_EXECUTION_ERROR' }
}

$ReportPath=Join-Path $OperatorRoot ($ReportRel -replace '/','\')
$ManifestPath=Join-Path $OperatorRoot ($ManifestRel -replace '/','\')
Ensure-Directory (Split-Path -Parent $ReportPath)
$Payload.captured_at=Now-Utc
[IO.File]::WriteAllText($ReportPath,(($Payload|ConvertTo-Json -Depth 30)+"`n"),$Utf8NoBom)
$ReportItem=Get-Item -LiteralPath $ReportPath
if ($ReportItem.Length -ge 48MB) { throw 'RECOVERY_REPORT_EXCEEDS_48_MIB' }
$ReportSha=(Get-FileHash -LiteralPath $ReportPath -Algorithm SHA256).Hash.ToLowerInvariant()
$Manifest=[ordered]@{schema_version=1;generated_at=Now-Utc;part_limit='less_than_48_MiB';files=@([ordered]@{path=$ReportRel;size_bytes=$ReportItem.Length;sha256=$ReportSha;below_48_mib=$true});force_push_used=$false;user_data_deleted=$false}
[IO.File]::WriteAllText($ManifestPath,(($Manifest|ConvertTo-Json -Depth 10)+"`n"),$Utf8NoBom)

$null=Invoke-GitBounded $OperatorRoot @('config','user.name','AAYS Operator Recovery') 60
$null=Invoke-GitBounded $OperatorRoot @('config','user.email','aays-operator@users.noreply.github.com') 60
$Stage=Invoke-GitBounded $OperatorRoot @('add','--',$ReportRel,$ManifestRel) 120; Assert-GitSuccess $Stage 'REPORT_STAGE_FAILED'
$Commit=Invoke-GitBounded $OperatorRoot @('commit','-m',"AAYS internet_access_3 recovery result $RunId") 120
if (($Commit.Code -ne 0) -and (($Commit.StdOut+$Commit.StdErr) -notmatch 'nothing to commit')) { throw "REPORT_COMMIT_FAILED=$(Sanitize-Text (($Commit.StdErr+$Commit.StdOut).Trim()))" }
$Push=Invoke-GitBounded $OperatorRoot @('push','origin',"HEAD:refs/heads/$ProbeBranch") 300; Assert-GitSuccess $Push 'REPORT_PUSH_FAILED'
Write-Output 'AAYS_RECOVERY_REPORT_PUBLISHED=true'
Write-Output "AAYS_RECOVERY_RESULT=$($Payload.result)"
exit 0

[CmdletBinding()]
param(
    [string]$RepoRoot = '',
    [string]$CanonicalBranch = 'codex/aays-single-runner-v5-20260706',
    [string]$ProbeBranch = 'operator/internet-access-3-recovery-probe-20260723-6d92b4'
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1'
$SlotId = 'internet_access_3'
$TaskId = 'aays1-internet-access-3-migrate-existing-then-no-data-20260722'
$AttemptId = 'internet-access-3-20260722-001'
$ContinuationKey = 'd4b44f265a8ba0ff5fdd1f76f07a20f1f41c8023ed1f6bce91061f5ea94d0c0c'
$ReportRel = 'docs/chatgpt_status/_shared/operator_reports/internet_access_3/recovery_probe_latest.json'
$ManifestRel = 'docs/chatgpt_status/_shared/operator_reports/internet_access_3/recovery_probe_manifest_latest.json'
$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')

function Now-Utc {
    return (Get-Date).ToUniversalTime().ToString('o')
}

function Ensure-Directory {
    param([string]$Path)
    if ($Path -and -not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Read-JsonSafe {
    param([string]$Path)
    try {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    } catch {}
    return $null
}

function Get-PropertyValue {
    param($Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    $Property = $Object.PSObject.Properties[$Name]
    if ($Property) { return $Property.Value }
    return $null
}

function Sanitize-Text {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    $Result = $Text -replace '(?i)(ghp_|github_pat_)[A-Za-z0-9_]+', '[REDACTED_TOKEN]'
    $Result = $Result -replace '(?i)(Authorization:\s*Bearer\s+)\S+', '$1[REDACTED]'
    $Result = $Result -replace '(https?://)[^/@\s]+:[^/@\s]+@', '$1[REDACTED]@'
    return $Result
}

function Invoke-GitBounded {
    param(
        [string]$WorkingDirectory,
        [string[]]$Arguments,
        [int]$TimeoutSeconds = 300
    )

    $StdOutPath = [IO.Path]::GetTempFileName()
    $StdErrPath = [IO.Path]::GetTempFileName()
    try {
        $FullArguments = @('-c', "safe.directory=$WorkingDirectory", '-C', $WorkingDirectory) + $Arguments
        $Process = Start-Process -FilePath $script:GitExe -ArgumentList $FullArguments -WorkingDirectory $WorkingDirectory -PassThru -NoNewWindow -RedirectStandardOutput $StdOutPath -RedirectStandardError $StdErrPath
        try {
            Wait-Process -Id $Process.Id -Timeout $TimeoutSeconds -ErrorAction Stop
        } catch {
            Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
            throw "GIT_TIMEOUT=$($Arguments -join ' ')"
        }
        $Process.Refresh()
        $StdOut = Get-Content -LiteralPath $StdOutPath -Raw -ErrorAction SilentlyContinue
        $StdErr = Get-Content -LiteralPath $StdErrPath -Raw -ErrorAction SilentlyContinue
        return [pscustomobject]@{
            Code = [int]$Process.ExitCode
            StdOut = [string]$StdOut
            StdErr = [string]$StdErr
        }
    } finally {
        Remove-Item -LiteralPath $StdOutPath, $StdErrPath -Force -ErrorAction SilentlyContinue
    }
}

function Assert-GitSuccess {
    param($Result, [string]$Code)
    if ($Result.Code -ne 0) {
        $Detail = Sanitize-Text (($Result.StdErr + ' ' + $Result.StdOut).Trim())
        throw "$Code=$Detail"
    }
}

function Get-CanonicalDaemons {
    param([string]$Root)
    return @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $CommandLine = [string]$_.CommandLine
            $CommandLine -and
            $CommandLine -match 'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707\.ps1' -and
            $CommandLine.IndexOf($Root, [StringComparison]::OrdinalIgnoreCase) -ge 0
        }
    )
}

function Get-HeartbeatProof {
    param([string]$Path)
    $Data = Read-JsonSafe $Path
    if ($null -eq $Data) { return $null }
    try {
        $At = [DateTimeOffset]::Parse([string](Get-PropertyValue $Data 'heartbeat_at')).ToUniversalTime()
    } catch {
        return $null
    }
    return [pscustomobject]@{
        Data = $Data
        At = $At.ToString('o')
        AgeSeconds = [math]::Round(([DateTimeOffset]::UtcNow - $At).TotalSeconds, 1)
    }
}

function Test-Http200 {
    param([string]$Url)
    try {
        $Response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10
        return ([int]$Response.StatusCode -eq 200)
    } catch {
        return $false
    }
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $Candidates = @()
    foreach ($Drive in @(Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
        $Candidates += Join-Path $Drive.Root 'TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
        $Candidates += Join-Path $Drive.Root 'TerraYield_AAYS_Portable\runner_system\adaptive_v2\publisher'
    }
    foreach ($Candidate in $Candidates) {
        $HasGit = Test-Path -LiteralPath (Join-Path $Candidate '.git')
        $HasShared = Test-Path -LiteralPath (Join-Path $Candidate 'docs\chatgpt_status\_shared')
        if ($HasGit -and $HasShared) {
            $RepoRoot = $Candidate
            break
        }
    }
}

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    throw 'CANONICAL_REPO_NOT_FOUND'
}

$script:RepoRoot = [IO.Path]::GetFullPath($RepoRoot).TrimEnd('\')
$GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if ($null -eq $GitCommand) { $GitCommand = Get-Command git -ErrorAction SilentlyContinue }
if ($null -eq $GitCommand) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$script:GitExe = $GitCommand.Source

$RemoteResult = Invoke-GitBounded -WorkingDirectory $script:RepoRoot -Arguments @('remote', 'get-url', 'origin') -TimeoutSeconds 60
Assert-GitSuccess $RemoteResult 'REMOTE_READ_FAILED'
if ($RemoteResult.StdOut -notmatch 'cagdascagdas100/chat_gpt_clone_1') {
    throw 'REMOTE_REPOSITORY_MISMATCH'
}

$FetchArguments = @(
    '-c', 'pack.windowMemory=8m',
    '-c', 'pack.packSizeLimit=20m',
    '-c', 'pack.threads=1',
    '-c', 'core.compression=0',
    'fetch', '--no-tags', 'origin',
    "+refs/heads/$CanonicalBranch`:refs/remotes/origin/$CanonicalBranch"
)
$FetchResult = Invoke-GitBounded -WorkingDirectory $script:RepoRoot -Arguments $FetchArguments -TimeoutSeconds 300
Assert-GitSuccess $FetchResult 'CANONICAL_FETCH_FAILED'

$HeadResult = Invoke-GitBounded -WorkingDirectory $script:RepoRoot -Arguments @('rev-parse', "origin/$CanonicalBranch") -TimeoutSeconds 60
Assert-GitSuccess $HeadResult 'CANONICAL_HEAD_READ_FAILED'
$CanonicalHead = $HeadResult.StdOut.Trim()

$StatusResult = Invoke-GitBounded -WorkingDirectory $script:RepoRoot -Arguments @('status', '--porcelain=v1', '-uall') -TimeoutSeconds 120
Assert-GitSuccess $StatusResult 'LOCAL_STATUS_FAILED'
$DirtyPaths = @()
foreach ($Line in @($StatusResult.StdOut -split "`r?`n" | Where-Object { $_ })) {
    if ($Line.Length -gt 3) { $DirtyPaths += $Line.Substring(3).Trim() }
    if ($DirtyPaths.Count -ge 200) { break }
}

$LockPath = Join-Path $script:RepoRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
$HeartbeatPath = Join-Path $script:RepoRoot 'docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json'
$LauncherPath = Join-Path $script:RepoRoot 'docs\chatgpt_status\_shared\automation\START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1'
$WorkRoot = Join-Path (Split-Path -Parent $script:RepoRoot) 'AAYS_STABLE_RUNNER_WORKTREES'
Ensure-Directory $WorkRoot

$BeforeDaemons = @(Get-CanonicalDaemons $script:RepoRoot)
$BeforeHeartbeat = Get-HeartbeatProof $HeartbeatPath
$LockData = Read-JsonSafe $LockPath
$LockPid = 0
if ($null -ne $LockData) {
    $SupervisorPid = Get-PropertyValue $LockData 'supervisor_pid'
    $PidValue = Get-PropertyValue $LockData 'pid'
    if ($null -ne $SupervisorPid) { $LockPid = [int]$SupervisorPid }
    elseif ($null -ne $PidValue) { $LockPid = [int]$PidValue }
}

$LockProcess = $null
if ($LockPid -gt 0) { $LockProcess = Get-Process -Id $LockPid -ErrorAction SilentlyContinue }
$LockIdentityValid = $false
if (($null -ne $LockData) -and ($null -ne $LockProcess)) {
    $StartMatches = $true
    $ExpectedStart = Get-PropertyValue $LockData 'process_start_time'
    if ($null -ne $ExpectedStart) {
        try {
            $StartMatches = [math]::Abs(($LockProcess.StartTime.ToUniversalTime() - ([datetime]$ExpectedStart).ToUniversalTime()).TotalSeconds) -lt 2
        } catch {
            $StartMatches = $false
        }
    }
    $ScopeMatches = ([string](Get-PropertyValue $LockData 'lock_scope') -eq 'single_shared_runner_daemon')
    $LockIdentityValid = ($StartMatches -and $ScopeMatches)
}

$Action = 'none'
$LauncherAttempted = $false
$LauncherExitCode = $null
$LauncherOutputTail = ''

if ($BeforeDaemons.Count -gt 1) {
    $Action = 'blocked_multiple_canonical_daemons'
} elseif ($BeforeDaemons.Count -eq 1) {
    $Action = 'existing_canonical_daemon_preserved'
} elseif (($null -ne $LockProcess) -and (-not $LockIdentityValid)) {
    $Action = 'blocked_live_lock_owner_unverified'
} else {
    if (-not (Test-Path -LiteralPath $LauncherPath -PathType Leaf)) {
        throw 'SHARED_LAUNCHER_MISSING'
    }
    $LauncherAttempted = $true
    $LauncherStdOut = [IO.Path]::GetTempFileName()
    $LauncherStdErr = [IO.Path]::GetTempFileName()
    try {
        $LauncherArguments = @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $LauncherPath,
            '-RepoRoot', $script:RepoRoot,
            '-RepoFullName', $RepoFullName,
            '-MainBranch', $CanonicalBranch,
            '-WorkRoot', $WorkRoot,
            '-MaxTasks', '1',
            '-StaleMinutes', '20',
            '-NoPanel'
        )
        $LauncherProcess = Start-Process -FilePath 'powershell.exe' -ArgumentList $LauncherArguments -WorkingDirectory $script:RepoRoot -PassThru -NoNewWindow -RedirectStandardOutput $LauncherStdOut -RedirectStandardError $LauncherStdErr
        try {
            Wait-Process -Id $LauncherProcess.Id -Timeout 180 -ErrorAction Stop
        } catch {
            Stop-Process -Id $LauncherProcess.Id -Force -ErrorAction SilentlyContinue
            $LauncherExitCode = 124
        }
        $LauncherProcess.Refresh()
        if ($null -eq $LauncherExitCode) { $LauncherExitCode = [int]$LauncherProcess.ExitCode }
        $OutputLines = @()
        $OutputLines += Get-Content -LiteralPath $LauncherStdOut -ErrorAction SilentlyContinue
        $OutputLines += Get-Content -LiteralPath $LauncherStdErr -ErrorAction SilentlyContinue
        $LauncherOutputTail = Sanitize-Text (($OutputLines | Select-Object -Last 80) -join "`n")
    } finally {
        Remove-Item -LiteralPath $LauncherStdOut, $LauncherStdErr -Force -ErrorAction SilentlyContinue
    }
    if ($LauncherExitCode -eq 0) { $Action = 'shared_launcher_invoked' }
    else { $Action = 'shared_launcher_failed' }
}

$RunnerFresh = $false
$FreshHeartbeat = $null
$RunnerDeadline = (Get-Date).AddSeconds(180)
do {
    $CurrentDaemons = @(Get-CanonicalDaemons $script:RepoRoot)
    $CurrentHeartbeat = Get-HeartbeatProof $HeartbeatPath
    if (($CurrentDaemons.Count -eq 1) -and ($null -ne $CurrentHeartbeat)) {
        $SingleRunnerOnly = [bool](Get-PropertyValue $CurrentHeartbeat.Data 'single_runner_only')
        $ParallelRunner = [bool](Get-PropertyValue $CurrentHeartbeat.Data 'parallel_runner')
        if (($CurrentHeartbeat.AgeSeconds -ge 0) -and ($CurrentHeartbeat.AgeSeconds -le 90) -and $SingleRunnerOnly -and (-not $ParallelRunner)) {
            $RunnerFresh = $true
            $FreshHeartbeat = $CurrentHeartbeat
            break
        }
    }
    Start-Sleep -Seconds 3
} while ((Get-Date) -lt $RunnerDeadline)

$RefreshSignalCreated = $false
if ($RunnerFresh) {
    $ControlDirectory = Join-Path $script:RepoRoot 'docs\chatgpt_status\_shared\control'
    Ensure-Directory $ControlDirectory
    $SignalPath = Join-Path $ControlDirectory 'request_queue_refresh.json'
    $SignalTempPath = "$SignalPath.tmp.$PID"
    $SignalPayload = [ordered]@{
        schema_version = 1
        requested_at = Now-Utc
        requested_by = 'internet_access_3_recovery_probe'
        slot_id = $SlotId
        continuation_key = $ContinuationKey
        force_push = $false
        reset_hard = $false
        data_delete = $false
    }
    $SignalPayload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $SignalTempPath -Encoding UTF8
    Move-Item -LiteralPath $SignalTempPath -Destination $SignalPath -Force
    $RefreshSignalCreated = $true
    Start-Sleep -Seconds 45
}

$SecondFetch = Invoke-GitBounded -WorkingDirectory $script:RepoRoot -Arguments $FetchArguments -TimeoutSeconds 300
$FetchAfterRecoveryOk = ($SecondFetch.Code -eq 0)
$AfterDaemons = @(Get-CanonicalDaemons $script:RepoRoot)
$AfterHeartbeat = Get-HeartbeatProof $HeartbeatPath

function Read-RemoteJson {
    param([string]$RelativePath)
    $ShowSpec = "origin/$CanonicalBranch`:$RelativePath"
    $ShowResult = Invoke-GitBounded -WorkingDirectory $script:RepoRoot -Arguments @('show', $ShowSpec) -TimeoutSeconds 120
    if ($ShowResult.Code -ne 0) { return $null }
    try { return $ShowResult.StdOut | ConvertFrom-Json } catch { return $null }
}

$RemoteManualAction = Read-RemoteJson 'docs/chatgpt_status/_shared/manual_actions/internet_access_3.json'
$RemoteSlotStatus = Read-RemoteJson 'docs/chatgpt_status/_shared/slots_21/internet_access_3/status_latest.json'
$RemoteCurrentTask = Read-RemoteJson 'docs/chatgpt_status/_shared/slots_21/internet_access_3/current_task_latest.json'

$HealthOk = Test-Http200 'http://127.0.0.1:8012/health'
$OpenApiOk = Test-Http200 'http://127.0.0.1:8012/openapi.json'
$ReadyPageOk = Test-Http200 'http://127.0.0.1:8012/england_map_web/geometry_review_3of4_columns_1264.html'

$CurrentTaskId = ''
$LastPickupTaskId = ''
if ($null -ne $AfterHeartbeat) {
    $CurrentTaskId = [string](Get-PropertyValue $AfterHeartbeat.Data 'current_task_id')
    $LastPickupTaskId = [string](Get-PropertyValue $AfterHeartbeat.Data 'last_pickup_task_id')
}
$ManualActionState = [string](Get-PropertyValue $RemoteManualAction 'state')
$PickupObserved = [bool](Get-PropertyValue $RemoteCurrentTask 'runner_pickup_observed')

$Result = 'RUNNER_HEALTHY_SEQUENTIAL_QUEUE_PENDING'
if ($BeforeDaemons.Count -gt 1) { $Result = 'BLOCKED_MULTIPLE_CANONICAL_DAEMONS' }
elseif ($Action -eq 'blocked_live_lock_owner_unverified') { $Result = 'BLOCKED_LIVE_LOCK_OWNER_UNVERIFIED' }
elseif (-not $RunnerFresh) { $Result = 'RUNNER_RECOVERY_FAILED_NO_FRESH_HEARTBEAT' }
elseif ($ManualActionState -eq 'RESOLVED') { $Result = 'RECOVERY_CONFIRMED_MANUAL_ACTION_RESOLVED' }
elseif ($PickupObserved -or ($CurrentTaskId -eq $TaskId) -or ($LastPickupTaskId -eq $TaskId)) { $Result = 'RUNNER_HEALTHY_INTERNET_ACCESS_3_ACTIVE' }

$Report = [ordered]@{
    schema_version = 2
    probe_id = 'internet-access-3-20260723-6d92b4'
    captured_at = Now-Utc
    result = $Result
    slot_id = $SlotId
    task_id = $TaskId
    attempt_id = $AttemptId
    continuation_key = $ContinuationKey
    repo_root = $script:RepoRoot
    repo_full_name = $RepoFullName
    canonical_branch = $CanonicalBranch
    canonical_head = $CanonicalHead
    probe_branch = $ProbeBranch
    local_dirty_path_count = $DirtyPaths.Count
    local_dirty_paths = $DirtyPaths
    daemon_count_before = $BeforeDaemons.Count
    daemon_pids_before = @($BeforeDaemons | ForEach-Object { $_.ProcessId })
    daemon_count_after = $AfterDaemons.Count
    daemon_pids_after = @($AfterDaemons | ForEach-Object { $_.ProcessId })
    lock_present = (Test-Path -LiteralPath $LockPath)
    lock_pid = $LockPid
    lock_process_alive = ($null -ne $LockProcess)
    lock_identity_valid = $LockIdentityValid
    heartbeat_before_at = $(if ($null -ne $BeforeHeartbeat) { $BeforeHeartbeat.At } else { $null })
    heartbeat_before_age_seconds = $(if ($null -ne $BeforeHeartbeat) { $BeforeHeartbeat.AgeSeconds } else { $null })
    heartbeat_after_at = $(if ($null -ne $AfterHeartbeat) { $AfterHeartbeat.At } else { $null })
    heartbeat_after_age_seconds = $(if ($null -ne $AfterHeartbeat) { $AfterHeartbeat.AgeSeconds } else { $null })
    heartbeat_state = $(if ($null -ne $AfterHeartbeat) { [string](Get-PropertyValue $AfterHeartbeat.Data 'state') } else { $null })
    current_task_id = $CurrentTaskId
    last_pickup_task_id = $LastPickupTaskId
    runner_fresh = $RunnerFresh
    single_runner_only = $(if ($null -ne $AfterHeartbeat) { [bool](Get-PropertyValue $AfterHeartbeat.Data 'single_runner_only') } else { $false })
    parallel_runner = $(if ($null -ne $AfterHeartbeat) { [bool](Get-PropertyValue $AfterHeartbeat.Data 'parallel_runner') } else { $false })
    action = $Action
    launcher_attempted = $LauncherAttempted
    launcher_exit_code = $LauncherExitCode
    launcher_output_tail = $LauncherOutputTail
    refresh_signal_created = $RefreshSignalCreated
    health_http_200 = $HealthOk
    openapi_http_200 = $OpenApiOk
    ready_page_http_200 = $ReadyPageOk
    fetch_after_recovery_ok = $FetchAfterRecoveryOk
    remote_manual_action_state = $ManualActionState
    remote_manual_requires_user_action = [bool](Get-PropertyValue $RemoteManualAction 'requires_user_action')
    remote_slot_state = [string](Get-PropertyValue $RemoteSlotStatus 'state')
    remote_pickup_observed = $PickupObserved
    remote_first_unverified_step = [string](Get-PropertyValue $RemoteCurrentTask 'first_unverified_step')
    force_push_used = $false
    reset_hard_used = $false
    git_clean_used = $false
    user_data_deleted = $false
    new_task_created = $false
    second_runner_requested = $false
    report_part_limit_bytes = 50331648
    final_ready = $false
}

$TempRoot = Join-Path ([IO.Path]::GetTempPath()) "aays_probe_$RunId"
Ensure-Directory $TempRoot
$TempReport = Join-Path $TempRoot 'recovery_probe_latest.json'
$TempManifest = Join-Path $TempRoot 'recovery_probe_manifest_latest.json'
[IO.File]::WriteAllText($TempReport, (($Report | ConvertTo-Json -Depth 30) + "`n"), [Text.UTF8Encoding]::new($false))
$ReportItem = Get-Item -LiteralPath $TempReport
if ($ReportItem.Length -ge 48MB) { throw 'REPORT_EXCEEDS_48_MIB' }
$ReportSha256 = (Get-FileHash -LiteralPath $TempReport -Algorithm SHA256).Hash.ToLowerInvariant()
$Manifest = [ordered]@{
    schema_version = 1
    generated_at = Now-Utc
    probe_id = 'internet-access-3-20260723-6d92b4'
    part_limit = 'less_than_48_MiB'
    files = @(
        [ordered]@{
            path = $ReportRel
            size_bytes = $ReportItem.Length
            sha256 = $ReportSha256
            below_48_mib = $true
        }
    )
    force_push_used = $false
    user_data_deleted = $false
}
[IO.File]::WriteAllText($TempManifest, (($Manifest | ConvertTo-Json -Depth 12) + "`n"), [Text.UTF8Encoding]::new($false))

$ProbeFetchArguments = @('fetch', '--no-tags', 'origin', "+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch")
$ProbeFetch = Invoke-GitBounded -WorkingDirectory $script:RepoRoot -Arguments $ProbeFetchArguments -TimeoutSeconds 300
Assert-GitSuccess $ProbeFetch 'PROBE_BRANCH_FETCH_FAILED'

$PublishRoot = Join-Path (Split-Path -Parent $script:RepoRoot) "AAYS_OPERATOR_PROBE_WORKTREE_$RunId"
$WorktreeAdd = Invoke-GitBounded -WorkingDirectory $script:RepoRoot -Arguments @('worktree', 'add', '--detach', $PublishRoot, "origin/$ProbeBranch") -TimeoutSeconds 300
Assert-GitSuccess $WorktreeAdd 'PROBE_WORKTREE_ADD_FAILED'

$null = Invoke-GitBounded -WorkingDirectory $PublishRoot -Arguments @('config', 'user.name', 'AAYS Operator Probe') -TimeoutSeconds 60
$null = Invoke-GitBounded -WorkingDirectory $PublishRoot -Arguments @('config', 'user.email', 'aays-operator@users.noreply.github.com') -TimeoutSeconds 60

$ReportPath = Join-Path $PublishRoot ($ReportRel -replace '/', '\')
$ManifestPath = Join-Path $PublishRoot ($ManifestRel -replace '/', '\')
Ensure-Directory (Split-Path -Parent $ReportPath)
Copy-Item -LiteralPath $TempReport -Destination $ReportPath -Force
Copy-Item -LiteralPath $TempManifest -Destination $ManifestPath -Force

$StageResult = Invoke-GitBounded -WorkingDirectory $PublishRoot -Arguments @('add', '--', $ReportRel, $ManifestRel) -TimeoutSeconds 120
Assert-GitSuccess $StageResult 'REPORT_STAGE_FAILED'
$CommitResult = Invoke-GitBounded -WorkingDirectory $PublishRoot -Arguments @('commit', '-m', "AAYS internet_access_3 recovery probe $RunId") -TimeoutSeconds 120
if (($CommitResult.Code -ne 0) -and (($CommitResult.StdOut + $CommitResult.StdErr) -notmatch 'nothing to commit')) {
    throw "REPORT_COMMIT_FAILED=$(Sanitize-Text (($CommitResult.StdErr + $CommitResult.StdOut).Trim()))"
}

$PushSucceeded = $false
for ($Attempt = 1; $Attempt -le 5; $Attempt++) {
    $PushResult = Invoke-GitBounded -WorkingDirectory $PublishRoot -Arguments @('push', 'origin', "HEAD:refs/heads/$ProbeBranch") -TimeoutSeconds 300
    if ($PushResult.Code -eq 0) {
        $PushSucceeded = $true
        break
    }
    $RefreshProbe = Invoke-GitBounded -WorkingDirectory $PublishRoot -Arguments $ProbeFetchArguments -TimeoutSeconds 300
    if ($RefreshProbe.Code -ne 0) { continue }
    $MergeResult = Invoke-GitBounded -WorkingDirectory $PublishRoot -Arguments @('merge', '--no-edit', "origin/$ProbeBranch") -TimeoutSeconds 180
    if ($MergeResult.Code -ne 0) {
        $null = Invoke-GitBounded -WorkingDirectory $PublishRoot -Arguments @('merge', '--abort') -TimeoutSeconds 60
        break
    }
}

if (-not $PushSucceeded) {
    throw "REPORT_PUSH_FAILED_LOCAL_COPY=$TempReport"
}

$ReadbackFetch = Invoke-GitBounded -WorkingDirectory $script:RepoRoot -Arguments $ProbeFetchArguments -TimeoutSeconds 300
Assert-GitSuccess $ReadbackFetch 'REPORT_READBACK_FETCH_FAILED'
$LocalBlob = Invoke-GitBounded -WorkingDirectory $PublishRoot -Arguments @('hash-object', '--', $ReportPath) -TimeoutSeconds 60
Assert-GitSuccess $LocalBlob 'LOCAL_REPORT_BLOB_FAILED'
$RemoteBlob = Invoke-GitBounded -WorkingDirectory $script:RepoRoot -Arguments @('rev-parse', "origin/$ProbeBranch`:$ReportRel") -TimeoutSeconds 60
Assert-GitSuccess $RemoteBlob 'REMOTE_REPORT_BLOB_FAILED'
if ($LocalBlob.StdOut.Trim() -ne $RemoteBlob.StdOut.Trim()) {
    throw 'REPORT_REMOTE_READBACK_MISMATCH'
}

Write-Output 'AAYS_PROBE_PUBLISHED=true'
Write-Output "PROBE_BRANCH=$ProbeBranch"
Write-Output "REPORT_PATH=$ReportRel"
Write-Output "RESULT=$Result"
Write-Output 'FORCE_PUSH_USED=false'
Write-Output 'RESET_HARD_USED=false'
Write-Output 'USER_DATA_DELETED=false'

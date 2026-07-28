param(
    [string]$PortableRoot = $env:AAYS_PORTABLE_ROOT,
    [string]$RepoRoot = $env:AAYS_REPO_ROOT,
    [string]$ArchivePath = "",
    [int]$TimeoutMinutes = 120,
    [int]$PollSeconds = 20,
    [int]$SampleSize = 64
)

$ErrorActionPreference = "Stop"
$SlotId = "internet_access_2"
$TaskId = "internet-access-2-ofcom-dynamic-zip-join-existing-11013-v2-20260722T041000Z"
$Branch = "codex/aays-single-runner-v5-20260706"

if ([string]::IsNullOrWhiteSpace($PortableRoot)) { throw "AAYS_PORTABLE_ROOT_REQUIRED" }
$PortableRoot = [System.IO.Path]::GetFullPath($PortableRoot)
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Join-Path $PortableRoot "runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
}
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
if ([string]::IsNullOrWhiteSpace($ArchivePath)) {
    $ArchivePath = Join-Path $PortableRoot "state\source_cache\ofcom_spring_2026\ofcom_fixed_coverage_202601_v2.zip"
}
$ArchivePath = [System.IO.Path]::GetFullPath($ArchivePath)

if ($TimeoutMinutes -lt 15 -or $TimeoutMinutes -gt 240) { throw "TIMEOUT_MINUTES_OUT_OF_RANGE" }
if ($PollSeconds -lt 5 -or $PollSeconds -gt 300) { throw "POLL_SECONDS_OUT_OF_RANGE" }
if ($SampleSize -lt 8 -or $SampleSize -gt 256) { throw "SAMPLE_SIZE_OUT_OF_RANGE" }
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "REPO_ROOT_NOT_FOUND:$RepoRoot" }

$MultiRouteRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\automation\019_RUN_MULTI_ROUTE_OFCom_STRICT_RECOVERY.ps1"
$PostjoinRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\automation\020_VALIDATE_006_POSTJOIN_READBACK.py"
$QueueRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\queue\internet_access_2_ofcom_dynamic_zip_join_existing_11013_006.v3.task.json"
$CurrentRel = "docs\chatgpt_status\_shared\slots_21\internet_access_2\current_task_latest.json"
$HeartbeatRel = "docs\chatgpt_status\_shared\slots_21\internet_access_2\heartbeat_latest.json"
$SourceRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\source_snapshots\006_ofcom_binary_readback.json"
$ValidationRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\validation\006_existing_11013_coverage_validation.json"
$StatusRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\status\006_status.json"
$DataRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\data\006_existing_11013_official_coverage_candidates.jsonl"
$ProgressRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\progress\006_progress.jsonl"

$MultiRoute = Join-Path $RepoRoot $MultiRouteRel
$Postjoin = Join-Path $RepoRoot $PostjoinRel
foreach ($Required in @($MultiRoute, $Postjoin)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) { throw "REQUIRED_AUTOMATION_NOT_FOUND:$Required" }
}

$GitCandidates = @(
    (Join-Path $PortableRoot "runtime\git\cmd\git.exe"),
    (Join-Path $PortableRoot "runtime\git\bin\git.exe")
)
$GitExe = $GitCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $GitExe) {
    $GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($GitCommand) { $GitExe = $GitCommand.Source }
}
if (-not $GitExe) { throw "GIT_EXECUTABLE_NOT_FOUND" }

$PythonCandidates = @(
    (Join-Path $PortableRoot "runtime\python\python.exe"),
    (Join-Path $PortableRoot "runtime\python\python3.exe")
)
$PythonExe = $PythonCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $PythonExe) {
    $PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($PythonCommand) { $PythonExe = $PythonCommand.Source }
}
if (-not $PythonExe) { throw "PYTHON_EXECUTABLE_NOT_FOUND" }

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
    $Output = & $GitExe -C $RepoRoot @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "GIT_FAILED:$([string]::Join(' ', $Arguments)):$([string]::Join(' | ', @($Output)))"
    }
    return @($Output)
}

function Read-JsonObject {
    param([Parameter(Mandatory=$true)][string]$RelativePath)
    $Path = Join-Path $RepoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        throw "JSON_READ_FAILED:${RelativePath}:$($_.Exception.Message)"
    }
}

function Get-HeartbeatProgressToken {
    param($Heartbeat)
    if (-not $Heartbeat) { return "NO_HEARTBEAT" }

    $TimestampFields = @("heartbeat_at", "last_heartbeat_at", "updated_at", "lease_expires_at")
    $LatestTimestamp = $null
    $FallbackTimestamps = New-Object System.Collections.Generic.List[string]
    foreach ($Field in $TimestampFields) {
        $RawTimestamp = [string]($Heartbeat.$Field)
        if ([string]::IsNullOrWhiteSpace($RawTimestamp)) { continue }
        $FallbackTimestamps.Add($RawTimestamp)
        $ParsedTimestamp = [datetimeoffset]::MinValue
        if ([datetimeoffset]::TryParse($RawTimestamp, [ref]$ParsedTimestamp)) {
            if ($null -eq $LatestTimestamp -or $ParsedTimestamp.UtcTicks -gt $LatestTimestamp.UtcTicks) {
                $LatestTimestamp = $ParsedTimestamp
            }
        }
    }

    if ($null -ne $LatestTimestamp) {
        $Timestamp = $LatestTimestamp.ToUniversalTime().ToString("o")
    }
    elseif ($FallbackTimestamps.Count -gt 0) {
        $Timestamp = [string]($FallbackTimestamps | Sort-Object -Descending | Select-Object -First 1)
    }
    else {
        $Timestamp = "NO_TIMESTAMP"
    }

    return "$([string]($Heartbeat.state))|$Timestamp|$([string]($Heartbeat.attempt_id))"
}

function Assert-CleanRepo {
    $Status = Invoke-Git status --porcelain --untracked-files=no
    if ($Status) { throw "REPO_NOT_CLEAN:$([string]::Join(' | ', @($Status)))" }
}

function Get-LocalHead {
    return ([string](Invoke-Git rev-parse HEAD | Select-Object -First 1)).Trim()
}

function Get-RemoteHead {
    $Remote = Invoke-Git ls-remote origin "refs/heads/$Branch"
    if (-not $Remote) { throw "REMOTE_HEAD_NOT_FOUND" }
    return (([string]($Remote | Select-Object -First 1)) -split "\s+")[0]
}

function Get-FetchedHead {
    return ([string](Invoke-Git rev-parse "refs/remotes/origin/$Branch" | Select-Object -First 1)).Trim()
}

function Sync-RemoteFastForward {
    Assert-CleanRepo
    $Local = Get-LocalHead
    $Fetched = $null
    $Remote = $null
    for ($Attempt = 1; $Attempt -le 2; $Attempt++) {
        Assert-CleanRepo
        Invoke-Git fetch origin $Branch | Out-Null
        $Fetched = Get-FetchedHead
        $Local = Get-LocalHead
        if ($Local -ne $Fetched) {
            Invoke-Git merge --ff-only "origin/$Branch" | Out-Null
        }
        Assert-CleanRepo
        $Local = Get-LocalHead
        $Remote = Get-RemoteHead
        if ($Local -eq $Remote) { return $Local }
    }
    throw "LOCAL_REMOTE_HEAD_MISMATCH_AFTER_BOUNDED_FAST_FORWARD:local=$Local fetched=$Fetched remote=$Remote"
}

function Sync-RemoteForPoll {
    $Status = @(Invoke-Git status --porcelain --untracked-files=no)
    $Local = Get-LocalHead
    $Remote = Get-RemoteHead
    if ($Status) {
        return [ordered]@{
            synced = $false
            reason = "WORKTREE_DIRTY_RUNNER_ACTIVITY"
            local_head = $Local
            fetched_head = $null
            remote_head = $Remote
            synchronization_attempts = 0
            remote_advanced_during_poll = $false
            dirty_paths = @($Status)
        }
    }

    $Fetched = $null
    $FastForwardUsed = $false
    $RemoteAdvanced = $false
    for ($Attempt = 1; $Attempt -le 2; $Attempt++) {
        Invoke-Git fetch origin $Branch | Out-Null
        $Fetched = Get-FetchedHead
        $Local = Get-LocalHead
        if ($Local -ne $Fetched) {
            Invoke-Git merge --ff-only "origin/$Branch" | Out-Null
            $FastForwardUsed = $true
        }

        $StatusAfter = @(Invoke-Git status --porcelain --untracked-files=no)
        $Local = Get-LocalHead
        $Remote = Get-RemoteHead
        if ($StatusAfter) {
            return [ordered]@{
                synced = $false
                reason = "WORKTREE_BECAME_DIRTY_DURING_POLL_SYNC"
                local_head = $Local
                fetched_head = $Fetched
                remote_head = $Remote
                synchronization_attempts = $Attempt
                remote_advanced_during_poll = $RemoteAdvanced
                dirty_paths = @($StatusAfter)
            }
        }
        if ($Local -eq $Remote) {
            return [ordered]@{
                synced = $true
                reason = $(if ($FastForwardUsed) { "FAST_FORWARDED_REMOTE_RUNNER_OUTPUT" } else { "ALREADY_AT_REMOTE_HEAD" })
                local_head = $Local
                fetched_head = $Fetched
                remote_head = $Remote
                synchronization_attempts = $Attempt
                remote_advanced_during_poll = $RemoteAdvanced
                dirty_paths = @()
            }
        }
        if ($Attempt -eq 1) {
            $RemoteAdvanced = $true
            continue
        }
    }

    throw "POLL_LOCAL_REMOTE_HEAD_MISMATCH_AFTER_BOUNDED_RETRY:local=$Local fetched=$Fetched remote=$Remote"
}

function Test-ExactJoinReady {
    $Queue = Read-JsonObject $QueueRel
    $Current = Read-JsonObject $CurrentRel
    $Source = Read-JsonObject $SourceRel
    $Validation = Read-JsonObject $ValidationRel
    $Status = Read-JsonObject $StatusRel

    if ($Queue -and $Queue.task_id -ne $TaskId) { throw "QUEUE_TASK_ID_MISMATCH" }
    if ($Current -and $Current.task_id -ne $TaskId) { throw "CURRENT_TASK_ID_MISMATCH" }

    $QueueStatus = [string]($Queue.status)
    $CurrentState = [string]($Current.state)
    $StatusState = [string]($Status.state)
    $TerminalFailure = @("FAILED", "STOPPED", "STOPPED_CLEAN", "CANCELLED")
    if ($TerminalFailure -contains $QueueStatus.ToUpperInvariant()) {
        throw "QUEUE_TERMINAL_FAILURE:$QueueStatus"
    }
    if ($TerminalFailure -contains $CurrentState.ToUpperInvariant()) {
        throw "CURRENT_TASK_TERMINAL_FAILURE:$CurrentState"
    }
    if ($StatusState.ToUpperInvariant() -match "FAILED|ERROR") {
        throw "BUSINESS_STATUS_FAILURE:$StatusState"
    }

    $AccessState = [string](($Source.access).state)
    $ExactRows = [int]($Source.exact_rows_returned)
    $ScanComplete = [bool]($Validation.source_scan_complete)
    $OutputRows = [int]($Validation.existing_shard2_rows)
    $DataPath = Join-Path $RepoRoot $DataRel
    $DataExists = Test-Path -LiteralPath $DataPath -PathType Leaf

    return [ordered]@{
        ready = ($AccessState -in @("CACHE_HIT", "DOWNLOADED")) -and $ExactRows -gt 0 -and $ScanComplete -and $OutputRows -eq 11013 -and $DataExists
        queue_status = $QueueStatus
        current_state = $CurrentState
        business_state = $StatusState
        access_state = $AccessState
        exact_rows = $ExactRows
        source_scan_complete = $ScanComplete
        output_rows = $OutputRows
        data_exists = [bool]$DataExists
    }
}

$env:AAYS_SLOT_ID = $SlotId
$InitialHead = Sync-RemoteFastForward

$RecoveryOutput = (& $MultiRoute -PortableRoot $PortableRoot -RepoRoot $RepoRoot -ArchivePath $ArchivePath -StartRunner | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "MULTI_ROUTE_RECOVERY_FAILED:$LASTEXITCODE" }

$StartedAt = (Get-Date).ToUniversalTime()
$Deadline = $StartedAt.AddMinutes($TimeoutMinutes)
$LastState = $null
$PollCount = 0
$Ready = $false
$LastSignature = $null
$NoProgressSince = $StartedAt
$LastPollSync = $null
$LastHeartbeatProgressToken = "NO_HEARTBEAT"

while ((Get-Date).ToUniversalTime() -lt $Deadline) {
    $PollCount++
    $LastPollSync = Sync-RemoteForPoll
    $LastState = Test-ExactJoinReady
    if ($LastState.ready) {
        $Ready = $true
        break
    }

    $Heartbeat = Read-JsonObject $HeartbeatRel
    if ($Heartbeat) {
        $HeartbeatState = [string]($Heartbeat.state)
        if ($HeartbeatState.ToUpperInvariant() -match "FAILED|ERROR|STOPPED") {
            throw "RUNNER_HEARTBEAT_TERMINAL_FAILURE:$HeartbeatState"
        }
    }
    $LastHeartbeatProgressToken = Get-HeartbeatProgressToken -Heartbeat $Heartbeat

    $Signature = "$($LastState.queue_status)|$($LastState.current_state)|$($LastState.business_state)|$($LastState.access_state)|$($LastState.exact_rows)|$($LastState.source_scan_complete)|$($LastState.output_rows)|$LastHeartbeatProgressToken"
    if ($Signature -ne $LastSignature) {
        $LastSignature = $Signature
        $NoProgressSince = (Get-Date).ToUniversalTime()
    } else {
        $ActiveState = "$($LastState.queue_status)|$($LastState.current_state)"
        if ($ActiveState -match "(?i)queued|pending|claimed|running|processing" -and ((Get-Date).ToUniversalTime() - $NoProgressSince).TotalMinutes -ge 15) {
            throw "RUNNER_STALLED_WITHOUT_STATE_OR_HEARTBEAT_CHANGE_15_MINUTES:last=$($LastState | ConvertTo-Json -Compress -Depth 5) heartbeat=$LastHeartbeatProgressToken"
        }
    }
    Start-Sleep -Seconds $PollSeconds
}

if (-not $Ready) {
    throw "EXACT_JOIN_TIMEOUT_AFTER_${TimeoutMinutes}_MINUTES:last=$($LastState | ConvertTo-Json -Compress -Depth 5)"
}

$RunnerPublishedHead = Sync-RemoteFastForward
Assert-CleanRepo

$AllowedPublishPaths = @(
    ($ValidationRel -replace "\\", "/"),
    ($StatusRel -replace "\\", "/"),
    ($ProgressRel -replace "\\", "/")
)
$BaselineUntracked = @(Invoke-Git ls-files --others --exclude-standard)

$PostjoinOutput = (& $PythonExe $Postjoin --repo $RepoRoot --archive $ArchivePath --sample-size $SampleSize | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "POSTJOIN_VALIDATOR_FAILED:$LASTEXITCODE" }

$TrackedMutations = @(Invoke-Git diff --name-only)
$UntrackedAfterValidation = @(Invoke-Git ls-files --others --exclude-standard)
$NewUntrackedMutations = @($UntrackedAfterValidation | Where-Object { $_ -notin $BaselineUntracked })
$AllMutations = @($TrackedMutations + $NewUntrackedMutations | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)
$UnexpectedMutations = @($AllMutations | Where-Object { $_ -notin $AllowedPublishPaths })
$MissingMutations = @($AllowedPublishPaths | Where-Object { $_ -notin $AllMutations })
if ($UnexpectedMutations) { throw "POSTJOIN_VALIDATOR_UNEXPECTED_MUTATIONS:$([string]::Join(',', $UnexpectedMutations))" }
if ($MissingMutations) { throw "POSTJOIN_VALIDATOR_MISSING_EXPECTED_MUTATIONS:$([string]::Join(',', $MissingMutations))" }

foreach ($Relative in $AllowedPublishPaths) {
    Invoke-Git add -- $Relative | Out-Null
}
$Staged = @(Invoke-Git diff --cached --name-only)
$Unexpected = @($Staged | Where-Object { $_ -notin $AllowedPublishPaths })
$Missing = @($AllowedPublishPaths | Where-Object { $_ -notin $Staged })
if ($Unexpected) { throw "UNEXPECTED_STAGED_PATHS:$([string]::Join(',', $Unexpected))" }
if ($Missing) { throw "EXPECTED_POSTJOIN_PATHS_NOT_STAGED:$([string]::Join(',', $Missing))" }
$RemainingTracked = @(Invoke-Git diff --name-only)
$UntrackedAfterStage = @(Invoke-Git ls-files --others --exclude-standard)
$RemainingNewUntracked = @($UntrackedAfterStage | Where-Object { $_ -notin $BaselineUntracked })
if ($RemainingTracked) { throw "POSTJOIN_UNSTAGED_TRACKED_MUTATIONS:$([string]::Join(',', $RemainingTracked))" }
if ($RemainingNewUntracked) { throw "POSTJOIN_UNSTAGED_NEW_FILES:$([string]::Join(',', $RemainingNewUntracked))" }

Invoke-Git commit -m "internet_access_2: publish exact Ofcom postjoin readback" | Out-Null
$PostjoinCommit = Get-LocalHead
Invoke-Git push origin "HEAD:$Branch" | Out-Null
$RemoteReadback = Get-RemoteHead
if ($RemoteReadback -ne $PostjoinCommit) {
    throw "POSTJOIN_REMOTE_READBACK_MISMATCH:local=$PostjoinCommit remote=$RemoteReadback"
}

[ordered]@{
    schema_version = 2
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    state = "FULL_HOST_CLOSURE_EXACT_JOIN_AND_POSTJOIN_PUBLISHED"
    slot_id = $SlotId
    task_id = $TaskId
    initial_head = $InitialHead
    runner_published_head = $RunnerPublishedHead
    postjoin_commit = $PostjoinCommit
    remote_readback = $true
    poll_count = $PollCount
    timeout_minutes = $TimeoutMinutes
    poll_seconds = $PollSeconds
    sample_size = $SampleSize
    exact_join_state = $LastState
    last_poll_sync = $LastPollSync
    last_heartbeat_progress_token = $LastHeartbeatProgressToken
    postjoin_mutation_scope_checked = $true
    recovery_output = $RecoveryOutput
    postjoin_output = $PostjoinOutput
    same_task_retained = $true
    duplicate_task_created = $false
    second_runner_started = $false
    force_push_used = $false
    reset_used = $false
    final_ready = $false
} | ConvertTo-Json -Depth 9
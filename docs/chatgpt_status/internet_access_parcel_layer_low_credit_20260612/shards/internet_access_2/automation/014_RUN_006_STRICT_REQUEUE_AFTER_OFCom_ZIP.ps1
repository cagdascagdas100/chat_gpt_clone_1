param(
    [string]$PortableRoot = $env:AAYS_PORTABLE_ROOT,
    [string]$RepoRoot = $env:AAYS_REPO_ROOT,
    [string]$ArchivePath = "",
    [switch]$StartRunner
)

$ErrorActionPreference = "Stop"
$Branch = "codex/aays-single-runner-v5-20260706"
$TaskId = "internet-access-2-ofcom-dynamic-zip-join-existing-11013-v2-20260722T041000Z"

if ([string]::IsNullOrWhiteSpace($PortableRoot)) {
    throw "AAYS_PORTABLE_ROOT_REQUIRED"
}
$PortableRoot = [System.IO.Path]::GetFullPath($PortableRoot)

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Join-Path $PortableRoot "runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
}
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)

if ([string]::IsNullOrWhiteSpace($ArchivePath)) {
    $ArchivePath = Join-Path $PortableRoot "state\source_cache\ofcom_spring_2026\ofcom_fixed_coverage_202601_v2.zip"
}
$ArchivePath = [System.IO.Path]::GetFullPath($ArchivePath)

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

if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "REPO_ROOT_NOT_FOUND:$RepoRoot" }
if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) { throw "OFFICIAL_OFCom_ZIP_NOT_FOUND:$ArchivePath" }

$GuardRelative = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\automation\013_requeue_existing_006_after_strict_ofcom_zip.py"
$HeartbeatRelative = "docs\chatgpt_status\_shared\slots_21\internet_access_2\heartbeat_latest.json"
$ClaimRelative = "docs\chatgpt_status\_shared\control\single_runner_active_claim.json"
$QueueRelative = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\queue\internet_access_2_ofcom_dynamic_zip_join_existing_11013_006.v3.task.json"
$GuardPath = Join-Path $RepoRoot $GuardRelative
if (-not (Test-Path -LiteralPath $GuardPath -PathType Leaf)) { throw "STRICT_REQUEUE_GUARD_NOT_FOUND:$GuardPath" }

function Read-JsonObject {
    param([Parameter(Mandatory=$true)][string]$RelativePath)
    $Path = Join-Path $RepoRoot $RelativePath
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "LEASE_GUARD_JSON_NOT_FOUND:$RelativePath" }
    try {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        throw "LEASE_GUARD_JSON_READ_FAILED:${RelativePath}:$($_.Exception.Message)"
    }
}

function Test-LeaseActive {
    param($Value)
    if (-not $Value) { return $false }
    $State = [string]$(if (-not [string]::IsNullOrWhiteSpace([string]$Value.state)) { $Value.state } else { $Value.status })
    $TerminalStates = @("DONE", "PUBLISHED", "BLOCKED", "STOPPED", "STOPPED_CLEAN", "FAILED", "CANCELLED")
    if ($TerminalStates -contains $State.ToUpperInvariant()) { return $false }
    $LeaseRaw = [string]$Value.lease_expires_at
    if ([string]::IsNullOrWhiteSpace($LeaseRaw)) { return $false }
    $Lease = [datetimeoffset]::MinValue
    if (-not [datetimeoffset]::TryParse($LeaseRaw, [ref]$Lease)) {
        throw "LEASE_EXPIRY_PARSE_FAILED:$LeaseRaw"
    }
    return $Lease.ToUniversalTime() -gt [datetimeoffset]::UtcNow
}

function Assert-NoLiveLeaseBeforeRunnerLaunch {
    $Heartbeat = Read-JsonObject -RelativePath $HeartbeatRelative
    $Claim = Read-JsonObject -RelativePath $ClaimRelative
    $Queue = Read-JsonObject -RelativePath $QueueRelative
    if ([string]$Queue.task_id -ne $TaskId) { throw "QUEUE_TASK_ID_CHANGED_BEFORE_RUNNER_LAUNCH" }
    if ([string]$Queue.status -ne "queued") { throw "QUEUE_NOT_QUEUED_BEFORE_RUNNER_LAUNCH:$([string]$Queue.status)" }
    if (Test-LeaseActive -Value $Heartbeat) { throw "SLOT_HEARTBEAT_LEASE_BECAME_ACTIVE_BEFORE_RUNNER_LAUNCH" }
    if (Test-LeaseActive -Value $Claim) { throw "GLOBAL_CLAIM_LEASE_BECAME_ACTIVE_BEFORE_RUNNER_LAUNCH" }
}

$Status = & $GitExe -C $RepoRoot status --porcelain --untracked-files=no
if ($LASTEXITCODE -ne 0) { throw "GIT_STATUS_FAILED" }
if ($Status) { throw "REPO_NOT_CLEAN_BEFORE_REQUEUE:$($Status -join ' | ')" }

$LocalHead = (& $GitExe -C $RepoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($LocalHead)) { throw "LOCAL_HEAD_READ_FAILED" }
$RemoteLine = & $GitExe -C $RepoRoot ls-remote origin "refs/heads/$Branch"
if ($LASTEXITCODE -ne 0 -or -not $RemoteLine) { throw "REMOTE_HEAD_READ_FAILED" }
$RemoteHead = (($RemoteLine | Select-Object -First 1) -split "\s+")[0]
if ($LocalHead -ne $RemoteHead) { throw "LOCAL_HEAD_NOT_REMOTE_HEAD_BEFORE_REQUEUE:local=$LocalHead remote=$RemoteHead" }

$GitDir = Split-Path -Parent $GitExe
if ([string]::IsNullOrWhiteSpace($GitDir) -or -not (Test-Path -LiteralPath $GitDir -PathType Container)) {
    throw "GIT_EXECUTABLE_DIRECTORY_INVALID:$GitExe"
}
$env:PATH = "$GitDir;$env:PATH"
$env:AAYS_GIT_EXE = $GitExe
$env:AAYS_PORTABLE_ROOT = $PortableRoot
$env:AAYS_REPO_ROOT = $RepoRoot
$env:AAYS_SLOT_ID = "internet_access_2"

$ResolvedGit = Get-Command git -ErrorAction SilentlyContinue
if (-not $ResolvedGit) { throw "GIT_NOT_RESOLVABLE_FOR_PYTHON_GUARD_AFTER_PATH_EXPORT" }

& $PythonExe $GuardPath --repo $RepoRoot --archive $ArchivePath --publish
if ($LASTEXITCODE -ne 0) { throw "STRICT_REQUEUE_GUARD_FAILED:$LASTEXITCODE" }

$PreLaunchLeaseRecheckPassed = $false
if ($StartRunner) {
    Assert-NoLiveLeaseBeforeRunnerLaunch
    $PreLaunchLeaseRecheckPassed = $true
    $Launcher = Join-Path $PortableRoot "RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK.cmd"
    if (-not (Test-Path -LiteralPath $Launcher -PathType Leaf)) { throw "SAFE_RUNNER_LAUNCHER_NOT_FOUND:$Launcher" }
    & $Launcher
    if ($LASTEXITCODE -ne 0) { throw "SAFE_RUNNER_LAUNCH_FAILED:$LASTEXITCODE" }
}

[ordered]@{
    schema_version = 2
    state = "STRICT_006_REQUEUE_WRAPPER_COMPLETE"
    task_id = $TaskId
    repo_root = $RepoRoot
    archive_path = $ArchivePath
    portable_git_path_exported = $true
    python_guard_git_resolvable = $true
    local_remote_head_match = $true
    existing_task_requeued = $true
    runner_start_requested = [bool]$StartRunner
    prelaunch_slot_and_global_lease_recheck_passed = [bool]$PreLaunchLeaseRecheckPassed
    duplicate_task_created = $false
    second_runner_forced = $false
    final_ready = $false
} | ConvertTo-Json -Depth 5

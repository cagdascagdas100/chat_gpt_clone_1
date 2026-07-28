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
$ClosureRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\automation\022_RUN_021_WITH_BOUNDED_PUBLISH_RECOVERY.ps1"

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

function Invoke-Git {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
    $Output = & $GitExe -C $RepoRoot @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "GIT_FAILED:$([string]::Join(' ', $Arguments)):$([string]::Join(' | ', @($Output)))"
    }
    return @($Output)
}

function Get-LocalHead {
    return ([string](Invoke-Git rev-parse HEAD | Select-Object -First 1)).Trim()
}

function Get-RemoteHead {
    $Remote = Invoke-Git ls-remote origin "refs/heads/$Branch"
    if (-not $Remote) { throw "REMOTE_HEAD_NOT_FOUND" }
    return (([string]($Remote | Select-Object -First 1)) -split "\s+")[0]
}

$TrackedStatus = @(Invoke-Git status --porcelain --untracked-files=no)
if ($TrackedStatus) {
    throw "BOOTSTRAP_REPO_NOT_CLEAN:$([string]::Join(' | ', $TrackedStatus))"
}
$CurrentBranch = ([string](Invoke-Git rev-parse --abbrev-ref HEAD | Select-Object -First 1)).Trim()
if ($CurrentBranch -ne $Branch) { throw "BOOTSTRAP_BRANCH_MISMATCH:current=$CurrentBranch expected=$Branch" }

$BeforeHead = Get-LocalHead
$RemoteBefore = Get-RemoteHead
Invoke-Git fetch origin $Branch | Out-Null
if ($BeforeHead -ne $RemoteBefore) {
    Invoke-Git merge --ff-only "origin/$Branch" | Out-Null
}
$AfterHead = Get-LocalHead
$RemoteAfter = Get-RemoteHead
if ($AfterHead -ne $RemoteAfter) {
    throw "BOOTSTRAP_LOCAL_REMOTE_HEAD_MISMATCH:local=$AfterHead remote=$RemoteAfter"
}

$Closure = Join-Path $RepoRoot $ClosureRel
if (-not (Test-Path -LiteralPath $Closure -PathType Leaf)) { throw "CLOSURE_022_NOT_FOUND_AFTER_BOOTSTRAP:$Closure" }
$env:AAYS_SLOT_ID = $SlotId
$ClosureOutput = (& $Closure -PortableRoot $PortableRoot -RepoRoot $RepoRoot -ArchivePath $ArchivePath -TimeoutMinutes $TimeoutMinutes -PollSeconds $PollSeconds -SampleSize $SampleSize | Out-String).Trim()
if ($LASTEXITCODE -ne 0) { throw "CLOSURE_022_NONZERO_EXIT:$LASTEXITCODE" }

[ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    state = "CANONICAL_FAST_FORWARD_BOOTSTRAP_AND_022_COMPLETE"
    slot_id = $SlotId
    task_id = $TaskId
    branch = $Branch
    local_head_before = $BeforeHead
    remote_head_before = $RemoteBefore
    local_head_after = $AfterHead
    remote_head_after = $RemoteAfter
    fast_forward_used = ($BeforeHead -ne $RemoteBefore)
    closure_path = $ClosureRel
    closure_output = $ClosureOutput
    same_task_retained = $true
    duplicate_task_created = $false
    second_runner_started = $false
    force_push_used = $false
    reset_used = $false
    final_ready = $false
} | ConvertTo-Json -Depth 12

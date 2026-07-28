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

if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw "REPO_ROOT_NOT_FOUND:$RepoRoot" }
$Closure = Join-Path $PSScriptRoot "021_RUN_FULL_OFCom_HOST_CLOSURE.ps1"
if (-not (Test-Path -LiteralPath $Closure -PathType Leaf)) { throw "CLOSURE_021_NOT_FOUND:$Closure" }

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

$AllowedPublishPaths = @(
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/validation/006_existing_11013_coverage_validation.json",
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/status/006_status.json",
    "docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_2/progress/006_progress.jsonl"
)

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

function Assert-CleanRepo {
    $Status = @(Invoke-Git status --porcelain --untracked-files=no)
    if ($Status) { throw "REPO_NOT_CLEAN_FOR_PUBLISH_RECOVERY:$([string]::Join(' | ', $Status))" }
}

function Assert-PostjoinCommitScope {
    param([Parameter(Mandatory=$true)][string]$Commit)
    $Paths = @(Invoke-Git diff-tree --no-commit-id --name-only -r $Commit)
    $Unexpected = @($Paths | Where-Object { $_ -notin $AllowedPublishPaths })
    $Missing = @($AllowedPublishPaths | Where-Object { $_ -notin $Paths })
    if ($Unexpected) { throw "RECOVERY_COMMIT_HAS_UNEXPECTED_PATHS:$([string]::Join(',', $Unexpected))" }
    if ($Missing) { throw "RECOVERY_COMMIT_MISSING_POSTJOIN_PATHS:$([string]::Join(',', $Missing))" }
}

function Test-IsAncestor {
    param(
        [Parameter(Mandatory=$true)][string]$Ancestor,
        [Parameter(Mandatory=$true)][string]$Descendant
    )
    & $GitExe -C $RepoRoot merge-base --is-ancestor $Ancestor $Descendant 2>$null
    if ($LASTEXITCODE -eq 0) { return $true }
    if ($LASTEXITCODE -eq 1) { return $false }
    throw "ANCESTRY_CHECK_FAILED:$Ancestor:$Descendant"
}

$env:AAYS_SLOT_ID = $SlotId
$BeforeHead = Get-LocalHead
$PrimaryOutput = $null
$PrimaryError = $null
$RecoveryUsed = $false
$Rebased = $false

try {
    $PrimaryOutput = (& $Closure -PortableRoot $PortableRoot -RepoRoot $RepoRoot -ArchivePath $ArchivePath -TimeoutMinutes $TimeoutMinutes -PollSeconds $PollSeconds -SampleSize $SampleSize | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "CLOSURE_021_NONZERO_EXIT:$LASTEXITCODE" }

    [ordered]@{
        schema_version = 1
        generated_at = (Get-Date).ToUniversalTime().ToString('o')
        state = "FULL_HOST_CLOSURE_COMPLETED_WITHOUT_PUBLISH_RECOVERY"
        slot_id = $SlotId
        task_id = $TaskId
        closure_output = $PrimaryOutput
        publish_recovery_used = $false
        duplicate_task_created = $false
        second_runner_started = $false
        final_ready = $false
    } | ConvertTo-Json -Depth 10
    exit 0
}
catch {
    $PrimaryError = $_.Exception.Message
}

if ($PrimaryError -notmatch "GIT_FAILED:push origin HEAD:" -and $PrimaryError -notmatch "POSTJOIN_REMOTE_READBACK_MISMATCH") {
    throw "CLOSURE_021_FAILED_WITHOUT_SAFE_PUBLISH_RECOVERY_PATH:$PrimaryError"
}

$RecoveryUsed = $true
Assert-CleanRepo
$PostjoinCommit = Get-LocalHead
if ($PostjoinCommit -eq $BeforeHead) {
    throw "PUBLISH_RECOVERY_REFUSED_NO_NEW_POSTJOIN_COMMIT:$PrimaryError"
}
Assert-PostjoinCommitScope -Commit $PostjoinCommit

Invoke-Git fetch origin $Branch | Out-Null
$RemoteHeadBefore = Get-RemoteHead
if (Test-IsAncestor -Ancestor $PostjoinCommit -Descendant "origin/$Branch") {
    [ordered]@{
        schema_version = 1
        generated_at = (Get-Date).ToUniversalTime().ToString('o')
        state = "POSTJOIN_COMMIT_ALREADY_CONTAINED_IN_REMOTE"
        slot_id = $SlotId
        task_id = $TaskId
        postjoin_commit = $PostjoinCommit
        remote_head = $RemoteHeadBefore
        postjoin_commit_ancestor_of_remote = $true
        primary_error = $PrimaryError
        publish_recovery_used = $RecoveryUsed
        rebase_used = $false
        duplicate_task_created = $false
        second_runner_started = $false
        final_ready = $false
    } | ConvertTo-Json -Depth 10
    exit 0
}

$RebaseOutput = & $GitExe -C $RepoRoot rebase "origin/$Branch" 2>&1
if ($LASTEXITCODE -ne 0) {
    $RebaseError = [string]::Join(' | ', @($RebaseOutput))
    & $GitExe -C $RepoRoot rebase --abort 2>$null | Out-Null
    throw "BOUNDED_POSTJOIN_REBASE_FAILED:$RebaseError"
}
$Rebased = $true
$PostjoinCommit = Get-LocalHead
Assert-CleanRepo
Assert-PostjoinCommitScope -Commit $PostjoinCommit

$PushOutput = & $GitExe -C $RepoRoot push origin "HEAD:$Branch" 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "BOUNDED_POSTJOIN_PUSH_RETRY_FAILED:$([string]::Join(' | ', @($PushOutput)))"
}

Invoke-Git fetch origin $Branch | Out-Null
$RemoteHeadAfter = Get-RemoteHead
if (-not (Test-IsAncestor -Ancestor $PostjoinCommit -Descendant "origin/$Branch")) {
    throw "POSTJOIN_COMMIT_NOT_CONTAINED_IN_REMOTE_AFTER_RECOVERY:commit=$PostjoinCommit remote=$RemoteHeadAfter"
}

[ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    state = "POSTJOIN_PUBLISH_RACE_RECOVERED_AND_REMOTE_VERIFIED"
    slot_id = $SlotId
    task_id = $TaskId
    postjoin_commit = $PostjoinCommit
    remote_head_before = $RemoteHeadBefore
    remote_head_after = $RemoteHeadAfter
    postjoin_commit_ancestor_of_remote = $true
    primary_error = $PrimaryError
    publish_recovery_used = $RecoveryUsed
    rebase_used = $Rebased
    bounded_push_retry_count = 1
    same_task_retained = $true
    duplicate_task_created = $false
    second_runner_started = $false
    final_ready = $false
} | ConvertTo-Json -Depth 10

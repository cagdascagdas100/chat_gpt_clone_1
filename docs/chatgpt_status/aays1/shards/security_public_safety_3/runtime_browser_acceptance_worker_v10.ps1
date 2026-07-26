$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$slotId = if ($env:AAYS_SLOT_ID) { [string]$env:AAYS_SLOT_ID } else { 'security_public_safety_3' }
$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'security-public-safety-3-resume-9147406c4a5f' }
$continuationKey = '9147406c4a5fb6fbd06910dddf2b38c200878a801d5bb0907aaf395f6170d1da'
$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
if ($slotId -ne 'security_public_safety_3') { Write-Error "SLOT_ID_MISMATCH:$slotId"; exit 2 }

function Resolve-RepoRoot {
    try {
        $candidate = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null).Trim()
        if ($candidate) { return $candidate }
    } catch {}
    $cursor = $PSScriptRoot
    while ($cursor) {
        if (Test-Path -LiteralPath (Join-Path $cursor '.git')) { return $cursor }
        $parent = Split-Path -Parent $cursor
        if (-not $parent -or $parent -eq $cursor) { break }
        $cursor = $parent
    }
    return $null
}

$repoRoot = Resolve-RepoRoot
if (-not $repoRoot) { Write-Error 'REPO_ROOT_UNAVAILABLE'; exit 2 }

$selfRelative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v10.ps1'
$innerRelative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v9.ps1'
$innerExpectedBlob = '34f03776bc20caec82ebe0c1ecac67fde4e1211f'
$queueRelative = 'docs/chatgpt_status/_shared/slots_21/security_public_safety_3/queue/9147406c4a5fb6fbd06910dddf2b38c200878a801d5bb0907aaf395f6170d1da.v3.task.json'
$statusRelative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/status/runtime_browser_acceptance_latest.json'
$operationRelative = 'england_map_web/data/aays_21_slots/security_public_safety_3/runtime_browser_acceptance_latest.json'
$selfPath = Join-Path $repoRoot $selfRelative
$innerPath = Join-Path $repoRoot $innerRelative
$queuePath = Join-Path $repoRoot $queueRelative
$statusPath = Join-Path $repoRoot $statusRelative
$operationPath = Join-Path $repoRoot $operationRelative

function Write-Utf8NoBom([string]$Path,[string]$Text) {
    $parent = Split-Path -Parent $Path
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))
}
function Write-JsonNoBom([string]$Path,$Value) {
    Write-Utf8NoBom $Path (($Value | ConvertTo-Json -Depth 100) + "`n")
}
function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Get-TrackedBlob([string]$Relative) {
    try { return ((& git -C $repoRoot rev-parse "HEAD:$Relative" 2>$null).Trim()) } catch { return $null }
}
function Test-TrackedFile([string]$Relative,[string]$ExpectedBlob) {
    $path = Join-Path $repoRoot $Relative
    if (-not (Test-Path -LiteralPath $path)) { return "TRACKED_FILE_MISSING:$Relative" }
    $blob = Get-TrackedBlob $Relative
    if (-not $blob) { return "TRACKED_BLOB_UNAVAILABLE:$Relative" }
    if ($ExpectedBlob -and $blob -ne $ExpectedBlob) { return "TRACKED_BLOB_MISMATCH:${Relative}:$blob/$ExpectedBlob" }
    & git -C $repoRoot diff --quiet -- $Relative
    if ($LASTEXITCODE -ne 0) { return "TRACKED_WORKTREE_DIRTY:$Relative" }
    & git -C $repoRoot diff --cached --quiet -- $Relative
    if ($LASTEXITCODE -ne 0) { return "TRACKED_INDEX_DIRTY:$Relative" }
    return $null
}
function Set-Property($Object,[string]$Name,$Value) {
    $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
}
function Write-FallbackEvidence([string]$Reason,[Nullable[int]]$InnerExitCode) {
    $finishedAt = [DateTimeOffset]::UtcNow.ToString('o')
    $status = [ordered]@{
        schema_version=3
        architecture_version=3
        workstream_id='AAYS_21_SLOT_SAFE_PARALLEL_V1'
        slot_id=$slotId
        task_id=$taskId
        continuation_key=$continuationKey
        status='RUNTIME_BROWSER_ACCEPTANCE_BLOCKED'
        acceptance_pass=$false
        worker_contract_version='v10_queue_bound_staged_unstaged_integrity_fail_closed'
        inner_worker_contract_version='v9_v8_v7_tracked_worker_integrity_fail_closed'
        wrapper_worker_path=$selfRelative
        inner_worker_path=$innerRelative
        queue_path=$queueRelative
        inner_exit_code=$InnerExitCode
        blockers=@($Reason)
        started_at=$startedAt
        finished_at=$finishedAt
        single_runner_only=$true
        new_runner=$false
        parallel_runner=$false
        data_deleted=$false
        force_push_used=$false
        reset_hard_used=$false
        fake_data=$false
        db_write=$false
        migration=$false
        production_deploy=$false
        final_ready=$false
    }
    $operation = [ordered]@{
        schema_version=1
        slot_id=$slotId
        continuation_key=$continuationKey
        generated_at=$finishedAt
        operations=@([ordered]@{
            operation_id='security_public_safety_3_runtime_browser_acceptance'
            operation_type='runtime_browser_acceptance'
            stage='v10_queue_bound_staged_unstaged_integrity_fail_closed'
            status='blocked'
            accuracy_score_4=4
            confidence_score=0
            worker_contract_version='v10_queue_bound_staged_unstaged_integrity_fail_closed'
            inner_exit_code=$InnerExitCode
            result=$Reason
            evidence_path=$statusRelative
            needs_manual_review=$true
        })
    }
    Write-JsonNoBom $statusPath $status
    Write-JsonNoBom $operationPath $operation
}

foreach ($check in @(
    @{Relative=$selfRelative;Expected=$null},
    @{Relative=$innerRelative;Expected=$innerExpectedBlob},
    @{Relative=$queueRelative;Expected=$null}
)) {
    $reason = Test-TrackedFile ([string]$check.Relative) ([string]$check.Expected)
    if ($reason) { Write-FallbackEvidence $reason $null; exit 2 }
}

$selfBlob = Get-TrackedBlob $selfRelative
$queue = $null
try { $queue = Get-Content -LiteralPath $queuePath -Raw -Encoding UTF8 | ConvertFrom-Json } catch {
    Write-FallbackEvidence ('QUEUE_PARSE_FAILED:' + $_.Exception.Message) $null
    exit 2
}
$queueValid = (
    [string]$queue.slot_id -eq $slotId -and
    [string]$queue.task_id -eq $taskId -and
    [string]$queue.continuation_key -eq $continuationKey -and
    [string]$queue.status -eq 'queued_for_single_shared_runner' -and
    [string]$queue.script_path -eq $selfRelative -and
    [string]$queue.automation_script -eq $selfRelative -and
    [string]$queue.worker_contract_version -eq 'v10_queue_bound_staged_unstaged_integrity_fail_closed' -and
    [string]$queue.worker_blob_sha -eq $selfBlob -and
    [bool]$queue.same_task_preserved -and
    [bool]$queue.same_continuation_key_preserved -and
    -not [bool]$queue.new_task_created -and
    -not [bool]$queue.new_runner_created -and
    -not [bool]$queue.parallel_runner_created
)
if (-not $queueValid) { Write-FallbackEvidence 'QUEUE_TO_EXECUTED_WORKER_BINDING_MISMATCH' $null; exit 2 }

$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($innerPath,[ref]$tokens,[ref]$parseErrors)
if (@($parseErrors).Count -gt 0) {
    $messages = @($parseErrors | ForEach-Object { $_.Message }) -join ' | '
    Write-FallbackEvidence ("INNER_V9_PARSE_FAILED:$messages") $null
    exit 2
}

$enginePath = $null
try { $enginePath = (Get-Process -Id $PID -ErrorAction Stop).Path } catch {}
if (-not $enginePath -or -not (Test-Path -LiteralPath $enginePath)) {
    foreach ($name in @('pwsh','powershell')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command -and $command.Source) { $enginePath = $command.Source; break }
    }
}
if (-not $enginePath -or -not (Test-Path -LiteralPath $enginePath)) {
    Write-FallbackEvidence 'POWERSHELL_ENGINE_UNAVAILABLE' $null
    exit 2
}

$beforeStatusSha = Get-Sha256 $statusPath
$beforeOperationSha = Get-Sha256 $operationPath
$innerExitCode = 2
try {
    & $enginePath -NoProfile -ExecutionPolicy Bypass -File $innerPath
    if ($null -ne $LASTEXITCODE) { $innerExitCode = [int]$LASTEXITCODE }
} catch {
    Write-FallbackEvidence ('INNER_V9_LAUNCH_EXCEPTION:' + $_.Exception.Message) $innerExitCode
    exit 2
}

if (-not (Test-Path -LiteralPath $statusPath)) { Write-FallbackEvidence 'INNER_STATUS_NOT_CREATED' $innerExitCode; exit 2 }
if (-not (Test-Path -LiteralPath $operationPath)) { Write-FallbackEvidence 'INNER_OPERATION_NOT_CREATED' $innerExitCode; exit 2 }
$afterStatusSha = Get-Sha256 $statusPath
$afterOperationSha = Get-Sha256 $operationPath
if ($beforeStatusSha -and $beforeStatusSha -eq $afterStatusSha) { Write-FallbackEvidence 'INNER_STATUS_NOT_REFRESHED' $innerExitCode; exit 2 }
if ($beforeOperationSha -and $beforeOperationSha -eq $afterOperationSha) { Write-FallbackEvidence 'INNER_OPERATION_NOT_REFRESHED' $innerExitCode; exit 2 }

try {
    $status = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $operationDoc = Get-Content -LiteralPath $operationPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $operations = @($operationDoc.operations)
    if ($operations.Count -ne 1) { Write-FallbackEvidence 'INNER_OPERATION_COUNT_MISMATCH' $innerExitCode; exit 2 }
    $operation = $operations[0]
    $acceptancePass = [bool]$status.acceptance_pass
    if ($acceptancePass) {
        $passValid = (
            [string]$status.worker_contract_version -eq 'v9_v8_v7_tracked_worker_integrity_fail_closed' -and
            [bool]$status.tracked_worker_integrity_pass -and
            [bool]$status.canonical_content_binding_pass -and
            [bool]$status.matrix_canonical_content_match -and
            [bool]$status.security_rows_canonical_content_match -and
            [bool]$status.browser_exact_parcel_set_match -and
            @($status.browser_missing_parcel_ids).Count -eq 0 -and
            @($status.browser_unexpected_parcel_ids).Count -eq 0 -and
            [int]$status.served_security_row_count -eq 300 -and
            [string]$status.selected_layer -eq 'security' -and
            [int]$status.browser_dom_security_row_count -eq 300 -and
            [int]$status.browser_filtered_security_row_count -eq 300 -and
            [int]$status.browser_page_size -eq 25 -and
            [int]$status.browser_page_count -eq 12 -and
            [int]$status.browser_rendered_across_pages -eq 300 -and
            [int]$status.browser_unique_parcel_count -eq 300 -and
            [int]$status.console_error_count -eq 0 -and
            [int]$status.runtime_exception_count -eq 0 -and
            [int]$status.browser_log_error_count -eq 0 -and
            [string]$operation.status -eq 'completed' -and
            [bool]$operation.tracked_worker_integrity_pass -and
            [bool]$operation.canonical_content_binding_pass -and
            $innerExitCode -eq 0
        )
        if (-not $passValid) { Write-FallbackEvidence 'INNER_V9_PASS_CONTRACT_INVALID' $innerExitCode; exit 2 }
        Set-Property $status 'worker_contract_version' 'v10_queue_bound_staged_unstaged_integrity_fail_closed'
        Set-Property $status 'inner_worker_contract_version' 'v9_v8_v7_tracked_worker_integrity_fail_closed'
        Set-Property $status 'wrapper_worker_path' $selfRelative
        Set-Property $status 'queue_path' $queueRelative
        Set-Property $status 'queue_worker_blob_sha' ([string]$queue.worker_blob_sha)
        Set-Property $status 'executed_worker_blob_sha' $selfBlob
        Set-Property $status 'queue_worker_binding_pass' $true
        Set-Property $status 'staged_and_unstaged_integrity_pass' $true
        Set-Property $status 'finished_at' ([DateTimeOffset]::UtcNow.ToString('o'))
        Write-JsonNoBom $statusPath $status
        Set-Property $operation 'worker_contract_version' 'v10_queue_bound_staged_unstaged_integrity_fail_closed'
        Set-Property $operation 'queue_worker_blob_sha' ([string]$queue.worker_blob_sha)
        Set-Property $operation 'executed_worker_blob_sha' $selfBlob
        Set-Property $operation 'queue_worker_binding_pass' $true
        Set-Property $operation 'staged_and_unstaged_integrity_pass' $true
        Set-Property $operation 'result' 'RUNTIME_BROWSER_ACCEPTANCE_VERIFIED_V10_QUEUE_BOUND_STAGED_UNSTAGED_INTEGRITY'
        Write-JsonNoBom $operationPath $operationDoc
        exit 0
    }
    if ($innerExitCode -eq 0) { Write-FallbackEvidence 'INNER_V9_EXIT_ZERO_WITH_BLOCKED_STATUS' $innerExitCode; exit 2 }
    exit 1
} catch {
    Write-FallbackEvidence ('INNER_V9_SCHEMA_VALIDATION_EXCEPTION:' + $_.Exception.Message) $innerExitCode
    exit 2
}

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

$statusRelative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/status/runtime_browser_acceptance_latest.json'
$operationRelative = 'england_map_web/data/aays_21_slots/security_public_safety_3/runtime_browser_acceptance_latest.json'
$innerRelative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v7.ps1'
$statusPath = Join-Path $repoRoot $statusRelative
$operationPath = Join-Path $repoRoot $operationRelative
$innerPath = Join-Path $repoRoot $innerRelative

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
        worker_contract_version='v8_v7_process_isolation_fail_closed'
        inner_worker_contract_version='v7_exact_set_canonical_content_binding'
        inner_worker_path=$innerRelative
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
            stage='v8_v7_process_isolation_fail_closed'
            status='blocked'
            accuracy_score_4=4
            confidence_score=0
            worker_contract_version='v8_v7_process_isolation_fail_closed'
            inner_worker_contract_version='v7_exact_set_canonical_content_binding'
            inner_exit_code=$InnerExitCode
            result=$Reason
            evidence_path=$statusRelative
            needs_manual_review=$true
        })
    }
    Write-JsonNoBom $statusPath $status
    Write-JsonNoBom $operationPath $operation
}

if (-not (Test-Path -LiteralPath $innerPath)) {
    Write-FallbackEvidence 'INNER_V7_WORKER_MISSING' $null
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
    Write-FallbackEvidence ('INNER_V7_LAUNCH_EXCEPTION:' + $_.Exception.Message) $innerExitCode
    exit 2
}

if (-not (Test-Path -LiteralPath $statusPath)) {
    Write-FallbackEvidence 'INNER_STATUS_NOT_CREATED' $innerExitCode
    exit 2
}
if (-not (Test-Path -LiteralPath $operationPath)) {
    Write-FallbackEvidence 'INNER_OPERATION_NOT_CREATED' $innerExitCode
    exit 2
}

$afterStatusSha = Get-Sha256 $statusPath
$afterOperationSha = Get-Sha256 $operationPath
if ($beforeStatusSha -and $beforeStatusSha -eq $afterStatusSha) {
    Write-FallbackEvidence 'INNER_STATUS_NOT_REFRESHED' $innerExitCode
    exit 2
}
if ($beforeOperationSha -and $beforeOperationSha -eq $afterOperationSha) {
    Write-FallbackEvidence 'INNER_OPERATION_NOT_REFRESHED' $innerExitCode
    exit 2
}

$innerStatus = $null
$operationDoc = $null
try {
    $innerStatus = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $operationDoc = Get-Content -LiteralPath $operationPath -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    Write-FallbackEvidence ('INNER_ARTIFACT_PARSE_FAILED:' + $_.Exception.Message) $innerExitCode
    exit 2
}

try {
    $operations = @($operationDoc.operations)
    if ($operations.Count -ne 1) {
        Write-FallbackEvidence 'INNER_OPERATION_COUNT_MISMATCH' $innerExitCode
        exit 2
    }
    $acceptancePass = [bool]$innerStatus.acceptance_pass
    if ($acceptancePass) {
        $operation = $operations[0]
        $passContractValid = (
            [string]$innerStatus.worker_contract_version -eq 'v7_exact_set_canonical_content_binding' -and
            [bool]$innerStatus.canonical_content_binding_pass -and
            [bool]$innerStatus.matrix_canonical_content_match -and
            [bool]$innerStatus.security_rows_canonical_content_match -and
            [bool]$innerStatus.browser_exact_parcel_set_match -and
            @($innerStatus.browser_missing_parcel_ids).Count -eq 0 -and
            @($innerStatus.browser_unexpected_parcel_ids).Count -eq 0 -and
            [int]$innerStatus.served_security_row_count -eq 300 -and
            [string]$innerStatus.selected_layer -eq 'security' -and
            [int]$innerStatus.browser_dom_security_row_count -eq 300 -and
            [int]$innerStatus.browser_filtered_security_row_count -eq 300 -and
            [int]$innerStatus.browser_page_size -eq 25 -and
            [int]$innerStatus.browser_page_count -eq 12 -and
            [int]$innerStatus.browser_rendered_across_pages -eq 300 -and
            [int]$innerStatus.browser_unique_parcel_count -eq 300 -and
            [int]$innerStatus.console_error_count -eq 0 -and
            [int]$innerStatus.runtime_exception_count -eq 0 -and
            [int]$innerStatus.browser_log_error_count -eq 0 -and
            [string]$operation.status -eq 'completed' -and
            [bool]$operation.canonical_content_binding_pass
        )
        if (-not $passContractValid) {
            Write-FallbackEvidence 'INNER_V7_PASS_CONTRACT_INVALID' $innerExitCode
            exit 2
        }
        if ($innerExitCode -ne 0) {
            Write-FallbackEvidence 'INNER_V7_EXIT_NONZERO_WITH_PASS_STATUS' $innerExitCode
            exit 2
        }
        exit 0
    }

    if ($innerExitCode -eq 0) {
        Write-FallbackEvidence 'INNER_V7_EXIT_ZERO_WITH_BLOCKED_STATUS' $innerExitCode
        exit 2
    }
    exit 1
} catch {
    Write-FallbackEvidence ('INNER_V7_SCHEMA_VALIDATION_EXCEPTION:' + $_.Exception.Message) $innerExitCode
    exit 2
}

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

$selfRelative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v12.ps1'
$innerRelative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v9.ps1'
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
function Write-JsonNoBom([string]$Path,$Value) { Write-Utf8NoBom $Path (($Value | ConvertTo-Json -Depth 100) + "`n") }
function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Get-TrackedBlob([string]$Relative,[string]$Revision='HEAD') {
    try { return ((& git -C $repoRoot rev-parse "${Revision}:$Relative" 2>$null).Trim()) } catch { return $null }
}
function Test-TrackedExact([string]$Relative,[string]$ExpectedBlob) {
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
function Get-RepoFullName([string]$RemoteUrl) {
    $value = $RemoteUrl.Trim()
    if ($value -match '(?i)github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$') {
        return (($Matches[1] + '/' + $Matches[2]) -replace '\.git$','')
    }
    return $null
}
function Set-Property($Object,[string]$Name,$Value) { $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force }
function Write-FallbackEvidence([string]$Reason,[Nullable[int]]$InnerExitCode) {
    $finishedAt = [DateTimeOffset]::UtcNow.ToString('o')
    $status = [ordered]@{
        schema_version=3; architecture_version=3; workstream_id='AAYS_21_SLOT_SAFE_PARALLEL_V1'; slot_id=$slotId
        task_id=$taskId; continuation_key=$continuationKey; status='RUNTIME_BROWSER_ACCEPTANCE_BLOCKED'; acceptance_pass=$false
        worker_contract_version='v12_actual_execution_chain_repository_branch_integrity_fail_closed'
        inner_worker_contract_version='v9_v8_v7_tracked_worker_integrity_fail_closed'
        wrapper_worker_path=$selfRelative; inner_worker_path=$innerRelative; queue_path=$queueRelative
        inner_exit_code=$InnerExitCode; blockers=@($Reason); started_at=$startedAt; finished_at=$finishedAt
        single_runner_only=$true; new_runner=$false; parallel_runner=$false; data_deleted=$false; force_push_used=$false
        reset_hard_used=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; final_ready=$false
    }
    $operation = [ordered]@{
        schema_version=1; slot_id=$slotId; continuation_key=$continuationKey; generated_at=$finishedAt
        operations=@([ordered]@{
            operation_id='security_public_safety_3_runtime_browser_acceptance'; operation_type='runtime_browser_acceptance'
            stage='v12_actual_execution_chain_repository_branch_integrity_fail_closed'; status='blocked'; accuracy_score_4=4; confidence_score=0
            worker_contract_version='v12_actual_execution_chain_repository_branch_integrity_fail_closed'; inner_exit_code=$InnerExitCode
            result=$Reason; evidence_path=$statusRelative; needs_manual_review=$true
        })
    }
    Write-JsonNoBom $statusPath $status
    Write-JsonNoBom $operationPath $operation
}

$trackedChecks = @(
    @{Relative=$selfRelative;Expected=$null},
    @{Relative='docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v9.ps1';Expected='34f03776bc20caec82ebe0c1ecac67fde4e1211f'},
    @{Relative='docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v8.ps1';Expected='c731d26a10d4a590e5c6033445798b04828a7a05'},
    @{Relative='docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v7.ps1';Expected='0b2e9ce1f971bde60fee1887804f1f7ab7c4cae6'},
    @{Relative='docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v6.ps1';Expected='c8ebb8f0e9dc0e0bb934b330138bb83eb0bb4225'},
    @{Relative='docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v4.ps1';Expected='b6ecd33edf8f53ce8500d6b6717b40799886fd8d'},
    @{Relative='england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html';Expected='f130dfe511eb7530f07a02f9bbca3feccbcca1a3'},
    @{Relative='england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json';Expected='ab876129928ec0370d482ca491f31a5dd1216aab'},
    @{Relative=$queueRelative;Expected=$null}
)
foreach ($check in $trackedChecks) {
    $reason = Test-TrackedExact ([string]$check.Relative) ([string]$check.Expected)
    if ($reason) { Write-FallbackEvidence $reason $null; exit 2 }
}

$queue = $null
try { $queue = Get-Content -LiteralPath $queuePath -Raw -Encoding UTF8 | ConvertFrom-Json } catch {
    Write-FallbackEvidence ('QUEUE_PARSE_FAILED:' + $_.Exception.Message) $null; exit 2
}
$selfBlob = Get-TrackedBlob $selfRelative
$headCommit = ((& git -C $repoRoot rev-parse HEAD 2>$null).Trim())
$originUrl = ((& git -C $repoRoot remote get-url origin 2>$null).Trim())
$actualRepoFullName = Get-RepoFullName $originUrl
if (-not $actualRepoFullName -or $actualRepoFullName -ne [string]$queue.repo_full_name) {
    Write-FallbackEvidence "REPOSITORY_ORIGIN_MISMATCH:$actualRepoFullName/$($queue.repo_full_name)" $null; exit 2
}
$currentBranch = $null
try { $currentBranch = ((& git -C $repoRoot symbolic-ref --quiet --short HEAD 2>$null).Trim()) } catch {}
$canonicalBranch = [string]$queue.canonical_branch
$branchBound = ($currentBranch -eq $canonicalBranch)
if (-not $branchBound) {
    foreach ($refName in @("refs/heads/$canonicalBranch","refs/remotes/origin/$canonicalBranch")) {
        try {
            $tip = ((& git -C $repoRoot rev-parse $refName 2>$null).Trim())
            if ($tip -and $tip -eq $headCommit) { $branchBound = $true; break }
        } catch {}
    }
}
if (-not $branchBound) { Write-FallbackEvidence "CANONICAL_BRANCH_BINDING_MISMATCH:$currentBranch/$canonicalBranch/$headCommit" $null; exit 2 }

$queueWorkerCommit = [string]$queue.worker_commit
if (-not $queueWorkerCommit) { Write-FallbackEvidence 'QUEUE_WORKER_COMMIT_MISSING' $null; exit 2 }
& git -C $repoRoot merge-base --is-ancestor $queueWorkerCommit HEAD
if ($LASTEXITCODE -ne 0) { Write-FallbackEvidence "QUEUE_WORKER_COMMIT_NOT_ANCESTOR:$queueWorkerCommit/$headCommit" $null; exit 2 }
$commitBlob = Get-TrackedBlob $selfRelative $queueWorkerCommit
$queueValid = (
    [string]$queue.slot_id -eq $slotId -and [string]$queue.task_id -eq $taskId -and
    [string]$queue.continuation_key -eq $continuationKey -and [string]$queue.status -eq 'queued_for_single_shared_runner' -and
    [string]$queue.script_path -eq $selfRelative -and [string]$queue.automation_script -eq $selfRelative -and
    [string]$queue.worker_contract_version -eq 'v12_actual_execution_chain_repository_branch_integrity_fail_closed' -and
    [string]$queue.worker_blob_sha -eq $selfBlob -and $commitBlob -eq $selfBlob -and
    [string]$queue.repo_full_name -eq 'cagdascagdas100/chat_gpt_clone_1' -and
    [string]$queue.canonical_branch -eq 'codex/aays-single-runner-v5-20260706' -and
    [bool]$queue.same_task_preserved -and [bool]$queue.same_continuation_key_preserved -and
    -not [bool]$queue.new_task_created -and -not [bool]$queue.new_runner_created -and -not [bool]$queue.parallel_runner_created
)
if (-not $queueValid) { Write-FallbackEvidence 'QUEUE_REPOSITORY_BRANCH_EXECUTED_WORKER_BINDING_MISMATCH' $null; exit 2 }

$tokens=$null; $parseErrors=$null
[void][System.Management.Automation.Language.Parser]::ParseFile($innerPath,[ref]$tokens,[ref]$parseErrors)
if (@($parseErrors).Count -gt 0) {
    Write-FallbackEvidence ('INNER_V9_PARSE_FAILED:' + ((@($parseErrors | ForEach-Object {$_.Message})) -join ' | ')) $null; exit 2
}
$enginePath=$null
try { $enginePath=(Get-Process -Id $PID -ErrorAction Stop).Path } catch {}
if (-not $enginePath -or -not (Test-Path -LiteralPath $enginePath)) {
    foreach ($name in @('pwsh','powershell')) {
        $command=Get-Command $name -ErrorAction SilentlyContinue
        if ($command -and $command.Source) { $enginePath=$command.Source; break }
    }
}
if (-not $enginePath -or -not (Test-Path -LiteralPath $enginePath)) { Write-FallbackEvidence 'POWERSHELL_ENGINE_UNAVAILABLE' $null; exit 2 }

$beforeStatusSha=Get-Sha256 $statusPath; $beforeOperationSha=Get-Sha256 $operationPath; $innerExitCode=2
try {
    & $enginePath -NoProfile -ExecutionPolicy Bypass -File $innerPath
    if ($null -ne $LASTEXITCODE) { $innerExitCode=[int]$LASTEXITCODE }
} catch { Write-FallbackEvidence ('INNER_V9_LAUNCH_EXCEPTION:' + $_.Exception.Message) $innerExitCode; exit 2 }
if (-not (Test-Path -LiteralPath $statusPath)) { Write-FallbackEvidence 'INNER_STATUS_NOT_CREATED' $innerExitCode; exit 2 }
if (-not (Test-Path -LiteralPath $operationPath)) { Write-FallbackEvidence 'INNER_OPERATION_NOT_CREATED' $innerExitCode; exit 2 }
$afterStatusSha=Get-Sha256 $statusPath; $afterOperationSha=Get-Sha256 $operationPath
if ($beforeStatusSha -and $beforeStatusSha -eq $afterStatusSha) { Write-FallbackEvidence 'INNER_STATUS_NOT_REFRESHED' $innerExitCode; exit 2 }
if ($beforeOperationSha -and $beforeOperationSha -eq $afterOperationSha) { Write-FallbackEvidence 'INNER_OPERATION_NOT_REFRESHED' $innerExitCode; exit 2 }

try {
    $status=Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $operationDoc=Get-Content -LiteralPath $operationPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $operations=@($operationDoc.operations)
    if ($operations.Count -ne 1) { Write-FallbackEvidence 'INNER_OPERATION_COUNT_MISMATCH' $innerExitCode; exit 2 }
    $operation=$operations[0]
    if (-not [bool]$status.acceptance_pass) { Write-FallbackEvidence ('INNER_V9_BLOCKED:' + ((@($status.blockers)) -join '|')) $innerExitCode; exit 1 }
    $httpResults=@($status.http_results)
    $httpPass=($httpResults.Count -eq 3 -and @($httpResults | Where-Object { [int]$_.status -ne 200 -or -not [string]$_.sha256 }).Count -eq 0)
    $pageCounts=@($status.browser_page_counts)
    $expectedPageCounts=@($status.browser_expected_page_counts)
    $pageCountsPass=($pageCounts.Count -eq 12 -and @($pageCounts | Where-Object { [int]$_ -ne 25 }).Count -eq 0)
    $expectedPageCountsPass=($expectedPageCounts.Count -eq 12 -and @($expectedPageCounts | Where-Object { [int]$_ -ne 25 }).Count -eq 0)
    $passValid=(
        [string]$status.worker_contract_version -eq 'v9_v8_v7_tracked_worker_integrity_fail_closed' -and
        [bool]$status.tracked_worker_integrity_pass -and [bool]$status.canonical_content_binding_pass -and
        [bool]$status.matrix_canonical_content_match -and [bool]$status.security_rows_canonical_content_match -and
        [bool]$status.browser_exact_parcel_set_match -and @($status.browser_missing_parcel_ids).Count -eq 0 -and
        @($status.browser_unexpected_parcel_ids).Count -eq 0 -and [int]$status.served_security_row_count -eq 300 -and
        [string]$status.selected_layer -eq 'security' -and [int]$status.browser_dom_security_row_count -eq 300 -and
        [int]$status.browser_filtered_security_row_count -eq 300 -and [int]$status.browser_page_size -eq 25 -and
        [int]$status.browser_page_count -eq 12 -and [bool]$status.browser_page_counts_match -and
        $pageCountsPass -and $expectedPageCountsPass -and [int]$status.browser_rendered_across_pages -eq 300 -and
        [int]$status.browser_unique_parcel_count -eq 300 -and $httpPass -and
        [int]$status.console_error_count -eq 0 -and [int]$status.runtime_exception_count -eq 0 -and
        [int]$status.browser_log_error_count -eq 0 -and [string]$operation.status -eq 'completed' -and
        [bool]$operation.tracked_worker_integrity_pass -and [bool]$operation.canonical_content_binding_pass -and $innerExitCode -eq 0
    )
    if (-not $passValid) { Write-FallbackEvidence 'INNER_V9_PASS_CONTRACT_INVALID' $innerExitCode; exit 2 }
    Set-Property $status 'worker_contract_version' 'v12_actual_execution_chain_repository_branch_integrity_fail_closed'
    Set-Property $status 'inner_worker_contract_version' 'v9_v8_v7_tracked_worker_integrity_fail_closed'
    Set-Property $status 'wrapper_worker_path' $selfRelative
    Set-Property $status 'repository_origin_full_name' $actualRepoFullName
    Set-Property $status 'canonical_branch' $canonicalBranch
    Set-Property $status 'executed_head_commit' $headCommit
    Set-Property $status 'queue_worker_commit' $queueWorkerCommit
    Set-Property $status 'repository_branch_binding_pass' $true
    Set-Property $status 'actual_execution_chain_integrity_pass' $true
    Set-Property $status 'http_200_sha_triplet_pass' $httpPass
    Set-Property $status 'all_twelve_page_counts_exact_25_pass' ($pageCountsPass -and $expectedPageCountsPass)
    Set-Property $status 'finished_at' ([DateTimeOffset]::UtcNow.ToString('o'))
    Write-JsonNoBom $statusPath $status
    Set-Property $operation 'worker_contract_version' 'v12_actual_execution_chain_repository_branch_integrity_fail_closed'
    Set-Property $operation 'repository_origin_full_name' $actualRepoFullName
    Set-Property $operation 'canonical_branch' $canonicalBranch
    Set-Property $operation 'executed_head_commit' $headCommit
    Set-Property $operation 'queue_worker_commit' $queueWorkerCommit
    Set-Property $operation 'repository_branch_binding_pass' $true
    Set-Property $operation 'actual_execution_chain_integrity_pass' $true
    Set-Property $operation 'http_200_sha_triplet_pass' $httpPass
    Set-Property $operation 'all_twelve_page_counts_exact_25_pass' ($pageCountsPass -and $expectedPageCountsPass)
    Set-Property $operation 'result' 'RUNTIME_BROWSER_ACCEPTANCE_VERIFIED_V12_ACTUAL_EXECUTION_CHAIN_REPOSITORY_BRANCH_INTEGRITY'
    Write-JsonNoBom $operationPath $operationDoc
    exit 0
} catch {
    Write-FallbackEvidence ('INNER_V9_SCHEMA_VALIDATION_EXCEPTION:' + $_.Exception.Message) $innerExitCode
    exit 2
}

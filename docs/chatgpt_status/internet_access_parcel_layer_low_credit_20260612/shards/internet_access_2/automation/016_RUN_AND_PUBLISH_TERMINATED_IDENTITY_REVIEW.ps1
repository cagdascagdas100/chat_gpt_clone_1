param(
    [string]$PortableRoot = $env:AAYS_PORTABLE_ROOT,
    [string]$RepoRoot = $env:AAYS_REPO_ROOT
)

$ErrorActionPreference = "Stop"
$Branch = "codex/aays-single-runner-v5-20260706"
$SlotId = "internet_access_2"
$ScriptRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\automation\015_export_two_terminated_identity_review_rows.py"
$InputRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\data\005_existing_11013_postcode_identity_candidates.jsonl"
$OutputRel = "england_map_web\data\aays_21_slots\internet_access_2\006_existing_11013_identity_review_rows.json"
$AuditRel = "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\shards\internet_access_2\recovery\014_006_terminated_identity_review_export.json"

if ([string]::IsNullOrWhiteSpace($PortableRoot)) { throw "AAYS_PORTABLE_ROOT_REQUIRED" }
$PortableRoot = [System.IO.Path]::GetFullPath($PortableRoot)
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = Join-Path $PortableRoot "runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707"
}
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
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

$ScriptPath = Join-Path $RepoRoot $ScriptRel
$InputPath = Join-Path $RepoRoot $InputRel
$OutputPath = Join-Path $RepoRoot $OutputRel
$AuditPath = Join-Path $RepoRoot $AuditRel
foreach ($Required in @($ScriptPath, $InputPath)) {
    if (-not (Test-Path -LiteralPath $Required -PathType Leaf)) { throw "REQUIRED_FILE_NOT_FOUND:$Required" }
}

$StatusBefore = & $GitExe -C $RepoRoot status --porcelain --untracked-files=all
if ($LASTEXITCODE -ne 0) { throw "GIT_STATUS_FAILED" }
if ($StatusBefore) { throw "REPO_NOT_CLEAN_BEFORE_REVIEW_EXPORT:$($StatusBefore -join ' | ')" }

$LocalHeadBefore = (& $GitExe -C $RepoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($LocalHeadBefore)) { throw "LOCAL_HEAD_READ_FAILED" }
$RemoteLine = & $GitExe -C $RepoRoot ls-remote origin "refs/heads/$Branch"
if ($LASTEXITCODE -ne 0 -or -not $RemoteLine) { throw "REMOTE_HEAD_READ_FAILED" }
$RemoteHeadBefore = (($RemoteLine | Select-Object -First 1) -split "\s+")[0]
if ($LocalHeadBefore -ne $RemoteHeadBefore) {
    throw "LOCAL_HEAD_NOT_REMOTE_HEAD_BEFORE_REVIEW_EXPORT:local=$LocalHeadBefore remote=$RemoteHeadBefore"
}

$env:AAYS_SLOT_ID = $SlotId
& $PythonExe $ScriptPath --repo-root $RepoRoot
if ($LASTEXITCODE -ne 0) { throw "TERMINATED_REVIEW_EXPORT_FAILED:$LASTEXITCODE" }
foreach ($Generated in @($OutputPath, $AuditPath)) {
    if (-not (Test-Path -LiteralPath $Generated -PathType Leaf)) { throw "EXPECTED_OUTPUT_NOT_FOUND:$Generated" }
}

$Output = Get-Content -LiteralPath $OutputPath -Raw -Encoding UTF8 | ConvertFrom-Json
$Audit = Get-Content -LiteralPath $AuditPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Output.state -ne "EXACT_TWO_TERMINATED_ONSPD_IDENTITIES_EXPORTED_FOR_REVIEW") { throw "OUTPUT_STATE_MISMATCH" }
if ([int]$Output.source_total_rows -ne 11013) { throw "OUTPUT_SOURCE_ROW_COUNT_MISMATCH" }
if ([int]$Output.review_row_count -ne 2 -or @($Output.rows).Count -ne 2) { throw "OUTPUT_REVIEW_COUNT_MISMATCH" }
if ($Output.internet_accuracy -ne "1/4_TERMINATED_POSTCODE_REVIEW_REQUIRED") { throw "OUTPUT_ACCURACY_MISMATCH" }
if ([int]$Output.official_coverage_verified -ne 0) { throw "OUTPUT_FALSE_COVERAGE_UPGRADE" }
foreach ($Row in @($Output.rows)) {
    if ($Row.internet_accuracy -ne "1/4") { throw "ROW_ACCURACY_MISMATCH" }
    if ([bool]$Row.official_coverage_verified) { throw "ROW_FALSE_COVERAGE_UPGRADE" }
    if ($Row.candidate_status -ne "ONSPD_TERMINATED_REVIEW_REQUIRED") { throw "ROW_STATUS_MISMATCH" }
}
if ($Audit.state -ne "TERMINATED_IDENTITY_REVIEW_EXPORT_PASS") { throw "AUDIT_STATE_MISMATCH" }
if ([int]$Audit.observed_review_rows -ne 2) { throw "AUDIT_REVIEW_COUNT_MISMATCH" }

$StatusAfter = @(& $GitExe -C $RepoRoot status --porcelain --untracked-files=all)
if ($LASTEXITCODE -ne 0) { throw "GIT_STATUS_AFTER_EXPORT_FAILED" }
$NormalizedAllowed = @($OutputRel.Replace('\','/'), $AuditRel.Replace('\','/'))
$Unexpected = @()
foreach ($Line in $StatusAfter) {
    if ([string]::IsNullOrWhiteSpace($Line)) { continue }
    $PathPart = $Line.Substring(3).Trim().Replace('\','/')
    if ($PathPart -notin $NormalizedAllowed) { $Unexpected += $Line }
}
if ($Unexpected.Count -gt 0) { throw "UNEXPECTED_WORKTREE_CHANGES:$($Unexpected -join ' | ')" }

& $GitExe -C $RepoRoot add -- $OutputRel $AuditRel
if ($LASTEXITCODE -ne 0) { throw "GIT_ADD_FAILED" }
$Staged = @(& $GitExe -C $RepoRoot diff --cached --name-only)
$ExpectedStaged = @($OutputRel.Replace('\','/'), $AuditRel.Replace('\','/')) | Sort-Object
$ObservedStaged = @($Staged | ForEach-Object { $_.Trim().Replace('\','/') } | Where-Object { $_ } | Sort-Object)
if (($ObservedStaged -join "`n") -ne ($ExpectedStaged -join "`n")) {
    & $GitExe -C $RepoRoot reset -- $OutputRel $AuditRel | Out-Null
    throw "STAGED_PATH_SET_MISMATCH:observed=$($ObservedStaged -join ',')"
}

& $GitExe -C $RepoRoot commit -m "internet_access_2: publish exact terminated identity review rows"
if ($LASTEXITCODE -ne 0) { throw "GIT_COMMIT_FAILED" }
$Commit = (& $GitExe -C $RepoRoot rev-parse HEAD).Trim()
& $GitExe -C $RepoRoot push origin "HEAD:$Branch"
if ($LASTEXITCODE -ne 0) { throw "GIT_PUSH_FAILED" }
$RemoteAfterLine = & $GitExe -C $RepoRoot ls-remote origin "refs/heads/$Branch"
if ($LASTEXITCODE -ne 0 -or -not $RemoteAfterLine) { throw "REMOTE_READBACK_FAILED" }
$RemoteAfter = (($RemoteAfterLine | Select-Object -First 1) -split "\s+")[0]
if ($RemoteAfter -ne $Commit) { throw "REMOTE_READBACK_MISMATCH:local=$Commit remote=$RemoteAfter" }

[ordered]@{
    state = "TERMINATED_IDENTITY_REVIEW_EXPORTED_AND_PUBLISHED"
    slot_id = $SlotId
    source_rows = 11013
    review_rows = 2
    internet_accuracy = "1/4_ONLY"
    official_coverage_verified = 0
    commit = $Commit
    remote_readback = $true
    duplicate_task_created = $false
    second_runner_started = $false
    final_ready = $false
} | ConvertTo-Json -Depth 5

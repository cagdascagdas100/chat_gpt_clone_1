$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$slotId = if ($env:AAYS_SLOT_ID) { [string]$env:AAYS_SLOT_ID } else { 'security_public_safety_3' }
$taskId = if ($env:AAYS_TASK_ID) { [string]$env:AAYS_TASK_ID } else { 'security-public-safety-3-resume-9147406c4a5f' }
$continuationKey = '9147406c4a5fb6fbd06910dddf2b38c200878a801d5bb0907aaf395f6170d1da'
if ($slotId -ne 'security_public_safety_3') { Write-Error "SLOT_ID_MISMATCH:$slotId"; exit 2 }

$repoRoot = (& git rev-parse --show-toplevel 2>$null).Trim()
if (-not $repoRoot) { Write-Error 'REPO_ROOT_UNAVAILABLE'; exit 2 }

$v6Relative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v6.ps1'
$v4Relative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v4.ps1'
$v6ExpectedBlob = 'c8ebb8f0e9dc0e0bb934b330138bb83eb0bb4225'
$v4ExpectedBlob = 'b6ecd33edf8f53ce8500d6b6717b40799886fd8d'
$matrixExpectedBlob = 'f130dfe511eb7530f07a02f9bbca3feccbcca1a3'
$rowsExpectedBlob = 'ab876129928ec0370d482ca491f31a5dd1216aab'
$v6Path = Join-Path $repoRoot $v6Relative
$v4Path = Join-Path $repoRoot $v4Relative

function Assert-TrackedBlob([string]$Relative,[string]$ExpectedBlob) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $Relative))) {
        Write-Error "TRACKED_WORKER_MISSING:$Relative"
        exit 2
    }
    $actualBlob = (& git rev-parse "HEAD:$Relative" 2>$null).Trim()
    if (-not $actualBlob) {
        Write-Error "TRACKED_WORKER_BLOB_UNAVAILABLE:$Relative"
        exit 2
    }
    if ($actualBlob -ne $ExpectedBlob) {
        Write-Error "TRACKED_WORKER_BLOB_MISMATCH:${Relative}:$actualBlob/$ExpectedBlob"
        exit 2
    }
    & git diff --quiet -- $Relative
    if ($LASTEXITCODE -ne 0) {
        Write-Error "TRACKED_WORKER_WORKTREE_DIRTY:$Relative"
        exit 2
    }
}

function Write-Utf8NoBom([string]$Path,[string]$Text) {
    $parent = Split-Path $Path
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))
}

function Write-JsonNoBom([string]$Path,$Value) {
    Write-Utf8NoBom $Path (($Value | ConvertTo-Json -Depth 100) + "`n")
}

function Set-Property($Object,[string]$Name,$Value) {
    $Object | Add-Member -NotePropertyName $Name -NotePropertyValue $Value -Force
}

function Get-NormalizedTextSha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $text = [IO.File]::ReadAllText($Path,[Text.Encoding]::UTF8)
    $text = $text.TrimStart([char]0xFEFF).Replace("`r`n","`n").Replace("`r","`n")
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($text)
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

Assert-TrackedBlob $v6Relative $v6ExpectedBlob
Assert-TrackedBlob $v4Relative $v4ExpectedBlob
Assert-TrackedBlob 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html' $matrixExpectedBlob
Assert-TrackedBlob 'england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json' $rowsExpectedBlob

$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($v6Path,[ref]$tokens,[ref]$parseErrors)
if (@($parseErrors).Count -gt 0) {
    $messages = @($parseErrors | ForEach-Object { $_.Message }) -join ' | '
    Write-Error "V7_V6_WRAPPER_PARSE_FAILED:$messages"
    exit 2
}

$engine = $null
foreach ($name in @('pwsh','powershell')) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) { $engine = $cmd.Source; break }
}
if (-not $engine) { Write-Error 'POWERSHELL_ENGINE_UNAVAILABLE'; exit 2 }

& $engine -NoProfile -ExecutionPolicy Bypass -File $v6Path
$innerExitCode = $LASTEXITCODE
if ($null -eq $innerExitCode) { $innerExitCode = 2 }
if ([int]$innerExitCode -ne 0) { exit ([int]$innerExitCode) }

$statusRelative = 'docs/chatgpt_status/aays1/shards/security_public_safety_3/status/runtime_browser_acceptance_latest.json'
$operationRelative = 'england_map_web/data/aays_21_slots/security_public_safety_3/runtime_browser_acceptance_latest.json'
$statusPath = Join-Path $repoRoot $statusRelative
$operationPath = Join-Path $repoRoot $operationRelative
if (-not (Test-Path -LiteralPath $statusPath)) { Write-Error "V7_STATUS_ARTIFACT_MISSING:$statusRelative"; exit 2 }
if (-not (Test-Path -LiteralPath $operationPath)) { Write-Error "V7_OPERATION_ARTIFACT_MISSING:$operationRelative"; exit 2 }

$status = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
$operationDoc = Get-Content -LiteralPath $operationPath -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not [bool]$status.acceptance_pass) { Write-Error 'V7_INNER_ACCEPTANCE_NOT_PASS'; exit 2 }
if (@($operationDoc.operations).Count -ne 1) { Write-Error 'V7_OPERATION_COUNT_MISMATCH'; exit 2 }

$matrixLocalRelative = 'england_map_web/TerraYield_England_Program_Parcel_Layer_Matrix_20260629.html'
$rowsLocalRelative = 'england_map_web/data/program_layer_matrix/security_public_safety_visible_rows.json'
$matrixLocalPath = Join-Path $repoRoot $matrixLocalRelative
$rowsLocalPath = Join-Path $repoRoot $rowsLocalRelative
$matrixHttp = @($status.http_results | Where-Object { [string]$_.name -eq 'matrix_html' } | Select-Object -First 1)
$rowsHttp = @($status.http_results | Where-Object { [string]$_.name -eq 'security_rows_json' } | Select-Object -First 1)
if (-not $matrixHttp) { Write-Error 'V7_MATRIX_HTTP_RESULT_MISSING'; exit 2 }
if (-not $rowsHttp) { Write-Error 'V7_ROWS_HTTP_RESULT_MISSING'; exit 2 }

$matrixServedPath = Join-Path $repoRoot ([string]$matrixHttp.artifact_path)
$rowsServedPath = Join-Path $repoRoot ([string]$rowsHttp.artifact_path)
$matrixLocalNormalizedSha256 = Get-NormalizedTextSha256 $matrixLocalPath
$matrixServedNormalizedSha256 = Get-NormalizedTextSha256 $matrixServedPath
$rowsLocalNormalizedSha256 = Get-NormalizedTextSha256 $rowsLocalPath
$rowsServedNormalizedSha256 = Get-NormalizedTextSha256 $rowsServedPath
$matrixContentMatch = [bool]($matrixLocalNormalizedSha256 -and $matrixLocalNormalizedSha256 -eq $matrixServedNormalizedSha256)
$rowsContentMatch = [bool]($rowsLocalNormalizedSha256 -and $rowsLocalNormalizedSha256 -eq $rowsServedNormalizedSha256)

$blockers = [Collections.Generic.List[string]]::new()
foreach ($item in @($status.blockers)) {
    if ($item -and -not $blockers.Contains([string]$item)) { $blockers.Add([string]$item) }
}
if (-not $matrixContentMatch) { $blockers.Add('SERVED_MATRIX_HTML_NOT_CANONICAL_LOCAL_CONTENT') }
if (-not $rowsContentMatch) { $blockers.Add('SERVED_SECURITY_ROWS_JSON_NOT_CANONICAL_LOCAL_CONTENT') }

$integrityPass = [bool](
    $blockers.Count -eq 0 -and
    $matrixContentMatch -and
    $rowsContentMatch -and
    [bool]$status.browser_exact_parcel_set_match -and
    @($status.browser_missing_parcel_ids).Count -eq 0 -and
    @($status.browser_unexpected_parcel_ids).Count -eq 0
)

Set-Property $status 'worker_contract_version' 'v7_exact_set_canonical_content_binding'
Set-Property $status 'wrapper_worker_path' 'docs/chatgpt_status/aays1/shards/security_public_safety_3/runtime_browser_acceptance_worker_v7.ps1'
Set-Property $status 'v6_worker_blob_sha' $v6ExpectedBlob
Set-Property $status 'v4_worker_blob_sha' $v4ExpectedBlob
Set-Property $status 'matrix_canonical_blob_sha' $matrixExpectedBlob
Set-Property $status 'security_rows_canonical_blob_sha' $rowsExpectedBlob
Set-Property $status 'matrix_local_normalized_sha256' $matrixLocalNormalizedSha256
Set-Property $status 'matrix_served_normalized_sha256' $matrixServedNormalizedSha256
Set-Property $status 'matrix_canonical_content_match' $matrixContentMatch
Set-Property $status 'security_rows_local_normalized_sha256' $rowsLocalNormalizedSha256
Set-Property $status 'security_rows_served_normalized_sha256' $rowsServedNormalizedSha256
Set-Property $status 'security_rows_canonical_content_match' $rowsContentMatch
Set-Property $status 'canonical_content_binding_pass' $integrityPass
Set-Property $status 'blockers' @($blockers)
Set-Property $status 'acceptance_pass' $integrityPass
Set-Property $status 'status' $(if ($integrityPass) { 'RUNTIME_BROWSER_ACCEPTANCE_VERIFIED' } else { 'RUNTIME_BROWSER_ACCEPTANCE_BLOCKED' })
Set-Property $status 'finished_at' ([DateTimeOffset]::UtcNow.ToString('o'))
Write-JsonNoBom $statusPath $status

$operation = @($operationDoc.operations)[0]
Set-Property $operation 'worker_contract_version' 'v7_exact_set_canonical_content_binding'
Set-Property $operation 'status' $(if ($integrityPass) { 'completed' } else { 'blocked' })
Set-Property $operation 'confidence_score' $(if ($integrityPass) { 100 } else { 0 })
Set-Property $operation 'matrix_local_normalized_sha256' $matrixLocalNormalizedSha256
Set-Property $operation 'matrix_served_normalized_sha256' $matrixServedNormalizedSha256
Set-Property $operation 'matrix_canonical_content_match' $matrixContentMatch
Set-Property $operation 'security_rows_local_normalized_sha256' $rowsLocalNormalizedSha256
Set-Property $operation 'security_rows_served_normalized_sha256' $rowsServedNormalizedSha256
Set-Property $operation 'security_rows_canonical_content_match' $rowsContentMatch
Set-Property $operation 'canonical_content_binding_pass' $integrityPass
Set-Property $operation 'result' $(if ($integrityPass) { 'RUNTIME_BROWSER_ACCEPTANCE_VERIFIED_V7_CANONICAL_CONTENT_BOUND' } else { 'RUNTIME_BROWSER_ACCEPTANCE_BLOCKED_V7_CANONICAL_CONTENT_MISMATCH' })
Set-Property $operation 'needs_manual_review' (-not $integrityPass)
Write-JsonNoBom $operationPath $operationDoc

if ($integrityPass) { exit 0 } else { exit 1 }

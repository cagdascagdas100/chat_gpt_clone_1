[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$attemptId = 'height-difference-2-20260721-020'
$taskVersion = '6.0-fhost-contract-reconciled-exact-chain'
$pickupRequestRevision = 3
$expectedBranch = 'codex/aays-single-runner-v5-20260706'
$expectedPageKey = 'aays1'
$expectedCanonicalBlob = 'bb48164e7a0af78df875f30421a6a3068c43edb8'
$expectedPointEvidenceBlob = '9c2932bf101b0f14740d9fe9a201067b2e5a5aad'
$expectedHmlrEvidenceBlob = 'bb8924be924303833949857c8a0e32296fc8092b'
$expectedExtractorBlob = '63363c56d1cfc7678a07f52b59375cccc5dd9bcf'
$expectedHmlrRecoveryBlob = '0846876dadd5639931c12d3099c36ce8999515fd'
$expectedEntryBlob = 'b9a6982fc3b47cd2614e7b4d4e59adbadc901ae2'
$expectedWebRows = 1004
$entryRel = 'docs\chatgpt_status\aays1\automation\height_difference_2_reconciled_candidate_then_sampling_entry.py'
$extractorRel = 'docs\chatgpt_status\topography\shards\height_difference_2\automation\043_extract_reconciled_exact_candidates.py'
$hmlrRecoveryRel = 'docs\chatgpt_status\topography\shards\height_difference_2\automation\043_prepare_hmlr_sources_and_match.py'
$canonicalRel = 'england_map_web\data\parcel_security_scores_rechecked_0_120m_spatial.geojson'
$pointEvidenceRel = 'england_map_web\data\aays_21_slots\height_difference_2\canonical_points_runtime_032.json'
$hmlrEvidenceRel = 'england_map_web\data\aays_21_slots\height_difference_2\hmlr_exact_polygons_runtime_034_v2.json'

function Resolve-RepoRoot {
  $configured = [string]$env:AAYS_REPO_ROOT
  if ($configured) {
    $candidate = [System.IO.Path]::GetFullPath($configured)
    if (Test-Path -LiteralPath (Join-Path $candidate $entryRel) -PathType Leaf) { return $candidate }
  }
  $cursor = [System.IO.DirectoryInfo](Get-Item -LiteralPath $PSScriptRoot)
  for ($i = 0; $i -lt 12 -and $null -ne $cursor; $i++) {
    if (Test-Path -LiteralPath (Join-Path $cursor.FullName $entryRel) -PathType Leaf) { return $cursor.FullName }
    $cursor = $cursor.Parent
  }
  throw 'HEIGHT_DIFFERENCE_2_REPO_ROOT_NOT_RESOLVED'
}

function Assert-GitBlob([string]$RepoRoot, [string]$RelativePath, [string]$ExpectedBlob, [string]$Label) {
  $path = Join-Path $RepoRoot $RelativePath
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "$Label`_MISSING=$path" }
  $actual = (& $script:git.Source -C $RepoRoot hash-object -- $path 2>&1 | Select-Object -Last 1).ToString().Trim()
  if ($LASTEXITCODE -ne 0 -or $actual -ne $ExpectedBlob) { throw "$Label`_BLOB_MISMATCH=$actual" }
  return $actual
}

$repoRoot = Resolve-RepoRoot
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$script:git = $git
$actualBranch = (& $git.Source -C $repoRoot rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
$branchReadExitCode = $LASTEXITCODE
$detachedHead = $actualBranch -eq 'HEAD'
if ($branchReadExitCode -ne 0 -or (-not $detachedHead -and $actualBranch -ne $expectedBranch)) {
  throw "HEIGHT_DIFFERENCE_2_WRONG_ACTIVE_BRANCH=$actualBranch"
}
$actualCommit = (& $git.Source -C $repoRoot rev-parse HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $actualCommit -notmatch '^[0-9a-f]{40}$') {
  throw "HEIGHT_DIFFERENCE_2_INVALID_ACTIVE_COMMIT=$actualCommit"
}

$canonicalBlob = Assert-GitBlob $repoRoot $canonicalRel $expectedCanonicalBlob 'HEIGHT_DIFFERENCE_2_CANONICAL_SECURITY_SOURCE'
$pointEvidenceBlob = Assert-GitBlob $repoRoot $pointEvidenceRel $expectedPointEvidenceBlob 'HEIGHT_DIFFERENCE_2_POINT_EVIDENCE'
$hmlrEvidenceBlob = Assert-GitBlob $repoRoot $hmlrEvidenceRel $expectedHmlrEvidenceBlob 'HEIGHT_DIFFERENCE_2_HMLR_EVIDENCE'
$extractorBlob = Assert-GitBlob $repoRoot $extractorRel $expectedExtractorBlob 'HEIGHT_DIFFERENCE_2_RECONCILED_EXTRACTOR'
$hmlrRecoveryBlob = Assert-GitBlob $repoRoot $hmlrRecoveryRel $expectedHmlrRecoveryBlob 'HEIGHT_DIFFERENCE_2_HMLR_RECOVERY'
$entryBlob = Assert-GitBlob $repoRoot $entryRel $expectedEntryBlob 'HEIGHT_DIFFERENCE_2_RECONCILED_ENTRYPOINT'

if ([string]$env:AAYS_TARGET_BRANCH -and [string]$env:AAYS_TARGET_BRANCH -ne $expectedBranch) { throw 'HEIGHT_DIFFERENCE_2_TARGET_BRANCH_ENV_MISMATCH' }
if ([string]$env:AAYS_PAGE_KEY -and [string]$env:AAYS_PAGE_KEY -ne $expectedPageKey) { throw 'HEIGHT_DIFFERENCE_2_PAGE_KEY_ENV_MISMATCH' }
if ([string]$env:AAYS_TASK_ID -and [string]$env:AAYS_TASK_ID -ne $taskId) { throw 'HEIGHT_DIFFERENCE_2_TASK_ID_ENV_MISMATCH' }
if ([string]$env:AAYS_ATTEMPT_ID -and [string]$env:AAYS_ATTEMPT_ID -ne $attemptId) { throw 'HEIGHT_DIFFERENCE_2_ATTEMPT_ID_ENV_MISMATCH' }

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

$entrypoint = Join-Path $repoRoot $entryRel
$env:AAYS_REPO_ROOT = $repoRoot
$env:AAYS_TARGET_BRANCH = $expectedBranch
$env:AAYS_PAGE_KEY = $expectedPageKey
$env:AAYS_TASK_ID = $taskId
$env:AAYS_ATTEMPT_ID = $attemptId
$env:AAYS_HEIGHT_DIFFERENCE_2_EXPECTED_WEB_ROWS = [string]$expectedWebRows

Write-Output 'SLOT_ID=height_difference_2'
Write-Output "TASK_VERSION=$taskVersion"
Write-Output "PICKUP_REQUEST_REVISION=$pickupRequestRevision"
Write-Output "TASK_ID=$taskId"
Write-Output "ATTEMPT_ID=$attemptId"
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "ACTIVE_BRANCH=$actualBranch"
Write-Output "DETACHED_HEAD=$($detachedHead.ToString().ToLowerInvariant())"
Write-Output "ACTIVE_COMMIT=$actualCommit"
Write-Output "CANONICAL_SECURITY_BLOB_SHA=$canonicalBlob"
Write-Output "POINT_EVIDENCE_BLOB_SHA=$pointEvidenceBlob"
Write-Output "HMLR_EVIDENCE_BLOB_SHA=$hmlrEvidenceBlob"
Write-Output "RECONCILED_EXTRACTOR_BLOB_SHA=$extractorBlob"
Write-Output "HMLR_RECOVERY_BLOB_SHA=$hmlrRecoveryBlob"
Write-Output "RECONCILED_ENTRYPOINT_BLOB_SHA=$entryBlob"
Write-Output 'CANONICAL_FEATURE_COUNT=92283'
Write-Output 'EXACT_TARGET_ROWS=30762,46142,61522'
Write-Output 'FRESH_HMLR_GML_REVALIDATION=true'
Write-Output 'EXACT_HMLR_ID_AND_POINT_INSIDE=true'
Write-Output 'NEAREST_ROW_FALLBACK=false'
Write-Output 'NEAREST_POLYGON_FILL=false'
Write-Output "EXPECTED_WEB_OPERATION_ROWS=$expectedWebRows"
Write-Output "PYTHON_SCRIPT=$entrypoint"

if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
  & $python.Source -3 $entrypoint
} else {
  & $python.Source $entrypoint
}
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 1 }
Write-Output "PYTHON_EXIT_CODE=$exitCode"
Write-Output 'FINAL_READY=false'
exit $exitCode

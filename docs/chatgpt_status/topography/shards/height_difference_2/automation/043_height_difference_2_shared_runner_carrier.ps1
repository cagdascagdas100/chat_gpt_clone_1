[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$attemptId = 'height-difference-2-20260721-020'
$taskVersion = '6.4-terrain50-accuracy-screening-web-integrity'
$pickupRequestRevision = 12
$expectedBranch = 'codex/aays-single-runner-v5-20260706'
$expectedPageKey = 'aays1'
$expectedCanonicalBlob = 'bb48164e7a0af78df875f30421a6a3068c43edb8'
$expectedPointEvidenceBlob = '9c2932bf101b0f14740d9fe9a201067b2e5a5aad'
$expectedHmlrEvidenceBlob = 'bb8924be924303833949857c8a0e32296fc8092b'
$expectedExtractorBlob = '63363c56d1cfc7678a07f52b59375cccc5dd9bcf'
$expectedHmlrRecoveryBlob = '0846876dadd5639931c12d3099c36ce8999515fd'
$expectedEntryBlob = '842ec93f6218025d583ee720cd56bce6ef2fb462'
$expectedTerrainResolverBlob = '90e87710cba7a63df01ab058b335d5bc570dc9f6'
$expectedTerrainCrosscheckerBlob = '9f4a652392017c74c5dd2f8cec899e114ccdc2d6'
$expectedTerrainWrapperBlob = '8ce81728c2eca74f8b14f3b3675c09ec393e06a5'
$expectedWebRows = 1036
$entryRel = 'docs\chatgpt_status\aays1\automation\height_difference_2_reconciled_candidate_then_sampling_entry.py'
$extractorRel = 'docs\chatgpt_status\topography\shards\height_difference_2\automation\043_extract_reconciled_exact_candidates.py'
$hmlrRecoveryRel = 'docs\chatgpt_status\topography\shards\height_difference_2\automation\043_prepare_hmlr_sources_and_match.py'
$terrainResolverRel = 'docs\chatgpt_status\topography\shards\height_difference_2\automation\015_resolve_os_terrain50_downloads.py'
$terrainCrosscheckerRel = 'docs\chatgpt_status\topography\shards\height_difference_2\automation\013_crosscheck_os_terrain50.py'
$terrainWrapperRel = 'docs\chatgpt_status\topography\shards\height_difference_2\automation\016_prepare_and_crosscheck_os_terrain50.py'
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
if ($LASTEXITCODE -ne 0 -or $actualBranch -ne $expectedBranch) { throw "HEIGHT_DIFFERENCE_2_WRONG_ACTIVE_BRANCH=$actualBranch" }

$canonicalBlob = Assert-GitBlob $repoRoot $canonicalRel $expectedCanonicalBlob 'HEIGHT_DIFFERENCE_2_CANONICAL_SECURITY_SOURCE'
$pointEvidenceBlob = Assert-GitBlob $repoRoot $pointEvidenceRel $expectedPointEvidenceBlob 'HEIGHT_DIFFERENCE_2_POINT_EVIDENCE'
$hmlrEvidenceBlob = Assert-GitBlob $repoRoot $hmlrEvidenceRel $expectedHmlrEvidenceBlob 'HEIGHT_DIFFERENCE_2_HMLR_EVIDENCE'
$extractorBlob = Assert-GitBlob $repoRoot $extractorRel $expectedExtractorBlob 'HEIGHT_DIFFERENCE_2_RECONCILED_EXTRACTOR'
$hmlrRecoveryBlob = Assert-GitBlob $repoRoot $hmlrRecoveryRel $expectedHmlrRecoveryBlob 'HEIGHT_DIFFERENCE_2_HMLR_RECOVERY'
$terrainResolverBlob = Assert-GitBlob $repoRoot $terrainResolverRel $expectedTerrainResolverBlob 'HEIGHT_DIFFERENCE_2_TERRAIN50_RESOLVER'
$terrainCrosscheckerBlob = Assert-GitBlob $repoRoot $terrainCrosscheckerRel $expectedTerrainCrosscheckerBlob 'HEIGHT_DIFFERENCE_2_TERRAIN50_CROSSCHECKER'
$terrainWrapperBlob = Assert-GitBlob $repoRoot $terrainWrapperRel $expectedTerrainWrapperBlob 'HEIGHT_DIFFERENCE_2_TERRAIN50_WRAPPER'
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
Write-Output "CANONICAL_SECURITY_BLOB_SHA=$canonicalBlob"
Write-Output "POINT_EVIDENCE_BLOB_SHA=$pointEvidenceBlob"
Write-Output "HMLR_EVIDENCE_BLOB_SHA=$hmlrEvidenceBlob"
Write-Output "RECONCILED_EXTRACTOR_BLOB_SHA=$extractorBlob"
Write-Output "HMLR_RECOVERY_BLOB_SHA=$hmlrRecoveryBlob"
Write-Output "TERRAIN50_RESOLVER_BLOB_SHA=$terrainResolverBlob"
Write-Output "TERRAIN50_CROSSCHECKER_BLOB_SHA=$terrainCrosscheckerBlob"
Write-Output "TERRAIN50_WRAPPER_BLOB_SHA=$terrainWrapperBlob"
Write-Output "RECONCILED_ENTRYPOINT_BLOB_SHA=$entryBlob"
Write-Output 'CANONICAL_FEATURE_COUNT=92283'
Write-Output 'EXACT_TARGET_ROWS=30762,46142,61522'
Write-Output 'FRESH_HMLR_GML_REVALIDATION=true'
Write-Output 'EXACT_HMLR_ID_AND_POINT_INSIDE=true'
Write-Output 'NEAREST_ROW_FALLBACK=false'
Write-Output 'NEAREST_POLYGON_FILL=false'
Write-Output 'TERRAIN50_OS_GRID_RMSE_M=4.0'
Write-Output 'EA_DTM1M_RMSE_M=0.15'
Write-Output 'TERRAIN50_CONSERVATIVE_ONE_RMSE_SUM_M=4.15'
Write-Output 'TERRAIN50_CONSERVATIVE_TWO_RMSE_SUM_M=8.30'
Write-Output 'TERRAIN50_TWO_RMSE_SCREENING_IS_NOT_CONFIDENCE_INTERVAL=true'
Write-Output 'PORT_8012_ACCEPTANCE_REQUIRED=true'
Write-Output 'PORT_8012_CURRENT_CANDIDATE_SHA256_REQUIRED=true'
Write-Output 'PORT_8012_OPERATION_FILE_PATH_GUARD_REQUIRED=true'
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

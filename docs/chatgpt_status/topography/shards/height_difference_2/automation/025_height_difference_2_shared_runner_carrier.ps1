[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$attemptId = 'height-difference-2-20260721-020'
$expectedBranch = 'codex/aays-single-runner-v5-20260706'
$expectedPageKey = 'aays1'
$expectedCanonicalBlob = 'ca95400a5644f77a79cbaf47b2c2d611d3777a55'
$expectedExtractorBlob = 'a7e220421523d3f77012440d9303658b0142a715'
$expectedWebRows = 365
$entryRel = 'docs\chatgpt_status\aays1\automation\height_difference_2_candidate_then_sampling_entry.py'
$extractorRel = 'docs\chatgpt_status\topography\shards\height_difference_2\automation\007_extract_three_canonical_candidates.py'
$canonicalRel = 'england_map_web\data\program_layer_matrix\topography.geojson'

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

$repoRoot = Resolve-RepoRoot
$entrypoint = Join-Path $repoRoot $entryRel
$extractor = Join-Path $repoRoot $extractorRel
$canonical = Join-Path $repoRoot $canonicalRel
if (-not (Test-Path -LiteralPath $canonical -PathType Leaf)) { throw 'HEIGHT_DIFFERENCE_2_CANONICAL_SOURCE_MISSING' }
if (-not (Test-Path -LiteralPath $extractor -PathType Leaf)) { throw 'HEIGHT_DIFFERENCE_2_EXACT_ROW_EXTRACTOR_MISSING' }

$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$actualBranch = (& $git.Source -C $repoRoot rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $actualBranch -ne $expectedBranch) {
  throw "HEIGHT_DIFFERENCE_2_WRONG_ACTIVE_BRANCH=$actualBranch"
}
$canonicalBlob = (& $git.Source -C $repoRoot hash-object -- $canonical 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $canonicalBlob -ne $expectedCanonicalBlob) {
  throw "HEIGHT_DIFFERENCE_2_CANONICAL_BLOB_MISMATCH=$canonicalBlob"
}
$extractorBlob = (& $git.Source -C $repoRoot hash-object -- $extractor 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $extractorBlob -ne $expectedExtractorBlob) {
  throw "HEIGHT_DIFFERENCE_2_EXACT_ROW_EXTRACTOR_BLOB_MISMATCH=$extractorBlob"
}

if ([string]$env:AAYS_TARGET_BRANCH -and [string]$env:AAYS_TARGET_BRANCH -ne $expectedBranch) { throw 'HEIGHT_DIFFERENCE_2_TARGET_BRANCH_ENV_MISMATCH' }
if ([string]$env:AAYS_PAGE_KEY -and [string]$env:AAYS_PAGE_KEY -ne $expectedPageKey) { throw 'HEIGHT_DIFFERENCE_2_PAGE_KEY_ENV_MISMATCH' }
if ([string]$env:AAYS_TASK_ID -and [string]$env:AAYS_TASK_ID -ne $taskId) { throw 'HEIGHT_DIFFERENCE_2_TASK_ID_ENV_MISMATCH' }

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

$env:AAYS_REPO_ROOT = $repoRoot
$env:AAYS_TARGET_BRANCH = $expectedBranch
$env:AAYS_PAGE_KEY = $expectedPageKey
$env:AAYS_TASK_ID = $taskId
$env:AAYS_ATTEMPT_ID = $attemptId
$env:AAYS_HEIGHT_DIFFERENCE_2_EXPECTED_WEB_ROWS = [string]$expectedWebRows

Write-Output 'SLOT_ID=height_difference_2'
Write-Output 'TASK_VERSION=5.8-binary-exact-target-stream'
Write-Output "TASK_ID=$taskId"
Write-Output "ATTEMPT_ID=$attemptId"
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "ACTIVE_BRANCH=$actualBranch"
Write-Output "CANONICAL_BLOB_SHA=$canonicalBlob"
Write-Output "EXACT_ROW_EXTRACTOR_BLOB_SHA=$extractorBlob"
Write-Output 'EXACT_TARGET_ROWS=30762,46142,61522'
Write-Output 'BINARY_FEATURE_STREAM=true'
Write-Output 'FULL_JSON_LOAD=false'
Write-Output 'SHA256_SAME_PASS=true'
Write-Output 'SCAN_THROUGH_FEATURES_ARRAY_END=true'
Write-Output 'NEAREST_ROW_FALLBACK=false'
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

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)][string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [Parameter(Mandatory=$false)][string]$PythonExe = $env:AAYS_PYTHON_EXE,
  [Parameter(Mandatory=$false)][string]$GitExe = $env:AAYS_GIT_EXE,
  [int]$Timeout = 120
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..\..')).Path
}
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd('\')
if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { throw 'AAYS_REPO_ROOT_NOT_FOUND' }
if ($Timeout -lt 1 -or $Timeout -gt 900) { throw 'TIMEOUT_OUT_OF_RANGE' }
if ([string]::IsNullOrWhiteSpace($PythonExe)) { $PythonExe = 'python' }
if ([string]::IsNullOrWhiteSpace($GitExe)) { $GitExe = 'git' }
$pythonCmd = Get-Command $PythonExe -ErrorAction Stop | Select-Object -First 1
$gitCmd = Get-Command $GitExe -ErrorAction Stop | Select-Object -First 1
$PythonExe = $pythonCmd.Source
$GitExe = $gitCmd.Source
& $PythonExe --version | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'PYTHON_EXECUTABLE_FAILED' }
& $GitExe --version | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'GIT_EXECUTABLE_FAILED' }

$entryRel = 'docs/chatgpt_status/topography/shards/height_difference_3/automation/028_execute_batch116_strict_proj_and_four_candidate_chain.py'
$candidateRel = 'docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/059_candidate_manifest_61536_61539_batch_115.json'
$outputRel = 'docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/012_strict_four_candidate_full_chain_batch_116'
$entry = Join-Path $RepoRoot ($entryRel -replace '/', '\')
$candidates = Join-Path $RepoRoot ($candidateRel -replace '/', '\')
$outputDir = Join-Path $RepoRoot ($outputRel -replace '/', '\')

$pins = [ordered]@{
  'docs/chatgpt_status/topography/shards/height_difference_3/automation/008_match_hmlr_inspire_gml.py' = '5240a20ea0d65fa99af845d15e8219daf1287cf2'
  'docs/chatgpt_status/topography/shards/height_difference_3/automation/009_sample_ea_dtm_and_os_terrain50.py' = '42ac87801263b6b94532c0897dbb5211b79ebeb1'
  'docs/chatgpt_status/topography/shards/height_difference_3/automation/010_publish_verified_height_difference_examples.py' = 'c24bb9e54244a527a560fd85b3eb74e6872d72a7'
  'docs/chatgpt_status/topography/shards/height_difference_3/automation/012_download_hmlr_inspire_sources.py' = 'f89aea9d3e89a3037194129498b281e380a92c0f'
  'docs/chatgpt_status/topography/shards/height_difference_3/automation/013_fetch_ea_dtm_wcs_for_matches.py' = '53c7371701f4f3495a4712b472a3a45f1f4fed12'
  'docs/chatgpt_status/topography/shards/height_difference_3/automation/014_prepare_os_terrain50_tiles.py' = '73fd2a95dd6941c30ef8d3eb36e40b7f5c32e2b9'
  'docs/chatgpt_status/topography/shards/height_difference_3/automation/021_download_os_terrain50_via_api.py' = '3dc2030c4f9dd8aa107a08121fc2c01803b2dee2'
  'docs/chatgpt_status/topography/shards/height_difference_3/automation/025_execute_batch115_hmlr_probe_and_exact_boundary_match.py' = 'b217c0665a25fcb85a2106ec1d1cf30c48b57388'
  'docs/chatgpt_status/topography/shards/height_difference_3/automation/026_execute_batch116_four_candidate_full_chain.py' = '9cb46a59b2e14e691fdab4dddc9d4d11a1748f75'
  'docs/chatgpt_status/topography/shards/height_difference_3/automation/027_verify_batch116_proj_ostn15_gate.py' = 'e5c8e0c78904695fe25683e6ca479fa6fb06a0ea'
  $entryRel = '8eb0033d3393e902e4ab833805e8213609da716b'
  $candidateRel = '8d8f3186dd530187849b1bc8b545b77fed9076c6'
}
foreach ($pair in $pins.GetEnumerator()) {
  $path = Join-Path $RepoRoot ($pair.Key -replace '/', '\')
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('REQUIRED_FILE_MISSING:' + $pair.Key) }
  $actual = (& $GitExe -C $RepoRoot hash-object --no-filters -- $path).Trim().ToLowerInvariant()
  if ($LASTEXITCODE -ne 0 -or $actual -ne $pair.Value) {
    throw ('TRACKED_BLOB_MISMATCH:' + $pair.Key + ':expected=' + $pair.Value + ':actual=' + $actual)
  }
}
$dirty = (& $GitExe -C $RepoRoot status --porcelain --untracked-files=no -- @($pins.Keys))
if ($LASTEXITCODE -ne 0) { throw 'CRITICAL_PATH_STATUS_FAILED' }
if (-not [string]::IsNullOrWhiteSpace(($dirty -join "`n"))) { throw ('CRITICAL_PATHS_DIRTY:' + ($dirty -join ';')) }

$candidateShaBefore = (Get-FileHash -Algorithm SHA256 -LiteralPath $candidates).Hash.ToLowerInvariant()
& $PythonExe $entry --candidate-manifest $candidates --output-dir $outputDir --timeout ([string]$Timeout)
$code = $LASTEXITCODE
if ($code -ne 0) { throw ('STRICT_FOUR_CANDIDATE_CHAIN_FAILED:' + $code) }
$candidateShaAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $candidates).Hash.ToLowerInvariant()
if ($candidateShaAfter -ne $candidateShaBefore) { throw 'CANDIDATE_MANIFEST_CHANGED_DURING_CHAIN' }

$executionPath = Join-Path $outputDir 'batch116_strict_execution.json'
if (-not (Test-Path -LiteralPath $executionPath -PathType Leaf)) { throw 'STRICT_EXECUTION_MANIFEST_MISSING' }
$execution = Get-Content -Raw -LiteralPath $executionPath | ConvertFrom-Json
$expectedRows = @(61536,61537,61538,61539)
$actualRows = @($execution.expected_rows | ForEach-Object { [int]$_ })
if ([int]$execution.schema_version -lt 3) { throw 'STRICT_EXECUTION_SCHEMA_TOO_OLD' }
if ([string]$execution.status -ne 'FOUR_HARDENED_CANDIDATES_CANDIDATE_AWARE_PROJ_OFFICIAL_SAME_POINT_MEASURED_AND_PUBLISHED') { throw 'STRICT_EXECUTION_STATUS_MISMATCH' }
if ([string]$execution.candidate_manifest_sha256 -ne $candidateShaBefore) { throw 'STRICT_EXECUTION_CANDIDATE_SHA_MISMATCH' }
if (($actualRows -join ',') -ne ($expectedRows -join ',')) { throw 'STRICT_EXECUTION_ROWS_MISMATCH' }
if (-not [bool]$execution.candidate_aware_proj_gate) { throw 'CANDIDATE_AWARE_PROJ_GATE_MISSING' }
if (-not [bool]$execution.same_point_crosscheck_required) { throw 'SAME_POINT_CROSSCHECK_GATE_MISSING' }
if (-not [bool]$execution.source_errors_forbid_promotion) { throw 'SOURCE_ERROR_PROMOTION_GATE_MISSING' }
if (-not [bool]$execution.transactional_output_tree) { throw 'TRANSACTIONAL_OUTPUT_TREE_MISSING' }
if (-not [bool]$execution.previous_valid_output_tree_preserved_on_failure) { throw 'OUTPUT_TREE_ROLLBACK_GATE_MISSING' }
if (-not [bool]$execution.numeric_publish_allowed) { throw 'NUMERIC_PUBLISH_GATE_NOT_PASSED' }
if ([bool]$execution.final_ready) { throw 'FINAL_READY_MUST_REMAIN_FALSE' }
if ([bool]$execution.fake_data) { throw 'FAKE_DATA_FLAG_MUST_REMAIN_FALSE' }

$hashPaths = [ordered]@{
  proj_gate_sha256 = '00_proj_ostn15_gate.json'
  four_candidate_execution_sha256 = '01_four_candidate_chain/batch116_four_candidate_execution.json'
  verified_json_sha256 = '01_four_candidate_chain/05_verified_examples.json'
  verified_geojson_sha256 = '01_four_candidate_chain/05_verified_examples.geojson'
}
foreach ($pair in $hashPaths.GetEnumerator()) {
  $path = Join-Path $outputDir ($pair.Value -replace '/', '\')
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('STRICT_OUTPUT_MISSING:' + $pair.Value) }
  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
  $expected = ([string]$execution.output_hashes.($pair.Key)).ToLowerInvariant()
  if ($actual -ne $expected) { throw ('STRICT_OUTPUT_SHA_MISMATCH:' + $pair.Value) }
}

Write-Output (([ordered]@{
  ok = $true
  status = [string]$execution.status
  candidate_manifest_sha256 = $candidateShaBefore
  validated_dependency_blob_count = $pins.Count
  verified_output_hash_count = $hashPaths.Count
  output_dir = $outputDir
  single_shared_runner_only = $true
  new_runner = $false
  parallel_runner = $false
  final_ready = $false
}) | ConvertTo-Json -Compress)
exit 0

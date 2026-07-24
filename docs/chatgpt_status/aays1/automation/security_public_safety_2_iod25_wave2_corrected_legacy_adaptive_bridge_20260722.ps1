[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$expectedBranch = 'codex/aays-single-runner-v5-20260706'
$pythonScriptRel = 'docs/chatgpt_status/aays1/automation/security_public_safety_2_iod25_relative_method_wave2_corrected_wrapper_20260722.py'
$expectedPythonBlob = '9de3f2015604407dcf114ec119d48756bc4a13e6'
$dependencyRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json'

if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne $slotId) { throw "WRONG_SLOT=$($env:AAYS_SLOT_ID)" }
if ($env:AAYS_TARGET_BRANCH -and $env:AAYS_TARGET_BRANCH -ne $expectedBranch) { throw "WRONG_TARGET_BRANCH=$($env:AAYS_TARGET_BRANCH)" }
if ($env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN -and $env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN.ToLowerInvariant() -ne 'true') { throw 'DIRECT_PUSH_GUARD_MISSING' }

$repoRoot = [System.IO.Path]::GetFullPath((Get-Location).Path).TrimEnd('\')
$dependency = Join-Path $repoRoot ($dependencyRel -replace '/', '\')
if (-not (Test-Path -LiteralPath $dependency -PathType Leaf)) { throw "WAVE1_DEPENDENCY_MISSING=$dependencyRel" }
try { $wave1 = Get-Content -LiteralPath $dependency -Raw -Encoding UTF8 | ConvertFrom-Json } catch { throw "WAVE1_DEPENDENCY_INVALID_JSON=$($_.Exception.Message)" }
$rows = @($wave1.rows)
if ($rows.Count -ne 12) { throw "WAVE1_DEPENDENCY_ROW_COUNT=$($rows.Count)" }
$expectedIds = @(30762..30773 | ForEach-Object { "parcel_$_" })
$actualIds = @($rows | ForEach-Object { [string]$_.parcel_id })
if (@($actualIds | Sort-Object -Unique).Count -ne 12) { throw 'WAVE1_DEPENDENCY_DUPLICATE_PARCEL_IDS' }
if (@(Compare-Object ($expectedIds | Sort-Object) ($actualIds | Sort-Object)).Count -ne 0) { throw 'WAVE1_DEPENDENCY_TARGET_IDS_MISMATCH' }
if (-not $wave1.canonical_point_source.git_blob_matches_expected) { throw 'WAVE1_CANONICAL_POINT_BLOB_GATE_FAILED' }
if ([int]$wave1.canonical_point_source.actual_feature_count -ne 92283) { throw 'WAVE1_CANONICAL_FEATURE_COUNT_GATE_FAILED' }
if ([int]$wave1.ons_single_match_rows -ne 12) { throw 'WAVE1_ONS_SINGLE_MATCH_GATE_FAILED' }
if ([int]$wave1.police_hashed_rows -ne 12) { throw 'WAVE1_POLICE_HASH_GATE_FAILED' }

$pythonScript = Join-Path $repoRoot ($pythonScriptRel -replace '/', '\')
if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) { throw "PYTHON_ENTRY_MISSING=$pythonScript" }
$actualPythonBlob = (& git -C $repoRoot hash-object -- $pythonScript 2>$null | Select-Object -First 1)
if (-not $actualPythonBlob) { throw 'PYTHON_ENTRY_BLOB_HASH_FAILED' }
$actualPythonBlob = ([string]$actualPythonBlob).Trim()
if ($actualPythonBlob -ne $expectedPythonBlob) { throw "PYTHON_ENTRY_BLOB_MISMATCH=$actualPythonBlob EXPECTED=$expectedPythonBlob" }

$portableRoot = [string]$env:AAYS_PORTABLE_ROOT
if ([string]::IsNullOrWhiteSpace($portableRoot)) {
  $cursor = $repoRoot
  while ($cursor) {
    if ((Split-Path -Leaf $cursor) -eq 'runner_system') { $portableRoot = Split-Path -Parent $cursor; break }
    $parent = Split-Path -Parent $cursor
    if (-not $parent -or $parent -eq $cursor) { break }
    $cursor = $parent
  }
}
$pythonCandidates = New-Object System.Collections.Generic.List[string]
if (-not [string]::IsNullOrWhiteSpace($portableRoot)) {
  [void]$pythonCandidates.Add((Join-Path $portableRoot 'runtime\python312\python.exe'))
  [void]$pythonCandidates.Add((Join-Path $portableRoot 'runtime\python311\python.exe'))
  [void]$pythonCandidates.Add((Join-Path $portableRoot 'runtime\python\python.exe'))
}
[void]$pythonCandidates.Add((Join-Path $repoRoot '.venv\Scripts\python.exe'))
$command = Get-Command python.exe -ErrorAction SilentlyContinue
if ($command) { [void]$pythonCandidates.Add([string]$command.Source) }
$command = Get-Command python -ErrorAction SilentlyContinue
if ($command) { [void]$pythonCandidates.Add([string]$command.Source) }
$python = $pythonCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -Unique | Select-Object -First 1
if (-not $python) { throw "PORTABLE_OR_PATH_PYTHON_NOT_AVAILABLE ROOT=$portableRoot" }

$env:AAYS_SLOT_ID = $slotId
$env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN = 'true'
& $python $pythonScript
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) { throw "PYTHON_ENTRY_EXIT_NONZERO=$exitCode" }
exit 0

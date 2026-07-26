[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$expectedBranch = 'codex/aays-single-runner-v5-20260706'
$pythonScriptRel = 'docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_candidate_join_20260723.py'
$expectedPythonBlob = '3e9a4d57754e13d68429cedfb0a0b271fda822eb'

if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne $slotId) {
  throw "WRONG_SLOT=$($env:AAYS_SLOT_ID)"
}
if ($env:AAYS_TARGET_BRANCH -and $env:AAYS_TARGET_BRANCH -ne $expectedBranch) {
  throw "WRONG_TARGET_BRANCH=$($env:AAYS_TARGET_BRANCH)"
}
if ($env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN -and $env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN.ToLowerInvariant() -ne 'true') {
  throw 'DIRECT_PUSH_GUARD_MISSING'
}

$repoRoot = [System.IO.Path]::GetFullPath((Get-Location).Path).TrimEnd('\')
$pythonScript = Join-Path $repoRoot ($pythonScriptRel -replace '/', '\')
if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) {
  throw "PYTHON_ENTRY_MISSING=$pythonScript"
}
$actualPythonBlob = (& git -C $repoRoot hash-object -- $pythonScript 2>$null | Select-Object -First 1)
if (-not $actualPythonBlob) { throw 'PYTHON_ENTRY_BLOB_HASH_FAILED' }
$actualPythonBlob = ([string]$actualPythonBlob).Trim()
if ($actualPythonBlob -ne $expectedPythonBlob) {
  throw "PYTHON_ENTRY_BLOB_MISMATCH=$actualPythonBlob EXPECTED=$expectedPythonBlob"
}

$portableRoot = [string]$env:AAYS_PORTABLE_ROOT
if ([string]::IsNullOrWhiteSpace($portableRoot)) {
  $cursor = $repoRoot
  while ($cursor) {
    if ((Split-Path -Leaf $cursor) -eq 'runner_system') {
      $portableRoot = Split-Path -Parent $cursor
      break
    }
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

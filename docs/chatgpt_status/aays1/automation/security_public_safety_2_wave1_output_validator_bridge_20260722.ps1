[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$branch = 'codex/aays-single-runner-v5-20260706'
$inputRel = 'docs/chatgpt_status/aays1/shards/security_public_safety_2/geometry_lsoa_police_sample_wave1_latest.json'
$scriptRel = 'docs/chatgpt_status/aays1/automation/security_public_safety_2_wave1_output_validator_20260722.py'
$expectedScriptBlob = '4f7c5a87b91af3c7912b30882efcd55244bbf01e'

if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne $slotId) { throw "WRONG_SLOT=$($env:AAYS_SLOT_ID)" }
if ($env:AAYS_TARGET_BRANCH -and $env:AAYS_TARGET_BRANCH -ne $branch) { throw "WRONG_TARGET_BRANCH=$($env:AAYS_TARGET_BRANCH)" }
if ($env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN -and $env:AAYS_CHILD_DIRECT_PUSH_FORBIDDEN.ToLowerInvariant() -ne 'true') { throw 'DIRECT_PUSH_GUARD_MISSING' }

$repoRoot = [System.IO.Path]::GetFullPath((Get-Location).Path).TrimEnd('\')
$inputPath = Join-Path $repoRoot ($inputRel -replace '/', '\')
if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) { throw "WAVE1_OUTPUT_DEPENDENCY_MISSING=$inputRel" }

$scriptPath = Join-Path $repoRoot ($scriptRel -replace '/', '\')
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) { throw "VALIDATOR_SCRIPT_MISSING=$scriptRel" }
$actualBlob = (& git -C $repoRoot hash-object -- $scriptPath 2>$null | Select-Object -First 1)
if (-not $actualBlob) { throw 'VALIDATOR_SCRIPT_BLOB_HASH_FAILED' }
$actualBlob = ([string]$actualBlob).Trim()
if ($actualBlob -ne $expectedScriptBlob) { throw "VALIDATOR_SCRIPT_BLOB_MISMATCH=$actualBlob EXPECTED=$expectedScriptBlob" }

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
& $python $scriptPath
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) { throw "WAVE1_VALIDATOR_EXIT_NONZERO=$exitCode" }
exit 0

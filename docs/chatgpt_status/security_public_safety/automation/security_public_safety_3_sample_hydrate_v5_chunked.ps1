[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) {
  [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
}
$pythonScript = Join-Path $repoRoot 'docs\chatgpt_status\security_public_safety\automation\security_public_safety_3_sample_hydrate_v5_chunked.py'
if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) {
  throw "V5_PYTHON_SCRIPT_MISSING: $pythonScript"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

Write-Output 'SLOT_ID=security_public_safety_3'
Write-Output 'TASK_VERSION=5.1-powershell-carrier'
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "PYTHON_SCRIPT=$pythonScript"

if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
  & $python.Source -3 $pythonScript
} else {
  & $python.Source $pythonScript
}
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 1 }
Write-Output "PYTHON_EXIT_CODE=$exitCode"
Write-Output 'FINAL_READY=false'
exit $exitCode

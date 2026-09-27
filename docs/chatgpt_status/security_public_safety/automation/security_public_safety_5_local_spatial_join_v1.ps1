[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) { [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT) } else { [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..')) }
$pythonScript = Join-Path $repoRoot 'docs\chatgpt_status\security_public_safety\automation\security_public_safety_5_local_spatial_join_v1.py'
if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) { throw "SPS5_JOIN_PYTHON_SCRIPT_MISSING: $pythonScript" }
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }
Write-Output 'SLOT_ID=security_public_safety_5'
Write-Output 'LINEAGE_ID=86b5e932de484ad26133fa8c'
Write-Output 'PARTITION=61524-76903'
Write-Output 'SECOND_RUNNER=false'
Write-Output "REPO_ROOT=$repoRoot"
if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') { & $python.Source -3 $pythonScript } else { & $python.Source $pythonScript }
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 1 }
Write-Output "PYTHON_EXIT_CODE=$exitCode"
Write-Output 'FINAL_READY=false'
exit $exitCode

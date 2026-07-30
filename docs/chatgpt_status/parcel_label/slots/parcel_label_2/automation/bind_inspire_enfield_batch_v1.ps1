[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) { [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT) } else { [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\..\..')) }
$pythonScript = Join-Path $repoRoot 'docs\chatgpt_status\parcel_label\slots\parcel_label_2\automation\bind_inspire_enfield_batch_v9.py'
if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) { throw "PARCEL_LABEL_2_INSPIRE_PYTHON_SCRIPT_MISSING: $pythonScript" }
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }
Write-Output 'SLOT_ID=parcel_label_2'
Write-Output 'TASK_VERSION=6.8-namespace-and-polygon-topology-strict-batch'
Write-Output 'CONTINUATION_KEY=c07f950559681f35d0a482491539c1f50400878e0a0b33f9ae3e733574346ce6'
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "PYTHON_SCRIPT=$pythonScript"
if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') { & $python.Source -3 $pythonScript } else { & $python.Source $pythonScript }
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 1 }
Write-Output "PYTHON_EXIT_CODE=$exitCode"
Write-Output 'FINAL_READY=false'
exit $exitCode

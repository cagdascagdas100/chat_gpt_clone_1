[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) {
  [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..'))
}
$pythonRepoPath = 'docs/chatgpt_status/parcel_label/automation/parcel_label_3_exact_points_and_historical_audit_v1.py'
$pythonScript = Join-Path $repoRoot ($pythonRepoPath -replace '/', '\')
$tempScript = $null

if (-not (Test-Path -LiteralPath $pythonScript -PathType Leaf)) {
  $git = Get-Command git -ErrorAction SilentlyContinue
  if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND_FOR_PYTHON_FALLBACK' }
  $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'aays_parcel_label_slot3'
  New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
  $tempScript = Join-Path $tempRoot 'parcel_label_3_exact_points_and_historical_audit_v1.py'
  $resolved = $false
  foreach ($ref in @('origin/main','main')) {
    & $git.Source -C $repoRoot show "$ref`:$pythonRepoPath" 2>$null | Set-Content -LiteralPath $tempScript -Encoding UTF8
    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $tempScript -PathType Leaf) -and ((Get-Item -LiteralPath $tempScript).Length -gt 0)) {
      $pythonScript = $tempScript
      $resolved = $true
      break
    }
  }
  if (-not $resolved) { throw "PARCEL_LABEL_3_PYTHON_SCRIPT_MISSING: $pythonRepoPath" }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

Write-Output 'SLOT_ID=parcel_label_3'
Write-Output 'TASK_VERSION=1.1-powershell-carrier'
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "PYTHON_SCRIPT=$pythonScript"
Write-Output 'SECURITY_SCORE_FIELDS_ALLOWED=false'

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

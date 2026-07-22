[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-security-public-safety-1-canonical-acceptance-v17-20260722'
$attemptId = 'security-public-safety-1-20260722-017'
$expectedBranch = 'codex/aays-single-runner-v5-20260706'
$wrapperRel = 'docs\chatgpt_status\aays1\automation\security_public_safety_1_canonical_acceptance_v17_runner.py'

function Resolve-RepoRoot {
  $configured = [string]$env:AAYS_REPO_ROOT
  if ($configured) {
    try {
      $candidate = [System.IO.Path]::GetFullPath($configured)
      if (Test-Path -LiteralPath (Join-Path $candidate $wrapperRel) -PathType Leaf) { return $candidate }
    } catch {}
  }
  $cursor = [System.IO.DirectoryInfo](Get-Item -LiteralPath $PSScriptRoot)
  for ($i = 0; $i -lt 12 -and $null -ne $cursor; $i++) {
    if (Test-Path -LiteralPath (Join-Path $cursor.FullName $wrapperRel) -PathType Leaf) { return $cursor.FullName }
    $cursor = $cursor.Parent
  }
  throw 'SECURITY_PUBLIC_SAFETY_1_REPO_ROOT_NOT_RESOLVED'
}

$repoRoot = Resolve-RepoRoot
if ($repoRoot.StartsWith('C:\', [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "SECURITY_PUBLIC_SAFETY_1_NON_CANONICAL_C_ROOT=$repoRoot"
}
if ([string]$env:AAYS_TASK_ID -and [string]$env:AAYS_TASK_ID -ne $taskId) {
  throw 'SECURITY_PUBLIC_SAFETY_1_TASK_ID_ENV_MISMATCH'
}
if ([string]$env:AAYS_TARGET_BRANCH -and [string]$env:AAYS_TARGET_BRANCH -ne $expectedBranch) {
  throw 'SECURITY_PUBLIC_SAFETY_1_TARGET_BRANCH_ENV_MISMATCH'
}

$wrapper = Join-Path $repoRoot $wrapperRel
if (-not (Test-Path -LiteralPath $wrapper -PathType Leaf)) {
  throw 'SECURITY_PUBLIC_SAFETY_1_PYTHON_WRAPPER_MISSING'
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) { throw 'SECURITY_PUBLIC_SAFETY_1_PYTHON_EXECUTABLE_NOT_FOUND' }

$env:AAYS_REPO_ROOT = $repoRoot
$env:AAYS_TASK_ID = $taskId
$env:AAYS_ATTEMPT_ID = $attemptId
$env:AAYS_TARGET_BRANCH = $expectedBranch
$env:PYTHONDONTWRITEBYTECODE = '1'

Write-Output 'SLOT_ID=security_public_safety_1'
Write-Output "TASK_ID=$taskId"
Write-Output "ATTEMPT_ID=$attemptId"
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "PYTHON_WRAPPER=$wrapper"
Write-Output 'EXECUTION_HOST=POWERSHELL_CARRIER_TO_PYTHON'
Write-Output 'NEW_RUNNER=false'
Write-Output 'PARALLEL_RUNNER=false'
Write-Output 'FINAL_READY=false'

if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
  & $python.Source -3 $wrapper
} else {
  & $python.Source $wrapper
}
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 1 }
Write-Output "PYTHON_WRAPPER_EXIT_CODE=$exitCode"
exit $exitCode

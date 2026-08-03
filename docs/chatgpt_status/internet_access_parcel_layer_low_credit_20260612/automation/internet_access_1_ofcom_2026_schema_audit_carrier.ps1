[CmdletBinding()
param()

$ErrorActionPreference = 'Stop'
$taskId = 'internet_access_1_ofcom_2026_schema_audit_862285f2'
$continuationKey = '862285f27e6f91e2a293bddb06bd4ea65294d412d2f61c7a253d02cfae30be22'
$expectedBranch = 'codex/aays-single-runner-v5-20260706'
$runnerRel = 'docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\automation\internet_access_1_ofcom_2026_schema_audit_runner.py'
$implementationRel = 'docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\automation\internet_access_1_ofcom_2026_schema_audit.py'
$expectedRunnerBlob = '94c08118ca9ee80874878ebe08c01b2f26cd97dc'
$expectedImplementationBlob = '53bef982dc111a2587eaeae922f6de36e6473078'

function Resolve-RepoRoot {
  $configured = [string]$env:AAYS_REPO_ROOT
  if ($configured) {
    $candidate = [System.IO.Path]::GetFullPath($configured)
    if (Test-Path -LiteralPath (Join-Path $candidate $runnerRel) -PathType Leaf) { return $candidate }
  }
  $cursor = [System.IO.DirectoryInfo](Get-Item -LiteralPath $PSScriptRoot)
  for ($i = 0; $i -lt 12 -and $null -ne $cursor; $i++) {
    if (Test-Path -LiteralPath (Join-Path $cursor.FullName $runnerRel) -PathType Leaf) { return $cursor.FullName }
    $cursor = $cursor.Parent
  }
  throw 'INTERNET_ACCESS_1_REPO_ROOT_NOT_RESOLVED'
}

function Assert-GitBlob([string]$RepoRoot, [string]$RelativePath, [string]$ExpectedBlob, [string]$Label) {
  $path = Join-Path $RepoRoot $RelativePath
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "$Label`_MISSING=$path" }
  $actual = (& $script:git.Source -C $RepoRoot hash-object -- $path 2>&1 | Select-Object -Last 1).ToString().Trim()
  if ($LASTEXITCODE -ne 0 -or $actual -ne $ExpectedBlob) { throw "$Label`_BLOB_MISMATCH=$actual" }
  return $actual
}

$repoRoot = Resolve-RepoRoot
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$script:git = $git
$actualBranch = (& $git.Source -C $repoRoot rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $actualBranch -ne $expectedBranch) { throw "INTERNET_ACCESS_1_WRONG_ACTIVE_BRANCH=$actualBranch" }

$runnerBlob = Assert-GitBlob $repoRoot $runnerRel $expectedRunnerBlob 'INTERNET_ACCESS_1_RUNNER'
$implementationBlob = Assert-GitBlob $repoRoot $implementationRel $expectedImplementationBlob 'INTERNET_ACCESS_1_IMPLEMENTATION'

if ([string]$env:AAYS_TARGET_BRANCH -and [string]$env:AAYS_TARGET_BRANCH -ne $expectedBranch) { throw 'INTERNET_ACCESS_1_TARGET_BRANCH_ENV_MISMATCH' }
if ([string]$env:AAYS_TASK_ID -and [string]$env:AAYS_TASK_ID -ne $taskId) { throw 'INTERNET_ACCESS_1_TASK_ID_ENV_MISMATCH' }

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

$runnerPath = Join-Path $repoRoot $runnerRel
$env:AAYS_REPO_ROOT = $repoRoot
$env:AAYS_TARGET_BRANCH = $expectedBranch
$env:AAYS_TASK_ID = $taskId
$env:AAYS_CONTINUATION_KEY = $continuationKey

Write-Output 'SLOT_ID=internet_access_1'
Write-Output "TASK_ID=$taskId"
Write-Output "CONTINUATION_KEY=$continuationKey"
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "ACTIVE_BRANCH=$actualBranch"
Write-Output "RUNNER_BLOB_SHA=$runnerBlob"
Write-Output "IMPLEMENTATION_BLOB_SHA=$implementationBlob"
Write-Output "PYTHON_SCRIPT=$runnerPath"

Push-Location -LiteralPath $repoRoot
try {
  if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
    & $python.Source -3 $runnerPath
  } else {
    & $python.Source $runnerPath
  }
  $exitCode = $LASTEXITCODE
} finally {
  Pop-Location
}
if ($null -eq $exitCode) { $exitCode = 1 }
Write-Output "PYTHON_EXIT_CODE=$exitCode"
Write-Output 'FINAL_READY=false'
exit $exitCode

[CmdletBinding()]
param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$SlotId = 'security_public_safety_2',
  [string]$TargetBranch = 'codex/aays-single-runner-v5-20260706'
)

$ErrorActionPreference = 'Stop'
$expectedSlot = 'security_public_safety_2'
$expectedBranch = 'codex/aays-single-runner-v5-20260706'

if ($SlotId -ne $expectedSlot) { throw "WRONG_SLOT:$SlotId" }
if ($TargetBranch -ne $expectedBranch) { throw "WRONG_BRANCH:$TargetBranch" }

if (-not $RepoRoot) {
  $RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\..\..'))
} else {
  $RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
}

$pipeline = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\shards\security_public_safety_2\automation\security_public_safety_2_runner_pipeline.py'
if (-not (Test-Path -LiteralPath $pipeline -PathType Leaf)) {
  throw "PIPELINE_SCRIPT_MISSING:$pipeline"
}

$env:AAYS_REPO_ROOT = $RepoRoot
$env:AAYS_SLOT_ID = $expectedSlot
$env:AAYS_TARGET_BRANCH = $expectedBranch

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

Write-Output "SLOT_ID=$expectedSlot"
Write-Output 'TASK_VERSION=5.1-powershell-carrier'
Write-Output "TARGET_BRANCH=$expectedBranch"
Write-Output "REPO_ROOT=$RepoRoot"
Write-Output "PIPELINE=$pipeline"
Write-Output 'SINGLE_SHARED_RUNNER_ONLY=true'
Write-Output 'NEW_RUNNER=false'
Write-Output 'PARALLEL_RUNNER=false'
Write-Output 'GLOBAL_TASK_MUTATION=false'

if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
  & $python.Source -3 $pipeline --repo-root $RepoRoot --slot-id $expectedSlot --target-branch $expectedBranch
} else {
  & $python.Source $pipeline --repo-root $RepoRoot --slot-id $expectedSlot --target-branch $expectedBranch
}
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 1 }

Write-Output "PIPELINE_EXIT_CODE=$exitCode"
Write-Output 'FINAL_READY=false'
exit $exitCode

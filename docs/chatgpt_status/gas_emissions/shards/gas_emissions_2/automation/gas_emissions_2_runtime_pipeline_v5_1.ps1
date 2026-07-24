[CmdletBinding()]
param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$SlotId = 'gas_emissions_2',
  [string]$TargetBranch = 'codex/aays-single-runner-v5-20260706',
  [int]$Port = 8012
)

$ErrorActionPreference = 'Stop'
$expectedSlot = 'gas_emissions_2'
$expectedBranch = 'codex/aays-single-runner-v5-20260706'

if ($SlotId -ne $expectedSlot) { throw "WRONG_SLOT:$SlotId" }
if ($TargetBranch -ne $expectedBranch) { throw "WRONG_BRANCH:$TargetBranch" }

if (-not $RepoRoot) {
  $RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\..\..'))
} else {
  $RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
}

$pipeline = Join-Path $RepoRoot 'docs\chatgpt_status\gas_emissions\shards\gas_emissions_2\automation\gas_emissions_2_runtime_pipeline_guard_v2.py'
if (-not (Test-Path -LiteralPath $pipeline -PathType Leaf)) {
  throw "PIPELINE_GUARD_MISSING:$pipeline"
}

$env:AAYS_REPO_ROOT = $RepoRoot
$env:AAYS_SLOT_ID = $expectedSlot
$env:AAYS_TARGET_BRANCH = $expectedBranch

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }

Write-Output "SLOT_ID=$expectedSlot"
Write-Output 'TASK_VERSION=20260721_24-guard-v2-powershell-v5.1-carrier'
Write-Output "TARGET_BRANCH=$expectedBranch"
Write-Output "REPO_ROOT=$RepoRoot"
Write-Output "PIPELINE_GUARD=$pipeline"
Write-Output "PORT=$Port"
Write-Output 'PORT_OWNERSHIP_PREFLIGHT=true'
Write-Output 'SERVED_ASSET_SHA256_GUARD=true'
Write-Output 'BROWSER_EXECUTABLE_FALLBACK=true'
Write-Output 'SINGLE_SHARED_RUNNER_ONLY=true'
Write-Output 'NEW_RUNNER=false'
Write-Output 'PARALLEL_RUNNER=false'
Write-Output 'DIRECT_PUSH=false'
Write-Output 'DB_WRITE=false'
Write-Output 'MIGRATION=false'
Write-Output 'PRODUCTION_DEPLOY=false'
Write-Output 'FINAL_READY=false'

if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
  & $python.Source -3 $pipeline --repo-root $RepoRoot --slot-id $expectedSlot --target-branch $expectedBranch --port $Port
} else {
  & $python.Source $pipeline --repo-root $RepoRoot --slot-id $expectedSlot --target-branch $expectedBranch --port $Port
}
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 1 }

Write-Output "PIPELINE_EXIT_CODE=$exitCode"
Write-Output 'FINAL_READY=false'
exit $exitCode

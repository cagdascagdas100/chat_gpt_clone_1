[CmdletBinding()]
param(
  [int]$Port = 8012
)
$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$targetBranch = 'codex/aays-single-runner-v5-20260706'
$repoRoot = if ($env:AAYS_REPO_ROOT) { [System.IO.Path]::GetFullPath($env:AAYS_REPO_ROOT) } else { [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\..\..')) }
if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne $slotId) { throw "WRONG_SLOT:$($env:AAYS_SLOT_ID)" }
if ($env:AAYS_TARGET_BRANCH -and $env:AAYS_TARGET_BRANCH -ne $targetBranch) { throw "WRONG_BRANCH:$($env:AAYS_TARGET_BRANCH)" }
$env:AAYS_SLOT_ID = $slotId
$env:AAYS_TARGET_BRANCH = $targetBranch
$env:AAYS_REPO_ROOT = $repoRoot
$pipeline = Join-Path $repoRoot 'docs\chatgpt_status\aays1\shards\security_public_safety_2\automation\security_public_safety_2_runner_pipeline_v2_resume.py'
if (-not (Test-Path -LiteralPath $pipeline -PathType Leaf)) { throw "PIPELINE_V2_MISSING:$pipeline" }
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'PYTHON_EXECUTABLE_NOT_FOUND' }
Write-Output "SLOT_ID=$slotId"
Write-Output "TARGET_BRANCH=$targetBranch"
Write-Output 'TASK_VERSION=5.2-resume-safe-powershell-carrier'
Write-Output "REPO_ROOT=$repoRoot"
Write-Output "PIPELINE=$pipeline"
if ($python.Name -eq 'py.exe' -or $python.Name -eq 'py') {
  & $python.Source -3 $pipeline --repo-root $repoRoot --slot-id $slotId --target-branch $targetBranch --port $Port
} else {
  & $python.Source $pipeline --repo-root $repoRoot --slot-id $slotId --target-branch $targetBranch --port $Port
}
$exitCode = $LASTEXITCODE
if ($null -eq $exitCode) { $exitCode = 1 }
Write-Output "PIPELINE_EXIT_CODE=$exitCode"
Write-Output 'NEW_RUNNER=false'
Write-Output 'PARALLEL_RUNNER=false'
Write-Output 'GLOBAL_TASK_MUTATION=false'
Write-Output 'FINAL_READY=false'
exit $exitCode

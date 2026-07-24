# AAYS existing F portable single-runner continuation launcher.
# Does not create a new runner, worktree, queue, DB write, migration, or production deploy.
# Setup gates are non-blocking; the actual single queue runner is always attempted.

$ErrorActionPreference = 'Continue'

$env:AAYS_PORTABLE_ROOT = 'F:\TerraYield_AAYS_Portable'
$env:AAYS_REPO_ROOT = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$workRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'
$branch = 'codex/aays-single-runner-v5-20260706'
$repoRunner = 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1'
$patchedRunner = 'F:\TerraYield_AAYS_Portable\_portable_runtime\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_PATCHED_20260709.ps1'
$runnerToUse = $repoRunner

Set-Location -LiteralPath $env:AAYS_REPO_ROOT

Write-Output 'AAYS_F_SINGLE_RUNNER_CONTINUE_START=true'
Write-Output "repo_root=$env:AAYS_REPO_ROOT"
Write-Output "branch=$branch"
Write-Output 'new_runner=false'
Write-Output 'parallel_runner=false'

try {
  & powershell -NoProfile -ExecutionPolicy Bypass -File 'docs\chatgpt_status\_shared\automation\APPLY_F_PORTABLE_SINGLE_RUNNER_HOTFIX_20260709.ps1'
  Write-Output "hotfix_exit=$LASTEXITCODE"
} catch {
  Write-Output "hotfix_warning=$($_.Exception.Message)"
}

if (Test-Path -LiteralPath $patchedRunner) {
  $runnerToUse = $patchedRunner
  Write-Output "patched_runner=true"
  Write-Output "runner_to_use=$runnerToUse"
} else {
  Write-Output "patched_runner=false"
  Write-Output "runner_to_use=$runnerToUse"
}

try {
  & powershell -NoProfile -ExecutionPolicy Bypass -File 'docs\chatgpt_status\distance_property_types\automation\patch_dpt_site_panel_status_20260709.ps1'
  Write-Output "panel_patch_exit=$LASTEXITCODE"
} catch {
  Write-Output "panel_patch_warning=$($_.Exception.Message)"
}

Write-Output 'QUEUE_RUNNER_STARTING=true'
& powershell -NoProfile -ExecutionPolicy Bypass -File $runnerToUse -RepoRoot $env:AAYS_REPO_ROOT -WorkRoot $workRoot -MainBranch $branch -MaxTasks 5
$runnerExit = $LASTEXITCODE
Write-Output "QUEUE_RUNNER_EXIT=$runnerExit"
exit $runnerExit

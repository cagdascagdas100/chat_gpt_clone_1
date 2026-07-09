# AAYS existing F portable single-runner continuation launcher.
# Does not create a new runner, worktree, queue, DB write, migration, or production deploy.

$ErrorActionPreference = 'Stop'

$env:AAYS_REPO_ROOT = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$workRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'
$branch = 'codex/aays-single-runner-v5-20260706'

Set-Location -LiteralPath $env:AAYS_REPO_ROOT

& powershell -NoProfile -ExecutionPolicy Bypass -File 'docs\chatgpt_status\_shared\automation\APPLY_F_PORTABLE_SINGLE_RUNNER_HOTFIX_20260709.ps1'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& powershell -NoProfile -ExecutionPolicy Bypass -File 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1' -RepoRoot $env:AAYS_REPO_ROOT -WorkRoot $workRoot -MainBranch $branch -MaxTasks 5
exit $LASTEXITCODE

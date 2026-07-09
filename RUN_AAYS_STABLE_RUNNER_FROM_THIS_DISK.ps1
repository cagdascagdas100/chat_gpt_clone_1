# AAYS EXISTING F SINGLE RUNNER LAUNCHER
# No new runner, no new worktree, no clone, no DB write, no migration, no production deploy.
# This only starts/continues the existing F portable single runner from the canonical F root.

$ErrorActionPreference = 'Stop'
$env:AAYS_REPO_ROOT = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$env:AAYS_WORK_ROOT = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'
$branch = 'codex/aays-single-runner-v5-20260706'

Write-Host 'AAYS existing F single runner launcher'
Write-Host "Repo root: $env:AAYS_REPO_ROOT"
Write-Host "Branch: $branch"

Set-Location -LiteralPath $env:AAYS_REPO_ROOT

git fetch origin $branch
git checkout $branch
git pull --ff-only origin $branch

& powershell -NoProfile -ExecutionPolicy Bypass -File 'docs\chatgpt_status\_shared\automation\RUN_EXISTING_F_PORTABLE_SINGLE_RUNNER_HOTFIX_THEN_CONTINUE_20260709.ps1'
exit $LASTEXITCODE

$ErrorActionPreference = "Stop"
$repoRoot = [System.IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path)).TrimEnd('\')
$expectedBranch = "codex/aays-single-runner-v5-20260706"
$canonicalPrefix = "F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\"

if (-not $repoRoot.StartsWith($canonicalPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "BLOCKED_NON_CANONICAL_PORTABLE_REPO_ROOT=$repoRoot"
}

$launcher = Join-Path $repoRoot "docs/chatgpt_status/_shared/automation/START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706.ps1"
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
  throw "Missing shared runner launcher: $launcher"
}

$worktreeParent = Split-Path -Parent $repoRoot
$workRoot = Join-Path $worktreeParent "AAYS_STABLE_RUNNER_WORKTREES"
New-Item -ItemType Directory -Force -Path $workRoot | Out-Null

Write-Output "AAYS_CANONICAL_REPO_ROOT=$repoRoot"
Write-Output "AAYS_CANONICAL_WORK_ROOT=$workRoot"
Write-Output "AAYS_CANONICAL_BRANCH=$expectedBranch"
Write-Output "AAYS_MAX_TASKS_PER_SCAN=1"

& powershell -NoProfile -ExecutionPolicy Bypass -File $launcher `
  -RepoRoot $repoRoot `
  -WorkRoot $workRoot `
  -MainBranch $expectedBranch `
  -MaxTasks 1 `
  -StaleMinutes 20 `
  -NoPanel
exit $LASTEXITCODE

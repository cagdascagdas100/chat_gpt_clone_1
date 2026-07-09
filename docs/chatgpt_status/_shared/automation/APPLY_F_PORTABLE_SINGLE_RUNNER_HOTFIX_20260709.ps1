# AAYS F portable single-runner hotfix
# Purpose: patch the existing stable shared runner script to use the F portable canonical root,
# avoid C:\AAYS_WT as canonical storage, and process multiple queued tasks sequentially in the same runner.
# Safety: no fake data, no DB write, no migration, no production deploy.
# Idempotent: if already applied, continue without throwing.

$ErrorActionPreference = 'Stop'

$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
$runnerScript = Join-Path $repoRoot 'docs\chatgpt_status\_shared\automation\RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1'

if (-not (Test-Path -LiteralPath $runnerScript)) {
  throw "RUNNER_SCRIPT_MISSING: $runnerScript"
}

$content = Get-Content -LiteralPath $runnerScript -Raw
$original = $content

$content = $content.Replace("[string]`$RepoRoot = 'C:\AAYS_WT\AAYS_REPAIR_20260706_1738'", "[string]`$RepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'")
$content = $content.Replace("[string]`$WorkRoot = 'C:\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'", "[string]`$WorkRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'")
$content = $content.Replace("[int]`$MaxTasks = 1", "[int]`$MaxTasks = 5")
$content = $content.Replace("if (`$RepoRoot.StartsWith('F:\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED_F_DRIVE_NOT_CANONICAL: ' + `$RepoRoot }", "if (`$RepoRoot.StartsWith('C:\AAYS_WT\', [System.StringComparison]::OrdinalIgnoreCase)) { throw 'BLOCKED_C_DRIVE_NOT_CANONICAL: ' + `$RepoRoot }")

$patchMode = 'applied'
if ($content -eq $original) {
  $patchMode = 'already_applied_or_patterns_not_needed'
} else {
  [System.IO.File]::WriteAllText($runnerScript, $content, [System.Text.UTF8Encoding]::new($false))
}

$statusPath = Join-Path $repoRoot 'docs\chatgpt_status\_shared\status\f_portable_runner_hotfix_latest.json'
$statusDir = Split-Path -Parent $statusPath
if (-not (Test-Path -LiteralPath $statusDir)) { New-Item -ItemType Directory -Force -Path $statusDir | Out-Null }
$status = [ordered]@{
  status = 'F_PORTABLE_SINGLE_RUNNER_HOTFIX_OK'
  patch_mode = $patchMode
  runner_script = 'docs/chatgpt_status/_shared/automation/RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707.ps1'
  canonical_repo_root = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
  canonical_work_root = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES'
  max_tasks = 5
  single_runner_only = $true
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  applied_at_utc = (Get-Date).ToUniversalTime().ToString('o')
}
$status | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $statusPath -Encoding UTF8
Write-Output ($status | ConvertTo-Json -Depth 20)

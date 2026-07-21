param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$SlotId = $env:AAYS_SLOT_ID,
  [string]$TargetBranch = $env:AAYS_TARGET_BRANCH
)
$ErrorActionPreference = "Stop"
if ($SlotId -ne "security_public_safety_2") { throw "WRONG_SLOT:$SlotId" }
if ($TargetBranch -ne "codex/aays-single-runner-v5-20260706") { throw "WRONG_BRANCH:$TargetBranch" }
if (-not $RepoRoot) { $RepoRoot = (& git rev-parse --show-toplevel 2>$null).Trim() }
if (-not $RepoRoot) { throw "AAYS_REPO_ROOT_NOT_RESOLVED" }
$env:AAYS_REPO_ROOT = $RepoRoot
$env:AAYS_SLOT_ID = "security_public_safety_2"
$env:AAYS_TARGET_BRANCH = "codex/aays-single-runner-v5-20260706"
$script = Join-Path $RepoRoot "docs/chatgpt_status/aays1/shards/security_public_safety_2/automation/security_public_safety_2_runner_pipeline_v9_parity.py"
& python $script --repo-root $RepoRoot --slot-id $env:AAYS_SLOT_ID --target-branch $env:AAYS_TARGET_BRANCH
exit $LASTEXITCODE

param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [int]$Port = 8012
)
$ErrorActionPreference = 'Stop'
$Slot = 'security_public_safety_2'
$Branch = 'codex/aays-single-runner-v5-20260706'
if ($env:AAYS_SLOT_ID -and $env:AAYS_SLOT_ID -ne $Slot) { throw "WRONG_SLOT:$($env:AAYS_SLOT_ID)" }
if ($env:AAYS_TARGET_BRANCH -and $env:AAYS_TARGET_BRANCH -ne $Branch) { throw "WRONG_BRANCH:$($env:AAYS_TARGET_BRANCH)" }
if (-not $RepoRoot) { $RepoRoot = (& git -C $PSScriptRoot rev-parse --show-toplevel 2>$null) }
if (-not $RepoRoot -or -not (Test-Path -LiteralPath $RepoRoot)) { throw 'REPO_ROOT_NOT_RESOLVED' }
$env:AAYS_REPO_ROOT = (Resolve-Path -LiteralPath $RepoRoot).Path
$env:AAYS_SLOT_ID = $Slot
$env:AAYS_TARGET_BRANCH = $Branch
$python = Get-Command python -ErrorAction Stop
$script = Join-Path $env:AAYS_REPO_ROOT 'docs/chatgpt_status/aays1/shards/security_public_safety_2/automation/security_public_safety_2_runner_pipeline_v7_failclosed.py'
& $python.Source $script --repo-root $env:AAYS_REPO_ROOT --slot-id $Slot --target-branch $Branch --port $Port
exit $LASTEXITCODE

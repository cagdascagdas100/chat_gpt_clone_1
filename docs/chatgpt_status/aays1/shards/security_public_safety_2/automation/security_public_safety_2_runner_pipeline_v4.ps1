param(
  [string]$RepoRoot = $env:AAYS_REPO_ROOT,
  [string]$SlotId = $env:AAYS_SLOT_ID,
  [string]$TargetBranch = $env:AAYS_TARGET_BRANCH,
  [int]$Port = 8012
)
$ErrorActionPreference = 'Stop'
$ExpectedSlot = 'security_public_safety_2'
$ExpectedBranch = 'codex/aays-single-runner-v5-20260706'
if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $RepoRoot = 'F:\chatgpt\chat_gpt_clone_1_main' }
if ($SlotId -ne $ExpectedSlot) { Write-Error "WRONG_SLOT:$SlotId"; exit 2 }
if ($TargetBranch -ne $ExpectedBranch) { Write-Error "WRONG_BRANCH:$TargetBranch"; exit 2 }
$env:AAYS_REPO_ROOT = $RepoRoot
$env:AAYS_SLOT_ID = $ExpectedSlot
$env:AAYS_TARGET_BRANCH = $ExpectedBranch
$Script = Join-Path $RepoRoot 'docs\chatgpt_status\aays1\shards\security_public_safety_2\automation\security_public_safety_2_runner_pipeline_v4_provenance.py'
if (-not (Test-Path -LiteralPath $Script)) { Write-Error "MISSING_PROVENANCE_PIPELINE:$Script"; exit 3 }
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) { $Python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $Python) { Write-Error 'PYTHON_NOT_FOUND'; exit 4 }
& $Python.Source $Script --repo-root $RepoRoot --slot-id $ExpectedSlot --target-branch $ExpectedBranch --port $Port
exit $LASTEXITCODE

param(
  [string]$TaskId = "aays1_fg100_runner_contract_blocker_20260623_008",
  [string]$ResultPath = "",
  [string]$RepoResultPath = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$PageKey = "aays1"
$Base = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$Reports = Join-Path $Base "reports"
$Heartbeat = Join-Path $Base "heartbeat"
New-Item -ItemType Directory -Force -Path $Reports,$Heartbeat | Out-Null
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$runnerOut = Join-Path $Reports "aays1_fg100_runner_contract_blocker_20260623_008_runner_output.txt"
$hb = Join-Path $Heartbeat "aays1_fg100_runner_contract_blocker_20260623_008_heartbeat.txt"
$text = @"
PAGE_KEY=$PageKey
TASK_ID=$TaskId
STATUS=BLOCKED_WRONG_ROOT_OR_MISSING_AUTOMATION
PRODUCT_PROGRESS_ESTIMATE=99.9999998
FINAL_READY=false
RUNNER_PICKUP=proven_local_only
RUNNER_PUSH=not_proven
BLOCKERS=missing_expected_main_root_git_repo;missing_expected_automation_chain;shared_runner_not_targeting_aays1
"@
$text | Set-Content -LiteralPath $runnerOut -Encoding UTF8
$text | Set-Content -LiteralPath $hb -Encoding UTF8
if ($ResultPath) { $text | Set-Content -LiteralPath $ResultPath -Encoding UTF8 }
if ($RepoResultPath) { $text | Set-Content -LiteralPath $RepoResultPath -Encoding UTF8 }
Write-Output "aays1 blocker outputs written"

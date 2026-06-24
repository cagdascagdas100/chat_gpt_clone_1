param(
  [string]$TaskId = "gas_emissions_runner_contract_bridge_20260624",
  [string]$ResultPath = "",
  [string]$RepoResultPath = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$PageKey = "gas_emissions"
$Base = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$Reports = Join-Path $Base "reports"
$Heartbeat = Join-Path $Base "heartbeat"
$Status = Join-Path $Base "status"
New-Item -ItemType Directory -Force -Path $Reports,$Heartbeat,$Status | Out-Null
$text = @"
PAGE_KEY=$PageKey
TASK_ID=$TaskId
STATUS=BLOCKED_MAIN_BRANCH_PROOF
completion_percent=89
final_ready=false
runner_pickup=proven_local_only
runner_push=not_proven
blockers=local_checkout_not_main;finalizer_not_proven_on_main;page_key_root_evidence_not_pushed
"@
$text | Set-Content -LiteralPath (Join-Path $Reports "gas_emissions_finalizer_result_20260622_2300.md") -Encoding UTF8
$text | Set-Content -LiteralPath (Join-Path $Heartbeat "gas_emissions_runner_heartbeat_20260624.txt") -Encoding UTF8
$text | Set-Content -LiteralPath (Join-Path $Status "gas_emissions_runner_status_20260624.txt") -Encoding UTF8
if ($ResultPath) { $text | Set-Content -LiteralPath $ResultPath -Encoding UTF8 }
if ($RepoResultPath) { $text | Set-Content -LiteralPath $RepoResultPath -Encoding UTF8 }
Write-Output "gas emissions bridge blocker written"

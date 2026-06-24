param(
  [string]$TaskId = "page34_runner_pickup_ping_20260623_011",
  [string]$ResultPath = "",
  [string]$RepoResultPath = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$PageKey = "AAYS_REAL_TOPOGRAPHY_PRODUCT"
$Base = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$Reports = Join-Path $Base "reports"
$Heartbeat = Join-Path $Base "heartbeat"
$Status = Join-Path $Base "status"
New-Item -ItemType Directory -Force -Path $Reports,$Heartbeat,$Status | Out-Null
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$report = Join-Path $Reports "page34_runner_pickup_ping_20260623_011_report.md"
$text = @"
repo_full_name=cagdascagdas100/chat_gpt_clone_1
branch=feature/terrayield-aays-integration
local_worktree=C:\Users\cagda\Documents\GitHub\AAYS
git_remote=https://github.com/cagdascagdas100/chat_gpt_clone_1
current_branch=feature/terrayield-aays-integration
page_key=$PageKey
consumed_queue_file=page34_runner_pickup_ping_20260623_011.task.json
generated_report=docs/chatgpt_status/$PageKey/reports/page34_runner_pickup_ping_20260623_011_report.md
push_result=not_proven
blocker_remaining=main_branch_not_active;queue_contract_split;expected_ready_json_missing_in_checkout
completion_percent=75
final_ready=false
"@
$text | Set-Content -LiteralPath $report -Encoding UTF8
$text | Set-Content -LiteralPath (Join-Path $Heartbeat "page34_runner_pickup_ping_20260623_011_heartbeat.txt") -Encoding UTF8
$text | Set-Content -LiteralPath (Join-Path $Status "page34_runner_pickup_ping_20260623_011_status.txt") -Encoding UTF8
if ($ResultPath) { $text | Set-Content -LiteralPath $ResultPath -Encoding UTF8 }
if ($RepoResultPath) { $text | Set-Content -LiteralPath $RepoResultPath -Encoding UTF8 }
Write-Output "page34 pickup report written"

[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$PageKey = "",
  [string]$TaskId = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
} else {
  $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
}
if ([string]::IsNullOrWhiteSpace($PageKey)) { throw "PageKey is required." }
if ([string]::IsNullOrWhiteSpace($TaskId)) { throw "TaskId is required." }

$pageRoot = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey"
$statusDir = Join-Path $pageRoot "status"
$reportDir = Join-Path $pageRoot "reports"
$blockedDir = Join-Path $pageRoot "blocked"
New-Item -ItemType Directory -Force -Path $statusDir, $reportDir, $blockedDir | Out-Null

$now = (Get-Date).ToUniversalTime().ToString("o")
$payload = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  status = "blocked"
  blocker = "NEW_CHATGPT_PAGE_AUTOMATION_TEMPLATE_NOT_IMPLEMENTED"
  final_ready = $false
  product_final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  generated_at = $now
}

$statusPath = Join-Path $statusDir "$TaskId.template_status.json"
$blockedPath = Join-Path $blockedDir "$TaskId.template_blocked.json"
$reportPath = Join-Path $reportDir "$TaskId.template_report.txt"
$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $blockedPath -Encoding UTF8
@(
  "page_key=$PageKey",
  "task_id=$TaskId",
  "status=blocked",
  "blocker=NEW_CHATGPT_PAGE_AUTOMATION_TEMPLATE_NOT_IMPLEMENTED",
  "final_ready=false",
  "product_final_ready=false",
  "fake_data=false",
  "db_write=false",
  "migration=false",
  "production_deploy=false"
) | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Output "BLOCKER=NEW_CHATGPT_PAGE_AUTOMATION_TEMPLATE_NOT_IMPLEMENTED"
exit 2

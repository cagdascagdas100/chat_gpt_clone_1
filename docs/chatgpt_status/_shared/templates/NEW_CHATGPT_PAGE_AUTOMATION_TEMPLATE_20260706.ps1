[CmdletBinding()]
param(
  [string]$RepoRoot = "",
  [string]$PageKey = "",
  [string]$TaskId = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}
if ([string]::IsNullOrWhiteSpace($PageKey)) { throw "PageKey is required." }
if ([string]::IsNullOrWhiteSpace($TaskId)) { throw "TaskId is required." }

$statusDir = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey/status"
$reportDir = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey/reports"
New-Item -ItemType Directory -Force -Path $statusDir, $reportDir | Out-Null

$now = (Get-Date).ToUniversalTime().ToString("o")
$payload = [ordered]@{
  page_key = $PageKey
  task_id = $TaskId
  status = "blocked"
  blocker = "NEW_PAGE_AUTOMATION_TEMPLATE_NOT_REPLACED"
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  generated_at = $now
}
$payload | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $statusDir "$TaskId.template_status.json") -Encoding UTF8
@(
  "page_key=$PageKey",
  "task_id=$TaskId",
  "status=blocked",
  "blocker=NEW_PAGE_AUTOMATION_TEMPLATE_NOT_REPLACED",
  "final_ready=false"
) | Set-Content -LiteralPath (Join-Path $reportDir "$TaskId.template_report.txt") -Encoding UTF8
Write-Output "BLOCKER=NEW_PAGE_AUTOMATION_TEMPLATE_NOT_REPLACED"
exit 2

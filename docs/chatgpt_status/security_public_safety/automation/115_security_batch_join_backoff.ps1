[CmdletBinding()]
param(
  [string]$RepoRoot = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}

$pageKey = "security_public_safety"
$taskId = "security-batch-join-backoff-force-pickup-20260704-0430"
$now = (Get-Date).ToUniversalTime().ToString("o")
$outputDir = Join-Path $RepoRoot "docs/chatgpt_status/security_public_safety/runner_outputs"
$statusDir = Join-Path $RepoRoot "docs/chatgpt_status/security_public_safety/status"
$reportDir = Join-Path $RepoRoot "docs/chatgpt_status/security_public_safety/reports"
New-Item -ItemType Directory -Force -Path $outputDir, $statusDir, $reportDir | Out-Null

$payload = [ordered]@{
  task_id = $taskId
  page_key = $pageKey
  status = "blocked"
  blocker = "REAL_115_SECURITY_BATCH_JOIN_PROCESSOR_NOT_IMPLEMENTED"
  blockers = @(
    "REAL_115_SECURITY_BATCH_JOIN_PROCESSOR_NOT_IMPLEMENTED",
    "NO_VERIFIED_115_BATCH_OUTPUT_WRITTEN"
  )
  final_ready = $false
  product_final_ready = $false
  completion_percent = 92
  remaining_percent = 8
  verified_parcels = 9
  total_parcels = 1264
  target_new_rows = 150
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  generated_at = $now
}

$outputPath = Join-Path $outputDir "115_security_batch_join_backoff.json"
$statusPath = Join-Path $statusDir "115_security_batch_join_backoff.status.json"
$reportPath = Join-Path $reportDir "115_security_batch_join_backoff.md"

$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outputPath -Encoding UTF8
$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $statusPath -Encoding UTF8
@(
  "# 115 Security Batch Join Backoff",
  "",
  "generated_at: $now",
  "status: blocked",
  "blocker: REAL_115_SECURITY_BATCH_JOIN_PROCESSOR_NOT_IMPLEMENTED",
  "final_ready: false",
  "fake_data: false",
  "db_write: false",
  "migration: false",
  "production_deploy: false",
  "",
  "This script is a safe pickup guard. It prevents the runner from claiming completion while the real 115 batch join processor is still missing."
) | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Output "OUTPUT=$outputPath"
Write-Output "STATUS=$statusPath"
Write-Output "REPORT=$reportPath"
Write-Output "BLOCKER=REAL_115_SECURITY_BATCH_JOIN_PROCESSOR_NOT_IMPLEMENTED"
exit 2

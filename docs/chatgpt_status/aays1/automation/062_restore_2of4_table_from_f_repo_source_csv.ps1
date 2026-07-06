$ErrorActionPreference = "Stop"

$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}
$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { "normalized-080-restore-75-rel-20260706" } else { $env:AAYS_TASK_ID }
$PageKey = if ([string]::IsNullOrWhiteSpace($env:AAYS_PAGE_KEY)) { "aays1" } else { $env:AAYS_PAGE_KEY }
$TargetBranch = if ([string]::IsNullOrWhiteSpace($env:AAYS_TARGET_BRANCH)) { "codex/aays-single-runner-v5-20260706" } else { $env:AAYS_TARGET_BRANCH }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$StatusDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
$ReportDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\reports"
New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir | Out-Null

$status = @"
status=BLOCKED_080_REPAIR_SAFE_SOURCE_CSV_REQUIRED
page_key=$PageKey
task_id=$TaskId
target_branch=$TargetBranch
final_ready=false
fake_data=false
db_write=false
migration=false
ddl=false
production_deploy=false
blocker=source_csv_restore_requires_repo_local_source_csv_no_fake_rows
updated_at=$Stamp
"@
$status | Set-Content -Encoding UTF8 (Join-Path $StatusDir "080_repair_safe_source_csv_required_$Stamp.txt")

$report = @"
# 080 Repair-Safe Source CSV Required

This script is repair-runner safe: it does not use F drive hard-coded worktrees, does not call git push, does not write DB, does not run migrations, does not deploy, and does not fabricate rows.

The previous implementation depended on F repo source CSV and pushed to main internally. That behavior was removed for the repair branch flow.

Next real implementation step: place the required source CSV under the repair repo and implement table restoration under allowed paths only.
"@
$report | Set-Content -Encoding UTF8 (Join-Path $ReportDir "080_repair_safe_source_csv_required_$Stamp.md")

Write-Output "AAYS1_080_BLOCKED_REPAIR_SAFE_SOURCE_CSV_REQUIRED page_key=$PageKey task_id=$TaskId final_ready=false fake_data=false db_write=false migration=false production_deploy=false"
exit 0

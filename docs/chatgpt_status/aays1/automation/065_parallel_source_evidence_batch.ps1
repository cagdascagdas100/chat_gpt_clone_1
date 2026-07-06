$ErrorActionPreference = "Stop"
<<<<<<< HEAD
$RepoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path }
$PageKey = if ($env:AAYS_PAGE_KEY) { $env:AAYS_PAGE_KEY } else { "aays1" }
$TaskId = if ($env:AAYS_TASK_ID) { $env:AAYS_TASK_ID } else { "normalized-065-progress-report-20260706" }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$StatusDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
$ReportDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\reports"
New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir | Out-Null
"status=BLOCKED_065_SOURCE_IMPLEMENTATION_MISSING`npage_key=$PageKey`ntask_id=$TaskId`nfinal_ready=false`nfake_data=false`ndb_write=false`nmigration=false`nproduction_deploy=false`nupdated_at=$Stamp" | Set-Content -Encoding UTF8 (Join-Path $StatusDir "065_blocked_$Stamp.txt")
"# 065 blocked`n`nNo fake completion. Source implementation is missing. final_ready=false." | Set-Content -Encoding UTF8 (Join-Path $ReportDir "065_blocked_$Stamp.md")
throw "BLOCKED_065_SOURCE_IMPLEMENTATION_MISSING"
=======

$RepoRoot = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
  $RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..\..")).Path
}
$TaskId = if ([string]::IsNullOrWhiteSpace($env:AAYS_TASK_ID)) { "normalized-065-progress-report-20260706" } else { $env:AAYS_TASK_ID }
$PageKey = if ([string]::IsNullOrWhiteSpace($env:AAYS_PAGE_KEY)) { "aays1" } else { $env:AAYS_PAGE_KEY }
$TargetBranch = if ([string]::IsNullOrWhiteSpace($env:AAYS_TARGET_BRANCH)) { "codex/aays-single-runner-v5-20260706" } else { $env:AAYS_TARGET_BRANCH }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$StatusDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\status"
$ReportDir = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey\reports"
New-Item -ItemType Directory -Force -Path $StatusDir,$ReportDir | Out-Null

$status = @"
status=BLOCKED_SCRIPT_CREATION_REQUIRES_SOURCE_FETCH_IMPLEMENTATION
page_key=$PageKey
task_id=$TaskId
target_branch=$TargetBranch
final_ready=false
fake_data=false
db_write=false
migration=false
production_deploy=false
blocker=parallel_source_fetch_script_requires_real_source_fetch_implementation
updated_at=$Stamp
"@
$status | Set-Content -Encoding UTF8 (Join-Path $StatusDir "065_parallel_source_evidence_batch_blocked_$Stamp.txt")

@"
# 065 Parallel Source Evidence Batch Blocked

Runner repair-safe mode executed the 065 task without local git push, DB write, migration, production deploy, fake evidence, or fake final_ready.

The remaining implementation work is real source/evidence fetch logic. This task intentionally does not fabricate verified rows.
"@ | Set-Content -Encoding UTF8 (Join-Path $ReportDir "065_parallel_source_evidence_batch_blocked_$Stamp.md")

Write-Output "AAYS1_065_BLOCKED_REAL_SOURCE_FETCH_IMPLEMENTATION_REQUIRED page_key=$PageKey task_id=$TaskId final_ready=false fake_data=false db_write=false migration=false production_deploy=false"
exit 0
>>>>>>> 2a158d013 (Make aays1 065 task repair-runner safe)

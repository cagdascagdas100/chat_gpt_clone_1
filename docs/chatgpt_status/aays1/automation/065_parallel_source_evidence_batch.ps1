$ErrorActionPreference = "Stop"
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

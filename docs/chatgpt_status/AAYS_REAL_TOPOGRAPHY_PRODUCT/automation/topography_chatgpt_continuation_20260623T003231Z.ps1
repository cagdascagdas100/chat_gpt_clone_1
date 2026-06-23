<#
AAYS Topography ChatGPT continuation wrapper.
Read-only diagnostic. Does not start a second runner.
#>
[CmdletBinding()]
param(
  [string]$Worktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706'
)
$ErrorActionPreference = 'Continue'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$TaskId = 'topography_chatgpt_continuation_20260623T003231Z'
$PageRoot = Join-Path $Worktree "docs\chatgpt_status\$PageKey"
$ReportDir = Join-Path $PageRoot 'reports'
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$Summary = Join-Path $ReportDir "$($TaskId)_work_summary.txt"
'AAYS_TOPOGRAPHY_CHATGPT_CONTINUATION' | Set-Content -LiteralPath $Summary -Encoding UTF8
"PAGE_KEY=$PageKey" | Add-Content -LiteralPath $Summary -Encoding UTF8
"TASK_ID=$TaskId" | Add-Content -LiteralPath $Summary -Encoding UTF8
'MODE=read_only_diagnostic_bundle' | Add-Content -LiteralPath $Summary -Encoding UTF8
'STEP=Check local runtime, remote sync, data coverage, and UI smoke evidence.' | Add-Content -LiteralPath $Summary -Encoding UTF8

$scripts = @(
  '10_verify_topography_local_runtime.ps1',
  '30_remote_sync_diagnostic.ps1',
  '20_audit_topography_data_coverage.ps1'
)
foreach ($name in $scripts) {
  $p = Join-Path $PageRoot "automation\$name"
  if (Test-Path -LiteralPath $p) {
    "RUNNING=$p" | Add-Content -LiteralPath $Summary -Encoding UTF8
    powershell -ExecutionPolicy Bypass -File $p -Worktree $Worktree
    "EXIT_CODE_$name=$LASTEXITCODE" | Add-Content -LiteralPath $Summary -Encoding UTF8
  } else {
    "MISSING_SCRIPT=$p" | Add-Content -LiteralPath $Summary -Encoding UTF8
  }
}
'NEXT=Review generated diagnostic reports before changing any remote branch.' | Add-Content -LiteralPath $Summary -Encoding UTF8
Write-Host "Wrote $Summary"
exit 0

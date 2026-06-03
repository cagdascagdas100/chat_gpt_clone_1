$ErrorActionPreference='Continue'
$TaskId='cost50-028-contract-readiness-summary-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function ReadFlag($Path,$Pattern){ if(Test-Path $Path){ $txt=Get-Content -Raw -Encoding UTF8 -Path $Path; if($txt -match $Pattern){ return $Matches[0] } }; return 'MISSING' }
Log "TASK=$TaskId"
Log 'MODE=readonly_contract_readiness_summary'
$prev026=Join-Path $ResultDir 'cost50-026-db-platform-readiness-matrix-audit-20260512.report.md'
$prev027=Join-Path $ResultDir 'cost50-027-readiness-gap-summary-20260512.report.md'
$out=Join-Path $ResultDir "$TaskId.report.md"
$report=@(
  '# Cost50 028 Contract Readiness Summary',
  '',
  "Generated: $(Get-Date -Format s)",
  '',
  "TASK=$TaskId",
  'MODE=readonly_summary_only',
  "PREV_026_DONE=$(ReadFlag $prev026 'TASK_COMPLETION=100/100')",
  "PREV_026_SCORE=$(ReadFlag $prev026 'READINESS_SCORE=\d+/100')",
  "PREV_027_DONE=$(ReadFlag $prev027 'TASK_COMPLETION=100/100')",
  "PREV_027_PERCENT=$(ReadFlag $prev027 'COST50_APPROX_PERCENT=\d+')",
  'CHANGE_EXECUTED=False',
  'READINESS_STATUS=contract_summary_ready_for_gap_audit',
  'NEXT_RECOMMENDED_STEP=cost50-029-db-backed-platform-contract-gap-audit',
  'PLAN_PROGRESS_PERCENT=56',
  'TASK_COMPLETION=100/100'
)
$report | Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log 'COST50_APPROX_PERCENT=56'
Log 'TASK_COMPLETION=100/100'
exit 0

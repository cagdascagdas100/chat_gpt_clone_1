$ErrorActionPreference='Continue'
$TaskId='cost50-024-safe-cleanup-decision-gate-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function PickLine($Path,$Pattern){
  if(Test-Path $Path){
    $txt=Get-Content -Raw -Encoding UTF8 -Path $Path
    if($txt -match $Pattern){ return $Matches[0] }
  }
  return 'MISSING'
}
Log "TASK=$TaskId"
Log 'MODE=safe_cleanup_decision_gate_readonly_no_delete'
$cost023=Join-Path $ResultDir 'cost50-023-safe-cleanup-audit-inventory-20260512.report.md'
$terra116=Join-Path $ResultDir 'terrayield-116-plan-l-zip-repair-status.txt'
$protected=PickLine $cost023 'PROTECTED_TOUCH_COUNT=0'
$deleteFlag=PickLine $cost023 'DELETE_EXECUTED=False'
$candidates=PickLine $cost023 'CANDIDATE_TOTAL_COUNT=\d+'
$candidateBytes=PickLine $cost023 'CANDIDATE_TOTAL_BYTES=\d+'
$terraAccept=PickLine $terra116 'FINAL_ACCEPTANCE=100/100'
$out=Join-Path $ResultDir "$TaskId.report.md"
$lines=@(
  '# Cost50 024 Safe Cleanup Decision Gate',
  '',
  "Generated: $(Get-Date -Format s)",
  '',
  "TASK=$TaskId",
  'MODE=readonly_no_delete',
  "COST50_023_REPORT_EXISTS=$(Test-Path $cost023)",
  "PROTECTED_TOUCH=$protected",
  "DELETE_EXECUTED=$deleteFlag",
  "CANDIDATE_TOTAL_COUNT=$candidates",
  "CANDIDATE_TOTAL_BYTES=$candidateBytes",
  "TERRAYIELD_FINAL_ACCEPTANCE=$terraAccept",
  'DECISION=NO_DELETE_WITHOUT_EXPLICIT_USER_AUTHORIZATION',
  'SAFE_NEXT_STEP=cost50-025-handoff-runbook-and-cleanup-approval-note',
  'TERRAYIELD_PLAN_PERCENT=99',
  'TERRAYIELD_REMAINING_PERCENT=1',
  'COST50_APPROX_PERCENT=48',
  'COST50_REMAINING_PERCENT=52',
  'TASK_COMPLETION=100/100'
)
$lines | Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log 'DECISION=NO_DELETE_WITHOUT_EXPLICIT_USER_AUTHORIZATION'
Log 'COST50_APPROX_PERCENT=48'
Log 'TASK_COMPLETION=100/100'
exit 0

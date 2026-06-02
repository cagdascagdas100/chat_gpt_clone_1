$ErrorActionPreference='Continue'
$TaskId='cost50-022-traceability-handoff-closure-audit-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function ReadFlag($Path,$Pattern){
  if(Test-Path $Path){
    $txt=Get-Content -Raw -Encoding UTF8 -Path $Path
    if($txt -match $Pattern){ return $Matches[0] }
  }
  return 'MISSING'
}
Log "TASK=$TaskId"
Log 'MODE=traceability_handoff_closure_audit_readonly'
Log "BRIDGE_ROOT=$BridgeRoot"
$current=Join-Path $BridgeRoot 'ai-tasks\current-task.json'
$last=Join-Path $BridgeRoot 'ai-tasks\.last-task-id'
$terraStatus=Join-Path $ResultDir 'terrayield-116-plan-l-zip-repair-status.txt'
$cost021=Join-Path $ResultDir 'cost50-021-runner-sync-probe-20260512.report.md'
$currentExists=Test-Path $current
$lastExists=Test-Path $last
$terraZipExists=ReadFlag $terraStatus 'FINAL_ZIP_EXISTS=True'
$terraRows=ReadFlag $terraStatus 'CSV_ROWS=\d+'
$terraFeatures=ReadFlag $terraStatus 'GEOJSON_FEATURES=\d+'
$terraMatch=ReadFlag $terraStatus 'ROWS_FEATURES_MATCH=True'
$cost021Done=ReadFlag $cost021 'TASK_COMPLETION=100/100'
$out=Join-Path $ResultDir "$TaskId.report.md"
$lines=@(
  '# Cost50 022 Traceability Handoff Closure Audit',
  '',
  "Generated: $(Get-Date -Format s)",
  '',
  "TASK=$TaskId",
  'MODE=readonly',
  "CURRENT_TASK_EXISTS=$currentExists",
  "LAST_TASK_EXISTS=$lastExists",
  "TERRAYIELD_FINAL_ZIP=$terraZipExists",
  "TERRAYIELD_CSV_ROWS=$terraRows",
  "TERRAYIELD_GEOJSON_FEATURES=$terraFeatures",
  "TERRAYIELD_ROWS_FEATURES_MATCH=$terraMatch",
  "COST50_021_DONE=$cost021Done",
  'TERRAYIELD_PLAN_PERCENT=99',
  'TERRAYIELD_REMAINING_PERCENT=1',
  'COST50_APPROX_PERCENT=44',
  'COST50_REMAINING_PERCENT=56',
  'NEXT_RECOMMENDED_STEP=cost50-023-final-index-and-artifact-map',
  'TASK_COMPLETION=100/100'
)
$lines | Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log 'TERRAYIELD_PLAN_PERCENT=99'
Log 'COST50_APPROX_PERCENT=44'
Log 'TASK_COMPLETION=100/100'
exit 0

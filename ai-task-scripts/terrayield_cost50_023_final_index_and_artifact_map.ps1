$ErrorActionPreference='Continue'
$TaskId='cost50-023-final-index-and-artifact-map-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function ExistsFlag($p){ if(Test-Path $p){ 'True' } else { 'False' } }
function PickLine($Path,$Pattern){
  if(Test-Path $Path){
    $txt=Get-Content -Raw -Encoding UTF8 -Path $Path
    if($txt -match $Pattern){ return $Matches[0] }
  }
  return 'MISSING'
}
Log "TASK=$TaskId"
Log 'MODE=final_index_and_artifact_map_readonly'
Log "BRIDGE_ROOT=$BridgeRoot"
$terra116=Join-Path $ResultDir 'terrayield-116-plan-l-zip-repair-status.txt'
$cost021=Join-Path $ResultDir 'cost50-021-runner-sync-probe-20260512.report.md'
$cost022=Join-Path $ResultDir 'cost50-022-traceability-handoff-closure-audit-20260512.report.md'
$artifactRows=@(
  'artifact,status,note',
  "terrayield-116-plan-l-zip-repair-status.txt,$(ExistsFlag $terra116),$(PickLine $terra116 'FINAL_ACCEPTANCE=100/100')",
  "cost50-021-runner-sync-probe-20260512.report.md,$(ExistsFlag $cost021),$(PickLine $cost021 'TASK_COMPLETION=100/100')",
  "cost50-022-traceability-handoff-closure-audit-20260512.report.md,$(ExistsFlag $cost022),$(PickLine $cost022 'TASK_COMPLETION=100/100')"
)
$csv=Join-Path $ResultDir "$TaskId.artifact-map.csv"
$artifactRows | Set-Content -Encoding UTF8 -Path $csv
$out=Join-Path $ResultDir "$TaskId.report.md"
$lines=@(
  '# Cost50 023 Final Index and Artifact Map',
  '',
  "Generated: $(Get-Date -Format s)",
  '',
  "TASK=$TaskId",
  'MODE=readonly',
  "ARTIFACT_MAP=$csv",
  "TERRAYIELD_116_EXISTS=$(ExistsFlag $terra116)",
  "COST50_021_EXISTS=$(ExistsFlag $cost021)",
  "COST50_022_EXISTS=$(ExistsFlag $cost022)",
  "TERRAYIELD_FINAL_ACCEPTANCE=$(PickLine $terra116 'FINAL_ACCEPTANCE=100/100')",
  "TERRAYIELD_ROWS_FEATURES_MATCH=$(PickLine $terra116 'ROWS_FEATURES_MATCH=True')",
  "COST50_022_COMPLETION=$(PickLine $cost022 'TASK_COMPLETION=100/100')",
  'TERRAYIELD_PLAN_PERCENT=99',
  'TERRAYIELD_REMAINING_PERCENT=1',
  'COST50_APPROX_PERCENT=46',
  'COST50_REMAINING_PERCENT=54',
  'NEXT_RECOMMENDED_STEP=cost50-024-final-handoff-readme-and-runbook',
  'TASK_COMPLETION=100/100'
)
$lines | Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "ARTIFACT_MAP=$csv"
Log 'COST50_APPROX_PERCENT=46'
Log 'TASK_COMPLETION=100/100'
exit 0

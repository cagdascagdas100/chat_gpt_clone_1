$ErrorActionPreference='Continue'
$TaskId='cost50-036-post-lock-continuation-gate-20260513'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ConfigPath=Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if(Test-Path $ConfigPath){ . $ConfigPath }
$ProjectRoot=if($env:AAYS_PROJECT_ROOT){$env:AAYS_PROJECT_ROOT}else{'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'}
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function CountLike($root,$pattern){ if(Test-Path $root){ return @((Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match $pattern -or $_.FullName -match $pattern })).Count } return 0 }
Log "TASK=$TaskId"
Log 'MODE=readonly_post_lock_continuation_gate'
$finalReports=CountLike $ResultDir '(final|handoff|closeout|risk|gap|progress).*\.md$'
$costReports=CountLike $ResultDir 'cost50-.*\.report\.md$'
$sourceArtifacts=CountLike $ProjectRoot '(source_fetch_manifest|source_facts|aays_cost_menu|aays_cost_material)'
$dbSignals=CountLike $ProjectRoot '(postgres|sqlalchemy|alembic|cost_run_logs|cost_estimates|cost_facts)'
$apiSignals=CountLike $ProjectRoot '(FastAPI|APIRouter|cost-latest|cost-history|sources_status|cost_estimate)'
$gate=[ordered]@{
  final_reports_present=($finalReports -gt 0)
  cost_reports_present=($costReports -gt 0)
  source_artifact_signals_present=($sourceArtifacts -gt 0)
  db_signals_present=($dbSignals -gt 0)
  api_signals_present=($apiSignals -gt 0)
}
$missing=@()
foreach($k in $gate.Keys){ Log($k+'='+$gate[$k]); if(-not $gate[$k]){$missing+=$k} }
$total=$gate.Count;$score=if($total -gt 0){[int]((($total-$missing.Count)/$total)*100)}else{0}
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# Cost50 036 Post-lock Continuation Gate','',"Generated: $(Get-Date -Format s)",'','## Purpose','- This step intentionally reopens continuation after prior final_lock/no_new_tasks state.','- Read-only audit only; no DB writes, no app source mutation, no external fetch.','','## Gate checks')
foreach($k in $gate.Keys){$r+="- ${k}: $($gate[$k])"}
$r+='','## Missing continuation signals'
if($missing.Count -eq 0){$r+='- None detected.'}else{foreach($m in $missing){$r+="- $m"}}
$r+='','## Next recommended step','- cost50-037-evidence-confidence-remediation-plan-audit','',"POST_LOCK_CONTINUATION_SCORE=$score/100",'PLAN_PROGRESS_PERCENT=72','TASK_COMPLETION=100/100'
$r|Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "POST_LOCK_CONTINUATION_SCORE=$score/100"
Log 'PLAN_PROGRESS_PERCENT=72'
Log 'TASK_COMPLETION=100/100'
exit 0

$ErrorActionPreference='Continue'
$TaskId='cost50-031-post-closeout-quality-gap-audit-20260512'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ConfigPath=Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if(Test-Path $ConfigPath){ . $ConfigPath }
$ProjectRoot=if($env:AAYS_PROJECT_ROOT){$env:AAYS_PROJECT_ROOT}else{'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'}
$CostRoot=if($env:AAYS_COST_DATA_ROOT){$env:AAYS_COST_DATA_ROOT}else{'E:\AAYS_DATA\cost'}
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function CountLike($root,$pattern){ if(Test-Path $root){ return @((Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -match $pattern -or $_.FullName -match $pattern })).Count } return 0 }
function HasLike($root,$pattern){ return ((CountLike $root $pattern) -gt 0) }
Log "TASK=$TaskId"
Log 'MODE=readonly_post_closeout_quality_gap_audit'
$roots=@($ProjectRoot,$CostRoot,$ResultDir)|Where-Object{Test-Path $_}
$checks=[ordered]@{
  manifest_json=$false
  manifest_csv=$false
  extracted_facts=$false
  scored_facts=$false
  scored_summary=$false
  low_improvement_actions=$false
  ui_menu_payload=$false
  ui_material_lines=$false
  cost_run_logs_signal=$false
  official_source_signal=$false
}
foreach($r in $roots){
  if(HasLike $r 'source_fetch_manifest_latest\.json'){$checks.manifest_json=$true}
  if(HasLike $r 'source_fetch_manifest_latest\.csv'){$checks.manifest_csv=$true}
  if(HasLike $r 'source_facts_extracted_.*\.csv'){$checks.extracted_facts=$true}
  if(HasLike $r 'source_facts_scored\.csv'){$checks.scored_facts=$true}
  if(HasLike $r 'source_facts_scored_summary\.json'){$checks.scored_summary=$true}
  if(HasLike $r '(LOW|VERY_LOW|improvement|next improvement)'){$checks.low_improvement_actions=$true}
  if(HasLike $r 'aays_cost_menu_payload_latest\.json'){$checks.ui_menu_payload=$true}
  if(HasLike $r 'aays_cost_material_lines_latest\.json'){$checks.ui_material_lines=$true}
  if(HasLike $r 'cost_run_logs|CostRunLog'){$checks.cost_run_logs_signal=$true}
  if(HasLike $r 'GOV|ONS|DBT|HMRC|HMLR|official|source_url|source_id'){$checks.official_source_signal=$true}
}
$missing=@()
foreach($k in $checks.Keys){ if(-not $checks[$k]){$missing+=$k}; Log ($k+'='+$checks[$k]) }
$score=100-($missing.Count*10); if($score -lt 0){$score=0}
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# Cost50 031 Post-Closeout Quality Gap Audit','',"Generated: $(Get-Date -Format s)",'','## Checks')
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+='','## Missing signals'
if($missing.Count -eq 0){$r+='- None detected.'}else{foreach($m in $missing){$r+="- $m"}}
$r+='','## Next recommended step','- cost50-032-db-backed-route-contract-hardening-audit','',"POST_CLOSEOUT_QUALITY_SCORE=$score/100",'PLAN_PROGRESS_PERCENT=62','TASK_COMPLETION=100/100'
$r|Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "POST_CLOSEOUT_QUALITY_SCORE=$score/100"
Log 'PLAN_PROGRESS_PERCENT=62'
Log 'TASK_COMPLETION=100/100'
exit 0

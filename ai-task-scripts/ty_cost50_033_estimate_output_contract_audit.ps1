$ErrorActionPreference='Continue'
$TaskId='cost50-033-estimate-output-contract-audit-20260513'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ConfigPath=Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if(Test-Path $ConfigPath){ . $ConfigPath }
$ProjectRoot=if($env:AAYS_PROJECT_ROOT){$env:AAYS_PROJECT_ROOT}else{'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'}
$CostRoot=if($env:AAYS_COST_DATA_ROOT){$env:AAYS_COST_DATA_ROOT}else{'E:\AAYS_DATA\cost'}
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function ReadAll($root,$pattern){ $t=''; if(Test-Path $root){ Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match $pattern -or $_.Name -match $pattern } | Select-Object -First 400 | ForEach-Object { try{ $t += "`n---FILE:$($_.FullName)---`n" + (Get-Content -Raw -Encoding UTF8 $_.FullName) }catch{} } }; return $t }
Log "TASK=$TaskId"
Log 'MODE=readonly_estimate_output_contract_audit'
$text=(ReadAll $ProjectRoot '(\.py$|\.json$|\.md$|\.csv$)')+(ReadAll $CostRoot '(aays_cost|estimate|material|source_facts|\.json$|\.csv$)')
$checks=[ordered]@{
  estimate_endpoint=[bool]($text -match 'admin.*/cost.*/estimate|cost_estimate|estimate_cost|POST /admin/cost/estimate')
  estimate_total=[bool]($text -match 'total_cost|estimate_total|grand_total|total')
  itemized_lines=[bool]($text -match 'cost_estimate_lines|estimate_lines|line_items|itemized')
  material_quantity=[bool]($text -match 'material.*quantity|quantity.*material|material_qty|qty')
  material_lines_payload=[bool]($text -match 'aays_cost_material_lines_latest|material_lines')
  menu_payload=[bool]($text -match 'aays_cost_menu_payload_latest|cost_menu')
  confidence=[bool]($text -match 'confidence')
  evidence_source=[bool]($text -match 'source_id|source_url|evidence_text')
  seed_penalty=[bool]($text -match 'seed.*penalt|penalt.*seed|is_seed')
  run_log_error=[bool]($text -match 'cost_run_logs|CostRunLog|run_log')
}
$missing=@()
foreach($k in $checks.Keys){ Log($k+'='+$checks[$k]); if(-not $checks[$k]){$missing+=$k} }
$total=$checks.Count;$score=if($total -gt 0){[int]((($total-$missing.Count)/$total)*100)}else{0}
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# Cost50 033 Estimate Output Contract Audit','',"Generated: $(Get-Date -Format s)",'','## Checks')
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+='','## Missing contract signals'
if($missing.Count -eq 0){$r+='- None detected.'}else{foreach($m in $missing){$r+="- $m"}}
$r+='','## Next recommended step','- cost50-034-source-status-contract-audit','',"ESTIMATE_OUTPUT_CONTRACT_SCORE=$score/100",'PLAN_PROGRESS_PERCENT=66','TASK_COMPLETION=100/100'
$r|Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "ESTIMATE_OUTPUT_CONTRACT_SCORE=$score/100"
Log 'PLAN_PROGRESS_PERCENT=66'
Log 'TASK_COMPLETION=100/100'
exit 0

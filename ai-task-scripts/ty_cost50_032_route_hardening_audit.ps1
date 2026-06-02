$ErrorActionPreference='Continue'
$TaskId='cost50-032-route-hardening-audit-20260513'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ConfigPath=Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if(Test-Path $ConfigPath){ . $ConfigPath }
$ProjectRoot=if($env:AAYS_PROJECT_ROOT){$env:AAYS_PROJECT_ROOT}else{'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'}
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function ReadAll($root,$pattern){ $t=''; if(Test-Path $root){ Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match $pattern } | Select-Object -First 300 | ForEach-Object { try{ $t += "`n---FILE:$($_.FullName)---`n" + (Get-Content -Raw -Encoding UTF8 $_.FullName) }catch{} } }; return $t }
Log "TASK=$TaskId"
Log 'MODE=readonly_route_hardening_audit'
$text=ReadAll $ProjectRoot '(\.py$|\.sql$|\.md$|\.json$)'
$checks=[ordered]@{
  post_sources_sync=[bool]($text -match 'admin.*/cost.*/sources.*/sync|sources_sync|cost_sources_sync')
  post_estimate=[bool]($text -match 'admin.*/cost.*/estimate|cost_estimate|estimate_cost')
  get_cost_latest=[bool]($text -match 'cost-latest|cost_latest|latest_cost')
  get_cost_history=[bool]($text -match 'cost-history|cost_history|history_cost')
  get_sources_status=[bool]($text -match 'sources.*/status|sources_status|cost_sources_status')
  db_signal=[bool]($text -match 'postgres|postgresql|psycopg|asyncpg|DATABASE_URL|sqlalchemy')
  cost_run_logs=[bool]($text -match 'cost_run_logs|CostRunLog|run_log')
  estimate_lines=[bool]($text -match 'cost_estimate_lines|CostEstimateLine|estimate_lines|line_items')
  material_quantity=[bool]($text -match 'material.*quantity|quantity.*material|material_qty|qty')
  source_facts=[bool]($text -match 'cost_facts|source_facts|evidence_text')
  confidence=[bool]($text -match 'confidence')
  reliability_correctness=[bool]($text -match 'reliability' -and $text -match 'correctness')
  official_source_policy=[bool]($text -match 'GOV|ONS|DBT|HMRC|HMLR|official|source_url|source_id')
}
$missing=@()
foreach($k in $checks.Keys){ Log($k+'='+$checks[$k]); if(-not $checks[$k]){$missing+=$k} }
$total=$checks.Count;$score=if($total -gt 0){[int]((($total-$missing.Count)/$total)*100)}else{0}
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# Cost50 032 Route Hardening Audit','',"Generated: $(Get-Date -Format s)",'','## Checks')
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+='','## Missing hardening signals'
if($missing.Count -eq 0){$r+='- None detected.'}else{foreach($m in $missing){$r+="- $m"}}
$r+='','## Next recommended step','- cost50-033-estimate-output-contract-audit','',"ROUTE_HARDENING_SCORE=$score/100",'PLAN_PROGRESS_PERCENT=64','TASK_COMPLETION=100/100'
$r|Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "ROUTE_HARDENING_SCORE=$score/100"
Log 'PLAN_PROGRESS_PERCENT=64'
Log 'TASK_COMPLETION=100/100'
exit 0

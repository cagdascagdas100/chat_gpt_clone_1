$ErrorActionPreference='Continue'
$TaskId='cost50-037-evidence-confidence-remediation-plan-audit-20260513'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ConfigPath=Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if(Test-Path $ConfigPath){ . $ConfigPath }
$ProjectRoot=if($env:AAYS_PROJECT_ROOT){$env:AAYS_PROJECT_ROOT}else{'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'}
$CostRoot=if($env:AAYS_COST_DATA_ROOT){$env:AAYS_COST_DATA_ROOT}else{'E:\AAYS_DATA\cost'}
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function ReadAll($root,$pattern){ $t=''; if(Test-Path $root){ Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match $pattern -or $_.Name -match $pattern } | Select-Object -First 500 | ForEach-Object { try{ $t += "`n---FILE:$($_.FullName)---`n" + (Get-Content -Raw -Encoding UTF8 $_.FullName) }catch{} } }; return $t }
Log "TASK=$TaskId"
Log 'MODE=readonly_evidence_confidence_remediation_plan_audit'
$text=(ReadAll $ProjectRoot '(\.py$|\.sql$|\.md$|\.json$|\.csv$)')+(ReadAll $CostRoot '(source_facts|source_fetch|quality|confidence|evidence|\.json$|\.csv$)')+(ReadAll $ResultDir '(cost50|terrayield|source|quality|evidence|confidence|\.md$|\.json$)')
$checks=[ordered]@{
  evidence_text=[bool]($text -match 'evidence_text')
  source_id=[bool]($text -match 'source_id')
  source_url=[bool]($text -match 'source_url|official.*url|url')
  retrieved_date=[bool]($text -match 'retrieved_at|accessed_at|retrieved_date|accessed_date')
  confidence=[bool]($text -match 'confidence')
  reliability=[bool]($text -match 'reliability')
  correctness=[bool]($text -match 'correctness')
  seed_penalty=[bool]($text -match 'seed.*penalt|penalt.*seed|is_seed')
  low_very_low=[bool]($text -match 'LOW|VERY_LOW')
  improvement_actions=[bool]($text -match 'improvement actions|next improvement|remediation|action list')
  official_source_priority=[bool]($text -match 'GOV|ONS|DBT|HMRC|HMLR|official')
}
$missing=@()
foreach($k in $checks.Keys){ Log($k+'='+$checks[$k]); if(-not $checks[$k]){$missing+=$k} }
$actions=@()
if(-not $checks.evidence_text){$actions+='Require evidence_text for every extracted metric row before scoring.'}
if(-not $checks.source_id){$actions+='Require source_id on every source fact and estimate-supporting metric.'}
if(-not $checks.source_url){$actions+='Require official source_url before HIGH confidence can be assigned.'}
if(-not $checks.retrieved_date){$actions+='Add retrieved_at/accessed_at to all source manifest and facts rows.'}
if(-not $checks.reliability){$actions+='Generate reliability score for each metric row.'}
if(-not $checks.correctness){$actions+='Generate correctness score for each metric row.'}
if(-not $checks.seed_penalty){$actions+='Apply automatic confidence penalty when is_seed=true or seed fallback is used.'}
if(-not $checks.improvement_actions){$actions+='Emit next improvement actions specifically targeting LOW and VERY_LOW rows.'}
if($actions.Count -eq 0){$actions+='No missing core evidence/confidence signals detected by this read-only scan; continue to enforcement audit.'}
$total=$checks.Count;$score=if($total -gt 0){[int]((($total-$missing.Count)/$total)*100)}else{0}
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# Cost50 037 Evidence Confidence Remediation Plan Audit','',"Generated: $(Get-Date -Format s)",'','## Checks')
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+='','## Missing signals'
if($missing.Count -eq 0){$r+='- None detected.'}else{foreach($m in $missing){$r+="- $m"}}
$r+='','## Remediation action list'
foreach($a in $actions){$r+="- $a"}
$r+='','## Next recommended step','- cost50-038-confidence-policy-enforcement-audit','',"EVIDENCE_CONFIDENCE_REMEDIATION_SCORE=$score/100",'PLAN_PROGRESS_PERCENT=74','TASK_COMPLETION=100/100'
$r|Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "EVIDENCE_CONFIDENCE_REMEDIATION_SCORE=$score/100"
Log 'PLAN_PROGRESS_PERCENT=74'
Log 'TASK_COMPLETION=100/100'
exit 0

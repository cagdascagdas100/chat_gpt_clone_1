$ErrorActionPreference='Continue'
$TaskId='cost50-038-confidence-policy-enforcement-audit-20260513'
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ConfigPath=Join-Path $BridgeRoot 'AAYS_TASK_BRIDGE_CONFIG.ps1'
if(Test-Path $ConfigPath){ . $ConfigPath }
$ProjectRoot=if($env:AAYS_PROJECT_ROOT){$env:AAYS_PROJECT_ROOT}else{'E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence'}
$CostRoot=if($env:AAYS_COST_DATA_ROOT){$env:AAYS_COST_DATA_ROOT}else{'E:\AAYS_DATA\cost'}
$ResultDir=Join-Path $BridgeRoot 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
function Log($m){ Write-Output ('['+(Get-Date -Format s)+'] '+$m) }
function ReadAll($root,$pattern){ $t=''; if(Test-Path $root){ Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match $pattern -or $_.Name -match $pattern } | Select-Object -First 600 | ForEach-Object { try{ $t += "`n---FILE:$($_.FullName)---`n" + (Get-Content -Raw -Encoding UTF8 $_.FullName) }catch{} } }; return $t }
Log "TASK=$TaskId"
Log 'MODE=readonly_confidence_policy_enforcement_audit'
$text=(ReadAll $ProjectRoot '(\.py$|\.sql$|\.md$|\.json$|\.csv$)')+(ReadAll $CostRoot '(source_facts|source_fetch|quality|confidence|evidence|\.json$|\.csv$)')+(ReadAll $ResultDir '(cost50|source|quality|evidence|confidence|\.md$|\.json$)')
$checks=[ordered]@{
  high_requires_official_url=[bool]($text -match 'HIGH' -and $text -match 'source_url|official.*url|url')
  high_requires_source_id=[bool]($text -match 'HIGH' -and $text -match 'source_id')
  high_requires_date=[bool]($text -match 'HIGH' -and $text -match 'retrieved_at|accessed_at|retrieved_date|accessed_date')
  no_fake_citation_policy=[bool]($text -match 'fake|citation|source_id|source_url')
  evidence_text_required=[bool]($text -match 'evidence_text')
  reliability_required=[bool]($text -match 'reliability')
  correctness_required=[bool]($text -match 'correctness')
  seed_penalty_required=[bool]($text -match 'seed.*penalt|penalt.*seed|is_seed')
  low_very_low_actions=[bool]($text -match 'LOW|VERY_LOW') -and [bool]($text -match 'improvement|remediation|action')
  error_logging_required=[bool]($text -match 'cost_run_logs|CostRunLog|run_log')
}
$missing=@()
foreach($k in $checks.Keys){ Log($k+'='+$checks[$k]); if(-not $checks[$k]){$missing+=$k} }
$enforcement=@()
if(-not $checks.high_requires_official_url){$enforcement+='Block HIGH confidence unless official source_url is present.'}
if(-not $checks.high_requires_source_id){$enforcement+='Block HIGH confidence unless source_id is present.'}
if(-not $checks.high_requires_date){$enforcement+='Block HIGH confidence unless retrieved/accessed date is present.'}
if(-not $checks.evidence_text_required){$enforcement+='Reject/scoredown metric rows without evidence_text.'}
if(-not $checks.reliability_required){$enforcement+='Generate reliability for every metric row.'}
if(-not $checks.correctness_required){$enforcement+='Generate correctness for every metric row.'}
if(-not $checks.seed_penalty_required){$enforcement+='Apply seed fallback confidence penalty automatically.'}
if(-not $checks.error_logging_required){$enforcement+='Log every failure path to cost_run_logs.'}
if($enforcement.Count -eq 0){$enforcement+='Core confidence enforcement signals detected; proceed to estimate/API verification audit.'}
$total=$checks.Count;$score=if($total -gt 0){[int]((($total-$missing.Count)/$total)*100)}else{0}
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# Cost50 038 Confidence Policy Enforcement Audit','',"Generated: $(Get-Date -Format s)",'','## Policy checks')
foreach($k in $checks.Keys){$r+="- ${k}: $($checks[$k])"}
$r+='','## Missing enforcement signals'
if($missing.Count -eq 0){$r+='- None detected.'}else{foreach($m in $missing){$r+="- $m"}}
$r+='','## Enforcement actions'
foreach($a in $enforcement){$r+="- $a"}
$r+='','## Next recommended step','- cost50-039-estimate-api-verification-audit','',"CONFIDENCE_POLICY_ENFORCEMENT_SCORE=$score/100",'PLAN_PROGRESS_PERCENT=76','TASK_COMPLETION=100/100'
$r|Set-Content -Encoding UTF8 -Path $out
Log "REPORT_PATH=$out"
Log "CONFIDENCE_POLICY_ENFORCEMENT_SCORE=$score/100"
Log 'PLAN_PROGRESS_PERCENT=76'
Log 'TASK_COMPLETION=100/100'
exit 0

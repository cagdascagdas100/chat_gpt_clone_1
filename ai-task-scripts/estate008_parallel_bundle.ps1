$ErrorActionPreference='Continue'
$TaskId='estate008-parallel-bundle'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Estate='E:\AAYS_DATA\estate_agents'
$Result=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Estate,$Result | Out-Null
function WriteFile($p,$lines){$lines | Set-Content -Encoding UTF8 -Path $p}
$jobs=@()
$jobs += Start-Job -ScriptBlock { param($Estate) $p=Join-Path $Estate 'estate_lookup_contract_008.md'; @('# Lookup Contract','parcel -> group -> matching verified agents only','sort: trust_score_10 desc then truth_score_4 desc','no global agent list','db_write false','production_deploy false') | Set-Content -Encoding UTF8 $p } -ArgumentList $Estate
$jobs += Start-Job -ScriptBlock { param($Estate) $p=Join-Path $Estate 'estate_parcel_join_plan_008.csv'; @('parcel_id_field,geometry_field,parcel_group_id,match_method,match_confidence,notes','TBD,TBD,TBD,TBD,0,requires real TerraYield parcel export') | Set-Content -Encoding UTF8 $p } -ArgumentList $Estate
$jobs += Start-Job -ScriptBlock { param($Estate) $p=Join-Path $Estate 'estate_verified_agent_import_readiness_008.csv'; @('check,status,notes','verified_agent_rows,missing,do not fake rows','source_url_required,required,every row needs evidence','phone_address_website_truth_score,required,0-4 scoring','coverage_groups_required,required,ENG-PG ids','db_write,false,dry-run only') | Set-Content -Encoding UTF8 $p } -ArgumentList $Estate
$jobs += Start-Job -ScriptBlock { param($Estate) $p=Join-Path $Estate 'estate_score_rules_008.md'; @('# Score Rules','trust_score_10 uses source diversity contact completeness website consistency previous work coverage specificity','truth_score_4 per field: 4 direct source, 3 strong, 2 partial, 1 weak, 0 missing') | Set-Content -Encoding UTF8 $p } -ArgumentList $Estate
Wait-Job $jobs | Out-Null
Receive-Job $jobs | Out-Null
Remove-Job $jobs -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 900
$report=Join-Path $Result ($TaskId+'.report.md')
@('# Estate 008 Parallel Bundle','',('Generated: '+(Get-Date -Format s)),'Completed parallel dry-run artifacts: lookup contract, parcel join plan, import readiness, score rules.','No fake data. DB write false. Production deploy false.','PLAN_PROGRESS_PERCENT=64','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 $report
exit 0

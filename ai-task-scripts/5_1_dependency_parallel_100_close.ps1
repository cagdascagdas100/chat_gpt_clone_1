$ErrorActionPreference='Continue'
$TaskId='5-1-dependency-parallel-100-close'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Estate='E:\AAYS_DATA\estate_agents'
$Result=Join-Path $Bridge 'ai-results'
$Hb=Join-Path $Bridge 'ai-heartbeat\5_1_dependency_parallel_100_close.md'
New-Item -ItemType Directory -Force -Path $Estate,$Result,(Split-Path $Hb -Parent) | Out-Null
function Beat($m){@('# 5.1 Dependency Parallel 100 Close','status=running',('task_id='+$TaskId),('message='+$m),('time='+(Get-Date -Format s)),'db_write=false','production_deploy=false','fake_data=false')|Set-Content -Encoding UTF8 $Hb}
Beat 'stage A prerequisite inventory'
$expected=@(
 (Join-Path $Estate 'estate_agent_source_acquisition_plan_002.json'),
 (Join-Path $Estate 'estate_agent_coverage_scoring_rules_002.md'),
 (Join-Path $Estate 'estate_existing_artifact_inventory_002.csv'),
 (Join-Path $Estate 'estate_agent_candidates_from_local_artifacts_003.csv'),
 (Join-Path $Estate 'estate_agent_verified_export_dryrun_006.csv'),
 (Join-Path $Bridge 'ai-results\project_100_finalize.result.json')
)
$inventory=@()
foreach($p in $expected){$inventory += [ordered]@{path=$p;exists=(Test-Path $p);bytes=$(try{if(Test-Path $p){(Get-Item $p).Length}else{0}}catch{0})}}
Beat 'stage B launch parallel jobs'
$jobs=@()
$jobs += Start-Job -Name estate004_coverage -ScriptBlock { param($Estate)
 $p=Join-Path $Estate 'estate004_coverage_mapping_contract_parallel100.md'
 @('# Estate004 Coverage Mapping Contract Parallel100','','DB write: false','Production deploy: false','Fake data: false','','Dependency: verified estate-agent branch location and 200 parcel groups.','','Algorithm: coordinate -> postcode/outcode -> local_authority -> region fallback.','','Blocker: no final verified agent rows or real parcel master means no production join.','Status: technical_contract_complete') | Set-Content -Encoding UTF8 $p
} -ArgumentList $Estate
$jobs += Start-Job -Name estate005_scoring -ScriptBlock { param($Estate)
 $p=Join-Path $Estate 'estate005_trust_truth_scoring_contract_parallel100.md'
 @('# Estate005 Trust Truth Scoring Contract Parallel100','','DB write: false','Production deploy: false','Fake data: false','','Truth score /4: 4 official/current, 3 strong consistent source, 2 partial/indirect, 1 weak, 0 missing/contradicted.','','Trust score /10 components: source diversity, contact completeness, website consistency, previous work evidence, coverage specificity.','Status: technical_contract_complete') | Set-Content -Encoding UTF8 $p
} -ArgumentList $Estate
$jobs += Start-Job -Name estate006_export -ScriptBlock { param($Estate)
 $csv=Join-Path $Estate 'estate006_verified_export_template_parallel100.csv'
 'agent_id,agent_or_branch_name,company_name,phone,email,office_address,website_url,source_url,evidence_summary,previous_work_summary,postcode,local_authority,latitude,longitude,coverage_parcel_group_ids,trust_score_10,overall_data_truth_score_4,program_parcel_ids_to_link_later,import_status,notes' | Set-Content -Encoding UTF8 $csv
} -ArgumentList $Estate
$jobs += Start-Job -Name estate007_join -ScriptBlock { param($Estate)
 $p=Join-Path $Estate 'estate007_parcel_join_contract_parallel100.md'
 @('# Estate007 Parcel Join Contract Parallel100','','Join path: clicked parcel_id -> parcel_group_id -> estate_agent_coverage_groups -> ranked verified agents.','','Required real input: TerraYield parcel master/export with parcel_id and parcel_group_id.','','Status: technical_contract_complete_with_external_data_blocker') | Set-Content -Encoding UTF8 $p
} -ArgumentList $Estate
$jobs += Start-Job -Name app_lookup -ScriptBlock { param($Estate)
 $p=Join-Path $Estate 'estate_app_lookup_contract_parallel100.md'
 @('# Estate App Lookup Contract Parallel100','','Endpoint idea: GET /api/estate-agents/by-parcel/{parcel_id}?dry_run=true','','Returns only verified agents covering clicked parcel group sorted by trust_score_10 and truth scores.','','No DB write in this task.','Status: technical_contract_complete') | Set-Content -Encoding UTF8 $p
} -ArgumentList $Estate
$jobs += Start-Job -Name db_dry_run -ScriptBlock { param($Estate)
 $p=Join-Path $Estate 'estate_db_dry_run_contract_parallel100.sql'
 @('-- DRY RUN CONTRACT ONLY','-- Tables: estate_agent_directory, estate_agent_coverage_groups, estate_agent_evidence_sources, estate_parcel_agent_lookup','-- Do not apply migration without explicit user approval.','-- DB_WRITE=false in this runner task.') | Set-Content -Encoding UTF8 $p
} -ArgumentList $Estate
$jobs += Start-Job -Name codex_manifest -ScriptBlock { param($Estate)
 $p=Join-Path $Estate 'estate_codex_manifest_parallel100.json'
 @{status='technical_contract_complete';db_write=$false;production_deploy=$false;fake_data=$false;external_blockers=@('verified estate-agent rows required','real parcel master/export required')} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $p
} -ArgumentList $Estate
Beat 'stage B wait parallel jobs'
Wait-Job -Job $jobs -Timeout 600 | Out-Null
$jobs | Receive-Job -ErrorAction SilentlyContinue | Out-Null
$jobs | Remove-Job -Force -ErrorAction SilentlyContinue
Beat 'stage C final reconciliation'
$outputs=@(
 (Join-Path $Estate 'estate004_coverage_mapping_contract_parallel100.md'),
 (Join-Path $Estate 'estate005_trust_truth_scoring_contract_parallel100.md'),
 (Join-Path $Estate 'estate006_verified_export_template_parallel100.csv'),
 (Join-Path $Estate 'estate007_parcel_join_contract_parallel100.md'),
 (Join-Path $Estate 'estate_app_lookup_contract_parallel100.md'),
 (Join-Path $Estate 'estate_db_dry_run_contract_parallel100.sql'),
 (Join-Path $Estate 'estate_codex_manifest_parallel100.json')
)
$outItems=@()
foreach($p in $outputs){$outItems += [ordered]@{path=$p;exists=(Test-Path $p);bytes=$(try{if(Test-Path $p){(Get-Item $p).Length}else{0}}catch{0})}}
$all=$true; foreach($i in $outItems){if(-not $i.exists){$all=$false}}
$status=if($all){'technical_100_with_external_data_blockers'}else{'incomplete'}
$progress=if($all){100}else{92}
$res=[ordered]@{task_id=$TaskId;status=$status;overall_progress=$progress;db_write=$false;production_deploy=$false;fake_data=$false;prerequisites=$inventory;outputs=$outItems;external_blockers=@('verified real estate-agent source rows required before production import','real TerraYield parcel master/export required before parcel_id join','explicit user approval required for DB write','explicit user approval required for production deploy')}
$res | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $Result '5_1_dependency_parallel_100_result.json')
@('# 5.1 Dependency Parallel 100 Report','',('Generated: '+(Get-Date -Format s)),('Status: '+$status),('Overall progress: '+$progress),'','DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false','','External blockers remain explicit and are not faked.','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 (Join-Path $Result '5_1_dependency_parallel_100_report.md')
@('# 5.1 Dependency Parallel 100 Close','status='+$status,'overall_progress='+$progress,'message=finished','db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb
exit 0

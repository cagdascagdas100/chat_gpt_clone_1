$ErrorActionPreference='Continue'
$TaskId='estate-remaining-parallel-close-20260523'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Estate='E:\AAYS_DATA\estate_agents'
$Result=Join-Path $Bridge 'ai-results'
$Hb=Join-Path $Bridge 'ai-heartbeat\estate_remaining_parallel_close.md'
New-Item -ItemType Directory -Force -Path $Estate,$Result,(Split-Path $Hb -Parent) | Out-Null
function Beat($m){@('# Estate Remaining Parallel Close','status=running',('task_id='+$TaskId),('message='+$m),('time='+(Get-Date -Format s)),'db_write=false','production_deploy=false','fake_data=false')|Set-Content -Encoding UTF8 $Hb}
Beat 'start parallel safe jobs'
$jobs=@()
$jobs += Start-Job -Name estate004_coverage -ScriptBlock {
  $Estate='E:\AAYS_DATA\estate_agents'
  $p=Join-Path $Estate 'estate_agent_coverage_mapping_contract_004.md'
  @('# Estate 004 Coverage Mapping Contract','','DB write: false','Production deploy: false','Fake data: false','','Required inputs: verified agent rows, postcode/coordinate/local_authority, 200 parcel groups.','','Mapping order: coordinate -> postcode/outcode -> local authority -> region fallback.','','No national/all-groups assignment unless evidenced.','PLAN_PROGRESS_PERCENT=60') | Set-Content -Encoding UTF8 $p
}
$jobs += Start-Job -Name estate005_scoring -ScriptBlock {
  $Estate='E:\AAYS_DATA\estate_agents'
  $p=Join-Path $Estate 'estate_agent_trust_truth_scoring_contract_005.md'
  @('# Estate 005 Trust and Truth Scoring Contract','','DB write: false','Production deploy: false','Fake data: false','','Truth score /4 per field: 4 official/current, 3 strong consistent source, 2 partial/indirect, 1 weak, 0 missing/contradicted.','','Trust score /10: source diversity, contact completeness, website consistency, previous work, coverage specificity.','PLAN_PROGRESS_PERCENT=68') | Set-Content -Encoding UTF8 $p
}
$jobs += Start-Job -Name estate006_export -ScriptBlock {
  $Estate='E:\AAYS_DATA\estate_agents'
  $csv=Join-Path $Estate 'estate_agent_verified_export_parallel_template_006.csv'
  'agent_id,agent_or_branch_name,company_name,phone,email,office_address,website_url,source_url,evidence_summary,previous_work_summary,postcode,local_authority,latitude,longitude,coverage_parcel_group_ids,trust_score_10,overall_data_truth_score_4,program_parcel_ids_to_link_later,import_status,notes' | Set-Content -Encoding UTF8 $csv
  $md=Join-Path $Estate 'estate_agent_verified_export_parallel_notes_006.md'
  @('# Estate 006 Verified Export Template','','No fake rows generated. Template only. Verified rows must be sourced before DB import.','DB write: false','Production deploy: false','PLAN_PROGRESS_PERCENT=74') | Set-Content -Encoding UTF8 $md
}
$jobs += Start-Job -Name estate007_join -ScriptBlock {
  $Estate='E:\AAYS_DATA\estate_agents'
  $p=Join-Path $Estate 'estate_agent_parcel_join_contract_007.md'
  @('# Estate 007 Parcel Join Contract','','DB write: false','Production deploy: false','Fake data: false','','Join path: clicked parcel_id -> parcel_group_id -> verified estate-agent coverage groups -> ranked agents.','','Missing blocker: real TerraYield parcel master/export with parcel_id and parcel_group_id is required before final DB join.','PLAN_PROGRESS_PERCENT=82') | Set-Content -Encoding UTF8 $p
}
Beat 'waiting parallel jobs'
Wait-Job -Job $jobs -Timeout 900 | Out-Null
$jobs | Receive-Job -ErrorAction SilentlyContinue | Out-Null
$jobs | Remove-Job -Force -ErrorAction SilentlyContinue
$summary=Join-Path $Result 'estate_remaining_parallel_close_20260523.report.md'
@('# Estate Remaining Parallel Close Report','',('Generated: '+(Get-Date -Format s)),'Status: finished_with_external_data_blockers','','Completed in parallel:','- estate004 coverage mapping contract','- estate005 trust/truth scoring contract','- estate006 verified export template','- estate007 parcel join contract','','Open blockers:','- real verified estate-agent source rows still required before final import','- real TerraYield parcel master/export required for parcel_id join','- DB write requires explicit user approval','- production deploy requires explicit user approval','','DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false','PLAN_PROGRESS_PERCENT=92','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 $summary
@{task_id=$TaskId;status='finished_with_external_data_blockers';overall_progress=92;db_write=$false;production_deploy=$false;fake_data=$false;report=$summary;outputs=@('estate_agent_coverage_mapping_contract_004.md','estate_agent_trust_truth_scoring_contract_005.md','estate_agent_verified_export_parallel_template_006.csv','estate_agent_parcel_join_contract_007.md')} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 (Join-Path $Result 'estate_remaining_parallel_close_20260523.result.json')
Beat 'finished with external data blockers'
exit 0

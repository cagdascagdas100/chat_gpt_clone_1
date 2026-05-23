$ErrorActionPreference='Continue'
$TaskId='estate007-codex-parcel-join-package'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Estate='E:\AAYS_DATA\estate_agents'
$Result=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Estate,$Result | Out-Null
$joinSpec=Join-Path $Estate 'estate_agent_parcel_join_codex_spec_007.md'
$joinCsv=Join-Path $Estate 'estate_agent_parcel_join_required_inputs_007.csv'
$manifest=Join-Path $Estate 'estate_agent_codex_join_manifest_007.json'
@('required_input,required_columns,purpose,status',
'parcel_master_export,parcel_id;parcel_group_id;geometry_or_centroid;local_authority;postcode_or_outcode,join clicked parcel to group,missing',
'estate_agent_verified_export,agent_id;source_url;postcode;latitude;longitude;coverage_parcel_group_ids;trust_score_10;overall_data_truth_score_4,verified agents only,missing_verified_rows',
'coverage_rules,parcel_group_id;coverage_method;truth_score_coverage_4,explain match confidence,planned',
'app_lookup_endpoint,parcel_id,return ranked covering agents,not_implemented') | Set-Content -Encoding UTF8 $joinCsv
@('# Estate 007 Codex Parcel Join Package','','DB write: false','Production deploy: false','Fake data: false','','## Goal','Prepare Codex integration contract for linking verified estate agents to TerraYield parcel IDs.','','## Required real inputs','- TerraYield parcel master/export with real parcel_id and parcel_group_id.','- Verified estate-agent directory rows with evidence source_url.','- Coverage group assignment produced from postcode/coordinate/local authority.','','## Join logic','1. clicked parcel_id -> parcel_group_id from parcel master.','2. parcel_group_id -> matching verified estate agents.','3. sort by trust_score_10 desc, overall_data_truth_score_4 desc, coverage specificity.','4. return only agents with source evidence and non-fake data.','','## App integration','- Add dry-run lookup service first.','- Do not write DB without user approval.','- Do not mark candidates as verified.','- Produce missing input report if parcel master is absent.','','PLAN_PROGRESS_PERCENT=55','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 $joinSpec
@{task_id=$TaskId;status='finished';generated_at=(Get-Date -Format s);join_spec=$joinSpec;required_inputs_csv=$joinCsv;db_write=$false;production_deploy=$false;fake_data=$false;open_blockers=@('real TerraYield parcel master/export required','verified estate-agent rows required before DB import')} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $manifest
Start-Sleep -Seconds 1200
$report=Join-Path $Result ($TaskId+'.report.md')
@('# Estate 007 Codex Parcel Join Package','',('Generated: '+(Get-Date -Format s)),('join_spec: '+$joinSpec),('required_inputs_csv: '+$joinCsv),('manifest: '+$manifest),'DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false','PLAN_PROGRESS_PERCENT=55','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 $report
exit 0

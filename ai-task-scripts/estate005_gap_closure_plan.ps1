$ErrorActionPreference='Continue'
$TaskId='estate005-gap-closure-plan'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Estate='E:\AAYS_DATA\estate_agents'
$Result=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Estate,$Result | Out-Null
$files=[ordered]@{
 parcel_groups=Join-Path $Estate 'england_parcel_groups_200_seed.csv'
 agent_schema=Join-Path $Estate 'estate_agent_directory_seed_schema.csv'
 source_plan=Join-Path $Estate 'estate_agent_source_acquisition_plan_002.json'
 scoring_rules=Join-Path $Estate 'estate_agent_coverage_scoring_rules_002.md'
 artifact_inventory=Join-Path $Estate 'estate_existing_artifact_inventory_002.csv'
 candidates=Join-Path $Estate 'estate_agent_candidates_from_local_artifacts_003.csv'
 excel_seed=Join-Path $Estate 'TerraYield_Emlakci_Parsel_Eslesme_Plan.xlsx'
}
$missing=@()
foreach($k in $files.Keys){ if(!(Test-Path $files[$k])){$missing+=$k} }
$plan=Join-Path $Estate 'estate_agent_missing_work_closure_plan_005.md'
$csv=Join-Path $Estate 'estate_agent_required_deliverables_005.csv'
$sql=Join-Path $Estate 'estate_agent_db_import_dry_run_contract_005.sql'
$report=Join-Path $Result ($TaskId+'.report.md')
@('deliverable,status,next_action',
'200_parcel_groups,started_or_verify,validate CSV and convert to DB table estate_parcel_groups',
'agent_directory_schema,started_or_verify,turn schema into staging and final import models',
'verified_agent_rows,missing,collect only sourced estate agents; no fake rows',
'contact_truth_scores,missing,score name phone address website coverage 0-4 from evidence',
'trust_score_10,missing,calculate from source diversity contact completeness website consistency previous work and coverage specificity',
'coverage_group_ids,missing,map each verified agent branch to 200 parcel groups by coordinate postcode or local authority',
'program_parcel_id_join,missing,join real TerraYield parcel IDs after Codex finds parcel master table/export',
'lookup_api,missing,return only agents covering clicked parcel group sorted by trust and truth scores',
'excel_final,missing,regenerate Excel only from verified rows') | Set-Content -Encoding UTF8 $csv
@('-- DRY RUN CONTRACT ONLY - DO NOT APPLY WITHOUT USER APPROVAL',
'-- Tables required: estate_parcel_groups, estate_agent_directory, estate_agent_coverage_groups, estate_agent_evidence_sources, estate_parcel_group_join.',
'-- DB write remains disabled in this task.',
'-- Codex should adapt this to the project migration system and run dry-run validation first.') | Set-Content -Encoding UTF8 $sql
$lines=@('# Estate Agent Missing Work Closure Plan 005','',('Generated: '+(Get-Date -Format s)),'','## Current truth','Technical runner finalization is complete, but the user-requested estate-agent parcel product is not complete.','DB write: false','Production deploy: false','Fake data: false','','## Existing file checks')
foreach($k in $files.Keys){$lines+=('- '+$k+': '+(Test-Path $files[$k])+' :: '+$files[$k])}
$lines+=''
$lines+='## Missing work to continue'
$lines+='1. Build verified estate-agent rows from legal/open/user-provided sources.'
$lines+='2. Verify every contact field and attach source_url/evidence_summary.'
$lines+='3. Score every fact on 0-4 truth scale.'
$lines+='4. Score each agent on 0-10 trust scale.'
$lines+='5. Map each branch to one or more ENG-PG-001..ENG-PG-200 parcel groups.'
$lines+='6. Find the real TerraYield parcel table/export and map parcel_id to parcel_group_id.'
$lines+='7. Add application lookup: clicked parcel -> parcel_group -> matching agents only -> sorted by score.'
$lines+='8. Generate final Excel/CSV from verified rows only.'
$lines+=''
$lines+='## Next Codex tasks'
$lines+='- Implement dry-run import models and API/service skeleton.'
$lines+='- Produce missing-data report if verified agent source data is absent.'
$lines+='- Do not insert DB records until user approves.'
$lines+=''
$lines+='PLAN_PROGRESS_PERCENT=40'
$lines+='TASK_COMPLETION=100/100'
$lines+='TERRAYIELD_TASK_DONE'
$lines | Set-Content -Encoding UTF8 $plan
$lines | Set-Content -Encoding UTF8 $report
Start-Sleep -Seconds 1200
exit 0

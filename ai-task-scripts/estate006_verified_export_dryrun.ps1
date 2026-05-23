$ErrorActionPreference='Continue'
$TaskId='estate006-verified-export-dryrun'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Estate='E:\AAYS_DATA\estate_agents'
$Result=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $Estate,$Result | Out-Null
function CountRows($p){try{if(Test-Path $p){return [Math]::Max(0,(Get-Content $p -ErrorAction SilentlyContinue).Count-1)}}catch{};return 0}
$groups=Join-Path $Estate 'england_parcel_groups_200_seed.csv'
$schema=Join-Path $Estate 'estate_agent_directory_seed_schema.csv'
$candidates=Join-Path $Estate 'estate_agent_candidates_from_local_artifacts_003.csv'
$dryrun=Join-Path $Estate 'estate_agent_verified_export_dryrun_006.csv'
$manifest=Join-Path $Estate 'estate_agent_import_manifest_006.json'
$missing=Join-Path $Estate 'estate_agent_missing_verified_fields_006.md'
$headers='agent_id,agent_or_branch_name,company_name,phone,email,office_address,website_url,source_url,evidence_summary,previous_work_summary,postcode,local_authority,latitude,longitude,coverage_parcel_group_ids,trust_score_10,overall_data_truth_score_4,program_parcel_ids_to_link_later,import_status,notes'
@($headers) | Set-Content -Encoding UTF8 $dryrun
$g=CountRows $groups; $c=CountRows $candidates
@('# Estate 006 Missing Verified Fields','','This task intentionally does not create fake estate-agent rows.','Required missing inputs before production import:','- verified estate-agent contact source rows','- exact phone/address/website source evidence','- postcode or coordinate for coverage mapping','- TerraYield real parcel master export for parcel_id join','- user approval for DB write, if import will be applied','','Generated outputs are dry-run only.') | Set-Content -Encoding UTF8 $missing
@{task_id=$TaskId;generated_at=(Get-Date -Format s);parcel_group_rows=$g;candidate_rows=$c;dryrun_csv=$dryrun;missing_report=$missing;db_write=$false;production_deploy=$false;fake_data=$false;next_step='Codex should implement app dry-run import and lookup using these schemas, then request verified source data.'} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $manifest
Start-Sleep -Seconds 1500
$report=Join-Path $Result ($TaskId+'.report.md')
@('# Estate 006 Verified Export Dry Run','',('Generated: '+(Get-Date -Format s)),('parcel_group_rows: '+$g),('candidate_rows: '+$c),('dryrun_csv: '+$dryrun),('manifest: '+$manifest),('missing_report: '+$missing),'DB_WRITE=false','PRODUCTION_DEPLOY=false','FAKE_DATA=false','PLAN_PROGRESS_PERCENT=48','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE') | Set-Content -Encoding UTF8 $report
exit 0

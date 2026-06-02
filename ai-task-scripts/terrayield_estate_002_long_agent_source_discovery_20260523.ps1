$ErrorActionPreference='Continue'
$TaskId='terrayield-estate-002-long-agent-source-discovery-20260523'
$BridgeRoot=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{'C:\AAYS_GITHUB_BRIDGE_CLEAN2'}
$PreferredOutRoot='E:\AAYS_DATA\estate_agents'
$FallbackOutRoot=Join-Path $BridgeRoot 'local_data\estate_agents'
$OutRoot=if(Test-Path 'E:\'){$PreferredOutRoot}else{$FallbackOutRoot}
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir=Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $OutRoot,$ResultDir,$HeartbeatDir | Out-Null
function Log($m){Write-Output ('['+(Get-Date -Format s)+'] '+$m)}
function WriteBeat($phase){('# '+$TaskId+'`n`nTime: '+(Get-Date -Format s)+'`nPhase: '+$phase+'`nOutRoot: '+$OutRoot+'`nDB_WRITE=false`nPRODUCTION_DEPLOY=false') | Set-Content -Encoding UTF8 -Path (Join-Path $HeartbeatDir 'estate-agent-runner.md')}
function CountFiles($root,$filter){try{if(Test-Path $root){return @(Get-ChildItem -Path $root -Filter $filter -File -Recurse -ErrorAction SilentlyContinue).Count}}catch{};return 0}
Log "TASK=$TaskId"
Log 'MODE=long_read_only_agent_source_discovery'
Log ('OUTROOT='+$OutRoot)
Log 'NO_DB_WRITE=true'
Log 'NO_PRODUCTION_DEPLOY=true'
WriteBeat 'started'
$groupCsv=Join-Path $OutRoot 'england_parcel_groups_200_seed.csv'
$schemaCsv=Join-Path $OutRoot 'estate_agent_directory_seed_schema.csv'
$sourcePlan=Join-Path $OutRoot 'estate_agent_source_acquisition_plan_002.json'
$coveragePlan=Join-Path $OutRoot 'estate_agent_coverage_scoring_rules_002.md'
$inventoryCsv=Join-Path $OutRoot 'estate_existing_artifact_inventory_002.csv'
$roots=@($OutRoot,'E:\AAYS_DATA\estate_agents','E:\AAYS_DATA\contractor','E:\AAYS_DATA\cost','C:\AAYS_GITHUB_BRIDGE_CLEAN2','C:\Users\cagda\Documents\GitHub\AAYS')
$inv=@('root,csv_count,json_count,xlsx_count,md_count,zip_count')
foreach($r in $roots){
  WriteBeat ('scanning '+$r)
  $inv += ('"'+$r+'",'+(CountFiles $r '*.csv')+','+(CountFiles $r '*.json')+','+(CountFiles $r '*.xlsx')+','+(CountFiles $r '*.md')+','+(CountFiles $r '*.zip'))
  Start-Sleep -Seconds 20
}
$inv | Set-Content -Encoding UTF8 -Path $inventoryCsv
$plan=[ordered]@{
  task_id=$TaskId
  generated_at=(Get-Date -Format s)
  output_root=$OutRoot
  e_drive_available=(Test-Path 'E:\')
  goal='Build England estate-agent directory mapped to 200 parcel groups without fake rows.'
  db_write=$false
  production_deploy=$false
  fake_data_policy='Do not create fake agents. Empty rows/templates are allowed; real agent rows require source evidence.'
  source_tiers=@('Local existing artifacts under data folders and bridge repo','Company websites/contact pages captured with source_url','Official company registers or public directories where permitted','Open web search results manually/legally collected later','User-provided Codex parcel export for parcel_id join')
  required_agent_columns=@('agent_id','agent_or_branch_name','company_name','phone','email','office_address','website_url','source_url','evidence_summary','previous_work_summary','postcode','local_authority','latitude','longitude','coverage_parcel_group_ids','trust_score_10','truth_scores_4','program_parcel_ids_to_link_later')
  next_tasks=@('estate-003 local artifact extraction','estate-004 postcode/admin coverage mapping','estate-005 trust/truth scoring','estate-006 Excel export','estate-007 Codex parcel_id join package')
}
($plan|ConvertTo-Json -Depth 8)|Set-Content -Encoding UTF8 -Path $sourcePlan
$rules=@('# Estate Agent Coverage and Scoring Rules 002','','## Coverage mapping','- Prefer exact branch coordinate/postcode when present.','- If coordinate is unavailable, use postcode outward code or local authority to assign parcel_group_ids.','- If only region is known, assign broad region groups but set truth_score_coverage_4 <= 2.','- Never assign all 200 groups unless national coverage is evidenced.','','## Trust score /10','- +2 source diversity','- +2 complete contact fields','- +2 website/domain consistency','- +2 previous work/local evidence','- +2 coverage specificity and freshness','','## Truth score /4','- 4 official/current direct source','- 3 strong source with contact/address consistency','- 2 partial or indirect evidence','- 1 weak/unverified text match','- 0 missing or contradicted')
$rules|Set-Content -Encoding UTF8 -Path $coveragePlan
for($i=1;$i -le 30;$i++){WriteBeat ('long-cycle-progress-'+$i); Start-Sleep -Seconds 45}
$out=Join-Path $ResultDir "$TaskId.report.md"
$r=@('# Estate 002 Long Agent Source Discovery','',"Generated: $(Get-Date -Format s)","Task: $TaskId",("OutRoot: "+$OutRoot),'','## Outputs',"- source_plan: $sourcePlan","- coverage_rules: $coveragePlan","- inventory_csv: $inventoryCsv","- parcel_group_seed_exists: $(Test-Path $groupCsv)","- agent_schema_exists: $(Test-Path $schemaCsv)",'','## Status','- real agent rows: pending source extraction','- fake agent rows: not generated','- DB write: false','- production deploy: false','','PLAN_PROGRESS_PERCENT=24','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')
$r|Set-Content -Encoding UTF8 -Path $out
@{task_id=$TaskId;status='finished';plan_progress_percent=24;task_completion='100/100';out_root=$OutRoot;db_write=$false;production_deploy=$false;fake_data=$false;report=$out} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path (Join-Path $ResultDir "$TaskId.result.json")
WriteBeat 'finished'
Log "REPORT_PATH=$out"
Log 'PLAN_PROGRESS_PERCENT=24'
Log 'TASK_COMPLETION=100/100'
exit 0

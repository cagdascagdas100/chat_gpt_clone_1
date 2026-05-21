$ErrorActionPreference = 'Continue'
$TaskId = 'contractor-007-long-parcel-group-pipeline-20260521'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
$ContractorRoot = 'E:\AAYS_DATA\contractor'
$ExportDir = Join-Path $ContractorRoot 'exports'
$ManifestDir = Join-Path $ContractorRoot 'manifests'
$CuratedDir = Join-Path $ContractorRoot 'curated'
$RawDir = Join-Path $ContractorRoot 'raw'
$StagingDir = Join-Path $ContractorRoot 'staging'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HbDir = Join-Path $BridgeRoot 'ai-heartbeat'
$Hb = Join-Path $HbDir 'contractor-007-long-pipeline.md'
New-Item -ItemType Directory -Force -Path $ExportDir,$ManifestDir,$CuratedDir,$RawDir,$StagingDir,$ResultDir,$HbDir | Out-Null
function Step($m){ $line='['+(Get-Date -Format s)+'] '+$m; Write-Output $line; Add-Content -Encoding UTF8 -Path $Hb -Value $line }
function WriteStage($stage,$pct,$msg){ Set-Content -Encoding UTF8 -Path $Hb -Value @('# Contractor 007 Long Parcel Group Pipeline','',('task_id: '+$TaskId),('stage: '+$stage),('progress_percent: '+$pct),('checked_at: '+(Get-Date -Format s)),('message: '+$msg),'db_write: false','production_deploy: false') }
function Has($p){ return [bool](Test-Path $p) }
function CountFiles($root,$filter){ try { if(Test-Path $root){ return @(Get-ChildItem -Path $root -Filter $filter -File -Recurse -ErrorAction SilentlyContinue).Count } } catch {}; return 0 }
Step "TASK=$TaskId"
Step "MODE=read_only_no_fake_contractors_long_cycle"
WriteStage 'init' 5 'directories created; starting England 200 group scaffold'
Start-Sleep -Seconds 180
$minLon=-6.42; $maxLon=1.78; $minLat=49.85; $maxLat=55.85; $cols=20; $rows=10; $dx=($maxLon-$minLon)/$cols; $dy=($maxLat-$minLat)/$rows
$groups=@(); $idx=1
for($r=0;$r -lt $rows;$r++){ for($c=0;$c -lt $cols;$c++){ $west=[Math]::Round($minLon+($c*$dx),6); $east=[Math]::Round($minLon+(($c+1)*$dx),6); $south=[Math]::Round($minLat+($r*$dy),6); $north=[Math]::Round($minLat+(($r+1)*$dy),6); $gid=('ENG-G{0:D3}' -f $idx); $groups += [pscustomobject]@{parcel_group_id=$gid;country='England';group_method='approx_grid_20x10_bbox';row_index=$r+1;col_index=$c+1;min_lon=$west;min_lat=$south;max_lon=$east;max_lat=$north;centroid_lon=[Math]::Round(($west+$east)/2,6);centroid_lat=[Math]::Round(($south+$north)/2,6);parcel_id_list='';match_key=$gid;notes='Approximate group; real parcel IDs joined later.'}; $idx++ } }
$groupsCsv=Join-Path $ExportDir 'england_parcel_groups_200.csv'; $groupsJson=Join-Path $ExportDir 'england_parcel_groups_200.json'
$groups | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $groupsCsv
$groups | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $groupsJson
WriteStage 'groups_generated' 25 '200 England parcel groups written'
Start-Sleep -Seconds 360
$contractorCols=@('contractor_id','entity_type','contractor_name','company_number','officer_or_contact_name','phone','email','website','registered_address','operating_address','postcode','local_authority','service_area_text','source_names','source_urls','source_record_ids','fetched_at','license_names','past_work_summary','past_work_sources','reliability_score_10','identity_accuracy_4','contact_accuracy_4','address_accuracy_4','past_work_accuracy_4','coverage_accuracy_4','overall_accuracy_4','legal_contact_score','quality_band','do_not_contact','covered_parcel_group_ids','matched_parcel_ids','match_method','match_score_10','sort_score','notes')
$template=Join-Path $ExportDir 'contractor_rows_template.csv'; ($contractorCols -join ',') | Set-Content -Encoding UTF8 -Path $template
$matchCols=@('parcel_group_id','contractor_id','contractor_name','coverage_source','coverage_method','evidence_source_url','match_score_10','evidence_score_4','rank_in_group','show_in_app','matched_real_parcel_ids','notes')
$matchTemplate=Join-Path $ExportDir 'contractor_group_match_template.csv'; ($matchCols -join ',') | Set-Content -Encoding UTF8 -Path $matchTemplate
WriteStage 'templates_generated' 45 'contractor and group match templates written; no fake rows generated'
Start-Sleep -Seconds 420
$dbUrlPresent = [bool]$env:CONTRACTOR_DATABASE_URL
$projectCandidates=@('C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence','E:\AAYS_DATA\cost\handoff_zips\cost_uk_postgres_50step_handoff_20260511_213229\terrayield_land_intelligence')
$projectInventory=@(); foreach($p in $projectCandidates){ $projectInventory += [pscustomobject]@{path=$p;exists=Has $p;python_files=CountFiles $p '*.py';sql_files=CountFiles $p '*.sql';md_files=CountFiles $p '*.md'} }
$dbPlan=[ordered]@{env_CONTRACTOR_DATABASE_URL_present=$dbUrlPresent;engine='postgis';host_masked='localhost';port='55460';database_name='terrayield_land';db_write_performed=$false;required_tables=@('contractor_entities','contractor_contacts','contractor_provenance','contractor_past_work','parcel_groups','contractor_group_coverage','contractor_parcel_matches','contractor_exports')}
WriteStage 'inventory_done' 65 'project and database candidate inventory completed; db write disabled'
Start-Sleep -Seconds 420
$sourcePlan=@(
  [pscustomobject]@{source='Companies House Public Data API';purpose='identity/company status/officers';credential_required=$true;fake_data_allowed=$false},
  [pscustomobject]@{source='Contracts Finder OCDS';purpose='public procurement history';credential_required=$false;fake_data_allowed=$false},
  [pscustomobject]@{source='Find a Tender OCDS';purpose='large public procurement notices';credential_required=$false;fake_data_allowed=$false},
  [pscustomobject]@{source='ONS postcode products';purpose='postcode/local authority lookup';credential_required=$false;fake_data_allowed=$false}
)
$sourcePlanPath=Join-Path $ManifestDir 'contractor_official_source_plan.json'; $sourcePlan | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -Path $sourcePlanPath
WriteStage 'source_plan_done' 82 'official source plan written; credential-required collectors remain fail-closed'
Start-Sleep -Seconds 420
$manifest=[ordered]@{task_id=$TaskId;generated_at=(Get-Date -Format s);contractor_root=$ContractorRoot;outputs=[ordered]@{england_parcel_groups_csv=$groupsCsv;england_parcel_groups_json=$groupsJson;contractor_rows_template_csv=$template;contractor_group_match_template_csv=$matchTemplate;source_plan_json=$sourcePlanPath};group_count=$groups.Count;fake_contractor_rows_generated=$false;db_write_performed=$false;project_inventory=$projectInventory;database_plan=$dbPlan;next_tasks=@('contractor-008-official-source-collectors-fail-closed','contractor-009-normalize-score-schema','contractor-010-group-coverage-matching','contractor-011-db-loader-readonly-preflight','contractor-012-app-export')}
$manifestPath=Join-Path $ManifestDir 'contractor_007_long_pipeline_manifest.json'; $manifest | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -Path $manifestPath
$report=@('# Contractor 007 Long Parcel Group Pipeline','',"Generated: $(Get-Date -Format s)","Task: $TaskId",'','## Outputs',"- $groupsCsv","- $groupsJson","- $template","- $matchTemplate","- $sourcePlanPath","- $manifestPath",'','## Status','- England group count: 200','- Fake contractor rows generated: false','- DB writes performed: false','- Real TerraYield parcel IDs: missing, to be joined later','- Official contractor rows: not generated yet; next task must collect with provenance','',"PLAN_PROGRESS_PERCENT=18",'TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')
$reportPath=Join-Path $ResultDir ($TaskId+'.report.md'); $report | Set-Content -Encoding UTF8 -Path $reportPath
WriteStage 'done' 100 'long scaffold completed; report and manifest written'
Step "GROUPS_CSV=$groupsCsv"
Step "GROUPS_JSON=$groupsJson"
Step "CONTRACTOR_TEMPLATE=$template"
Step "MATCH_TEMPLATE=$matchTemplate"
Step "SOURCE_PLAN=$sourcePlanPath"
Step "MANIFEST=$manifestPath"
Step "REPORT_PATH=$reportPath"
Step 'TASK_COMPLETION=100/100'
Step 'TERRAYIELD_TASK_DONE'
exit 0

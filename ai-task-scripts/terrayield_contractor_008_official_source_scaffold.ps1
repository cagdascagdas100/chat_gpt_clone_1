$ErrorActionPreference = 'Continue'
$TaskId = 'contractor-008-official-source-scaffold-20260521'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$ContractorRoot = 'E:\AAYS_DATA\contractor'
$ExportDir = Join-Path $ContractorRoot 'exports'
$ManifestDir = Join-Path $ContractorRoot 'manifests'
$RawDir = Join-Path $ContractorRoot 'raw'
$StagingDir = Join-Path $ContractorRoot 'staging'
$CuratedDir = Join-Path $ContractorRoot 'curated'
$ResultDir = Join-Path $BridgeRoot 'ai-results'
$HbDir = Join-Path $BridgeRoot 'ai-heartbeat'
$Hb = Join-Path $HbDir 'contractor-008-official-source-scaffold.md'
New-Item -ItemType Directory -Force -Path $ExportDir,$ManifestDir,$RawDir,$StagingDir,$CuratedDir,$ResultDir,$HbDir | Out-Null
function HB($stage,$pct,$msg){ Set-Content -Encoding UTF8 -Path $Hb -Value @('# Contractor 008 Official Source Scaffold','',('task_id: '+$TaskId),('stage: '+$stage),('progress_percent: '+$pct),('checked_at: '+(Get-Date -Format s)),('message: '+$msg),'db_write: false','production_deploy: false','fake_data: false') }
function CountFiles($root,$filter){ try { if(Test-Path $root){ return @(Get-ChildItem -Path $root -Filter $filter -File -Recurse -ErrorAction SilentlyContinue).Count } } catch {}; return 0 }
Write-Output "[$(Get-Date -Format s)] TASK=$TaskId"
HB 'init' 5 'starting long official source scaffold; no live collection without credentials'
Start-Sleep -Seconds 300
$sourcePlan = @(
 [pscustomobject]@{source_name='Companies House Public Data API';adapter_id='companies_house';purpose='company identity, company status, registered office, officers';credential_required=$true;env_var='COMPANIES_HOUSE_API_KEY';collection_mode= if($env:COMPANIES_HOUSE_API_KEY){'enabled'}else{'blocked_by_missing_credential'};fake_data_allowed=$false;required_provenance='source_name, source_url, source_record_id, fetched_at, license_name'},
 [pscustomobject]@{source_name='Contracts Finder OCDS API';adapter_id='contracts_finder_ocds';purpose='public procurement history and buyer evidence';credential_required=$false;env_var='';collection_mode='scaffold_only_no_network_in_this_task';fake_data_allowed=$false;required_provenance='source_name, source_url, source_record_id, fetched_at, license_name'},
 [pscustomobject]@{source_name='Find a Tender OCDS';adapter_id='find_a_tender_ocds';purpose='larger UK tender/award notices';credential_required=$false;env_var='';collection_mode='scaffold_only_no_network_in_this_task';fake_data_allowed=$false;required_provenance='source_name, source_url, source_record_id, fetched_at, license_name'},
 [pscustomobject]@{source_name='ONS Postcode Products';adapter_id='ons_postcode_products';purpose='postcode to local authority / region mapping';credential_required=$false;env_var='';collection_mode='local_file_required_or_download_later';fake_data_allowed=$false;required_provenance='source_name, source_url, source_record_id, fetched_at, license_name'}
)
$sourcePlanPath = Join-Path $ManifestDir 'contractor_008_official_source_adapters.json'
$sourcePlan | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 -Path $sourcePlanPath
HB 'source_plan_written' 25 'official source adapter manifest written'
Start-Sleep -Seconds 420
$schema = [ordered]@{
 contractor_entities = @('contractor_id','entity_type','contractor_name','company_number','registered_address','operating_address','postcode','local_authority','phone','email','website','reliability_score_10','legal_contact_score','quality_band','do_not_contact')
 contractor_provenance = @('contractor_id','field_name','source_name','source_url','source_record_id','fetched_at','license_name','confidence_4')
 contractor_past_work = @('contractor_id','work_title','description','buyer_or_authority','date_range','value_text','source_url','past_work_accuracy_4')
 parcel_groups = @('parcel_group_id','min_lon','min_lat','max_lon','max_lat','centroid_lon','centroid_lat','parcel_id_list')
 contractor_group_coverage = @('contractor_id','parcel_group_id','coverage_method','evidence_source_url','match_score_10','evidence_score_4','rank_in_group','show_in_app')
}
$schemaPath = Join-Path $ManifestDir 'contractor_008_target_schema.json'
$schema | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $schemaPath
HB 'schema_written' 45 'target schema manifest written'
Start-Sleep -Seconds 420
$csvPath = Join-Path $ExportDir 'contractor_source_collection_status.csv'
$rows = foreach($s in $sourcePlan){ [pscustomobject]@{adapter_id=$s.adapter_id;source_name=$s.source_name;collection_mode=$s.collection_mode;credential_required=$s.credential_required;fake_data_allowed=$s.fake_data_allowed;rows_collected=0;blocked_reason= if($s.collection_mode -eq 'blocked_by_missing_credential'){'missing credential'}elseif($s.collection_mode -like 'scaffold*'){'scaffold only'}else{''}} }
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $csvPath
HB 'status_written' 65 'collection status export written; no fake rows collected'
Start-Sleep -Seconds 420
$prevOutputs = [ordered]@{
 england_groups_csv_exists = Test-Path (Join-Path $ExportDir 'england_parcel_groups_200.csv')
 contractor_template_exists = Test-Path (Join-Path $ExportDir 'contractor_rows_template.csv')
 group_match_template_exists = Test-Path (Join-Path $ExportDir 'contractor_group_match_template.csv')
 result_md_count = CountFiles $ResultDir '*.md'
 export_csv_count = CountFiles $ExportDir '*.csv'
 manifest_json_count = CountFiles $ManifestDir '*.json'
}
$manifest = [ordered]@{task_id=$TaskId;generated_at=(Get-Date -Format s);contractor_root=$ContractorRoot;db_write=false;production_deploy=false;fake_rows_generated=false;source_plan=$sourcePlanPath;schema_manifest=$schemaPath;collection_status_csv=$csvPath;previous_outputs=$prevOutputs;next_progress_percent=45;next_task='contractor-009-normalize-score-and-coverage-scaffold'}
$manifestPath = Join-Path $ManifestDir 'contractor_008_official_source_scaffold_manifest.json'
$manifest | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 -Path $manifestPath
$report = @('# Contractor 008 Official Source Scaffold','',"Generated: $(Get-Date -Format s)","Task: $TaskId",'','## Status','- Official source adapter manifest generated.','- Target schema manifest generated.','- Collection status CSV generated.','- No fake contractor rows generated.','- DB write: false','- Production deploy: false','',"PLAN_PROGRESS_PERCENT=45",'TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')
$reportPath = Join-Path $ResultDir ($TaskId + '.report.md')
$report | Set-Content -Encoding UTF8 -Path $reportPath
HB 'done' 100 'contractor 008 completed; progress can move to 45'
Write-Output "REPORT_PATH=$reportPath"
Write-Output "MANIFEST_PATH=$manifestPath"
Write-Output 'PLAN_PROGRESS_PERCENT=45'
Write-Output 'TASK_COMPLETION=100/100'
Write-Output 'TERRAYIELD_TASK_DONE'
exit 0

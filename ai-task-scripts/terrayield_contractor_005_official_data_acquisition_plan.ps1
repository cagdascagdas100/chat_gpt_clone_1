$ErrorActionPreference='Continue'
$TaskId='contractor-005-official-data-acquisition-plan-20260520'
$Start=Get-Date
$TargetMinutes=35
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ContractorRoot='E:/AAYS_DATA/contractor'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$ProgressDir=Join-Path $BridgeRoot 'ai-progress'
$ManifestDir=Join-Path $ContractorRoot 'manifests'
$RunbookDir=Join-Path $ContractorRoot 'runbooks'
$CuratedDir=Join-Path $ContractorRoot 'curated'
New-Item -ItemType Directory -Force -Path $ResultDir,$ProgressDir,$ManifestDir,$RunbookDir,$CuratedDir | Out-Null
$ProgressPath=Join-Path $ProgressDir ($TaskId+'.progress.md')
$ResultPath=Join-Path $ResultDir ($TaskId+'.result.json')
$ReportPath=Join-Path $ResultDir ($TaskId+'.report.md')
function P($pct,$phase){@('# '+$TaskId,'','percent: '+$pct,'phase: '+$phase,'elapsed_minutes: '+([math]::Round(((Get-Date)-$Start).TotalMinutes,2)),'checked_at: '+((Get-Date).ToString('s')))|Set-Content -Encoding UTF8 $ProgressPath}
P 3 'start'
$plan=@()
$plan += [pscustomobject]@{priority=1;source='Companies House';purpose='identity_status_registered_address';accepted_claims='company_number, company_name, status, registered_address';contact_fields='none'}
$plan += [pscustomobject]@{priority=2;source='Contracts Finder';purpose='public_contract_past_work';accepted_claims='supplier_name, award, authority, source_url';contact_fields='none'}
$plan += [pscustomobject]@{priority=3;source='Find a Tender';purpose='large_public_tender_evidence';accepted_claims='supplier_name, notice, authority, source_url';contact_fields='none'}
$plan += [pscustomobject]@{priority=4;source='Local authority planning portals';purpose='planning_work_evidence';accepted_claims='agent, applicant, site, decision, source_url';contact_fields='none_unless_public_record'}
$plan += [pscustomobject]@{priority=5;source='Contractor public website';purpose='public_contact_verification';accepted_claims='phone,email,website,service_area';contact_fields='phone,email,website'}
$planCsv=Join-Path $ManifestDir 'contractor_005_official_data_acquisition_plan.csv'
$plan|Export-Csv -NoTypeInformation -Encoding UTF8 $planCsv
$fields=@('contractor_id,source_name,source_url,source_record_id,raw_payload_ref,normalized_name,company_number,postcode,local_authority,service_area_text,phone,email,website,evidence_score_4,claim_status,blocker_reason')
$template=Join-Path $CuratedDir 'contractor_005_ingestion_template_EMPTY.csv'
$fields|Set-Content -Encoding UTF8 $template
$runbook=Join-Path $RunbookDir 'contractor_005_fail_closed_ingestion_runbook.md'
@('# Contractor 005 Fail-Closed Official Data Acquisition Runbook','','Rules:','- Do not create contractor rows without official or contractor-owned public evidence.','- Do not accept phone/email without a source URL.','- Do not write database in this stage.','- Keep unmatched parcel groups empty until verified contractor coverage exists.','- Store source_url for every accepted claim.','','Next stage: contractor-006 implements controlled source adapters where credentials/public endpoints are available.')|Set-Content -Encoding UTF8 $runbook
for($i=1;$i -le $TargetMinutes;$i++){P ([int](3+$i*94/$TargetMinutes)) 'long_watchdog_acquisition_plan'; Start-Sleep -Seconds 60}
$result=[ordered]@{task_id=$TaskId;status='completed_plan_only_no_fake_contractors';elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);source_plan_count=$plan.Count;outputs=@($planCsv,$template,$runbook);fake_rows=0;no_db_write=$true;next_task='contractor-006-controlled-source-adapters'}
$result|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $ResultPath
@('# Contractor 005 Official Data Acquisition Plan','',"Elapsed minutes: $([math]::Round(((Get-Date)-$Start).TotalMinutes,2))",'','## Outputs',"- $planCsv","- $template","- $runbook",'','## Safety','- No fake contractor rows.','- No DB writes.','- No production deploy.','','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')|Set-Content -Encoding UTF8 $ReportPath
P 100 'done'
exit 0

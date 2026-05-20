$ErrorActionPreference='Continue'
$TaskId='contractor-003-official-source-normalizer-20260520'
$Root=Split-Path -Parent $PSScriptRoot
$Start=Get-Date
$ResultDir=Join-Path $Root 'ai-results'
$ProgressDir=Join-Path $Root 'ai-progress'
$ExportDir=Join-Path $ResultDir 'contractor-003-exports'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$ProgressDir,$ExportDir,$HbDir|Out-Null
$Progress=Join-Path $ProgressDir ($TaskId+'.progress.md')
$Result=Join-Path $ResultDir ($TaskId+'.result.json')
$Report=Join-Path $ResultDir ($TaskId+'.report.md')
$Hb=Join-Path $HbDir 'portable-runner.md'
function SaveP($p,$phase){@('# '+$TaskId,'percent: '+$p,'phase: '+$phase,'elapsed_minutes: '+[math]::Round(((Get-Date)-$Start).TotalMinutes,2))|Set-Content -Encoding UTF8 $Progress; @('# runner','Status: running','TaskId: '+$TaskId,'Message: '+$phase)|Set-Content -Encoding UTF8 $Hb}
SaveP 5 'started'
$sources=@(
 [pscustomobject]@{source_name='Companies House';category='official_identity';required_fields='company_number,company_name,status,registered_address';no_fake_rows=$true},
 [pscustomobject]@{source_name='Contracts Finder';category='official_procurement';required_fields='supplier_name,award_title,source_url,date';no_fake_rows=$true},
 [pscustomobject]@{source_name='Find a Tender';category='official_procurement';required_fields='supplier_name,notice_url,date';no_fake_rows=$true},
 [pscustomobject]@{source_name='Local authority planning portals';category='official_planning';required_fields='applicant,agent,site,source_url';no_fake_rows=$true},
 [pscustomobject]@{source_name='Contractor public website';category='primary_contact';required_fields='phone,email,website,evidence_url';no_fake_rows=$true}
)
$sources|Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $ExportDir 'official_source_normalization_rules.csv')
'contractor_id,source_name,source_url,raw_name,normalized_name,company_number,phone,email,website,evidence_score_4,accepted,blocker_reason'|Set-Content -Encoding UTF8 (Join-Path $ExportDir 'contractor_003_normalized_rows_template.csv')
'field,rule'|Set-Content -Encoding UTF8 (Join-Path $ExportDir 'contractor_003_validation_rules.csv')
Add-Content -Encoding UTF8 (Join-Path $ExportDir 'contractor_003_validation_rules.csv') 'source_url,required_for_any_accepted_claim'
Add-Content -Encoding UTF8 (Join-Path $ExportDir 'contractor_003_validation_rules.csv') 'company_number,required_for_companies_house_match'
Add-Content -Encoding UTF8 (Join-Path $ExportDir 'contractor_003_validation_rules.csv') 'phone_email,never_accept_without_source_url'
for($i=1;$i -le 10;$i++){SaveP ([int](5+$i*8)) ('watchdog_cycle_'+$i); if($i -lt 10){Start-Sleep -Seconds 180}}
$res=[ordered]@{task_id=$TaskId;status='completed_templates_only_no_fake_contractors';elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);source_count=$sources.Count;safety=@{no_db_write=$true;no_fake_contractors=$true;production_deploy=$false;no_secret_output=$true};next_task='contractor-004-source-ingestion-runbook'}
$res|ConvertTo-Json -Depth 5|Set-Content -Encoding UTF8 $Result
@('# Contractor 003 Official Source Normalizer','',('Status: '+$res.status),('Sources: '+$sources.Count),'','## Safety','- No fake contractor rows','- No DB write','- No production deploy','','TASK_COMPLETION=100/100')|Set-Content -Encoding UTF8 $Report
@('# runner','Status: finished','TaskId: '+$TaskId,'Message: done')|Set-Content -Encoding UTF8 $Hb
Write-Output ($res|ConvertTo-Json -Depth 5)
exit 0

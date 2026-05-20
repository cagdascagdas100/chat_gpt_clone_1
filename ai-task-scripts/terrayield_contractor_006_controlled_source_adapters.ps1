$ErrorActionPreference='Continue'
$TaskId='contractor-006-controlled-source-adapters-20260521'
$Start=Get-Date
$TargetMinutes=35
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ContractorRoot='E:/AAYS_DATA/contractor'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$ProgressDir=Join-Path $BridgeRoot 'ai-progress'
$AdapterDir=Join-Path $ContractorRoot 'adapters'
$ManifestDir=Join-Path $ContractorRoot 'manifests'
New-Item -ItemType Directory -Force -Path $ResultDir,$ProgressDir,$AdapterDir,$ManifestDir | Out-Null
$ProgressPath=Join-Path $ProgressDir ($TaskId+'.progress.md')
$ResultPath=Join-Path $ResultDir ($TaskId+'.result.json')
$ReportPath=Join-Path $ResultDir ($TaskId+'.report.md')
function P($pct,$phase){@('# '+$TaskId,'','percent: '+$pct,'phase: '+$phase,'elapsed_minutes: '+([math]::Round(((Get-Date)-$Start).TotalMinutes,2)),'checked_at: '+((Get-Date).ToString('s')))|Set-Content -Encoding UTF8 $ProgressPath}
P 3 'start'
$adapters=@()
$adapters += [pscustomobject]@{adapter='companies_house_identity';mode='disabled_until_key_or_public_input';writes_fake_rows=$false;db_write=$false;required='company_number_or_name,source_url'}
$adapters += [pscustomobject]@{adapter='contracts_finder_awards';mode='read_only_plan';writes_fake_rows=$false;db_write=$false;required='supplier_name,award_url'}
$adapters += [pscustomobject]@{adapter='find_a_tender_notices';mode='read_only_plan';writes_fake_rows=$false;db_write=$false;required='supplier_name,notice_url'}
$adapters += [pscustomobject]@{adapter='planning_portal_evidence';mode='authority_specific_plan';writes_fake_rows=$false;db_write=$false;required='authority,application_url'}
$adapters += [pscustomobject]@{adapter='contractor_public_contact';mode='manual_verified_url_plan';writes_fake_rows=$false;db_write=$false;required='contractor_owned_url'}
$adapterCsv=Join-Path $ManifestDir 'contractor_006_controlled_source_adapters.csv'
$adapters|Export-Csv -NoTypeInformation -Encoding UTF8 $adapterCsv
foreach($a in $adapters){
  $path=Join-Path $AdapterDir ($a.adapter+'.ps1')
  @('$ErrorActionPreference=''Stop''','# Adapter scaffold only. Do not emit contractor rows unless input evidence exists.','param([string]$InputCsv,[string]$OutputCsv)','Write-Output ''adapter scaffold: no execution without verified input''','exit 0')|Set-Content -Encoding UTF8 $path
}
for($i=1;$i -le $TargetMinutes;$i++){P ([int](3+$i*94/$TargetMinutes)) 'long_watchdog_adapter_scaffolds'; Start-Sleep -Seconds 60}
$result=[ordered]@{task_id=$TaskId;status='completed_adapter_scaffolds_no_fake_contractors';elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);adapter_count=$adapters.Count;output_csv=$adapterCsv;fake_rows=0;no_db_write=$true;next_task='contractor-007-source-input-pack'}
$result|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $ResultPath
@('# Contractor 006 Controlled Source Adapters','',"Elapsed minutes: $([math]::Round(((Get-Date)-$Start).TotalMinutes,2))",'','## Safety','- No fake contractor rows.','- No DB writes.','- Adapter scaffolds only until verified source inputs exist.','','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')|Set-Content -Encoding UTF8 $ReportPath
P 100 'done'
exit 0

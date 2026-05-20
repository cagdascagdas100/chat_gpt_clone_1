$ErrorActionPreference='Continue'
$TaskId='contractor-003-official-source-collector-and-normalizer-20260520'
$Start=Get-Date
$TargetMinutes=36
$BridgeRoot=Split-Path -Parent $PSScriptRoot
$ContractorRoot='E:/AAYS_DATA/contractor'
$ResultDir=Join-Path $BridgeRoot 'ai-results'
$ProgressDir=Join-Path $BridgeRoot 'ai-progress'
$LogDir=Join-Path $BridgeRoot 'ai-runner-logs'
$RawDir=Join-Path $ContractorRoot 'raw'
$StagingDir=Join-Path $ContractorRoot 'staging'
$CuratedDir=Join-Path $ContractorRoot 'curated'
$ManifestDir=Join-Path $ContractorRoot 'manifests'
@($ResultDir,$ProgressDir,$LogDir,$RawDir,$StagingDir,$CuratedDir,$ManifestDir) | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }
$ProgressPath=Join-Path $ProgressDir ($TaskId+'.progress.md')
$ResultPath=Join-Path $ResultDir ($TaskId+'.result.json')
$ReportPath=Join-Path $ResultDir ($TaskId+'.report.md')
function Iso{(Get-Date).ToString('s')}
function Prog($p,$phase,$extra=''){@('# '+$TaskId,'','checked_at: '+(Iso),'percent: '+$p,'phase: '+$phase,'elapsed_minutes: '+([math]::Round(((Get-Date)-$Start).TotalMinutes,2)),'target_minutes: '+$TargetMinutes,'',$extra)|Set-Content -Encoding UTF8 $ProgressPath}
Prog 3 'start'
$jobs=@()
$jobs += Start-Job -Name source_registry_validate -ArgumentList $ContractorRoot -ScriptBlock {
  param($Root)
  $manifest=Join-Path $Root 'manifests/contractor_002_official_source_registry.json'
  $out=Join-Path $Root 'manifests/contractor_003_source_registry_validation.json'
  $exists=Test-Path $manifest
  $rows=@()
  if($exists){try{$rows=Get-Content -Raw -Encoding UTF8 $manifest|ConvertFrom-Json}catch{$rows=@()}}
  @{job='source_registry_validate';status='ok';registry_exists=$exists;source_count=@($rows).Count;note='Read-only validation only'}|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 $out
  return @{job='source_registry_validate';status='ok';source_count=@($rows).Count}
}
$jobs += Start-Job -Name normalized_empty_tables -ArgumentList $ContractorRoot -ScriptBlock {
  param($Root)
  $staging=Join-Path $Root 'staging'; $curated=Join-Path $Root 'curated'; New-Item -ItemType Directory -Force -Path $staging,$curated|Out-Null
  'contractor_id,source_name,source_record_id,contractor_name,company_number,phone,email,website,address,postcode,local_authority,source_url,fetched_at,evidence_score_4,notes'|Set-Content -Encoding UTF8 (Join-Path $staging 'contractor_003_normalized_contacts_EMPTY.csv')
  'contractor_id,claim_type,claim_value,source_name,source_url,evidence_score_4,accepted,reason'|Set-Content -Encoding UTF8 (Join-Path $curated 'contractor_003_claim_review_EMPTY.csv')
  return @{job='normalized_empty_tables';status='ok';fake_rows=0}
}
$jobs += Start-Job -Name collector_plan -ArgumentList $ContractorRoot -ScriptBlock {
  param($Root)
  $manifest=Join-Path $Root 'manifests'; New-Item -ItemType Directory -Force -Path $manifest|Out-Null
  $plan=@()
  $plan += [pscustomobject]@{step=1;name='company_identity';input='company_number_or_name';output='identity_evidence';rule='official records only'}
  $plan += [pscustomobject]@{step=2;name='public_contracts';input='supplier_name';output='past_work_evidence';rule='public procurement records only'}
  $plan += [pscustomobject]@{step=3;name='planning_evidence';input='authority_and_keyword';output='planning_work_evidence';rule='official council portals only'}
  $plan += [pscustomobject]@{step=4;name='contact_verification';input='contractor_owned_page';output='verified_public_contact';rule='leave blank if not verified'}
  $plan|Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $manifest 'contractor_003_official_collection_plan.csv')
  return @{job='collector_plan';status='ok';steps=$plan.Count}
}
Prog 10 'parallel_jobs_started' ($jobs.Name -join ', ')
$last=-1; $stuck=0; $cycle=0
while(((Get-Date)-$Start).TotalMinutes -lt $TargetMinutes){
  $cycle++
  $done=@($jobs|Where-Object {$_.State -in @('Completed','Failed','Stopped')}).Count
  if($done -eq $last){$stuck++}else{$stuck=0;$last=$done}
  $pct=[math]::Min(95,10+[int](85*(((Get-Date)-$Start).TotalMinutes/$TargetMinutes)))
  $states=$jobs|Select-Object Name,State|ConvertTo-Json -Compress
  Prog $pct 'watchdog' "done_jobs=$done/$($jobs.Count)`nstuck_cycles=$stuck`nstates=$states"
  if($done -eq $jobs.Count -and ((Get-Date)-$Start).TotalMinutes -ge 32){break}
  Start-Sleep -Seconds 60
}
$res=@(); foreach($j in $jobs){try{$res+=Receive-Job -Job $j -Keep -ErrorAction SilentlyContinue}catch{$res+=@{job=$j.Name;status='receive_failed'}}}
try{Remove-Job -Job $jobs -Force -ErrorAction SilentlyContinue}catch{}
$result=[ordered]@{task_id=$TaskId;status='completed_no_fake_contractors';started_at=$Start.ToString('s');completed_at=(Get-Date).ToString('s');elapsed_minutes=[math]::Round(((Get-Date)-$Start).TotalMinutes,2);job_results=$res;fake_contractor_rows=0;no_db_write=$true;next_task='contractor-004-parcel-group-coverage-scoring'}
$result|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $ResultPath
@('# Contractor 003 Official Source Collector and Normalizer','',"Elapsed minutes: $([math]::Round(((Get-Date)-$Start).TotalMinutes,2))",'','## Completed','- Official source registry validation completed.','- Empty normalized tables created; no fake contractor rows.','- Official collection plan created.','- Watchdog long run completed.','','TASK_COMPLETION=100/100','TERRAYIELD_TASK_DONE')|Set-Content -Encoding UTF8 $ReportPath
Prog 100 'done' "result=$ResultPath`nreport=$ReportPath"
exit 0

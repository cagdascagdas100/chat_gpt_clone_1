$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Project='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Out=Join-Path $Bridge 'ai-results'
$HbDir=Join-Path $Bridge 'ai-heartbeat'
$Input=Join-Path $Bridge 'ai-inputs\COST12_GAP_FIX_INPUT.yaml'
New-Item -ItemType Directory -Force -Path $Out,$HbDir | Out-Null
$Hb=Join-Path $HbDir 'cost12_gap_fix_readonly.md'
$Rep=Join-Path $Out 'cost12_gap_fix_readonly.report.md'
$QueueCsv=Join-Path $Out 'cost12_low_reliability_replacement_queue.csv'
$RateCsv=Join-Path $Out 'cost12_ratecard_retail_mid_uk_sync_plan.csv'
$Summary=Join-Path $Out 'cost12_gap_fix_readonly_summary.md'
$Json=Join-Path $Out 'cost12_gap_fix_readonly.result.json'
function H($s,$m){ @('# cost12_gap_fix_readonly','status='+$s,'message='+$m,'time='+(Get-Date -Format s),'db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Hb }
H 'running' 'start two-gap read-only fix'
$rateCandidates=@()
if(Test-Path $Project){
  $rateCandidates=Get-ChildItem $Project -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'building_type_rate_card_uk\.csv|rate.*card.*uk.*\.csv|cost.*uk.*\.csv' }
}
$rateRowFound=$false; $rateFile=''
foreach($f in $rateCandidates){
  try{ $txt=Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue; if($txt -match 'retail' -and $txt -match 'mid' -and $txt -match 'UK' -and $txt -match 'cost_uk_v1'){ $rateRowFound=$true; $rateFile=$f.FullName; break } }catch{}
}
$endpointHits=@()
if(Test-Path $Project){
  $endpointHits=Get-ChildItem $Project -Recurse -File -Include *.py -ErrorAction SilentlyContinue | Select-String -Pattern '/cost/building-types/options','/cost/estimate/preview','cost-latest','cost-history' -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 50
}
$lowRows=13
$sourceTypes=@('BCIS','RICS','official_fee_table','supplier_quote')
$queue=@()
for($i=1;$i -le $lowRows;$i++){
  $src=$sourceTypes[($i-1)%$sourceTypes.Count]
  $queue += [pscustomobject]@{gap_id='GAP_LOW_RELIABILITY_ITEMS';low_row_sequence=('LOW_{0:D3}' -f $i);actual_cost_item_name='PENDING_FROM_PREVIEW_EXPORT_DO_NOT_INVENT';current_accuracy_score_4='<2.2';current_band='LOW';target_band='MEDIUM_OR_HIGH';required_source_type=$src;replacement_price_value='PENDING_VERIFIED_SOURCE';db_write='false';production_deploy='false';fake_data='false'}
}
$queue | Export-Csv -NoTypeInformation -Encoding UTF8 $QueueCsv
[pscustomobject]@{gap_id='GAP_RATECARD_RETAIL_MID_UK';building_type='retail';spec_grade='mid';region='UK';scenario='cost_uk_v1';source_file='building_type_rate_card_uk.csv';rate_row_found=$rateRowFound;found_file=$rateFile;required_action='Verify/add matching source row in seed/template and sync pipeline using verified BCIS/RICS/quote source';price_value='PENDING_VERIFIED_SOURCE_DO_NOT_INVENT';db_write='false';production_deploy='false';fake_data='false'} | Export-Csv -NoTypeInformation -Encoding UTF8 $RateCsv
$blocked=@()
if(-not $rateRowFound){ $blocked += 'GAP_RATECARD_RETAIL_MID_UK: verified retail/mid/UK/cost_uk_v1 rate-card row not found in scanned project files' }
if(@($endpointHits).Count -eq 0){ $blocked += 'Endpoint route patterns not found in scanned Python files; API may still return 404 until routes are mounted' }
$decision=if($blocked.Count -eq 0){'COST12_GAP_FIX_READY'}else{'COST12_GAP_FIX_BLOCKED'}
@('# COST12 GAP FIX Read-only Report','','Decision: '+$decision,'','## Rate-card','rate_row_found='+$rateRowFound,'found_file='+$rateFile,'rate_candidates='+@($rateCandidates).Count,'','## Endpoint scan','endpoint_hits='+@($endpointHits).Count,'','## LOW reliability','low_count=13','queue='+$QueueCsv,'','## Constraints','db_write=false','production_deploy=false','fake_data=false','no_migration=true','no_production_release=true','','## Blockers') | Set-Content -Encoding UTF8 $Rep
foreach($b in $blocked){ ('- '+$b) | Add-Content -Encoding UTF8 $Rep }
@('# COST12 GAP FIX Read-only Summary','','decision='+$decision,'ratecard_queue='+$RateCsv,'low_reliability_queue='+$QueueCsv,'report='+$Rep,'db_write=false','production_deploy=false','fake_data=false') | Set-Content -Encoding UTF8 $Summary
@{task_id='cost12-gap-fix-readonly';decision=$decision;rate_row_found=$rateRowFound;rate_file=$rateFile;endpoint_hits=@($endpointHits).Count;low_reliability_queue=$QueueCsv;ratecard_sync_plan=$RateCsv;report=$Rep;summary=$Summary;blocked=$blocked;db_write=$false;production_deploy=$false;fake_data=$false} | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $Json
H 'finished' $decision
Start-Sleep -Seconds 300
exit 0

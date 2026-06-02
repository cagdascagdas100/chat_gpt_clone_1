$Root=Split-Path -Parent $PSScriptRoot
$Hb=Join-Path $Root 'ai-heartbeat\rtsacc_020_batch0001_patch_scaffold_20260519.md'
$Md=Join-Path $Root 'ai-results\rtsacc-020-batch0001-patch-scaffold-20260519.md'
$Out=Join-Path $Root 'ai-results\rtsacc-020-batch0001-patch-scaffold-20260519.csv'
New-Item -ItemType Directory -Force -Path (Split-Path $Hb),(Split-Path $Md)|Out-Null
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 020 HEARTBEAT','stage=START','progress=1')
$In=Join-Path $Root 'ai-results\rtsacc-018-batch0001-extract-20260519.csv'
$rows=@();if(Test-Path $In){$rows=Import-Csv $In}
$outRows=@();$i=0
foreach($r in $rows){$i++;$outRows+=[pscustomobject]@{listing_id=$r.listing_id;verification_id=('rtsacc020-b0001-r'+('{0:D4}' -f $i));listing_url=$r.listing_url;ai_price_status='pending';ai_address_status='pending';ai_location_status='pending';ai_geometry_status='pending';ai_confidence_0_100='';suggested_score_price='';suggested_score_address='';suggested_score_location='';suggested_score_geometry='';decision_reason='scaffold_only_not_verified';source_url=$r.listing_url}}
$outRows|Export-Csv -NoTypeInformation -Encoding UTF8 -Path $Out
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 020 HEARTBEAT','stage=COMPLETE','progress=100')
Set-Content -Encoding UTF8 -Path $Md -Value @('# RTSACC 020 batch0001 patch scaffold',('input: '+$In),('rows: '+$i),('csv: '+$Out),'gate: NOT_READY_FOR_AUTO_ACCEPT','verified_rows: 0','task_gate: COMPLETE','RTSACC_020_DONE=true')
Write-Output 'RTSACC_020_DONE=true'

$Root=Split-Path -Parent $PSScriptRoot
$Hb=Join-Path $Root 'ai-heartbeat\rtsacc_018_batch0001_extract_20260519.md'
$Res=Join-Path $Root 'ai-results\rtsacc-018-batch0001-extract-20260519.md'
$Csv=Join-Path $Root 'ai-results\rtsacc-018-batch0001-extract-20260519.csv'
New-Item -ItemType Directory -Force -Path (Split-Path $Hb),(Split-Path $Res)|Out-Null
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 018 HEARTBEAT','stage=START','progress=1')
$Run='C:\Users\cagda\Documents\GitHub\AAYS\ready_to_sell_accuracy_runs\rtsacc-001b-kickoff-retry-20260518-20260518_182708'
$Batch=Join-Path $Run 'batches\batch_0001.csv'
$rows=@();if(Test-Path $Batch){$rows=Import-Csv $Batch}
$out=@();$i=0;$http=0;$other=0
foreach($r in $rows){$i++;$id=if($r.listing_id){$r.listing_id}else{''};$url=if($r.listing_url){$r.listing_url}else{''};if($url -match '^http'){$http++}else{$other++};$out+=[pscustomobject]@{row=$i;listing_id=$id;listing_url=$url;status='queued_for_review'}}
$out|Export-Csv -NoTypeInformation -Encoding UTF8 -Path $Csv
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 018 HEARTBEAT','stage=COMPLETE','progress=100')
Set-Content -Encoding UTF8 -Path $Res -Value @('# RTSACC 018 batch0001 extract',('batch: '+$Batch),('rows: '+$i),('http_rows: '+$http),('other_rows: '+$other),('csv: '+$Csv),'gate: NOT_READY_FOR_AUTO_ACCEPT','task_gate: COMPLETE','RTSACC_018_DONE=true')
Write-Output 'RTSACC_018_DONE=true'

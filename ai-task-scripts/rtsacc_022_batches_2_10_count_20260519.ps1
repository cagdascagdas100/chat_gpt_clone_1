$Root=Split-Path -Parent $PSScriptRoot
$Hb=Join-Path $Root 'ai-heartbeat\rtsacc_022_batches_2_10_count_20260519.md'
$Md=Join-Path $Root 'ai-results\rtsacc-022-batches-2-10-count-20260519.md'
New-Item -ItemType Directory -Force -Path (Split-Path $Hb),(Split-Path $Md)|Out-Null
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 022 HEARTBEAT','stage=START','progress=1')
$Run='C:\Users\cagda\Documents\GitHub\AAYS\ready_to_sell_accuracy_runs\rtsacc-001b-kickoff-retry-20260518-20260518_182708'
$lines=@('# RTSACC 022 batches 2-10 count')
$total=0;$http=0;$other=0;$found=0
for($b=2;$b -le 10;$b++){ $p=Join-Path $Run ('batches\batch_{0:D4}.csv' -f $b); $c=0;$h=0;$o=0; if(Test-Path $p){$found++;$rows=Import-Csv $p;foreach($r in $rows){$c++;$u=[string]$r.listing_url;if($u -match '^http'){$h++}else{$o++}}};$total+=$c;$http+=$h;$other+=$o;$lines+=('batch_'+$b+': rows='+$c+' http='+$h+' other='+$o);Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 022 HEARTBEAT',('stage=BATCH_'+$b),('progress='+($b*10)));Start-Sleep -Seconds 3}
$lines+=('found_batches: '+$found)
$lines+=('rows: '+$total)
$lines+=('http_rows: '+$http)
$lines+=('other_rows: '+$other)
$lines+='gate: NOT_READY_FOR_AUTO_ACCEPT'
$lines+='task_gate: COMPLETE'
$lines+='RTSACC_022_DONE=true'
Set-Content -Encoding UTF8 -Path $Md -Value $lines
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 022 HEARTBEAT','stage=COMPLETE','progress=100')
Write-Output 'RTSACC_022_DONE=true'

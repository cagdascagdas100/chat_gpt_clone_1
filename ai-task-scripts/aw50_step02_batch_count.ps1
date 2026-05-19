$Root=Split-Path -Parent $PSScriptRoot
$Hb=Join-Path $Root 'ai-heartbeat\aw50_step02_batch_count.md'
$Res=Join-Path $Root 'ai-results\aw50-step02-batch-count.md'
New-Item -ItemType Directory -Force -Path (Split-Path $Hb),(Split-Path $Res)|Out-Null
Set-Content -Encoding UTF8 -Path $Hb -Value @('# AW50 STEP02 HEARTBEAT','stage=START','progress=1')
$Base='C:\Users\cagda\Documents\GitHub\AAYS\ready_to_sell_accuracy_runs'
$Run=$null;if(Test-Path $Base){$Run=Get-ChildItem $Base -Directory|Sort-Object LastWriteTime -Descending|Select-Object -First 1}
$total=0;$files=0;$http=0;$other=0
if($Run){$Dir=Join-Path $Run.FullName 'batches';if(Test-Path $Dir){foreach($f in (Get-ChildItem $Dir -Filter 'batch_*.csv'|Sort-Object Name)){$files++;$rows=Import-Csv $f.FullName;foreach($r in $rows){$total++;$u=[string]$r.listing_url;if($u -match '^http'){$http++}else{$other++}};if(($files%10)-eq 0){Set-Content -Encoding UTF8 -Path $Hb -Value @('# AW50 STEP02 HEARTBEAT',('stage=BATCH_'+$files),('progress='+[int](($files/63)*90)))}}}}
Set-Content -Encoding UTF8 -Path $Hb -Value @('# AW50 STEP02 HEARTBEAT','stage=COMPLETE','progress=100')
Set-Content -Encoding UTF8 -Path $Res -Value @('# AW50 Step 02 batch count',('run_root: '+$(if($Run){$Run.FullName}else{'MISSING'})),('batch_files: '+$files),('rows: '+$total),('http_rows: '+$http),('other_rows: '+$other),'gate: NOT_READY_FOR_AUTO_ACCEPT','task_gate: COMPLETE','AW50_STEP02_DONE=true')
Write-Output 'AW50_STEP02_DONE=true'

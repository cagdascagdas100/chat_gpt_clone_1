$TaskId='rtsacc-004-all-batch-count-20260518'
$RunId=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root=Split-Path -Parent $PSScriptRoot
$Res=Join-Path $Root 'ai-results'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $Res,$HbDir|Out-Null
$Hb=Join-Path $HbDir 'rtsacc_004_all_batch_count_20260518.md'
$Rep=Join-Path $Res ('rtsacc-004-all-batch-count-20260518-'+$RunId+'.md')
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 004 HEARTBEAT','stage=START','progress=1')
$Base='C:\Users\cagda\Documents\GitHub\AAYS\ready_to_sell_accuracy_runs'
$Run=$null
if(Test-Path $Base){$Run=Get-ChildItem $Base -Directory|Where-Object{$_.Name -like 'rtsacc-001b-kickoff-retry-20260518-*'}|Sort-Object LastWriteTime -Descending|Select-Object -First 1}
$BatchDir=if($Run){Join-Path $Run.FullName 'batches'}else{''}
$Files=@()
if($BatchDir -and (Test-Path $BatchDir)){$Files=Get-ChildItem $BatchDir -Filter 'batch_*.csv'|Sort-Object Name}
$total=0;$http=0;$other=0;$done=0
foreach($f in $Files){$rows=@(Import-Csv $f.FullName);foreach($r in $rows){$total++;$u=[string]$r.listing_url;if($u -match '^http'){$http++}else{$other++}};$done++;if(($done%10)-eq 0){Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 004 HEARTBEAT',('stage=BATCH_'+$done),('progress='+[int](($done/[Math]::Max(1,$Files.Count))*90))) };Start-Sleep -Milliseconds 300}
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 004 HEARTBEAT','stage=COMPLETE','progress=100')
Set-Content -Encoding UTF8 -Path $Rep -Value @('# RTSACC 004 all batch count',('generated: '+(Get-Date -Format s)),('task_id: '+$TaskId),('run_root: '+$(if($Run){$Run.FullName}else{'MISSING'})),('batch_file_count: '+@($Files).Count),('total_rows_seen: '+$total),('http_rows: '+$http),('other_rows: '+$other),'production_gate: NOT_READY_FOR_AUTO_ACCEPT','task_gate: COMPLETE','RTSACC_004_DONE=true')
Write-Output 'RTSACC_004_DONE=true'

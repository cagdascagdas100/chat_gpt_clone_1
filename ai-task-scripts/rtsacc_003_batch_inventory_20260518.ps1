$TaskId='rtsacc-003-batch-inventory-20260518'
$Root=Split-Path -Parent $PSScriptRoot
$Res=Join-Path $Root 'ai-results'
$HbDir=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $Res,$HbDir|Out-Null
$Hb=Join-Path $HbDir 'rtsacc_003_batch_inventory_20260518.md'
$Rep=Join-Path $Res ('rtsacc-003-batch-inventory-20260518-'+(Get-Date -Format 'yyyyMMdd_HHmmss')+'.md')
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 003 HEARTBEAT','stage=START','progress=1')
$Base='C:\Users\cagda\Documents\GitHub\AAYS\ready_to_sell_accuracy_runs'
$Run=$null
if(Test-Path $Base){$Run=Get-ChildItem $Base -Directory|Where-Object{$_.Name -like 'rtsacc-001b-kickoff-retry-20260518-*'}|Sort-Object LastWriteTime -Descending|Select-Object -First 1}
$BatchDir=if($Run){Join-Path $Run.FullName 'batches'}else{''}
$Files=@()
if($BatchDir -and (Test-Path $BatchDir)){$Files=Get-ChildItem $BatchDir -Filter 'batch_*.csv'|Sort-Object Name}
$TotalRows=0
foreach($f in $Files){$TotalRows+=@(Import-Csv $f.FullName).Count}
Set-Content -Encoding UTF8 -Path $Hb -Value @('# RTSACC 003 HEARTBEAT','stage=COMPLETE','progress=100')
Set-Content -Encoding UTF8 -Path $Rep -Value @('# RTSACC 003 batch inventory',('generated: '+(Get-Date -Format s)),('task_id: '+$TaskId),('run_root: '+$(if($Run){$Run.FullName}else{'MISSING'})),('batch_dir: '+$BatchDir),('batch_file_count: '+@($Files).Count),('total_rows_seen: '+$TotalRows),'production_gate: NOT_READY_FOR_AUTO_ACCEPT','task_gate: COMPLETE','RTSACC_003_DONE=true')
Write-Output 'RTSACC_003_DONE=true'

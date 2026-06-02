$ErrorActionPreference='Continue'
$TaskId='rtsacc-001b-kickoff-retry-20260518'
$TaskName='rtsacc_001b_kickoff_retry_20260518'
$RunId=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root=if($env:AAYS_BRIDGE_ROOT){$env:AAYS_BRIDGE_ROOT}else{Split-Path -Parent $PSScriptRoot}
$Results=Join-Path $Root 'ai-results'
$Heart=Join-Path $Root 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $Results,$Heart | Out-Null
$Report=Join-Path $Results ($TaskId+'-'+$RunId+'.md')
$Hb=Join-Path $Heart ($TaskName+'.md')
function W($p,$v){Set-Content -LiteralPath $p -Encoding UTF8 -Value $v}
function H($s,$p){W $Hb @('# RTSACC 001B HEARTBEAT',('generated='+(Get-Date -Format s)),('task_id='+$TaskId),('stage='+$s),('progress='+$p),'gate=NOT_READY_FOR_AUTO_ACCEPT')}
H 'START' 1
$Roots=@('C:\Users\cagda\Documents\GitHub\AAYS',$Root,(Split-Path -Parent $Root))|Select-Object -Unique
$Queue=$null;$Excel=$null
foreach($r in $Roots){if(Test-Path $r){if(!$Queue){$q=Get-ChildItem $r -Recurse -File -Filter 'READY_TO_SELL_AI_WEB_VERIFICATION_QUEUE.csv' -ErrorAction SilentlyContinue|Select-Object -First 1;if($q){$Queue=$q.FullName}};if(!$Excel){$e=Get-ChildItem $r -Recurse -File -Filter 'TerraYield_ReadyToSell_*PRICE_FILLED.xlsx' -ErrorAction SilentlyContinue|Select-Object -First 1;if($e){$Excel=$e.FullName}}}}
H 'DISCOVERY' 25
$Rows=@();if($Queue){$Rows=Import-Csv -LiteralPath $Queue}
$Total=@($Rows).Count
$OutBase=if($Queue){Split-Path -Parent $Queue}else{$Root}
$Out=Join-Path $OutBase ('ready_to_sell_accuracy_runs\'+$TaskId+'-'+$RunId)
$BatchDir=Join-Path $Out 'batches'
New-Item -ItemType Directory -Force -Path $Out,$BatchDir | Out-Null
$Size=50;$Count=if($Total -gt 0){[int][Math]::Ceiling($Total/[double]$Size)}else{0}
for($i=0;$i -lt $Count;$i++){ $n=$i+1; $f=Join-Path $BatchDir ('batch_{0:0000}.csv' -f $n); $Rows|Select-Object -Skip ($i*$Size) -First $Size|Export-Csv -LiteralPath $f -NoTypeInformation -Encoding UTF8 }
H 'BATCHES' 70
$State=@{task_id=$TaskId;generated_at=(Get-Date -Format s);queue_path=$Queue;excel_path=$Excel;total_rows=$Total;batch_size=$Size;batch_count=$Count;output_root=$Out;next_task='rtsacc-002-verify-batch-0001'}
$StateJson=$State|ConvertTo-Json -Depth 4
W (Join-Path $Out 'RTSACC_001B_RUN_STATE.json') $StateJson
W $Report @('# RTSACC 001B kickoff retry report',('generated: '+(Get-Date -Format s)),('task_id: '+$TaskId),('queue_path: '+$(if($Queue){$Queue}else{'MISSING'})),('excel_path: '+$(if($Excel){$Excel}else{'MISSING'})),('total_rows: '+$Total),('batch_size: '+$Size),('batch_count: '+$Count),('output_root: '+$Out),'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT','safe_output_gate: READY_FOR_HUMAN_EVIDENCE_REVIEW','no_db_write: yes','task_gate: COMPLETE','RTSACC_001B_DONE=true')
H 'COMPLETE' 100
Write-Output 'RTSACC_001B_DONE=true'
Write-Output ('OUTPUT_ROOT='+$Out)
exit 0

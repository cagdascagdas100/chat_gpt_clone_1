$ErrorActionPreference = 'Continue'
$TaskId = 'rtsacc-001-kickoff-20260518'
$TaskName = 'rtsacc_001_kickoff_20260518'
$RunId = Get-Date -Format 'yyyyMMdd_HHmmss'
$BridgeRoot = if ($env:AAYS_BRIDGE_ROOT) { $env:AAYS_BRIDGE_ROOT } else { Split-Path -Parent $PSScriptRoot }
$ResultsDir = Join-Path $BridgeRoot 'ai-results'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultsDir, $HeartbeatDir | Out-Null
$ReportPath = Join-Path $ResultsDir ($TaskId + '-' + $RunId + '.md')
$HeartbeatPath = Join-Path $HeartbeatDir ($TaskName + '.md')
function SaveText($p,$v){ Set-Content -LiteralPath $p -Encoding UTF8 -Value $v }
function Heartbeat($stage,$progress){ SaveText $HeartbeatPath @('# RTSACC 001 HEARTBEAT',('generated='+(Get-Date -Format s)),('task_id='+$TaskId),('stage='+$stage),('progress='+$progress),'production_gate=NOT_READY_FOR_AUTO_ACCEPT','safe_output_gate=READY_FOR_HUMAN_EVIDENCE_REVIEW') }
Heartbeat 'STARTED' 1
$roots = @('C:\Users\cagda\Documents\GitHub\AAYS',$BridgeRoot,(Split-Path -Parent $BridgeRoot)) | Select-Object -Unique
$queue = $null
$excel = $null
foreach($r in $roots){
  if(Test-Path -LiteralPath $r){
    if(-not $queue){ $q = Get-ChildItem -LiteralPath $r -Recurse -File -Filter 'READY_TO_SELL_AI_WEB_VERIFICATION_QUEUE.csv' -ErrorAction SilentlyContinue | Select-Object -First 1; if($q){$queue=$q.FullName} }
    if(-not $excel){ $e = Get-ChildItem -LiteralPath $r -Recurse -File -Filter 'TerraYield_ReadyToSell_*_PRICE_FILLED.xlsx' -ErrorAction SilentlyContinue | Select-Object -First 1; if($e){$excel=$e.FullName} }
  }
}
Heartbeat 'DISCOVERY_DONE' 30
$rows = @()
if($queue){ $rows = Import-Csv -LiteralPath $queue }
$total = @($rows).Count
$rootOut = if($queue){ Split-Path -Parent $queue } else { $BridgeRoot }
$out = Join-Path $rootOut ('ready_to_sell_accuracy_runs\' + $TaskId + '-' + $RunId)
$batches = Join-Path $out 'batches'
New-Item -ItemType Directory -Force -Path $out,$batches | Out-Null
$batchSize = 50
$batchCount = if($total -gt 0){ [int][Math]::Ceiling($total/[double]$batchSize) } else { 0 }
for($i=0;$i -lt $batchCount;$i++){
  $batchNo = $i + 1
  $file = Join-Path $batches ('batch_{0:0000}.csv' -f $batchNo)
  $rows | Select-Object -Skip ($i*$batchSize) -First $batchSize | Export-Csv -LiteralPath $file -NoTypeInformation -Encoding UTF8
}
Heartbeat 'BATCHES_CREATED' 70
$state = [ordered]@{ task_id=$TaskId; generated_at=(Get-Date -Format s); queue_path=$queue; excel_path=$excel; total_rows=$total; batch_size=$batchSize; batch_count=$batchCount; output_root=$out; production_acceptance_gate='NOT_READY_FOR_AUTO_ACCEPT'; safe_output_gate='READY_FOR_HUMAN_EVIDENCE_REVIEW'; next_task='rtsacc-002-verify-batch-0001' }
$statePath = Join-Path $out 'RTSACC_001_RUN_STATE.json'
$state | ConvertTo-Json -Depth 5 | SaveText $statePath
$report = @('# RTSACC 001 kickoff report',('Generated: '+(Get-Date -Format s)),('task_id: '+$TaskId),('queue_path: '+$(if($queue){$queue}else{'MISSING'})),('excel_path: '+$(if($excel){$excel}else{'MISSING'})),('total_rows: '+$total),('batch_size: '+$batchSize),('batch_count: '+$batchCount),('output_root: '+$out),('run_state: '+$statePath),'production_acceptance_gate: NOT_READY_FOR_AUTO_ACCEPT','safe_output_gate: READY_FOR_HUMAN_EVIDENCE_REVIEW','no_db_write: yes','old_task_continuation: no','task_gate: COMPLETE','RTSACC_001_DONE=true')
SaveText $ReportPath $report
Heartbeat 'COMPLETE' 100
Write-Output 'RTSACC_001_DONE=true'
Write-Output ('OUTPUT_ROOT='+$out)
exit 0

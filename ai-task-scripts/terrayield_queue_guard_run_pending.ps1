$ErrorActionPreference='Continue'
$Root='C:/AAYS_GITHUB_BRIDGE_CLEAN2'
$TaskId='terrayield-queue-guard-run-pending-20260520'
$Progress=Join-Path $Root 'ai-progress'
$Results=Join-Path $Root 'ai-results'
$Pending=Join-Path $Root 'ai-tasks/pending'
$Logs=Join-Path $Root 'ai-runner-logs'
New-Item -ItemType Directory -Force -Path $Progress,$Results,$Pending,$Logs | Out-Null
$ProgressPath=Join-Path $Progress ($TaskId+'.progress.md')
$ResultPath=Join-Path $Results ($TaskId+'.result.json')
function Tick($phase,$pct,$extra='') { @('# queue guard clean2','',"phase: $phase","percent: $pct","checked_at: $((Get-Date).ToString('s'))",$extra) | Set-Content -Encoding UTF8 $ProgressPath }
Tick 'scan' 5
$items=Get-ChildItem -Path $Pending -Filter '*.json' -File -ErrorAction SilentlyContinue
$ran=@()
if($items.Count -gt 0){
  $idx=0
  foreach($it in $items){
    $idx++
    Tick 'pending item found' ([int](10+($idx*70/[Math]::Max(1,$items.Count)))) $it.Name
    try { $task=Get-Content -Raw -Encoding UTF8 $it.FullName | ConvertFrom-Json } catch { $ran += @{file=$it.Name;status='bad_json'}; continue }
    $sp=Join-Path $Root ('ai-task-scripts/'+[string]$task.script_path)
    if(Test-Path $sp){
      $log=Join-Path $Logs (($task.id)+'.queue.log')
      powershell -NoProfile -ExecutionPolicy Bypass -File $sp *> $log
      $ran += @{id=$task.id;script=$task.script_path;status='ran';log=$log;exit=$LASTEXITCODE}
    } else { $ran += @{id=$task.id;script=$task.script_path;status='script_missing'} }
  }
} else {
  Tick 'no pending; contractor fallback' 10
  $fallback=Join-Path $Root 'ai-task-scripts/terrayield_contractor_002_long_watchdog_foundation.ps1'
  if(Test-Path $fallback){
    $log=Join-Path $Logs 'contractor-002-fallback.queue.log'
    Tick 'running contractor fallback' 20 $fallback
    powershell -NoProfile -ExecutionPolicy Bypass -File $fallback *> $log
    $ran += @{id='contractor-002-fallback';script='terrayield_contractor_002_long_watchdog_foundation.ps1';status='ran';log=$log;exit=$LASTEXITCODE}
  } else {
    $ran += @{id='contractor-002-fallback';status='fallback_script_missing'}
  }
}
Tick 'done' 100
@{task_id=$TaskId;status='queue_guard_done';pending_count=$items.Count;root=$Root;processed=$ran;no_db_write=$true}|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $ResultPath
Write-Host 'QUEUE_GUARD_DONE'
exit 0
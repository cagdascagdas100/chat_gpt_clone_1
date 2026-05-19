$ErrorActionPreference='Continue'
$Root='C:/AAYS_GITHUB_BRIDGE_CLEAN'
$TaskId='terrayield-queue-guard-run-pending-20260520'
$Pending=Join-Path $Root 'ai-tasks/pending'
$Active=Join-Path $Root 'ai-tasks/active'
$Done=Join-Path $Root 'ai-tasks/done'
$Failed=Join-Path $Root 'ai-tasks/failed'
$Progress=Join-Path $Root 'ai-progress'
$Results=Join-Path $Root 'ai-results'
$Logs=Join-Path $Root 'ai-runner-logs'
@($Pending,$Active,$Done,$Failed,$Progress,$Results,$Logs) | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }
$ProgressPath=Join-Path $Progress ($TaskId+'.progress.md')
$ResultPath=Join-Path $Results ($TaskId+'.result.json')
function Iso { (Get-Date).ToString('s') }
function Progress($p,$phase,$extra='') { @("# $TaskId",'',"checked_at: $(Iso)","percent: $p","phase: $phase",'',$extra) | Set-Content -Encoding UTF8 $ProgressPath }
Progress 5 'queue_guard_started'
$items=Get-ChildItem -Path $Pending -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime
$results=@()
if(-not $items -or $items.Count -eq 0){
  Progress 100 'no_pending_tasks'
  @{task_id=$TaskId;status='no_pending_tasks';checked_at=Iso}|ConvertTo-Json -Depth 6|Set-Content -Encoding UTF8 $ResultPath
  exit 0
}
$i=0
foreach($item in $items){
  $i++
  try { $task=Get-Content -Raw -Encoding UTF8 $item.FullName | ConvertFrom-Json } catch { $results += @{file=$item.Name;status='bad_json'}; continue }
  $scriptName=[string]$task.script_path
  $scriptPath=Join-Path $Root ('ai-task-scripts/'+$scriptName)
  $activePath=Join-Path $Active $item.Name
  Move-Item -Force $item.FullName $activePath
  Progress ([int](10+($i*70/[Math]::Max(1,$items.Count)))) ('running '+$task.id) "script=$scriptName"
  if(Test-Path $scriptPath){
    $log=Join-Path $Logs (($task.id)+'.queue-guard.log')
    powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath *> $log
    $code=$LASTEXITCODE
    if($code -eq 0){ Move-Item -Force $activePath (Join-Path $Done (Split-Path $activePath -Leaf)); $results += @{id=$task.id;script=$scriptName;status='done';exit_code=$code;log=$log} }
    else { Move-Item -Force $activePath (Join-Path $Failed (Split-Path $activePath -Leaf)); $results += @{id=$task.id;script=$scriptName;status='failed';exit_code=$code;log=$log} }
  } else {
    Move-Item -Force $activePath (Join-Path $Failed (Split-Path $activePath -Leaf))
    $results += @{id=$task.id;script=$scriptName;status='script_missing'}
  }
}
Progress 100 'queue_guard_done'
@{task_id=$TaskId;status='done';checked_at=Iso;processed=$results}|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 $ResultPath
exit 0

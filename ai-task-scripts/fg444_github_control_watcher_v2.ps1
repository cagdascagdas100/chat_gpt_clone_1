$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$RepoUrl='https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$LocalRepo='C:\Users\cagda\Documents\GitHub\AAYS'
$ScriptDir=Join-Path $Bridge 'ai-task-scripts'
$QueueRoot=Join-Path $Bridge 'ai-queue'
$Pending=Join-Path $QueueRoot 'pending'
$Running=Join-Path $QueueRoot 'running'
$StateDir=Join-Path $Bridge 'fg444-controller-state'
$Runner=Join-Path $ScriptDir 'portable_queue_runner.ps1'
$ControlUrls=@(
  'https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/main/docs/chatgpt_control/FG444_LONDON_REQUEST.json',
  'https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/main/docs/chatgpt_control/FG444_CONTROLLER_NEXT.json'
)
New-Item -ItemType Directory -Force -Path $ScriptDir,$Pending,$Running,$StateDir | Out-Null
$Log=Join-Path $StateDir ('fg444_github_control_watcher_v2_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.txt')
function L([string]$m){ ('['+(Get-Date -Format s)+'] '+$m) | Tee-Object -FilePath $Log -Append }
function Ensure-LocalRepo {
  if(Test-Path (Join-Path $LocalRepo '.git')){
    Push-Location $LocalRepo
    git fetch origin 2>&1 | Add-Content -Encoding UTF8 $Log
    git pull --ff-only origin main 2>&1 | Add-Content -Encoding UTF8 $Log
    Pop-Location
    return $true
  }
  L "LOCAL_REPO_NOT_FOUND=$LocalRepo"
  return $false
}
function Ensure-OneRunner {
  $procs=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'portable_queue_runner.ps1' } | Sort-Object CreationDate)
  if($procs.Count -gt 1){ $procs | Select-Object -Skip 1 | ForEach-Object { L "STOP_EXTRA_RUNNER_PID=$($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }
  if($procs.Count -eq 0 -and (Test-Path $Runner)){ L "START_RUNNER=$Runner"; Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`"" }
  return @((Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'portable_queue_runner.ps1' })).Count
}
function Get-Controls {
  $items=@()
  foreach($u in $ControlUrls){
    try{
      $raw=(Invoke-WebRequest -UseBasicParsing -TimeoutSec 15 $u).Content
      $c=$raw | ConvertFrom-Json
      $c | Add-Member -NotePropertyName source_url -NotePropertyValue $u -Force
      $items += $c
    }catch{ L "CONTROL_FETCH_SKIP=$u :: $($_.Exception.Message)" }
  }
  return $items
}
function Test-ResultExists([object]$c){
  if(-not $c.result_branch -or -not $c.result_latest_path){ return $false }
  $u='https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/' + $c.result_branch + '/' + $c.result_latest_path
  try{ $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 $u; if($r.Content.Length -gt 20){ L "RESULT_ALREADY_ON_GITHUB=true URL=$u"; return $true } }catch{}
  L 'RESULT_ALREADY_ON_GITHUB=false'
  return $false
}
function Queue-ControlTask([object]$c){
  if(-not $c.enabled){ L "CONTROL_DISABLED source=$($c.source_url)"; return $false }
  if($c.step -ne '01_READONLY_AUDIT'){ L "UNSUPPORTED_STEP=$($c.step) source=$($c.source_url)"; return $false }
  $prefix=[string]$c.task_id_prefix; if([string]::IsNullOrWhiteSpace($prefix)){ $prefix='fg444-task' }
  $runningTasks=@(Get-ChildItem $Running -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match [regex]::Escape($prefix) })
  $pendingTasks=@(Get-ChildItem $Pending -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match [regex]::Escape($prefix) })
  L "PREFIX=$prefix PENDING_COUNT=$($pendingTasks.Count) RUNNING_COUNT=$($runningTasks.Count)"
  if($pendingTasks.Count -gt 0 -or $runningTasks.Count -gt 0){ return $false }
  if(Test-ResultExists $c){ return $false }
  Ensure-LocalRepo | Out-Null
  $repoScript=Join-Path $LocalRepo ([string]$c.runner_script_repo_path)
  $localScript=Join-Path $ScriptDir (Split-Path ([string]$c.runner_script_repo_path) -Leaf)
  if(Test-Path $repoScript){ Copy-Item $repoScript $localScript -Force }
  if(-not (Test-Path $localScript)){ L "MISSING_RUNNER_SCRIPT=$localScript"; return $false }
  $taskId=$prefix + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
  $pageKey=[string]$c.page_key; if([string]::IsNullOrWhiteSpace($pageKey)){ $pageKey='FG444_DYNAMIC' }
  $Task=[ordered]@{
    page_key=$pageKey
    project_name='AAYS_TerraYield'
    id=$taskId
    task_id=$taskId
    script_path=$localScript
    timeout_seconds=[int]$c.timeout_seconds
    db_write=[bool]$c.db_write
    production_deploy=[bool]$c.production_deploy
    migration_ddl=[bool]$c.migration_ddl
    fake_data=[bool]$c.fake_data
    wait_minutes_after_start=[string]$c.wait_minutes_after_start
    purpose=[string]$c.purpose
    control_step=[string]$c.step
    workspace_root=[string]$c.workspace_root
  }
  $Task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $Pending ($taskId + '.task.json'))
  L "QUEUED=$taskId SCRIPT=$localScript PAGE_KEY=$pageKey"
  return $true
}
function Push-Heartbeat {
  try{
    if(Test-Path (Join-Path $LocalRepo '.git')){
      $statusDir=Join-Path $LocalRepo 'docs\chatgpt_status\FG444_CONTROLLER_HEARTBEAT'
      New-Item -ItemType Directory -Force $statusDir | Out-Null
      $latest=Join-Path $statusDir 'FG444_CONTROLLER_HEARTBEAT_LATEST.txt'
      @(
        'FG444_CONTROLLER_HEARTBEAT_V2',
        'UPDATED_AT='+(Get-Date -Format s),
        'WATCHER_LOG='+$Log,
        'PENDING_DIR='+$Pending,
        'RUNNING_DIR='+$Running,
        'RUNNER_ACTIVE_COUNT='+(Ensure-OneRunner),
        'CONTROL_URLS='+($ControlUrls -join ';'),
        'MANUAL_OUTPUT_PASTE_REQUIRED=false'
      ) | Set-Content -Encoding UTF8 $latest
      Push-Location $LocalRepo
      git add docs/chatgpt_status/FG444_CONTROLLER_HEARTBEAT 2>&1 | Add-Content -Encoding UTF8 $Log
      if(git status --porcelain docs/chatgpt_status/FG444_CONTROLLER_HEARTBEAT){ git commit -m 'Update FG444 controller heartbeat v2' 2>&1 | Add-Content -Encoding UTF8 $Log; git push origin HEAD:fg444-controller-heartbeat-latest --force 2>&1 | Add-Content -Encoding UTF8 $Log }
      Pop-Location
    }
  }catch{ L "HEARTBEAT_PUSH_FAIL=$($_.Exception.Message)" }
}
L 'FG444_GITHUB_CONTROL_WATCHER_V2_START'
$lastHeartbeat=Get-Date '2000-01-01'
while($true){
  try{
    Ensure-LocalRepo | Out-Null
    foreach($control in (Get-Controls)){ [void](Queue-ControlTask $control) }
    $active=Ensure-OneRunner
    L "RUNNER_ACTIVE_COUNT=$active"
    if(((Get-Date)-$lastHeartbeat).TotalMinutes -ge 5){ Push-Heartbeat; $lastHeartbeat=Get-Date }
  }catch{ L "WATCHER_LOOP_ERROR=$($_.Exception.Message)" }
  Start-Sleep -Seconds 60
}

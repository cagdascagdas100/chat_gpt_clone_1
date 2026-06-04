$ErrorActionPreference="Continue"

$BridgeRoot="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$WorktreePath="F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706"
$WorkBranch="aays-runner-v17-icon-work-20260603-232706"
$PageKey="AAYS_SAME_PROJECT_NEW_PAGE"
$ScriptDir=Join-Path $BridgeRoot "ai-task-scripts"
$QueuePending=Join-Path $BridgeRoot "ai-queue\pending"
$StateDir=Join-Path $BridgeRoot "ai-state"
$ResultDir=Join-Path $BridgeRoot "ai-results"
New-Item -ItemType Directory -Force -Path $ScriptDir,$QueuePending,$StateDir,$ResultDir | Out-Null

$PollerPath=Join-Path $ScriptDir "github_task_poller_AAYS_SAME_PROJECT_NEW_PAGE.ps1"
$Poller=@'
param([switch]$Loop)
$ErrorActionPreference="Continue"
$BridgeRoot="C:\AAYS_GITHUB_BRIDGE_CLEAN2"
$WorktreePath="F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706"
$WorkBranch="aays-runner-v17-icon-work-20260603-232706"
$PageKey="AAYS_SAME_PROJECT_NEW_PAGE"
$QueuePending=Join-Path $BridgeRoot "ai-queue\pending"
$StateDir=Join-Path $BridgeRoot "ai-state"
$ResultDir=Join-Path $BridgeRoot "ai-results"
$StatePath=Join-Path $StateDir "github_task_poller_seen.json"
New-Item -ItemType Directory -Force -Path $QueuePending,$StateDir,$ResultDir | Out-Null

function Invoke-AaysPollOnce {
  $now=Get-Date -Format "yyyyMMdd-HHmmss"
  $lines=@()
  $lines+="PAGE_KEY=$PageKey"
  $lines+="RUN_AT=$((Get-Date).ToString('o'))"
  $lines+="MODE=GITHUB_TASK_POLLER_ONCE"
  $lines+="WORKTREE_PATH=$WorktreePath"
  $lines+="WORK_BRANCH=$WorkBranch"
  $lines+="SAFETY=no_delete_no_reset_hard_no_git_clean_no_force_push"

  if(!(Test-Path $WorktreePath)){
    $lines+="ERROR=worktree_missing"
  } else {
    git -C $WorktreePath fetch origin $WorkBranch *> (Join-Path $ResultDir "github_task_poller_git_$now.txt")
    git -C $WorktreePath checkout "origin/$WorkBranch" -- "docs/chatgpt_status/AAYS_SAME_PROJECT_NEW_PAGE/runner_tasks" 2>> (Join-Path $ResultDir "github_task_poller_git_$now.txt")
    $taskDir=Join-Path $WorktreePath "docs\chatgpt_status\AAYS_SAME_PROJECT_NEW_PAGE\runner_tasks"
    $seen=@{}
    if(Test-Path $StatePath){
      try { $seen=Get-Content $StatePath -Raw | ConvertFrom-Json -AsHashtable } catch { $seen=@{} }
    }
    $queued=0
    Get-ChildItem $taskDir -Filter "*.ps1" -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike "INSTALL_*" } | ForEach-Object {
      $hash=(Get-FileHash $_.FullName -Algorithm SHA256).Hash
      $key=$_.Name
      if(-not $seen.ContainsKey($key) -or $seen[$key] -ne $hash){
        $taskId="github-task-"+($_.BaseName -replace '[^A-Za-z0-9_-]','-')+"-"+$now
        @{task_id=$taskId; page_key=$PageKey; script_path=$_.FullName; source="github_task_poller"; sha256=$hash} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $QueuePending ($taskId+".task.json")) -Encoding UTF8
        $seen[$key]=$hash
        $queued++
        $lines+="QUEUED_TASK=$taskId"
        $lines+="SCRIPT_PATH=$($_.FullName)"
      }
    }
    $seen | ConvertTo-Json -Depth 5 | Set-Content $StatePath -Encoding UTF8
    $lines+="QUEUED_COUNT=$queued"
  }
  $lines+="PROGRESS_ESTIMATE=45"
  $lines+="FINAL_LABEL=AAYS_GITHUB_TASK_POLLER_ONCE_DONE"
  $report=Join-Path $ResultDir ("AAYS_SAME_PROJECT_NEW_PAGE_github_task_poller_"+$now+".txt")
  ($lines -join [Environment]::NewLine) | Set-Content $report -Encoding UTF8
  return $report
}

if($Loop){
  while($true){ Invoke-AaysPollOnce | Out-Null; Start-Sleep -Seconds 60 }
} else {
  Invoke-AaysPollOnce
}
'@
$Poller | Set-Content $PollerPath -Encoding UTF8

$Report=Join-Path $ResultDir ("AAYS_SAME_PROJECT_NEW_PAGE_install_github_task_poller_"+(Get-Date -Format "yyyyMMdd-HHmmss")+".txt")
$RunnerPath=Join-Path $BridgeRoot "ai-task-scripts\portable_queue_runner.ps1"
$runnerCount=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*portable_queue_runner.ps1*" }).Count
$pollerRunning=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*github_task_poller_AAYS_SAME_PROJECT_NEW_PAGE.ps1*" }).Count
if($pollerRunning -lt 1){
  Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PollerPath`" -Loop"
}
if($runnerCount -lt 1 -and (Test-Path $RunnerPath)){
  Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$RunnerPath`""
}
$onceReport=powershell -NoProfile -ExecutionPolicy Bypass -File $PollerPath
@(
"PAGE_KEY=$PageKey",
"RUN_AT=$((Get-Date).ToString('o'))",
"MODE=INSTALL_GITHUB_QUEUE_POLLER_V1",
"POLLER_PATH=$PollerPath",
"RUNNER_PATH=$RunnerPath",
"RUNNER_PROCESS_COUNT_BEFORE=$runnerCount",
"POLLER_STARTED_OR_ALREADY_RUNNING=true",
"ONCE_REPORT=$onceReport",
"SAFETY=no_delete_no_reset_hard_no_git_clean_no_force_push",
"PROGRESS_ESTIMATE=45",
"FINAL_LABEL=AAYS_GITHUB_QUEUE_POLLER_INSTALLED"
) -join [Environment]::NewLine | Set-Content $Report -Encoding UTF8
Write-Host "POLLER_PATH=$PollerPath"
Write-Host "REPORT=$Report"
Write-Host "Bekleme suresi: 1-3 dakika"

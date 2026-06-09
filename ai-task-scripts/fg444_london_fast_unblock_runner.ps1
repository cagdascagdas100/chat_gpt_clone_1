$ErrorActionPreference='Continue'
$RepoUrl='https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$ScriptDir=Join-Path $Bridge 'ai-task-scripts'
$Pending=Join-Path $Bridge 'ai-queue\pending'
$Running=Join-Path $Bridge 'ai-queue\running'
$WorkRoot='F:\chatgpt\AAYS_WORK\FG444_LONDON'
$RunRoot=Join-Path $WorkRoot ('fast_unblock_' + $Stamp)
New-Item -ItemType Directory -Force -Path $ScriptDir,$Pending,$Running,$WorkRoot,$RunRoot | Out-Null
$Report=Join-Path $RunRoot ('FG444_LONDON_FAST_UNBLOCK_' + $Stamp + '.txt')
function L([string]$m){ $m | Tee-Object -FilePath $Report -Append }
L 'FG444_LONDON_FAST_UNBLOCK_START'
L ('CREATED_AT='+(Get-Date -Format s))
L ('BRIDGE='+$Bridge)
L ('PENDING='+$Pending)
L ('RUNNING='+$Running)
L ('WORK_ROOT='+$WorkRoot)
$prefix='fg444-london-01-readonly-audit'
$pendingAudit=@(Get-ChildItem $Pending -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like ($prefix+'*') })
$runningAudit=@(Get-ChildItem $Running -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -like ($prefix+'*') })
L ('PENDING_AUDIT_COUNT='+$pendingAudit.Count)
foreach($f in $pendingAudit){ L ('PENDING_AUDIT_FILE='+$f.FullName) }
L ('RUNNING_AUDIT_COUNT='+$runningAudit.Count)
foreach($f in $runningAudit){ L ('RUNNING_AUDIT_FILE='+$f.FullName) }
$runnerCount=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'portable_queue_runner.ps1' }).Count
L ('RUNNER_ACTIVE_COUNT='+$runnerCount)
$hasResult=$false
try{
  $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 15 'https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/fg444-london-readonly-audit-latest/docs/chatgpt_status/FG444_LONDON_READONLY_AUDIT/FG444_LONDON_READONLY_AUDIT_LATEST.txt'
  if($r.Content.Length -gt 20){ $hasResult=$true }
}catch{}
L ('READONLY_RESULT_EXISTS='+$hasResult)
if((-not $hasResult) -and $pendingAudit.Count -eq 0 -and $runningAudit.Count -eq 0){
  $localScript=Join-Path $ScriptDir 'fg444_london_01_readonly_audit_runner.ps1'
  try{ Invoke-WebRequest -UseBasicParsing -TimeoutSec 30 'https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/main/ai-task-scripts/fg444_london_01_readonly_audit_runner.ps1' -OutFile $localScript }catch{ L ('DOWNLOAD_AUDIT_RUNNER_FAIL='+$_.Exception.Message) }
  if(Test-Path $localScript){
    $taskId=$prefix + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
    $task=[ordered]@{
      page_key='FG444_LONDON_ONLY_F_DRIVE'
      project_name='AAYS_TerraYield'
      id=$taskId
      task_id=$taskId
      script_path=$localScript
      timeout_seconds=7200
      db_write=$false
      production_deploy=$false
      migration_ddl=$false
      fake_data=$false
      wait_minutes_after_start='20-45'
      purpose='London-only F-drive readonly audit queued by fast unblock'
      workspace_root=$WorkRoot
    }
    $task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $Pending ($taskId+'.task.json'))
    L ('AUDIT_TASK_QUEUED='+$taskId)
  }else{
    L ('AUDIT_RUNNER_MISSING='+$localScript)
  }
}else{
  L 'AUDIT_TASK_NOT_REQUEUED_ALREADY_PENDING_RUNNING_OR_RESULT_EXISTS'
}
$PushWork=Join-Path $WorkRoot ('fast_unblock_push_' + $Stamp)
git clone $RepoUrl $PushWork 2>&1 | Add-Content -Encoding UTF8 $Report
Push-Location $PushWork
git checkout -B fg444-london-fast-unblock-latest origin/main 2>&1 | Add-Content -Encoding UTF8 $Report
$Dest=Join-Path $PushWork 'docs\chatgpt_status\FG444_LONDON_FAST_UNBLOCK'
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Copy-Item $Report (Join-Path $Dest 'FG444_LONDON_FAST_UNBLOCK_LATEST.txt') -Force
git config user.email 'aays-runner@example.local'
git config user.name 'AAYS Runner'
git add docs/chatgpt_status/FG444_LONDON_FAST_UNBLOCK 2>&1 | Add-Content -Encoding UTF8 $Report
git commit -m 'Add FG444 London fast unblock report' 2>&1 | Add-Content -Encoding UTF8 $Report
git push origin HEAD:refs/heads/fg444-london-fast-unblock-latest --force-with-lease 2>&1 | Add-Content -Encoding UTF8 $Report
Pop-Location
L 'FG444_LONDON_FAST_UNBLOCK_END'
exit 0

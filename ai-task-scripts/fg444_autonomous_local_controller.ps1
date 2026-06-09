$ErrorActionPreference='Continue'
$Bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$RepoUrl='https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$LocalRepo='C:\Users\cagda\Documents\GitHub\AAYS'
$ScriptDir=Join-Path $Bridge 'ai-task-scripts'
$QueueRoot=Join-Path $Bridge 'ai-queue'
$Pending=Join-Path $QueueRoot 'pending'
$Running=Join-Path $QueueRoot 'running'
$Results=Join-Path $Bridge 'ai-results'
$Runner=Join-Path $ScriptDir 'portable_queue_runner.ps1'
$StateDir=Join-Path $Bridge 'fg444-controller-state'
New-Item -ItemType Directory -Force -Path $ScriptDir,$Pending,$Running,$Results,$StateDir | Out-Null
$Log=Join-Path $StateDir ('fg444_autonomous_controller_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.txt')
function L([string]$m){ $m | Tee-Object -FilePath $Log -Append }
function Ensure-OneRunner {
  $procs=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'portable_queue_runner.ps1' } | Sort-Object CreationDate)
  if($procs.Count -gt 1){ $procs | Select-Object -Skip 1 | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }
  if($procs.Count -eq 0 -and (Test-Path $Runner)){ Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`"" }
  return @((Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'portable_queue_runner.ps1' })).Count
}
function Queue-Step01 {
  $taskId='fg444-100-01-readonly-audit-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
  $repoScript=Join-Path $LocalRepo 'ai-task-scripts\fg444_100_01_readonly_audit_runner.ps1'
  $localScript=Join-Path $ScriptDir 'fg444_100_01_readonly_audit_runner.ps1'
  if(Test-Path $repoScript){ Copy-Item $repoScript $localScript -Force }
  if(-not (Test-Path $localScript)){ L "MISSING_RUNNER_SCRIPT=$localScript"; return $false }
  $Task=[ordered]@{
    page_key='FG444_100_COMPLETION'
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
    purpose='FG444 step 01 read-only audit and GitHub result push'
  }
  $Task | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 (Join-Path $Pending ($taskId + '.task.json'))
  L "QUEUED=$taskId"
  return $true
}
L 'FG444_AUTONOMOUS_CONTROLLER_START'
L "STARTED_AT=$(Get-Date -Format s)"
if(Test-Path (Join-Path $LocalRepo '.git')){
  Push-Location $LocalRepo
  git fetch origin 2>&1 | Add-Content -Encoding UTF8 $Log
  git pull --ff-only origin main 2>&1 | Add-Content -Encoding UTF8 $Log
  Pop-Location
}else{
  L "LOCAL_REPO_NOT_FOUND=$LocalRepo"
}
$latestUrl='https://raw.githubusercontent.com/cagdascagdas100/chat_gpt_clone_1/fg444-100-readonly-audit-latest/docs/chatgpt_status/FG444_100_READONLY_AUDIT/FG444_100_READONLY_AUDIT_LATEST.txt'
$alreadyDone=$false
try{
  $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 $latestUrl
  if($r.Content -match 'FG444_100_READONLY_AUDIT_LATEST'){ $alreadyDone=$true; L 'RESULT_ALREADY_ON_GITHUB=true' }
}catch{ L 'RESULT_ALREADY_ON_GITHUB=false' }
$runningTasks=@(Get-ChildItem $Running -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'fg444-100-01-readonly-audit' })
$pendingTasks=@(Get-ChildItem $Pending -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'fg444-100-01-readonly-audit' })
L "PENDING_COUNT=$($pendingTasks.Count)"
L "RUNNING_COUNT=$($runningTasks.Count)"
if(-not $alreadyDone -and $pendingTasks.Count -eq 0 -and $runningTasks.Count -eq 0){ [void](Queue-Step01) }
$active=Ensure-OneRunner
L "RUNNER_ACTIVE_COUNT=$active"
L 'MANUAL_OUTPUT_PASTE_REQUIRED=false'
L 'WAIT_MINUTES=20-45'
L 'FG444_AUTONOMOUS_CONTROLLER_END'

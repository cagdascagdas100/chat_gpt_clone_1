$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
$RepoUrl = 'https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$RunnerName = 'AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1'
$TaskName = 'AAYS-Portable-Task-Runner-Fixed'

function Write-Step {
  param([string]$Text)
  Write-Host ('[' + (Get-Date -Format 's') + '] ' + $Text)
}

Write-Step 'AAYS sync repair bootstrap started.'
Write-Step ('BridgeRoot=' + $BridgeRoot)

if (-not (Test-Path $BridgeRoot)) {
  Write-Step 'Bridge root missing; cloning bridge repo.'
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BridgeRoot) | Out-Null
  git clone $RepoUrl $BridgeRoot
}

Set-Location $BridgeRoot

Write-Step 'Stopping duplicate portable runner processes except this command tree.'
try {
  $currentPid = $PID
  $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match [regex]::Escape($RunnerName) }
  foreach ($p in $procs) {
    if ($p.ProcessId -ne $currentPid) {
      Write-Step ('Stopping runner PID=' + $p.ProcessId)
      Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
  }
} catch {
  Write-Step ('Process cleanup warning: ' + $_.Exception.Message)
}

Write-Step 'Saving local runner outputs before sync.'
git add ai-results ai-heartbeat ai-tasks/.last-task-id ai-runner-logs AAYS_TASK_BRIDGE_CONFIG.ps1 2>&1 | Write-Host
$commitOut = git commit -m ('Local runner result sync before repair ' + (Get-Date -Format 'yyyyMMdd-HHmmss')) 2>&1 | Out-String
Write-Host $commitOut

Write-Step 'Fetching remote main.'
git fetch origin main 2>&1 | Write-Host

Write-Step 'Trying pull --rebase --autostash.'
$pullOut = git pull --rebase --autostash origin main 2>&1 | Out-String
Write-Host $pullOut

if ($LASTEXITCODE -ne 0 -or $pullOut -match 'CONFLICT|fatal:|error:') {
  Write-Step 'Pull rebase failed; entering conservative stash recovery.'
  git rebase --abort 2>&1 | Write-Host
  git stash push -u -m ('aays-sync-repair-' + (Get-Date -Format 'yyyyMMdd-HHmmss')) 2>&1 | Write-Host
  git reset --hard origin/main 2>&1 | Write-Host
  $stashList = git stash list 2>&1 | Out-String
  Write-Host $stashList
  if ($stashList -match 'aays-sync-repair') {
    Write-Step 'Applying latest stash.'
    git stash pop 2>&1 | Write-Host
    git add ai-results ai-heartbeat ai-tasks/.last-task-id ai-runner-logs AAYS_TASK_BRIDGE_CONFIG.ps1 2>&1 | Write-Host
    git commit -m ('Restore local runner outputs after sync repair ' + (Get-Date -Format 'yyyyMMdd-HHmmss')) 2>&1 | Write-Host
  }
}

Write-Step 'Pushing repaired bridge state.'
git push origin main 2>&1 | Write-Host

Write-Step 'Registering scheduled task for runner auto-start.'
try {
  $runnerPath = Join-Path $BridgeRoot $RunnerName
  $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "' + $runnerPath + '"')
  $trigger = New-ScheduledTaskTrigger -AtLogOn
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description 'AAYS GitHub bridge portable task runner auto-start' -Force | Out-Null
  Write-Step ('Scheduled task registered: ' + $TaskName)
} catch {
  Write-Step ('Scheduled task registration warning: ' + $_.Exception.Message)
}

Write-Step 'Starting runner in current PowerShell. Keep this window open.'
powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $BridgeRoot $RunnerName)

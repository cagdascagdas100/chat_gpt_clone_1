$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\Users\cagda\Documents\chat_gpt_clone_1'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ('force-restart-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
function L($x) { $line = (Get-Date -Format 's') + ' ' + $x; Write-Host $line; Add-Content -Encoding UTF8 -Path $Log -Value $line }

L 'AAYS force restart started'
Set-Location $BridgeRoot

L 'Stopping watchdog script if available'
try {
  $stop = Join-Path $BridgeRoot 'STOP_AAYS_USERMODE_WATCHDOG.ps1'
  if (Test-Path $stop) { powershell -NoProfile -ExecutionPolicy Bypass -File $stop | Out-String | Add-Content -Encoding UTF8 -Path $Log }
} catch { L ('Stop watchdog warning: ' + $_.Exception.Message) }

L 'Killing stale runner/watchdog PowerShell processes'
try {
  Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -like '*AAYS_CHATGPT_RUNNER_V4.ps1*' -or
    $_.CommandLine -like '*START_AAYS_USERMODE_WATCHDOG.ps1*' -or
    $_.CommandLine -like '*USERMODE_WATCHDOG*'
  } | ForEach-Object {
    L ('Stopping PID=' + $_.ProcessId + ' CMD=' + $_.CommandLine)
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
} catch { L ('Kill warning: ' + $_.Exception.Message) }

Start-Sleep -Seconds 3

L 'Removing git locks'
Remove-Item (Join-Path $BridgeRoot '.git\index.lock') -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $BridgeRoot '.git\shallow.lock') -Force -ErrorAction SilentlyContinue

L 'Syncing bridge repo with origin/main'
try {
  git fetch origin main 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $Log
  git reset --hard origin/main 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $Log
} catch { L ('Git sync warning: ' + $_.Exception.Message) }

L 'Starting watchdog script'
try {
  $start = Join-Path $BridgeRoot 'START_AAYS_USERMODE_WATCHDOG.ps1'
  if (Test-Path $start) {
    powershell -NoProfile -ExecutionPolicy Bypass -File $start 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $Log
  } else {
    L 'START_AAYS_USERMODE_WATCHDOG.ps1 not found'
  }
} catch { L ('Start watchdog warning: ' + $_.Exception.Message) }

Start-Sleep -Seconds 5

L 'Reading status files'
try {
  $runnerHb = Join-Path $BridgeRoot 'ai-heartbeat\runner-v4.md'
  $watchdogHb = Join-Path $BridgeRoot 'ai-heartbeat\user-mode-watchdog.md'
  $task = Join-Path $BridgeRoot 'ai-tasks\current-task.json'
  if (Test-Path $task) { L 'CURRENT TASK:'; Get-Content -Raw $task | Tee-Object -FilePath $Log -Append | Write-Host }
  if (Test-Path $runnerHb) { L 'RUNNER HEARTBEAT:'; Get-Content -Raw $runnerHb | Tee-Object -FilePath $Log -Append | Write-Host }
  if (Test-Path $watchdogHb) { L 'WATCHDOG HEARTBEAT:'; Get-Content -Raw $watchdogHb | Tee-Object -FilePath $Log -Append | Write-Host }
} catch { L ('Status read warning: ' + $_.Exception.Message) }

L 'AAYS force restart finished'
L ('LOG=' + $Log)

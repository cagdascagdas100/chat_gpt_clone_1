$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
$Runner = Join-Path $BridgeRoot 'AAYS_REMOTE_AUTOPILOT_V84_SINGLE.ps1'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
$HeartbeatDir = Join-Path $BridgeRoot 'ai-heartbeat'
$StartupDir = [Environment]::GetFolderPath('Startup')
$StartupCmd = Join-Path $StartupDir 'AAYS_V84_USERMODE_KEEPALIVE.cmd'
$WatchdogPs1 = Join-Path $BridgeRoot 'AAYS_V84_USERMODE_WATCHDOG.ps1'
New-Item -ItemType Directory -Force -Path $LogDir,$HeartbeatDir | Out-Null

function Log($m) {
  $line = '[' + (Get-Date -Format 's') + '] ' + $m
  Write-Host $line
  Add-Content -Encoding UTF8 -Path (Join-Path $LogDir 'v84-usermode-keepalive-install.log') -Value $line
}

Log 'INSTALL_START'
Set-Location $BridgeRoot

Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -match 'AAYS_REMOTE_AUTOPILOT_V7\.ps1|AAYS_REMOTE_AUTOPILOT_V8_SINGLE\.ps1|AAYS_REMOTE_AUTOPILOT_V81_SINGLE\.ps1|AAYS_REMOTE_AUTOPILOT_V82_SINGLE\.ps1|AAYS_REMOTE_AUTOPILOT_V83_SINGLE\.ps1|AAYS_REMOTE_AUTOPILOT_V84_SINGLE\.ps1|AAYS_PORTABLE_TASK_RUNNER_FIXED\.ps1|git.exe|credential-manager'
} | ForEach-Object {
  Log ('STOP_PID=' + $_.ProcessId)
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2
Remove-Item (Join-Path $BridgeRoot '.git\index.lock') -Force -ErrorAction SilentlyContinue

git fetch origin main
git checkout -B main origin/main
git reset --hard origin/main

$watchdog = @"
`$ErrorActionPreference = 'Continue'
`$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN'
`$Runner = Join-Path `$BridgeRoot 'AAYS_REMOTE_AUTOPILOT_V84_SINGLE.ps1'
`$LogDir = Join-Path `$BridgeRoot 'ai-runner-logs'
New-Item -ItemType Directory -Force -Path `$LogDir | Out-Null
function WLog(`$m) { Add-Content -Encoding UTF8 -Path (Join-Path `$LogDir 'v84-usermode-watchdog.log') -Value ('[' + (Get-Date -Format 's') + '] ' + `$m) }
while (`$true) {
  try {
    `$p = Get-CimInstance Win32_Process | Where-Object { `$_.CommandLine -match 'AAYS_REMOTE_AUTOPILOT_V84_SINGLE\.ps1' }
    if (-not `$p) {
      WLog 'START_V84'
      Start-Process powershell.exe -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File C:\AAYS_GITHUB_BRIDGE_CLEAN\AAYS_REMOTE_AUTOPILOT_V84_SINGLE.ps1' -WorkingDirectory 'C:\AAYS_GITHUB_BRIDGE_CLEAN' -WindowStyle Minimized
    } else {
      WLog ('V84_RUNNING_COUNT=' + (`$p | Measure-Object).Count)
    }
  } catch { WLog ('ERROR=' + `$_.Exception.Message) }
  Start-Sleep -Seconds 60
}
"@
Set-Content -Encoding UTF8 -Path $WatchdogPs1 -Value $watchdog

$cmd = '@echo off' + "`r`n" + 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\AAYS_GITHUB_BRIDGE_CLEAN\AAYS_V84_USERMODE_WATCHDOG.ps1"'
Set-Content -Encoding ASCII -Path $StartupCmd -Value $cmd

Start-Process powershell.exe -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File C:\AAYS_GITHUB_BRIDGE_CLEAN\AAYS_V84_USERMODE_WATCHDOG.ps1' -WorkingDirectory $BridgeRoot -WindowStyle Minimized
Start-Sleep -Seconds 10

$p2 = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'AAYS_REMOTE_AUTOPILOT_V84_SINGLE\.ps1|AAYS_V84_USERMODE_WATCHDOG\.ps1' } | Select-Object ProcessId, CommandLine
$p2 | Format-Table -AutoSize
Get-Content (Join-Path $HeartbeatDir 'remote-autopilot-v84.md') -ErrorAction SilentlyContinue
Log 'INSTALL_DONE'

$ErrorActionPreference = 'Continue'

$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$TaskName = 'AAYS-CLEAN2-Portable-Runner-Watchdog'
$WatchdogPath = Join-Path $BridgeRoot 'AAYS_CLEAN2_RUNNER_WATCHDOG.ps1'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Watchdog = @'
$ErrorActionPreference = 'Continue'
$BridgeRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Runner = Join-Path $BridgeRoot 'AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1'
$LogDir = Join-Path $BridgeRoot 'ai-runner-logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ('clean2-watchdog-' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.log')
function W([string]$m){ $line='['+(Get-Date -Format s)+'] '+$m; Write-Output $line; Add-Content -Encoding UTF8 -Path $Log -Value $line }
W 'CLEAN2 watchdog started'
while($true){
  try{
    Get-CimInstance Win32_Process |
      Where-Object {
        ($_.CommandLine -match 'continue-safe-runner') -or
        ($_.CommandLine -match 'C:\\Users\\cagda\\Documents\\chat_gpt_clone_1')
      } |
      ForEach-Object { W ('Stopping wrong runner PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

    $clean2 = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'AAYS_PORTABLE_TASK_RUNNER_FIXED\.ps1' -and $_.CommandLine -match 'C:\\AAYS_GITHUB_BRIDGE_CLEAN2' })
    if($clean2.Count -eq 0){
      W 'Starting CLEAN2 portable runner'
      Set-Location $BridgeRoot
      Remove-Item '.\.git\index.lock' -Force -ErrorAction SilentlyContinue
      git merge --abort 2>$null | Out-Null
      git rebase --abort 2>$null | Out-Null
      git fetch origin main 2>&1 | Out-Null
      git reset --hard origin/main 2>&1 | Out-Null
      Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$Runner) -WorkingDirectory $BridgeRoot
    } elseif($clean2.Count -gt 1){
      $keep = $clean2 | Select-Object -First 1
      $clean2 | Select-Object -Skip 1 | ForEach-Object { W ('Stopping duplicate CLEAN2 runner PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
      W ('Kept CLEAN2 runner PID ' + $keep.ProcessId)
    } else {
      W ('CLEAN2 runner OK PID ' + $clean2[0].ProcessId)
    }
  } catch { W ('WATCHDOG_ERROR ' + $_.Exception.Message) }
  Start-Sleep -Seconds 60
}
'@

Set-Content -Encoding UTF8 -Path $WatchdogPath -Value $Watchdog

$Action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "' + $WatchdogPath + '"')
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DisallowStartIfOnBatteries:$false -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description 'Keeps AAYS CLEAN2 portable runner alive and stops wrong safe runner.' -Force | Out-Null

Write-Output 'AAYS CLEAN2 runner watchdog installed.'
Write-Output ('TaskName=' + $TaskName)
Write-Output ('WatchdogPath=' + $WatchdogPath)
Write-Output 'Starting watchdog now...'
Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$WatchdogPath) -WorkingDirectory $BridgeRoot

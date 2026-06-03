$ErrorActionPreference='Stop'
$BridgeRoot='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$Runner=Join-Path $BridgeRoot 'AAYS_PORTABLE_TASK_RUNNER_FIXED.ps1'
$TaskName='AAYS-GitHub-Bridge-CLEAN2-Runner'
$KickName='AAYS-GitHub-Bridge-CLEAN2-Kick'
if(-not (Test-Path $BridgeRoot)){throw "Bridge root not found: $BridgeRoot"}
if(-not (Test-Path $Runner)){throw "Runner not found: $Runner"}
$Action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`"" -WorkingDirectory $BridgeRoot
$Trigger=New-ScheduledTaskTrigger -AtLogOn
$Settings=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 12)
try{Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue}catch{}
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description 'Keeps AAYS GitHub bridge runner available after login.' | Out-Null
$KickAction=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Runner`"" -WorkingDirectory $BridgeRoot
$KickTrigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
$KickSettings=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 3)
try{Unregister-ScheduledTask -TaskName $KickName -Confirm:$false -ErrorAction SilentlyContinue}catch{}
Register-ScheduledTask -TaskName $KickName -Action $KickAction -Trigger $KickTrigger -Settings $KickSettings -Description 'Immediate one-shot kick for AAYS GitHub bridge runner.' | Out-Null
Start-ScheduledTask -TaskName $KickName
Write-Output "INSTALLED_TASK=$TaskName"
Write-Output "STARTED_KICK_TASK=$KickName"
Write-Output "BRIDGE_ROOT=$BridgeRoot"
Write-Output "RUNNER=$Runner"
Write-Output 'NEXT_WAIT_MINUTES=3-5'

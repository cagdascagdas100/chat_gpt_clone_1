$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$WatchdogFile = "C:\Users\cagda\Documents\chat_gpt_clone_1\AAYS_USERMODE_WATCHDOG.ps1"
Set-Location $BridgeRoot
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$WatchdogFile`"" -WorkingDirectory $BridgeRoot -WindowStyle Minimized
Write-Host "AAYS user-mode watchdog başlatıldı."

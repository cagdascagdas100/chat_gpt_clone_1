$targets = Get-CimInstance Win32_Process -Filter "name = 'powershell.exe' OR name = 'pwsh.exe'" |
    Where-Object {
        $_.CommandLine -and (
            $_.CommandLine -like "*AAYS_USERMODE_WATCHDOG.ps1*" -or
            $_.CommandLine -like "*AAYS_CHATGPT_RUNNER_V4.ps1*"
        )
    }

foreach ($p in $targets) {
    try {
        Stop-Process -Id $p.ProcessId -Force
        Write-Host "Stopped PID=$($p.ProcessId)"
    } catch {
        Write-Host "Stop failed PID=$($p.ProcessId): $($_.Exception.Message)"
    }
}

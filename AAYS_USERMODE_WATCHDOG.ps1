$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$RunnerFile = Join-Path $BridgeRoot "AAYS_CHATGPT_RUNNER_V4.ps1"
$LogDir = Join-Path $BridgeRoot "ai-runner-logs"
$HeartbeatDir = Join-Path $BridgeRoot "ai-heartbeat"
$LogFile = Join-Path $LogDir "user-mode-watchdog.log"
$HeartbeatFile = Join-Path $HeartbeatDir "user-mode-watchdog.md"

New-Item -ItemType Directory -Force -Path $LogDir, $HeartbeatDir | Out-Null

function Log([string]$Text) {
    $line = "[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] " + $Text
    Write-Host $line
    Add-Content -Encoding UTF8 -Path $LogFile -Value $line
}

function WriteBeat([string]$Status) {
    $txt = "# AAYS User Mode Watchdog`n`nTime: $(Get-Date)`nStatus: $Status`nBridgeRoot: $BridgeRoot`nRunnerFile: $RunnerFile`nLogFile: $LogFile`n"
    Set-Content -Encoding UTF8 -Path $HeartbeatFile -Value $txt
}

function RunnerRunning {
    try {
        $p = Get-CimInstance Win32_Process -Filter "name = 'powershell.exe' OR name = 'pwsh.exe'" |
            Where-Object { $_.CommandLine -and $_.CommandLine -like "*AAYS_CHATGPT_RUNNER_V4.ps1*" }
        return (($p | Measure-Object).Count -gt 0)
    } catch {
        return $false
    }
}

function PushBridge([string]$Msg) {
    try {
        Set-Location $BridgeRoot
        git add ai-heartbeat ai-runner-logs ai-results ai-tasks AAYS_USERMODE_WATCHDOG.ps1 START_AAYS_USERMODE_WATCHDOG.ps1 STOP_AAYS_USERMODE_WATCHDOG.ps1 2>$null | Out-Null
        $s = git status --short
        if ($s) {
            git commit -m $Msg | Out-Null
            git pull --rebase origin main | Out-Null
            git push | Out-Null
        }
    } catch {
        Log ("GIT_PUSH_WARN: " + $_.Exception.Message)
    }
}

Log "User-mode watchdog başladı."
WriteBeat "started"
PushBridge "User-mode watchdog started"

$lastPush = Get-Date

while ($true) {
    try {
        Set-Location $BridgeRoot

        if (Test-Path ".git") {
            git pull --rebase origin main | Out-Null
        }

        if (!(Test-Path $RunnerFile)) {
            Log "Runner dosyası yok: $RunnerFile"
            WriteBeat "runner-file-missing"
            Start-Sleep -Seconds 30
            continue
        }

        if (RunnerRunning) {
            Log "Runner V4 çalışıyor."
            WriteBeat "runner-running"
        } else {
            Log "Runner V4 kapalı. Yeniden başlatılıyor."
            Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$RunnerFile`"" -WorkingDirectory $BridgeRoot -WindowStyle Minimized
            Start-Sleep -Seconds 5

            if (RunnerRunning) {
                Log "Runner V4 başarıyla başlatıldı."
                WriteBeat "runner-restarted"
            } else {
                Log "Runner V4 başlatılamadı."
                WriteBeat "runner-restart-failed"
            }
        }

        if (((Get-Date) - $lastPush).TotalSeconds -ge 120) {
            PushBridge "User-mode watchdog heartbeat"
            $lastPush = Get-Date
        }

        Start-Sleep -Seconds 30
    } catch {
        Log ("WATCHDOG_ERROR: " + $_.Exception.Message)
        WriteBeat ("error " + $_.Exception.Message)
        Start-Sleep -Seconds 30
    }
}

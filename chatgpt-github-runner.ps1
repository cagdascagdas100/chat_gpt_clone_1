$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$AllowedProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"

$TaskFile = Join-Path $BridgeRoot "ai-tasks\current-task.json"
$StateFile = Join-Path $BridgeRoot "ai-tasks\.last-task-id"
$ResultDir = Join-Path $BridgeRoot "ai-results"

New-Item -ItemType Directory -Force -Path (Split-Path $TaskFile -Parent), $ResultDir | Out-Null

function RunnerLog {
    param([string]$Text)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Text"
}

function IsPathAllowed {
    param([string]$Path)

    try {
        $full = [System.IO.Path]::GetFullPath($Path)
        $allowed = [System.IO.Path]::GetFullPath($AllowedProjectRoot)
        return $full.StartsWith($allowed, [System.StringComparison]::OrdinalIgnoreCase)
    } catch {
        return $false
    }
}

function IsCommandBlocked {
    param([string]$Command)

    $blockedPatterns = @(
        'Remove-Item\s+-Recurse\s+-Force\s+C:\\',
        'rm\s+-rf',
        'Format-Volume',
        'Clear-Disk',
        'Remove-Partition',
        'Set-ExecutionPolicy',
        'reg\s+delete',
        'shutdown',
        'Restart-Computer',
        'Stop-Computer',
        'cipher\s+/w',
        'takeown\s+',
        'icacls\s+.*\/grant',
        'net\s+user',
        'New-LocalUser',
        'Set-LocalUser',
        'Invoke-Expression',
        '\biex\b'
    )

    foreach ($pattern in $blockedPatterns) {
        if ($Command -match $pattern) {
            return $true
        }
    }

    return $false
}
RunnerLog "ChatGPT GitHub runner basladi."
RunnerLog "Bridge root: $BridgeRoot"
RunnerLog "Allowed project root: $AllowedProjectRoot"
RunnerLog "Task file: $TaskFile"
RunnerLog "Bu pencere acik kalmali. Durdurmak icin Ctrl+C."

while ($true) {
    try {
        Set-Location $BridgeRoot

        git pull --rebase origin main | Out-Null

        if (!(Test-Path $TaskFile)) {
            Start-Sleep -Seconds 8
            continue
        }

        $taskRaw = Get-Content -Raw -Encoding UTF8 $TaskFile
        $task = $taskRaw | ConvertFrom-Json

        if (!$task.id) {
            RunnerLog "Task id yok. Bekleniyor."
            Start-Sleep -Seconds 8
            continue
        }

        $lastId = ""
        if (Test-Path $StateFile) {
            $lastId = (Get-Content -Raw -Encoding UTF8 $StateFile).Trim()
        }

        if ($lastId -eq $task.id.Trim()) {
            Start-Sleep -Seconds 8
            continue
        }

        $taskId = [string]$task.id
        $title = [string]$task.title
        $progress = [string]$task.progress
        $workdir = [string]$task.working_directory
        $command = [string]$task.command
$action = [string]$task.action

if ([string]::IsNullOrWhiteSpace($command) -and $action -eq "health_check") {
    $command = "Write-Output 'TASK: Otomasyon saglik kontrolu'; Write-Output 'PROGRESS: 20%'; Write-Output 'STATUS: Runner action modunu otomatik calistirdi.'; Write-Output 'WORKDIR:'; Get-Location; Write-Output 'TIME:'; Get-Date"
}
elseif ([string]::IsNullOrWhiteSpace($command) -and $action -eq "preflight") {
    $command = "Write-Output 'TASK: TerraYield preflight'; Write-Output 'PROGRESS: 30%'; Write-Output 'PROJECT:'; Get-Location; Write-Output 'FILES:'; Get-ChildItem -Force | Select-Object Name,Mode,Length | Out-String"
}
elseif ([string]::IsNullOrWhiteSpace($command)) {
    $command = "Write-Output 'UNKNOWN_OR_EMPTY_ACTION'; Write-Output 'Action:'; Write-Output '$action'"
}

        if ([string]::IsNullOrWhiteSpace($title)) {
            $title = "Untitled task"
        }

        if ([string]::IsNullOrWhiteSpace($progress)) {
            $progress = "0"
        }

        if ([string]::IsNullOrWhiteSpace($workdir)) {
            $workdir = $AllowedProjectRoot
        }

        RunnerLog "Yeni gorev bulundu: $taskId"
        RunnerLog "TASK: $title"
        RunnerLog "PROGRESS: $progress%"
        RunnerLog "WORKDIR: $workdir"

        $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
        $safeId = ($taskId -replace '[^a-zA-Z0-9_-]+', '-')
        $resultPath = Join-Path $ResultDir "$timestamp-$safeId.md"

        if (!(Test-Path $workdir)) {
            $exitCode = 9001
            $output = "WORKDIR_NOT_FOUND: $workdir"
        }
        elseif (!(IsPathAllowed $workdir)) {
            $exitCode = 9002
            $output = "WORKDIR_BLOCKED_BY_RUNNER. Allowed root: $AllowedProjectRoot"
        }
        elseif (IsCommandBlocked $command) {
            $exitCode = 9003
            $output = "COMMAND_BLOCKED_BY_RUNNER_SAFETY_POLICY`n$command"
        }
        else {
            Set-Location $workdir
            $output = powershell -NoProfile -Command $command 2>&1 | Out-String
            $exitCode = $LASTEXITCODE
        }

        $lines = @()
        $lines += "# ChatGPT Runner Result"
        $lines += ""
        $lines += "## Task"
        $lines += $title
        $lines += ""
        $lines += "## Task ID"
        $lines += $taskId
        $lines += ""
        $lines += "## Progress"
        $lines += "$progress%"
        $lines += ""
        $lines += "## Time"
        $lines += "$(Get-Date)"
        $lines += ""
        $lines += "## Working Directory"
        $lines += $workdir
        $lines += ""
        $lines += "## Exit Code"
        $lines += "$exitCode"
        $lines += ""
        $lines += "## Command"
        $lines += $command
        $lines += ""
        $lines += "## Output"
        $lines += $output

        $lines -join "`r`n" | Set-Content -Encoding UTF8 $resultPath

        $taskId | Set-Content -Encoding UTF8 $StateFile

        Set-Location $BridgeRoot
        git pull --rebase origin main | Out-Null
        git add ai-results ai-tasks | Out-Null
        git commit -m "Runner result $taskId" | Out-Null
        git push | Out-Null

        RunnerLog "Sonuc GitHub'a push edildi: $resultPath"
    }
    catch {
        RunnerLog "RUNNER ERROR: $($_.Exception.Message)"
    }

    Start-Sleep -Seconds 8
}


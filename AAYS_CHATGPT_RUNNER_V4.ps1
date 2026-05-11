$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$TaskFile = Join-Path $BridgeRoot "ai-tasks\current-task.json"
$StateFile = Join-Path $BridgeRoot "ai-tasks\.last-task-id"
$ResultDir = Join-Path $BridgeRoot "ai-results"
$HeartbeatDir = Join-Path $BridgeRoot "ai-heartbeat"
$RunnerLogDir = Join-Path $BridgeRoot "ai-runner-logs"
$TmpDir = Join-Path $BridgeRoot "ai-tmp"

New-Item -ItemType Directory -Force -Path (Split-Path $TaskFile -Parent), $ResultDir, $HeartbeatDir, $RunnerLogDir, $TmpDir | Out-Null
$RunnerLog = Join-Path $RunnerLogDir ("runner-v4-" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
$IoMutexName = "Global\AAYS_CHATGPT_RUNNER_V4_FILE_IO"

function SafeWriteText([string]$Path, [string]$Text) {
    $ok = $false
    for ($i = 1; $i -le 12; $i++) {
        $mutex = $null
        try {
            $mutex = New-Object System.Threading.Mutex($false, $IoMutexName)
            [void]$mutex.WaitOne(3000)
            $dir = Split-Path $Path -Parent
            if (!(Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
            $tmp = Join-Path $dir ("." + [System.IO.Path]::GetFileName($Path) + ".tmp." + [guid]::NewGuid().ToString("N"))
            [System.IO.File]::WriteAllText($tmp, $Text, [System.Text.UTF8Encoding]::new($true))
            Move-Item -Force -Path $tmp -Destination $Path
            $ok = $true
            break
        } catch [System.Management.Automation.PipelineStoppedException] {
            Start-Sleep -Milliseconds (250 * $i)
        } catch [System.IO.IOException] {
            Start-Sleep -Milliseconds (250 * $i)
        } catch {
            Start-Sleep -Milliseconds (250 * $i)
        } finally {
            try { if ($mutex) { $mutex.ReleaseMutex() | Out-Null; $mutex.Dispose() } } catch {}
        }
    }
    return $ok
}

function SafeAppendLine([string]$Path, [string]$Text) {
    for ($i = 1; $i -le 8; $i++) {
        try {
            $dir = Split-Path $Path -Parent
            if (!(Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
            Add-Content -Encoding UTF8 -Path $Path -Value $Text
            return $true
        } catch [System.Management.Automation.PipelineStoppedException] {
            Start-Sleep -Milliseconds (200 * $i)
        } catch [System.IO.IOException] {
            Start-Sleep -Milliseconds (200 * $i)
        } catch {
            Start-Sleep -Milliseconds (200 * $i)
        }
    }
    return $false
}

function Say([string]$Text) {
    $line = "[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] " + $Text
    try { Write-Host $line } catch {}
    [void](SafeAppendLine $RunnerLog $line)
}

function Heartbeat([string]$Status) {
    $path = Join-Path $HeartbeatDir "runner-v4.md"
    $txt = "# AAYS ChatGPT Runner V4`n`nTime: $(Get-Date)`nStatus: $Status`nBridgeRoot: $BridgeRoot`nProjectRoot: $ProjectRoot`nTaskFile: $TaskFile`nRunnerLog: $RunnerLog`nPipelineStoppedHandling: enabled`nFileLockRetry: enabled`nPageJobTracking: enabled`n"
    $ok = SafeWriteText $path $txt
    if (-not $ok) { Say "HEARTBEAT_WRITE_RETRY_FAILED: $Status" }
}

function PushBridge([string]$Message) {
    try {
        Set-Location $BridgeRoot
        git config --local pull.rebase false | Out-Null
        git add ai-results ai-heartbeat ai-runner-logs ai-tasks ai-page-jobs AAYS_CHATGPT_RUNNER_V4.ps1 2>$null | Out-Null
        $s = git status --short 2>$null
        if ($s) {
            git commit -m $Message | Out-Null
            git fetch origin main --prune | Out-Null
            git pull --ff-only origin main | Out-Null
            git push | Out-Null
        }
    } catch [System.Management.Automation.PipelineStoppedException] {
        Say "GIT_PUSH_PIPELINE_STOPPED_CONTINUING"
    } catch {
        Say ("GIT_PUSH_ERROR_CONTINUING: " + $_.Exception.Message)
    }
}

function Allowed([string]$Path) {
    try {
        $full = [System.IO.Path]::GetFullPath($Path)
        $allowed = [System.IO.Path]::GetFullPath($ProjectRoot)
        return $full.StartsWith($allowed, [System.StringComparison]::OrdinalIgnoreCase)
    } catch { return $false }
}

function Blocked([string]$Command) {
    if ([string]::IsNullOrWhiteSpace($Command)) { return $false }
    $patterns = @('Remove-Item\s+-Recurse\s+-Force\s+C:\\','rm\s+-rf','Format-Volume','Clear-Disk','Remove-Partition','Set-ExecutionPolicy','reg\s+delete','shutdown','Restart-Computer','Stop-Computer','cipher\s+/w','takeown\s+','New-LocalUser','Set-LocalUser','net\s+user','\biex\b')
    foreach ($p in $patterns) { if ($Command -match $p) { return $true } }
    return $false
}

function ActionScript([string]$Action) {
    if ($Action -eq "health_check") { return "Write-Output 'TASK: Runner V4 health check'; Write-Output 'STATUS: Runner V4 calisiyor'; Get-Date" }
    if ($Action -eq "status_check") { return "Write-Output 'TASK: TerraYield status check'; Write-Output 'STATUS: status probe'; git status --short" }
    return "Write-Output 'UNKNOWN_ACTION: $Action'"
}

function RunTask([string]$ScriptText, [string]$Workdir, [int]$TimeoutSeconds, [string]$TaskId) {
    $safe = $TaskId -replace '[^a-zA-Z0-9_-]+','-'
    $scriptPath = Join-Path $TmpDir ("task-" + $safe + ".ps1")
    SafeWriteText $scriptPath $ScriptText | Out-Null
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "powershell.exe"
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
    $psi.WorkingDirectory = $Workdir
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $psi
    try { [void]$p.Start() } catch { return [PSCustomObject]@{ ExitCode=997; Output="PROCESS_START_FAILED"; Error=$_.Exception.Message } }
    $outTask = $p.StandardOutput.ReadToEndAsync()
    $errTask = $p.StandardError.ReadToEndAsync()
    $done = $p.WaitForExit($TimeoutSeconds * 1000)
    if (-not $done) {
        try { $p.Kill() } catch {}
        return [PSCustomObject]@{ ExitCode=124; Output=$outTask.Result; Error=$errTask.Result + "`nTIMEOUT_AFTER_SECONDS=$TimeoutSeconds" }
    }
    return [PSCustomObject]@{ ExitCode=$p.ExitCode; Output=$outTask.Result; Error=$errTask.Result }
}

Say "AAYS ChatGPT Runner V4 basladi."
Say "PipelineStopped ve file-lock korumasi aktif."
Say "ai-page-jobs izleme aktif."
Say "Bu pencere acik kalmali. Bundan sonra webde sadece devam et yaz."
Heartbeat "started"
PushBridge "Runner V4 hardened page jobs started"

while ($true) {
    try {
        Set-Location $BridgeRoot
        try { git config --local pull.rebase false | Out-Null; git fetch origin main --prune | Out-Null; git pull --ff-only origin main | Out-Null } catch { Say ("GIT_PULL_CONTINUING: " + $_.Exception.Message) }
        Heartbeat "polling"
        if (!(Test-Path $TaskFile)) { Say "Bekliyor: current-task.json yok."; PushBridge "Runner V4 heartbeat no task"; Start-Sleep -Seconds 10; continue }
        $task = (Get-Content -Raw -Encoding UTF8 $TaskFile) | ConvertFrom-Json
        $taskId = [string]$task.id
        if ([string]::IsNullOrWhiteSpace($taskId)) { Say "Bekliyor: task id yok."; Start-Sleep -Seconds 10; continue }
        $lastId = ""
        if (Test-Path $StateFile) { $lastId = (Get-Content -Raw -Encoding UTF8 $StateFile).Trim() }
        if ($lastId -eq $taskId.Trim()) { Say "Bekliyor: yeni aktif paket yok. Son paket=$lastId"; Start-Sleep -Seconds 10; continue }
        $title = if ($task.title) { [string]$task.title } else { "Untitled task" }
        $progress = if ($task.progress -ne $null) { [int]$task.progress } else { 0 }
        $action = if ($task.action) { [string]$task.action } else { "" }
        $workdir = if ($task.working_directory) { [string]$task.working_directory } else { $ProjectRoot }
        $command = if ($task.command) { [string]$task.command } else { "" }
        $timeout = if ($task.timeout_seconds -ne $null) { [int]$task.timeout_seconds } else { 600 }
        if ($timeout -lt 30) { $timeout = 30 }
        if ($timeout -gt 14400) { $timeout = 14400 }
        Say "Aktif paket bulundu: $taskId | $title | $progress% | action=$action | timeout=$timeout"
        Heartbeat "running $taskId"
        $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
        $safeId = $taskId -replace '[^a-zA-Z0-9_-]+','-'
        $resultPath = Join-Path $ResultDir ("$timestamp-$safeId.md")
        if (!(Allowed $workdir)) { $exitCode=9001; $output="WORKDIR_NOT_ALLOWED: $workdir"; $errorText="" }
        elseif ([string]::IsNullOrWhiteSpace($command)) { $command = ActionScript $action; if (Blocked $command) { $exitCode=9002; $output="BLOCKED_BY_RUNNER_SAFETY_POLICY"; $errorText=$command } else { $r=RunTask $command $workdir $timeout $taskId; $exitCode=$r.ExitCode; $output=$r.Output; $errorText=$r.Error } }
        else { if (Blocked $command) { $exitCode=9002; $output="BLOCKED_BY_RUNNER_SAFETY_POLICY"; $errorText=$command } else { $r=RunTask $command $workdir $timeout $taskId; $exitCode=$r.ExitCode; $output=$r.Output; $errorText=$r.Error } }
        $md = "# AAYS ChatGPT Runner V4 Result`n`n## Task`n$title`n`n## Task ID`n$taskId`n`n## Progress`n$progress%`n`n## Action`n$action`n`n## Time`n$(Get-Date)`n`n## Working Directory`n$workdir`n`n## Timeout Seconds`n$timeout`n`n## Exit Code`n$exitCode`n`n## Output`n````text`n$output`n`````n`n## Error`n````text`n$errorText`n`````n"
        SafeWriteText $resultPath $md | Out-Null
        SafeWriteText $StateFile $taskId | Out-Null
        Heartbeat "finished $taskId exit=$exitCode"
        PushBridge "Runner V4 result $taskId"
        Say "Paket bitti. ExitCode=$exitCode Sonuc=$resultPath"
    } catch [System.Management.Automation.PipelineStoppedException] {
        Say "RUNNER_PIPELINE_STOPPED_CAUGHT_CONTINUING"; Heartbeat "pipeline-stopped-caught-continuing"; PushBridge "Runner V4 pipeline stopped caught"; Start-Sleep -Seconds 5
    } catch {
        Say ("RUNNER_ERROR_CONTINUING: " + $_.Exception.Message); Heartbeat ("error-continuing " + $_.Exception.Message); PushBridge "Runner V4 error continuing"; Start-Sleep -Seconds 10
    }
}



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

function Say([string]$Text) {
    $line = "[" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + "] " + $Text
    Write-Host $line
    Add-Content -Encoding UTF8 -Path $RunnerLog -Value $line
}

function Heartbeat([string]$Status) {
    $path = Join-Path $HeartbeatDir "runner-v4.md"
    $txt = "# AAYS ChatGPT Runner V4`n`nTime: $(Get-Date)`nStatus: $Status`nBridgeRoot: $BridgeRoot`nProjectRoot: $ProjectRoot`nTaskFile: $TaskFile`nRunnerLog: $RunnerLog`n"
    Set-Content -Encoding UTF8 -Path $path -Value $txt
}

function PushBridge([string]$Message) {
    try {
        Set-Location $BridgeRoot
        git add ai-results ai-heartbeat ai-runner-logs ai-tasks AAYS_CHATGPT_RUNNER_V4.ps1 2>$null | Out-Null
        $s = git status --short 2>$null
        if ($s) {
            git commit -m $Message | Out-Null
            git pull --rebase origin main | Out-Null
            git push | Out-Null
        }
    } catch {
        Say ("GIT_PUSH_ERROR: " + $_.Exception.Message)
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
    $patterns = @('Remove-Item\s+-Recurse\s+-Force\s+C:\\','rm\s+-rf','Format-Volume','Clear-Disk','Remove-Partition','Set-ExecutionPolicy','reg\s+delete','shutdown','Restart-Computer','Stop-Computer','cipher\s+/w','takeown\s+','New-LocalUser','Set-LocalUser','net\s+user','\biex\b','Invoke-Expression')
    foreach ($p in $patterns) { if ($Command -match $p) { return $true } }
    return $false
}

function ActionScript([string]$Action) {
    if ($Action -eq "health_check") {
        return "Write-Output 'TASK: Runner V4 health check'; Write-Output 'PROGRESS: 5%'; Write-Output 'STATUS: Runner V4 calisiyor'; Get-Date; docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml ps; try { `$r=Invoke-WebRequest -Uri 'http://localhost:8010/health' -UseBasicParsing -TimeoutSec 10; Write-Output ('OK /health ' + `$r.StatusCode) } catch { Write-Output ('FAIL /health ' + `$_.Exception.Message) }"
    }
    if ($Action -eq "status_check") {
        return "$endpoints=@('/health','/openapi.json','/map/listings','/map/sales-layers/verified-history','/map/sales-history/status','/map/sales-history/external-evidence','/map/sales-history/parcels','/map/sales-history/combined'); Write-Output 'TASK: TerraYield status check'; Write-Output 'PROGRESS: 100%'; docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml ps; docker inspect terrayield_land_api --format '{{json .Config.Cmd}}'; foreach (`$ep in `$endpoints) { try { `$sw=[System.Diagnostics.Stopwatch]::StartNew(); `$r=Invoke-WebRequest -Uri ('http://localhost:8010'+`$ep) -UseBasicParsing -TimeoutSec 45; `$sw.Stop(); Write-Output ('OK ' + `$ep + ' status=' + `$r.StatusCode + ' ms=' + `$sw.ElapsedMilliseconds + ' bytes=' + `$r.Content.Length) } catch { Write-Output ('FAIL ' + `$ep + ' error=' + `$_.Exception.Message) } }"
    }
    if ($Action -eq "fast_restart") {
        return "Write-Output 'TASK: TerraYield fast API restart'; Write-Output 'PROGRESS: 80%'; `$start=Get-Date; docker compose -f docker-compose.yml -f docker-compose.aays-fast-start.yml up -d --no-deps --force-recreate api; `$ready=`$false; for (`$i=1; `$i -le 72; `$i++) { Start-Sleep -Seconds 5; try { `$r=Invoke-WebRequest -Uri 'http://localhost:8010/health' -UseBasicParsing -TimeoutSec 5; `$elapsed=[int]((Get-Date)-`$start).TotalSeconds; Write-Output ('READY /health status=' + `$r.StatusCode + ' elapsed=' + `$elapsed + 's'); `$ready=`$true; break } catch { `$elapsed=[int]((Get-Date)-`$start).TotalSeconds; Write-Output ('WAIT ' + `$i + '/72 elapsed=' + `$elapsed + 's') } }; if (-not `$ready) { docker logs --tail 180 terrayield_land_api; exit 1 }; Write-Output 'FAST_RESTART_DONE'"
    }
    return "Write-Output 'UNKNOWN_ACTION: $Action'"
}

function RunTask([string]$ScriptText, [string]$Workdir, [int]$TimeoutSeconds, [string]$TaskId) {
    $safe = $TaskId -replace '[^a-zA-Z0-9_-]+','-'
    $scriptPath = Join-Path $TmpDir ("task-" + $safe + ".ps1")
    Set-Content -Encoding UTF8 -Path $scriptPath -Value $ScriptText
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
    [void]$p.Start()
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
Say "Bu pencere acik kalmali. Bundan sonra webde sadece devam et yaz."
Heartbeat "started"
PushBridge "Runner V4 started"

while ($true) {
    try {
        Set-Location $BridgeRoot
        git pull --rebase origin main | Out-Null
        Heartbeat "polling"
        if (!(Test-Path $TaskFile)) { Say "Bekliyor: current-task.json yok."; PushBridge "Runner V4 heartbeat no task"; Start-Sleep -Seconds 10; continue }
        $task = (Get-Content -Raw -Encoding UTF8 $TaskFile) | ConvertFrom-Json
        $taskId = [string]$task.id
        if ([string]::IsNullOrWhiteSpace($taskId)) { Say "Bekliyor: task id yok."; Start-Sleep -Seconds 10; continue }
        $lastId = ""
        if (Test-Path $StateFile) { $lastId = (Get-Content -Raw -Encoding UTF8 $StateFile).Trim() }
        if ($lastId -eq $taskId.Trim()) { Say "Bekliyor: yeni gorev yok. Son gorev=$lastId"; Start-Sleep -Seconds 10; continue }
        $title = if ($task.title) { [string]$task.title } else { "Untitled task" }
        $progress = if ($task.progress -ne $null) { [int]$task.progress } else { 0 }
        $action = if ($task.action) { [string]$task.action } else { "" }
        $workdir = if ($task.working_directory) { [string]$task.working_directory } else { $ProjectRoot }
        $command = if ($task.command) { [string]$task.command } else { "" }
        $timeout = if ($task.timeout_seconds -ne $null) { [int]$task.timeout_seconds } else { 600 }
        if ($timeout -lt 30) { $timeout = 30 }
        if ($timeout -gt 1800) { $timeout = 1800 }
        Say "Yeni gorev bulundu: $taskId | $title | $progress% | action=$action | timeout=$timeout"
        Heartbeat "running $taskId"
        $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
        $safeId = $taskId -replace '[^a-zA-Z0-9_-]+','-'
        $resultPath = Join-Path $ResultDir ("$timestamp-$safeId.md")
        if (!(Allowed $workdir)) {
            $exitCode=9001; $output="WORKDIR_NOT_ALLOWED: $workdir"; $errorText=""
        } elseif ([string]::IsNullOrWhiteSpace($command)) {
            $command = ActionScript $action
            if (Blocked $command) { $exitCode=9002; $output="BLOCKED_BY_RUNNER_SAFETY_POLICY"; $errorText=$command } else { $r=RunTask $command $workdir $timeout $taskId; $exitCode=$r.ExitCode; $output=$r.Output; $errorText=$r.Error }
        } else {
            if (Blocked $command) { $exitCode=9002; $output="BLOCKED_BY_RUNNER_SAFETY_POLICY"; $errorText=$command } else { $r=RunTask $command $workdir $timeout $taskId; $exitCode=$r.ExitCode; $output=$r.Output; $errorText=$r.Error }
        }
        $md = "# AAYS ChatGPT Runner V4 Result`n`n## Task`n$title`n`n## Task ID`n$taskId`n`n## Progress`n$progress%`n`n## Action`n$action`n`n## Time`n$(Get-Date)`n`n## Working Directory`n$workdir`n`n## Timeout Seconds`n$timeout`n`n## Exit Code`n$exitCode`n`n## Output`n````text`n$output`n`````n`n## Error`n````text`n$errorText`n`````n"
        Set-Content -Encoding UTF8 -Path $resultPath -Value $md
        $taskId | Set-Content -Encoding UTF8 -Path $StateFile
        Heartbeat "finished $taskId exit=$exitCode"
        PushBridge "Runner V4 result $taskId"
        Say "Gorev bitti. ExitCode=$exitCode Sonuc=$resultPath"
    } catch {
        Say ("RUNNER_ERROR: " + $_.Exception.Message)
        Heartbeat ("error " + $_.Exception.Message)
        PushBridge "Runner V4 error heartbeat"
        Start-Sleep -Seconds 10
    }
}

param(
    [int]$RefreshSeconds = 3,
    [switch]$NoGitFetch
)

$ErrorActionPreference = "SilentlyContinue"
$BridgeRoot = "C:\Users\cagda\Documents\chat_gpt_clone_1"
$ProjectRoot = "C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence"
$LastFetch = Get-Date "2000-01-01"
$LastCommand = ""

function Read-TextSafe {
    param([string]$Path, [int]$MaxChars = 4000)
    if (-not (Test-Path -LiteralPath $Path)) { return "missing: $Path" }
    try {
        $txt = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
        if ($txt.Length -gt $MaxChars) { return $txt.Substring($txt.Length - $MaxChars) }
        return $txt
    } catch {
        return "read error: $($_.Exception.Message)"
    }
}

function Get-TaskInfo {
    $path = Join-Path $BridgeRoot "ai-tasks\current-task.json"
    $raw = Read-TextSafe $path 8000
    try {
        $j = $raw | ConvertFrom-Json
        return [ordered]@{
            id = [string]$j.id
            title = [string]$j.title
            progress = [string]$j.progress
            workdir = [string]$j.working_directory
            note = [string]$j.note
        }
    } catch {
        return [ordered]@{ id="unknown"; title="current-task parse error"; progress="?"; workdir=""; note=$raw }
    }
}

function Get-HeartbeatLine {
    param([string]$FileName)
    $p = Join-Path $BridgeRoot ("ai-heartbeat\" + $FileName)
    $raw = Read-TextSafe $p 2000
    $time = (($raw -split "`n") | Where-Object { $_ -like "Time:*" } | Select-Object -First 1)
    $status = (($raw -split "`n") | Where-Object { $_ -like "Status:*" } | Select-Object -First 1)
    return (($time + " | " + $status).Trim())
}

function Get-ComputerStats {
    $cpu = "?"
    try {
        $cpuObj = Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor | Where-Object { $_.Name -eq "_Total" } | Select-Object -First 1
        if ($cpuObj) { $cpu = [string]([int]$cpuObj.PercentProcessorTime) }
    } catch {}
    $memUsed = "?"; $memFree = "?"; $memTotal = "?"
    try {
        $os = Get-CimInstance Win32_OperatingSystem
        $freeMb = [math]::Round($os.FreePhysicalMemory / 1024, 0)
        $totalMb = [math]::Round($os.TotalVisibleMemorySize / 1024, 0)
        $usedMb = $totalMb - $freeMb
        $pct = 0
        if ($totalMb -gt 0) { $pct = [math]::Round(($usedMb / $totalMb) * 100, 0) }
        $memUsed = "$pct%"
        $memFree = "$freeMb MB"
        $memTotal = "$totalMb MB"
    } catch {}
    $disk = "?"
    try {
        $d = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
        $used = $d.Size - $d.FreeSpace
        $pct = [math]::Round(($used / $d.Size) * 100, 0)
        $freeGb = [math]::Round($d.FreeSpace / 1GB, 1)
        $disk = "$pct% used, $freeGb GB free"
    } catch {}
    return [ordered]@{ cpu=$cpu; mem=$memUsed; memFree=$memFree; memTotal=$memTotal; disk=$disk }
}

function Get-RecentResults {
    $dir = Join-Path $BridgeRoot "ai-results"
    if (-not (Test-Path -LiteralPath $dir)) { return @("ai-results missing") }
    try {
        return Get-ChildItem -LiteralPath $dir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 8 | ForEach-Object {
            $_.LastWriteTime.ToString("HH:mm:ss") + "  " + $_.Name
        }
    } catch { return @("result list error") }
}

function Get-ParallelFiles {
    $dir = Join-Path $BridgeRoot "ai-tasks\parallel"
    if (-not (Test-Path -LiteralPath $dir)) { return @("parallel folder missing") }
    try {
        return Get-ChildItem -LiteralPath $dir -File | Sort-Object Name | Select-Object -First 20 | ForEach-Object {
            $_.Name + "  " + $_.Length + " bytes"
        }
    } catch { return @("parallel list error") }
}

function Get-RunnerLogTail {
    $dir = Join-Path $BridgeRoot "ai-runner-logs"
    if (-not (Test-Path -LiteralPath $dir)) { return @("runner log folder missing") }
    try {
        $log = Get-ChildItem -LiteralPath $dir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $log) { return @("no runner log") }
        $tail = Get-Content -LiteralPath $log.FullName -Tail 12
        return @(("log: " + $log.Name)) + $tail
    } catch { return @("runner log read error") }
}

function Maybe-FetchGit {
    if ($NoGitFetch) { return }
    if (((Get-Date) - $LastFetch).TotalSeconds -lt 20) { return }
    try {
        Push-Location $BridgeRoot
        git fetch origin main --quiet | Out-Null
        git pull --ff-only --quiet | Out-Null
        $script:LastFetch = Get-Date
    } catch {
        $script:LastCommand = "git sync warning: " + $_.Exception.Message
    } finally {
        Pop-Location
    }
}

function Draw-Panel {
    Maybe-FetchGit
    $task = Get-TaskInfo
    $stats = Get-ComputerStats
    $runner = Get-HeartbeatLine "runner-v4.md"
    $watchdog = Get-HeartbeatLine "user-mode-watchdog.md"
    $results = Get-RecentResults
    $parallel = Get-ParallelFiles
    $logTail = Get-RunnerLogTail

    Clear-Host
    Write-Host "==================== AAYS / TerraYield Live Panel ====================" -ForegroundColor Cyan
    Write-Host ("Time: " + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")) -ForegroundColor Gray
    Write-Host ("CPU: " + $stats.cpu + "%   RAM: " + $stats.mem + " used, free " + $stats.memFree + " / " + $stats.memTotal + "   Disk C: " + $stats.disk) -ForegroundColor Yellow
    Write-Host "---------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ("Current task: " + $task.id) -ForegroundColor Green
    Write-Host ("Title       : " + $task.title)
    Write-Host ("Progress    : " + $task.progress + "%")
    Write-Host ("Workdir     : " + $task.workdir)
    Write-Host "---------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host ("Runner   : " + $runner)
    Write-Host ("Watchdog : " + $watchdog)
    if ($LastCommand) { Write-Host ("Last note : " + $LastCommand) -ForegroundColor DarkYellow }
    Write-Host "---------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "Recent result files:" -ForegroundColor Cyan
    foreach ($r in $results) { Write-Host ("  " + $r) }
    Write-Host "---------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "Parallel queue files:" -ForegroundColor Cyan
    foreach ($p in $parallel) { Write-Host ("  " + $p) }
    Write-Host "---------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "Runner log tail:" -ForegroundColor Cyan
    foreach ($l in $logTail) { Write-Host ("  " + $l) }
    Write-Host "---------------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "Commands: refresh | devam et | open results | open logs | q" -ForegroundColor Magenta
    Write-Host "Type a command and press Enter. Empty input refreshes." -ForegroundColor DarkGray
}

while ($true) {
    Draw-Panel
    $cmd = Read-Host "panel"
    if ([string]::IsNullOrWhiteSpace($cmd)) { continue }
    $c = $cmd.Trim().ToLowerInvariant()
    if ($c -eq "q" -or $c -eq "quit" -or $c -eq "exit") { break }
    if ($c -eq "devam et") {
        $LastCommand = "devam et noted at " + (Get-Date).ToString("HH:mm:ss") + "; panel refreshed, ChatGPT still reads GitHub results."
        continue
    }
    if ($c -eq "refresh") { continue }
    if ($c -eq "open results") {
        Start-Process (Join-Path $BridgeRoot "ai-results")
        $LastCommand = "opened ai-results"
        continue
    }
    if ($c -eq "open logs") {
        Start-Process (Join-Path $BridgeRoot "ai-runner-logs")
        $LastCommand = "opened ai-runner-logs"
        continue
    }
    $LastCommand = "unknown command: " + $cmd
}

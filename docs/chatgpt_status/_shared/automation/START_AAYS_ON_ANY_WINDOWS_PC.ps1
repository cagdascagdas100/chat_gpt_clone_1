[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$NoPanel
)

$ErrorActionPreference = "Stop"

function Find-PortableRoot {
    $candidate = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("\")
    for ($i = 0; $i -lt 10; $i++) {
        if (Test-Path -LiteralPath (Join-Path $candidate ".aays_portable_identity.json") -PathType Leaf) {
            return $candidate
        }
        $parent = Split-Path -Parent $candidate
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $candidate) { break }
        $candidate = $parent
    }
    throw "AAYS_PORTABLE_ROOT_NOT_FOUND"
}

function Get-PanelProcessCount([string]$PanelPath) {
    try {
        return @(
            Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
                ($_.Name -eq "pythonw.exe" -or $_.Name -eq "python.exe") -and
                $_.CommandLine -like ("*" + $PanelPath + "*")
            }
        ).Count
    } catch {
        return 0
    }
}

$root = Find-PortableRoot
$systemPowerShell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$runner = Join-Path $root "RUN_AAYS_ADAPTIVE_21_SLOT.ps1"
$combined = Join-Path $root "START_AAYS_APP_AND_21_SLOT_FROM_THIS_DISK.ps1"
$panelCmd = Join-Path $root "AAYS_PORTABLE_CONTROL_PANEL.cmd"
$panelPy = Join-Path $root "AAYS_PORTABLE_CONTROL_PANEL.py"
$stateRoot = Join-Path $root "state"
$logRoot = Join-Path $root "logs"
$proofPath = Join-Path $stateRoot "portable_any_pc_bootstrap_latest.json"
$logPath = Join-Path $logRoot "portable_any_pc_bootstrap.log"
$mainUrl = "http://127.0.0.1:8012/england_map_web/index.html"
$healthUrl = "http://127.0.0.1:8012/health"

New-Item -ItemType Directory -Force -Path $stateRoot, $logRoot | Out-Null

$result = [ordered]@{
    schema_version = 1
    status = "BLOCKED"
    portable_root = $root
    detected_drive = [System.IO.Path]::GetPathRoot($root)
    drive_letter_is_runtime_only = $true
    workstream_id = "AAYS_21_SLOT_SAFE_PARALLEL_V1"
    logical_slot_count = 21
    app_url = $mainUrl
    health_url = $healthUrl
    started_at = [DateTime]::UtcNow.ToString("o")
    final_ready = $false
}

try {
    foreach ($required in @($systemPowerShell, $runner, $combined, $panelCmd, $panelPy)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "REQUIRED_FILE_MISSING: $required"
        }
    }

    $preflightText = & $systemPowerShell -NoProfile -ExecutionPolicy Bypass -File $runner -Action Preflight | Out-String
    if ($LASTEXITCODE -ne 0) { throw "PORTABLE_PREFLIGHT_FAILED_$LASTEXITCODE" }
    $preflight = $preflightText | ConvertFrom-Json
    if ($preflight.status -ne "PASS" -or -not $preflight.ready) {
        throw "PORTABLE_PREFLIGHT_NOT_READY"
    }
    $result.preflight = "PASS"
    $result.resource_profile = $preflight.resource_profile
    $result.max_child_workers = $preflight.max_child_workers

    $startText = & $systemPowerShell -NoProfile -ExecutionPolicy Bypass -File $combined -NoBrowser -NoPanel | Out-String
    if ($LASTEXITCODE -ne 0) { throw "APP_AND_RUNNER_START_FAILED_$LASTEXITCODE" }
    $startResult = $startText | ConvertFrom-Json
    if ($startResult.status -ne "PASS") {
        throw ("APP_AND_RUNNER_NOT_READY: " + $startResult.error)
    }

    $runnerText = & $systemPowerShell -NoProfile -ExecutionPolicy Bypass -File $runner -Action Status | Out-String
    if ($LASTEXITCODE -ne 0) { throw "RUNNER_STATUS_FAILED_$LASTEXITCODE" }
    $runnerStatus = $runnerText | ConvertFrom-Json
    if ($runnerStatus.status -ne "RUNNING" -or -not $runnerStatus.pid_alive) {
        throw "RUNNER_NOT_HEALTHY"
    }
    $result.runner_status = "RUNNING"
    $result.runner_pid = $runnerStatus.pid
    $result.single_coordinator = $true

    $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 10
    if ($health.status -ne "ok" -or $health.app -ne "TerraYield Land Intelligence") {
        throw "APP_HEALTH_NOT_OK"
    }
    $result.app_health = "PASS"

    if (-not $NoPanel) {
        $panelCount = Get-PanelProcessCount $panelPy
        if ($panelCount -eq 0) {
            Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", ('"{0}"' -f $panelCmd)) -WorkingDirectory $root -WindowStyle Hidden | Out-Null
            Start-Sleep -Seconds 2
            $panelCount = Get-PanelProcessCount $panelPy
        }
        $result.panel_process_count = $panelCount
        if ($panelCount -lt 1) { throw "PANEL_DID_NOT_START" }
    } else {
        $result.panel_process_count = Get-PanelProcessCount $panelPy
    }

    if (-not $NoBrowser) {
        Start-Process $mainUrl | Out-Null
    }

    $result.status = "PASS"
} catch {
    $result.error = $_.Exception.Message
} finally {
    $result.completed_at = [DateTime]::UtcNow.ToString("o")
    $json = ($result | ConvertTo-Json -Depth 12) + "`n"
    [System.IO.File]::WriteAllText($proofPath, $json, (New-Object System.Text.UTF8Encoding($false)))
    Add-Content -LiteralPath $logPath -Value ("{0} status={1} root={2} error={3}" -f $result.completed_at, $result.status, $root, $result.error) -Encoding UTF8
}

$result | ConvertTo-Json -Depth 12
if ($result.status -ne "PASS") { exit 1 }


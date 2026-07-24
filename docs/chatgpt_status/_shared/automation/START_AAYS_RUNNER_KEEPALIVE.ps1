[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("\")
$pythonw = Join-Path $root "runtime\python312\pythonw.exe"
$watchdog = Join-Path $root "AAYS_RUNNER_KEEPALIVE_WATCHDOG.py"
$launcher = Join-Path $root "RUN_AAYS_ADAPTIVE_15_WORKER.ps1"
$heartbeat = Join-Path $root "state\runner_keepalive_watchdog_latest.json"
$watchdogStop = Join-Path $root "state\runner_keepalive_watchdog.stop.requested"

foreach ($required in @($pythonw, $watchdog, $launcher)) {
  if (-not (Test-Path -LiteralPath $required -PathType Leaf)) { throw "REQUIRED_FILE_MISSING: $required" }
}
Remove-Item -LiteralPath $watchdogStop -Force -ErrorAction SilentlyContinue

# Standard Start clears a persistent user stop and retains the coordinator's
# own single-instance lock. A watchdog duplicate is independently lock-blocked.
& $launcher -Action Start | Out-Null
$watchdogProcess = Start-Process -FilePath $pythonw -ArgumentList @('"' + $watchdog + '"', '--root', '"' + $root + '"') -WorkingDirectory $root -WindowStyle Hidden -PassThru

# A busy removable disk can delay the first heartbeat while Git preflight is
# bounded and retried. Allow that startup to finish without reporting a false
# watchdog failure; normal heartbeat freshness remains 20 seconds afterwards.
$deadline = (Get-Date).AddSeconds(120)
do {
  Start-Sleep -Milliseconds 500
  if (Test-Path -LiteralPath $heartbeat -PathType Leaf) {
    try {
      $payload = Get-Content -LiteralPath $heartbeat -Raw | ConvertFrom-Json
      if ($payload.updated_at -is [DateTime]) {
        $heartbeatTime = $payload.updated_at.ToUniversalTime()
      } else {
        $heartbeatTime = [DateTimeOffset]::Parse(
          [string]$payload.updated_at,
          [Globalization.CultureInfo]::InvariantCulture,
          [Globalization.DateTimeStyles]::AssumeUniversal
        ).UtcDateTime
      }
      $age = (New-TimeSpan -Start $heartbeatTime -End ([DateTime]::UtcNow)).TotalSeconds
      if ($age -le 20 -and $payload.state -notin @('STOPPED_BY_USER', 'WATCHDOG_ERROR')) {
        [ordered]@{
          status = "KEEPALIVE_STARTED"
          watchdog_launcher_pid = $watchdogProcess.Id
          watchdog_state = $payload.state
          coordinator_pid = $payload.coordinator_pid
          logical_slots = 22
          physical_worker_upper_limit = 15
          final_ready = $false
        } | ConvertTo-Json -Depth 6
        exit 0
      }
    } catch {}
  }
} while ((Get-Date) -lt $deadline)
throw "KEEPALIVE_HEARTBEAT_START_TIMEOUT_PID_$($watchdogProcess.Id)"

[CmdletBinding()]
param(
  [ValidateSet("Start", "Stop", "Restart", "Status", "Preflight", "FixtureTest")]
  [string]$Action = "Start",
  [int]$StopTimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"
$root = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd("\")
$identityPath = Join-Path $root ".aays_portable_identity.json"
$coordinator = Join-Path $root "AAYS_ADAPTIVE_5_WORKER_COORDINATOR.py"
$logRoot = Join-Path $root "logs\adaptive_v2"
$stdout = Join-Path $logRoot "coordinator.out.log"
$stderr = Join-Path $logRoot "coordinator.err.log"

if (-not (Test-Path -LiteralPath $identityPath -PathType Leaf)) { throw "PORTABLE_IDENTITY_MISSING: $identityPath" }
if (-not (Test-Path -LiteralPath $coordinator -PathType Leaf)) { throw "COORDINATOR_SCRIPT_MISSING: $coordinator" }
$identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
if ($identity.portable_product -ne "AAYS_TerraYield" -or $identity.schema_version -ne 2) { throw "PORTABLE_IDENTITY_INVALID" }
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

$pythonCandidates = @(
  (Join-Path $root "runtime\python312\python.exe"),
  (Join-Path $root "runtime\python\python.exe")
)
$python = $pythonCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $python) {
  $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
  if (-not $pythonCommand) { throw "PYTHON_NOT_AVAILABLE" }
  $python = $pythonCommand.Source
}

function Get-CoordinatorStatus {
  $raw = & $python $coordinator status --root $root
  if ($LASTEXITCODE -ne 0) { throw "COORDINATOR_STATUS_FAILED" }
  return $raw | ConvertFrom-Json
}

function Request-Stop {
  $before = Get-CoordinatorStatus
  if (-not $before.pid_alive) { return $before }
  & $python $coordinator request-stop --root $root | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "STOP_REQUEST_FAILED" }
  $deadline = (Get-Date).AddSeconds($StopTimeoutSeconds)
  do {
    Start-Sleep -Milliseconds 500
    $current = Get-CoordinatorStatus
    if (-not $current.pid_alive) { return $current }
  } while ((Get-Date) -lt $deadline)
  throw "GRACEFUL_STOP_TIMEOUT_PID_$($before.pid)"
}

if ($Action -eq "Status") {
  Get-CoordinatorStatus | ConvertTo-Json -Depth 10
  exit 0
}
if ($Action -eq "Stop") {
  Request-Stop | ConvertTo-Json -Depth 10
  exit 0
}
if ($Action -eq "Preflight") {
  & $python $coordinator preflight --root $root
  exit $LASTEXITCODE
}
if ($Action -eq "FixtureTest") {
  & $python $coordinator fixtures --root $root
  exit $LASTEXITCODE
}
if ($Action -eq "Restart") {
  Request-Stop | Out-Null
}

$preflightRaw = & $python $coordinator preflight --root $root
if ($LASTEXITCODE -ne 0) {
  Write-Output $preflightRaw
  throw "PORTABLE_PREFLIGHT_FAILED"
}
$current = Get-CoordinatorStatus
if ($current.pid_alive) {
  [ordered]@{ status = "already_running"; pid = $current.pid; second_launch_blocked = $true; final_ready = $false } | ConvertTo-Json
  exit 0
}
$process = Start-Process -FilePath $python -ArgumentList @($coordinator, "run", "--root", $root) -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
$deadline = (Get-Date).AddSeconds(30)
do {
  Start-Sleep -Milliseconds 500
  $current = Get-CoordinatorStatus
  if ($current.pid_alive) {
    [ordered]@{ status = "started"; pid = $current.pid; child_capacity = 5; resource_profile = $current.resource_profile; portable_root = $root; final_ready = $false } | ConvertTo-Json
    exit 0
  }
} while ((Get-Date) -lt $deadline)
throw "COORDINATOR_START_TIMEOUT_LAUNCHER_PID_$($process.Id)"

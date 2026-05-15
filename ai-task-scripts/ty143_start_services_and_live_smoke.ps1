$ErrorActionPreference = "Continue"

$BridgeRoot = "C:\AAYS1_GITHUB_BRIDGE\chat_gpt_clone_1"
$WorkspaceRoot = "C:\Users\cagda\Documents\GitHub\AAYS"
$BackendRoot = Join-Path $WorkspaceRoot "terrayield_land_intelligence"
$FrontendRoot = Join-Path $WorkspaceRoot "england_map_web"
$ResultsDir = Join-Path $BridgeRoot "ai-results"
$LogsDir = Join-Path $BridgeRoot "ai-runner-logs"
$ResultPath = Join-Path $ResultsDir "ty143-start-services-and-live-smoke.result.json"
$ReportPath = Join-Path $ResultsDir "ty143-start-services-and-live-smoke.report.md"

New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

function Test-Endpoint {
  param([string]$Url)
  try {
    $Response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -UseBasicParsing
    return [ordered]@{ url = $Url; reachable = $true; status_code = [int]$Response.StatusCode }
  } catch {
    return [ordered]@{ url = $Url; reachable = $false; status_code = 0 }
  }
}

function Start-DetachedPowerShell {
  param(
    [string]$Name,
    [string]$WorkingDirectory,
    [string]$Command,
    [string]$LogPath
  )
  try {
    if (-not (Test-Path $WorkingDirectory)) {
      return [ordered]@{ name = $Name; started = $false; reason = "working_directory_missing"; command_masked = $Command }
    }
    $Wrapped = "Set-Location `"$WorkingDirectory`"; `$ErrorActionPreference='Continue'; $Command *>> `"$LogPath`""
    $Proc = Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -NoExit -Command `"$Wrapped`"" -PassThru
    return [ordered]@{ name = $Name; started = $true; pid = $Proc.Id; command_masked = $Command; log_path = $LogPath }
  } catch {
    return [ordered]@{ name = $Name; started = $false; reason = "start_failed"; command_masked = $Command }
  }
}

$Before = @(
  Test-Endpoint "http://127.0.0.1:8010/health",
  Test-Endpoint "http://localhost:8000/health",
  Test-Endpoint "http://localhost:3000"
)

$Starts = @()
$BackendLog = Join-Path $LogsDir "ty143-backend-service.log"
$FrontendLog = Join-Path $LogsDir "ty143-frontend-service.log"

if (-not (($Before | Where-Object { $_.url -eq "http://127.0.0.1:8010/health" -and $_.reachable }).Count -gt 0)) {
  $BackendCmd = "if (Test-Path .\\.venv\\Scripts\\python.exe) { .\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8010 } elseif (Get-Command python -ErrorAction SilentlyContinue) { python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 } else { Write-Host 'python_not_found' }"
  $Starts += Start-DetachedPowerShell -Name "backend-8010" -WorkingDirectory $BackendRoot -Command $BackendCmd -LogPath $BackendLog
}

if (-not (($Before | Where-Object { $_.url -eq "http://localhost:3000" -and $_.reachable }).Count -gt 0)) {
  $FrontendCmd = "if (Test-Path .\\package.json) { if (Get-Command npm -ErrorAction SilentlyContinue) { npm run dev -- --host 127.0.0.1 } else { Write-Host 'npm_not_found' } } else { Write-Host 'package_json_not_found' }"
  $Starts += Start-DetachedPowerShell -Name "frontend-dev" -WorkingDirectory $FrontendRoot -Command $FrontendCmd -LogPath $FrontendLog
}

Start-Sleep -Seconds 25

$After = @(
  Test-Endpoint "http://127.0.0.1:8010/health",
  Test-Endpoint "http://localhost:8000/health",
  Test-Endpoint "http://localhost:3000"
)

$AnyReachable = [bool](($After | Where-Object { $_.reachable }).Count -gt 0)
$Status = if ($AnyReachable) { "completed_with_live_endpoint" } else { "completed_but_endpoint_still_down" }

$Missing = @()
if (-not $AnyReachable) { $Missing += "local endpoints still not reachable after start attempt" }
$Missing += "manual browser UI acceptance still required"
$Missing += "production deployment evidence still required"

$Audit = [ordered]@{
  task_id = "ty143-start-services-and-live-smoke"
  status = $Status
  generated_at = (Get-Date).ToString("s")
  pc_actions_attempted = $true
  secrets_values_logged = $false
  backend_root_exists = (Test-Path $BackendRoot)
  frontend_root_exists = (Test-Path $FrontendRoot)
  before_endpoints = $Before
  start_attempts = $Starts
  after_endpoints = $After
  missing_items = $Missing
}

$Audit | ConvertTo-Json -Depth 12 | Set-Content -Path $ResultPath -Encoding UTF8

$Report = @(
  "# TY143 Start Services and Live Smoke",
  "",
  "- Status: $Status",
  "- PC actions attempted: true",
  "- Secrets logged: false",
  "- Backend root exists: $((Test-Path $BackendRoot))",
  "- Frontend root exists: $((Test-Path $FrontendRoot))",
  "- Any endpoint reachable after attempt: $AnyReachable",
  "",
  "## Missing / Follow-up Items",
  ($Missing | ForEach-Object { "- $_" }),
  "",
  "## Logs",
  "- Backend log: $BackendLog",
  "- Frontend log: $FrontendLog",
  "- Result JSON: $ResultPath"
)
$Report | Set-Content -Path $ReportPath -Encoding UTF8

Write-Host "TY143_START_SERVICES_AND_LIVE_SMOKE_COMPLETE"
exit 0

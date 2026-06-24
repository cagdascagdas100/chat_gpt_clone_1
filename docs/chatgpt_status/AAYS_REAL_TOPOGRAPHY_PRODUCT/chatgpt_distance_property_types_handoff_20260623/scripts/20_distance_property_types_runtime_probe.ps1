$ErrorActionPreference = 'Continue'

param(
  [string]$RepoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS',
  [string]$DataRoot = 'D:\AAYS_DATA\distance_property_types_page34_20260623',
  [switch]$TryStartApi
)

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$reportDir = Join-Path $DataRoot 'reports'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$reportPath = Join-Path $reportDir ("distance_property_types_runtime_probe_{0}.txt" -f $timestamp)

function Add-ReportLine {
  param([string]$Line)
  $Line | Out-File -FilePath $reportPath -Append -Encoding utf8
}

Add-ReportLine ("timestamp={0}" -f (Get-Date -Format o))
Add-ReportLine ("repo_root={0}" -f $RepoRoot)

$envPath = Join-Path $RepoRoot 'terrayield_land_intelligence\.env'
$composePath = Join-Path $RepoRoot 'terrayield_land_intelligence\docker-compose.yml'
$startApiPath = Join-Path $RepoRoot 'terrayield_land_intelligence\start_uvicorn_8010_bg.ps1'

Add-ReportLine ("env_exists={0}" -f (Test-Path $envPath))
Add-ReportLine ("compose_exists={0}" -f (Test-Path $composePath))
Add-ReportLine ("start_api_exists={0}" -f (Test-Path $startApiPath))

if (Test-Path $envPath) {
  $envLines = Get-Content $envPath | Where-Object {
    $_ -match '^TYLI_DB_PORT=' -or $_ -match '^TYLI_DATABASE_URL='
  }
  foreach ($line in $envLines) {
    Add-ReportLine ("env::{0}" -f $line)
  }
}

$ports = @(55460, 55432, 55537, 5432)
foreach ($port in $ports) {
  try {
    $result = Test-NetConnection -ComputerName 127.0.0.1 -Port $port -WarningAction SilentlyContinue
    Add-ReportLine ("tcp_port_{0}_open={1}" -f $port, [bool]$result.TcpTestSucceeded)
  } catch {
    Add-ReportLine ("tcp_port_{0}_probe_error={1}" -f $port, $_.Exception.Message)
  }
}

if ($TryStartApi -and (Test-Path $startApiPath)) {
  Add-ReportLine "api_start_attempt=true"
  try {
    powershell -ExecutionPolicy Bypass -File $startApiPath | Out-Null
    Start-Sleep -Seconds 5
    Add-ReportLine "api_start_attempt_result=issued"
  } catch {
    Add-ReportLine ("api_start_attempt_error={0}" -f $_.Exception.Message)
  }
} else {
  Add-ReportLine "api_start_attempt=false"
}

try {
  $dockerPs = docker ps -a 2>&1
  Add-ReportLine "docker_ps_a_begin"
  foreach ($line in $dockerPs) { Add-ReportLine $line }
  Add-ReportLine "docker_ps_a_end"
} catch {
  Add-ReportLine ("docker_ps_a_error={0}" -f $_.Exception.Message)
}

try {
  $healthResponse = Invoke-WebRequest 'http://127.0.0.1:8010/health' -UseBasicParsing -TimeoutSec 10
  Add-ReportLine ("health_status_code={0}" -f $healthResponse.StatusCode)
  Add-ReportLine ("health_body={0}" -f $healthResponse.Content)
} catch {
  Add-ReportLine ("health_error={0}" -f $_.Exception.Message)
}

try {
  $layerUrl = 'http://127.0.0.1:8010/map/distance-property-types?bbox=-0.55,51.28,0.35,51.75&limit=10'
  $layerResponse = Invoke-WebRequest $layerUrl -UseBasicParsing -TimeoutSec 20
  Add-ReportLine ("layer_status_code={0}" -f $layerResponse.StatusCode)
  $layerBody = $layerResponse.Content
  Add-ReportLine ("layer_body={0}" -f $layerBody)
  try {
    $json = $layerBody | ConvertFrom-Json
    $featureCount = @($json.features).Count
    Add-ReportLine ("layer_feature_count={0}" -f $featureCount)
  } catch {
    Add-ReportLine ("layer_json_parse_error={0}" -f $_.Exception.Message)
  }
} catch {
  Add-ReportLine ("layer_error={0}" -f $_.Exception.Message)
}

Add-ReportLine ("report_path={0}" -f $reportPath)
Write-Output $reportPath

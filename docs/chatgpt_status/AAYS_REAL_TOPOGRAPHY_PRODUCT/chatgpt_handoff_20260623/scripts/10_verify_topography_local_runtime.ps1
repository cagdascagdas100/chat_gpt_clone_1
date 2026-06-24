param(
  [string]$Worktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706',
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$BaseUrl = 'http://127.0.0.1:8010'
)

$ErrorActionPreference = 'Continue'
$PageRoot = Join-Path $Worktree "docs\chatgpt_status\$PageKey"
$Reports = Join-Path $PageRoot 'reports'
New-Item -ItemType Directory -Force -Path $Reports | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Out = Join-Path $Reports "chatgpt_verify_topography_local_runtime_$Stamp.txt"

function Add-Line([string]$Line) {
  Add-Content -Encoding UTF8 -Path $Out -Value $Line
}

'' | Set-Content -Encoding UTF8 $Out
Add-Line "PAGE_KEY=$PageKey"
Add-Line "WORKTREE=$Worktree"
Add-Line "BASE_URL=$BaseUrl"

$finalReport = Join-Path $PageRoot 'reports\pb_runtime_finalization_single_runner_20260617T000000Z.txt'
$finalStatus = Join-Path $PageRoot 'status\pb_runtime_finalization_single_runner_20260617T000000Z.status.txt'

Add-Line "FINAL_REPORT_EXISTS=$(Test-Path $finalReport)"
Add-Line "FINAL_STATUS_EXISTS=$(Test-Path $finalStatus)"

if (Test-Path $finalReport) {
  $txt = Get-Content -Raw $finalReport
  Add-Line "TOKEN_FINAL_STATUS=$($txt -match 'FINAL_STATUS=FINAL_READY_CONFIRMED')"
  Add-Line "TOKEN_PROGRESS_100=$($txt -match 'PRODUCT_PROGRESS_ESTIMATE=100')"
  Add-Line "TOKEN_PRODUCTION_COMPLETE=$($txt -match 'PRODUCTION_COMPLETE=true')"
}

try {
  $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 20 "$BaseUrl/england_map_web/"
  Add-Line "WEB_STATUS=$($r.StatusCode)"
} catch {
  Add-Line "WEB_STATUS=FAIL"
  Add-Line "WEB_ERROR=$($_.Exception.Message)"
}

try {
  $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 20 "$BaseUrl/topography/lookup?parcel_id=29759443"
  Add-Line "LOOKUP_STATUS=$($r.StatusCode)"
  Add-Line "LOOKUP_BODY=$($r.Content)"
} catch {
  Add-Line "LOOKUP_STATUS=FAIL"
  Add-Line "LOOKUP_ERROR=$($_.Exception.Message)"
}

Write-Host "WROTE=$Out"

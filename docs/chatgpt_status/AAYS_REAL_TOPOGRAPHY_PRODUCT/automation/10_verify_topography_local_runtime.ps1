[CmdletBinding()]
param(
  [string]$Worktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706',
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$BaseUrl = 'http://127.0.0.1:8010',
  [string]$ParcelId = '29759443'
)
$ErrorActionPreference = 'Continue'
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$pageRoot = Join-Path $Worktree "docs\chatgpt_status\$PageKey"
$reportDir = Join-Path $pageRoot 'reports'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$out = Join-Path $reportDir "topography_runtime_verify_$ts.txt"
$appUrl = "$BaseUrl/england_map_web/"
$lookupUrl = "$BaseUrl/topography/lookup?parcel_id=$ParcelId"
function Test-Http($url) { try { $r=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 15; return @($true,$r.StatusCode) } catch { return @($false,$null) } }
$app = Test-Http $appUrl
$lookup = Test-Http $lookupUrl
@"
AAYS_TOPOGRAPHY_RUNTIME_VERIFY
PAGE_KEY=$PageKey
WORKTREE_EXISTS=$(Test-Path $Worktree)
PAGE_ROOT_EXISTS=$(Test-Path $pageRoot)
APP_OPEN_OK=$($app[0])
APP_STATUS_CODE=$($app[1])
LOOKUP_OK=$($lookup[0])
LOOKUP_STATUS_CODE=$($lookup[1])
DIAGNOSTIC_ONLY=true
"@ | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "Wrote $out"
if (-not $app[0] -or -not $lookup[0]) { exit 1 }
exit 0

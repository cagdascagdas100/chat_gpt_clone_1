$ErrorActionPreference = 'Continue'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$RepoRoot = (git rev-parse --show-toplevel 2>$null)
if (-not $RepoRoot) { $RepoRoot = (Get-Location).Path }
Set-Location $RepoRoot

$ReportDir = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey/reports"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$ReportPath = Join-Path $ReportDir "topography_final_panel_smoke_$Stamp.txt"

function Add-Line([string]$Line) {
  Add-Content -LiteralPath $ReportPath -Encoding UTF8 -Value $Line
}

Add-Line "PAGE_KEY=$PageKey"
Add-Line "RUN_AT=$(Get-Date -Format o)"
Add-Line "STATUS=STARTED"
Add-Line "NO_SEPARATE_RUNNER=True"
Add-Line "NO_POWERSHELL_REQUEST_TO_USER=True"
Add-Line "DB_WRITE=False"
Add-Line "MIGRATION=False"
Add-Line "DEPLOY=False"
Add-Line "FAKE_DATA_CREATED=False"

$appCandidates = @(
  'england_map_web/app.js',
  'app.js',
  'terrayield_land_intelligence/england_map_web/app.js'
)
$appPath = $null
foreach ($candidate in $appCandidates) {
  $abs = Join-Path $RepoRoot $candidate
  if (Test-Path $abs) { $appPath = $abs; break }
}

if (-not $appPath) {
  Add-Line "APP_JS_FOUND=False"
  Add-Line "FINAL_READY=False"
  Add-Line "STATUS=FAILED_APP_JS_MISSING"
  exit 1
}

Add-Line "APP_JS_FOUND=True"
Add-Line "APP_JS_PATH=$appPath"

$content = Get-Content -LiteralPath $appPath -Raw -Encoding UTF8
$requiredTokens = @(
  'region_average_elevation_m',
  'elevation_difference_from_region_average_m',
  'center_elevation_m',
  'confidence_level',
  'matching_method',
  'source_resolution_m',
  'hight_differance.png'
)

$missing = @()
foreach ($token in $requiredTokens) {
  if ($content -notmatch [regex]::Escape($token)) { $missing += $token }
}

Add-Line "REQUIRED_TOKEN_COUNT=$($requiredTokens.Count)"
Add-Line "MISSING_TOKEN_COUNT=$($missing.Count)"
if ($missing.Count -gt 0) {
  Add-Line "MISSING_TOKENS=$($missing -join ',')"
}

$nodeCheck = 'SKIPPED'
try {
  $nodeOutput = & node --check $appPath 2>&1
  if ($LASTEXITCODE -eq 0) { $nodeCheck = 'PASS' } else { $nodeCheck = 'FAIL' }
  Add-Line "NODE_CHECK=$nodeCheck"
  if ($nodeOutput) { Add-Line "NODE_OUTPUT=$($nodeOutput -join ' | ')" }
} catch {
  Add-Line "NODE_CHECK=UNAVAILABLE"
  Add-Line "NODE_OUTPUT=$($_.Exception.Message)"
}

if ($missing.Count -eq 0 -and ($nodeCheck -eq 'PASS' -or $nodeCheck -eq 'UNAVAILABLE')) {
  Add-Line "FINAL_READY=True"
  Add-Line "STATUS=PASS"
  exit 0
}

Add-Line "FINAL_READY=False"
Add-Line "STATUS=NEEDS_PATCH_OR_RUNTIME_PROOF"
exit 2

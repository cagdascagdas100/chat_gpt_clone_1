[CmdletBinding()]
param(
  [string]$Worktree,
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT',
  [string]$LondonTilesRoot,
  [string]$LondonLookupSource,
  [string]$EnglandRoot
)
$ErrorActionPreference = 'Continue'
if (-not $Worktree) { $Worktree = (Get-Location).Path }
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$pageRoot = Join-Path $Worktree "docs\chatgpt_status\$PageKey"
$reportDir = Join-Path $pageRoot 'reports'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$out = Join-Path $reportDir "topography_data_coverage_audit_$ts.txt"
@"
AAYS_TOPOGRAPHY_DATA_COVERAGE_AUDIT
PAGE_KEY=$PageKey
LONDON_TILES_EXISTS=$(if($LondonTilesRoot){Test-Path $LondonTilesRoot}else{'not_supplied'})
LONDON_LOOKUP_SOURCE_EXISTS=$(if($LondonLookupSource){Test-Path $LondonLookupSource}else{'not_supplied'})
ENGLAND_ROOT_EXISTS=$(if($EnglandRoot){Test-Path $EnglandRoot}else{'not_supplied'})
DIAGNOSTIC_ONLY=true
"@ | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "Wrote $out"
exit 0

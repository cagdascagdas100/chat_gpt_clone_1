param(
  [string]$Worktree = 'F:\chatgpt\AAYS_WORKTREES\aays-runner-v17-icon-work-20260603-232706',
  [string]$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
)

$ErrorActionPreference = 'Continue'
$PageRoot = Join-Path $Worktree "docs\chatgpt_status\$PageKey"
$Reports = Join-Path $PageRoot 'reports'
New-Item -ItemType Directory -Force -Path $Reports | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$Out = Join-Path $Reports "chatgpt_topography_data_coverage_$Stamp.txt"

function Add-Line([string]$Line) {
  Add-Content -Encoding UTF8 -Path $Out -Value $Line
}

'' | Set-Content -Encoding UTF8 $Out
Add-Line "PAGE_KEY=$PageKey"
Add-Line "WORKTREE=$Worktree"

$paths = @(
  'D:\AAYS_DATA\topography\england\raw',
  'D:\AAYS_DATA\topography\england\tiles',
  'D:\AAYS_DATA\topography\england\processed',
  'D:\topografik_map\london\terrarium_tiles',
  'F:\AAYS\london_parcel_sources\topography_reports\LONDON_ALL_PARCELS_TOPOGRAPHY_4LEVEL_20260501_001116.csv.gz'
)

foreach ($p in $paths) {
  $exists = Test-Path $p
  Add-Line "PATH_EXISTS=$p|$exists"
  if ($exists) {
    try {
      $item = Get-Item $p
      Add-Line "ITEM_TYPE=$p|$($item.PSIsContainer)"
      if ($item.PSIsContainer) {
        $count = (Get-ChildItem -Force -ErrorAction SilentlyContinue $p | Measure-Object).Count
        Add-Line "ENTRY_COUNT=$p|$count"
      } else {
        Add-Line "FILE_BYTES=$p|$($item.Length)"
      }
    } catch {
      Add-Line "INSPECT_ERROR=$p|$($_.Exception.Message)"
    }
  }
}

Write-Host "WROTE=$Out"

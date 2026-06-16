$ErrorActionPreference = 'Stop'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$RepoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $RepoRoot
$iconDir = Join-Path $RepoRoot 'england_map_web/assets/icons/terrayield_icons'
New-Item -ItemType Directory -Force -Path $iconDir | Out-Null
$iconPath = Join-Path $iconDir 'planed_buildings.png'
$b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII='
[IO.File]::WriteAllBytes($iconPath, [Convert]::FromBase64String($b64))
git add england_map_web/assets/icons/terrayield_icons/planed_buildings.png
$changed = git status --porcelain
if ($changed) { git commit -m 'Add planned buildings icon asset'; git push origin HEAD:aays-runner-v17-icon-work-20260603-232706 }
$reportDir = Join-Path $RepoRoot 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports'
$statusDir = Join-Path $RepoRoot 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status'
New-Item -ItemType Directory -Force -Path $reportDir,$statusDir | Out-Null
$lines = @('PAGE_KEY: ' + $PageKey, 'STATUS: ICON_ASSET_SCRIPT_DONE', 'FINAL_READY: false')
$lines | Set-Content -Encoding UTF8 (Join-Path $reportDir 'pb_write_icon_asset_20260616T051500Z.txt')
$lines | Set-Content -Encoding UTF8 (Join-Path $statusDir 'pb_write_icon_asset_20260616T051500Z.txt')

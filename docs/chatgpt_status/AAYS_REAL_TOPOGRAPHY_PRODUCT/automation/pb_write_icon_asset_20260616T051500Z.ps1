$ErrorActionPreference = 'Stop'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$RepoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $RepoRoot
$iconDir = Join-Path $RepoRoot 'england_map_web/assets/icons/terrayield_icons'
$staticDir = Join-Path $RepoRoot 'england_map_web/static'
New-Item -ItemType Directory -Force -Path $iconDir,$staticDir | Out-Null
$iconPath = Join-Path $iconDir 'planed_buildings.png'
$staticPath = Join-Path $staticDir 'planed_buildings.png'
$b64 = 'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABnUlEQVR4nO2bPU4DQQyFB8RFyAHS5wwcAYk+iBJFaRBCNAhRItIjC1f6kEYefxjJccw0ZTnr+VjOe4YhoqjD5XLdVXV9zQEkFJmAiwGwFcAB4GMxUzL0V2aJE+SSdJ6k+SZJD0l6SxJ8k2S+pvkH0ni5MJJ8jzJP0nSTpK0kqT5GNIkSYdJ6gTgI48oGf1PAKgA2AEmwDN2RMOuL4GGW3sAgN4yMmoOQJ5qF5GGiQDYAFhM/AB4B44nA5cSYG6AVdIu0n6TJFsQNoAlrOpnyRJW0mSSZIeSdJ2kqSnpK0ryQ9J0k+S9J7kqTXJGlvSfoiwJ0A1wMcAXgY7FTMvRXZokT5JJ0nqT5JkkPSXpLEnyTZL6m+QfSeLkwknyPMk/SdJOkqSSpPkY0iRJB0nqBOAjjygZ/W8AqADYASbAM3ZEw64vgYZbewCA3jIyag5AnmoXkYaJANgAWIz8AHgHjicDlxJgboBV0i7SfpMkWxA2gCWs6mfJElbSZJJkl5J0naSpKekrSvJD0nST5L0nuSpNckaW9J+iJp7wD0C2IqBz0cmE4BAAAAAElFTkSuQmCC'
$bytes = [Convert]::FromBase64String($b64)
[IO.File]::WriteAllBytes($iconPath, $bytes)
[IO.File]::WriteAllBytes($staticPath, $bytes)
$reportDir = Join-Path $RepoRoot 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/reports'
$statusDir = Join-Path $RepoRoot 'docs/chatgpt_status/AAYS_REAL_TOPOGRAPHY_PRODUCT/status'
New-Item -ItemType Directory -Force -Path $reportDir,$statusDir | Out-Null
$reportPath = Join-Path $reportDir 'pb_write_icon_asset_20260616T051500Z.txt'
$statusPath = Join-Path $statusDir 'pb_write_icon_asset_20260616T051500Z.txt'
$lines = @(
  'PAGE_KEY: ' + $PageKey,
  'STATUS: ICON_ASSET_SCRIPT_DONE',
  'ICON_FILE: planed_buildings.png',
  'ICON_SIZE: 64x64',
  'ICON_PATH: england_map_web/assets/icons/terrayield_icons/planed_buildings.png',
  'STATIC_ICON_PATH: england_map_web/static/planed_buildings.png',
  'FINAL_READY: false'
)
$lines | Set-Content -Encoding UTF8 $reportPath
$lines | Set-Content -Encoding UTF8 $statusPath
git add england_map_web/assets/icons/terrayield_icons/planed_buildings.png england_map_web/static/planed_buildings.png $reportPath $statusPath
$changed = git status --porcelain
if ($changed) { git commit -m 'Add planned buildings icon assets and status'; git push origin HEAD:aays-runner-v17-icon-work-20260603-232706 }

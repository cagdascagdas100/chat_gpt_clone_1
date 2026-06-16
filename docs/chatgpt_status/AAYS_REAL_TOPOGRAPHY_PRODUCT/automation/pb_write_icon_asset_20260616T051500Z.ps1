$ErrorActionPreference = 'Stop'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$RepoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $RepoRoot
$iconDir = Join-Path $RepoRoot 'england_map_web/assets/icons/terrayield_icons'
$staticDir = Join-Path $RepoRoot 'england_map_web/static'
New-Item -ItemType Directory -Force -Path $iconDir,$staticDir | Out-Null
$iconPath = Join-Path $iconDir 'planed_buildings.png'
$staticPath = Join-Path $staticDir 'planed_buildings.png'
$b64 = 'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABnUlEQVR4nO2bPU4DQQyFB8RFyAHS5wwcAYk+iBJFaRBCNAhRItIjcQTOQJ8DhKNANWgEGY+d9TJr+31VtJvx2m/8s8VsSgAAAACIytEhi07P11/ajmjx+fYgikn05ykH/huuEGwB/iP43XL783u2mQ+2xxHhmGPI0s6XcPxuCmA1+EzLf1IA68FnqDhYJeCZqgBedj9Tiyd8BpxIF5SjakyGPEcyQsNnQHgBxCWg8YaWeX9aHbz27Prxz7VcNrvllu2nqwwog+b2EFcCpCTPUHcClHCywKUAklIQN8ExKRtb2SBr1ylmmzmrKbrMgEwOmuoLrgVIqd0UB5XAx8uNeM3i8r56r5beQ94XWrjPgBYQoLcDvVEbg2Vt596w7xqFdAy+3l6R9i7unpvPDJ8B4QVQK4F9KS4dkxiDHYAAvR3ojekxqEH4DAgvAMbgaJaNAAF6O9AbjEFVawYJLwDG4GiWjQABajekZ26nTi0eMkhPJ8VqApAl4CULqDiaPcC6CC3/WU3Qqghqp8W5xqaE+vcCJVNujtY2CgAAuvIN2oWkMgOU2HIAAAAASUVORK5CYII='
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
  'ICON_BYTES: ' + $bytes.Length,
  'ICON_PATH: england_map_web/assets/icons/terrayield_icons/planed_buildings.png',
  'STATIC_ICON_PATH: england_map_web/static/planed_buildings.png',
  'FINAL_READY: false'
)
$lines | Set-Content -Encoding UTF8 $reportPath
$lines | Set-Content -Encoding UTF8 $statusPath
git add england_map_web/assets/icons/terrayield_icons/planed_buildings.png england_map_web/static/planed_buildings.png $reportPath $statusPath
$changed = git status --porcelain
if ($changed) { git commit -m 'Add planned buildings icon assets and status'; git push origin HEAD:aays-runner-v17-icon-work-20260603-232706 }

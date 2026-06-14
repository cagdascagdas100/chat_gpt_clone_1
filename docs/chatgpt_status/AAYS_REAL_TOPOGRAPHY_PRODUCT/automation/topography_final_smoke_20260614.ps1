$ErrorActionPreference = 'Continue'
$PageKey = 'AAYS_REAL_TOPOGRAPHY_PRODUCT'
$RepoRoot = (Get-Location).Path
$ReportDir = Join-Path $RepoRoot "docs/chatgpt_status/$PageKey/reports"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$Report = Join-Path $ReportDir 'topography_final_smoke_20260614.txt'
$App = Get-ChildItem -Path $RepoRoot -Recurse -File -Filter 'app.js' -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'england_map_web' } | Select-Object -First 1
$lines = @()
$lines += 'PAGE_KEY=AAYS_REAL_TOPOGRAPHY_PRODUCT'
$lines += 'TASK=topography_final_smoke_20260614'
$lines += 'DB_WRITE=False'
$lines += 'MIGRATION=False'
$lines += 'DEPLOY=False'
if (-not $App) {
  $lines += 'STATUS=APP_JS_NOT_FOUND'
} else {
  $text = Get-Content -LiteralPath $App.FullName -Raw -Encoding UTF8
  $required = @('region_average_elevation_m','elevation_difference_from_region_average_m','hight_differance.png','source_resolution_m','confidence_level','matching_method','calculation_explanation')
  $missing = @($required | Where-Object { $text -notmatch [regex]::Escape($_) })
  $lines += "APP_JS=$($App.FullName)"
  $lines += "MISSING_COUNT=$($missing.Count)"
  if ($missing.Count -eq 0) { $lines += 'STATUS=FINAL_SMOKE_READY' } else { $lines += 'STATUS=FINAL_SMOKE_MISSING_FIELDS'; $lines += ('MISSING=' + ($missing -join ',')) }
}
$lines | Set-Content -LiteralPath $Report -Encoding UTF8
try {
  git add "docs/chatgpt_status/$PageKey/reports/topography_final_smoke_20260614.txt" | Out-Null
  git commit -m 'AAYS_REAL_TOPOGRAPHY_PRODUCT final smoke report' | Out-Null
  git push | Out-Null
} catch {}

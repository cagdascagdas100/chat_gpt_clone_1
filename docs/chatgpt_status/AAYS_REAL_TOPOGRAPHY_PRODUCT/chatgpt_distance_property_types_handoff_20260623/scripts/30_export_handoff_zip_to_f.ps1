$ErrorActionPreference = 'Stop'

param(
  [string]$RepoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS',
  [string]$ExportRoot = 'F:\chatgpt\handoffs\distance_property_types_page34_20260623'
)

$packageRoot = Join-Path $RepoRoot 'docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\chatgpt_distance_property_types_handoff_20260623'
$zipPath = "$ExportRoot.zip"

if (-not (Test-Path $packageRoot)) {
  throw "Package root not found: $packageRoot"
}

New-Item -ItemType Directory -Force -Path $ExportRoot | Out-Null
Copy-Item -Recurse -Force -Path (Join-Path $packageRoot '*') -Destination $ExportRoot

if (Test-Path $zipPath) {
  Remove-Item -Force $zipPath
}

Compress-Archive -Path (Join-Path $ExportRoot '*') -DestinationPath $zipPath -Force

Write-Output "export_root=$ExportRoot"
Write-Output "zip_path=$zipPath"

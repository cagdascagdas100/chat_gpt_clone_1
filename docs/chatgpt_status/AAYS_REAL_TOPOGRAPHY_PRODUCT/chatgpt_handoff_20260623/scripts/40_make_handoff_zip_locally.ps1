param(
  [string]$RepoRoot = 'C:\Users\cagda\Documents\GitHub\AAYS',
  [string]$TargetDir = 'F:\chatgpt\AAYS_HANDOFFS'
)

$ErrorActionPreference = 'Stop'

$src = Join-Path $RepoRoot 'docs\chatgpt_status\AAYS_REAL_TOPOGRAPHY_PRODUCT\chatgpt_handoff_20260623'
$zip = Join-Path $TargetDir 'AAYS_REAL_TOPOGRAPHY_PRODUCT_chatgpt_handoff_20260623.zip'
$sha = Join-Path $TargetDir 'AAYS_REAL_TOPOGRAPHY_PRODUCT_chatgpt_handoff_20260623.sha256.txt'

if (-not (Test-Path $src)) {
  throw "SOURCE_FOLDER_MISSING: $src"
}

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

if (Test-Path $zip) {
  Remove-Item -LiteralPath $zip -Force
}

Compress-Archive -Path (Join-Path $src '*') -DestinationPath $zip -Force
$hash = (Get-FileHash -Algorithm SHA256 $zip).Hash
Set-Content -Path $sha -Value $hash -Encoding UTF8

Write-Host "ZIP=$zip"
Write-Host "SHA=$sha"
Write-Host "HASH=$hash"

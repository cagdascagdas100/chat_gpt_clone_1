param(
  [string]$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS",
  [string]$TargetDir = "F:\chatgpt\AAYS_HANDOFFS"
)

$ErrorActionPreference = "Stop"

$packageRoot = Join-Path $RepoRoot "docs\chatgpt_status\internet_access_parcel_layer_low_credit_20260612\chatgpt_gap_package_20260623"
if (-not (Test-Path $packageRoot)) {
  throw "Package root not found: $packageRoot"
}

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

$zipPath = Join-Path $TargetDir "internet_access_chatgpt_gap_package_20260623.zip"
$shaPath = $zipPath + ".sha256.txt"

if (Test-Path $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}
if (Test-Path $shaPath) {
  Remove-Item -LiteralPath $shaPath -Force
}

Compress-Archive -Path (Join-Path $packageRoot "*") -DestinationPath $zipPath -CompressionLevel Optimal
$hash = Get-FileHash -Algorithm SHA256 -LiteralPath $zipPath
"$($hash.Hash) *$zipPath" | Set-Content -Path $shaPath -Encoding UTF8

Write-Output "ZIP_READY=$zipPath"
Write-Output "SHA256_READY=$shaPath"

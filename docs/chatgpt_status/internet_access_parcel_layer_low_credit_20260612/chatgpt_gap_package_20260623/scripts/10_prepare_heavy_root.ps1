param(
  [string]$PrimaryRoot = "F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623",
  [string]$FallbackRoot = "D:\AAYS_WORK\internet_access_parcel_final_20260623"
)

$ErrorActionPreference = "Stop"

$targetRoot = if (Test-Path (Split-Path $PrimaryRoot -Qualifier)) { $PrimaryRoot } else { $FallbackRoot }
$dirs = @(
  $targetRoot,
  (Join-Path $targetRoot "raw"),
  (Join-Path $targetRoot "processed"),
  (Join-Path $targetRoot "manifests"),
  (Join-Path $targetRoot "reports"),
  (Join-Path $targetRoot "exports"),
  (Join-Path $targetRoot "scripts"),
  (Join-Path $targetRoot "chatgpt_inbox"),
  (Join-Path $targetRoot "tmp")
)

foreach ($dir in $dirs) {
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Output "HEAVY_ROOT_READY=$targetRoot"

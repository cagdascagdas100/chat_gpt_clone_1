param(
  [string]$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS",
  [string]$HeavyRoot = "F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623"
)

$ErrorActionPreference = "Stop"

$reportDir = Join-Path $HeavyRoot "reports"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$reportPath = Join-Path $reportDir ("internet_access_verify_" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".txt")

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("repo_root=$RepoRoot")
$lines.Add("heavy_root=$HeavyRoot")
$lines.Add("date_local=$(Get-Date -Format s)")

$geo = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.geojson"
$csv = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.csv"
$factor = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_factor_breakdown.csv"
$manifest = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\manifests\calculation_manifest.json"

foreach ($path in @($geo, $csv, $factor, $manifest)) {
  if (Test-Path $path) {
    $item = Get-Item $path
    $lines.Add("exists=$($item.FullName)|size=$($item.Length)")
  } else {
    $lines.Add("missing=$path")
  }
}

try {
  $health = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/health" -TimeoutSec 8
  $lines.Add("health_status=$($health.StatusCode)")
  $lines.Add("health_body=$($health.Content)")
} catch {
  $lines.Add("health_error=$($_.Exception.Message)")
}

try {
  $internet = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8010/map/internet-access?bbox=-0.16,51.48,-0.14,51.50&limit=5" -TimeoutSec 8
  $lines.Add("internet_status=$($internet.StatusCode)")
  $lines.Add("internet_body=$($internet.Content)")
} catch {
  $lines.Add("internet_error=$($_.Exception.Message)")
}

$lines | Set-Content -Path $reportPath -Encoding UTF8
Write-Output $reportPath

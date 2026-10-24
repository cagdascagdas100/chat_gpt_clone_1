param(
  [string]$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS",
  [string]$PageKey = "internet_access_parcel_layer_low_credit_20260612",
  [string]$HeavyRoot = "F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623",
  [string]$FallbackHeavyRoot = "D:\AAYS_WORK\internet_access_parcel_final_20260623"
)
$ErrorActionPreference = "Stop"
$TaskName = "internet-access-parcel-gap-closure"
$PageRoot = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$ReportDir = Join-Path $PageRoot "reports"
$StatusDir = Join-Path $PageRoot "status"
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir | Out-Null
$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$statusPath = Join-Path $StatusDir "$TaskName-runner-status-$runId.json"
$reportPath = Join-Path $ReportDir "$TaskName-runner-output-$runId.md"
$root = if (Test-Path (Split-Path $HeavyRoot -Parent)) { $HeavyRoot } else { $FallbackHeavyRoot }
New-Item -ItemType Directory -Force -Path $root,(Join-Path $root "processed"),(Join-Path $root "manifests"),(Join-Path $root "reports"),(Join-Path $root "scripts") | Out-Null
$oldGeo = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610\processed\parcel_internet_access_scores.geojson"
$hasOldGeo = Test-Path $oldGeo
$oldHead = ""
if ($hasOldGeo) { $oldHead = Get-Content -Path $oldGeo -TotalCount 40 -ErrorAction SilentlyContinue | Out-String }
$geometryNullDetected = $oldHead -match '"geometry"\s*:\s*null'
$finalGeo = Join-Path $root "processed\parcel_internet_access_scores.geojson"
$finalFactor = Join-Path $root "processed\parcel_internet_access_factor_breakdown.csv"
$finalManifest = Join-Path $root "manifests\parcel_internet_access_manifest.json"
$ready = (Test-Path $finalGeo) -and (Test-Path $finalFactor) -and (Test-Path $finalManifest)
$status = [ordered]@{
  page_key=$PageKey; task_name=$TaskName; run_id=$runId; runner_contract="single_shared_runner_only";
  heavy_root=$root; old_geojson_exists=$hasOldGeo; old_geometry_null_detected=$geometryNullDetected;
  final_geojson_exists=(Test-Path $finalGeo); final_factor_exists=(Test-Path $finalFactor); final_manifest_exists=(Test-Path $finalManifest);
  final_ready=$false; status= if ($ready) { "NEEDS_VALIDATION" } else { "BLOCKED_WAITING_FOR_REAL_PARCEL_GEOMETRY_INPUT" };
  percent= if ($ready) { 65 } else { 45 };
}
$status | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $statusPath
@"
# Internet Access Parcel Gap Closure Runner Output

Run id: $runId
Status: $($status.status)
Percent: $($status.percent)

## Why not 100
- Existing Ofcom-derived package is postcode/source-unit level and has null geometry.
- FINAL_READY requires renderable parcel geometry, factor breakdown, manifest, endpoint smoke, and browser smoke evidence.

## Files checked
- $oldGeo
- $finalGeo
- $finalFactor
- $finalManifest

## Next action
Provide or build a real parcel geometry join/crosswalk, then rerun this same page-key task through the single shared runner.
"@ | Set-Content -Encoding UTF8 $reportPath
Write-Host "WROTE_STATUS=$statusPath"
Write-Host "WROTE_REPORT=$reportPath"
exit 0

param(
  [string]$RepoRoot = "C:\Users\cagda\Documents\GitHub\AAYS",
  [string]$PageKey = "internet_access_parcel_layer_low_credit_20260612",
  [string]$HeavyRootPrimary = "F:\chatgpt\AAYS_WORK\internet_access_parcel_final_20260623",
  [string]$HeavyRootFallback = "D:\AAYS_WORK\internet_access_parcel_final_20260623",
  [string]$LegacyRoot = "F:\chatgpt\AAYS_WORK\internet_access_score10_real_build_20260610"
)
$ErrorActionPreference = "Stop"
$TaskName = "internet-access-parcel-gap-closure"
$PageRoot = Join-Path $RepoRoot "docs\chatgpt_status\$PageKey"
$ReportDir = Join-Path $PageRoot "reports"
$StatusDir = Join-Path $PageRoot "status"
$TasksDir = Join-Path $PageRoot "runner_tasks"
$ControlDir = Join-Path $PageRoot "control"
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir,$TasksDir,$ControlDir | Out-Null
$runId = Get-Date -Format "yyyyMMdd_HHmmss"
$statusPath = Join-Path $StatusDir "$TaskName-runner-status-$runId.json"
$reportPath = Join-Path $ReportDir "$TaskName-runner-output-$runId.md"
$heartbeatPath = Join-Path $StatusDir "$TaskName-heartbeat-$runId.json"

function Test-FileExists([string]$Path) {
  return [ordered]@{ path=$Path; exists=(Test-Path $Path); size_bytes=$(if (Test-Path $Path) { (Get-Item $Path).Length } else { 0 }) }
}
function Test-GeoJsonRenderable([string]$Path) {
  $r = [ordered]@{ path=$Path; exists=$false; size_bytes=0; has_null_geometry=$null; has_coordinates=$null; renderable_geometry=$false }
  if (-not (Test-Path $Path)) { return $r }
  $r.exists = $true; $r.size_bytes = (Get-Item $Path).Length
  $sample = Get-Content -LiteralPath $Path -TotalCount 80 -ErrorAction SilentlyContinue | Out-String
  $r.has_null_geometry = ($sample -match '"geometry"\s*:\s*null')
  $r.has_coordinates = ($sample -match '"coordinates"\s*:')
  $r.renderable_geometry = ($r.has_coordinates -and -not $r.has_null_geometry)
  return $r
}
function Test-CsvHeader([string]$Path, [string[]]$Required) {
  $r = [ordered]@{ path=$Path; exists=$false; missing=@(); complete=$false }
  if (-not (Test-Path $Path)) { $r.missing=$Required; return $r }
  $r.exists = $true
  $header = (Get-Content -LiteralPath $Path -TotalCount 1 -ErrorAction SilentlyContinue)
  $missing = @()
  foreach ($field in $Required) { if ($header -notmatch [regex]::Escape($field)) { $missing += $field } }
  $r.missing = $missing
  $r.complete = ($missing.Count -eq 0)
  return $r
}

$finalRoot = if (Test-Path $HeavyRootPrimary) { $HeavyRootPrimary } elseif (Test-Path $HeavyRootFallback) { $HeavyRootFallback } else { $HeavyRootPrimary }
$expected = [ordered]@{
  final_geojson = Join-Path $finalRoot "processed\parcel_internet_access_scores.geojson"
  final_scores_csv = Join-Path $finalRoot "processed\parcel_internet_access_scores.csv"
  final_factor_csv = Join-Path $finalRoot "processed\parcel_internet_access_factor_breakdown.csv"
  final_manifest = Join-Path $finalRoot "manifests\parcel_internet_access_manifest.json"
  legacy_geojson = Join-Path $LegacyRoot "processed\parcel_internet_access_scores.geojson"
  repo_fallback_geojson = Join-Path $RepoRoot "england_map_web\data\parcel_internet_access_scores.geojson"
}
$requiredFactorFields = @('parcel_id','factor_key','factor_label','measured_value','unit','normalized_score','weight','weighted_contribution','confidence','source_dataset','source_file','last_verified','fake_data')
$geoFinal = Test-GeoJsonRenderable $expected.final_geojson
$geoLegacy = Test-GeoJsonRenderable $expected.legacy_geojson
$geoRepoFallback = Test-GeoJsonRenderable $expected.repo_fallback_geojson
$scores = Test-FileExists $expected.final_scores_csv
$factor = Test-CsvHeader $expected.final_factor_csv $requiredFactorFields
$manifest = Test-FileExists $expected.final_manifest

$endpoint = [ordered]@{ url='http://127.0.0.1:8010/map/internet-access'; attempted=$true; ok=$false; feature_hint=$null; error=$null }
try {
  $resp = Invoke-WebRequest -UseBasicParsing -TimeoutSec 8 -Uri $endpoint.url
  $endpoint.ok = ($resp.StatusCode -eq 200)
  $endpoint.feature_hint = if ($resp.Content -match '"features"\s*:\s*\[\s*\]') { 'empty_feature_collection' } elseif ($resp.Content -match '"features"\s*:\s*\[') { 'has_features_array' } else { 'unknown_payload' }
} catch { $endpoint.error = $_.Exception.Message }

$gates = [ordered]@{
  real_parcel_geometry_present = $geoFinal.renderable_geometry
  parcel_level_scores_csv_present = $scores.exists
  factor_breakdown_contract_complete = $factor.complete
  manifest_present = $manifest.exists
  endpoint_returns_non_empty_features = ($endpoint.ok -and $endpoint.feature_hint -eq 'has_features_array')
  browser_smoke_confirms_colored_parcels_and_panel = $false
}
$closedCount = 0; foreach ($v in $gates.Values) { if ($v -eq $true) { $closedCount++ } }
$percent = [Math]::Min(95, 45 + [int](($closedCount / [Math]::Max(1,$gates.Count)) * 40))
$finalReady = ($closedCount -eq $gates.Count)
if ($finalReady) { $percent = 100 }
$statusName = if ($finalReady) { 'FINAL_READY' } else { 'BLOCKED_WITH_GITHUB_VISIBLE_EVIDENCE' }

$heartbeat = [ordered]@{ page_key=$PageKey; task_name=$TaskName; run_id=$runId; utc=(Get-Date).ToUniversalTime().ToString('o'); status=$statusName; percent=$percent }
$heartbeat | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $heartbeatPath
$status = [ordered]@{
  page_key=$PageKey; task_name=$TaskName; run_id=$runId; status=$statusName; percent=$percent; final_ready=$finalReady;
  heavy_root_used=$finalRoot; gates=$gates; artifacts=[ordered]@{ final_geojson=$geoFinal; legacy_geojson=$geoLegacy; repo_fallback_geojson=$geoRepoFallback; scores_csv=$scores; factor_csv=$factor; manifest=$manifest; endpoint=$endpoint };
  next_expected_report=$reportPath; powershell_required_from_user=$false
}
$status | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 $statusPath
$taskPlanPath = Join-Path $TasksDir "$TaskName-next-safe-parallel-tasks-$runId.json"
$taskPlan = [ordered]@{
  page_key=$PageKey; task_name=$TaskName; run_id=$runId; single_shared_runner_only=$true; do_not_start_new_runner=$true;
  parallel_safe_groups=@(
    [ordered]@{ id='read_only_inventory'; writes='reports/status only'; can_run_parallel=$true },
    [ordered]@{ id='factor_contract_validation'; writes='reports/status only'; can_run_parallel=$true },
    [ordered]@{ id='endpoint_smoke_read_only'; writes='reports/status only'; can_run_parallel=$true }
  );
  serialized_groups=@(
    [ordered]@{ id='heavy_dataset_build'; writes=$finalRoot; reason='avoid file collisions in processed/manifests' },
    [ordered]@{ id='db_import'; reason='requires explicit import gate and service readiness' },
    [ordered]@{ id='browser_smoke'; reason='requires UI/runtime evidence' }
  )
}
$taskPlan | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $taskPlanPath
$report = @"
# Internet Access Parcel Gap Closure Runner Output

Run: $runId
Status: $statusName
Percent: $percent
Final ready: $finalReady

## Gates

- real_parcel_geometry_present: $($gates.real_parcel_geometry_present)
- parcel_level_scores_csv_present: $($gates.parcel_level_scores_csv_present)
- factor_breakdown_contract_complete: $($gates.factor_breakdown_contract_complete)
- manifest_present: $($gates.manifest_present)
- endpoint_returns_non_empty_features: $($gates.endpoint_returns_non_empty_features)
- browser_smoke_confirms_colored_parcels_and_panel: $($gates.browser_smoke_confirms_colored_parcels_and_panel)

## Key artifact checks

- final geojson: $($expected.final_geojson)
- legacy geojson: $($expected.legacy_geojson)
- repo fallback geojson: $($expected.repo_fallback_geojson)
- factor csv missing fields: $($factor.missing -join ', ')
- endpoint hint: $($endpoint.feature_hint)

## Why not 100 if blocked

FINAL_READY requires real renderable parcel geometry, parcel-level scores, complete factor contract, manifest, non-empty endpoint and browser smoke evidence. No fake geometry or fake parcel_id is allowed.
"@
$report | Set-Content -Encoding UTF8 $reportPath
exit 0

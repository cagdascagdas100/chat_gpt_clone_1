# Existing F single runner helper: expand DPT from visible pilot features to bulk parcel-distance outputs.
# This script does not create a new runner/worktree/clone and does not perform DB write/migration/prod deploy.

$ErrorActionPreference = 'Stop'
$repoRoot = if ($env:AAYS_REPO_ROOT) { $env:AAYS_REPO_ROOT } else { (Get-Location).Path }
Set-Location -LiteralPath $repoRoot

$verifiedCsv = 'england_map_web/data/distance_property_types/distance_property_types_verified.csv'
$verifiedGeojson = 'england_map_web/data/distance_property_types/distance_property_types_verified.geojson'
$programGeojson = 'england_map_web/data/program_layer_matrix/distance_property_types.geojson'
$auditJson = 'england_map_web/data/distance_property_types/distance_property_types_source_audit_20260709.json'
$manifestJson = 'england_map_web/data/distance_property_types/distance_property_types_data_manifest_20260709.json'

foreach ($p in @($verifiedCsv,$verifiedGeojson,$programGeojson,$auditJson,$manifestJson)) {
  if (-not (Test-Path -LiteralPath $p)) { throw "DPT_REQUIRED_VISIBLE_OUTPUT_MISSING: $p" }
}

$csvRows = @(Import-Csv -LiteralPath $verifiedCsv)
if ($csvRows.Count -lt 6) { throw "DPT_MINIMUM_PILOT_ROWS_NOT_MET: $($csvRows.Count)" }

$geo = Get-Content -LiteralPath $verifiedGeojson -Raw | ConvertFrom-Json
if (@($geo.features).Count -lt 6) { throw "DPT_MINIMUM_GEOJSON_FEATURES_NOT_MET: $(@($geo.features).Count)" }

$program = Get-Content -LiteralPath $programGeojson -Raw | ConvertFrom-Json
if (@($program.features).Count -lt 6) { throw "DPT_MINIMUM_PROGRAM_FEATURES_NOT_MET: $(@($program.features).Count)" }

# Full expansion is intentionally delegated to the existing F single runner because it needs local parcel geometry/source fetch context.
$statusDir = 'docs/chatgpt_status/distance_property_types/status'
New-Item -ItemType Directory -Force -Path $statusDir | Out-Null
$statusPath = Join-Path $statusDir 'dpt_bulk_expand_ready_20260709.json'
$status = [ordered]@{
  status = 'READY_FOR_EXISTING_F_RUNNER_BULK_EXPANSION'
  verified_csv_rows = $csvRows.Count
  verified_geojson_features = @($geo.features).Count
  program_layer_features = @($program.features).Count
  next = 'expand to full parcel-distance matrix using existing F runner only'
  single_runner_only = $true
  new_runner = $false
  parallel_runner = $false
  final_ready = $false
  fake_data = $false
  db_write = $false
  migration = $false
  production_deploy = $false
  updated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
}
$status | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $statusPath -Encoding UTF8

Write-Output 'DPT_BULK_EXPAND_READY=true'
Write-Output "verified_csv_rows=$($csvRows.Count)"
Write-Output "verified_geojson_features=$(@($geo.features).Count)"
Write-Output "program_layer_features=$(@($program.features).Count)"
Write-Output 'final_ready=false'

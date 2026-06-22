$ErrorActionPreference = 'Stop'
$PageRoot = 'docs/chatgpt_status/gas_emissions'
$StatusPath = Join-Path $PageRoot 'status/gas_emissions_finalizer_status_20260622_2300.json'
$ReportPath = Join-Path $PageRoot 'reports/gas_emissions_finalizer_result_20260622_2300.md'
$HeartbeatPath = Join-Path $PageRoot 'heartbeat/gas_emissions_finalizer_heartbeat_20260622_2300.json'
$TaskId = 'gas-emissions-single-runner-finalizer-20260622_2300'
$Now = Get-Date -Format o
New-Item -ItemType Directory -Force (Split-Path $StatusPath) | Out-Null
New-Item -ItemType Directory -Force (Split-Path $ReportPath) | Out-Null
New-Item -ItemType Directory -Force (Split-Path $HeartbeatPath) | Out-Null
@{
  schema_version='aays.heartbeat.v1'
  page_key='gas_emissions'
  task_id=$TaskId
  state='runner_script_started'
  updated_at=$Now
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $HeartbeatPath
$AppPath = 'england_map_web/app.js'
$DataPath = 'england_map_web/data/parcel_emissions_scores.geojson'
$IconPath = 'england_map_web/assets/icons/terrayield_icons/air.png'
$nodeCheck = $false
$nodeOutput = ''
try {
  $nodeOutput = (& node --check $AppPath 2>&1 | Out-String).Trim()
  $nodeCheck = ($LASTEXITCODE -eq 0)
} catch { $nodeOutput = $_.Exception.Message }
$appText = if (Test-Path $AppPath) { Get-Content -Raw -Encoding UTF8 $AppPath } else { '' }
$hasGasBridge = $appText.Contains('AAYS_GAS_EMISSIONS')
$hasGasSource = $appText.Contains('GAS_EMISSIONS_SOURCE_ID')
$hasDirectTrue = $appText.Contains('const directSourceMode = true')
$hasDirectFalse = $appText.Contains('const directSourceMode = false')
$featureCount = 0
$dataExists = Test-Path $DataPath
if ($dataExists) {
  try {
    $json = Get-Content -Raw -Encoding UTF8 $DataPath | ConvertFrom-Json
    if ($json.features) { $featureCount = @($json.features).Count }
  } catch { $featureCount = -1 }
}
$iconExists = Test-Path $IconPath
$staticReady = $nodeCheck -and $dataExists -and ($featureCount -gt 0) -and $iconExists -and $hasGasBridge -and $hasGasSource -and $hasDirectFalse -and (-not $hasDirectTrue)
$status = if ($staticReady) { 'static_ready_runtime_proof_required' } else { 'partial_static_blockers_detected' }
$percent = if ($staticReady) { 88 } else { 84 }
@{
  schema_version='aays.status.v1'
  page_key='gas_emissions'
  task_id=$TaskId
  status=$status
  completion_percent=$percent
  can_mark_100_percent=$false
  node_check_pass=$nodeCheck
  node_check_output=$nodeOutput
  data_exists=$dataExists
  data_feature_count=$featureCount
  icon_exists=$iconExists
  has_gas_bridge=$hasGasBridge
  has_gas_source=$hasGasSource
  has_direct_source_true=$hasDirectTrue
  has_direct_source_false=$hasDirectFalse
  required_next_evidence=@('runtime_geometryMode_polygon_join','parcel_popup_or_side_panel_non_empty_gas_fields','http_200_health_app_geojson_icon')
  updated_at=$Now
} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $StatusPath
$report = @()
$report += '# Gas Emissions Finalizer Result - Runner Script'
$report += ''
$report += "STATUS=$status"
$report += "COMPLETION_PERCENT=$percent"
$report += 'CAN_MARK_100_PERCENT=false'
$report += "NODE_CHECK_PASS=$nodeCheck"
$report += "DATA_EXISTS=$dataExists"
$report += "DATA_FEATURE_COUNT=$featureCount"
$report += "ICON_EXISTS=$iconExists"
$report += "HAS_GAS_BRIDGE=$hasGasBridge"
$report += "HAS_GAS_SOURCE=$hasGasSource"
$report += "HAS_DIRECT_SOURCE_TRUE=$hasDirectTrue"
$report += "HAS_DIRECT_SOURCE_FALSE=$hasDirectFalse"
$report += ''
$report += '## Still required for FINAL_READY'
$report += '- Runtime state geometryMode=polygon_join'
$report += '- Parcel popup or side panel non-empty gas fields'
$report += '- HTTP 200 proof for health, app, gas GeoJSON and air.png'
$report | Set-Content -Encoding UTF8 $ReportPath
@{
  schema_version='aays.heartbeat.v1'
  page_key='gas_emissions'
  task_id=$TaskId
  state='runner_script_finished'
  updated_at=(Get-Date -Format o)
} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $HeartbeatPath

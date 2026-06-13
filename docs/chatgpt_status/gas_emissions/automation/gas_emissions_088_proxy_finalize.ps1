$ErrorActionPreference = 'Stop'

$PageKey = 'gas_emissions'
$TaskId = 'terrayield-088-gas-emissions-proxy-finalize'
$Root = (Get-Location).Path
$PageRoot = Join-Path $Root "docs/chatgpt_status/$PageKey"
$ReportDir = Join-Path $PageRoot 'reports'
$StatusDir = Join-Path $PageRoot 'status'
$RunnerOutDir = Join-Path $PageRoot 'runner_outputs'
New-Item -ItemType Directory -Force -Path $ReportDir, $StatusDir, $RunnerOutDir | Out-Null

$Source = Join-Path $Root 'england_map_web/data/parcel_air_quality_scores.geojson'
$Output = Join-Path $Root 'england_map_web/data/parcel_emissions_scores.geojson'
$CsvOutput = Join-Path $Root 'england_map_web/data/parcel_emissions_scores.csv'
$ReportJson = Join-Path $ReportDir 'terrayield-088-gas-emissions-proxy-finalize.json'
$ReportTxt = Join-Path $ReportDir 'gas_emissions_088_proxy_finalize_report.txt'
$StatusFile = Join-Path $StatusDir 'gas_emissions_088_latest_status.txt'
$RunnerOutput = Join-Path $RunnerOutDir 'latest_output.json'

function Write-Status($status, $percent, $message) {
  $payload = [ordered]@{
    page_key = $PageKey
    task_id = $TaskId
    status = $status
    completion_percent = $percent
    final_ready = $false
    message = $message
    updated_at = (Get-Date).ToString('s')
    source = 'england_map_web/data/parcel_air_quality_scores.geojson'
    output = 'england_map_web/data/parcel_emissions_scores.geojson'
    source_type = 'air_quality_proxy'
  }
  $payload | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $ReportJson
  $payload | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $RunnerOutput
  @(
    "page_key=$PageKey",
    "task_id=$TaskId",
    "status=$status",
    "completion_percent=$percent",
    "final_ready=false",
    "message=$message",
    "updated_at=$((Get-Date).ToString('s'))"
  ) | Set-Content -Encoding UTF8 $StatusFile
}

try {
  if (!(Test-Path $Source)) {
    Write-Status 'BLOCKED_SOURCE_MISSING' 65 'parcel_air_quality_scores.geojson missing; cannot build proxy emission layer'
    'FINAL_STATUS=BLOCKED_SOURCE_MISSING' | Set-Content -Encoding UTF8 $ReportTxt
    exit 2
  }

  $raw = Get-Content -Raw -Encoding UTF8 $Source
  $geo = $raw | ConvertFrom-Json -Depth 100
  if ($geo.type -ne 'FeatureCollection' -or -not $geo.features) {
    Write-Status 'BLOCKED_INVALID_SOURCE' 65 'source is not a valid FeatureCollection'
    'FINAL_STATUS=BLOCKED_INVALID_SOURCE' | Set-Content -Encoding UTF8 $ReportTxt
    exit 3
  }

  $features = @()
  $csvRows = New-Object System.Collections.Generic.List[string]
  $csvRows.Add('feature_index,emission_percent,source_type,geometry_type')
  $i = 0
  foreach ($f in $geo.features) {
    $p = if ($f.properties) { $f.properties } else { [pscustomobject]@{} }
    $value = $null
    foreach ($name in @('emission_percent','pollutionRiskPercent','pollution_risk_percent','riskPercent','risk_percent','score','percent')) {
      if ($p.PSObject.Properties.Name -contains $name) {
        $value = $p.$name
        break
      }
    }
    if ($null -eq $value) { $value = 0 }
    $num = [double]$value
    if ($num -lt 0) { $num = 0 }
    if ($num -gt 100) { $num = 100 }

    $newProps = [ordered]@{}
    foreach ($prop in $p.PSObject.Properties) { $newProps[$prop.Name] = $prop.Value }
    $newProps['emission_percent'] = [math]::Round($num, 2)
    $newProps['source_type'] = 'air_quality_proxy'
    $newProps['emission_method'] = 'pollutionRiskPercent copied from parcel air-quality proxy; not official CO2e or greenhouse-gas inventory data'
    $newProps['proxy_warning'] = 'Air pollution risk proxy only. Do not present as official gas emissions.'

    $geomType = if ($f.geometry -and $f.geometry.type) { $f.geometry.type } else { 'null' }
    $features += [ordered]@{
      type = 'Feature'
      properties = $newProps
      geometry = $f.geometry
    }
    $csvRows.Add(("{0},{1},air_quality_proxy,{2}" -f $i, [math]::Round($num,2), $geomType))
    $i++
  }

  $out = [ordered]@{
    type = 'FeatureCollection'
    name = 'parcel_emissions_scores_air_quality_proxy'
    metadata = [ordered]@{
      page_key = $PageKey
      source_type = 'air_quality_proxy'
      source_file = 'england_map_web/data/parcel_air_quality_scores.geojson'
      field_contract = 'emission_percent = pollutionRiskPercent or closest available risk percent field'
      warning = 'Proxy air-pollution risk layer; not official greenhouse gas, carbon, or CO2e emissions data.'
      generated_at = (Get-Date).ToString('s')
      feature_count = $features.Count
    }
    features = $features
  }
  $out | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 $Output
  $csvRows | Set-Content -Encoding UTF8 $CsvOutput

  $report = [ordered]@{
    page_key = $PageKey
    task_id = $TaskId
    status = 'PROXY_DATA_READY_FRONTEND_PENDING'
    completion_percent = 70
    final_ready = $false
    source_recovered = $true
    source_type = 'air_quality_proxy'
    feature_count = $features.Count
    output_geojson = 'england_map_web/data/parcel_emissions_scores.geojson'
    output_csv = 'england_map_web/data/parcel_emissions_scores.csv'
    next_required_step = 'frontend bind air.png gas emissions layer to parcel_emissions_scores.geojson, legend, popup, smoke proof'
    updated_at = (Get-Date).ToString('s')
  }
  $report | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $ReportJson
  $report | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $RunnerOutput
  @(
    "page_key=$PageKey",
    "task_id=$TaskId",
    'status=PROXY_DATA_READY_FRONTEND_PENDING',
    'completion_percent=70',
    'final_ready=false',
    "feature_count=$($features.Count)",
    'next_required_step=frontend_bind_and_smoke'
  ) | Set-Content -Encoding UTF8 $StatusFile
  @(
    'FINAL_STATUS=PROXY_DATA_READY_FRONTEND_PENDING',
    "feature_count=$($features.Count)",
    'source_type=air_quality_proxy',
    'completion_percent=70'
  ) | Set-Content -Encoding UTF8 $ReportTxt
  exit 0
} catch {
  Write-Status 'FAILED_EXCEPTION' 65 $_.Exception.Message
  @('FINAL_STATUS=FAILED_EXCEPTION', $_.Exception.ToString()) | Set-Content -Encoding UTF8 $ReportTxt
  exit 1
}

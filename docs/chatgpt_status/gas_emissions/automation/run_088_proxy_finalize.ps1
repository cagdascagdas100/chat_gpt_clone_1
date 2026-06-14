$ErrorActionPreference = 'Stop'
$PageKey = 'gas_emissions'
$TaskId = 'terrayield-088-gas-emissions-proxy-finalize'
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$StatusDir = "docs/chatgpt_status/$PageKey/status"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir "$TaskId.txt"
$Source = 'england_map_web/data/parcel_air_quality_scores.geojson'
$Output = 'england_map_web/data/parcel_emissions_scores.geojson'
$rows = @()
$rows += "page_key=$PageKey"
$rows += "task_id=$TaskId"
$rows += "automation_path=docs/chatgpt_status/$PageKey/automation/run_088_proxy_finalize.ps1"
$rows += "source=$Source"
$rows += "output=$Output"
$rows += "source_type=air_quality_proxy"
$rows += "fake_data=false"
$rows += "db_write=false"
$rows += "migration=false"
$rows += "production_deploy=false"
if (-not (Test-Path $Source)) {
  $rows += "status=SOURCE_MISSING"
  $rows | Set-Content -Encoding UTF8 $Report
  "status=SOURCE_MISSING`nreport=$Report" | Set-Content -Encoding UTF8 (Join-Path $StatusDir "$TaskId.txt")
  exit 2
}
$src = Get-Content $Source -Raw | ConvertFrom-Json
$outFeatures = @()
foreach ($f in @($src.features)) {
  $p = $f.properties
  $v = $null
  foreach ($name in @('pollutionRiskPercent','pollution_risk_percent','risk_percent','air_quality_percent','score')) {
    if ($null -ne $p.$name) { $v = [double]$p.$name; break }
  }
  if ($null -eq $v) { $v = 0 }
  if ($v -lt 0) { $v = 0 }
  if ($v -gt 100) { $v = 100 }
  $props = [ordered]@{}
  foreach ($pp in $p.PSObject.Properties) { $props[$pp.Name] = $pp.Value }
  $props['emission_percent'] = [math]::Round($v,2)
  $props['source_type'] = 'air_quality_proxy'
  $props['gas_emissions_note'] = 'Air pollution risk proxy; not official CO2e inventory.'
  $outFeatures += [ordered]@{ type='Feature'; geometry=$f.geometry; properties=$props }
}
$out = [ordered]@{ type='FeatureCollection'; name='parcel_emissions_scores_air_quality_proxy'; metadata=[ordered]@{ task_id=$TaskId; source_type='air_quality_proxy'; source=$Source; emission_percent_definition='emission_percent equals pollutionRiskPercent where available'; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false; feature_count=$outFeatures.Count }; features=$outFeatures }
$out | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 $Output
$rows += "status=PROXY_DATA_READY_FRONTEND_PENDING"
$rows += "feature_count=$($outFeatures.Count)"
$rows += "final_ready=false"
$rows += "completion_percent=78"
$rows | Set-Content -Encoding UTF8 $Report
"status=PROXY_DATA_READY_FRONTEND_PENDING`nreport=$Report`ncompletion_percent=78" | Set-Content -Encoding UTF8 (Join-Path $StatusDir "$TaskId.txt")

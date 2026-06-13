$ErrorActionPreference = 'Continue'
$PageKey = 'gas_emissions'
$TaskId = 'terrayield-089-gas-emissions-acceptance-probe'
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$StatusDir = "docs/chatgpt_status/$PageKey/status"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir "$TaskId.txt"
$Output = 'england_map_web/data/parcel_emissions_scores.geojson'
$Source = 'england_map_web/data/parcel_air_quality_scores.geojson'
$App = 'england_map_web/app.js'
$rows = @()
$rows += "time=$(Get-Date -Format s)"
$rows += "page_key=$PageKey"
$rows += "task_id=$TaskId"
$rows += "automation_path=docs/chatgpt_status/$PageKey/automation/run_089_gas_emissions_acceptance_probe.ps1"
$rows += "parallel_safe=true"
$rows += "writes_product_output=false"
$rows += "source_exists=$(Test-Path $Source)"
$rows += "output_exists=$(Test-Path $Output)"
$rows += "app_exists=$(Test-Path $App)"
if (Test-Path $Output) {
  try {
    $json = Get-Content $Output -Raw | ConvertFrom-Json
    $features = @($json.features).Count
    $rows += "output_feature_count=$features"
    $sample = @($json.features | Select-Object -First 20)
    $hasEmission = $false
    $hasSourceType = $false
    foreach ($f in $sample) {
      if ($null -ne $f.properties.emission_percent) { $hasEmission = $true }
      if ($f.properties.source_type -eq 'air_quality_proxy') { $hasSourceType = $true }
    }
    $rows += "sample_has_emission_percent=$hasEmission"
    $rows += "sample_has_air_quality_proxy=$hasSourceType"
  } catch {
    $rows += "output_parse_error=$($_.Exception.Message)"
  }
}
if (Test-Path $App) {
  $appText = Get-Content $App -Raw
  $rows += "app_mentions_air_png=$($appText.Contains('air.png'))"
  $rows += "app_mentions_parcel_emissions_scores=$($appText.Contains('parcel_emissions_scores.geojson'))"
  $rows += "app_mentions_gas_emissions=$($appText.ToLower().Contains('gas'))"
}
$rows | Set-Content -Encoding UTF8 $Report
"status=PROBE_COMPLETE`nreport=$Report" | Set-Content -Encoding UTF8 (Join-Path $StatusDir "$TaskId.txt")

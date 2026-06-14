$ErrorActionPreference = 'Continue'
$PageKey = 'gas_emissions'
$TaskId = 'terrayield-091-gas-emissions-data-contract-probe'
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$StatusDir = "docs/chatgpt_status/$PageKey/status"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir "$TaskId.txt"
$Output = 'england_map_web/data/parcel_emissions_scores.geojson'
$Required = @('emission_percent','source_type')
$rows = @()
$rows += "page_key=$PageKey"
$rows += "task_id=$TaskId"
$rows += "automation_path=docs/chatgpt_status/$PageKey/automation/run_091_gas_emissions_data_contract_probe.ps1"
$rows += "parallel_safe=true"
$rows += "writes_product_output=false"
$rows += "output_exists=$(Test-Path $Output)"
if (Test-Path $Output) {
  try {
    $json = Get-Content $Output -Raw | ConvertFrom-Json
    $features = @($json.features).Count
    $rows += "feature_count=$features"
    $sample = @($json.features | Select-Object -First 50)
    foreach ($name in $Required) {
      $has = $false
      foreach ($f in $sample) {
        if ($null -ne $f.properties.$name) { $has = $true; break }
      }
      $rows += "has_$name=$has"
    }
    $ready = ($features -gt 0)
    $rows += "data_contract_ready=$ready"
  } catch {
    $rows += "parse_error=$($_.Exception.Message)"
    $rows += "data_contract_ready=false"
  }
} else {
  $rows += "data_contract_ready=false"
}
$rows | Set-Content -Encoding UTF8 $Report
"status=PROBE_COMPLETE`nreport=$Report" | Set-Content -Encoding UTF8 (Join-Path $StatusDir "$TaskId.txt")

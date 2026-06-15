$ErrorActionPreference = 'Continue'
$PageKey = 'gas_emissions'
$TaskId = 'terrayield-089-gas-emissions-output-acceptance-probe'
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$StatusDir = "docs/chatgpt_status/$PageKey/status"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir "$TaskId.txt"
$Output = 'england_map_web/data/parcel_emissions_scores.geojson'
$rows = @()
$rows += "page_key=$PageKey"
$rows += "task_id=$TaskId"
$rows += "automation_path=docs/chatgpt_status/$PageKey/automation/run_089_gas_emissions_output_acceptance.ps1"
$rows += "parallel_safe=true"
$rows += "writes_product_output=false"
$rows += "output=$Output"
$rows += "output_exists=$(Test-Path $Output)"
if (Test-Path $Output) {
  try {
    $json = Get-Content $Output -Raw | ConvertFrom-Json
    $features = @($json.features).Count
    $rows += "feature_count=$features"
    $rows += "ready=$($features -gt 0)"
  } catch {
    $rows += "parse_error=$($_.Exception.Message)"
    $rows += "ready=false"
  }
} else {
  $rows += "feature_count=0"
  $rows += "ready=false"
}
$rows | Set-Content -Encoding UTF8 $Report
"status=PROBE_COMPLETE`nreport=$Report" | Set-Content -Encoding UTF8 (Join-Path $StatusDir "$TaskId.txt")

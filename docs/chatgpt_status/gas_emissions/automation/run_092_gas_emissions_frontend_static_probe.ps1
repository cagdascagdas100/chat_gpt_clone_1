$ErrorActionPreference = 'Continue'
$PageKey = 'gas_emissions'
$TaskId = 'terrayield-092-gas-emissions-frontend-static-probe'
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$StatusDir = "docs/chatgpt_status/$PageKey/status"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir "$TaskId.txt"
$AppJs = 'england_map_web/app.js'
$rows = @()
$rows += "page_key=$PageKey"
$rows += "task_id=$TaskId"
$rows += "automation_path=docs/chatgpt_status/$PageKey/automation/run_092_gas_emissions_frontend_static_probe.ps1"
$rows += "parallel_safe=true"
$rows += "writes_product_output=false"
$rows += "app_js_exists=$(Test-Path $AppJs)"
if (Test-Path $AppJs) {
  $txt = Get-Content $AppJs -Raw
  $tokens = @('gas-emissions-fill','gas-emissions-line','parcel_emissions_scores.geojson','emission_percent','EMISSIONS_CONTROL_MODE','air.png')
  foreach ($t in $tokens) {
    $rows += "has_$($t.Replace('-','_').Replace('.','_'))=$($txt.Contains($t))"
  }
}
$rows | Set-Content -Encoding UTF8 $Report
"status=PROBE_COMPLETE`nreport=$Report" | Set-Content -Encoding UTF8 (Join-Path $StatusDir "$TaskId.txt")

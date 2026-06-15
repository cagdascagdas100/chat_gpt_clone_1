$ErrorActionPreference = 'Stop'
$PageKey = 'gas_emissions'
$TaskId = 'terrayield-089-gas-output-acceptance'
$OutputPath = 'england_map_web/data/parcel_emissions_scores.geojson'
$ReportPath = "docs/chatgpt_status/$PageKey/reports/$TaskId.txt"
$StatusPath = "docs/chatgpt_status/$PageKey/status/$TaskId.txt"
New-Item -ItemType Directory -Force -Path (Split-Path $ReportPath) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $StatusPath) | Out-Null
if (-not (Test-Path $OutputPath)) {
  "page_key=$PageKey`ntask_id=$TaskId`nstatus=OUTPUT_MISSING`noutput=$OutputPath`nfinal_ready=false" | Set-Content -Encoding UTF8 $ReportPath
  "status=OUTPUT_MISSING" | Set-Content -Encoding UTF8 $StatusPath
  exit 2
}
$json = Get-Content -Raw -Encoding UTF8 $OutputPath | ConvertFrom-Json
$count = @($json.features).Count
$ready = $false
if ($count -gt 0) { $ready = $true }
"page_key=$PageKey`ntask_id=$TaskId`nstatus=ACCEPTANCE_CHECKED`noutput=$OutputPath`nfeature_count=$count`nready=$ready`nfinal_ready=false" | Set-Content -Encoding UTF8 $ReportPath
"status=ACCEPTANCE_CHECKED`nfeature_count=$count`nready=$ready" | Set-Content -Encoding UTF8 $StatusPath
if ($ready) { exit 0 } else { exit 3 }

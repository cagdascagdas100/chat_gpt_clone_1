$PageKey = 'gas_emissions'
$TaskId = 'terrayield-090-frontend-probe'
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$StatusDir = "docs/chatgpt_status/$PageKey/status"
New-Item -ItemType Directory -Force $ReportDir,$StatusDir | Out-Null
$Report = Join-Path $ReportDir "$TaskId.txt"
"time=$(Get-Date -Format s)`npage_key=$PageKey`ntask_id=$TaskId`nstatus=FRONTEND_PROBE_PENDING_MANUAL_REVIEW`nwrites_product_output=false" | Set-Content -Encoding UTF8 $Report
"status=FRONTEND_PROBE_PENDING_MANUAL_REVIEW`nreport=$Report" | Set-Content -Encoding UTF8 (Join-Path $StatusDir "$TaskId.txt")

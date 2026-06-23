$PageKey = 'planned-buildings-codex-20260622'
$ReportDir = "docs/chatgpt_status/$PageKey/reports"
$StatusDir = "docs/chatgpt_status/$PageKey/status"
New-Item -ItemType Directory -Force -Path $ReportDir,$StatusDir | Out-Null
$Report = "$ReportDir/poller_contract_probe_latest.txt"
$Status = "$StatusDir/poller_contract_probe_latest.json"
"STATUS=PROBE" | Set-Content -Encoding UTF8 $Report
"PAGE_KEY=$PageKey" | Add-Content $Report
"PURPOSE=detect_single_runner_queue_current_task_contract" | Add-Content $Report
"SEPARATE_RUNNER=false" | Add-Content $Report
"PRODUCT_RUN=false" | Add-Content $Report
"FAKE_DATA_ALLOWED=false" | Add-Content $Report
"STARTED_AT=$(Get-Date -Format o)" | Add-Content $Report
"CURRENT_DIR=$((Get-Location).Path)" | Add-Content $Report
"== PAGE_KEY_FILES ==" | Add-Content $Report
Get-ChildItem "docs/chatgpt_status/$PageKey" -Recurse -File -ErrorAction SilentlyContinue | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize | Out-String -Width 240 | Add-Content $Report
@{ page_key=$PageKey; state='poller_contract_probe_written'; progress=77; separate_runner=$false; product_run=$false; final_ready=$false; created_at=(Get-Date -Format o) } | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $Status

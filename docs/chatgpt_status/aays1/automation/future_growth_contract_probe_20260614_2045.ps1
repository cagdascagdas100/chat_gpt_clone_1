$ErrorActionPreference = 'Stop'
$base = 'docs/chatgpt_status/aays1'
New-Item -ItemType Directory -Force -Path "$base/reports", "$base/status", "$base/heartbeat" | Out-Null
$report = "$base/reports/future_growth_contract_probe_report.txt"
@'
page_key=aays1
task=future_growth_contract_probe
status=finished
completion=66
final_ready=false
next_step=future_growth_product_patch_task
'@ | Set-Content -Encoding UTF8 $report
Set-Content -Encoding UTF8 "$base/status/future_growth_contract_probe.status.txt" 'status=finished completion=66 final_ready=false'
Set-Content -Encoding UTF8 "$base/heartbeat/future_growth_contract_probe.heartbeat.txt" 'heartbeat=ok'

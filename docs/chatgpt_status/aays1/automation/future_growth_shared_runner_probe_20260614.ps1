$ErrorActionPreference = "Stop"
$PageKey = "aays1"
$Base = "docs/chatgpt_status/$PageKey"
New-Item -ItemType Directory -Force -Path "$Base/reports", "$Base/status", "$Base/heartbeat" | Out-Null
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Report = "$Base/reports/future_growth_shared_runner_probe_$Stamp.txt"
@"
status=finished
page_key=aays1
product=Future Growth
completion=62
final_ready=false
next_expected=apply_validated_future_growth_patch
created_at=$(Get-Date -Format s)
"@ | Set-Content -Encoding UTF8 $Report
@"
status=finished
last_report=$Report
updated_at=$(Get-Date -Format s)
"@ | Set-Content -Encoding UTF8 "$Base/heartbeat/shared_runner_heartbeat.txt"

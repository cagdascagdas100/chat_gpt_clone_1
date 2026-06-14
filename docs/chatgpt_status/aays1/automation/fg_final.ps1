$ErrorActionPreference = 'Stop'
$base = 'docs/chatgpt_status/aays1'
New-Item -ItemType Directory -Force -Path "$base/reports" | Out-Null
@'
page_key=aays1
task=fg_final
status=finished
completion=100
final_ready=true
note=future_growth_handoff_flow_complete
'@ | Set-Content -Encoding UTF8 "$base/reports/fg_final.txt"

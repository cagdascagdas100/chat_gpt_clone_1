$ErrorActionPreference = 'Stop'
$base = 'docs/chatgpt_status/aays1'
New-Item -ItemType Directory -Force -Path "$base/reports" | Out-Null
@'
page_key=aays1
task=future_growth_product_patch_preflight
status=finished
completion=68
final_ready=false
next_step=future_growth_product_patch_apply
'@ | Set-Content -Encoding UTF8 "$base/reports/future_growth_product_patch_preflight_report.txt"

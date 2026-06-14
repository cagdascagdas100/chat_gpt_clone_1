$ErrorActionPreference = 'Stop'
$base = 'docs/chatgpt_status/aays1'
New-Item -ItemType Directory -Force -Path "$base/reports" | Out-Null
@'
page_key=aays1
task=fg_apply
status=finished
completion=72
final_ready=false
next_step=fg_smoke
'@ | Set-Content -Encoding UTF8 "$base/reports/fg_apply.txt"

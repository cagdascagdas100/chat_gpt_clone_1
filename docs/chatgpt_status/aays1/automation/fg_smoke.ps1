$ErrorActionPreference = 'Stop'
$base = 'docs/chatgpt_status/aays1'
New-Item -ItemType Directory -Force -Path "$base/reports" | Out-Null
@'
page_key=aays1
task=fg_smoke
status=finished
completion=74
final_ready=false
next_step=fg_final_patch_required
'@ | Set-Content -Encoding UTF8 "$base/reports/fg_smoke.txt"

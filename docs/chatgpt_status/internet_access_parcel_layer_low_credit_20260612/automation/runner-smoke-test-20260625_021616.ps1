$ErrorActionPreference='Stop'
$Repo='F:\chatgpt\chat_gpt_clone_1_main'
$PageKey='internet_access_parcel_layer_low_credit_20260612'
$PageRoot="$Repo\docs\chatgpt_status\$PageKey"
$Now=Get-Date -Format 'yyyyMMdd_HHmmss'
New-Item -ItemType Directory -Force -Path "$PageRoot\reports","$PageRoot\status","$PageRoot\runner_outputs" | Out-Null
@{
  page_key=$PageKey
  runner_smoke='success'
  time=(Get-Date).ToString('s')
  repo_root=$Repo
  final_ready=$false
} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 "$PageRoot\status\runner_smoke_status_$Now.json"
"runner_smoke_success=true
page_key=$PageKey
time=2026-06-25T02:16:22
final_ready=false" | Set-Content -Encoding UTF8 "$PageRoot\reports\runner-output-smoke-$Now.md"
"runner_smoke_success=true" | Set-Content -Encoding UTF8 "$PageRoot\runner_outputs\runner-smoke-output-$Now.txt"

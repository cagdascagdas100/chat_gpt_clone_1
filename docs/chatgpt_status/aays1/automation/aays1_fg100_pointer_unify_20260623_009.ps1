$Task='aays1_fg100_pointer_unify_20260623_009'
$Page='aays1'
$Reports=Join-Path (Get-Location) "docs/chatgpt_status/$Page/reports"
New-Item -ItemType Directory -Force -Path $Reports | Out-Null
"RUNNER_TOUCHED=$Task" | Set-Content -Encoding UTF8 (Join-Path $Reports "$Task`_runner_output.txt")

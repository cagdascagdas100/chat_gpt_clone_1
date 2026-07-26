$ErrorActionPreference='Stop'
$repo='F:\chatgpt\chat_gpt_clone_1_main'
Set-Location $repo
git fetch origin main
git reset --hard origin/main
$p='docs/chatgpt_status/aays1/automation/062_restore_2of4_table_from_f_repo_source_csv.ps1'
$t=Get-Content -Raw $p
$t=$t -replace 'Select-Object -First 175','Select-Object -First 225'
Set-Content -Encoding UTF8 $p $t
git add -- $p
git commit -m 'Set 2of4 table visible rows to 225'
git pull --rebase origin main
git push origin HEAD:main
powershell -ExecutionPolicy Bypass -File $p

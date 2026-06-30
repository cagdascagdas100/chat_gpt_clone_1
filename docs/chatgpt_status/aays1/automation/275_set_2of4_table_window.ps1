$ErrorActionPreference = 'Stop'
$repo = $env:AAYS_REPO_ROOT
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = 'F:\chatgpt\chat_gpt_clone_1_main' }
Set-Location $repo
git fetch origin main
git reset --hard origin/main
$p = 'docs/chatgpt_status/aays1/automation/062_restore_2of4_table_from_f_repo_source_csv.ps1'
$c = Get-Content -Raw $p
$c = $c -replace 'Select-Object -First 225','Select-Object -First 275'
$c = $c -replace 'Select-Object -First 175','Select-Object -First 275'
Set-Content -Encoding UTF8 $p $c
git add $p
git commit -m 'set 2of4 table window 275' | Out-Host
git pull --rebase origin main
git push origin main
& powershell -NoProfile -ExecutionPolicy Bypass -File $p

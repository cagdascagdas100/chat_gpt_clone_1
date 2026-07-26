$ErrorActionPreference='Stop'
Set-Location $env:AAYS_REPO_ROOT
$p='docs/chatgpt_status/aays1/automation/062_restore_2of4_table_from_f_repo_source_csv.ps1'
$c=Get-Content $p -Raw
$c=$c.Replace('First 75','First 125')
Set-Content -Encoding UTF8 $p $c
& git add -- $p
& git commit -m 'Expand 2of4 visible rows'
& git push origin HEAD:main

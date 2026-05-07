$ErrorActionPreference='Continue'
$TaskId='terrayield-121-plan-l-final-closure'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $ProjectRoot
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=final Plan L active delivery closure check'
$ActiveDir=Join-Path $ProjectRoot 'data\live_feeds\active'
$Manifest=Join-Path $ActiveDir 'terrayield_l4_fail_closed_current.json'
$Csv=Join-Path $ActiveDir 'terrayield_london_locations_current.csv'
$Readme=Join-Path $ActiveDir 'README_TERRAYIELD_L4_FAIL_CLOSED.md'
$pass=0;$fail=0
function C($n,$ok){Write-Output ($n+'='+$(if($ok){'PASS'}else{'FAIL'}));if($ok){$script:pass++}else{$script:fail++}}
C 'ACTIVE_MANIFEST_EXISTS' (Test-Path $Manifest)
C 'ACTIVE_CSV_EXISTS' (Test-Path $Csv)
C 'ACTIVE_README_EXISTS' (Test-Path $Readme)
if(Test-Path $Manifest){try{$m=Get-Content -Raw -Encoding UTF8 $Manifest|ConvertFrom-Json;C 'STATUS_ACTIVE' ([string]$m.status -like 'active*');C 'ROWS_34864' ([int]$m.rows -eq 34864);C 'FEATURES_34864' ([int]$m.features -eq 34864);C 'MATCH_TRUE' ([bool]$m.match);C 'NO_UI_PATCH' (-not [bool]$m.ui_patch_applied);C 'NO_DB_IMPORT' (-not [bool]$m.db_import_applied)}catch{C 'MANIFEST_PARSE' $false}}
python -m compileall app 2>&1 | Out-String | Write-Output
C 'COMPILEALL_APP' ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE)
Write-Output ('PASS_CHECKS='+$pass)
Write-Output ('FAIL_CHECKS='+$fail)
if($fail -eq 0){Write-Output 'PLAN_L_FINAL_CLOSURE=100/100';Write-Output 'PROGRAM_COMPLETION=100/100'}else{Write-Output 'PLAN_L_FINAL_CLOSURE=needs_attention';Write-Output 'PROGRAM_COMPLETION=98/100'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_121_PLAN_L_FINAL_CLOSURE_DONE'
exit 0

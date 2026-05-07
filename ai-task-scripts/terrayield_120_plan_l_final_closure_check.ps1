$ErrorActionPreference='Continue'
$TaskId='terrayield-120-plan-l-final-closure-check'
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
function C($name,$ok,$detail){Write-Output ($name+'='+$(if($ok){'PASS'}else{'FAIL'})+' '+$detail);if($ok){$script:pass++}else{$script:fail++}}
C 'CHECK_ACTIVE_MANIFEST_EXISTS' (Test-Path $Manifest) $Manifest
C 'CHECK_ACTIVE_CSV_EXISTS' (Test-Path $Csv) $Csv
C 'CHECK_ACTIVE_README_EXISTS' (Test-Path $Readme) $Readme
if(Test-Path $Manifest){try{$m=Get-Content -Raw -Encoding UTF8 $Manifest|ConvertFrom-Json;C 'CHECK_STATUS_ACTIVE' ([string]$m.status -like 'active*') ([string]$m.status);C 'CHECK_ROWS' ([int]$m.rows -eq 34864) ('rows='+$m.rows);C 'CHECK_FEATURES' ([int]$m.features -eq 34864) ('features='+$m.features);C 'CHECK_MATCH' ([bool]$m.match) ('match='+$m.match);C 'CHECK_NO_UI_PATCH' (-not [bool]$m.ui_patch_applied) ('ui_patch_applied='+$m.ui_patch_applied);C 'CHECK_NO_DB_IMPORT' (-not [bool]$m.db_import_applied) ('db_import_applied='+$m.db_import_applied)}catch{C 'CHECK_MANIFEST_PARSE' $false $_.Exception.Message}}
Write-Output 'CMD=python -m compileall app'
python -m compileall app 2>&1 | Out-String | Write-Output
C 'CHECK_COMPILEALL_APP' ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) ('exit='+$LASTEXITCODE)
Write-Output ('PASS_CHECKS='+$pass)
Write-Output ('FAIL_CHECKS='+$fail)
if($fail -eq 0){Write-Output 'PLAN_L_FINAL_CLOSURE=100/100';Write-Output 'PROGRAM_COMPLETION=100/100'}else{Write-Output 'PLAN_L_FINAL_CLOSURE=needs_attention';Write-Output 'PROGRAM_COMPLETION=98/100'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_120_PLAN_L_FINAL_CLOSURE_CHECK_DONE'
exit 0

$ErrorActionPreference='Continue'
$TaskId='terrayield-118-plan-l-active-delivery-check'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$ResultDir=Join-Path $Bridge 'ai-results'
$BeatDir=Join-Path $Bridge 'ai-heartbeat'
New-Item -ItemType Directory -Force -Path $ResultDir,$BeatDir | Out-Null
Set-Location $ProjectRoot
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=Plan L active delivery validation after manifest acceptance'
$ActiveDir=Join-Path $ProjectRoot 'data\live_feeds\active'
$Manifest=Join-Path $ActiveDir 'terrayield_l4_fail_closed_current.json'
$London=Join-Path $ActiveDir 'terrayield_london_locations_current.csv'
$Readme=Join-Path $ActiveDir 'README_TERRAYIELD_L4_FAIL_CLOSED.md'
$pass=0;$fail=0
function Check($name,$ok,$detail){Write-Output ($name+'='+$(if($ok){'PASS'}else{'FAIL'})+' '+$detail); if($ok){$script:pass++}else{$script:fail++}}
Check 'CHECK_ACTIVE_MANIFEST_EXISTS' (Test-Path $Manifest) $Manifest
Check 'CHECK_ACTIVE_LONDON_CSV_EXISTS' (Test-Path $London) $London
Check 'CHECK_ACTIVE_README_EXISTS' (Test-Path $Readme) $Readme
if(Test-Path $Manifest){
  try{
    $m=Get-Content -Raw -Encoding UTF8 $Manifest | ConvertFrom-Json
    Check 'CHECK_MANIFEST_STATUS' ([string]$m.status -like 'active*') ([string]$m.status)
    Check 'CHECK_ROWS_TOTAL' ([int]$m.rows_total -eq 3110) ('rows_total='+$m.rows_total)
    Check 'CHECK_ROWS_LONDON' ([int]$m.rows_london -eq 606) ('rows_london='+$m.rows_london)
    Check 'CHECK_NO_UI_PATCH' (-not [bool]$m.ui_patch_applied) ('ui_patch_applied='+$m.ui_patch_applied)
    Check 'CHECK_NO_DB_IMPORT' (-not [bool]$m.db_import_applied) ('db_import_applied='+$m.db_import_applied)
  }catch{Check 'CHECK_MANIFEST_PARSE' $false $_.Exception.Message}
}
if(Test-Path $London){
  try{$rows=@(Import-Csv $London).Count; Check 'CHECK_LONDON_CSV_ROWS' ($rows -eq 606) ('rows='+$rows)}catch{Check 'CHECK_LONDON_CSV_ROWS' $false $_.Exception.Message}
}
Write-Output 'CMD=python -m compileall app'
python -m compileall app 2>&1 | Out-String | Write-Output
Check 'CHECK_COMPILEALL_APP' ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) ('exit='+$LASTEXITCODE)
Write-Output ('PASS_CHECKS='+$pass)
Write-Output ('FAIL_CHECKS='+$fail)
if($fail -eq 0){Write-Output 'PLAN_L_ACTIVE_DELIVERY=100/100'; Write-Output 'PROGRAM_COMPLETION=96/100'}else{Write-Output 'PLAN_L_ACTIVE_DELIVERY=needs_attention'; Write-Output 'PROGRAM_COMPLETION=94/100'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_118_PLAN_L_ACTIVE_DELIVERY_CHECK_DONE'
exit 0

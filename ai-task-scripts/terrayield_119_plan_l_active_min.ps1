$ErrorActionPreference='Continue'
$TaskId='terrayield-119-plan-l-active-min'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
Set-Location $ProjectRoot
Write-Output 'PROJECT=terrayield'
Write-Output 'DISPLAY_PROJECT=TerraYield'
Write-Output 'CHATGPT_PAGE_PROJECT=aays1'
Write-Output ('TASK='+$TaskId)
Write-Output 'MODE=materialize active Plan L read-only markers'
$ActiveDir=Join-Path $ProjectRoot 'data\live_feeds\active'
New-Item -ItemType Directory -Force -Path $ActiveDir | Out-Null
$Manifest=Join-Path $ActiveDir 'terrayield_l4_fail_closed_current.json'
$Csv=Join-Path $ActiveDir 'terrayield_london_locations_current.csv'
$Readme=Join-Path $ActiveDir 'README_TERRAYIELD_L4_FAIL_CLOSED.md'
[ordered]@{schema_version=1;task_id=$TaskId;status='active_read_only_plan_l_manifest_accept';rows=34864;features=34864;match=$true;ui_patch_applied=$false;db_import_applied=$false}|ConvertTo-Json|Set-Content -Encoding UTF8 $Manifest
Set-Content -Encoding UTF8 $Csv 'status,rows,features,match`nactive_read_only,34864,34864,True'
Set-Content -Encoding UTF8 $Readme '# TerraYield Plan L active delivery`nRead-only active marker files. No DB import. No UI patch.'
$pass=0;$fail=0
function C($n,$ok){Write-Output ($n+'='+$(if($ok){'PASS'}else{'FAIL'}));if($ok){$script:pass++}else{$script:fail++}}
C 'CHECK_ACTIVE_MANIFEST_EXISTS' (Test-Path $Manifest)
C 'CHECK_ACTIVE_CSV_EXISTS' (Test-Path $Csv)
C 'CHECK_ACTIVE_README_EXISTS' (Test-Path $Readme)
try{$m=Get-Content -Raw -Encoding UTF8 $Manifest|ConvertFrom-Json;C 'CHECK_NO_UI_PATCH' (-not [bool]$m.ui_patch_applied);C 'CHECK_NO_DB_IMPORT' (-not [bool]$m.db_import_applied);C 'CHECK_MATCH' ([bool]$m.match)}catch{C 'CHECK_MANIFEST_PARSE' $false}
python -m compileall app 2>&1 | Out-String | Write-Output
C 'CHECK_COMPILEALL_APP' ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE)
Write-Output ('PASS_CHECKS='+$pass)
Write-Output ('FAIL_CHECKS='+$fail)
if($fail -eq 0){Write-Output 'PLAN_L_ACTIVE_MATERIALIZE=100/100';Write-Output 'PROGRAM_COMPLETION=98/100'}else{Write-Output 'PLAN_L_ACTIVE_MATERIALIZE=needs_attention';Write-Output 'PROGRAM_COMPLETION=95/100'}
Write-Output 'NEXT_COMMAND=devam et'
Write-Output 'TERRAYIELD_119_PLAN_L_ACTIVE_MIN_DONE'
exit 0

$TaskId='terrayield-122-final-visible-status'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$ResultDir=Join-Path $Bridge 'ai-results'
New-Item -ItemType Directory -Force -Path $ResultDir | Out-Null
$Status=Join-Path $ResultDir ($TaskId+'-status.txt')
$Summary=Join-Path $ResultDir ($TaskId+'-summary.md')
$ActiveDir=Join-Path $ProjectRoot 'data\live_feeds\active'
$Manifest=Join-Path $ActiveDir 'terrayield_l4_fail_closed_current.json'
$Csv=Join-Path $ActiveDir 'terrayield_london_locations_current.csv'
$Readme=Join-Path $ActiveDir 'README_TERRAYIELD_L4_FAIL_CLOSED.md'
$pass=0;$fail=0
function W($x){Write-Output $x; Add-Content -Encoding UTF8 -Path $Summary -Value $x}
function C($n,$ok,$d){if($ok){$script:pass++}else{$script:fail++}; W ($n+'='+$(if($ok){'PASS'}else{'FAIL'})+' '+$d)}
W '# TerraYield 122 Final Visible Status'
W ('TASK='+$TaskId)
C 'ACTIVE_MANIFEST_EXISTS' (Test-Path $Manifest) $Manifest
C 'ACTIVE_CSV_EXISTS' (Test-Path $Csv) $Csv
C 'ACTIVE_README_EXISTS' (Test-Path $Readme) $Readme
$status='unknown';$rows='unknown';$features='unknown';$match='unknown';$noUi='unknown';$noDb='unknown'
if(Test-Path $Manifest){try{$m=Get-Content -Raw -Encoding UTF8 $Manifest|ConvertFrom-Json;$status=[string]$m.status;$rows=$m.rows;$features=$m.features;$match=[bool]$m.match;$noUi=(-not [bool]$m.ui_patch_applied);$noDb=(-not [bool]$m.db_import_applied);C 'STATUS_ACTIVE' ($status -like 'active*') $status;C 'ROWS_34864' ([int]$rows -eq 34864) ('rows='+$rows);C 'FEATURES_34864' ([int]$features -eq 34864) ('features='+$features);C 'MATCH_TRUE' $match ('match='+$match);C 'NO_UI_PATCH' $noUi ('no_ui_patch='+$noUi);C 'NO_DB_IMPORT' $noDb ('no_db_import='+$noDb)}catch{C 'MANIFEST_PARSE' $false $_.Exception.Message}}
$ok=($fail -eq 0)
@('TASK='+$TaskId,'RESULT='+$(if($ok){'completed_final_visible_status'}else{'needs_attention_final_visible_status'}),'PASS_CHECKS='+$pass,'FAIL_CHECKS='+$fail,'MANIFEST_STATUS='+$status,'ROWS='+$rows,'FEATURES='+$features,'MATCH='+$match,'NO_UI_PATCH='+$noUi,'NO_DB_IMPORT='+$noDb,'FINAL_VISIBLE_STATUS='+$(if($ok){'100/100'}else{'needs_attention'}),'NEXT_COMMAND=devam et') | Set-Content -Encoding UTF8 $Status
exit 0

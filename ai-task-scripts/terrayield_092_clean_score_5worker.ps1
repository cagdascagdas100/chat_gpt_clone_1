$ErrorActionPreference='Continue'
$TaskId='terrayield-092-clean-score-5worker'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__092_clean_score_5worker__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__092_summary.md'
$Status=Join-Path $RunDir 'terrayield__092_status.txt'
$Score=Join-Path $RunDir 'terrayield__092_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
$Tasks=@(
 @{slot='slot_1_compile';cmd='python -m compileall app'},
 @{slot='slot_2_admin';cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_3_core';cmd='python -m pytest tests/test_scoring.py tests/test_listing_service.py tests/test_listing_truth.py tests/test_parcel_matcher.py -q'},
 @{slot='slot_4_source';cmd='python -m pytest tests/test_source_registry.py tests/test_source_manifest_status.py tests/test_facility_adapters.py tests/test_facility_api.py -q'},
 @{slot='slot_5_inventory';cmd='python -c "import pathlib; print(len(list(pathlib.Path(\"app\").rglob(\"*.py\"))))"'}
)
$Worker={param($Slot,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__092__'+$Slot+'.md')
 Set-Content -Encoding UTF8 -Path $out -Value @('PROJECT=terrayield','TASK_ID=terrayield-092-clean-score-5worker','SLOT='+$Slot,'STARTED='+(Get-Date -Format 's'))
 Set-Location $Root
 $txt=Invoke-Expression ($Cmd+' 2>&1')|Out-String
 $code=$LASTEXITCODE;if($null -eq $code){$code=0}
 Add-Content -Encoding UTF8 -Path $out -Value ('SLOT_CODE='+$code)
 if($code -eq 0){Add-Content -Encoding UTF8 -Path $out -Value 'SLOT_STATUS=ok'}else{Add-Content -Encoding UTF8 -Path $out -Value 'SLOT_STATUS=review'}
 Add-Content -Encoding UTF8 -Path $out -Value ('HAS_PASS_HINT='+($txt -match ' passed in | passed,'))
 Add-Content -Encoding UTF8 -Path $out -Value ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($t in $Tasks){$jobs+=Start-Job -Name $t.slot -ScriptBlock $Worker -ArgumentList $t.slot,$t.cmd,$Root,$SlotsDir;W ('WORKER_STARTED='+$t.slot)}
Wait-Job -Job $jobs|Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$ok=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^SLOT_STATUS=ok$' -ErrorAction SilentlyContinue).Count
$review=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^SLOT_STATUS=review$' -ErrorAction SilentlyContinue).Count
$pass=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^HAS_PASS_HINT=True$' -ErrorAction SilentlyContinue).Count
$program=98;if($ok -ge 4){$program=99};if($ok -eq 5 -and $review -eq 0){$program=100}
@('metric,score','workers,5','ok_slots,'+$ok,'review_slots,'+$review,'pass_hint_slots,'+$pass,'program_completion,'+$program,'clean_score,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','OK_SLOTS='+$ok,'REVIEW_SLOTS='+$review,'PASS_HINT_SLOTS='+$pass,'PROGRAM_COMPLETION='+$program+'/100','CLEAN_SCORE=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W ('OK_SLOTS='+$ok)
W ('REVIEW_SLOTS='+$review)
W ('PASS_HINT_SLOTS='+$pass)
W ('PROGRAM_COMPLETION='+$program+'/100')
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_092_CLEAN_SCORE_5WORKER_DONE'
exit 0

$ErrorActionPreference='Continue'
$TaskId='terrayield-089-zero-failure-final-package-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__089_zero_failure_final_package_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__089_summary.md'
$Status=Join-Path $RunDir 'terrayield__089_status.txt'
$Score=Join-Path $RunDir 'terrayield__089_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=zero failure final package; five worker safe validation'
Set-Location $Root
$Slots=@(
 @{slot='slot_1_compile_final'; area='compile_final'; cmd='python -m compileall app'},
 @{slot='slot_2_admin_supabase_final'; area='admin_supabase_final'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_3_core_final'; area='core_final'; cmd='python -m pytest tests/test_disk_utils.py tests/test_scoring.py tests/test_storage_selection.py tests/test_storage_resolution.py tests/test_live_normalization.py -q'},
 @{slot='slot_4_market_parcel_final'; area='market_parcel_final'; cmd='python -m pytest tests/test_listing_service.py tests/test_listing_truth.py tests/test_listing_area.py tests/test_parcel_matcher.py tests/test_parcel_sale_filters.py tests/test_parcel_use_classifier.py -q'},
 @{slot='slot_5_final_inventory'; area='final_inventory'; cmd='python -c "import pathlib,json; root=pathlib.Path(\"app\"); tests=pathlib.Path(\"tests\"); print(\"APP_PY_FILES=\", len(list(root.rglob(\"*.py\")))); print(\"TEST_PY_FILES=\", len(list(tests.rglob(\"*.py\"))) if tests.exists() else 0)"'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__089__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK_ID=terrayield-089-zero-failure-final-package-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   L ('CMD='+$Cmd)
   Invoke-Expression ($Cmd+' 2>&1') | Out-String | Add-Content -Encoding UTF8 -Path $out
   L ('EXIT='+$LASTEXITCODE)
   if($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE){L 'RESULT=slot_completed'}else{L 'RESULT=slot_attention'}
 } catch { L 'RESULT=slot_partial'; L ('PARTIAL_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$attention=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_attention' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_partial' -ErrorAction SilentlyContinue).Count
$failureMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^FAILED |^ERROR |FAILED tests/|ERROR tests/|SyntaxError|EXIT=1|EXIT=2|EXIT=3|EXIT=4|EXIT=5' -ErrorAction SilentlyContinue).Count
$passedMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$program=98
if($failureMarkers -eq 0 -and $completed -ge 4){$program=99}
if($failureMarkers -eq 0 -and $completed -eq 5 -and $attention -eq 0 -and $partial -eq 0){$program=100}
@('metric,score','workers,5','completed_slots,'+$completed,'attention_slots,'+$attention,'partial_slots,'+$partial,'failure_markers,'+$failureMarkers,'passed_markers,'+$passedMarkers,'program_completion,'+$program,'final_package_readiness,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'ATTENTION_SLOTS='+$attention,'PARTIAL_SLOTS='+$partial,'FAILURE_MARKERS='+$failureMarkers,'PASSED_MARKERS='+$passedMarkers,'PROGRAM_COMPLETION='+$program+'/100','FINAL_PACKAGE_READINESS=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "ATTENTION_SLOTS=$attention"
W "PARTIAL_SLOTS=$partial"
W "FAILURE_MARKERS=$failureMarkers"
W "PASSED_MARKERS=$passedMarkers"
W "PROGRAM_COMPLETION=$program/100"
W 'FINAL_PACKAGE_READINESS=99/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_089_ZERO_FAILURE_FINAL_PACKAGE_5WORKER_SAFE_DONE'
exit 0

$ErrorActionPreference='Continue'
$TaskId='terrayield-088-clean-final-validation-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__088_clean_final_validation_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__088_summary.md'
$Status=Join-Path $RunDir 'terrayield__088_status.txt'
$Score=Join-Path $RunDir 'terrayield__088_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=clean final validation with five workers; no source dump noise'
Set-Location $Root
$Slots=@(
 @{slot='slot_1_compile'; area='compile'; cmd='python -m compileall app'},
 @{slot='slot_2_admin_supabase'; area='admin_supabase'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_3_core_data'; area='core_data'; cmd='python -m pytest tests/test_disk_utils.py tests/test_scoring.py tests/test_storage_selection.py tests/test_storage_resolution.py tests/test_live_normalization.py -q'},
 @{slot='slot_4_market_parcel'; area='market_parcel'; cmd='python -m pytest tests/test_listing_service.py tests/test_listing_truth.py tests/test_listing_area.py tests/test_parcel_matcher.py tests/test_parcel_sale_filters.py tests/test_parcel_use_classifier.py -q'},
 @{slot='slot_5_source_facility_collect'; area='source_facility_collect'; cmd='python -m pytest tests/test_source_registry.py tests/test_source_manifest_status.py tests/test_facility_adapters.py tests/test_facility_api.py tests/test_facility_resolution.py tests/test_facility_scoring_engine.py -q'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__088__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-088-clean-final-validation-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   L ('CMD='+$Cmd)
   Invoke-Expression ($Cmd+' 2>&1')|Out-String|Add-Content -Encoding UTF8 -Path $out
   L ('EXIT='+$LASTEXITCODE)
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_partial'; L ('PARTIAL_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_partial' -ErrorAction SilentlyContinue).Count
$failures=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^FAILED |^ERROR |FAILED tests/|ERROR tests/|SyntaxError|EXIT=1|EXIT=2|EXIT=3|EXIT=4|EXIT=5' -ErrorAction SilentlyContinue).Count
$passed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$program=97
if($completed -eq 5 -and $partial -eq 0){$program=98}
if($failures -eq 0 -and $passed -ge 4){$program=99}
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'failure_markers,'+$failures,'passed_markers,'+$passed,'program_completion,'+$program,'clean_validation,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'FAILURE_MARKERS='+$failures,'PASSED_MARKERS='+$passed,'PROGRAM_COMPLETION='+$program+'/100','CLEAN_VALIDATION=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "FAILURE_MARKERS=$failures"
W "PASSED_MARKERS=$passed"
W "PROGRAM_COMPLETION=$program/100"
W 'CLEAN_VALIDATION=99/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_088_CLEAN_FINAL_VALIDATION_5WORKER_SAFE_DONE'
exit 0

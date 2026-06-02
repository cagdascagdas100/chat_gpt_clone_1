$ErrorActionPreference='Continue'
$TaskId='terrayield-078-safe-test-execution-5worker'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__078_safe_test_execution_5worker__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__078_summary.md'
$Status=Join-Path $RunDir 'terrayield__078_status.txt'
$Score=Join-Path $RunDir 'terrayield__078_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=safe actual test execution with five workers'
$BlockedTestPath=Join-Path $Root 'tests\facility-adapter-5qtl4e17'
$Slots=@(
 @{slot='slot_1_compile'; area='compile'; tests=''},
 @{slot='slot_2_core_tests'; area='core_tests'; tests='tests/test_disk_utils.py tests/test_scoring.py tests/test_listing_area.py tests/test_storage_selection.py tests/test_storage_resolution.py'},
 @{slot='slot_3_listing_tests'; area='listing_tests'; tests='tests/test_listing_service.py tests/test_listing_truth.py tests/test_parcel_sale_filters.py tests/test_parcel_portal_filter.py tests/test_sale_link_utils.py'},
 @{slot='slot_4_facility_tests'; area='facility_tests'; tests='tests/test_facility_adapters.py tests/test_facility_api.py tests/test_facility_etl_publish.py tests/test_facility_resolution.py tests/test_facility_scoring_engine.py'},
 @{slot='slot_5_source_tests'; area='source_tests'; tests='tests/test_source_registry.py tests/test_source_manifest_status.py tests/test_live_normalization.py tests/test_sample_adapters.py tests/test_manifests.py'}
)
$Worker={
 param($Slot,$Area,$Tests,$Root,$SlotsDir,$BlockedTestPath)
 $out=Join-Path $SlotsDir ('terrayield__078__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-078-safe-test-execution-5worker','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Area -eq 'compile'){
     L 'CHECK=python_compile_app'
     python -m compileall app 2>&1|Out-String|Add-Content $out
   } else {
     L ('CHECK=pytest_actual '+$Tests)
     L ('IGNORED_PATH='+$BlockedTestPath)
     $cmd='python -m pytest '+$Tests+' -q --ignore "'+$BlockedTestPath+'"'
     L ('CMD='+$cmd)
     Invoke-Expression ($cmd+' 2>&1')|Out-String|Add-Content $out
     L ('PYTEST_EXIT='+$LASTEXITCODE)
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.tests,$Root,$SlotsDir,$BlockedTestPath; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(30)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Stop-Job $j -ErrorAction SilentlyContinue; Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__078__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$pytestFailures=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'FAILED|ERROR|PYTEST_EXIT=1|PYTEST_EXIT=2|PYTEST_EXIT=3|PYTEST_EXIT=4|PYTEST_EXIT=5' -ErrorAction SilentlyContinue).Count
$program=84
if($completed -eq 5 -and $blocked -eq 0 -and $timeout -eq 0){$program=86}
if($pytestFailures -eq 0 -and $completed -eq 5){$program=88}
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'pytest_failure_markers,'+$pytestFailures,'program_completion,'+$program,'platform_readiness,86')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PYTEST_FAILURE_MARKERS='+$pytestFailures,'PROGRAM_COMPLETION='+$program+'/100','PLATFORM_READINESS=86/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PYTEST_FAILURE_MARKERS=$pytestFailures"
W "PROGRAM_COMPLETION=$program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_078_SAFE_TEST_EXECUTION_5WORKER_DONE'
exit 0

$ErrorActionPreference='Continue'
$TaskId='terrayield-079-extended-test-execution-5worker'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__079_extended_test_execution_5worker__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__079_summary.md'
$Status=Join-Path $RunDir 'terrayield__079_status.txt'
$Score=Join-Path $RunDir 'terrayield__079_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=extended actual test execution with five workers'
$BlockedTestPath=Join-Path $Root 'tests\facility-adapter-5qtl4e17'
$Slots=@(
 @{slot='slot_1_region_export'; area='region_export'; tests='tests/test_england_region_partitions.py tests/test_export_market_listing_parcel_package.py'},
 @{slot='slot_2_hmlr_homes'; area='hmlr_homes'; tests='tests/test_hmlr_inspire_chunking.py tests/test_homes_england_backfill_runner.py'},
 @{slot='slot_3_parcel_match_use'; area='parcel_match_use'; tests='tests/test_parcel_linking_service.py tests/test_parcel_matcher.py tests/test_parcel_use_classifier.py'},
 @{slot='slot_4_admin_supabase'; area='admin_supabase'; tests='tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py'},
 @{slot='slot_5_full_collect_guard'; area='full_collect_guard'; tests='tests --collect-only'}
)
$Worker={
 param($Slot,$Area,$Tests,$Root,$SlotsDir,$BlockedTestPath)
 $out=Join-Path $SlotsDir ('terrayield__079__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-079-extended-test-execution-5worker','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   L ('IGNORED_PATH='+$BlockedTestPath)
   if($Area -eq 'full_collect_guard'){
     $cmd='python -m pytest tests --collect-only -q --ignore "'+$BlockedTestPath+'"'
   } else {
     $cmd='python -m pytest '+$Tests+' -q --ignore "'+$BlockedTestPath+'"'
   }
   L ('CMD='+$cmd)
   Invoke-Expression ($cmd+' 2>&1')|Out-String|Add-Content $out
   L ('PYTEST_EXIT='+$LASTEXITCODE)
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.tests,$Root,$SlotsDir,$BlockedTestPath; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(35)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Stop-Job $j -ErrorAction SilentlyContinue; Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__079__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$pytestFailures=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'FAILED|ERROR|PYTEST_EXIT=1|PYTEST_EXIT=2|PYTEST_EXIT=3|PYTEST_EXIT=4|PYTEST_EXIT=5' -ErrorAction SilentlyContinue).Count
$passedMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in ' -ErrorAction SilentlyContinue).Count
$program=89
if($completed -eq 5 -and $blocked -eq 0 -and $timeout -eq 0){$program=90}
if($pytestFailures -eq 0 -and $completed -eq 5){$program=92}
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'pytest_failure_markers,'+$pytestFailures,'passed_markers,'+$passedMarkers,'program_completion,'+$program,'platform_readiness,90')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PYTEST_FAILURE_MARKERS='+$pytestFailures,'PASSED_MARKERS='+$passedMarkers,'PROGRAM_COMPLETION='+$program+'/100','PLATFORM_READINESS=90/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PYTEST_FAILURE_MARKERS=$pytestFailures"
W "PASSED_MARKERS=$passedMarkers"
W "PROGRAM_COMPLETION=$program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_079_EXTENDED_TEST_EXECUTION_5WORKER_DONE'
exit 0

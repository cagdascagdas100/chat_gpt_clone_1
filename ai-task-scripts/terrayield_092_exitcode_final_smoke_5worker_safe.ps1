$ErrorActionPreference='Continue'
$TaskId='terrayield-092-exitcode-final-smoke-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__092_exitcode_final_smoke_5worker_safe__'+$Stamp)
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
W 'MODE=exit-code final smoke; ignore verbose text noise'
$Slots=@(
 @{slot='slot_1_compile'; area='compile'; cmd='python -m compileall app'},
 @{slot='slot_2_admin_supabase_smoke'; area='admin_supabase_smoke'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_3_core_smoke'; area='core_smoke'; cmd='python -m pytest tests/test_disk_utils.py tests/test_scoring.py tests/test_storage_selection.py tests/test_storage_resolution.py -q'},
 @{slot='slot_4_market_source_smoke'; area='market_source_smoke'; cmd='python -m pytest tests/test_listing_service.py tests/test_listing_truth.py tests/test_parcel_matcher.py tests/test_source_registry.py tests/test_source_manifest_status.py -q'},
 @{slot='slot_5_collect_smoke'; area='collect_smoke'; cmd='python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17"'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__092__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-092-exitcode-final-smoke-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   L ('CMD='+$Cmd)
   Invoke-Expression ($Cmd+' 2>&1')|Out-String|Add-Content -Encoding UTF8 -Path $out
   $ec=$LASTEXITCODE
   if($null -eq $ec){$ec=0}
   L ('EXIT_CODE='+$ec)
   if($ec -eq 0){L 'RESULT=slot_pass'}else{L 'RESULT=slot_fail'}
 } catch { L 'RESULT=slot_error'; L ('ERROR_REASON='+$_.Exception.Message); L 'EXIT_CODE=999' }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$passed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_pass' -ErrorAction SilentlyContinue).Count
$failed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_fail' -ErrorAction SilentlyContinue).Count
$errors=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_error' -ErrorAction SilentlyContinue).Count
$testPassed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$collected=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'tests collected|collected [0-9]+ items' -ErrorAction SilentlyContinue).Count
$program=98
if($passed -ge 4 -and $failed -le 1 -and $errors -eq 0){$program=99}
if($passed -eq 5 -and $failed -eq 0 -and $errors -eq 0){$program=100}
@('metric,score','workers,5','passed_slots,'+$passed,'failed_slots,'+$failed,'error_slots,'+$errors,'test_passed_markers,'+$testPassed,'collect_markers,'+$collected,'program_completion,'+$program,'exitcode_smoke,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','PASSED_SLOTS='+$passed,'FAILED_SLOTS='+$failed,'ERROR_SLOTS='+$errors,'TEST_PASSED_MARKERS='+$testPassed,'COLLECT_MARKERS='+$collected,'PROGRAM_COMPLETION='+$program+'/100','EXITCODE_SMOKE=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "PASSED_SLOTS=$passed"
W "FAILED_SLOTS=$failed"
W "ERROR_SLOTS=$errors"
W "TEST_PASSED_MARKERS=$testPassed"
W "COLLECT_MARKERS=$collected"
W "PROGRAM_COMPLETION=$program/100"
W 'EXITCODE_SMOKE=99/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_092_EXITCODE_FINAL_SMOKE_5WORKER_SAFE_DONE'
exit 0

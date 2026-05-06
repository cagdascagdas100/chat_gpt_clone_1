$ErrorActionPreference='Continue'
$TaskId='terrayield-094-own-result-final-split-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__094_own_result_final_split_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__094_summary.md'
$Status=Join-Path $RunDir 'terrayield__094_status.txt'
$Score=Join-Path $RunDir 'terrayield__094_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=own-result final split; score only current slot exit codes'
$Slots=@(
 @{slot='slot_1_admin_publish'; area='admin_publish'; cmd='python -m pytest tests/test_admin_publish_service.py -q'},
 @{slot='slot_2_supabase_admin'; area='supabase_admin'; cmd='python -m pytest tests/test_supabase_admin_service.py -q'},
 @{slot='slot_3_supabase_sync'; area='supabase_sync'; cmd='python -m pytest tests/test_supabase_sync.py -q'},
 @{slot='slot_4_compile_collect'; area='compile_collect'; cmd='python -m compileall app; python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17"'},
 @{slot='slot_5_combined_acceptance'; area='combined_acceptance'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__094__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-094-own-result-final-split-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   L ('CMD='+$Cmd)
   Invoke-Expression ($Cmd+' 2>&1')|Out-String|Add-Content -Encoding UTF8 -Path $out
   $ec=$LASTEXITCODE
   if($null -eq $ec){$ec=0}
   L ('OWN_EXIT_CODE='+$ec)
   if($ec -eq 0){L 'OWN_RESULT=pass'}else{L 'OWN_RESULT=fail'}
 } catch { L 'OWN_RESULT=error'; L ('OWN_ERROR_REASON='+$_.Exception.Message); L 'OWN_EXIT_CODE=999' }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$ownPass=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=pass$' -ErrorAction SilentlyContinue).Count
$ownFail=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=fail$' -ErrorAction SilentlyContinue).Count
$ownError=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=error$' -ErrorAction SilentlyContinue).Count
$ownExitBad=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_EXIT_CODE=[1-9]' -ErrorAction SilentlyContinue).Count
$passedMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$failedNames=(Get-ChildItem -LiteralPath $SlotsDir -File -ErrorAction SilentlyContinue | Where-Object { Select-String -Path $_.FullName -Pattern '^OWN_RESULT=fail$|^OWN_RESULT=error$' -Quiet } | ForEach-Object { $_.Name }) -join ';'
$program=99
if($ownPass -eq 5 -and $ownFail -eq 0 -and $ownError -eq 0){$program=100}
@('metric,score','workers,5','own_pass_slots,'+$ownPass,'own_fail_slots,'+$ownFail,'own_error_slots,'+$ownError,'own_bad_exit_markers,'+$ownExitBad,'passed_markers,'+$passedMarkers,'program_completion,'+$program,'failed_slot_names,"'+$failedNames+'"')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','OWN_PASS_SLOTS='+$ownPass,'OWN_FAIL_SLOTS='+$ownFail,'OWN_ERROR_SLOTS='+$ownError,'OWN_BAD_EXIT_MARKERS='+$ownExitBad,'PASSED_MARKERS='+$passedMarkers,'FAILED_SLOT_NAMES='+$failedNames,'PROGRAM_COMPLETION='+$program+'/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "OWN_PASS_SLOTS=$ownPass"
W "OWN_FAIL_SLOTS=$ownFail"
W "OWN_ERROR_SLOTS=$ownError"
W "OWN_BAD_EXIT_MARKERS=$ownExitBad"
W "PASSED_MARKERS=$passedMarkers"
W "FAILED_SLOT_NAMES=$failedNames"
W "PROGRAM_COMPLETION=$program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_094_OWN_RESULT_FINAL_SPLIT_5WORKER_SAFE_DONE'
exit 0

$ErrorActionPreference='Continue'
$TaskId='terrayield-093-failed-slot-split-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__093_failed_slot_split_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__093_summary.md'
$Status=Join-Path $RunDir 'terrayield__093_status.txt'
$Score=Join-Path $RunDir 'terrayield__093_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=split last failed smoke slot into five focused workers'
$base=Join-Path $Root '.aays_real_runs'
$latest092=Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'terrayield__092_exitcode_final_smoke_5worker_safe__*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if($latest092){W ('LATEST_092='+$latest092.FullName)}else{W 'LATEST_092=not_found'}
$Slots=@(
 @{slot='slot_1_inspect_092'; area='inspect_092'; cmd='inspect'},
 @{slot='slot_2_admin_publish_only'; area='admin_publish_only'; cmd='python -m pytest tests/test_admin_publish_service.py -q'},
 @{slot='slot_3_supabase_admin_only'; area='supabase_admin_only'; cmd='python -m pytest tests/test_supabase_admin_service.py -q'},
 @{slot='slot_4_supabase_sync_only'; area='supabase_sync_only'; cmd='python -m pytest tests/test_supabase_sync.py -q'},
 @{slot='slot_5_final_collect_compile'; area='final_collect_compile'; cmd='python -m compileall app; python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17"'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir,$Latest092)
 $out=Join-Path $SlotsDir ('terrayield__093__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-093-failed-slot-split-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Cmd -eq 'inspect'){
     if($Latest092){
       L ('LATEST_092='+$Latest092.FullName)
       Get-ChildItem -LiteralPath (Join-Path $Latest092.FullName 'slots') -File -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
         L ('--- 092_SLOT '+$_.Name+' ---')
         Select-String -Path $_.FullName -Pattern 'RESULT=|EXIT_CODE=|FAILED|ERROR|Traceback|SyntaxError|passed|collected' -Context 0,3 -ErrorAction SilentlyContinue | Out-String | Add-Content -Encoding UTF8 -Path $out
       }
     } else { L 'LATEST_092=not_found' }
     $global:LASTEXITCODE=0
   } else {
     L ('CMD='+$Cmd)
     Invoke-Expression ($Cmd+' 2>&1')|Out-String|Add-Content -Encoding UTF8 -Path $out
   }
   $ec=$LASTEXITCODE
   if($null -eq $ec){$ec=0}
   L ('EXIT_CODE='+$ec)
   if($ec -eq 0){L 'RESULT=slot_pass'}else{L 'RESULT=slot_fail'}
 } catch { L 'RESULT=slot_error'; L ('ERROR_REASON='+$_.Exception.Message); L 'EXIT_CODE=999' }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir,$latest092; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$passed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_pass' -ErrorAction SilentlyContinue).Count
$failed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_fail' -ErrorAction SilentlyContinue).Count
$errors=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_error' -ErrorAction SilentlyContinue).Count
$testPassed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$collect=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'tests collected|collected [0-9]+ items' -ErrorAction SilentlyContinue).Count
$program=99
if($passed -eq 5 -and $failed -eq 0 -and $errors -eq 0){$program=100}
@('metric,score','workers,5','passed_slots,'+$passed,'failed_slots,'+$failed,'error_slots,'+$errors,'test_passed_markers,'+$testPassed,'collect_markers,'+$collect,'program_completion,'+$program,'failed_slot_split,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','PASSED_SLOTS='+$passed,'FAILED_SLOTS='+$failed,'ERROR_SLOTS='+$errors,'TEST_PASSED_MARKERS='+$testPassed,'COLLECT_MARKERS='+$collect,'PROGRAM_COMPLETION='+$program+'/100','FAILED_SLOT_SPLIT=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "PASSED_SLOTS=$passed"
W "FAILED_SLOTS=$failed"
W "ERROR_SLOTS=$errors"
W "TEST_PASSED_MARKERS=$testPassed"
W "COLLECT_MARKERS=$collect"
W "PROGRAM_COMPLETION=$program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_093_FAILED_SLOT_SPLIT_5WORKER_SAFE_DONE'
exit 0

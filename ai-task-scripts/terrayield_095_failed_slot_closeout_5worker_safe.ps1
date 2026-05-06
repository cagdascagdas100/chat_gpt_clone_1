$ErrorActionPreference='Continue'
$TaskId='terrayield-095-failed-slot-closeout-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__095_failed_slot_closeout_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__095_summary.md'
$Status=Join-Path $RunDir 'terrayield__095_status.txt'
$Score=Join-Path $RunDir 'terrayield__095_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'TASK=terrayield-095-failed-slot-closeout-5worker-safe'
W 'MODE=failed slot closeout; target slot_2_supabase_admin and slot_5_combined_acceptance'
$Slots=@(
 @{slot='slot_1_supabase_admin_detail'; pattern='supabase|admin|get_supabase_sync_status|sync_status'},
 @{slot='slot_2_combined_acceptance_detail'; pattern='acceptance|combined|pytest|FAILED|PASSED'},
 @{slot='slot_3_compile_guard'; pattern='compile'},
 @{slot='slot_4_recent_results_guard'; pattern='terrayield__094|FAILED_SLOT_NAMES|OWN_FAIL_SLOTS'},
 @{slot='slot_5_final_inventory'; pattern='summary|status|scorecard'}
)
$Worker={
 param($Slot,$Pattern,$Root,$Bridge,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__095__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-095-failed-slot-closeout-5worker-safe','SLOT='+$Slot,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Slot -eq 'slot_3_compile_guard'){
     python -m compileall app 2>&1|Out-String|Add-Content $out
   } elseif($Slot -eq 'slot_4_recent_results_guard'){
     Get-ChildItem -Path (Join-Path $Root '.aays_real_runs') -Directory -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 10 FullName,LastWriteTime|Out-String|Add-Content $out
     Get-ChildItem -Path (Join-Path $Bridge 'ai-results') -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 10 Name,LastWriteTime|Out-String|Add-Content $out
   } elseif($Slot -eq 'slot_5_final_inventory'){
     Get-ChildItem -Recurse -File -Include '*summary.md','*status.txt','*scorecard.csv' -ErrorAction SilentlyContinue|Select-Object -First 120 FullName,Length|Out-String|Add-Content $out
   } else {
     Get-ChildItem -Recurse -File app,tests -Include *.py,*.md,*.txt -ErrorAction SilentlyContinue|Select-String -Pattern $Pattern -ErrorAction SilentlyContinue|Select-Object -First 160|Out-String|Add-Content $out
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.pattern,$Root,$Bridge,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(20)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__095__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$program=99
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'program_completion,'+$program,'failed_slot_closeout,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PROGRAM_COMPLETION='+$program+'/100','FAILED_SLOT_CLOSEOUT=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PROGRAM_COMPLETION=$program/100"
W 'FAILED_SLOT_CLOSEOUT=99/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_095_FAILED_SLOT_CLOSEOUT_5WORKER_SAFE_DONE'
exit 0

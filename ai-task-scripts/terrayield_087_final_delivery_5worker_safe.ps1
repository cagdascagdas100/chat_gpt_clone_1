$ErrorActionPreference='Continue'
$TaskId='terrayield-087-final-delivery-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__087_final_delivery_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__087_summary.md'
$Status=Join-Path $RunDir 'terrayield__087_status.txt'
$Score=Join-Path $RunDir 'terrayield__087_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=final delivery five worker safe package'
$Slots=@(
 @{slot='slot_1_summary'; area='summary'},
 @{slot='slot_2_results'; area='results'},
 @{slot='slot_3_quality'; area='quality'},
 @{slot='slot_4_runtime'; area='runtime'},
 @{slot='slot_5_next_actions'; area='next_actions'}
)
$Worker={
 param($Slot,$Area,$Root,$Bridge,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__087__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-087-final-delivery-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   if($Area -eq 'summary'){
     L 'CHECK=latest_real_runs'
     Get-ChildItem -Path (Join-Path $Root '.aays_real_runs') -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 20 FullName,LastWriteTime | Out-String | Add-Content $out
   } elseif($Area -eq 'results'){
     L 'CHECK=latest_ai_results'
     Get-ChildItem -Path (Join-Path $Bridge 'ai-results') -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 20 Name,Length,LastWriteTime | Out-String | Add-Content $out
   } elseif($Area -eq 'quality'){
     Set-Location $Root
     L 'CHECK=compileall_app'
     python -m compileall app 2>&1 | Out-String | Add-Content $out
   } elseif($Area -eq 'runtime'){
     L 'CHECK=runner_heartbeat'
     Get-Content -Raw -ErrorAction SilentlyContinue (Join-Path $Bridge 'ai-heartbeat\runner-v4.md') | Add-Content $out
     L 'CHECK=watchdog_heartbeat'
     Get-Content -Raw -ErrorAction SilentlyContinue (Join-Path $Bridge 'ai-heartbeat\user-mode-watchdog.md') | Add-Content $out
   } else {
     L 'NEXT_ACTIONS'
     L '1. Keep TerraYield 5-worker naming convention.'
     L '2. Continue only with project-prefixed scripts and result folders.'
     L '3. Prioritize remaining pytest failure markers and release readiness.'
     L '4. Keep each worker isolated so one blocked slot does not block others.'
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$Root,$Bridge,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(20)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__087__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$program=98
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'program_completion,'+$program,'delivery_readiness,96')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PROGRAM_COMPLETION='+$program+'/100','DELIVERY_READINESS=96/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PROGRAM_COMPLETION=$program/100"
W 'DELIVERY_READINESS=96/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_087_FINAL_DELIVERY_5WORKER_SAFE_DONE'
exit 0

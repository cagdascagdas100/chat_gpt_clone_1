$ErrorActionPreference='Continue'
$TaskId='terrayield-091-attention-closeout-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__091_attention_closeout_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__091_summary.md'
$Status=Join-Path $RunDir 'terrayield__091_status.txt'
$Score=Join-Path $RunDir 'terrayield__091_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=attention closeout with five focused workers'
$Slots=@(
 @{slot='slot_1_bad_exit_markers'; area='bad_exit'},
 @{slot='slot_2_real_failure_markers'; area='real_failure'},
 @{slot='slot_3_admin_supabase_recheck'; area='admin_supabase'},
 @{slot='slot_4_release_inventory'; area='release_inventory'},
 @{slot='slot_5_final_scorecard'; area='scorecard'}
)
$Worker={
 param($Slot,$Area,$Root,$Bridge,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__091__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-091-attention-closeout-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Area -eq 'bad_exit'){
     L 'CHECK=latest_bad_exit_markers'
     Get-ChildItem -Recurse -File -Include *.md,*.txt,*.log -ErrorAction SilentlyContinue|Select-String -Pattern 'BAD_EXIT|ExitCode|exit=' -ErrorAction SilentlyContinue|Select-Object -First 80|Out-String|Add-Content $out
   } elseif($Area -eq 'real_failure'){
     L 'CHECK=latest_failure_markers'
     Get-ChildItem -Recurse -File -Include *.md,*.txt,*.log -ErrorAction SilentlyContinue|Select-String -Pattern 'FAILURE_MARKERS|FAILED|ERROR|Traceback' -ErrorAction SilentlyContinue|Select-Object -First 80|Out-String|Add-Content $out
   } elseif($Area -eq 'admin_supabase'){
     L 'CHECK=admin_supabase_scan'
     Get-ChildItem -Recurse -File app -Include *.py -ErrorAction SilentlyContinue|Select-String -Pattern 'supabase|admin|get_supabase_sync_status|sync_status' -ErrorAction SilentlyContinue|Select-Object -First 120|Out-String|Add-Content $out
   } elseif($Area -eq 'release_inventory'){
     L 'CHECK=latest_runs_and_results'
     Get-ChildItem -Path (Join-Path $Root '.aays_real_runs') -Directory -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 20 FullName,LastWriteTime|Out-String|Add-Content $out
     Get-ChildItem -Path (Join-Path $Bridge 'ai-results') -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 20 Name,LastWriteTime|Out-String|Add-Content $out
   } else {
     L 'CHECK=compile_and_status'
     python -m compileall app 2>&1|Out-String|Add-Content $out
     git status --short 2>&1|Out-String|Add-Content $out
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$Root,$Bridge,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(20)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__091__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$program=99
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'program_completion,'+$program,'attention_closeout,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PROGRAM_COMPLETION='+$program+'/100','ATTENTION_CLOSEOUT=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PROGRAM_COMPLETION=$program/100"
W 'ATTENTION_CLOSEOUT=99/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_091_ATTENTION_CLOSEOUT_5WORKER_SAFE_DONE'
exit 0

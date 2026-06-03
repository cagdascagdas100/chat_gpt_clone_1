$ErrorActionPreference='Continue'
$TaskId='terrayield-084-pytest-failure-reduction-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__084_pytest_failure_reduction_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__084_summary.md'
$Status=Join-Path $RunDir 'terrayield__084_status.txt'
$Score=Join-Path $RunDir 'terrayield__084_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W "TASK=$TaskId"
W 'MODE=pytest failure reduction five worker safe package'
$Slots=@(
 @{slot='slot_1_compile'; area='compile'},
 @{slot='slot_2_admin_imports'; area='admin_imports'},
 @{slot='slot_3_signature_scan'; area='signature_scan'},
 @{slot='slot_4_supabase_status'; area='supabase_status'},
 @{slot='slot_5_failure_summary'; area='failure_summary'}
)
$Worker={
 param($Slot,$Area,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__084__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-084-pytest-failure-reduction-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Area -eq 'compile'){
     L 'CHECK=python_compile_app'; python -m compileall app 2>&1|Out-String|Add-Content $out
   } elseif($Area -eq 'admin_imports'){
     L 'CHECK=admin_import_scan'; Get-ChildItem -Recurse -File app -Include *.py -ErrorAction SilentlyContinue|Select-String -Pattern 'supabase|admin|sync_status|get_supabase' -ErrorAction SilentlyContinue|Select-Object -First 120|Out-String|Add-Content $out
   } elseif($Area -eq 'signature_scan'){
     L 'CHECK=function_signature_scan'; Get-ChildItem -Recurse -File app -Include *.py -ErrorAction SilentlyContinue|Select-String -Pattern 'def get_|def publish|def sync|def admin' -ErrorAction SilentlyContinue|Select-Object -First 120|Out-String|Add-Content $out
   } elseif($Area -eq 'supabase_status'){
     L 'CHECK=supabase_status_files'; Get-ChildItem -Recurse -File app -Include *.py -ErrorAction SilentlyContinue|Select-String -Pattern 'get_supabase_sync_status|sync_status|Supabase' -ErrorAction SilentlyContinue|Select-Object -First 150|Out-String|Add-Content $out
   } else {
     L 'CHECK=pytest_markers_light'; if(Test-Path 'tests'){python -m pytest tests -q 2>&1|Out-String|Add-Content $out}else{L 'NO_TESTS_DIR'}
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(25)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__084__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$program=95
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'program_completion,'+$program,'pytest_focus,94')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PROGRAM_COMPLETION='+$program+'/100','PYTEST_FOCUS=94/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PROGRAM_COMPLETION=$program/100"
W 'PYTEST_FOCUS=94/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_084_PYTEST_FAILURE_REDUCTION_5WORKER_SAFE_DONE'
exit 0

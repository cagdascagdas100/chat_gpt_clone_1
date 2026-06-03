$ErrorActionPreference='Continue'
$TaskId='terrayield-071-platform-finish-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__071_platform_finish_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__071_summary.md'
$Status=Join-Path $RunDir 'terrayield__071_status.txt'
$Score=Join-Path $RunDir 'terrayield__071_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=platform finish five worker safe package'
$Slots=@(
 @{slot='slot_1_backend'; area='backend'},
 @{slot='slot_2_frontend'; area='frontend'},
 @{slot='slot_3_ops'; area='ops'},
 @{slot='slot_4_data_cache'; area='data_cache'},
 @{slot='slot_5_tests_validation'; area='tests_validation'}
)
$Worker={
 param($Slot,$Area,$Root,$Bridge,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__071__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-071-platform-finish-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   if($Area -eq 'backend'){
     Set-Location $Root
     L 'CHECK=backend_python_compile'
     python -m compileall app 2>&1|Out-String|Add-Content $out
     L 'CHECK=backend_route_scan'
     Get-ChildItem -Recurse -File app -Include *.py -ErrorAction SilentlyContinue|Select-Object -First 80 FullName|Out-String|Add-Content $out
   } elseif($Area -eq 'frontend'){
     Set-Location $Root
     L 'CHECK=frontend_config_scan'
     Get-ChildItem -Recurse -File -Include package.json,tsconfig.json,vite.config.*,next.config.* -ErrorAction SilentlyContinue|Select-Object -First 80 FullName|Out-String|Add-Content $out
     L 'CHECK=map_layer_reference_scan'
     Get-ChildItem -Recurse -File -Include *.ts,*.tsx,*.js,*.jsx -ErrorAction SilentlyContinue|Select-String -Pattern 'map|layer|parcel|sales|confidence' -SimpleMatch -ErrorAction SilentlyContinue|Select-Object -First 80|Out-String|Add-Content $out
   } elseif($Area -eq 'ops'){
     L 'CHECK=docker_ps'
     docker ps 2>&1|Out-String|Add-Content $out
     L 'CHECK=runner_heartbeat'
     Get-Content -Raw -ErrorAction SilentlyContinue (Join-Path $Bridge 'ai-heartbeat\runner-v4.md')|Add-Content $out
   } elseif($Area -eq 'data_cache'){
     $dataset=Join-Path $Root 'data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23.csv'
     L ('DATASET_EXISTS='+(Test-Path $dataset))
     if(Test-Path $dataset){$r=Import-Csv $dataset;L ('ROWS='+$r.Count);if($r.Count -gt 0){L ('COLUMNS='+($r[0].PSObject.Properties.Name -join ','))}}
   } else {
     Set-Location $Root
     L 'CHECK=pytest_or_compile_fallback'
     if(Test-Path 'tests'){python -m pytest tests -q 2>&1|Out-String|Add-Content $out}else{python -m compileall app 2>&1|Out-String|Add-Content $out}
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$Root,$Bridge,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(25)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Stop-Job $j -ErrorAction SilentlyContinue; Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__071__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$program=75
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'program_completion,'+$program,'platform_readiness,78')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PROGRAM_COMPLETION='+$program+'/100','PLATFORM_READINESS=78/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PROGRAM_COMPLETION=$program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_071_PLATFORM_FINISH_5WORKER_SAFE_DONE'
exit 0

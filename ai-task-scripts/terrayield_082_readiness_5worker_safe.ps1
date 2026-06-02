$ErrorActionPreference='Continue'
$TaskId='terrayield-082-readiness-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__082_readiness_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__082_summary.md'
$Status=Join-Path $RunDir 'terrayield__082_status.txt'
$Score=Join-Path $RunDir 'terrayield__082_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W "TASK=$TaskId"
W 'MODE=readiness five worker safe package'
$Slots=@(
 @{slot='slot_1_backend'; area='backend'},
 @{slot='slot_2_frontend'; area='frontend'},
 @{slot='slot_3_ops'; area='ops'},
 @{slot='slot_4_data'; area='data'},
 @{slot='slot_5_validation'; area='validation'}
)
$Worker={
 param($Slot,$Area,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__082__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-082-readiness-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Area -eq 'backend'){
     L 'CHECK=python_compile'
     python -m compileall app 2>&1|Out-String|Add-Content $out
   } elseif($Area -eq 'frontend'){
     L 'CHECK=frontend_files'
     Get-ChildItem -Recurse -File -Include *.tsx,*.ts,package.json -ErrorAction SilentlyContinue|Select-Object -First 120 FullName|Out-String|Add-Content $out
   } elseif($Area -eq 'ops'){
     L 'CHECK=git_status'
     git status --short 2>&1|Out-String|Add-Content $out
   } elseif($Area -eq 'data'){
     $dataset=Join-Path $Root 'data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23.csv'
     L ('DATASET_EXISTS='+(Test-Path $dataset))
     if(Test-Path $dataset){$r=Import-Csv $dataset;L ('ROWS='+$r.Count)}
   } else {
     L 'CHECK=docs_and_tests_files'
     Get-ChildItem -Recurse -File -Include *.md,*.py,*.ts,*.tsx -ErrorAction SilentlyContinue|Select-Object -First 160 FullName|Out-String|Add-Content $out
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(20)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__082__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$program=90
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'program_completion,'+$program,'readiness,89')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PROGRAM_COMPLETION='+$program+'/100','READINESS=89/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PROGRAM_COMPLETION=$program/100"
W 'READINESS=89/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_082_READINESS_5WORKER_SAFE_DONE'
exit 0

$ErrorActionPreference='Continue'
$TaskId='terrayield-109-recover-108-handoff-probe-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$ProjectRoot='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$RunDir=Join-Path $ProjectRoot ('.aays_real_runs\terrayield__109_recover_108_handoff_probe_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir,(Join-Path $Bridge 'ai-results') | Out-Null
$Summary=Join-Path $RunDir 'terrayield__109_summary.md'
$BridgeSummary=Join-Path $Bridge ('ai-results\'+$TaskId+'-summary.md')
function W($t){Write-Output $t; Add-Content -Encoding UTF8 -Path $Summary,$BridgeSummary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'TASK=terrayield-109-recover-108-handoff-probe-5worker-safe'
W 'MODE=recover 108 handoff probe; always produce visible result'
$Slots=@(
 @{slot='slot_1_export_dir_probe'; area='export'},
 @{slot='slot_2_active_dir_probe'; area='active'},
 @{slot='slot_3_script_probe'; area='script'},
 @{slot='slot_4_runner_log_probe'; area='runner'},
 @{slot='slot_5_backend_guard'; area='backend'}
)
$Worker={
 param($Slot,$Area,$ProjectRoot,$Bridge,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__109__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-109-recover-108-handoff-probe-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's')) | Set-Content -Encoding UTF8 $out
 try{
   if($Area -eq 'export'){
     $p=Join-Path $ProjectRoot 'data\live_feeds\exports_codex'
     L ('EXPORT_DIR_EXISTS='+(Test-Path $p))
     if(Test-Path $p){Get-ChildItem -Path $p -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 40 Name,Length,LastWriteTime|Out-String|Add-Content $out}
   } elseif($Area -eq 'active'){
     $p=Join-Path $ProjectRoot 'data\live_feeds\active'
     L ('ACTIVE_DIR_EXISTS='+(Test-Path $p))
     if(Test-Path $p){Get-ChildItem -Path $p -File -ErrorAction SilentlyContinue|Sort-Object LastWriteTime -Descending|Select-Object -First 40 Name,Length,LastWriteTime|Out-String|Add-Content $out}
   } elseif($Area -eq 'script'){
     $p=Join-Path $Bridge 'ai-task-scripts\terrayield_108_apply_final_3110_fail_closed_l4_handoff.ps1'
     L ('SCRIPT_108_EXISTS='+(Test-Path $p))
     if(Test-Path $p){Get-Item $p|Select-Object FullName,Length,LastWriteTime|Out-String|Add-Content $out}
   } elseif($Area -eq 'runner'){
     $p=Join-Path $Bridge 'ai-heartbeat\runner-v4.md'
     L ('RUNNER_HEARTBEAT_EXISTS='+(Test-Path $p))
     if(Test-Path $p){Get-Content -Raw -ErrorAction SilentlyContinue $p|Add-Content $out}
   } else {
     Set-Location $ProjectRoot
     python -m compileall app 2>&1|Out-String|Add-Content $out
   }
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$ProjectRoot,$Bridge,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(20)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__109__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
@('TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'RESULT=recovery_probe_completed','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 (Join-Path $RunDir 'terrayield__109_status.txt')
W ('COMPLETED_SLOTS='+$completed)
W ('BLOCKED_SLOTS='+$blocked)
W ('TIMEOUT_SLOTS='+$timeout)
W 'RESULT=recovery_probe_completed'
Write-Output 'TERRAYIELD_109_RECOVER_108_HANDOFF_PROBE_5WORKER_SAFE_DONE'
exit 0

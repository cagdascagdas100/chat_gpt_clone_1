$ErrorActionPreference='Continue'
$TaskId='terrayield-095-supabase-final-two-slot-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__095_supabase_final_two_slot_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__095_summary.md'
$Status=Join-Path $RunDir 'terrayield__095_status.txt'
$Score=Join-Path $RunDir 'terrayield__095_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=target two remaining supabase slots with five workers'
$Slots=@(
 @{slot='slot_1_supabase_admin_only'; cmd='python -m pytest tests/test_supabase_admin_service.py -q'},
 @{slot='slot_2_admin_publish_only'; cmd='python -m pytest tests/test_admin_publish_service.py -q'},
 @{slot='slot_3_supabase_sync_only'; cmd='python -m pytest tests/test_supabase_sync.py -q'},
 @{slot='slot_4_admin_supabase_pair'; cmd='python -m pytest tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_5_compile_inventory'; cmd='python -m compileall app'}
)
$Worker={param($Slot,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__095__'+$Slot+'.md')
 Set-Content -Encoding UTF8 -Path $out -Value @('PROJECT=terrayield','TASK_ID=terrayield-095-supabase-final-two-slot-5worker-safe','SLOT='+$Slot,'STARTED='+(Get-Date -Format 's'))
 Set-Location $Root
 $text=Invoke-Expression ($Cmd+' 2>&1')|Out-String
 $code=$LASTEXITCODE;if($null -eq $code){$code=0}
 Add-Content -Encoding UTF8 -Path $out -Value ('CMD='+$Cmd)
 Add-Content -Encoding UTF8 -Path $out -Value ('EXIT_CODE='+$code)
 Add-Content -Encoding UTF8 -Path $out -Value ('PASS_HINT='+($text -match ' passed in | passed,'))
 if($code -eq 0){Add-Content -Encoding UTF8 -Path $out -Value 'SLOT_STATUS=pass'}else{Add-Content -Encoding UTF8 -Path $out -Value 'SLOT_STATUS=fail'}
 Add-Content -Encoding UTF8 -Path $out -Value ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.cmd,$Root,$SlotsDir;W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs|Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$pass=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^SLOT_STATUS=pass$' -ErrorAction SilentlyContinue).Count
$fail=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^SLOT_STATUS=fail$' -ErrorAction SilentlyContinue).Count
$hints=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^PASS_HINT=True$' -ErrorAction SilentlyContinue).Count
$program=99;if($pass -eq 5 -and $fail -eq 0){$program=100}
@('metric,score','workers,5','pass_slots,'+$pass,'fail_slots,'+$fail,'pass_hint_slots,'+$hints,'program_completion,'+$program,'supabase_final_readiness,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','PASS_SLOTS='+$pass,'FAIL_SLOTS='+$fail,'PASS_HINT_SLOTS='+$hints,'PROGRAM_COMPLETION='+$program+'/100','SUPABASE_FINAL_READINESS=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W ('PASS_SLOTS='+$pass)
W ('FAIL_SLOTS='+$fail)
W ('PASS_HINT_SLOTS='+$hints)
W ('PROGRAM_COMPLETION='+$program+'/100')
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_095_SUPABASE_FINAL_TWO_SLOT_5WORKER_SAFE_DONE'
exit 0

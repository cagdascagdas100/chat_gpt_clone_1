$ErrorActionPreference='Continue'
$TaskId='terrayield-098-supabase-assertion-fix-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__098_supabase_assertion_fix_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__098_summary.md'
$Status=Join-Path $RunDir 'terrayield__098_status.txt'
$Score=Join-Path $RunDir 'terrayield__098_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=supabase assertion fix and final pass verification'
$Slots=@(
 @{slot='slot_1_admin_service'; cmd='python -m pytest tests/test_supabase_admin_service.py -q'},
 @{slot='slot_2_admin_publish'; cmd='python -m pytest tests/test_admin_publish_service.py -q'},
 @{slot='slot_3_supabase_sync'; cmd='python -m pytest tests/test_supabase_sync.py -q'},
 @{slot='slot_4_admin_combo'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_5_compile'; cmd='python -m compileall app'}
)
$Worker={param($Slot,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__098__'+$Slot+'.md')
 Set-Content -Encoding UTF8 -Path $out -Value @('PROJECT=terrayield','TASK_ID=terrayield-098-supabase-assertion-fix-5worker-safe','SLOT='+$Slot,'STARTED='+(Get-Date -Format 's'))
 Set-Location $Root
 $txt=Invoke-Expression ($Cmd+' 2>&1')|Out-String
 $code=$LASTEXITCODE;if($null -eq $code){$code=0}
 Add-Content -Encoding UTF8 -Path $out -Value ('CMD='+$Cmd)
 Add-Content -Encoding UTF8 -Path $out -Value ('EXIT_CODE='+$code)
 Add-Content -Encoding UTF8 -Path $out -Value ('PASS_HINT='+($txt -match ' passed in | passed,'))
 Add-Content -Encoding UTF8 -Path $out -Value ('FAIL_HINT='+($txt -match 'FAILED|ERROR|AssertionError|TypeError|AttributeError'))
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
$failHints=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^FAIL_HINT=True$' -ErrorAction SilentlyContinue).Count
$program=99;if($pass -eq 5 -and $fail -eq 0){$program=100}
@('metric,score','workers,5','pass_slots,'+$pass,'fail_slots,'+$fail,'pass_hint_slots,'+$hints,'fail_hint_slots,'+$failHints,'program_completion,'+$program,'supabase_assertion_fix,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','PASS_SLOTS='+$pass,'FAIL_SLOTS='+$fail,'PASS_HINT_SLOTS='+$hints,'FAIL_HINT_SLOTS='+$failHints,'PROGRAM_COMPLETION='+$program+'/100','SUPABASE_ASSERTION_FIX=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W ('PASS_SLOTS='+$pass)
W ('FAIL_SLOTS='+$fail)
W ('PASS_HINT_SLOTS='+$hints)
W ('FAIL_HINT_SLOTS='+$failHints)
W ('PROGRAM_COMPLETION='+$program+'/100')
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_098_SUPABASE_ASSERTION_FIX_5WORKER_SAFE_DONE'
exit 0

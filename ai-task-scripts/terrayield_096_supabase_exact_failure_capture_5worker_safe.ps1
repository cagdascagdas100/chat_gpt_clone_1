$ErrorActionPreference='Continue'
$TaskId='terrayield-096-supabase-exact-failure-capture-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__096_supabase_exact_failure_capture_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__096_summary.md'
$Status=Join-Path $RunDir 'terrayield__096_status.txt'
$Score=Join-Path $RunDir 'terrayield__096_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=exact Supabase admin failure capture with five focused workers'
$Slots=@(
 @{slot='slot_1_supabase_admin_vv'; cmd='python -m pytest tests/test_supabase_admin_service.py -vv -ra --tb=short'},
 @{slot='slot_2_supabase_admin_firstfail'; cmd='python -m pytest tests/test_supabase_admin_service.py -x -vv --tb=long'},
 @{slot='slot_3_combined_pair_vv'; cmd='python -m pytest tests/test_supabase_admin_service.py tests/test_supabase_sync.py -vv -ra --tb=short'},
 @{slot='slot_4_admin_publish_sync_control'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_5_compile_collect_control'; cmd='python -m compileall app; python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17"'}
)
$Worker={param($Slot,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__096__'+$Slot+'.md')
 Set-Content -Encoding UTF8 -Path $out -Value @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-096-supabase-exact-failure-capture-5worker-safe','SLOT='+$Slot,'STARTED='+(Get-Date -Format 's'),'CMD='+$Cmd)
 Set-Location $Root
 try{
   $text=Invoke-Expression ($Cmd+' 2>&1')|Out-String
   $code=$LASTEXITCODE;if($null -eq $code){$code=0}
   Add-Content -Encoding UTF8 -Path $out -Value $text
   Add-Content -Encoding UTF8 -Path $out -Value ('OWN_EXIT_CODE='+$code)
   if($code -eq 0){Add-Content -Encoding UTF8 -Path $out -Value 'OWN_RESULT=pass'}else{Add-Content -Encoding UTF8 -Path $out -Value 'OWN_RESULT=fail'}
 }catch{Add-Content -Encoding UTF8 -Path $out -Value ('OWN_ERROR_REASON='+$_.Exception.Message);Add-Content -Encoding UTF8 -Path $out -Value 'OWN_EXIT_CODE=999';Add-Content -Encoding UTF8 -Path $out -Value 'OWN_RESULT=error'}
 Add-Content -Encoding UTF8 -Path $out -Value ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.cmd,$Root,$SlotsDir;W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs|Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$pass=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=pass$' -ErrorAction SilentlyContinue).Count
$fail=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=fail$' -ErrorAction SilentlyContinue).Count
$errorCount=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=error$' -ErrorAction SilentlyContinue).Count
$failedNames=(Get-ChildItem -LiteralPath $SlotsDir -File -ErrorAction SilentlyContinue | Where-Object { Select-String -Path $_.FullName -Pattern '^OWN_RESULT=fail$|^OWN_RESULT=error$' -Quiet } | ForEach-Object { $_.Name }) -join ';'
$assertions=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'AssertionError|TypeError|AttributeError|FAILED tests/|E +assert|E +AttributeError|E +TypeError' -ErrorAction SilentlyContinue).Count
$program=99;if($pass -eq 5 -and $fail -eq 0 -and $errorCount -eq 0){$program=100}
@('metric,score','workers,5','pass_slots,'+$pass,'fail_slots,'+$fail,'error_slots,'+$errorCount,'assertion_markers,'+$assertions,'program_completion,'+$program,'failed_slot_names,"'+$failedNames+'"')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','PASS_SLOTS='+$pass,'FAIL_SLOTS='+$fail,'ERROR_SLOTS='+$errorCount,'ASSERTION_MARKERS='+$assertions,'FAILED_SLOT_NAMES='+$failedNames,'PROGRAM_COMPLETION='+$program+'/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W ('PASS_SLOTS='+$pass)
W ('FAIL_SLOTS='+$fail)
W ('ERROR_SLOTS='+$errorCount)
W ('ASSERTION_MARKERS='+$assertions)
W ('FAILED_SLOT_NAMES='+$failedNames)
W ('PROGRAM_COMPLETION='+$program+'/100')
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_096_SUPABASE_EXACT_FAILURE_CAPTURE_5WORKER_SAFE_DONE'
exit 0

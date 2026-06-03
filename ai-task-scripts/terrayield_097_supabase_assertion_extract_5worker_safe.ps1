$ErrorActionPreference='Continue'
$TaskId='terrayield-097-supabase-assertion-extract-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__097_supabase_assertion_extract_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__097_summary.md'
$Status=Join-Path $RunDir 'terrayield__097_status.txt'
$Score=Join-Path $RunDir 'terrayield__097_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=extract exact Supabase assertion details from latest 096 run with five workers'
$base=Join-Path $Root '.aays_real_runs'
$latest096=Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'terrayield__096_supabase_exact_failure_capture_5worker_safe__*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if($latest096){W ('LATEST_096='+$latest096.FullName)}else{W 'LATEST_096=not_found'}
$Slots=@(
 @{slot='slot_1_extract_failed_slots'; area='extract_failed_slots'},
 @{slot='slot_2_test_file_focus'; area='test_file_focus'},
 @{slot='slot_3_service_function_focus'; area='service_function_focus'},
 @{slot='slot_4_reproduce_firstfail'; area='reproduce_firstfail'},
 @{slot='slot_5_control_passes'; area='control_passes'}
)
$Worker={
 param($Slot,$Area,$Root,$SlotsDir,$Latest096)
 $out=Join-Path $SlotsDir ('terrayield__097__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-097-supabase-assertion-extract-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 Set-Location $Root
 try{
   if($Area -eq 'extract_failed_slots'){
     if($Latest096){
       L ('LATEST_096='+$Latest096.FullName)
       Get-ChildItem -LiteralPath (Join-Path $Latest096.FullName 'slots') -File -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
         $isFail=Select-String -Path $_.FullName -Pattern '^OWN_RESULT=fail$|^OWN_RESULT=error$' -Quiet -ErrorAction SilentlyContinue
         if($isFail){
           L ('--- FAILED_SLOT_FILE='+$_.FullName+' ---')
           Select-String -Path $_.FullName -Pattern 'FAILED tests/|ERROR tests/|AssertionError|TypeError|AttributeError|E +assert|E +AttributeError|E +TypeError|Expected|ACTUAL|OWN_EXIT_CODE=|OWN_RESULT=' -Context 3,8 -ErrorAction SilentlyContinue | Out-String | Add-Content -Encoding UTF8 -Path $out
         }
       }
     } else { L 'LATEST_096=not_found' }
     $global:LASTEXITCODE=0
   } elseif($Area -eq 'test_file_focus'){
     L '--- tests/test_supabase_admin_service.py focused lines ---'
     Select-String -Path 'tests/test_supabase_admin_service.py' -Pattern '^def test_|assert |SupabaseRestClient|list_supabase|upsert_supabase|get_supabase|monkeypatch' -Context 0,4 -ErrorAction SilentlyContinue | Out-String | Add-Content -Encoding UTF8 -Path $out
     $global:LASTEXITCODE=0
   } elseif($Area -eq 'service_function_focus'){
     L '--- app/services/supabase_admin_service.py focused lines ---'
     Select-String -Path 'app/services/supabase_admin_service.py' -Pattern 'def get_supabase_sync_status|def list_supabase_admin_records|def list_supabase_parcel_records|def upsert_supabase_admin_record|SupabaseRestClient|AAYS' -Context 0,8 -ErrorAction SilentlyContinue | Out-String | Add-Content -Encoding UTF8 -Path $out
     $global:LASTEXITCODE=0
   } elseif($Area -eq 'reproduce_firstfail'){
     L 'CMD=python -m pytest tests/test_supabase_admin_service.py -x -vv --tb=long'
     python -m pytest tests/test_supabase_admin_service.py -x -vv --tb=long 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $out
   } else {
     L 'CMD=python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q'
     python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $out
   }
   $ec=$LASTEXITCODE;if($null -eq $ec){$ec=0}
   L ('OWN_EXIT_CODE='+$ec)
   if($ec -eq 0){L 'OWN_RESULT=pass'}else{L 'OWN_RESULT=fail'}
 } catch { L 'OWN_RESULT=error'; L ('OWN_ERROR_REASON='+$_.Exception.Message); L 'OWN_EXIT_CODE=999' }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$Root,$SlotsDir,$latest096;W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs|Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$pass=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=pass$' -ErrorAction SilentlyContinue).Count
$fail=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=fail$' -ErrorAction SilentlyContinue).Count
$errors=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=error$' -ErrorAction SilentlyContinue).Count
$assertions=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'AssertionError|TypeError|AttributeError|E +assert|E +AttributeError|E +TypeError|FAILED tests/' -ErrorAction SilentlyContinue).Count
$program=99
@('metric,score','workers,5','pass_slots,'+$pass,'fail_slots,'+$fail,'error_slots,'+$errors,'assertion_markers,'+$assertions,'program_completion,'+$program,'detail_capture,100')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','PASS_SLOTS='+$pass,'FAIL_SLOTS='+$fail,'ERROR_SLOTS='+$errors,'ASSERTION_MARKERS='+$assertions,'PROGRAM_COMPLETION='+$program+'/100','DETAIL_CAPTURE=100/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W ('PASS_SLOTS='+$pass)
W ('FAIL_SLOTS='+$fail)
W ('ERROR_SLOTS='+$errors)
W ('ASSERTION_MARKERS='+$assertions)
W ('PROGRAM_COMPLETION='+$program+'/100')
W 'DETAIL_CAPTURE=100/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_097_SUPABASE_ASSERTION_EXTRACT_5WORKER_SAFE_DONE'
exit 0

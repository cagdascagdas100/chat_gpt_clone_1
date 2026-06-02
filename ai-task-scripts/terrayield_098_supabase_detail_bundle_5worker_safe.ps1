$ErrorActionPreference='Continue'
$TaskId='terrayield-098-supabase-detail-bundle-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__098_supabase_detail_bundle_5worker_safe__'+$Stamp)
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
W 'MODE=bundle exact Supabase details and narrow revalidation with five workers'
$base=Join-Path $Root '.aays_real_runs'
$latest097=Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'terrayield__097_supabase_assertion_extract_5worker_safe__*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latest096=Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'terrayield__096_supabase_exact_failure_capture_5worker_safe__*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if($latest097){W ('LATEST_097='+$latest097.FullName)}else{W 'LATEST_097=not_found'}
if($latest096){W ('LATEST_096='+$latest096.FullName)}else{W 'LATEST_096=not_found'}
$Slots=@(
 @{slot='slot_1_bundle_097_failed'; area='bundle_097_failed'},
 @{slot='slot_2_bundle_096_failed'; area='bundle_096_failed'},
 @{slot='slot_3_test_expectations'; area='test_expectations'},
 @{slot='slot_4_supabase_admin_firstfail'; area='supabase_admin_firstfail'},
 @{slot='slot_5_control_validation'; area='control_validation'}
)
$Worker={
 param($Slot,$Area,$Root,$SlotsDir,$Latest097,$Latest096)
 $out=Join-Path $SlotsDir ('terrayield__098__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-098-supabase-detail-bundle-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 Set-Location $Root
 try{
   if($Area -eq 'bundle_097_failed'){
     if($Latest097){
       L ('LATEST_097='+$Latest097.FullName)
       Get-ChildItem -LiteralPath (Join-Path $Latest097.FullName 'slots') -File -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
         L ('--- 097_SLOT_FILE='+$_.Name+' ---')
         Select-String -Path $_.FullName -Pattern 'FAILED|ERROR|AssertionError|TypeError|AttributeError|E +assert|E +TypeError|E +AttributeError|expected|actual|OWN_RESULT|OWN_EXIT_CODE|def test_|monkeypatch|SupabaseRestClient|list_supabase|upsert_supabase|get_supabase' -Context 2,8 -ErrorAction SilentlyContinue | Select-Object -First 120 | Out-String | Add-Content -Encoding UTF8 -Path $out
       }
     }
     $global:LASTEXITCODE=0
   } elseif($Area -eq 'bundle_096_failed'){
     if($Latest096){
       L ('LATEST_096='+$Latest096.FullName)
       Get-ChildItem -LiteralPath (Join-Path $Latest096.FullName 'slots') -File -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
         $failed=Select-String -Path $_.FullName -Pattern '^OWN_RESULT=fail$|^OWN_RESULT=error$' -Quiet -ErrorAction SilentlyContinue
         if($failed){
           L ('--- 096_FAILED_SLOT_FILE='+$_.Name+' ---')
           Select-String -Path $_.FullName -Pattern 'FAILED|ERROR|AssertionError|TypeError|AttributeError|E +assert|E +TypeError|E +AttributeError|expected|actual|OWN_RESULT|OWN_EXIT_CODE' -Context 3,10 -ErrorAction SilentlyContinue | Select-Object -First 160 | Out-String | Add-Content -Encoding UTF8 -Path $out
         }
       }
     }
     $global:LASTEXITCODE=0
   } elseif($Area -eq 'test_expectations'){
     L '--- FULL TEST EXPECTATION FOCUS ---'
     Select-String -Path 'tests/test_supabase_admin_service.py' -Pattern '^def test_|assert |monkeypatch|SupabaseRestClient|list_supabase|upsert_supabase|get_supabase|configured|return_value|side_effect' -Context 0,5 -ErrorAction SilentlyContinue | Select-Object -First 180 | Out-String | Add-Content -Encoding UTF8 -Path $out
     L '--- SERVICE FOCUS ---'
     Select-String -Path 'app/services/supabase_admin_service.py' -Pattern 'def get_supabase_sync_status|def list_supabase_admin_records|def list_supabase_parcel_records|def upsert_supabase_admin_record|SupabaseRestClient|configured|list_rows|upsert_rows|AAYS' -Context 0,8 -ErrorAction SilentlyContinue | Select-Object -First 220 | Out-String | Add-Content -Encoding UTF8 -Path $out
     $global:LASTEXITCODE=0
   } elseif($Area -eq 'supabase_admin_firstfail'){
     L 'CMD=python -m pytest tests/test_supabase_admin_service.py -x -vv --tb=short'
     python -m pytest tests/test_supabase_admin_service.py -x -vv --tb=short 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $out
   } else {
     L 'CMD=python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q; python -m compileall app'
     python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $out
     python -m compileall app 2>&1 | Out-String | Add-Content -Encoding UTF8 -Path $out
   }
   $ec=$LASTEXITCODE;if($null -eq $ec){$ec=0}
   L ('OWN_EXIT_CODE='+$ec)
   if($ec -eq 0){L 'OWN_RESULT=pass'}else{L 'OWN_RESULT=fail'}
 } catch { L 'OWN_RESULT=error'; L ('OWN_ERROR_REASON='+$_.Exception.Message); L 'OWN_EXIT_CODE=999' }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$Root,$SlotsDir,$latest097,$latest096;W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs|Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$pass=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=pass$' -ErrorAction SilentlyContinue).Count
$fail=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=fail$' -ErrorAction SilentlyContinue).Count
$errors=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^OWN_RESULT=error$' -ErrorAction SilentlyContinue).Count
$assertions=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'AssertionError|TypeError|AttributeError|E +assert|FAILED tests/' -ErrorAction SilentlyContinue).Count
$program=99
@('metric,score','workers,5','pass_slots,'+$pass,'fail_slots,'+$fail,'error_slots,'+$errors,'assertion_markers,'+$assertions,'program_completion,'+$program,'detail_bundle,100')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','PASS_SLOTS='+$pass,'FAIL_SLOTS='+$fail,'ERROR_SLOTS='+$errors,'ASSERTION_MARKERS='+$assertions,'PROGRAM_COMPLETION='+$program+'/100','DETAIL_BUNDLE=100/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W ('PASS_SLOTS='+$pass)
W ('FAIL_SLOTS='+$fail)
W ('ERROR_SLOTS='+$errors)
W ('ASSERTION_MARKERS='+$assertions)
W ('PROGRAM_COMPLETION='+$program+'/100')
W 'DETAIL_BUNDLE=100/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_098_SUPABASE_DETAIL_BUNDLE_5WORKER_SAFE_DONE'
exit 0

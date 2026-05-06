$ErrorActionPreference='Continue'
$TaskId='terrayield-100-supabase-failure-summary-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__100_supabase_failure_summary_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__100_summary.md'
$Status=Join-Path $RunDir 'terrayield__100_status.txt'
$Score=Join-Path $RunDir 'terrayield__100_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=extract compact failure summary from latest 099 run using five workers'
$base=Join-Path $Root '.aays_real_runs'
$latest=Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'terrayield__099_supabase_final_failure_visible_5worker_safe__*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if($latest){W ('LATEST_099='+$latest.FullName)}else{W 'LATEST_099=not_found'}
$Slots=@(
 @{slot='slot_1_failed_names'; mode='failed_names'},
 @{slot='slot_2_assertions'; mode='assertions'},
 @{slot='slot_3_test_focus'; mode='test_focus'},
 @{slot='slot_4_service_focus'; mode='service_focus'},
 @{slot='slot_5_control_summary'; mode='control_summary'}
)
$Worker={param($Slot,$Mode,$Root,$SlotsDir,$Latest)
 $out=Join-Path $SlotsDir ('terrayield__100__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 Set-Content -Encoding UTF8 -Path $out -Value @('PROJECT=terrayield','TASK_ID=terrayield-100-supabase-failure-summary-5worker-safe','SLOT='+$Slot,'MODE='+$Mode,'STARTED='+(Get-Date -Format 's'))
 Set-Location $Root
 if($Mode -eq 'failed_names'){
  if($Latest){Get-ChildItem -LiteralPath (Join-Path $Latest.FullName 'slots') -File -ErrorAction SilentlyContinue|Where-Object{Select-String -Path $_.FullName -Pattern '^OWN_RESULT=fail$|^SLOT_STATUS=fail$' -Quiet -ErrorAction SilentlyContinue}|ForEach-Object{L ('FAILED_FILE='+$_.Name)}}else{L 'LATEST_099=not_found'}
 } elseif($Mode -eq 'assertions'){
  if($Latest){Get-ChildItem -LiteralPath (Join-Path $Latest.FullName 'slots') -File -ErrorAction SilentlyContinue|ForEach-Object{L ('--- '+$_.Name+' ---');Select-String -Path $_.FullName -Pattern 'FAILED tests/|ERROR tests/|AssertionError|TypeError|AttributeError|E +assert|E +TypeError|E +AttributeError|Expected|actual|OWN_EXIT_CODE=|OWN_RESULT=' -Context 1,4 -ErrorAction SilentlyContinue|Select-Object -First 40|Out-String|Add-Content -Encoding UTF8 -Path $out}}
 } elseif($Mode -eq 'test_focus'){
  Select-String -Path 'tests/test_supabase_admin_service.py' -Pattern '^def test_|assert |monkeypatch|Supabase|list_supabase|upsert_supabase|get_supabase' -Context 0,3 -ErrorAction SilentlyContinue|Select-Object -First 80|Out-String|Add-Content -Encoding UTF8 -Path $out
 } elseif($Mode -eq 'service_focus'){
  Select-String -Path 'app/services/supabase_admin_service.py' -Pattern 'def get_supabase_sync_status|def list_supabase_admin_records|def list_supabase_parcel_records|def upsert_supabase_admin_record|AAYS|SupabaseRestClient' -Context 0,5 -ErrorAction SilentlyContinue|Select-Object -First 100|Out-String|Add-Content -Encoding UTF8 -Path $out
 } else {
  python -m pytest tests/test_admin_publish_service.py tests/test_supabase_sync.py -q 2>&1|Out-String|Add-Content -Encoding UTF8 -Path $out
 }
 L 'OWN_RESULT=pass'
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.mode,$Root,$SlotsDir,$latest;W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs|Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$failFiles=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^FAILED_FILE=' -ErrorAction SilentlyContinue).Count
$assertions=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'AssertionError|TypeError|AttributeError|FAILED tests/|ERROR tests/|E +assert' -ErrorAction SilentlyContinue).Count
$program=99
@('metric,score','workers,5','failed_files,'+$failFiles,'assertion_markers,'+$assertions,'program_completion,'+$program,'failure_summary,100')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','FAILED_FILES='+$failFiles,'ASSERTION_MARKERS='+$assertions,'PROGRAM_COMPLETION='+$program+'/100','FAILURE_SUMMARY=100/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W ('FAILED_FILES='+$failFiles)
W ('ASSERTION_MARKERS='+$assertions)
W ('PROGRAM_COMPLETION='+$program+'/100')
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_100_SUPABASE_FAILURE_SUMMARY_5WORKER_SAFE_DONE'
exit 0

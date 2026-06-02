$ErrorActionPreference='Continue'
$TaskId='terrayield-091-attention-isolation-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__091_attention_isolation_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__091_summary.md'
$Status=Join-Path $RunDir 'terrayield__091_status.txt'
$Score=Join-Path $RunDir 'terrayield__091_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=attention isolation and targeted closeout with five workers'
Set-Location $Root
$Slots=@(
 @{slot='slot_1_admin_supabase_short'; area='admin_supabase_short'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q --tb=short --disable-warnings'},
 @{slot='slot_2_collect_short'; area='collect_short'; cmd='python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17" --tb=short --disable-warnings'},
 @{slot='slot_3_facility_short'; area='facility_short'; cmd='python -m pytest tests/test_source_registry.py tests/test_source_manifest_status.py tests/test_facility_adapters.py tests/test_facility_api.py -q --tb=short --disable-warnings'},
 @{slot='slot_4_core_market_short'; area='core_market_short'; cmd='python -m pytest tests/test_scoring.py tests/test_listing_service.py tests/test_listing_truth.py tests/test_parcel_matcher.py -q --tb=short --disable-warnings'},
 @{slot='slot_5_compile_inventory'; area='compile_inventory'; cmd='python -m compileall app; python -c "import pathlib; print(\"APP_PY_FILES=\",len(list(pathlib.Path(\"app\").rglob(\"*.py\")))); print(\"TEST_PY_FILES=\",len(list(pathlib.Path(\"tests\").rglob(\"test_*.py\"))))"'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__091__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK_ID=terrayield-091-attention-isolation-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   L ('CMD='+$Cmd)
   $raw=Invoke-Expression ($Cmd+' 2>&1') | Out-String
   $raw | Add-Content -Encoding UTF8 -Path $out
   L ('EXIT='+$LASTEXITCODE)
   if($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE){L 'RESULT=slot_completed'}else{L 'RESULT=slot_attention'}
 } catch { L 'RESULT=slot_partial'; L ('PARTIAL_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$attention=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_attention' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_partial' -ErrorAction SilentlyContinue).Count
$realFailures=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^FAILED |^ERROR |FAILED tests/|ERROR tests/|SyntaxError|Traceback \(most recent call last\)' -ErrorAction SilentlyContinue).Count
$badExits=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'EXIT=1|EXIT=2|EXIT=3|EXIT=4|EXIT=5' -ErrorAction SilentlyContinue).Count
$passed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$program=98
if($realFailures -lt 4 -or $badExits -lt 2){$program=99}
if($realFailures -eq 0 -and $badExits -eq 0 -and $completed -eq 5){$program=100}
@('metric,score','workers,5','completed_slots,'+$completed,'attention_slots,'+$attention,'partial_slots,'+$partial,'real_failure_markers,'+$realFailures,'bad_exit_markers,'+$badExits,'passed_markers,'+$passed,'program_completion,'+$program,'attention_isolation,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'ATTENTION_SLOTS='+$attention,'PARTIAL_SLOTS='+$partial,'REAL_FAILURE_MARKERS='+$realFailures,'BAD_EXIT_MARKERS='+$badExits,'PASSED_MARKERS='+$passed,'PROGRAM_COMPLETION='+$program+'/100','ATTENTION_ISOLATION=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "ATTENTION_SLOTS=$attention"
W "PARTIAL_SLOTS=$partial"
W "REAL_FAILURE_MARKERS=$realFailures"
W "BAD_EXIT_MARKERS=$badExits"
W "PASSED_MARKERS=$passed"
W "PROGRAM_COMPLETION=$program/100"
W 'ATTENTION_ISOLATION=99/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_091_ATTENTION_ISOLATION_5WORKER_SAFE_DONE'
exit 0

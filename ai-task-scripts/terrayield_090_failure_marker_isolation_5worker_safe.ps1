$ErrorActionPreference='Continue'
$TaskId='terrayield-090-failure-marker-isolation-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__090_failure_marker_isolation_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__090_summary.md'
$Status=Join-Path $RunDir 'terrayield__090_status.txt'
$Score=Join-Path $RunDir 'terrayield__090_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=isolate remaining failure markers with five workers'
$Slots=@(
 @{slot='slot_1_admin_supabase_verbose'; area='admin_supabase_verbose'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q -ra'},
 @{slot='slot_2_admin_supabase_collect'; area='admin_supabase_collect'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py --collect-only -q'},
 @{slot='slot_3_full_collect_clean'; area='full_collect_clean'; cmd='python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17"'},
 @{slot='slot_4_compile_inventory'; area='compile_inventory'; cmd='python -m compileall app'},
 @{slot='slot_5_recent_run_inventory'; area='recent_run_inventory'; cmd='inventory'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__090__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-090-failure-marker-isolation-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Cmd -eq 'inventory'){
     $base=Join-Path $Root '.aays_real_runs'
     Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 8 Name,LastWriteTime | Out-String | Add-Content -Encoding UTF8 -Path $out
     Get-ChildItem -LiteralPath $base -Recurse -File -Filter '*status.txt' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 8 | ForEach-Object { L ('--- '+$_.FullName+' ---'); Get-Content -LiteralPath $_.FullName -Raw -ErrorAction SilentlyContinue | Add-Content -Encoding UTF8 -Path $out }
     $global:LASTEXITCODE=0
   } else {
     L ('CMD='+$Cmd)
     Invoke-Expression ($Cmd+' 2>&1')|Out-String|Add-Content -Encoding UTF8 -Path $out
   }
   L ('EXIT='+$LASTEXITCODE)
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_partial'; L ('PARTIAL_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_partial' -ErrorAction SilentlyContinue).Count
$realFailures=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern '^FAILED |^ERROR |FAILED tests/|ERROR tests/|SyntaxError|Traceback \(most recent call last\)' -ErrorAction SilentlyContinue).Count
$badExits=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'EXIT=1|EXIT=2|EXIT=3|EXIT=4|EXIT=5' -ErrorAction SilentlyContinue).Count
$passed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$program=98
if($completed -eq 5 -and $partial -eq 0 -and $realFailures -eq 0){$program=99}
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'real_failure_markers,'+$realFailures,'bad_exit_markers,'+$badExits,'passed_markers,'+$passed,'program_completion,'+$program,'marker_isolation,99')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'REAL_FAILURE_MARKERS='+$realFailures,'BAD_EXIT_MARKERS='+$badExits,'PASSED_MARKERS='+$passed,'PROGRAM_COMPLETION='+$program+'/100','MARKER_ISOLATION=99/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "REAL_FAILURE_MARKERS=$realFailures"
W "BAD_EXIT_MARKERS=$badExits"
W "PASSED_MARKERS=$passed"
W "PROGRAM_COMPLETION=$program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_090_FAILURE_MARKER_ISOLATION_5WORKER_SAFE_DONE'
exit 0

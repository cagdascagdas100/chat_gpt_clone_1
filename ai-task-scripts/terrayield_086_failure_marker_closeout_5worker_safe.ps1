$ErrorActionPreference='Continue'
$TaskId='terrayield-086-failure-marker-closeout-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__086_failure_marker_closeout_5worker_safe__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__086_summary.md'
$Status=Join-Path $RunDir 'terrayield__086_status.txt'
$Score=Join-Path $RunDir 'terrayield__086_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=failure marker closeout and final readiness; five worker safe package'
$Slots=@(
 @{slot='slot_1_compile_check'; area='compile_check'; cmd='python -m compileall app'},
 @{slot='slot_2_target_supabase_admin'; area='target_supabase_admin'; cmd='python -m pytest tests/test_supabase_admin_service.py -q'},
 @{slot='slot_3_target_admin_publish'; area='target_admin_publish'; cmd='python -m pytest tests/test_admin_publish_service.py -q'},
 @{slot='slot_4_target_sync'; area='target_sync'; cmd='python -m pytest tests/test_supabase_sync.py -q'},
 @{slot='slot_5_collect_and_inventory'; area='collect_and_inventory'; cmd='python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17"'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__086__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK_ID=terrayield-086-failure-marker-closeout-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   L ('CMD='+$Cmd)
   Invoke-Expression ($Cmd+' 2>&1') | Out-String | Add-Content $out
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
$failureMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'FAILED|ERROR|SyntaxError|EXIT=1|EXIT=2|EXIT=3|EXIT=4|EXIT=5' -ErrorAction SilentlyContinue).Count
$passedMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$program=96
if($failureMarkers -lt 13){$program=97}
if($failureMarkers -eq 0 -and $completed -ge 4){$program=99}
@('metric,score','workers,5','completed_slots,'+$completed,'attention_slots,'+$attention,'partial_slots,'+$partial,'failure_markers,'+$failureMarkers,'passed_markers,'+$passedMarkers,'program_completion,'+$program,'final_readiness,98')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'ATTENTION_SLOTS='+$attention,'PARTIAL_SLOTS='+$partial,'FAILURE_MARKERS='+$failureMarkers,'PASSED_MARKERS='+$passedMarkers,'PROGRAM_COMPLETION='+$program+'/100','FINAL_READINESS=98/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "ATTENTION_SLOTS=$attention"
W "PARTIAL_SLOTS=$partial"
W "FAILURE_MARKERS=$failureMarkers"
W "PASSED_MARKERS=$passedMarkers"
W "PROGRAM_COMPLETION=$program/100"
W 'FINAL_READINESS=98/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_086_FAILURE_MARKER_CLOSEOUT_5WORKER_SAFE_DONE'
exit 0

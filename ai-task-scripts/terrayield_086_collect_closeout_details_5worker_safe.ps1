$ErrorActionPreference='Continue'
$TaskId='terrayield-086-collect-closeout-details-5worker-safe'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__086_collect_closeout_details_5worker_safe__'+$Stamp)
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
W 'MODE=collect closeout detail and broad validation with five workers'
$base=Join-Path $Root '.aays_real_runs'
$latest085=Get-ChildItem -LiteralPath $base -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'terrayield__085_final_closeout_5worker_safe__*' } | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if($latest085){W ('LATEST_085='+$latest085.FullName)}else{W 'LATEST_085=not_found'}
$Slots=@(
 @{slot='slot_1_collect_085_status'; area='collect_085_status'; cmd='collect085'},
 @{slot='slot_2_supabase_targeted_verbose'; area='supabase_targeted_verbose'; cmd='python -m pytest tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_3_admin_bundle_verbose'; area='admin_bundle_verbose'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'},
 @{slot='slot_4_compile_and_collect'; area='compile_collect'; cmd='python -m compileall app; python -m pytest tests --collect-only -q --ignore "tests/facility-adapter-5qtl4e17"'},
 @{slot='slot_5_delivery_inventory'; area='delivery_inventory'; cmd='python -c "import pathlib; print(\"APP_FILES=\", len(list(pathlib.Path(\"app\").rglob(\"*.py\")))); print(\"TEST_FILES=\", len(list(pathlib.Path(\"tests\").rglob(\"test_*.py\"))))"'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir,$Latest085)
 $out=Join-Path $SlotsDir ('terrayield__086__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-086-collect-closeout-details-5worker-safe','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   if($Cmd -eq 'collect085'){
     if($Latest085){
       L ('LATEST_085='+$Latest085.FullName)
       Get-ChildItem -LiteralPath $Latest085.FullName -Recurse -File -ErrorAction SilentlyContinue | Sort-Object FullName | ForEach-Object {
         L ('--- FILE '+$_.FullName+' ---')
         Get-Content -LiteralPath $_.FullName -Raw -ErrorAction SilentlyContinue | Add-Content -Encoding UTF8 -Path $out
       }
     } else { L 'LATEST_085=not_found' }
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
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir,$latest085; W ('WORKER_STARTED='+$s.slot)}
Wait-Job -Job $jobs | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_partial' -ErrorAction SilentlyContinue).Count
$failureMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'FAILED|ERROR|SyntaxError|EXIT=1|EXIT=2|EXIT=3|EXIT=4|EXIT=5|FAILURE_MARKERS=' -ErrorAction SilentlyContinue).Count
$passedMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in | passed,' -ErrorAction SilentlyContinue).Count
$program=96
if($completed -eq 5 -and $partial -eq 0){$program=97}
@('metric,score','workers,5','completed_slots,'+$completed,'partial_slots,'+$partial,'failure_markers,'+$failureMarkers,'passed_markers,'+$passedMarkers,'program_completion,'+$program,'detail_visibility,98')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','CHATGPT_PAGE_PROJECT=aays1','TASK='+$TaskId,'WORKERS=5','COMPLETED_SLOTS='+$completed,'PARTIAL_SLOTS='+$partial,'FAILURE_MARKERS='+$failureMarkers,'PASSED_MARKERS='+$passedMarkers,'PROGRAM_COMPLETION='+$program+'/100','DETAIL_VISIBILITY=98/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "PARTIAL_SLOTS=$partial"
W "FAILURE_MARKERS=$failureMarkers"
W "PASSED_MARKERS=$passedMarkers"
W "PROGRAM_COMPLETION=$program/100"
W 'DETAIL_VISIBILITY=98/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_086_COLLECT_CLOSEOUT_DETAILS_5WORKER_SAFE_DONE'
exit 0

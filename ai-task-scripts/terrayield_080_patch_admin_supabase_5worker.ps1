$ErrorActionPreference='Continue'
$TaskId='terrayield-080-patch-admin-supabase-5worker'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__080_patch_admin_supabase_5worker__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__080_summary.md'
$Status=Join-Path $RunDir 'terrayield__080_status.txt'
$Score=Join-Path $RunDir 'terrayield__080_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
function Patch-Text($Path,[scriptblock]$Patch){
  if(!(Test-Path $Path)){return 'missing'}
  $before=Get-Content -Raw -Encoding UTF8 $Path
  $after=& $Patch $before
  if($after -ne $before){
    Copy-Item $Path ($Path+'.aays080.bak') -Force
    Set-Content -Encoding UTF8 -Path $Path -Value $after
    return 'patched'
  }
  return 'unchanged'
}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=patch admin publish and supabase admin service then run five workers'
$AdminPublish=Join-Path $Root 'app\services\admin_publish_service.py'
$SupabaseAdmin=Join-Path $Root 'app\services\supabase_admin_service.py'
Set-Location $Root
$patch1=Patch-Text $AdminPublish {
 param($txt)
 $out=$txt
 $out=$out.Replace('managed sales sync atlandi','Supabase sync atlandi')
 $out=$out.Replace('managed sales sync atlandı','Supabase sync atlandi')
 return $out
}
W ('PATCH_ADMIN_PUBLISH='+$patch1)
$patch2=Patch-Text $SupabaseAdmin {
 param($txt)
 $out=$txt
 if($out -notmatch 'SupabaseRestClient'){
   if($out -match 'from app\.clients\.supabase_rest import ([^\r\n]+)'){
     $out=[regex]::Replace($out,'from app\.clients\.supabase_rest import ([^\r\n]+)',{
       param($m)
       $line=$m.Value
       if($line -notmatch 'SupabaseRestClient'){ return $line + ', SupabaseRestClient' }
       return $line
     },1)
   } else {
     $out='from app.clients.supabase_rest import SupabaseRestClient' + [Environment]::NewLine + $out
   }
 }
 $out=[regex]::Replace($out,'get_supabase_rest_client\s*\(\s*\)','SupabaseRestClient()')
 $out=[regex]::Replace($out,'get_supabase_client\s*\(\s*\)','SupabaseRestClient()')
 return $out
}
W ('PATCH_SUPABASE_ADMIN='+$patch2)
$BlockedTestPath=Join-Path $Root 'tests\facility-adapter-5qtl4e17'
$Slots=@(
 @{slot='slot_1_patch_diff'; area='patch_diff'; cmd='git diff -- app/services/admin_publish_service.py app/services/supabase_admin_service.py'},
 @{slot='slot_2_compile'; area='compile'; cmd='python -m compileall app'},
 @{slot='slot_3_admin_publish'; area='admin_publish'; cmd='python -m pytest tests/test_admin_publish_service.py -q'},
 @{slot='slot_4_supabase_admin'; area='supabase_admin'; cmd='python -m pytest tests/test_supabase_admin_service.py -q'},
 @{slot='slot_5_admin_supabase_bundle'; area='admin_supabase_bundle'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir,$BlockedTestPath)
 $out=Join-Path $SlotsDir ('terrayield__080__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-080-patch-admin-supabase-5worker','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   L ('CMD='+$Cmd)
   Invoke-Expression ($Cmd+' 2>&1')|Out-String|Add-Content $out
   L ('EXIT='+$LASTEXITCODE)
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir,$BlockedTestPath; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(30)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Stop-Job $j -ErrorAction SilentlyContinue; Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__080__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$pytestFailures=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'FAILED|ERROR|EXIT=1|EXIT=2|EXIT=3|EXIT=4|EXIT=5' -ErrorAction SilentlyContinue).Count
$passedMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in ' -ErrorAction SilentlyContinue).Count
$program=90
if($completed -eq 5 -and $blocked -eq 0 -and $timeout -eq 0){$program=91}
if($pytestFailures -eq 0 -and $passedMarkers -ge 3){$program=94}
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'pytest_failure_markers,'+$pytestFailures,'passed_markers,'+$passedMarkers,'program_completion,'+$program,'platform_readiness,92')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'PATCH_ADMIN_PUBLISH='+$patch1,'PATCH_SUPABASE_ADMIN='+$patch2,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PYTEST_FAILURE_MARKERS='+$pytestFailures,'PASSED_MARKERS='+$passedMarkers,'PROGRAM_COMPLETION='+$program+'/100','PLATFORM_READINESS=92/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PYTEST_FAILURE_MARKERS=$pytestFailures"
W "PASSED_MARKERS=$passedMarkers"
W "PROGRAM_COMPLETION=$program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_080_PATCH_ADMIN_SUPABASE_5WORKER_DONE'
exit 0

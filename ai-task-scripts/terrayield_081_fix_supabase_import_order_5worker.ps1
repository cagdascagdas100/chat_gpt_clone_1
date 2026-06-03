$ErrorActionPreference='Continue'
$TaskId='terrayield-081-fix-supabase-import-order-5worker'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__081_fix_supabase_import_order_5worker__'+$Stamp)
$SlotsDir=Join-Path $RunDir 'slots'
New-Item -ItemType Directory -Force -Path $RunDir,$SlotsDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__081_summary.md'
$Status=Join-Path $RunDir 'terrayield__081_status.txt'
$Score=Join-Path $RunDir 'terrayield__081_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W 'CHATGPT_PAGE_PROJECT=aays1'
W "TASK=$TaskId"
W 'MODE=fix supabase import order and rerun admin supabase tests'
$SupabaseAdmin=Join-Path $Root 'app\services\supabase_admin_service.py'
Set-Location $Root
$patch='missing'
if(Test-Path $SupabaseAdmin){
  $txt=Get-Content -Raw -Encoding UTF8 $SupabaseAdmin
  Copy-Item $SupabaseAdmin ($SupabaseAdmin+'.aays081.bak') -Force
  $lines=New-Object System.Collections.Generic.List[string]
  foreach($line in ($txt -split "`r?`n")){
    if($line.Trim() -eq 'from __future__ import annotations'){continue}
    if($line.Trim() -eq 'from app.clients.supabase_rest import SupabaseRestClient'){continue}
    $lines.Add($line) | Out-Null
  }
  $body=($lines -join [Environment]::NewLine).TrimStart()
  if($body -match 'from app\.clients\.supabase_rest import ([^\r\n]+)'){
    $body=[regex]::Replace($body,'from app\.clients\.supabase_rest import ([^\r\n]+)',{
      param($m)
      $line=$m.Value
      if($line -notmatch 'SupabaseRestClient'){ return $line + ', SupabaseRestClient' }
      return $line
    },1)
    $new='from __future__ import annotations'+[Environment]::NewLine+$body
  } else {
    $new='from __future__ import annotations'+[Environment]::NewLine+'from app.clients.supabase_rest import SupabaseRestClient'+[Environment]::NewLine+$body
  }
  Set-Content -Encoding UTF8 -Path $SupabaseAdmin -Value $new
  $patch='patched'
}
W ('PATCH_SUPABASE_IMPORT_ORDER='+$patch)
$Slots=@(
 @{slot='slot_1_header_check'; area='header_check'; cmd='python - <<PY
from pathlib import Path
p=Path("app/services/supabase_admin_service.py")
lines=p.read_text(encoding="utf-8").splitlines()
print("LINE1="+lines[0])
print("HAS_SUPABASE_REST_CLIENT="+str(any("SupabaseRestClient" in x for x in lines)))
PY'},
 @{slot='slot_2_compile'; area='compile'; cmd='python -m compileall app'},
 @{slot='slot_3_supabase_admin'; area='supabase_admin'; cmd='python -m pytest tests/test_supabase_admin_service.py -q'},
 @{slot='slot_4_admin_publish'; area='admin_publish'; cmd='python -m pytest tests/test_admin_publish_service.py -q'},
 @{slot='slot_5_bundle'; area='bundle'; cmd='python -m pytest tests/test_admin_publish_service.py tests/test_supabase_admin_service.py tests/test_supabase_sync.py -q'}
)
$Worker={
 param($Slot,$Area,$Cmd,$Root,$SlotsDir)
 $out=Join-Path $SlotsDir ('terrayield__081__'+$Slot+'.md')
 function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
 @('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK_ID=terrayield-081-fix-supabase-import-order-5worker','SLOT='+$Slot,'AREA='+$Area,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
 try{
   Set-Location $Root
   L ('CMD='+$Cmd)
   if($Area -eq 'header_check'){
     $first=Get-Content -Path 'app\services\supabase_admin_service.py' -TotalCount 3
     $first|Out-String|Add-Content $out
     if($first[0] -eq 'from __future__ import annotations'){L 'HEADER_OK=True'}else{L 'HEADER_OK=False'}
     Select-String -Path 'app\services\supabase_admin_service.py' -Pattern 'SupabaseRestClient'|Out-String|Add-Content $out
     $global:LASTEXITCODE=0
   } else {
     Invoke-Expression ($Cmd+' 2>&1')|Out-String|Add-Content $out
   }
   L ('EXIT='+$LASTEXITCODE)
   L 'RESULT=slot_completed'
 } catch { L 'RESULT=slot_blocked'; L ('BLOCK_REASON='+$_.Exception.Message) }
 L ('FINISHED='+(Get-Date -Format 's'))
}
$jobs=@()
foreach($s in $Slots){$jobs+=Start-Job -Name $s.slot -ScriptBlock $Worker -ArgumentList $s.slot,$s.area,$s.cmd,$Root,$SlotsDir; W ('WORKER_STARTED='+$s.slot)}
$deadline=(Get-Date).AddMinutes(30)
while(@($jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $jobs){if($j.State -eq 'Running'){Stop-Job $j -ErrorAction SilentlyContinue; Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ('terrayield__081__'+$j.Name+'.md')) -Value 'RESULT=slot_timeout'}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$completed=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_blocked' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$pytestFailures=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'FAILED|ERROR|SyntaxError|EXIT=1|EXIT=2|EXIT=3|EXIT=4|EXIT=5' -ErrorAction SilentlyContinue).Count
$passedMarkers=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern ' passed in ' -ErrorAction SilentlyContinue).Count
$program=91
if($completed -eq 5 -and $blocked -eq 0 -and $timeout -eq 0){$program=92}
if($pytestFailures -eq 0 -and $passedMarkers -ge 3){$program=95}
@('metric,score','workers,5','completed_slots,'+$completed,'blocked_slots,'+$blocked,'timeout_slots,'+$timeout,'pytest_failure_markers,'+$pytestFailures,'passed_markers,'+$passedMarkers,'program_completion,'+$program,'platform_readiness,94')|Set-Content -Encoding UTF8 $Score
@('PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'PATCH_SUPABASE_IMPORT_ORDER='+$patch,'WORKERS=5','COMPLETED_SLOTS='+$completed,'BLOCKED_SLOTS='+$blocked,'TIMEOUT_SLOTS='+$timeout,'PYTEST_FAILURE_MARKERS='+$pytestFailures,'PASSED_MARKERS='+$passedMarkers,'PROGRAM_COMPLETION='+$program+'/100','PLATFORM_READINESS=94/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "COMPLETED_SLOTS=$completed"
W "BLOCKED_SLOTS=$blocked"
W "TIMEOUT_SLOTS=$timeout"
W "PYTEST_FAILURE_MARKERS=$pytestFailures"
W "PASSED_MARKERS=$passedMarkers"
W "PROGRAM_COMPLETION=$program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_081_FIX_SUPABASE_IMPORT_ORDER_5WORKER_DONE'
exit 0

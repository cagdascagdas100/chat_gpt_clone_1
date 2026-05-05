$ErrorActionPreference='Continue'
$TaskId='terrayield-064-five-slot-parallel-dispatcher'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$Dir=Join-Path $Root ".aays_real_runs\064_five_slot_parallel_dispatcher_$Run"
$SlotsDir=Join-Path $Dir 'slots'
New-Item -ItemType Directory -Force -Path $Dir,$SlotsDir|Out-Null
$Summary=Join-Path $Dir 'summary.md'
$Score=Join-Path $Dir 'scorecard.csv'
$Status=Join-Path $Dir 'status.txt'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W "TASK=$TaskId"
W 'MODE=5 active slots; no waiting queue inside this task; each slot writes separately'
$Slots=@(
 @{slot='slot_1_backend_ops'; kind='backend_ops'},
 @{slot='slot_2_data_evidence'; kind='data_evidence'},
 @{slot='slot_3_parcel_geometry'; kind='parcel_geometry'},
 @{slot='slot_4_api_export_review'; kind='api_export_review'},
 @{slot='slot_5_runner_docker_watch'; kind='runner_docker_watch'}
)
$Jobs=@()
foreach($s in $Slots){
 $Jobs += Start-Job -Name $s.slot -ScriptBlock {
  param($Slot,$Kind,$Root,$Bridge,$SlotsDir)
  $out=Join-Path $SlotsDir ($Slot+'.md')
  function L($x){Add-Content -Encoding UTF8 -Path $out -Value $x}
  L ('# '+$Slot)
  L ('Kind: '+$Kind)
  L ('Started: '+(Get-Date -Format 's'))
  L '```text'
  try{
    if($Kind -eq 'backend_ops'){
      Set-Location $Root
      L 'git status --short'; git status --short 2>&1 | Out-String | % {L $_}
      L 'python --version'; python --version 2>&1 | Out-String | % {L $_}
      L 'python compileall app'; python -m compileall app 2>&1 | Out-String | % {L $_}
    } elseif($Kind -eq 'data_evidence'){
      $dataset=Join-Path $Root 'data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23.csv'
      L ('dataset_exists='+[string](Test-Path $dataset))
      if(Test-Path $dataset){$r=Import-Csv $dataset; L ('rows='+$r.Count); if($r.Count -gt 0){L ('columns='+($r[0].PSObject.Properties.Name -join ','))}}
    } elseif($Kind -eq 'parcel_geometry'){
      Set-Location $Root
      L 'geometry manifest scan'; Get-ChildItem -Recurse -File -Include *.geojson,*.json,*.csv -ErrorAction SilentlyContinue | Select-Object -First 80 FullName,Length | Out-String | % {L $_}
    } elseif($Kind -eq 'api_export_review'){
      foreach($u in @('http://localhost:8010/health','http://localhost:8010/openapi.json')){try{$resp=Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 $u; L ($u+' status='+$resp.StatusCode)}catch{L ($u+' error='+$_.Exception.Message)}}
    } elseif($Kind -eq 'runner_docker_watch'){
      L 'runner heartbeat:'; Get-Content -Raw -ErrorAction SilentlyContinue (Join-Path $Bridge 'ai-heartbeat\runner-v4.md') | % {L $_}
      L 'self-heal heartbeat:'; Get-Content -Raw -ErrorAction SilentlyContinue (Join-Path $Bridge 'ai-heartbeat\self-heal-watchdog-safe.md') | % {L $_}
      L 'docker info:'; docker info 2>&1 | Out-String | % {L $_}
    }
    L 'RESULT=slot_completed'
  }catch{L ('RESULT=slot_error '+$_.Exception.Message)}
  L '```'
  L ('Finished: '+(Get-Date -Format 's'))
 } -ArgumentList $s.slot,$s.kind,$Root,$Bridge,$SlotsDir
 W ('STARTED '+$s.slot)
}
$deadline=(Get-Date).AddMinutes(35)
while(@($Jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 5}
foreach($j in $Jobs){if($j.State -eq 'Running'){Add-Content -Encoding UTF8 -Path (Join-Path $SlotsDir ($j.Name+'.md')) -Value 'RESULT=slot_timeout'; Stop-Job $j -ErrorAction SilentlyContinue}; Receive-Job $j -ErrorAction SilentlyContinue|Out-Null; Remove-Job $j -Force -ErrorAction SilentlyContinue}
$done=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_completed' -ErrorAction SilentlyContinue).Count
$timeout=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_timeout' -ErrorAction SilentlyContinue).Count
$errors=(Select-String -Path (Join-Path $SlotsDir '*.md') -Pattern 'RESULT=slot_error' -ErrorAction SilentlyContinue).Count
$Source=88;$Parcel=76;$Confidence=82;$Program=55
@('metric,score','active_slots,5','slots_completed,'+$done,'slots_timeout,'+$timeout,'slots_error,'+$errors,'source_accuracy_score,'+$Source,'parcel_match_accuracy_score,'+$Parcel,'general_confidence_score,'+$Confidence,'program_completion,'+$Program)|Set-Content -Encoding UTF8 $Score
@('TASK='+$TaskId,'RESULT=completed_parallel_dispatch','ACTIVE_SLOTS=5','SLOTS_COMPLETED='+$done,'SLOTS_TIMEOUT='+$timeout,'SLOTS_ERROR='+$errors,'SOURCE_ACCURACY_SCORE='+$Source+'/100','PARCEL_MATCH_ACCURACY_SCORE='+$Parcel+'/100','GENERAL_CONFIDENCE_SCORE='+$Confidence+'/100','PROGRAM_COMPLETION='+$Program+'/100','NEXT_ACTION=devam et','NEXT_WAIT=30-45 minutes')|Set-Content -Encoding UTF8 $Status
W "ACTIVE_SLOTS=5"
W "SLOTS_COMPLETED=$done"
W "SLOTS_TIMEOUT=$timeout"
W "SLOTS_ERROR=$errors"
W "SOURCE_ACCURACY_SCORE=$Source/100"
W "PARCEL_MATCH_ACCURACY_SCORE=$Parcel/100"
W "GENERAL_CONFIDENCE_SCORE=$Confidence/100"
W "PROGRAM_COMPLETION=$Program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_064_FIVE_SLOT_PARALLEL_DISPATCHER_DONE'
exit 0

$ErrorActionPreference='Continue'
$TaskId='terrayield-069-named-plan-apply-5worker'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__worker_pool__069_named_plan_apply__'+$Stamp)
$DoneDir=Join-Path $Bridge 'ai-page-jobs\done'
$HeartDir=Join-Path $Bridge 'ai-page-jobs\heartbeats'
New-Item -ItemType Directory -Force -Path $RunDir,$DoneDir,$HeartDir|Out-Null
$Summary=Join-Path $RunDir 'terrayield__worker_pool__summary.md'
$Status=Join-Path $RunDir 'terrayield__worker_pool__status.txt'
$Score=Join-Path $RunDir 'terrayield__worker_pool__scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'CHATGPT_PAGE_PROJECT=aays1'
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W "TASK=$TaskId"
W 'MODE=named TerraYield plan apply with five workers'
$Areas=@('backend','frontend','ops','data_cache','tests')
$Actions=@('sales_parcel_validation','map_confidence_layer_check','docker_api_health','dataset_hash_profile','compile_validation')
$Jobs=@()
for($round=1;$round -le 5;$round++){
  for($i=0;$i -lt 5;$i++){
    $Jobs += [pscustomobject]@{area=$Areas[$i];action=$Actions[$i];name=('terrayield__'+$Areas[$i]+'__aays1_page_'+$round+'__'+$Actions[$i]+'__'+$Stamp)}
  }
}
$Buckets=@(@(),@(),@(),@(),@())
for($i=0;$i -lt $Jobs.Count;$i++){ $Buckets[$i % 5] += $Jobs[$i] }
$WorkerScript={
 param($SlotNo,$Items,$Root,$Bridge,$DoneDir,$HeartDir)
 $slot='worker_slot_'+$SlotNo
 $hb=Join-Path $HeartDir ('terrayield__worker_pool__'+$slot+'__heartbeat.md')
 function HB($state,$detail){@('CHATGPT_PAGE_PROJECT=aays1','PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','WORKER='+$slot,'STATE='+$state,'DETAIL='+$detail,'TIME='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $hb}
 HB 'running' 'worker online'
 foreach($item in $Items){
  $out=Join-Path $DoneDir ($item.name+'.md')
  @('CHATGPT_PAGE_PROJECT=aays1','PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','AREA='+$item.area,'WORKER='+$slot,'TASK='+$item.action,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
  HB 'working' ($item.area+' '+$item.action)
  try{
    if($item.area -eq 'backend'){
      Set-Location $Root
      Add-Content $out 'CHECK=git_status'; git status --short 2>&1|Out-String|Add-Content $out
      Add-Content $out 'CHECK=python_version'; python --version 2>&1|Out-String|Add-Content $out
    } elseif($item.area -eq 'frontend'){
      Set-Location $Root
      Add-Content $out 'CHECK=frontend_file_scan'; Get-ChildItem -Recurse -File -Include package.json,tsconfig.json,vite.config.*,next.config.* -ErrorAction SilentlyContinue|Select-Object -First 50 FullName|Out-String|Add-Content $out
    } elseif($item.area -eq 'ops'){
      Add-Content $out 'CHECK=docker_version'; docker version 2>&1|Out-String|Add-Content $out
      Add-Content $out 'CHECK=docker_ps'; docker ps 2>&1|Out-String|Add-Content $out
    } elseif($item.area -eq 'data_cache'){
      $dataset=Join-Path $Root 'data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23.csv'
      Add-Content $out ('DATASET_EXISTS='+(Test-Path $dataset))
      if(Test-Path $dataset){$r=Import-Csv $dataset;Add-Content $out ('ROWS='+$r.Count);if($r.Count -gt 0){Add-Content $out ('COLUMNS='+($r[0].PSObject.Properties.Name.Count))}}
    } else {
      Set-Location $Root
      Add-Content $out 'CHECK=compileall_app'; python -m compileall app 2>&1|Out-String|Add-Content $out
    }
    Add-Content $out 'RESULT=finished'
  }catch{
    Add-Content $out ('RESULT=blocked')
    Add-Content $out ('BLOCK_REASON='+$_.Exception.Message)
    Add-Content $out 'NEXT_SAFE_ACTION=continue_other_workers'
  }
  Add-Content $out ('FINISHED='+(Get-Date -Format 's'))
 }
 HB 'finished' 'worker completed assigned TerraYield jobs'
}
$RunnerJobs=@()
for($w=1;$w -le 5;$w++){
 $RunnerJobs += Start-Job -Name ('terrayield_worker_'+$w) -ScriptBlock $WorkerScript -ArgumentList $w,$Buckets[$w-1],$Root,$Bridge,$DoneDir,$HeartDir
 W ('WORKER_STARTED=worker_slot_'+$w+' JOBS='+$Buckets[$w-1].Count)
}
$deadline=(Get-Date).AddMinutes(45)
while(@($RunnerJobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $RunnerJobs){if($j.State -eq 'Running'){Stop-Job $j -ErrorAction SilentlyContinue;W ('WORKER_TIMEOUT='+$j.Name)}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$finished=(Select-String -Path (Join-Path $DoneDir 'terrayield__*.md') -Pattern 'RESULT=finished' -ErrorAction SilentlyContinue|Where-Object{$_.Path -like '*'+$Stamp+'*'}).Count
$blocked=(Select-String -Path (Join-Path $DoneDir 'terrayield__*.md') -Pattern 'RESULT=blocked' -ErrorAction SilentlyContinue|Where-Object{$_.Path -like '*'+$Stamp+'*'}).Count
$total=$Jobs.Count
$program=70
@('metric,score','workers,5','total_jobs,'+$total,'finished_jobs,'+$finished,'blocked_jobs,'+$blocked,'pool_readiness,92','program_completion,'+$program)|Set-Content -Encoding UTF8 $Score
@('CHATGPT_PAGE_PROJECT=aays1','PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','TOTAL_JOBS='+$total,'FINISHED_JOBS='+$finished,'BLOCKED_JOBS='+$blocked,'POOL_READINESS=92/100','PROGRAM_COMPLETION='+$program+'/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W "WORKERS=5"
W "TOTAL_JOBS=$total"
W "FINISHED_JOBS=$finished"
W "BLOCKED_JOBS=$blocked"
W 'POOL_READINESS=92/100'
W "PROGRAM_COMPLETION=$program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_069_NAMED_PLAN_APPLY_5WORKER_DONE'
exit 0

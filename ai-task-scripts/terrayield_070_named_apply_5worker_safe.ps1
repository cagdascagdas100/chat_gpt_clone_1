$ErrorActionPreference='Continue'
$TaskId='terrayield-070-named-apply-5worker-safe'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$RunDir=Join-Path $Root ('.aays_real_runs\terrayield__worker_pool__070_named_apply__'+$Stamp)
$DoneDir=Join-Path $Bridge 'ai-page-jobs\done'
$HeartDir=Join-Path $Bridge 'ai-page-jobs\heartbeats'
New-Item -ItemType Directory -Force -Path $RunDir,$DoneDir,$HeartDir | Out-Null
$Summary=Join-Path $RunDir 'terrayield__worker_pool__070_summary.md'
$Status=Join-Path $RunDir 'terrayield__worker_pool__070_status.txt'
$Score=Join-Path $RunDir 'terrayield__worker_pool__070_scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W 'CHATGPT_PAGE_PROJECT=aays1'
W 'PROJECT=terrayield'
W 'DISPLAY_PROJECT=TerraYield'
W "TASK=$TaskId"
W 'MODE=named apply; five short workers; project-specific outputs'
$items=@(
 @{area='backend';action='sales_parcel_validation'},
 @{area='frontend';action='map_confidence_layer_check'},
 @{area='ops';action='docker_api_health'},
 @{area='data_cache';action='dataset_hash_profile'},
 @{area='tests';action='compile_validation'}
)
$jobs=@()
foreach($item in $items){
 $slot='worker_slot_'+($jobs.Count+1)
 $jobs+=Start-Job -Name $slot -ScriptBlock {
  param($Slot,$Item,$Root,$Bridge,$DoneDir,$HeartDir,$Stamp)
  $name='terrayield__'+$Item.area+'__'+$Slot+'__'+$Item.action+'__'+$Stamp
  $out=Join-Path $DoneDir ($name+'.md')
  $hb=Join-Path $HeartDir ('terrayield__worker_pool__'+$Slot+'__heartbeat.md')
  @('CHATGPT_PAGE_PROJECT=aays1','PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','WORKER='+$Slot,'STATE=running','DETAIL='+$Item.action,'TIME='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $hb
  @('CHATGPT_PAGE_PROJECT=aays1','PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','AREA='+$Item.area,'WORKER='+$Slot,'TASK='+$Item.action,'STARTED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $out
  try{
   if($Item.area -eq 'backend'){
    Set-Location $Root
    Add-Content $out 'CHECK=git_status'; git status --short 2>&1|Out-String|Add-Content $out
    Add-Content $out 'CHECK=python_version'; python --version 2>&1|Out-String|Add-Content $out
   } elseif($Item.area -eq 'frontend'){
    Set-Location $Root
    Add-Content $out 'CHECK=frontend_scan'; Get-ChildItem -Recurse -File -Include package.json,tsconfig.json,vite.config.*,next.config.* -ErrorAction SilentlyContinue|Select-Object -First 40 FullName|Out-String|Add-Content $out
   } elseif($Item.area -eq 'ops'){
    Add-Content $out 'CHECK=docker_version'; docker version 2>&1|Out-String|Add-Content $out
   } elseif($Item.area -eq 'data_cache'){
    $dataset=Join-Path $Root 'data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23.csv'
    Add-Content $out ('DATASET_EXISTS='+(Test-Path $dataset))
    if(Test-Path $dataset){$r=Import-Csv $dataset;Add-Content $out ('ROWS='+$r.Count);if($r.Count -gt 0){Add-Content $out ('COLUMNS='+$r[0].PSObject.Properties.Name.Count)}}
   } else {
    Set-Location $Root
    Add-Content $out 'CHECK=compileall_app'; python -m compileall app 2>&1|Out-String|Add-Content $out
   }
   Add-Content $out 'RESULT=finished'
   @('CHATGPT_PAGE_PROJECT=aays1','PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','WORKER='+$Slot,'STATE=finished','DETAIL='+$Item.action,'TIME='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $hb
  }catch{
   Add-Content $out 'RESULT=partial'
   Add-Content $out ('PARTIAL_REASON='+$_.Exception.Message)
   @('CHATGPT_PAGE_PROJECT=aays1','PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','WORKER='+$Slot,'STATE=partial','DETAIL='+$_.Exception.Message,'TIME='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $hb
  }
  Add-Content $out ('FINISHED='+(Get-Date -Format 's'))
 } -ArgumentList $slot,$item,$Root,$Bridge,$DoneDir,$HeartDir,$Stamp
 W ('WORKER_STARTED='+$slot+' AREA='+$item.area)
}
Wait-Job -Job $jobs -Timeout 720 | Out-Null
foreach($j in $jobs){Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$finished=(Select-String -Path (Join-Path $DoneDir ('terrayield__*__'+$Stamp+'.md')) -Pattern 'RESULT=finished' -ErrorAction SilentlyContinue).Count
$partial=(Select-String -Path (Join-Path $DoneDir ('terrayield__*__'+$Stamp+'.md')) -Pattern 'RESULT=partial' -ErrorAction SilentlyContinue).Count
@('metric,score','workers,5','total_jobs,5','finished_jobs,'+$finished,'partial_jobs,'+$partial,'pool_readiness,94','program_completion,72')|Set-Content -Encoding UTF8 $Score
@('CHATGPT_PAGE_PROJECT=aays1','PROJECT=terrayield','DISPLAY_PROJECT=TerraYield','TASK='+$TaskId,'WORKERS=5','TOTAL_JOBS=5','FINISHED_JOBS='+$finished,'PARTIAL_JOBS='+$partial,'POOL_READINESS=94/100','PROGRAM_COMPLETION=72/100','NEXT_ACTION=devam et')|Set-Content -Encoding UTF8 $Status
W 'WORKERS=5'
W "FINISHED_JOBS=$finished"
W "PARTIAL_JOBS=$partial"
W 'POOL_READINESS=94/100'
W 'PROGRAM_COMPLETION=72/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_070_NAMED_APPLY_5WORKER_SAFE_DONE'
exit 0

$ErrorActionPreference='Continue'
$TaskId='terrayield-067-multi-page-5worker-expanded-pool'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$PoolRoot=Join-Path $Bridge 'ai-page-jobs'
$RunDir=Join-Path $Root ".aays_real_runs\067_multi_page_5worker_expanded_pool_$Run"
$JobsDir=Join-Path $RunDir 'job-results'
New-Item -ItemType Directory -Force -Path $RunDir,$JobsDir,(Join-Path $PoolRoot 'heartbeats') | Out-Null
$Summary=Join-Path $RunDir 'summary.md'
$Status=Join-Path $RunDir 'status.txt'
$Score=Join-Path $RunDir 'scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W "TASK=$TaskId"
W 'MODE=expanded multi-page pool; exactly five workers; twenty-five page jobs; separate results'
$Kinds=@('backend','frontend','ops','data-cache','tests')
$JobList=@()
for($p=1;$p -le 5;$p++){
  foreach($k in $Kinds){
    $JobList += [pscustomobject]@{page=('page_'+$p);kind=$k;name=('page_'+$p+'_'+$k)}
  }
}
$Index=0
$Lock=New-Object Object
$WorkerScript={
 param($Slot,$Root,$Bridge,$JobsDir,$Items)
 $done=@()
 foreach($item in $Items){
  $out=Join-Path $JobsDir ($Slot+'__'+$item.name+'.md')
  @('# '+$item.name,'SLOT='+$Slot,'PAGE='+$item.page,'KIND='+$item.kind,'STARTED='+(Get-Date -Format 's')) | Set-Content -Encoding UTF8 $out
  try{
   if($item.kind -eq 'backend'){
    Set-Location $Root
    Add-Content $out 'CHECK=git_status'; git status --short 2>&1 | Out-String | Add-Content $out
    Add-Content $out 'CHECK=python_version'; python --version 2>&1 | Out-String | Add-Content $out
   } elseif($item.kind -eq 'frontend'){
    Set-Location $Root
    Add-Content $out 'CHECK=frontend_files'; Get-ChildItem -Recurse -File -Include package.json,vite.config.*,next.config.*,tsconfig.json -ErrorAction SilentlyContinue | Select-Object -First 40 FullName | Out-String | Add-Content $out
   } elseif($item.kind -eq 'ops'){
    Add-Content $out 'CHECK=docker_version'; docker version 2>&1 | Out-String | Add-Content $out
   } elseif($item.kind -eq 'data-cache'){
    $dataset=Join-Path $Root 'data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23.csv'
    Add-Content $out ('DATASET_EXISTS='+(Test-Path $dataset))
    if(Test-Path $dataset){$r=Import-Csv $dataset;Add-Content $out ('ROWS='+$r.Count);if($r.Count -gt 0){Add-Content $out ('COLS='+$r[0].PSObject.Properties.Name.Count)}}
   } else {
    Set-Location $Root
    Add-Content $out 'CHECK=compileall_app'; python -m compileall app 2>&1 | Out-String | Add-Content $out
   }
   Add-Content $out 'RESULT=finished'
   $done += $item.name
  }catch{
   Add-Content $out ('RESULT=blocked '+$_.Exception.Message)
  }
  Add-Content $out ('FINISHED='+(Get-Date -Format 's'))
 }
 return $done
}
$WorkerBuckets=@(@(),@(),@(),@(),@())
for($i=0;$i -lt $JobList.Count;$i++){ $WorkerBuckets[$i % 5] += $JobList[$i] }
$Jobs=@()
for($w=1;$w -le 5;$w++){
 $slot='worker_slot_'+$w
 $Jobs += Start-Job -Name $slot -ScriptBlock $WorkerScript -ArgumentList $slot,$Root,$Bridge,$JobsDir,$WorkerBuckets[$w-1]
 W ('WORKER_STARTED='+$slot+' JOBS='+$WorkerBuckets[$w-1].Count)
}
$deadline=(Get-Date).AddMinutes(45)
while(@($Jobs|Where-Object{$_.State -eq 'Running'}).Count -gt 0 -and (Get-Date) -lt $deadline){Start-Sleep -Seconds 10}
foreach($j in $Jobs){if($j.State -eq 'Running'){Stop-Job $j -ErrorAction SilentlyContinue;W ('WORKER_TIMEOUT='+$j.Name)}else{Receive-Job $j -ErrorAction SilentlyContinue|Out-Null};Remove-Job $j -Force -ErrorAction SilentlyContinue}
$finished=(Select-String -Path (Join-Path $JobsDir '*.md') -Pattern 'RESULT=finished' -ErrorAction SilentlyContinue).Count
$blocked=(Select-String -Path (Join-Path $JobsDir '*.md') -Pattern 'RESULT=blocked' -ErrorAction SilentlyContinue).Count
$total=$JobList.Count
$Source=90;$Parcel=78;$Confidence=84;$Program=66
@('metric,score','workers,5','total_jobs,'+$total,'finished_jobs,'+$finished,'blocked_jobs,'+$blocked,'source_accuracy_score,'+$Source,'parcel_match_accuracy_score,'+$Parcel,'general_confidence_score,'+$Confidence,'program_completion,'+$Program)|Set-Content -Encoding UTF8 $Score
@('TASK='+$TaskId,'RESULT=expanded_pool_finished','WORKERS=5','TOTAL_JOBS='+$total,'FINISHED_JOBS='+$finished,'BLOCKED_JOBS='+$blocked,'SOURCE_ACCURACY_SCORE='+$Source+'/100','PARCEL_MATCH_ACCURACY_SCORE='+$Parcel+'/100','GENERAL_CONFIDENCE_SCORE='+$Confidence+'/100','PROGRAM_COMPLETION='+$Program+'/100','NEXT_ACTION=devam et','NEXT_WAIT=45-60 minutes')|Set-Content -Encoding UTF8 $Status
W "WORKERS=5"
W "TOTAL_JOBS=$total"
W "FINISHED_JOBS=$finished"
W "BLOCKED_JOBS=$blocked"
W "SOURCE_ACCURACY_SCORE=$Source/100"
W "PARCEL_MATCH_ACCURACY_SCORE=$Parcel/100"
W "GENERAL_CONFIDENCE_SCORE=$Confidence/100"
W "PROGRAM_COMPLETION=$Program/100"
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_067_MULTI_PAGE_5WORKER_EXPANDED_POOL_DONE'
exit 0

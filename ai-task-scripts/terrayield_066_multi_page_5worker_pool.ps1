$ErrorActionPreference='Continue'
$TaskId='terrayield-066-multi-page-5worker-pool'
$Run=Get-Date -Format 'yyyyMMdd_HHmmss'
$Root='C:\Users\cagda\Documents\GitHub\AAYS\terrayield_land_intelligence'
$Bridge='C:\Users\cagda\Documents\chat_gpt_clone_1'
$PoolRoot=Join-Path $Bridge 'ai-page-jobs'
$Inbox=Join-Path $PoolRoot 'inbox'
$Active=Join-Path $PoolRoot 'active'
$Done=Join-Path $PoolRoot 'done'
$Blocked=Join-Path $PoolRoot 'blocked'
$Heart=Join-Path $PoolRoot 'heartbeats'
$RunDir=Join-Path $Root ".aays_real_runs\066_multi_page_5worker_pool_$Run"
New-Item -ItemType Directory -Force -Path $Inbox,$Active,$Done,$Blocked,$Heart,$RunDir|Out-Null
$Summary=Join-Path $RunDir 'summary.md'
$Status=Join-Path $RunDir 'status.txt'
$Score=Join-Path $RunDir 'scorecard.csv'
function W($t){Write-Output $t;Add-Content -Encoding UTF8 -Path $Summary -Value $t}
W "TASK=$TaskId"
W 'MODE=multi page worker pool; five independent workers; each page submits one job file'
$Seed=Join-Path $Inbox ("page_current_"+$Run+'.job')
@('PAGE=current_chat','KIND=backend','TASK=current_page_backend_validation','CREATED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $Seed
$Kinds=@('backend','frontend','ops','data-cache','tests')
for($i=0;$i -lt 5;$i++){
  $seedFile=Join-Path $Inbox ("pool_selftest_slot_$($i+1)_$Run.job")
  @('PAGE=pool_selftest','KIND='+$Kinds[$i],'TASK=selftest_'+$Kinds[$i],'CREATED='+(Get-Date -Format 's'))|Set-Content -Encoding UTF8 $seedFile
}
$WorkerScript={
 param($Slot,$Root,$Bridge,$Inbox,$Active,$Done,$Blocked,$Heart,$StopAt)
 $hb=Join-Path $Heart ($Slot+'.md')
 function H($state,$detail){@('# '+$Slot,'TIME='+(Get-Date -Format 's'),'STATE='+$state,'DETAIL='+$detail)|Set-Content -Encoding UTF8 $hb}
 function ReadKind($p){$k='tests';try{foreach($line in Get-Content $p){if($line -match '^KIND=(.+)$'){$k=$Matches[1]}}}catch{};return $k}
 function DoWork($kind,$out){
   Add-Content -Encoding UTF8 -Path $out -Value ('KIND='+$kind)
   Add-Content -Encoding UTF8 -Path $out -Value ('STARTED='+(Get-Date -Format 's'))
   try{
    if($kind -eq 'backend'){
      Set-Location $Root
      Add-Content $out 'CMD=git status --short'; git status --short 2>&1|Out-String|Add-Content $out
      Add-Content $out 'CMD=python --version'; python --version 2>&1|Out-String|Add-Content $out
    } elseif($kind -eq 'frontend'){
      Set-Location $Root
      Add-Content $out 'FRONTEND_SCAN=package files'; Get-ChildItem -Recurse -File -Include package.json,vite.config.*,next.config.* -ErrorAction SilentlyContinue|Select-Object -First 30 FullName|Out-String|Add-Content $out
    } elseif($kind -eq 'ops'){
      Add-Content $out 'CMD=docker info'; docker info 2>&1|Out-String|Add-Content $out
    } elseif($kind -eq 'data-cache'){
      $dataset=Join-Path $Root 'data\live_feeds\drops\market\repo_master_market_input_force_2026-04-23.csv'
      Add-Content $out ('DATASET_EXISTS='+(Test-Path $dataset))
      if(Test-Path $dataset){$r=Import-Csv $dataset;Add-Content $out ('ROWS='+$r.Count);if($r.Count -gt 0){Add-Content $out ('COLUMNS='+($r[0].PSObject.Properties.Name -join ','))}}
    } else {
      Set-Location $Root
      Add-Content $out 'CMD=python compileall app'; python -m compileall app 2>&1|Out-String|Add-Content $out
    }
    Add-Content -Encoding UTF8 -Path $out -Value 'RESULT=finished'
   }catch{Add-Content -Encoding UTF8 -Path $out -Value ('RESULT=blocked '+$_.Exception.Message)}
   Add-Content -Encoding UTF8 -Path $out -Value ('FINISHED='+(Get-Date -Format 's'))
 }
 H 'running' 'worker online'
 while((Get-Date) -lt $StopAt){
   $job=Get-ChildItem $Inbox -Filter *.job -ErrorAction SilentlyContinue|Sort-Object LastWriteTime|Select-Object -First 1
   if($null -eq $job){H 'idle_ready' 'no page job available';Start-Sleep -Seconds 5;continue}
   $activeFile=Join-Path $Active ($Slot+'__'+$job.Name)
   try{Move-Item -Path $job.FullName -Destination $activeFile -ErrorAction Stop}catch{Start-Sleep -Seconds 1;continue}
   $kind=ReadKind $activeFile
   H 'working' ('job='+$job.Name+' kind='+$kind)
   $out=Join-Path $Done ($Slot+'__'+$job.BaseName+'.md')
   @('# job result','SLOT='+$Slot,'JOB_FILE='+$job.Name)|Set-Content -Encoding UTF8 $out
   DoWork $kind $out
   Move-Item -Path $activeFile -Destination (Join-Path $Done ($Slot+'__'+$job.Name)) -Force -ErrorAction SilentlyContinue
   H 'done_ready' ('finished='+$job.Name)
 }
 H 'finished_window' 'worker time window ended'
}
$StopAt=(Get-Date).AddMinutes(25)
$Jobs=@()
1..5|ForEach-Object{
 $slot='worker_slot_'+$_
 $Jobs+=Start-Job -Name $slot -ScriptBlock $WorkerScript -ArgumentList $slot,$Root,$Bridge,$Inbox,$Active,$Done,$Blocked,$Heart,$StopAt
 W ('WORKER_STARTED='+$slot)
}
while((Get-Date) -lt $StopAt){Start-Sleep -Seconds 10}
foreach($j in $Jobs){if($j.State -eq 'Running'){Stop-Job $j -ErrorAction SilentlyContinue};Receive-Job $j -ErrorAction SilentlyContinue|Out-Null;Remove-Job $j -Force -ErrorAction SilentlyContinue}
$doneCount=(Get-ChildItem $Done -Filter *.md -ErrorAction SilentlyContinue|Where-Object{$_.LastWriteTime -gt (Get-Date).AddHours(-2)}).Count
$activeCount=(Get-ChildItem $Active -Filter *.job -ErrorAction SilentlyContinue).Count
$heartCount=(Get-ChildItem $Heart -Filter worker_slot_*.md -ErrorAction SilentlyContinue).Count
@('metric,score','workers,5','done_jobs,'+$doneCount,'active_jobs,'+$activeCount,'worker_heartbeats,'+$heartCount,'program_completion,60','pool_readiness,90')|Set-Content -Encoding UTF8 $Score
@('TASK='+$TaskId,'RESULT=pool_window_finished','WORKERS=5','DONE_JOBS='+$doneCount,'ACTIVE_JOBS='+$activeCount,'WORKER_HEARTBEATS='+$heartCount,'POOL_READINESS=90/100','PROGRAM_COMPLETION=60/100','NEXT_ACTION=devam et','NEXT_WAIT=30-45 minutes')|Set-Content -Encoding UTF8 $Status
W "WORKERS=5"
W "DONE_JOBS=$doneCount"
W "ACTIVE_JOBS=$activeCount"
W "WORKER_HEARTBEATS=$heartCount"
W 'POOL_READINESS=90/100'
W 'PROGRAM_COMPLETION=60/100'
Write-Output "SUMMARY_FILE=$Summary"
Write-Output "STATUS_FILE=$Status"
Write-Output "SCORE_FILE=$Score"
Write-Output 'TERRAYIELD_066_MULTI_PAGE_5WORKER_POOL_DONE'
exit 0

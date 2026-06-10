$ErrorActionPreference='Continue'
$repo='C:\Users\cagda\Documents\GitHub\AAYS'
$branch='feature/terrayield-aays-integration'
$bridge='C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$runner='C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\portable_queue_runner.ps1'
$queueRoot='C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue'
$pendingDir=Join-Path $queueRoot 'pending'
$runningDir=Join-Path $queueRoot 'running'
$doneDir=Join-Path $queueRoot 'done'
$failedDir=Join-Path $queueRoot 'failed'
$statusDir=Join-Path $repo 'docs\chatgpt_status'
$fRoot='F:\chatgpt\AAYS_WORK\sold_buildings\london_only'
$scriptDir=Join-Path $fRoot 'runner_scripts'
$ts=Get-Date -Format 'yyyyMMdd_HHmmss'
$out=Join-Path $statusDir 'LOCAL_SOLD_BUILDINGS_MULTI_FIELD_CONTRACT_V3_PICKUP_LATEST.txt'

New-Item -ItemType Directory -Force -Path $statusDir,$pendingDir,$runningDir,$doneDir,$failedDir,$fRoot,$scriptDir | Out-Null
Set-Location $repo
git fetch origin $branch | Out-Null
git reset --hard "origin/$branch" | Out-Null

$before=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*portable_queue_runner.ps1*' })
foreach($p in $before){ Stop-Process -Id $p.ProcessId -Force -ErrorAction Continue }
Start-Sleep -Seconds 8

$lockActions=@()
foreach($lf in @('.queue-lock','.single-runner.lock','queue.lock')){
  $p=Join-Path $queueRoot $lf
  if(Test-Path $p){
    $bak=$p + ".bak_multifield_v3_$ts"
    Move-Item $p $bak -Force -ErrorAction Continue
    $lockActions += "moved_lock: $p -> $bak"
  } else {
    $lockActions += "not_found: $p"
  }
}

$moveActions=@()
foreach($dir in @($pendingDir,$runningDir)){
  foreach($f in @(Get-ChildItem $dir -File -Force -ErrorAction Continue)){
    $n=$f.Name.ToLowerInvariant()
    if($n -like '*sold-buildings*' -or $n -like '*sold_buildings*'){
      $dest=Join-Path $failedDir ("old_sold_multifield_v3_${ts}_" + $f.Name)
      Move-Item $f.FullName $dest -Force -ErrorAction Continue
      $moveActions += "moved_old_sold_task: $($f.FullName) -> $dest"
    }
  }
}

$heldDir=Join-Path $queueRoot "held_non_sold_buildings_multifield_v3_$ts"
New-Item -ItemType Directory -Force -Path $heldDir | Out-Null
foreach($dir in @($pendingDir,$runningDir)){
  foreach($f in @(Get-ChildItem $dir -File -Force -ErrorAction Continue)){
    $n=$f.Name.ToLowerInvariant()
    $isSold=($n -like '*sold-buildings*' -or $n -like '*sold_buildings*')
    if(-not $isSold){
      $dest=Join-Path $heldDir ($dir.Split('\')[-1] + '_' + $f.Name)
      Move-Item $f.FullName $dest -Force -ErrorAction Continue
      $moveActions += "held_non_sold_task: $($f.FullName) -> $dest"
    }
  }
}

$ackScript=Join-Path $scriptDir "sold_buildings_runner_self_ack_multifield_v3_$ts.ps1"
$ackLines=@(
"`$ErrorActionPreference = 'Continue'",
"`$repo = '$repo'",
"`$branch = '$branch'",
"`$queueRoot = '$queueRoot'",
"`$statusDir = Join-Path `$repo 'docs\chatgpt_status'",
"`$fRoot = '$fRoot'",
"New-Item -ItemType Directory -Force -Path `$statusDir,`$fRoot | Out-Null",
"Set-Location `$repo",
"'ok' | Set-Content -Path (Join-Path `$fRoot '_runner_self_ack_multifield_v3_write_test.txt') -Encoding UTF8",
"`$runnerProcs = @(Get-CimInstance Win32_Process | Where-Object { `$_.CommandLine -like '*portable_queue_runner.ps1*' })",
"`$ack = @()",
"`$ack += 'status=AUTOMATION_RUNNER_PICKUP_ACK'",
"`$ack += ('created_at=' + (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'))",
"`$ack += 'page=auto-2.2-soldBuildings'",
"`$ack += 'ack_source=runner_self_report'",
"`$ack += ('active_branch=' + (git rev-parse --abbrev-ref HEAD))",
"`$ack += ('head=' + (git rev-parse HEAD))",
"`$ack += ('runner_process_count=' + `$runnerProcs.Count)",
"`$ack += ('runner_pids=' + (`$runnerProcs.ProcessId -join ','))",
"`$ack += ('single_runner_ok=' + (`$runnerProcs.Count -eq 1))",
"`$ack += 'queue_root=$queueRoot'",
"`$ack += ('f_drive_visible=' + (Test-Path 'F:\'))",
"`$ack += ('f_drive_writable=' + (Test-Path (Join-Path `$fRoot '_runner_self_ack_multifield_v3_write_test.txt')))",
"`$ack += 'next_required_action=run_london_only_source_gate_and_match'",
"`$ack -join [Environment]::NewLine | Set-Content -Path (Join-Path `$statusDir 'AUTOMATION_RUNNER_PICKUP_ACK_LATEST.txt') -Encoding UTF8",
"`$contract = @()",
"`$contract += 'status=SOLD_BUILDINGS_RUNNER_CONTRACT_INVENTORY'",
"`$contract += ('created_at=' + (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'))",
"`$contract += 'page=auto-2.2-soldBuildings'",
"`$contract += 'contract=task_json_script_alias_multifield_v3'",
"`$contract += 'queue_root=$queueRoot'",
"`$contract += 'script_aliases=script,script_path,ps1,path,command'",
"`$contract += 'script_format=multiline_ps1_v3'",
"`$contract -join [Environment]::NewLine | Set-Content -Path (Join-Path `$statusDir 'SOLD_BUILDINGS_RUNNER_CONTRACT_INVENTORY_LATEST.txt') -Encoding UTF8",
"git add docs/chatgpt_status/AUTOMATION_RUNNER_PICKUP_ACK_LATEST.txt docs/chatgpt_status/SOLD_BUILDINGS_RUNNER_CONTRACT_INVENTORY_LATEST.txt",
"git commit -m 'status: sold buildings true runner self pickup ack multifield v3' 2>`$null",
"git push origin HEAD:$branch"
)
$ackLines | Set-Content -Path $ackScript -Encoding UTF8

$taskId="sold-buildings-multifield-contract-v3-pickup-proof-$ts"
$taskPath=Join-Path $pendingDir "$taskId.task.json"
$task=[ordered]@{
  id=$taskId
  page='auto-2.2-soldBuildings'
  branch=$branch
  scope='Greater London only'
  script=$ackScript
  script_path=$ackScript
  ps1=$ackScript
  path=$ackScript
  command=$ackScript
  created_at=(Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
  task='Execute local PowerShell script using any supported script field alias and write true runner self ACK. Do not run source-gate, V2, LOCATION_MATCH, DB write, deploy, or PPD redownload.'
}
$task | ConvertTo-Json -Depth 8 | Set-Content $taskPath -Encoding UTF8
$task | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $queueRoot 'current-task.txt') -Encoding UTF8

Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$runner) -WorkingDirectory $bridge
Start-Sleep -Seconds 150

$after=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*portable_queue_runner.ps1*' })
'ok' | Set-Content -Path (Join-Path $fRoot '_multifield_v3_probe_write_test.txt') -Encoding UTF8

$pendingListing=Get-ChildItem $pendingDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String
$runningListing=Get-ChildItem $runningDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String
$doneListing=Get-ChildItem $doneDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String
$failedListing=Get-ChildItem $failedDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 120 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String

@"
status=LOCAL_SOLD_BUILDINGS_MULTI_FIELD_CONTRACT_V3_PICKUP
created_at=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
page=auto-2.2-soldBuildings
branch=$branch
active_branch=$(git rev-parse --abbrev-ref HEAD)
head=$(git rev-parse HEAD)
runner_process_count_before_stop=$($before.Count)
runner_process_count_after_restart=$($after.Count)
runner_pids_after_restart=$($after.ProcessId -join ',')
single_runner_ok=$($after.Count -eq 1)
queue_lock_exists=$(Test-Path (Join-Path $queueRoot '.queue-lock'))
single_runner_lock_exists=$(Test-Path (Join-Path $queueRoot '.single-runner.lock'))
f_drive_visible=$(Test-Path 'F:\')
f_drive_writable=$(Test-Path (Join-Path $fRoot '_multifield_v3_probe_write_test.txt'))
contract=script_alias_multifield_v3
script_aliases=script,script_path,ps1,path,command
script_path=$ackScript
new_clean_task=$taskPath

lock_actions_begin
$($lockActions -join "`r`n")
lock_actions_end

move_actions_begin
$($moveActions -join "`r`n")
move_actions_end

pending_listing_begin
$pendingListing
pending_listing_end

running_listing_begin
$runningListing
running_listing_end

done_listing_begin
$doneListing
done_listing_end

failed_listing_begin
$failedListing
failed_listing_end
"@ | Set-Content -Path $out -Encoding UTF8

git add docs/chatgpt_status/LOCAL_SOLD_BUILDINGS_MULTI_FIELD_CONTRACT_V3_PICKUP_LATEST.txt
git commit -m "status: sold buildings multi field contract v3 pickup proof" 2>$null
git push origin HEAD:$branch

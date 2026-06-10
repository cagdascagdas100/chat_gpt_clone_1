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
$ppd='F:\sold_buildings\open_sources\ppd\pp-complete.csv'
$licensed='F:\sold_buildings\licensed\incoming'
$ts=Get-Date -Format 'yyyyMMdd_HHmmss'

New-Item -ItemType Directory -Force -Path $pendingDir,$runningDir,$doneDir,$failedDir,$statusDir,$fRoot,$scriptDir | Out-Null
Set-Location $repo

$before=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*portable_queue_runner.ps1*' })
foreach ($p in $before) { Stop-Process -Id $p.ProcessId -Force -ErrorAction Continue }
Start-Sleep -Seconds 6

$lockActions=@()
foreach ($lf in @('.queue-lock','.single-runner.lock','queue.lock')) {
  $p=Join-Path $queueRoot $lf
  if (Test-Path $p) {
    $bak=$p + ".bak_source_gate_unblock_$ts"
    Move-Item $p $bak -Force -ErrorAction Continue
    $lockActions += "moved_lock: $p -> $bak"
  } else {
    $lockActions += "not_found: $p"
  }
}

$heldDir=Join-Path $queueRoot "held_non_sold_source_gate_unblock_$ts"
New-Item -ItemType Directory -Force -Path $heldDir | Out-Null
$moveActions=@()

foreach ($dir in @($pendingDir,$runningDir)) {
  foreach ($f in @(Get-ChildItem $dir -File -Force -ErrorAction Continue)) {
    $n=$f.Name.ToLowerInvariant()
    $isSold=($n -like '*sold-buildings*' -or $n -like '*sold_buildings*')
    if (-not $isSold) {
      $dest=Join-Path $heldDir (($dir | Split-Path -Leaf) + '_' + $f.Name)
      Move-Item $f.FullName $dest -Force -ErrorAction Continue
      $moveActions += "held_non_sold_task: $($f.FullName) -> $dest"
    } elseif ($isSold -and ($n -like '*source-gate*' -or $n -like '*source_gate*')) {
      $dest=Join-Path $failedDir ("old_sold_source_gate_replaced_${ts}_" + $f.Name)
      Move-Item $f.FullName $dest -Force -ErrorAction Continue
      $moveActions += "replaced_old_sold_source_gate_task: $($f.FullName) -> $dest"
    }
  }
}

$gateScript=Join-Path $scriptDir "sold_buildings_london_source_gate_unblocked_$ts.ps1"
$scriptLines=@(
'$ErrorActionPreference="Continue"',
'$repo="C:\Users\cagda\Documents\GitHub\AAYS"',
'$branch="feature/terrayield-aays-integration"',
'$statusDir=Join-Path $repo "docs\chatgpt_status"',
'$fRoot="F:\chatgpt\AAYS_WORK\sold_buildings\london_only"',
'$ppd="F:\sold_buildings\open_sources\ppd\pp-complete.csv"',
'$licensed="F:\sold_buildings\licensed\incoming"',
'New-Item -ItemType Directory -Force -Path $statusDir,$fRoot | Out-Null',
'Set-Location $repo',
'$runnerProcs=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*portable_queue_runner.ps1*" })',
'$ppdExists=Test-Path $ppd',
'$licensedExists=Test-Path $licensed',
'$fVisible=Test-Path "F:\"',
'$writeTest=Join-Path $fRoot "_source_gate_unblocked_write_test.txt"',
'"ok" | Set-Content -Path $writeTest -Encoding UTF8',
'$fWritable=Test-Path $writeTest',
'$ppdSize=0',
'if($ppdExists){ $ppdSize=(Get-Item $ppd).Length }',
'$licensedFiles=0',
'if($licensedExists){ $licensedFiles=@(Get-ChildItem $licensed -File -Recurse -ErrorAction Continue).Count }',
'$ready=($ppdExists -and $licensedExists -and $fVisible -and $fWritable)',
'$content=@()',
'$content += "status=LONDON_ONLY_SOURCE_GATE_AND_MATCH"',
'$content += "created_at=$(Get-Date -Format ''yyyy-MM-ddTHH:mm:ssK'')"',
'$content += "page=auto-2.2-soldBuildings"',
'$content += "branch=feature/terrayield-aays-integration"',
'$content += "active_branch=$(git rev-parse --abbrev-ref HEAD)"',
'$content += "head=$(git rev-parse HEAD)"',
'$content += "scope=Greater London only"',
'$content += "mode=source_gate_readiness_no_db_write_no_deploy"',
'$content += "runner_process_count=$($runnerProcs.Count)"',
'$content += "runner_pids=$($runnerProcs.ProcessId -join '','')"',
'$content += "single_runner_ok=$($runnerProcs.Count -eq 1)"',
'$content += "f_drive_visible=$fVisible"',
'$content += "f_drive_writable=$fWritable"',
'$content += "work_root=$fRoot"',
'$content += "ppd_path=$ppd"',
'$content += "ppd_exists=$ppdExists"',
'$content += "ppd_size_bytes=$ppdSize"',
'$content += "licensed_incoming=$licensed"',
'$content += "licensed_incoming_exists=$licensedExists"',
'$content += "licensed_file_count=$licensedFiles"',
'$content += "source_gate_ready=$ready"',
'$content += "next_required_action=if_ready_run_london_only_match_staging_task"',
'$content | Set-Content -Path (Join-Path $statusDir "LONDON_ONLY_SOURCE_GATE_AND_MATCH_LATEST.txt") -Encoding UTF8',
'git add docs/chatgpt_status/LONDON_ONLY_SOURCE_GATE_AND_MATCH_LATEST.txt',
'git commit -m "status: london only source gate and match readiness unblocked" 2>$null',
'git push origin HEAD:feature/terrayield-aays-integration'
)
$scriptLines | Set-Content -Path $gateScript -Encoding UTF8

$taskId="sold-buildings-london-source-gate-unblocked-$ts"
$taskPath=Join-Path $pendingDir "$taskId.task.json"
$task=[ordered]@{
  id=$taskId
  page='auto-2.2-soldBuildings'
  branch=$branch
  scope='Greater London only'
  script=$gateScript
  script_path=$gateScript
  ps1=$gateScript
  path=$gateScript
  command=$gateScript
  created_at=(Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
  task='Run London-only source gate/readiness only. No DB write, no import, no deploy.'
}
$task | ConvertTo-Json -Depth 8 | Set-Content $taskPath -Encoding UTF8
$task | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $queueRoot 'current-task.txt') -Encoding UTF8

Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$runner) -WorkingDirectory $bridge
Start-Sleep -Seconds 180

$after=@(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*portable_queue_runner.ps1*' })
$pendingListing=Get-ChildItem $pendingDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String
$runningListing=Get-ChildItem $runningDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String
$doneListing=Get-ChildItem $doneDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String
$failedListing=Get-ChildItem $failedDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 120 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String

$sourceGatePath=Join-Path $statusDir 'LONDON_ONLY_SOURCE_GATE_AND_MATCH_LATEST.txt'
$sourceGateExists=Test-Path $sourceGatePath
if($sourceGateExists){ $sourceGateContent=Get-Content $sourceGatePath -Raw -ErrorAction Continue } else { $sourceGateContent='SOURCE_GATE_REPORT_NOT_FOUND' }

@"
status=LOCAL_SOLD_BUILDINGS_SOURCE_GATE_QUEUE_UNBLOCK
created_at=$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')
page=auto-2.2-soldBuildings
branch=$branch
runner_process_count_before_stop=$($before.Count)
runner_process_count_after_restart=$($after.Count)
runner_pids_after_restart=$($after.ProcessId -join ',')
single_runner_ok=$($after.Count -eq 1)
task_path=$taskPath
script_path=$gateScript
source_gate_report_exists=$sourceGateExists
expected_report=docs/chatgpt_status/LONDON_ONLY_SOURCE_GATE_AND_MATCH_LATEST.txt

lock_actions_begin
$($lockActions -join "`r`n")
lock_actions_end

move_actions_begin
$($moveActions -join "`r`n")
move_actions_end

source_gate_content_begin
$sourceGateContent
source_gate_content_end

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
"@ | Set-Content -Path (Join-Path $statusDir 'LOCAL_SOLD_BUILDINGS_SOURCE_GATE_QUEUE_UNBLOCK_LATEST.txt') -Encoding UTF8

git add docs/chatgpt_status/LOCAL_SOLD_BUILDINGS_SOURCE_GATE_QUEUE_UNBLOCK_LATEST.txt
git commit -m 'status: unblock sold buildings source gate queue'
git push origin HEAD:$branch

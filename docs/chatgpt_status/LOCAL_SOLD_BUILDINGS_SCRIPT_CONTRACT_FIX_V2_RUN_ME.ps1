$ErrorActionPreference = 'Continue'

$repo = 'C:\Users\cagda\Documents\GitHub\AAYS'
$branch = 'feature/terrayield-aays-integration'
$page = 'auto-2.2-soldBuildings'
$bridge = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2'
$runner = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\portable_queue_runner.ps1'
$queueRoot = 'C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue'
$pendingDir = Join-Path $queueRoot 'pending'
$runningDir = Join-Path $queueRoot 'running'
$doneDir = Join-Path $queueRoot 'done'
$failedDir = Join-Path $queueRoot 'failed'
$statusDir = Join-Path $repo 'docs\chatgpt_status'
$fRoot = 'F:\chatgpt\AAYS_WORK\sold_buildings\london_only'
$scriptDir = Join-Path $fRoot 'runner_scripts'
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$out = Join-Path $statusDir 'LOCAL_SOLD_BUILDINGS_SCRIPT_CONTRACT_PICKUP_V2_LATEST.txt'

New-Item -ItemType Directory -Force -Path $statusDir,$pendingDir,$runningDir,$doneDir,$failedDir,$fRoot,$scriptDir | Out-Null

Set-Location $repo
git fetch origin $branch | Out-Null
git checkout $branch | Out-Null
git reset --hard "origin/$branch" | Out-Null

$before = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*portable_queue_runner.ps1*' })
foreach ($p in $before) { Stop-Process -Id $p.ProcessId -Force -ErrorAction Continue }
Start-Sleep -Seconds 8

$lockActions = @()
foreach ($lf in @('.queue-lock','.single-runner.lock','queue.lock')) {
    $lp = Join-Path $queueRoot $lf
    if (Test-Path $lp) {
        $bak = $lp + ".bak_script_contract_v2_$ts"
        Move-Item $lp $bak -Force -ErrorAction Continue
        $lockActions += "moved_lock: $lp -> $bak"
    } else {
        $lockActions += "not_found: $lp"
    }
}

$moveActions = @()
foreach ($dir in @($pendingDir,$runningDir)) {
    foreach ($f in @(Get-ChildItem $dir -File -Force -ErrorAction Continue)) {
        $n = $f.Name.ToLowerInvariant()
        if ($n -like '*sold-buildings*' -or $n -like '*sold_buildings*') {
            $dest = Join-Path $failedDir ("old_sold_script_contract_v2_${ts}_" + $f.Name)
            Move-Item $f.FullName $dest -Force -ErrorAction Continue
            $moveActions += "moved_old_sold_task: $($f.FullName) -> $dest"
        }
    }
}

$heldDir = Join-Path $queueRoot "held_non_sold_buildings_script_contract_v2_$ts"
New-Item -ItemType Directory -Force -Path $heldDir | Out-Null
foreach ($dir in @($pendingDir,$runningDir)) {
    foreach ($f in @(Get-ChildItem $dir -File -Force -ErrorAction Continue)) {
        $n = $f.Name.ToLowerInvariant()
        $isSold = ($n -like '*sold-buildings*' -or $n -like '*sold_buildings*')
        if (-not $isSold) {
            $dest = Join-Path $heldDir ($dir.Split('\')[-1] + '_' + $f.Name)
            Move-Item $f.FullName $dest -Force -ErrorAction Continue
            $moveActions += "held_non_sold_task: $($f.FullName) -> $dest"
        }
    }
}

$ackScript = Join-Path $scriptDir "sold_buildings_runner_self_ack_v2_$ts.ps1"
$ackLines = @(
    '$ErrorActionPreference = ''Continue''',
    '$repo = ''C:\Users\cagda\Documents\GitHub\AAYS''',
    '$branch = ''feature/terrayield-aays-integration''',
    '$page = ''auto-2.2-soldBuildings''',
    '$queueRoot = ''C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue''',
    '$statusDir = Join-Path $repo ''docs\chatgpt_status''',
    '$fRoot = ''F:\chatgpt\AAYS_WORK\sold_buildings\london_only''',
    'New-Item -ItemType Directory -Force -Path $statusDir,$fRoot | Out-Null',
    'Set-Location $repo',
    '''ok'' | Set-Content -Path (Join-Path $fRoot ''_runner_self_ack_v2_write_test.txt'') -Encoding UTF8',
    '$runnerProcs = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like ''*portable_queue_runner.ps1*'' })',
    '$ack = @()',
    '$ack += ''status=AUTOMATION_RUNNER_PICKUP_ACK''',
    '$ack += (''created_at='' + (Get-Date -Format ''yyyy-MM-ddTHH:mm:ssK''))',
    '$ack += ''page=auto-2.2-soldBuildings''',
    '$ack += ''ack_source=runner_self_report''',
    '$ack += (''active_branch='' + (git rev-parse --abbrev-ref HEAD))',
    '$ack += (''head='' + (git rev-parse HEAD))',
    '$ack += (''runner_process_count='' + $runnerProcs.Count)',
    '$ack += (''runner_pids='' + ($runnerProcs.ProcessId -join '',''))',
    '$ack += (''single_runner_ok='' + ($runnerProcs.Count -eq 1))',
    '$ack += ''queue_root=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue''',
    '$ack += (''f_drive_visible='' + (Test-Path ''F:\''))',
    '$ack += (''f_drive_writable='' + (Test-Path (Join-Path $fRoot ''_runner_self_ack_v2_write_test.txt'')))',
    '$ack += ''next_required_action=run_london_only_source_gate_and_match''',
    '$ack -join [Environment]::NewLine | Set-Content -Path (Join-Path $statusDir ''AUTOMATION_RUNNER_PICKUP_ACK_LATEST.txt'') -Encoding UTF8',
    '$bridge = @()',
    '$bridge += ''status=AUTOMATION_BRIDGE_HEALTH''',
    '$bridge += (''created_at='' + (Get-Date -Format ''yyyy-MM-ddTHH:mm:ssK''))',
    '$bridge += ''page=auto-2.2-soldBuildings''',
    '$bridge += ''bridge_root=C:\AAYS_GITHUB_BRIDGE_CLEAN2''',
    '$bridge += ''queue_root=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue''',
    '$bridge += ''runner_script=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-task-scripts\portable_queue_runner.ps1''',
    '$bridge += (''runner_process_count='' + $runnerProcs.Count)',
    '$bridge += (''single_runner_ok='' + ($runnerProcs.Count -eq 1))',
    '$bridge -join [Environment]::NewLine | Set-Content -Path (Join-Path $statusDir ''AUTOMATION_BRIDGE_HEALTH_LATEST.txt'') -Encoding UTF8',
    '$fd = @()',
    '$fd += ''status=LONDON_ONLY_F_DISK_POLICY''',
    '$fd += (''created_at='' + (Get-Date -Format ''yyyy-MM-ddTHH:mm:ssK''))',
    '$fd += ''page=auto-2.2-soldBuildings''',
    '$fd += ''scope=Greater London only''',
    '$fd += ''work_root=F:\chatgpt\AAYS_WORK\sold_buildings\london_only''',
    '$fd += (''f_drive_visible='' + (Test-Path ''F:\''))',
    '$fd += (''f_drive_writable='' + (Test-Path (Join-Path $fRoot ''_runner_self_ack_v2_write_test.txt'')))',
    '$fd -join [Environment]::NewLine | Set-Content -Path (Join-Path $statusDir ''LONDON_ONLY_F_DISK_POLICY_LATEST.txt'') -Encoding UTF8',
    '$contract = @()',
    '$contract += ''status=SOLD_BUILDINGS_RUNNER_CONTRACT_INVENTORY''',
    '$contract += (''created_at='' + (Get-Date -Format ''yyyy-MM-ddTHH:mm:ssK''))',
    '$contract += ''page=auto-2.2-soldBuildings''',
    '$contract += ''contract=task_json_requires_script_path''',
    '$contract += ''queue_root=C:\AAYS_GITHUB_BRIDGE_CLEAN2\ai-queue''',
    '$contract += ''script_field_required=True''',
    '$contract += ''script_format=multiline_ps1_v2''',
    '$contract -join [Environment]::NewLine | Set-Content -Path (Join-Path $statusDir ''SOLD_BUILDINGS_RUNNER_CONTRACT_INVENTORY_LATEST.txt'') -Encoding UTF8',
    'git add docs/chatgpt_status/AUTOMATION_RUNNER_PICKUP_ACK_LATEST.txt docs/chatgpt_status/AUTOMATION_BRIDGE_HEALTH_LATEST.txt docs/chatgpt_status/LONDON_ONLY_F_DISK_POLICY_LATEST.txt docs/chatgpt_status/SOLD_BUILDINGS_RUNNER_CONTRACT_INVENTORY_LATEST.txt',
    'git commit -m ''status: sold buildings true runner self pickup ack v2'' 2>$null',
    'git push origin HEAD:feature/terrayield-aays-integration'
)
Set-Content -Path $ackScript -Value $ackLines -Encoding UTF8

$taskId = "sold-buildings-script-contract-v2-pickup-proof-$ts"
$taskPath = Join-Path $pendingDir "$taskId.task.json"
$task = [ordered]@{
    id = $taskId
    page = 'auto-2.2-soldBuildings'
    branch = $branch
    scope = 'Greater London only'
    script = $ackScript
    created_at = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssK')
    task = 'Execute script field to write true runner self ACK v2 and refresh bridge/F-disk/contract reports. Do not run source-gate, V2, LOCATION_MATCH, DB write, deploy, or PPD redownload.'
}
$task | ConvertTo-Json -Depth 8 | Set-Content $taskPath -Encoding UTF8
$task | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $queueRoot 'current-task.txt') -Encoding UTF8

Start-Process powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$runner) -WorkingDirectory $bridge
Start-Sleep -Seconds 150

$after = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*portable_queue_runner.ps1*' })
'ok' | Set-Content -Path (Join-Path $fRoot '_script_contract_v2_probe_write_test.txt') -Encoding UTF8

$pendingListing = Get-ChildItem $pendingDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String
$runningListing = Get-ChildItem $runningDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String
$doneListing = Get-ChildItem $doneDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 80 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String
$failedListing = Get-ChildItem $failedDir -Force -ErrorAction Continue | Sort-Object LastWriteTime -Descending | Select-Object -First 120 Name,Length,LastWriteTime | Format-Table -AutoSize | Out-String

$report = @()
$report += 'status=LOCAL_SOLD_BUILDINGS_SCRIPT_CONTRACT_PICKUP_V2'
$report += ('created_at=' + (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK'))
$report += 'page=auto-2.2-soldBuildings'
$report += ('branch=' + $branch)
$report += ('active_branch=' + (git rev-parse --abbrev-ref HEAD))
$report += ('head=' + (git rev-parse HEAD))
$report += ('runner_process_count_before_stop=' + $before.Count)
$report += ('runner_process_count_after_restart=' + $after.Count)
$report += ('runner_pids_after_restart=' + ($after.ProcessId -join ','))
$report += ('single_runner_ok=' + ($after.Count -eq 1))
$report += ('queue_lock_exists=' + (Test-Path (Join-Path $queueRoot '.queue-lock')))
$report += ('single_runner_lock_exists=' + (Test-Path (Join-Path $queueRoot '.single-runner.lock')))
$report += ('f_drive_visible=' + (Test-Path 'F:\'))
$report += ('f_drive_writable=' + (Test-Path (Join-Path $fRoot '_script_contract_v2_probe_write_test.txt')))
$report += 'script_contract=task_json_requires_script_path'
$report += 'script_format=multiline_ps1_v2'
$report += ('script_path=' + $ackScript)
$report += ('new_clean_task=' + $taskPath)
$report += 'lock_actions_begin'
$report += ($lockActions -join [Environment]::NewLine)
$report += 'lock_actions_end'
$report += 'move_actions_begin'
$report += ($moveActions -join [Environment]::NewLine)
$report += 'move_actions_end'
$report += 'pending_listing_begin'
$report += $pendingListing
$report += 'pending_listing_end'
$report += 'running_listing_begin'
$report += $runningListing
$report += 'running_listing_end'
$report += 'done_listing_begin'
$report += $doneListing
$report += 'done_listing_end'
$report += 'failed_listing_begin'
$report += $failedListing
$report += 'failed_listing_end'
$report -join [Environment]::NewLine | Set-Content -Path $out -Encoding UTF8

git add docs/chatgpt_status/LOCAL_SOLD_BUILDINGS_SCRIPT_CONTRACT_PICKUP_V2_LATEST.txt
git commit -m 'status: sold buildings script contract pickup v2 proof' 2>$null
git push origin HEAD:$branch

'SOLD_BUILDINGS_SCRIPT_CONTRACT_V2_PICKUP_REPORT_PUSHED_OR_PUSH_ATTEMPTED'

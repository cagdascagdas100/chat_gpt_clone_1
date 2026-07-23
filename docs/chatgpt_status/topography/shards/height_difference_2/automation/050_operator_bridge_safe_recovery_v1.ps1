[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1'
$RepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$CanonicalBranch = 'codex/aays-single-runner-v5-20260706'
$BridgeBranch = 'operator/height_difference_2-recovery-bridge-v1'
$ReceiptPath = 'docs/chatgpt_status/topography/shards/height_difference_2/runner_outputs/018_chatgpt_bridge_recovery_latest.json'
$SlotId = 'height_difference_2'
$TaskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$AttemptId = 'height-difference-2-20260721-020'
$ContinuationKey = 'd6add1c8b2626cb73cf77f4f731ce74e326997b04c7615f481ca82ce2f635d44'
$RunId = [guid]::NewGuid().ToString('N')
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$StartedAt = (Get-Date).ToUniversalTime().ToString('o')
$HeartbeatPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json'
$LockPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
$CurrentTaskPath = Join-Path $RepoRoot 'ai-tasks\current-task.json'
$ExpectedOutputPath = Join-Path $RepoRoot 'docs\chatgpt_status\topography\shards\height_difference_2\runner_outputs\003_height_difference_2_canonical_export_official_sampling_latest.json'
$DevamPath = Join-Path $RepoRoot 'devam.ps1'
$script:GitExe = $null

function Now-Utc { (Get-Date).ToUniversalTime().ToString('o') }

function Read-JsonFile([string]$Path) {
    try {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    } catch { }
    return $null
}

function Write-Utf8Json([string]$Path, [object]$Value) {
    $parent = Split-Path -Parent $Path
    if ($parent -and -not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $json = ($Value | ConvertTo-Json -Depth 60) + "`n"
    [System.IO.File]::WriteAllText($Path, $json, [System.Text.UTF8Encoding]::new($false))
}

function Invoke-Git {
    param(
        [Parameter(Mandatory=$true)][string]$Cwd,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [switch]$AllowFailure
    )
    $output = & $script:GitExe -c "safe.directory=$Cwd" -C $Cwd @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $text = (($output | Out-String).Trim())
    if ($exitCode -ne 0 -and -not $AllowFailure) {
        throw "GIT_FAILED exit=$exitCode command=git $($Arguments -join ' ') detail=$text"
    }
    [pscustomobject]@{ ExitCode = $exitCode; Output = $text }
}

function Publish-ReceiptWithGh([object]$Payload, [string]$Phase) {
    $gh = Get-Command gh.exe -ErrorAction SilentlyContinue
    if (-not $gh) { $gh = Get-Command gh -ErrorAction SilentlyContinue }
    if (-not $gh) { return $false }

    & $gh.Source auth status -h github.com 1>$null 2>$null
    if ($LASTEXITCODE -ne 0) { return $false }

    $Payload.phase = $Phase
    $Payload.receipt_updated_at = Now-Utc
    $json = ($Payload | ConvertTo-Json -Depth 60) + "`n"
    $base64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($json))
    $endpoint = "repos/$RepoFullName/contents/$ReceiptPath"
    $encodedRef = [uri]::EscapeDataString($BridgeBranch)
    $sha = $null

    $existingRaw = & $gh.Source api "$endpoint`?ref=$encodedRef" 2>$null
    if ($LASTEXITCODE -eq 0 -and $existingRaw) {
        try { $sha = ([string]($existingRaw | ConvertFrom-Json).sha).Trim() } catch { $sha = $null }
    }

    $args = @(
        'api','--method','PUT',$endpoint,
        '-f',"message=chore(height_difference_2): update recovery receipt $RunId $Phase",
        '-f',"content=$base64",
        '-f',"branch=$BridgeBranch"
    )
    if ($sha) { $args += @('-f',"sha=$sha") }

    $putRaw = & $gh.Source @args 2>&1
    if ($LASTEXITCODE -ne 0) { return $false }
    return $true
}

function Publish-ReceiptWithGit([object]$Payload, [string]$Phase) {
    if (-not $script:GitExe -or -not (Test-Path -LiteralPath $RepoRoot -PathType Container)) { return $false }

    $Payload.phase = $Phase
    $Payload.receipt_updated_at = Now-Utc
    $worktreeRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("aays_hd2_bridge_" + [guid]::NewGuid().ToString('N'))
    try {
        Invoke-Git -Cwd $RepoRoot -Arguments @('fetch','--atomic','--prune','origin',$BridgeBranch) | Out-Null
        Invoke-Git -Cwd $RepoRoot -Arguments @('worktree','add','--detach',$worktreeRoot,"origin/$BridgeBranch") | Out-Null
        Invoke-Git -Cwd $worktreeRoot -Arguments @('config','user.name','AAYS F-host Recovery') | Out-Null
        Invoke-Git -Cwd $worktreeRoot -Arguments @('config','user.email','aays-recovery@users.noreply.github.com') | Out-Null

        $fullReceipt = Join-Path $worktreeRoot ($ReceiptPath -replace '/','\')
        Write-Utf8Json -Path $fullReceipt -Value $Payload
        if ((Get-Item -LiteralPath $fullReceipt).Length -ge 50331648) {
            throw 'RECEIPT_EXCEEDS_48_MIB'
        }

        Invoke-Git -Cwd $worktreeRoot -Arguments @('add','--',$ReceiptPath) | Out-Null
        $diff = Invoke-Git -Cwd $worktreeRoot -Arguments @('diff','--cached','--quiet') -AllowFailure
        if ($diff.ExitCode -eq 1) {
            Invoke-Git -Cwd $worktreeRoot -Arguments @('commit','-m',"chore(height_difference_2): update recovery receipt $RunId $Phase") | Out-Null
        } elseif ($diff.ExitCode -ne 0) {
            throw "RECEIPT_DIFF_CHECK_FAILED=$($diff.Output)"
        }

        for ($i = 1; $i -le 5; $i++) {
            $push = Invoke-Git -Cwd $worktreeRoot -Arguments @('push','origin',"HEAD:refs/heads/$BridgeBranch") -AllowFailure
            if ($push.ExitCode -eq 0) { return $true }
            Invoke-Git -Cwd $worktreeRoot -Arguments @('fetch','--atomic','origin',$BridgeBranch) | Out-Null
            $rebase = Invoke-Git -Cwd $worktreeRoot -Arguments @('rebase',"origin/$BridgeBranch") -AllowFailure
            if ($rebase.ExitCode -ne 0) {
                Invoke-Git -Cwd $worktreeRoot -Arguments @('rebase','--abort') -AllowFailure | Out-Null
                return $false
            }
        }
        return $false
    } catch {
        return $false
    } finally {
        if (Test-Path -LiteralPath $worktreeRoot) {
            Invoke-Git -Cwd $RepoRoot -Arguments @('worktree','remove','--force',$worktreeRoot) -AllowFailure | Out-Null
        }
    }
}

function Publish-Receipt([object]$Payload, [string]$Phase) {
    if (Publish-ReceiptWithGh -Payload $Payload -Phase $Phase) { return }
    if (Publish-ReceiptWithGit -Payload $Payload -Phase $Phase) { return }
    throw "GITHUB_RECEIPT_PUBLISH_FAILED phase=$Phase"
}

function Get-ProcessCommandLine([int]$ProcessId) {
    try { return [string](Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction Stop).CommandLine } catch { return '' }
}

function Get-CanonicalDaemons {
    @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $cmd = [string]$_.CommandLine
            $cmd -and $cmd -match 'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707' -and $cmd -like "*$RepoRoot*"
        }
    )
}

function Get-CanonicalWorkers {
    @(
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $cmd = [string]$_.CommandLine
            $cmd -and $cmd -match 'RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707' -and $cmd -like "*$RepoRoot*"
        }
    )
}

function Get-HeartbeatState {
    $heartbeat = Read-JsonFile $HeartbeatPath
    $time = $null
    if ($heartbeat) {
        foreach ($name in @('updated_at','heartbeat_at','checked_at','timestamp')) {
            $prop = $heartbeat.PSObject.Properties[$name]
            if ($prop -and $prop.Value) {
                try { $time = ([datetime]$prop.Value).ToUniversalTime(); break } catch { }
            }
        }
    }
    if (-not $time -and (Test-Path -LiteralPath $HeartbeatPath -PathType Leaf)) {
        $time = (Get-Item -LiteralPath $HeartbeatPath).LastWriteTimeUtc
    }
    $ageMinutes = if ($time) { ((Get-Date).ToUniversalTime() - $time).TotalMinutes } else { [double]::PositiveInfinity }
    [pscustomobject]@{
        Exists = [bool](Test-Path -LiteralPath $HeartbeatPath -PathType Leaf)
        Timestamp = if ($time) { $time.ToString('o') } else { $null }
        AgeMinutes = $ageMinutes
        Fresh = ($ageMinutes -le 20)
    }
}

function Test-TaskObserved {
    $current = Read-JsonFile $CurrentTaskPath
    $expected = Read-JsonFile $ExpectedOutputPath
    $currentTaskId = $null
    $currentStatus = $null
    if ($current) {
        foreach ($name in @('task_id','id')) {
            $p = $current.PSObject.Properties[$name]
            if ($p -and $p.Value) { $currentTaskId = [string]$p.Value; break }
        }
        foreach ($name in @('status','state')) {
            $p = $current.PSObject.Properties[$name]
            if ($p -and $p.Value) { $currentStatus = [string]$p.Value; break }
        }
    }
    $outputAttempt = $null
    $outputStatus = $null
    if ($expected) {
        $p = $expected.PSObject.Properties['attempt_id']; if ($p) { $outputAttempt = [string]$p.Value }
        foreach ($name in @('status','state','result')) {
            $q = $expected.PSObject.Properties[$name]
            if ($q -and $q.Value) { $outputStatus = [string]$q.Value; break }
        }
    }
    [pscustomobject]@{
        Observed = ($currentTaskId -eq $TaskId -or $outputAttempt -eq $AttemptId)
        CurrentTaskId = $currentTaskId
        CurrentStatus = $currentStatus
        OutputAttemptId = $outputAttempt
        OutputStatus = $outputStatus
        ExpectedOutputExists = [bool](Test-Path -LiteralPath $ExpectedOutputPath -PathType Leaf)
    }
}

$report = [ordered]@{
    schema_version = 2
    bridge_version = 'height_difference_2-safe-recovery-v2'
    run_id = $RunId
    phase = 'INITIALIZING'
    slot_id = $SlotId
    task_id = $TaskId
    attempt_id = $AttemptId
    continuation_key = $ContinuationKey
    canonical_branch = $CanonicalBranch
    bridge_branch = $BridgeBranch
    started_at = $StartedAt
    receipt_updated_at = $StartedAt
    result = 'STARTED'
    error = $null
    repo_root = $RepoRoot
    repo_exists = $false
    origin = $null
    branch_before = $null
    local_head_before = $null
    remote_head = $null
    local_head_after = $null
    dirty_before = $null
    dirty_entries = @()
    stash_created = $false
    stash_ref = $null
    stash_auto_restore_attempted = $false
    stash_dropped = $false
    backup_branch = $null
    daemon_count_before = $null
    worker_count_before = $null
    heartbeat_before = $null
    stale_daemon_stopped = $false
    stopped_daemon_pid = $null
    daemon_count_after = $null
    daemon_pid_after = $null
    heartbeat_after = $null
    runner_start_attempted = $false
    runner_entry_exit_code = $null
    runner_entry_output_tail = $null
    task_observed = $false
    current_task_id = $null
    current_task_status = $null
    expected_output_exists = $false
    expected_output_attempt_id = $null
    expected_output_status = $null
    reset_hard_used = $false
    force_push_used = $false
    data_deleted = $false
    new_runner_architecture_created = $false
    parallel_runner_started = $false
    large_file_limit_bytes = 50331648
    sha256_manifest_required_for_large_files = $true
    finished_at = $null
    final_ready = $false
}

try {
    $git = Get-Command git.exe -ErrorAction SilentlyContinue
    if (-not $git) { $git = Get-Command git -ErrorAction SilentlyContinue }
    if ($git) { $script:GitExe = $git.Source }

    Publish-Receipt -Payload $report -Phase 'STARTED'

    if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
        throw "CANONICAL_F_REPO_MISSING=$RepoRoot"
    }
    if (-not $script:GitExe) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
    if (-not (Test-Path -LiteralPath $DevamPath -PathType Leaf)) { throw "SAFE_RUNNER_ENTRY_MISSING=$DevamPath" }
    $report.repo_exists = $true

    $inside = Invoke-Git -Cwd $RepoRoot -Arguments @('rev-parse','--is-inside-work-tree')
    if ($inside.Output.Trim() -ne 'true') { throw 'CANONICAL_PATH_IS_NOT_GIT_WORKTREE' }

    $origin = (Invoke-Git -Cwd $RepoRoot -Arguments @('remote','get-url','origin')).Output.Trim()
    $report.origin = $origin
    if ($origin -notmatch 'cagdascagdas100/chat_gpt_clone_1') { throw "UNEXPECTED_ORIGIN=$origin" }

    $daemons = @(Get-CanonicalDaemons)
    $workers = @(Get-CanonicalWorkers)
    $heartbeat = Get-HeartbeatState
    $report.daemon_count_before = $daemons.Count
    $report.worker_count_before = $workers.Count
    $report.heartbeat_before = [ordered]@{ exists=$heartbeat.Exists; timestamp=$heartbeat.Timestamp; age_minutes=$heartbeat.AgeMinutes; fresh=$heartbeat.Fresh }

    if ($daemons.Count -gt 1 -or $workers.Count -gt 1) {
        throw "BLOCKED_MULTIPLE_CANONICAL_PROCESSES daemon_count=$($daemons.Count) worker_count=$($workers.Count)"
    }
    if ($daemons.Count -eq 0 -and $workers.Count -gt 0) {
        throw "BLOCKED_ORPHAN_CANONICAL_WORKER pid=$($workers[0].ProcessId)"
    }

    if ($daemons.Count -eq 1 -and -not $heartbeat.Fresh) {
        if ($workers.Count -gt 0) {
            throw "BLOCKED_STALE_DAEMON_WITH_ACTIVE_WORKER daemon_pid=$($daemons[0].ProcessId) worker_pid=$($workers[0].ProcessId)"
        }
        $lock = Read-JsonFile $LockPath
        if (-not $lock) { throw 'BLOCKED_STALE_DAEMON_LOCK_MISSING_OR_INVALID' }
        $lockPid = 0
        if ($lock.PSObject.Properties['supervisor_pid'] -and $lock.supervisor_pid) { $lockPid = [int]$lock.supervisor_pid }
        elseif ($lock.PSObject.Properties['pid'] -and $lock.pid) { $lockPid = [int]$lock.pid }
        $daemonPid = [int]$daemons[0].ProcessId
        $cmd = Get-ProcessCommandLine $daemonPid
        if ($lockPid -ne $daemonPid -or -not $cmd -or $cmd -notlike "*$RepoRoot*" -or $cmd -notmatch 'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707') {
            throw "BLOCKED_STALE_DAEMON_IDENTITY_MISMATCH lock_pid=$lockPid daemon_pid=$daemonPid"
        }
        Stop-Process -Id $daemonPid -ErrorAction Stop
        try { Wait-Process -Id $daemonPid -Timeout 20 -ErrorAction Stop } catch { throw "BLOCKED_STALE_DAEMON_DID_NOT_STOP pid=$daemonPid" }
        if (Get-Process -Id $daemonPid -ErrorAction SilentlyContinue) { throw "BLOCKED_STALE_DAEMON_STILL_ALIVE pid=$daemonPid" }
        if (Test-Path -LiteralPath $LockPath -PathType Leaf) { Remove-Item -LiteralPath $LockPath -Force }
        $report.stale_daemon_stopped = $true
        $report.stopped_daemon_pid = $daemonPid
        $daemons = @()
    }

    $report.branch_before = (Invoke-Git -Cwd $RepoRoot -Arguments @('rev-parse','--abbrev-ref','HEAD')).Output.Trim()
    $report.local_head_before = (Invoke-Git -Cwd $RepoRoot -Arguments @('rev-parse','HEAD')).Output.Trim()
    $statusText = (Invoke-Git -Cwd $RepoRoot -Arguments @('status','--porcelain=v1','-uall')).Output
    $dirtyEntries = @($statusText -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $report.dirty_before = ($dirtyEntries.Count -gt 0)
    $report.dirty_entries = $dirtyEntries

    Invoke-Git -Cwd $RepoRoot -Arguments @('fetch','--atomic','--prune','origin',$CanonicalBranch) | Out-Null
    $report.remote_head = (Invoke-Git -Cwd $RepoRoot -Arguments @('rev-parse',"origin/$CanonicalBranch")).Output.Trim()

    $liveFreshDaemon = (@(Get-CanonicalDaemons).Count -eq 1 -and (Get-HeartbeatState).Fresh)
    if ($liveFreshDaemon) {
        if ($report.branch_before -ne $CanonicalBranch -or $report.local_head_before -ne $report.remote_head -or $report.dirty_before) {
            $report.result = 'LIVE_SINGLE_RUNNER_PRESERVED_SYNC_DEFERRED'
        } else {
            $report.result = 'LIVE_SINGLE_RUNNER_PRESERVED_SYNCHRONIZED'
        }
    } else {
        if ($dirtyEntries.Count -gt 0) {
            $stashMessage = "height_difference_2 attempt020 safe recovery $Stamp"
            Invoke-Git -Cwd $RepoRoot -Arguments @('stash','push','--include-untracked','--message',$stashMessage) | Out-Null
            $stashRef = (Invoke-Git -Cwd $RepoRoot -Arguments @('rev-parse','--verify','refs/stash')).Output.Trim()
            if (-not $stashRef) { throw 'SAFE_STASH_REFERENCE_NOT_CREATED' }
            $report.stash_created = $true
            $report.stash_ref = $stashRef
            $postStash = (Invoke-Git -Cwd $RepoRoot -Arguments @('status','--porcelain=v1','-uall')).Output.Trim()
            if ($postStash) { throw "REPO_NOT_CLEAN_AFTER_SAFE_STASH=$postStash" }
        }

        $activeBranch = (Invoke-Git -Cwd $RepoRoot -Arguments @('rev-parse','--abbrev-ref','HEAD')).Output.Trim()
        if ($activeBranch -ne $CanonicalBranch) {
            $branchExists = Invoke-Git -Cwd $RepoRoot -Arguments @('show-ref','--verify','--quiet',"refs/heads/$CanonicalBranch") -AllowFailure
            if ($branchExists.ExitCode -eq 0) {
                Invoke-Git -Cwd $RepoRoot -Arguments @('switch',$CanonicalBranch) | Out-Null
            } else {
                Invoke-Git -Cwd $RepoRoot -Arguments @('switch','-c',$CanonicalBranch,'--track',"origin/$CanonicalBranch") | Out-Null
            }
        }

        $localHead = (Invoke-Git -Cwd $RepoRoot -Arguments @('rev-parse','HEAD')).Output.Trim()
        if ($localHead -ne $report.remote_head) {
            $ancestor = Invoke-Git -Cwd $RepoRoot -Arguments @('merge-base','--is-ancestor',$localHead,$report.remote_head) -AllowFailure
            if ($ancestor.ExitCode -eq 0) {
                Invoke-Git -Cwd $RepoRoot -Arguments @('merge','--ff-only',"origin/$CanonicalBranch") | Out-Null
            } else {
                $backupBranch = "recovery/$SlotId-pre-sync-$Stamp"
                Invoke-Git -Cwd $RepoRoot -Arguments @('branch','-m',$backupBranch) | Out-Null
                Invoke-Git -Cwd $RepoRoot -Arguments @('branch','--unset-upstream',$backupBranch) -AllowFailure | Out-Null
                Invoke-Git -Cwd $RepoRoot -Arguments @('switch','-c',$CanonicalBranch,'--track',"origin/$CanonicalBranch") | Out-Null
                $report.backup_branch = $backupBranch
            }
        }

        $report.local_head_after = (Invoke-Git -Cwd $RepoRoot -Arguments @('rev-parse','HEAD')).Output.Trim()
        if ($report.local_head_after -ne $report.remote_head) {
            throw "CANONICAL_SYNC_FAILED local=$($report.local_head_after) remote=$($report.remote_head)"
        }
        $clean = (Invoke-Git -Cwd $RepoRoot -Arguments @('status','--porcelain=v1','-uall')).Output.Trim()
        if ($clean) { throw "REPO_NOT_CLEAN_BEFORE_RUNNER_START=$clean" }

        $report.runner_start_attempted = $true
        $runnerOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $DevamPath 2>&1
        $runnerExit = $LASTEXITCODE
        $report.runner_entry_exit_code = $runnerExit
        $runnerText = (($runnerOutput | Out-String).Trim())
        if ($runnerText.Length -gt 4000) { $runnerText = $runnerText.Substring($runnerText.Length - 4000) }
        $report.runner_entry_output_tail = $runnerText
        if ($runnerExit -ne 0) { throw "SAFE_RUNNER_ENTRY_FAILED exit=$runnerExit" }
        $report.result = 'SAFE_RECOVERY_APPLIED_RUNNER_START_REQUESTED'
    }

    $deadline = (Get-Date).AddSeconds(90)
    do {
        Start-Sleep -Seconds 3
        $daemonsAfter = @(Get-CanonicalDaemons)
        $heartbeatAfter = Get-HeartbeatState
        if ($daemonsAfter.Count -gt 1) { throw "MULTIPLE_DAEMONS_AFTER_RECOVERY=$($daemonsAfter.Count)" }
    } while (($daemonsAfter.Count -ne 1 -or -not $heartbeatAfter.Fresh) -and (Get-Date) -lt $deadline)

    $report.daemon_count_after = $daemonsAfter.Count
    if ($daemonsAfter.Count -eq 1) { $report.daemon_pid_after = [int]$daemonsAfter[0].ProcessId }
    $report.heartbeat_after = [ordered]@{ exists=$heartbeatAfter.Exists; timestamp=$heartbeatAfter.Timestamp; age_minutes=$heartbeatAfter.AgeMinutes; fresh=$heartbeatAfter.Fresh }
    if ($daemonsAfter.Count -ne 1) { throw 'SINGLE_PERSISTENT_DAEMON_NOT_OBSERVED' }
    if (-not $heartbeatAfter.Fresh) { throw 'PERSISTENT_DAEMON_HEARTBEAT_NOT_FRESH' }

    $taskDeadline = (Get-Date).AddSeconds(180)
    do {
        $taskState = Test-TaskObserved
        if ($taskState.Observed) { break }
        Start-Sleep -Seconds 5
    } while ((Get-Date) -lt $taskDeadline)

    $report.task_observed = $taskState.Observed
    $report.current_task_id = $taskState.CurrentTaskId
    $report.current_task_status = $taskState.CurrentStatus
    $report.expected_output_exists = $taskState.ExpectedOutputExists
    $report.expected_output_attempt_id = $taskState.OutputAttemptId
    $report.expected_output_status = $taskState.OutputStatus

    if ($report.result -like 'LIVE_SINGLE_RUNNER*') {
        $report.result = if ($taskState.Observed) { 'LIVE_SINGLE_RUNNER_PRESERVED_TASK_OBSERVED' } else { 'LIVE_SINGLE_RUNNER_PRESERVED_WAITING_PICKUP' }
    } else {
        $report.result = if ($taskState.Observed) { 'RECOVERY_COMPLETE_SINGLE_RUNNER_TASK_OBSERVED' } else { 'RECOVERY_COMPLETE_SINGLE_RUNNER_WAITING_PICKUP' }
    }
} catch {
    $report.error = $_.Exception.Message
    if ($report.result -eq 'STARTED') { $report.result = 'STOPPED_SAFELY' }
} finally {
    $report.finished_at = Now-Utc
    try {
        Publish-Receipt -Payload $report -Phase 'FINAL'
        Write-Host "GITHUB_RECEIPT_PUBLISHED=true"
        Write-Host "BRIDGE_BRANCH=$BridgeBranch"
        Write-Host "RECEIPT_PATH=$ReceiptPath"
        Write-Host "RESULT=$($report.result)"
    } catch {
        Write-Host "GITHUB_RECEIPT_PUBLISHED=false"
        Write-Host "RECEIPT_ERROR=$($_.Exception.Message)"
        throw
    }
}

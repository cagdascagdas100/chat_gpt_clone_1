param([string]$Repo)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Slot = 'ready_to_sell_1'
$CanonicalBranch = 'codex/aays-single-runner-v5-20260706'
$ChannelBranch = 'recovery/ready_to_sell_1-command-channel'
$ReportRelativePath = 'docs/chatgpt_status/_shared/recovery_inbox/ready_to_sell_1/latest.json'
$FixedRemote = 'https://github.com/cagdascagdas100/chat_gpt_clone_1.git'
$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd-HHmmss')
$script:RepoRoot = $null
$script:Origin = $FixedRemote

$script:Report = [ordered]@{
    schema_version = 4
    protocol = 'AAYS_READY_TO_SELL_1_SAFE_REPAIR_V4'
    slot_id = $Slot
    started_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    completed_at_utc = $null
    state = 'STARTING'
    error = $null
    safety = [ordered]@{
        reset_hard_used = $false
        git_clean_used = $false
        force_push_used = $false
        other_slot_files_deleted = $false
        tracked_changes_preserved_in_stash = $false
        slot_untracked_changes_preserved_in_stash = $false
        local_ahead_commits_preserved_by_normal_push = $false
    }
    repository = [ordered]@{}
    runner = [ordered]@{
        before = @()
        stopped_duplicate_pids = @()
        after = @()
    }
    git = [ordered]@{}
}

function Protect-Text {
    param([AllowNull()][string]$Text)
    if ($null -eq $Text) { return '' }
    $safe = $Text
    if ($script:RepoRoot) {
        $safe = $safe -replace [regex]::Escape($script:RepoRoot), '<REPO>'
    }
    if ($HOME) {
        $safe = $safe -replace [regex]::Escape($HOME), '<HOME>'
    }
    $safe = [regex]::Replace($safe, '(?i)https://[^\s/@]+(?::[^\s/@]*)?@github\.com', 'https://github.com')
    $safe = [regex]::Replace($safe, '(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b', '<REDACTED_TOKEN>')
    return $safe
}

function Quote-Arg {
    param([AllowEmptyString()][string]$Value)
    if ($Value -notmatch '[\s"]') { return $Value }
    return '"' + ($Value -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

function Invoke-TimedProcess {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$Arguments,
        [int]$TimeoutSeconds = 60,
        [string]$WorkingDirectory
    )

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    $psi.Arguments = (($Arguments | ForEach-Object { Quote-Arg "$_" }) -join ' ')
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $psi
    if (-not $process.Start()) { throw "Process başlatılamadı: $FilePath" }

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $finished = $process.WaitForExit($TimeoutSeconds * 1000)
    $timedOut = -not $finished

    if ($timedOut) {
        try { $process.Kill() } catch {}
        try { $process.WaitForExit(5000) | Out-Null } catch {}
    }

    try { $stdout = $stdoutTask.Result } catch { $stdout = '' }
    try { $stderr = $stderrTask.Result } catch { $stderr = '' }
    $exitCode = if ($timedOut) { 124 } else { $process.ExitCode }
    $process.Dispose()

    return [ordered]@{
        exit_code = $exitCode
        timed_out = $timedOut
        timeout_seconds = $TimeoutSeconds
        stdout = Protect-Text $stdout.Trim()
        stderr = Protect-Text $stderr.Trim()
    }
}

function Invoke-Git {
    param(
        [Parameter(Mandatory)][string[]]$Arguments,
        [int]$TimeoutSeconds = 60,
        [string]$At
    )
    if (-not $At) { $At = $script:RepoRoot }
    return Invoke-TimedProcess -FilePath 'git.exe' -Arguments (@('-C', $At) + $Arguments) -TimeoutSeconds $TimeoutSeconds -WorkingDirectory $At
}

function Invoke-GitRequired {
    param(
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][string]$Label,
        [int]$TimeoutSeconds = 60,
        [string]$At
    )
    $result = Invoke-Git -Arguments $Arguments -TimeoutSeconds $TimeoutSeconds -At $At
    $script:Report.git[$Label] = $result
    if ([int]$result.exit_code -ne 0) {
        throw "$Label başarısız. timed_out=$($result.timed_out) stderr=$($result.stderr) stdout=$($result.stdout)"
    }
    return $result
}

function Find-RepositoryRoot {
    param([string]$Preferred)
    $candidates = @(
        $Preferred,
        (Get-Location).Path,
        $env:AAYS_REPO,
        (Join-Path $HOME 'chat_gpt_clone_1'),
        (Join-Path $HOME 'Desktop\chat_gpt_clone_1'),
        (Join-Path $HOME 'Documents\chat_gpt_clone_1'),
        'C:\AAYS\chat_gpt_clone_1',
        'D:\AAYS\chat_gpt_clone_1'
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique

    foreach ($candidate in $candidates) {
        $probe = Invoke-TimedProcess -FilePath 'git.exe' -Arguments @('-C', $candidate, 'rev-parse', '--show-toplevel') -TimeoutSeconds 15 -WorkingDirectory $candidate
        if ([int]$probe.exit_code -eq 0 -and $probe.stdout) {
            return $probe.stdout.Trim()
        }
    }
    throw 'chat_gpt_clone_1 Git deposu otomatik bulunamadı.'
}

function Get-RunnerProcesses {
    $pattern = '(?i)(?:(?:aays|terrayield).*(?:single[-_]?runner|runner\.(?:py|ps1|js))|(?:single[-_]?runner|runner\.(?:py|ps1|js)).*(?:aays|terrayield))'
    return @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -match $pattern } |
        ForEach-Object {
            [ordered]@{
                process_id = $_.ProcessId
                parent_process_id = $_.ParentProcessId
                name = $_.Name
                creation_date = "$($_.CreationDate)"
                command_line = Protect-Text $_.CommandLine
                normalized_command = (($_.CommandLine -replace '\s+', ' ').Trim().ToLowerInvariant())
            }
        })
}

function Publish-Report {
    param([string]$State, [AllowNull()][string]$ErrorText)

    $script:Report.state = $State
    $script:Report.error = Protect-Text $ErrorText
    $script:Report.completed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    $json = $script:Report | ConvertTo-Json -Depth 30

    if ([System.Text.Encoding]::UTF8.GetByteCount($json) -ge 45MB) {
        throw 'Recovery raporu 45 MiB sınırını aştı.'
    }

    $tempClone = Join-Path ([System.IO.Path]::GetTempPath()) ('aays-rts1-report-v4-' + [guid]::NewGuid().ToString('N'))
    try {
        $clone = Invoke-TimedProcess -FilePath 'git.exe' -Arguments @('clone', '--depth', '1', '--branch', $ChannelBranch, $script:Origin, $tempClone) -TimeoutSeconds 120
        if ([int]$clone.exit_code -ne 0 -and $script:Origin -ne $FixedRemote) {
            $clone = Invoke-TimedProcess -FilePath 'git.exe' -Arguments @('clone', '--depth', '1', '--branch', $ChannelBranch, $FixedRemote, $tempClone) -TimeoutSeconds 120
        }
        if ([int]$clone.exit_code -ne 0) {
            throw "Recovery dalı klonlanamadı: $($clone.stderr)"
        }

        $fullReportPath = Join-Path $tempClone ($ReportRelativePath -replace '/', '\')
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $fullReportPath) | Out-Null
        [System.IO.File]::WriteAllText($fullReportPath, $json, [System.Text.UTF8Encoding]::new($false))

        $null = Invoke-Git -At $tempClone -Arguments @('config', 'user.name', 'AAYS Recovery Channel') -TimeoutSeconds 10
        $null = Invoke-Git -At $tempClone -Arguments @('config', 'user.email', 'aays-recovery@users.noreply.github.com') -TimeoutSeconds 10
        $add = Invoke-Git -At $tempClone -Arguments @('add', '--', $ReportRelativePath) -TimeoutSeconds 20
        if ([int]$add.exit_code -ne 0) { throw "Rapor stage başarısız: $($add.stderr)" }

        $commit = Invoke-Git -At $tempClone -Arguments @('commit', '-m', "recovery($Slot): publish V4 state $State") -TimeoutSeconds 30
        if ([int]$commit.exit_code -ne 0) { throw "Rapor commit başarısız: $($commit.stderr)" }

        $pushed = $false
        for ($attempt = 1; $attempt -le 4 -and -not $pushed; $attempt++) {
            $push = Invoke-Git -At $tempClone -Arguments @('push', 'origin', "HEAD:refs/heads/$ChannelBranch") -TimeoutSeconds 90
            if ([int]$push.exit_code -eq 0) {
                $pushed = $true
                break
            }
            $fetch = Invoke-Git -At $tempClone -Arguments @('fetch', 'origin', $ChannelBranch) -TimeoutSeconds 60
            if ([int]$fetch.exit_code -ne 0) { continue }
            $rebase = Invoke-Git -At $tempClone -Arguments @('rebase', "origin/$ChannelBranch") -TimeoutSeconds 45
            if ([int]$rebase.exit_code -ne 0) { break }
        }
        if (-not $pushed) { throw 'Recovery raporu normal push ile yayımlanamadı.' }
    }
    finally {
        if (Test-Path -LiteralPath $tempClone) {
            Remove-Item -LiteralPath $tempClone -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

try {
    $script:RepoRoot = Find-RepositoryRoot -Preferred $Repo
    $script:Report.repository.root = '<REPO>'

    $origin = Invoke-GitRequired -Arguments @('remote', 'get-url', 'origin') -Label 'origin_read' -TimeoutSeconds 15
    $originText = $origin.stdout.Trim()
    if ($originText -notmatch 'cagdascagdas100[/:]chat_gpt_clone_1(?:\.git)?$') {
        throw "Beklenmeyen origin: $originText"
    }
    $script:Origin = $originText
    $script:Report.repository.origin = Protect-Text $originText

    Publish-Report -State 'STARTED' -ErrorText $null

    $runnersBefore = Get-RunnerProcesses
    $script:Report.runner.before = @($runnersBefore | ForEach-Object {
        $copy = [ordered]@{}
        foreach ($key in $_.Keys) { if ($key -ne 'normalized_command') { $copy[$key] = $_[$key] } }
        $copy
    })

    $duplicateGroups = @($runnersBefore | Group-Object normalized_command | Where-Object { $_.Count -gt 1 })
    foreach ($group in $duplicateGroups) {
        $ordered = @($group.Group | Sort-Object creation_date, process_id)
        foreach ($duplicate in @($ordered | Select-Object -Skip 1)) {
            Stop-Process -Id ([int]$duplicate.process_id) -ErrorAction Stop
            $script:Report.runner.stopped_duplicate_pids += [int]$duplicate.process_id
        }
    }
    $script:Report.runner.after = @(Get-RunnerProcesses | ForEach-Object {
        $copy = [ordered]@{}
        foreach ($key in $_.Keys) { if ($key -ne 'normalized_command') { $copy[$key] = $_[$key] } }
        $copy
    })

    $null = Invoke-GitRequired -Arguments @('fetch', '--prune', 'origin', "+refs/heads/$CanonicalBranch`:refs/remotes/origin/$CanonicalBranch") -Label 'fetch_canonical_before' -TimeoutSeconds 120

    $statusBefore = Invoke-Git -Arguments @('status', '--porcelain=v2', '--branch', '--untracked-files=no') -TimeoutSeconds 45
    $script:Report.git.status_before = $statusBefore

    $dirtyWorktree = Invoke-Git -Arguments @('diff', '--quiet', 'HEAD') -TimeoutSeconds 30
    $dirtyIndex = Invoke-Git -Arguments @('diff', '--cached', '--quiet', 'HEAD') -TimeoutSeconds 30
    $script:Report.git.diff_quiet_before = $dirtyWorktree
    $script:Report.git.cached_diff_quiet_before = $dirtyIndex

    if ([int]$dirtyWorktree.exit_code -eq 124 -or [int]$dirtyIndex.exit_code -eq 124) {
        throw 'İzlenen değişiklik kontrolü timeout verdi; güvenli stash doğrulanamadı.'
    }

    if ([int]$dirtyWorktree.exit_code -ne 0 -or [int]$dirtyIndex.exit_code -ne 0) {
        $stashMessage = "AAYS SYSTEM tracked recovery $Slot $Stamp"
        $stash = Invoke-GitRequired -Arguments @('stash', 'push', '-m', $stashMessage) -Label 'stash_tracked_changes' -TimeoutSeconds 180
        $stashSha = Invoke-GitRequired -Arguments @('rev-parse', 'refs/stash') -Label 'stash_tracked_sha' -TimeoutSeconds 15
        $script:Report.git.tracked_stash = [ordered]@{ message = $stashMessage; sha = $stashSha.stdout.Trim() }
        $script:Report.safety.tracked_changes_preserved_in_stash = $true
    }

    $slotStatus = Invoke-Git -Arguments @('status', '--porcelain=v1', '--untracked-files=all', '--', "docs/chatgpt_status/slots_21/$Slot") -TimeoutSeconds 45
    $script:Report.git.slot_status_after_tracked_stash = $slotStatus
    if ([int]$slotStatus.exit_code -eq 0 -and $slotStatus.stdout -match '(?m)^\?\? ') {
        $slotStashMessage = "AAYS $Slot untracked V53 recovery $Stamp"
        $slotStash = Invoke-GitRequired -Arguments @('stash', 'push', '-u', '-m', $slotStashMessage, '--', "docs/chatgpt_status/slots_21/$Slot") -Label 'stash_slot_untracked' -TimeoutSeconds 180
        $slotStashSha = Invoke-GitRequired -Arguments @('rev-parse', 'refs/stash') -Label 'stash_slot_untracked_sha' -TimeoutSeconds 15
        $script:Report.git.slot_untracked_stash = [ordered]@{ message = $slotStashMessage; sha = $slotStashSha.stdout.Trim() }
        $script:Report.safety.slot_untracked_changes_preserved_in_stash = $true
    }

    $cleanWorktree = Invoke-Git -Arguments @('diff', '--quiet', 'HEAD') -TimeoutSeconds 30
    $cleanIndex = Invoke-Git -Arguments @('diff', '--cached', '--quiet', 'HEAD') -TimeoutSeconds 30
    $script:Report.git.diff_quiet_after_stash = $cleanWorktree
    $script:Report.git.cached_diff_quiet_after_stash = $cleanIndex
    if ([int]$cleanWorktree.exit_code -ne 0 -or [int]$cleanIndex.exit_code -ne 0) {
        throw 'Stash sonrasında izlenen çalışma ağacı temiz değil.'
    }

    $null = Invoke-GitRequired -Arguments @('fetch', '--prune', 'origin', "+refs/heads/$CanonicalBranch`:refs/remotes/origin/$CanonicalBranch") -Label 'fetch_canonical_after_stash' -TimeoutSeconds 120
    $currentBranchResult = Invoke-GitRequired -Arguments @('branch', '--show-current') -Label 'current_branch' -TimeoutSeconds 15
    $currentBranch = $currentBranchResult.stdout.Trim()

    if ($currentBranch -eq $CanonicalBranch) {
        $counts = Invoke-GitRequired -Arguments @('rev-list', '--left-right', '--count', "HEAD...origin/$CanonicalBranch") -Label 'canonical_ahead_behind' -TimeoutSeconds 30
        $parts = $counts.stdout.Trim() -split '\s+'
        $ahead = [int]$parts[0]
        $behind = [int]$parts[1]

        if ($ahead -gt 0) {
            $backupBranch = "recovery/system-local-ahead-$Stamp"
            $null = Invoke-GitRequired -Arguments @('push', '-u', 'origin', "HEAD:refs/heads/$backupBranch") -Label 'push_local_ahead_backup' -TimeoutSeconds 180
            $script:Report.safety.local_ahead_commits_preserved_by_normal_push = $true
            $script:Report.git.local_ahead_backup_branch = $backupBranch
            $null = Invoke-GitRequired -Arguments @('branch', '-m', $backupBranch) -Label 'rename_local_canonical_to_backup' -TimeoutSeconds 30
            $null = Invoke-GitRequired -Arguments @('switch', '-c', $CanonicalBranch, '--track', "origin/$CanonicalBranch") -Label 'recreate_clean_canonical' -TimeoutSeconds 60
        }
        elseif ($behind -gt 0) {
            $null = Invoke-GitRequired -Arguments @('pull', '--ff-only', 'origin', $CanonicalBranch) -Label 'fast_forward_canonical' -TimeoutSeconds 120
        }
    }
    else {
        $localCanonical = Invoke-Git -Arguments @('show-ref', '--verify', '--quiet', "refs/heads/$CanonicalBranch") -TimeoutSeconds 15
        $script:Report.git.local_canonical_exists = $localCanonical
        if ([int]$localCanonical.exit_code -eq 0) {
            $localCounts = Invoke-GitRequired -Arguments @('rev-list', '--left-right', '--count', "$CanonicalBranch...origin/$CanonicalBranch") -Label 'local_canonical_ahead_behind' -TimeoutSeconds 30
            $localParts = $localCounts.stdout.Trim() -split '\s+'
            $localAhead = [int]$localParts[0]
            if ($localAhead -gt 0) {
                $backupBranch = "recovery/system-local-canonical-ahead-$Stamp"
                $null = Invoke-GitRequired -Arguments @('push', '-u', 'origin', "$CanonicalBranch`:refs/heads/$backupBranch") -Label 'push_local_canonical_backup' -TimeoutSeconds 180
                $script:Report.safety.local_ahead_commits_preserved_by_normal_push = $true
                $script:Report.git.local_ahead_backup_branch = $backupBranch
                $null = Invoke-GitRequired -Arguments @('branch', '-m', $CanonicalBranch, $backupBranch) -Label 'rename_existing_local_canonical' -TimeoutSeconds 30
                $null = Invoke-GitRequired -Arguments @('switch', '-c', $CanonicalBranch, '--track', "origin/$CanonicalBranch") -Label 'switch_new_clean_canonical' -TimeoutSeconds 60
            }
            else {
                $null = Invoke-GitRequired -Arguments @('switch', $CanonicalBranch) -Label 'switch_existing_canonical' -TimeoutSeconds 60
                $null = Invoke-GitRequired -Arguments @('pull', '--ff-only', 'origin', $CanonicalBranch) -Label 'fast_forward_existing_canonical' -TimeoutSeconds 120
            }
        }
        else {
            $null = Invoke-GitRequired -Arguments @('switch', '-c', $CanonicalBranch, '--track', "origin/$CanonicalBranch") -Label 'create_tracking_canonical' -TimeoutSeconds 60
        }
    }

    $localHead = Invoke-GitRequired -Arguments @('rev-parse', 'HEAD') -Label 'final_local_head' -TimeoutSeconds 15
    $remoteHead = Invoke-GitRequired -Arguments @('rev-parse', "origin/$CanonicalBranch") -Label 'final_remote_head' -TimeoutSeconds 15
    if ($localHead.stdout.Trim() -ne $remoteHead.stdout.Trim()) {
        throw "Yerel ve uzak canonical HEAD eşleşmiyor. local=$($localHead.stdout.Trim()) remote=$($remoteHead.stdout.Trim())"
    }

    $finalStatus = Invoke-GitRequired -Arguments @('status', '--porcelain=v2', '--branch', '--untracked-files=no') -Label 'final_tracked_status' -TimeoutSeconds 45
    $trackedLines = @($finalStatus.stdout -split "`r?`n" | Where-Object { $_ -match '^[12u] ' })
    $script:Report.repository.final_branch = $CanonicalBranch
    $script:Report.repository.final_head = $localHead.stdout.Trim()
    $script:Report.repository.final_tracked_change_count = $trackedLines.Count
    if ($trackedLines.Count -ne 0) {
        throw "Final izlenen çalışma ağacı temiz değil; count=$($trackedLines.Count)"
    }

    Publish-Report -State 'RESOLVED' -ErrorText $null
    Write-Host 'AAYS_READY_TO_SELL_1_V4_RESOLVED' -ForegroundColor Green
}
catch {
    $message = $_.Exception.Message
    try {
        Publish-Report -State 'BLOCKED' -ErrorText $message
        Write-Host 'AAYS_READY_TO_SELL_1_V4_BLOCKED_REPORTED' -ForegroundColor Yellow
    }
    catch {
        $publishError = $_.Exception.Message
        $fallback = Join-Path ([Environment]::GetFolderPath('MyDocuments')) "AAYS-ready_to_sell_1-v4-fallback-$Stamp.json"
        $script:Report.state = 'BLOCKED_REPORT_PUBLISH_FAILED'
        $script:Report.error = Protect-Text "$message | report_publish_error=$publishError"
        $script:Report.completed_at_utc = (Get-Date).ToUniversalTime().ToString('o')
        [System.IO.File]::WriteAllText($fallback, ($script:Report | ConvertTo-Json -Depth 30), [System.Text.UTF8Encoding]::new($false))
        Write-Host "AAYS_REPORT_PUBLISH_FAILED fallback=$fallback" -ForegroundColor Red
    }
    exit 1
}

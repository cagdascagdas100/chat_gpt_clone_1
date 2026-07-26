param(
    [string]$Repo
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Slot = 'ready_to_sell_1'
$CanonicalBranch = 'codex/aays-single-runner-v5-20260706'
$ChannelBranch = 'recovery/ready_to_sell_1-command-channel'
$ExpectedRepository = 'cagdascagdas100/chat_gpt_clone_1'
$ReportRelativePath = 'docs/chatgpt_status/_shared/recovery_inbox/ready_to_sell_1/latest.json'
$CollectedAtUtc = (Get-Date).ToUniversalTime().ToString('o')

function Get-RepoRoot {
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
        $top = & git -C $candidate rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and $top) {
            return (($top | Out-String).Trim())
        }
    }

    $entered = Read-Host 'chat_gpt_clone_1 repo klasorunun tam yolunu yazin'
    $top = & git -C $entered rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $top) {
        throw "Gecerli Git deposu bulunamadi: $entered"
    }
    return (($top | Out-String).Trim())
}

function Protect-Text {
    param([AllowNull()][string]$Text)
    if ($null -eq $Text) { return '' }
    $safe = $Text
    if ($script:Repo) { $safe = $safe -replace [regex]::Escape($script:Repo), '<REPO>' }
    if ($HOME) { $safe = $safe -replace [regex]::Escape($HOME), '<HOME>' }
    $safe = [regex]::Replace($safe, '(?i)https://[^\s/@]+(?::[^\s/@]*)?@github\.com', 'https://github.com')
    $safe = [regex]::Replace($safe, '(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{16,})\b', '<REDACTED_TOKEN>')
    $safe = [regex]::Replace($safe, '(?i)("(?:token|password|secret|authorization|cookie|api[_-]?key|access[_-]?token)"\s*:\s*")[^"]*(")', '$1<REDACTED>$2')
    return $safe
}

function Quote-ProcessArgument {
    param([AllowEmptyString()][string]$Value)
    if ($Value -notmatch '[\s"]') { return $Value }
    return '"' + ($Value -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
}

function Invoke-ProcessTimed {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$Arguments,
        [Parameter(Mandatory)][int]$TimeoutSeconds,
        [string]$WorkingDirectory
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.Arguments = (($Arguments | ForEach-Object { Quote-ProcessArgument "$_" }) -join ' ')
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    if ($WorkingDirectory) { $psi.WorkingDirectory = $WorkingDirectory }

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    $started = $process.Start()
    if (-not $started) { throw "Process baslatilamadi: $FilePath" }

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
        command = $FilePath + ' ' + (($Arguments | ForEach-Object { "$_" }) -join ' ')
        timeout_seconds = $TimeoutSeconds
        timed_out = $timedOut
        exit_code = $exitCode
        stdout = Protect-Text $stdout.Trim()
        stderr = Protect-Text $stderr.Trim()
    }
}

function Invoke-GitTimed {
    param(
        [Parameter(Mandatory)][string[]]$Arguments,
        [int]$TimeoutSeconds = 30,
        [string]$At
    )
    if (-not $At) { $At = $script:Repo }
    return Invoke-ProcessTimed -FilePath 'git.exe' -Arguments (@('-C', $At) + $Arguments) -TimeoutSeconds $TimeoutSeconds -WorkingDirectory $At
}

function Get-SafeFileRecord {
    param([string]$FullPath, [string]$RelativePath)
    $item = Get-Item -LiteralPath $FullPath
    $record = [ordered]@{
        path = ($RelativePath -replace '\\', '/')
        size_bytes = $item.Length
        last_write_utc = $item.LastWriteTimeUtc.ToString('o')
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $FullPath).Hash.ToLowerInvariant()
    }
    if ($item.Length -le 262144 -and $item.Extension -in @('.json', '.md', '.txt', '.log')) {
        try { $record.content = Protect-Text (Get-Content -LiteralPath $FullPath -Raw) }
        catch { $record.content_error = Protect-Text $_.Exception.Message }
    } else {
        $record.content_omitted = $true
    }
    return $record
}

$script:Repo = Get-RepoRoot -Preferred $Repo
$origin = Invoke-GitTimed -Arguments @('remote', 'get-url', 'origin') -TimeoutSeconds 15
if ($origin.exit_code -ne 0) { throw "origin okunamadi: $($origin.stderr)" }
if (($origin.stdout + $origin.stderr) -notmatch 'cagdascagdas100[/:]chat_gpt_clone_1(?:\.git)?$') {
    throw "Beklenmeyen origin: $($origin.stdout)"
}

$commands = [ordered]@{}
$commands.fetch_canonical = Invoke-GitTimed -Arguments @('fetch', '--prune', 'origin', "+refs/heads/$CanonicalBranch`:refs/remotes/origin/$CanonicalBranch") -TimeoutSeconds 90
$commands.current_branch = Invoke-GitTimed -Arguments @('branch', '--show-current') -TimeoutSeconds 10
$commands.local_head = Invoke-GitTimed -Arguments @('rev-parse', 'HEAD') -TimeoutSeconds 10
$commands.remote_head = Invoke-GitTimed -Arguments @('ls-remote', 'origin', "refs/heads/$CanonicalBranch") -TimeoutSeconds 30
$commands.ahead_behind = Invoke-GitTimed -Arguments @('rev-list', '--left-right', '--count', "HEAD...origin/$CanonicalBranch") -TimeoutSeconds 20
$commands.status_tracked = Invoke-GitTimed -Arguments @('status', '--porcelain=v2', '--branch', '--untracked-files=no') -TimeoutSeconds 40
$commands.diff_name_status = Invoke-GitTimed -Arguments @('diff', '--name-status', '--find-renames', 'HEAD') -TimeoutSeconds 40
$commands.cached_diff_name_status = Invoke-GitTimed -Arguments @('diff', '--cached', '--name-status', '--find-renames', 'HEAD') -TimeoutSeconds 30
$commands.diff_check = Invoke-GitTimed -Arguments @('diff', '--check', 'HEAD') -TimeoutSeconds 30
$commands.stashes = Invoke-GitTimed -Arguments @('stash', 'list', '--date=iso-strict') -TimeoutSeconds 15
$commands.worktrees = Invoke-GitTimed -Arguments @('worktree', 'list', '--porcelain') -TimeoutSeconds 15
$commands.count_objects = Invoke-GitTimed -Arguments @('count-objects', '-vH') -TimeoutSeconds 20
$commands.fsck_connectivity = Invoke-GitTimed -Arguments @('fsck', '--no-progress', '--connectivity-only') -TimeoutSeconds 45
$commands.slot_tracked_paths = Invoke-GitTimed -Arguments @('ls-files', '--', "docs/chatgpt_status/slots_21/$Slot", "*${Slot}*", '*v53*') -TimeoutSeconds 30

$gitCommonResult = Invoke-GitTimed -Arguments @('rev-parse', '--git-common-dir') -TimeoutSeconds 10
$locks = @()
if ($gitCommonResult.exit_code -eq 0 -and $gitCommonResult.stdout) {
    $gitCommon = $gitCommonResult.stdout.Trim()
    if (-not [System.IO.Path]::IsPathRooted($gitCommon)) { $gitCommon = Join-Path $script:Repo $gitCommon }
    if (Test-Path -LiteralPath $gitCommon) {
        $locks = @(Get-ChildItem -LiteralPath $gitCommon -File -Filter '*.lock' -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 100 |
            ForEach-Object {
                [ordered]@{
                    path = Protect-Text $_.FullName
                    size_bytes = $_.Length
                    created_utc = $_.CreationTimeUtc.ToString('o')
                    last_write_utc = $_.LastWriteTimeUtc.ToString('o')
                    age_seconds = [math]::Round(((Get-Date).ToUniversalTime() - $_.LastWriteTimeUtc).TotalSeconds, 1)
                }
            })
    }
}

$processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.CommandLine -and
        ($_.Name -match '^(git|git-lfs|python|pythonw|pwsh|powershell|node)(\.exe)?$') -and
        ($_.CommandLine -match '(?i)(aays|terrayield|ready_to_sell_1|runner|chat_gpt_clone_1)')
    } |
    Select-Object -First 100 |
    ForEach-Object {
        [ordered]@{
            process_id = $_.ProcessId
            parent_process_id = $_.ParentProcessId
            name = $_.Name
            creation_date = "$(($_.CreationDate))"
            command_line = Protect-Text $_.CommandLine
        }
    })

$evidencePaths = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$roots = @(
    "docs/chatgpt_status/slots_21/$Slot",
    'docs/chatgpt_status/_shared/manual_actions',
    'docs/chatgpt_status/_shared/recovery',
    'docs/chatgpt_status/_shared/queue',
    'docs/chatgpt_status/_shared/queues',
    'docs/chatgpt_status/_shared/current-task',
    'docs/chatgpt_status/_shared/current_tasks',
    'docs/chatgpt_status/_shared/ownership',
    'docs/chatgpt_status/_shared/heartbeats'
)
foreach ($root in $roots) {
    $fullRoot = Join-Path $script:Repo ($root -replace '/', '\')
    if (Test-Path -LiteralPath $fullRoot) {
        Get-ChildItem -LiteralPath $fullRoot -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $root -like "*/$Slot" -or $_.Name -match [regex]::Escape($Slot) -or $_.DirectoryName -match [regex]::Escape($Slot) } |
            Select-Object -First 150 |
            ForEach-Object {
                $relative = $_.FullName.Substring($script:Repo.Length).TrimStart('\', '/') -replace '\\', '/'
                [void]$evidencePaths.Add($relative)
            }
    }
}

$localEvidence = @()
foreach ($relative in ($evidencePaths | Sort-Object | Select-Object -First 250)) {
    $full = Join-Path $script:Repo ($relative -replace '/', '\')
    if (Test-Path -LiteralPath $full -PathType Leaf) {
        try { $localEvidence += Get-SafeFileRecord -FullPath $full -RelativePath $relative }
        catch { $localEvidence += [ordered]@{ path = $relative; error = Protect-Text $_.Exception.Message } }
    }
}

$timedOutCommands = @($commands.GetEnumerator() | Where-Object { $_.Value.timed_out } | ForEach-Object { $_.Key })
$statusLines = if ($commands.status_tracked.stdout) { @($commands.status_tracked.stdout -split "`r?`n" | Where-Object { $_ -match '^[12u] ' }) } else { @() }
$diffLines = if ($commands.diff_name_status.stdout) { @($commands.diff_name_status.stdout -split "`r?`n" | Where-Object { $_.Trim() }) } else { @() }

$report = [ordered]@{
    schema_version = 2
    protocol = 'AAYS_READY_TO_SELL_1_GITHUB_DIAGNOSTIC_CHANNEL_V2'
    collected_at_utc = $CollectedAtUtc
    slot_id = $Slot
    repository = $ExpectedRepository
    canonical_branch = $CanonicalBranch
    channel_branch = $ChannelBranch
    safety = [ordered]@{
        canonical_branch_modified = $false
        worktree_files_modified = $false
        reset_hard_used = $false
        git_clean_used = $false
        force_push_used = $false
        diagnostic_branch_only = $true
    }
    summary = [ordered]@{
        timed_out_commands = $timedOutCommands
        tracked_status_count = $statusLines.Count
        diff_name_status_count = $diffLines.Count
        lock_count = $locks.Count
        relevant_process_count = $processes.Count
        local_evidence_count = $localEvidence.Count
    }
    git = [ordered]@{
        origin = $origin
        commands = $commands
        locks = $locks
        relevant_processes = $processes
    }
    local_slot_evidence = $localEvidence
}

$json = $report | ConvertTo-Json -Depth 40
if ([System.Text.Encoding]::UTF8.GetByteCount($json) -ge 45MB) {
    $report.local_slot_evidence = @($localEvidence | ForEach-Object {
        $copy = [ordered]@{}
        foreach ($p in $_.Keys) { if ($p -ne 'content') { $copy[$p] = $_[$p] } }
        $copy
    })
    $json = $report | ConvertTo-Json -Depth 40
}

$tempClone = Join-Path ([System.IO.Path]::GetTempPath()) ('aays-rts1-channel-v2-' + [guid]::NewGuid().ToString('N'))
try {
    $clone = Invoke-ProcessTimed -FilePath 'git.exe' -Arguments @('clone', '--depth', '1', '--branch', $ChannelBranch, $origin.stdout.Trim(), $tempClone) -TimeoutSeconds 120
    if ($clone.exit_code -ne 0) { throw "Recovery channel clone basarisiz: $($clone.stderr)" }

    $reportPath = Join-Path $tempClone ($ReportRelativePath -replace '/', '\')
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $reportPath) | Out-Null
    [System.IO.File]::WriteAllText($reportPath, $json, [System.Text.UTF8Encoding]::new($false))

    $null = Invoke-GitTimed -At $tempClone -Arguments @('config', 'user.name', 'AAYS Recovery Channel') -TimeoutSeconds 10
    $null = Invoke-GitTimed -At $tempClone -Arguments @('config', 'user.email', 'aays-recovery@users.noreply.github.com') -TimeoutSeconds 10
    $add = Invoke-GitTimed -At $tempClone -Arguments @('add', '--', $ReportRelativePath) -TimeoutSeconds 20
    if ($add.exit_code -ne 0) { throw "Rapor stage basarisiz: $($add.stderr)" }
    $commit = Invoke-GitTimed -At $tempClone -Arguments @('commit', '-m', "diagnostics($Slot): publish timeout-safe snapshot") -TimeoutSeconds 30
    if ($commit.exit_code -ne 0) { throw "Rapor commit basarisiz: $($commit.stderr)" }

    $pushed = $false
    for ($attempt = 1; $attempt -le 3 -and -not $pushed; $attempt++) {
        $push = Invoke-GitTimed -At $tempClone -Arguments @('push', 'origin', "HEAD:refs/heads/$ChannelBranch") -TimeoutSeconds 90
        if ($push.exit_code -eq 0) { $pushed = $true; break }
        $fetch = Invoke-GitTimed -At $tempClone -Arguments @('fetch', 'origin', $ChannelBranch) -TimeoutSeconds 60
        if ($fetch.exit_code -ne 0) { continue }
        $rebase = Invoke-GitTimed -At $tempClone -Arguments @('rebase', "origin/$ChannelBranch") -TimeoutSeconds 30
        if ($rebase.exit_code -ne 0) { break }
    }
    if (-not $pushed) { throw 'Recovery channel normal push basarisiz.' }

    $readback = Invoke-GitTimed -Arguments @('ls-remote', 'origin', "refs/heads/$ChannelBranch") -TimeoutSeconds 30
    if ($readback.exit_code -ne 0) { throw "Uzak readback basarisiz: $($readback.stderr)" }

    Write-Host ''
    Write-Host 'AAYS_DIAGNOSTIC_V2_PUBLISHED' -ForegroundColor Green
    Write-Host "Branch: $ChannelBranch"
    Write-Host "Path:   $ReportRelativePath"
    Write-Host "Remote: $($readback.stdout)"
}
finally {
    if (Test-Path -LiteralPath $tempClone) {
        Remove-Item -LiteralPath $tempClone -Recurse -Force -ErrorAction SilentlyContinue
    }
}

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

function Get-RepositoryRoot {
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

$Repo = Get-RepositoryRoot -Preferred $Repo

function Protect-Text {
    param([AllowNull()][string]$Text)

    if ($null -eq $Text) { return '' }

    $safe = $Text
    if ($Repo) {
        $safe = $safe -replace [regex]::Escape($Repo), '<REPO>'
    }
    if ($HOME) {
        $safe = $safe -replace [regex]::Escape($HOME), '<HOME>'
    }

    $safe = [regex]::Replace(
        $safe,
        '(?i)https://[^\s/@]+(?::[^\s/@]*)?@github\.com',
        'https://github.com'
    )
    $safe = [regex]::Replace(
        $safe,
        '(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{16,})\b',
        '<REDACTED_TOKEN>'
    )
    $safe = [regex]::Replace(
        $safe,
        '(?i)("(?:token|password|secret|authorization|cookie|api[_-]?key|access[_-]?token)"\s*:\s*")[^"]*(")',
        '$1<REDACTED>$2'
    )

    return $safe
}

function Invoke-GitCapture {
    param(
        [Parameter(Mandatory)][string]$At,
        [Parameter(Mandatory)][string[]]$Arguments
    )

    $lines = & git -C $At @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $raw = (($lines | ForEach-Object { "$_" }) -join [Environment]::NewLine).Trim()

    return [ordered]@{
        exit_code = $exitCode
        output = Protect-Text $raw
        raw = $raw
        command = 'git ' + ($Arguments -join ' ')
    }
}

function Assert-GitSuccess {
    param(
        [Parameter(Mandatory)]$Result,
        [Parameter(Mandatory)][string]$Context
    )

    if ([int]$Result.exit_code -ne 0) {
        throw "$Context basarisiz oldu.`n$($Result.output)"
    }
}

function Get-StringSha256 {
    param([AllowEmptyString()][string]$Text)

    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function Get-SafeTextFileRecord {
    param(
        [Parameter(Mandatory)][string]$FullPath,
        [Parameter(Mandatory)][string]$RelativePath,
        [int64]$ContentLimitBytes = 131072
    )

    $item = Get-Item -LiteralPath $FullPath
    $record = [ordered]@{
        path = ($RelativePath -replace '\\', '/')
        size_bytes = $item.Length
        last_write_utc = $item.LastWriteTimeUtc.ToString('o')
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $FullPath).Hash.ToLowerInvariant()
    }

    if ($item.Length -le $ContentLimitBytes -and $item.Extension -in @('.json', '.md', '.txt', '.log')) {
        try {
            $record.content = Protect-Text (Get-Content -LiteralPath $FullPath -Raw)
        }
        catch {
            $record.content_error = Protect-Text $_.Exception.Message
        }
    }
    else {
        $record.content_omitted = $true
    }

    return $record
}

$originRaw = ((& git -C $Repo remote get-url origin 2>&1 | Out-String).Trim())
if ($LASTEXITCODE -ne 0) {
    throw 'origin uzak deposu okunamadi.'
}
if ($originRaw -notmatch 'cagdascagdas100[/:]chat_gpt_clone_1(?:\.git)?$') {
    throw "Beklenmeyen origin: $(Protect-Text $originRaw)"
}

$fetchCanonical = Invoke-GitCapture -At $Repo -Arguments @(
    'fetch', '--prune', 'origin',
    "+refs/heads/$CanonicalBranch`:refs/remotes/origin/$CanonicalBranch"
)
Assert-GitSuccess -Result $fetchCanonical -Context 'Kanonik branch fetch'

$fetchChannel = Invoke-GitCapture -At $Repo -Arguments @(
    'fetch', 'origin',
    "+refs/heads/$ChannelBranch`:refs/remotes/origin/$ChannelBranch"
)
Assert-GitSuccess -Result $fetchChannel -Context 'Recovery channel fetch'

$commands = [ordered]@{}
$commands.status = Invoke-GitCapture -At $Repo -Arguments @('status', '--porcelain=v2', '--branch', '--untracked-files=all')
$commands.current_branch = Invoke-GitCapture -At $Repo -Arguments @('branch', '--show-current')
$commands.local_head = Invoke-GitCapture -At $Repo -Arguments @('rev-parse', 'HEAD')
$commands.canonical_remote_head = Invoke-GitCapture -At $Repo -Arguments @('rev-parse', "origin/$CanonicalBranch")
$commands.channel_remote_head = Invoke-GitCapture -At $Repo -Arguments @('rev-parse', "origin/$ChannelBranch")
$commands.ahead_behind_canonical = Invoke-GitCapture -At $Repo -Arguments @('rev-list', '--left-right', '--count', "HEAD...origin/$CanonicalBranch")
$commands.diff_name_status = Invoke-GitCapture -At $Repo -Arguments @('diff', '--name-status', '--find-renames', 'HEAD')
$commands.cached_diff_name_status = Invoke-GitCapture -At $Repo -Arguments @('diff', '--cached', '--name-status', '--find-renames', 'HEAD')
$commands.diff_check = Invoke-GitCapture -At $Repo -Arguments @('diff', '--check', 'HEAD')
$commands.stashes = Invoke-GitCapture -At $Repo -Arguments @('stash', 'list', '--date=iso-strict')
$commands.worktrees = Invoke-GitCapture -At $Repo -Arguments @('worktree', 'list', '--porcelain')
$commands.submodules = Invoke-GitCapture -At $Repo -Arguments @('submodule', 'status', '--recursive')
$commands.object_store = Invoke-GitCapture -At $Repo -Arguments @('count-objects', '-vH')
$commands.connectivity = Invoke-GitCapture -At $Repo -Arguments @('fsck', '--no-progress', '--connectivity-only')
$commands.canonical_last_commit = Invoke-GitCapture -At $Repo -Arguments @('log', '-1', '--format=%H%n%cI%n%an%n%s', "origin/$CanonicalBranch")

$pathCommands = @(
    (Invoke-GitCapture -At $Repo -Arguments @('diff', '--name-only', 'HEAD')),
    (Invoke-GitCapture -At $Repo -Arguments @('diff', '--cached', '--name-only', 'HEAD')),
    (Invoke-GitCapture -At $Repo -Arguments @('ls-files', '--others', '--exclude-standard'))
)

$pathSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($pathCommand in $pathCommands) {
    if ([int]$pathCommand.exit_code -eq 0 -and $pathCommand.raw) {
        foreach ($line in ($pathCommand.raw -split "`r?`n")) {
            $clean = $line.Trim()
            if ($clean) { [void]$pathSet.Add(($clean -replace '\\', '/')) }
        }
    }
}

$changedInventory = @()
foreach ($relative in ($pathSet | Sort-Object)) {
    $full = Join-Path $Repo ($relative -replace '/', '\')
    $record = [ordered]@{
        path = $relative
        exists = Test-Path -LiteralPath $full
    }

    if (Test-Path -LiteralPath $full -PathType Leaf) {
        try {
            $item = Get-Item -LiteralPath $full
            $record.kind = 'file'
            $record.size_bytes = $item.Length
            $record.over_48_mib = ($item.Length -ge 48MB)
            $record.sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $full).Hash.ToLowerInvariant()
            $record.last_write_utc = $item.LastWriteTimeUtc.ToString('o')
        }
        catch {
            $record.hash_error = Protect-Text $_.Exception.Message
        }
    }
    elseif (Test-Path -LiteralPath $full -PathType Container) {
        $record.kind = 'directory'
    }
    else {
        $record.kind = 'deleted_or_missing'
    }

    $changedInventory += $record
}

$batchMaterial = (($changedInventory | Sort-Object path | ForEach-Object {
    $size = if ($_.Contains('size_bytes')) { $_.size_bytes } else { '' }
    $hash = if ($_.Contains('sha256')) { $_.sha256 } else { '' }
    "$($_.path)`t$($_.kind)`t$size`t$hash"
}) -join "`n")

$v53OrSlotInventory = @($changedInventory | Where-Object {
    $_.path -match '(?i)(ready_to_sell_1|v53)'
})
$v53Material = (($v53OrSlotInventory | Sort-Object path | ForEach-Object {
    $size = if ($_.Contains('size_bytes')) { $_.size_bytes } else { '' }
    $hash = if ($_.Contains('sha256')) { $_.sha256 } else { '' }
    "$($_.path)`t$($_.kind)`t$size`t$hash"
}) -join "`n")

$gitCommonResult = Invoke-GitCapture -At $Repo -Arguments @('rev-parse', '--git-common-dir')
$locks = @()
if ([int]$gitCommonResult.exit_code -eq 0 -and $gitCommonResult.raw) {
    $gitCommon = $gitCommonResult.raw
    if (-not [System.IO.Path]::IsPathRooted($gitCommon)) {
        $gitCommon = Join-Path $Repo $gitCommon
    }

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
            creation_date = if ($_.CreationDate) { ([Management.ManagementDateTimeConverter]::ToDateTime($_.CreationDate)).ToUniversalTime().ToString('o') } else { $null }
            command_line = Protect-Text $_.CommandLine
        }
    })

$ghAuth = $null
if (Get-Command gh -ErrorAction SilentlyContinue) {
    $ghLines = & gh auth status 2>&1
    $ghAuth = [ordered]@{
        exit_code = $LASTEXITCODE
        output = Protect-Text (($ghLines | ForEach-Object { "$_" }) -join [Environment]::NewLine)
    }
}

$slotRootRelative = "docs/chatgpt_status/slots_21/$Slot"
$sharedRootsRelative = @(
    'docs/chatgpt_status/_shared/manual_actions',
    'docs/chatgpt_status/_shared/recovery',
    'docs/chatgpt_status/_shared/queue',
    'docs/chatgpt_status/_shared/queues',
    'docs/chatgpt_status/_shared/current-task',
    'docs/chatgpt_status/_shared/current_tasks',
    'docs/chatgpt_status/_shared/ownership',
    'docs/chatgpt_status/_shared/heartbeats'
)

$localEvidencePaths = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$slotRootFull = Join-Path $Repo ($slotRootRelative -replace '/', '\')
if (Test-Path -LiteralPath $slotRootFull) {
    Get-ChildItem -LiteralPath $slotRootFull -File -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 200 |
        ForEach-Object {
            $relative = $_.FullName.Substring($Repo.Length).TrimStart('\', '/') -replace '\\', '/'
            [void]$localEvidencePaths.Add($relative)
        }
}

foreach ($sharedRelative in $sharedRootsRelative) {
    $sharedFull = Join-Path $Repo ($sharedRelative -replace '/', '\')
    if (Test-Path -LiteralPath $sharedFull) {
        Get-ChildItem -LiteralPath $sharedFull -File -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match [regex]::Escape($Slot) -or $_.DirectoryName -match [regex]::Escape($Slot) } |
            Select-Object -First 100 |
            ForEach-Object {
                $relative = $_.FullName.Substring($Repo.Length).TrimStart('\', '/') -replace '\\', '/'
                [void]$localEvidencePaths.Add($relative)
            }
    }
}

$localEvidence = @()
foreach ($relative in ($localEvidencePaths | Sort-Object | Select-Object -First 200)) {
    $full = Join-Path $Repo ($relative -replace '/', '\')
    if (Test-Path -LiteralPath $full -PathType Leaf) {
        try {
            $localEvidence += Get-SafeTextFileRecord -FullPath $full -RelativePath $relative
        }
        catch {
            $localEvidence += [ordered]@{
                path = $relative
                error = Protect-Text $_.Exception.Message
            }
        }
    }
}

$remoteRoots = @($slotRootRelative) + $sharedRootsRelative
$remoteTree = Invoke-GitCapture -At $Repo -Arguments (@('ls-tree', '-r', '--name-only', "origin/$CanonicalBranch", '--') + $remoteRoots)
$remoteEvidence = @()
if ([int]$remoteTree.exit_code -eq 0 -and $remoteTree.raw) {
    $remotePaths = @($remoteTree.raw -split "`r?`n" | Where-Object {
        $_ -like "$slotRootRelative/*" -or $_ -match [regex]::Escape($Slot)
    } | Sort-Object -Unique | Select-Object -First 200)

    foreach ($path in $remotePaths) {
        $show = Invoke-GitCapture -At $Repo -Arguments @('show', "origin/${CanonicalBranch}:$path")
        $record = [ordered]@{
            path = $path
            exit_code = $show.exit_code
        }
        if ([int]$show.exit_code -eq 0) {
            $bytes = [System.Text.Encoding]::UTF8.GetByteCount($show.raw)
            $record.size_bytes = $bytes
            $record.sha256 = Get-StringSha256 $show.raw
            if ($bytes -le 131072 -and $path -match '(?i)\.(json|md|txt|log)$') {
                $record.content = Protect-Text $show.raw
            }
            else {
                $record.content_omitted = $true
            }
        }
        else {
            $record.error = $show.output
        }
        $remoteEvidence += $record
    }
}

$report = [ordered]@{
    schema_version = 1
    protocol = 'AAYS_READY_TO_SELL_1_GITHUB_DIAGNOSTIC_CHANNEL_V1'
    slot_id = $Slot
    collected_at_utc = $CollectedAtUtc
    repository = $ExpectedRepository
    canonical_branch = $CanonicalBranch
    channel_branch = $ChannelBranch
    expected_problem_codes = @(
        'NO_SAFE_AUTOMATIC_REPAIR_FOR_BLOCKER',
        'GIT_PATH_LIST_TIMEOUT_120S',
        'PICKUP_TIMEOUT_WAITING_SHARED_COORDINATOR_CLEAN_REMOTE_HEAD_V53_RERUN',
        'STALE_V53_LOCAL_DATA_REPORT_REJECTED',
        'LOCAL_BATCH_SHA_AND_COUNT_MISMATCH_MUST_BE_CLEANED',
        'V53_BROWSER_DOM_JSON_AND_MARKDOWN_REPORTS_NOT_YET_ACCEPTED',
        'WAITING_GIT_CLEAN_PUBLISHER'
    )
    safety = [ordered]@{
        canonical_branch_modified = $false
        worktree_files_modified = $false
        stash_created = $false
        reset_hard_used = $false
        git_clean_used = $false
        force_push_used = $false
        diagnostic_branch_only = $true
    }
    git = [ordered]@{
        origin = Protect-Text $originRaw
        commands = $commands
        gh_auth = $ghAuth
        locks = $locks
        relevant_processes = $processes
    }
    changed_files = [ordered]@{
        count = $changedInventory.Count
        batch_sha256 = Get-StringSha256 $batchMaterial
        over_48_mib_count = @($changedInventory | Where-Object { $_.Contains('over_48_mib') -and $_.over_48_mib }).Count
        inventory = $changedInventory
    }
    ready_to_sell_1_or_v53_batch = [ordered]@{
        count = $v53OrSlotInventory.Count
        batch_sha256 = Get-StringSha256 $v53Material
        inventory = $v53OrSlotInventory
    }
    local_slot_evidence = $localEvidence
    canonical_remote_slot_evidence = [ordered]@{
        tree_command = $remoteTree
        files = $remoteEvidence
    }
}

$json = $report | ConvertTo-Json -Depth 40
$jsonBytes = [System.Text.Encoding]::UTF8.GetByteCount($json)
if ($jsonBytes -ge 48MB) {
    throw "Teshis raporu 48 MiB sinirini asti: $jsonBytes bayt"
}

$tempWorktree = Join-Path ([System.IO.Path]::GetTempPath()) ("aays-ready-to-sell-1-channel-" + [guid]::NewGuid().ToString('N'))
$reportFullPath = $null
$pushSucceeded = $false

try {
    $addWorktree = Invoke-GitCapture -At $Repo -Arguments @('worktree', 'add', '--detach', $tempWorktree, "origin/$ChannelBranch")
    Assert-GitSuccess -Result $addWorktree -Context 'Izole recovery worktree olusturma'

    $reportFullPath = Join-Path $tempWorktree ($ReportRelativePath -replace '/', '\')
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $reportFullPath) | Out-Null
    [System.IO.File]::WriteAllText($reportFullPath, $json, [System.Text.UTF8Encoding]::new($false))

    $add = Invoke-GitCapture -At $tempWorktree -Arguments @('add', '--', $ReportRelativePath)
    Assert-GitSuccess -Result $add -Context 'Teshis raporunu stage etme'

    $commit = Invoke-GitCapture -At $tempWorktree -Arguments @(
        'commit', '-m', "diagnostics($Slot): publish safe recovery snapshot"
    )
    Assert-GitSuccess -Result $commit -Context 'Teshis commit'

    $localDiagnosticHead = (Invoke-GitCapture -At $tempWorktree -Arguments @('rev-parse', 'HEAD'))
    Assert-GitSuccess -Result $localDiagnosticHead -Context 'Teshis commit SHA okuma'

    $push = Invoke-GitCapture -At $tempWorktree -Arguments @(
        'push', 'origin', "HEAD:refs/heads/$ChannelBranch"
    )
    Assert-GitSuccess -Result $push -Context 'Recovery channel push'

    $readback = Invoke-GitCapture -At $Repo -Arguments @('ls-remote', 'origin', "refs/heads/$ChannelBranch")
    Assert-GitSuccess -Result $readback -Context 'Uzak SHA readback'

    $remoteDiagnosticHead = (($readback.raw -split '\s+')[0]).Trim()
    if ($remoteDiagnosticHead -ne $localDiagnosticHead.raw.Trim()) {
        throw "Uzak readback eslesmedi. Yerel=$($localDiagnosticHead.raw.Trim()) Uzak=$remoteDiagnosticHead"
    }

    $pushSucceeded = $true
    Write-Host ''
    Write-Host 'AAYS_DIAGNOSTIC_PUBLISHED' -ForegroundColor Green
    Write-Host "Branch: $ChannelBranch"
    Write-Host "Path:   $ReportRelativePath"
    Write-Host "SHA:    $remoteDiagnosticHead"
}
finally {
    if (Test-Path -LiteralPath $tempWorktree) {
        $remove = Invoke-GitCapture -At $Repo -Arguments @('worktree', 'remove', $tempWorktree)
        if ([int]$remove.exit_code -ne 0) {
            Write-Warning "Gecici worktree otomatik kaldirilamadi: $(Protect-Text $tempWorktree)"
        }
        else {
            [void](Invoke-GitCapture -At $Repo -Arguments @('worktree', 'prune'))
        }
    }
}

if (-not $pushSucceeded) {
    throw 'Teshis GitHub kanalina yayimlanamadi.'
}

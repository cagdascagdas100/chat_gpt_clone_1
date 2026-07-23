[CmdletBinding()]
param()

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$RepoFullName = 'cagdascagdas100/chat_gpt_clone_1'
$ProbeBranch = 'operator/internet-access-3-recovery-probe-20260723-6d92b4'
$ProbeScriptRel = 'docs/chatgpt_status/_shared/operator_tools/internet_access_3_recovery_probe_v2.ps1'
$ProbeReportRel = 'docs/chatgpt_status/_shared/operator_reports/internet_access_3/recovery_probe_latest.json'
$BootstrapReportRel = 'docs/chatgpt_status/_shared/operator_reports/internet_access_3/bootstrap_latest.json'
$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')

function Now-Utc { return (Get-Date).ToUniversalTime().ToString('o') }
function Sanitize-Text([string]$Text) {
    if ($null -eq $Text) { return '' }
    $Result = $Text -replace '(?i)(ghp_|github_pat_)[A-Za-z0-9_]+', '[REDACTED_TOKEN]'
    $Result = $Result -replace '(?i)(Authorization:\s*Bearer\s+)\S+', '$1[REDACTED]'
    $Result = $Result -replace '(https?://)[^/@\s]+:[^/@\s]+@', '$1[REDACTED]@'
    return $Result
}
function Ensure-Directory([string]$Path) {
    if ($Path -and -not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}
function Invoke-GitBounded {
    param([string]$WorkingDirectory,[string[]]$Arguments,[int]$TimeoutSeconds=300)
    $OutFile=[IO.Path]::GetTempFileName(); $ErrFile=[IO.Path]::GetTempFileName()
    try {
        $Full=@('-c',"safe.directory=$WorkingDirectory",'-C',$WorkingDirectory)+$Arguments
        $P=Start-Process -FilePath $script:GitExe -ArgumentList $Full -WorkingDirectory $WorkingDirectory -PassThru -NoNewWindow -RedirectStandardOutput $OutFile -RedirectStandardError $ErrFile
        try { Wait-Process -Id $P.Id -Timeout $TimeoutSeconds -ErrorAction Stop }
        catch { Stop-Process -Id $P.Id -Force -ErrorAction SilentlyContinue; throw "GIT_TIMEOUT=$($Arguments -join ' ')" }
        $P.Refresh()
        return [pscustomobject]@{
            Code=[int]$P.ExitCode
            StdOut=[string](Get-Content -LiteralPath $OutFile -Raw -ErrorAction SilentlyContinue)
            StdErr=[string](Get-Content -LiteralPath $ErrFile -Raw -ErrorAction SilentlyContinue)
        }
    } finally {
        Remove-Item -LiteralPath $OutFile,$ErrFile -Force -ErrorAction SilentlyContinue
    }
}
function Assert-GitSuccess($Result,[string]$Code) {
    if ($Result.Code -ne 0) {
        throw "$Code=$(Sanitize-Text (($Result.StdErr+' '+$Result.StdOut).Trim()))"
    }
}
function Publish-BootstrapReport {
    param([string]$RepoRoot,[hashtable]$Payload)
    $Fetch=Invoke-GitBounded $RepoRoot @('fetch','--no-tags','origin',"+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch") 300
    Assert-GitSuccess $Fetch 'BOOTSTRAP_REPORT_FETCH_FAILED'

    $PublishRoot=Join-Path (Split-Path -Parent $RepoRoot) "AAYS_OPERATOR_BOOTSTRAP_WORKTREE_$RunId"
    $Add=Invoke-GitBounded $RepoRoot @('worktree','add','--detach',$PublishRoot,"origin/$ProbeBranch") 300
    Assert-GitSuccess $Add 'BOOTSTRAP_WORKTREE_ADD_FAILED'

    $null=Invoke-GitBounded $PublishRoot @('config','user.name','AAYS Operator Bootstrap') 60
    $null=Invoke-GitBounded $PublishRoot @('config','user.email','aays-operator@users.noreply.github.com') 60

    $ReportPath=Join-Path $PublishRoot ($BootstrapReportRel -replace '/','\')
    Ensure-Directory (Split-Path -Parent $ReportPath)
    [IO.File]::WriteAllText($ReportPath,(($Payload|ConvertTo-Json -Depth 20)+"`n"),[Text.UTF8Encoding]::new($false))
    if ((Get-Item -LiteralPath $ReportPath).Length -ge 48MB) { throw 'BOOTSTRAP_REPORT_EXCEEDS_48_MIB' }

    Assert-GitSuccess (Invoke-GitBounded $PublishRoot @('add','--',$BootstrapReportRel) 120) 'BOOTSTRAP_REPORT_STAGE_FAILED'
    $Commit=Invoke-GitBounded $PublishRoot @('commit','-m',"AAYS internet_access_3 bootstrap report $RunId") 120
    if (($Commit.Code -ne 0) -and (($Commit.StdOut+$Commit.StdErr) -notmatch 'nothing to commit')) {
        throw "BOOTSTRAP_REPORT_COMMIT_FAILED=$(Sanitize-Text (($Commit.StdErr+$Commit.StdOut).Trim()))"
    }

    $Pushed=$false
    for ($I=1;$I -le 5;$I++) {
        $Push=Invoke-GitBounded $PublishRoot @('push','origin',"HEAD:refs/heads/$ProbeBranch") 300
        if ($Push.Code -eq 0) { $Pushed=$true; break }
        $Refresh=Invoke-GitBounded $PublishRoot @('fetch','--no-tags','origin',"+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch") 300
        if ($Refresh.Code -ne 0) { continue }
        $Merge=Invoke-GitBounded $PublishRoot @('merge','--no-edit',"origin/$ProbeBranch") 180
        if ($Merge.Code -ne 0) {
            $null=Invoke-GitBounded $PublishRoot @('merge','--abort') 60
            break
        }
    }
    if (-not $Pushed) { throw 'BOOTSTRAP_REPORT_PUSH_FAILED' }
}

$RepoCandidates=@()
foreach ($Drive in @(Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
    $RepoCandidates += Join-Path $Drive.Root 'TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
    $RepoCandidates += Join-Path $Drive.Root 'TerraYield_AAYS_Portable\runner_system\adaptive_v2\publisher'
}
$RepoRoot=$null
foreach ($Candidate in $RepoCandidates) {
    if ((Test-Path -LiteralPath (Join-Path $Candidate '.git')) -and (Test-Path -LiteralPath (Join-Path $Candidate 'docs\chatgpt_status\_shared'))) {
        $RepoRoot=[IO.Path]::GetFullPath($Candidate).TrimEnd('\')
        break
    }
}
if (-not $RepoRoot) { throw 'AAYS_CANONICAL_REPOSITORY_NOT_FOUND' }

$GitCommand=Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $GitCommand) { $GitCommand=Get-Command git -ErrorAction SilentlyContinue }
if (-not $GitCommand) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$script:GitExe=$GitCommand.Source

$ProbeExitCode=127
$ProbeOutput=''
$ProbeStartedAt=Now-Utc
$FatalError=$null
try {
    $Fetch=Invoke-GitBounded $RepoRoot @('fetch','--no-tags','origin',"+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch") 300
    Assert-GitSuccess $Fetch 'PROBE_BRANCH_FETCH_FAILED'
    $Show=Invoke-GitBounded $RepoRoot @('show',"origin/$ProbeBranch`:$ProbeScriptRel") 120
    Assert-GitSuccess $Show 'PROBE_SCRIPT_READ_FAILED'

    $LocalProbe=Join-Path $env:TEMP "aays_internet_access_3_probe_$RunId.ps1"
    [IO.File]::WriteAllText($LocalProbe,$Show.StdOut,[Text.UTF8Encoding]::new($false))
    $OutFile=[IO.Path]::GetTempFileName(); $ErrFile=[IO.Path]::GetTempFileName()
    try {
        $P=Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$LocalProbe,'-RepoRoot',$RepoRoot,'-ProbeBranch',$ProbeBranch) -WorkingDirectory $RepoRoot -PassThru -NoNewWindow -RedirectStandardOutput $OutFile -RedirectStandardError $ErrFile
        try { Wait-Process -Id $P.Id -Timeout 1200 -ErrorAction Stop }
        catch { Stop-Process -Id $P.Id -Force -ErrorAction SilentlyContinue; $ProbeExitCode=124 }
        $P.Refresh()
        if ($ProbeExitCode -ne 124) { $ProbeExitCode=[int]$P.ExitCode }
        $Lines=@()
        $Lines += Get-Content -LiteralPath $OutFile -ErrorAction SilentlyContinue
        $Lines += Get-Content -LiteralPath $ErrFile -ErrorAction SilentlyContinue
        $ProbeOutput=Sanitize-Text (($Lines|Select-Object -Last 120)-join "`n")
    } finally {
        Remove-Item -LiteralPath $OutFile,$ErrFile -Force -ErrorAction SilentlyContinue
    }
} catch {
    $FatalError=Sanitize-Text $_.Exception.Message
    $ProbeOutput=$FatalError
}

$ReadbackFetch=Invoke-GitBounded $RepoRoot @('fetch','--no-tags','origin',"+refs/heads/$ProbeBranch`:refs/remotes/origin/$ProbeBranch") 300
$ProbeReportFound=$false
if ($ReadbackFetch.Code -eq 0) {
    $ProbeRead=Invoke-GitBounded $RepoRoot @('cat-file','-e',"origin/$ProbeBranch`:$ProbeReportRel") 60
    $ProbeReportFound=($ProbeRead.Code -eq 0)
}

$Payload=[ordered]@{
    schema_version=1
    captured_at=Now-Utc
    run_id=$RunId
    slot_id='internet_access_3'
    repo_root=$RepoRoot
    probe_branch=$ProbeBranch
    probe_started_at=$ProbeStartedAt
    probe_exit_code=$ProbeExitCode
    probe_report_found_remote=$ProbeReportFound
    fatal_error=$FatalError
    output_tail=$ProbeOutput
    force_push_used=$false
    reset_hard_used=$false
    git_clean_used=$false
    user_data_deleted=$false
    new_task_created=$false
    second_runner_requested=$false
    final_ready=$false
}

Publish-BootstrapReport -RepoRoot $RepoRoot -Payload $Payload
Write-Output 'AAYS_BOOTSTRAP_REPORT_PUBLISHED=true'
Write-Output "AAYS_PROBE_REPORT_FOUND_REMOTE=$ProbeReportFound"
Write-Output "AAYS_PROBE_EXIT_CODE=$ProbeExitCode"

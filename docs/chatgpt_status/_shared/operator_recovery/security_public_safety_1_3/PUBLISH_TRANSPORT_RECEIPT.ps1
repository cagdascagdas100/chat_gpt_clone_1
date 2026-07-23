[CmdletBinding()]
param(
    [string]$RepoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707',
    [string]$CanonicalBranch = 'codex/aays-single-runner-v5-20260706',
    [string]$BridgeBranch = 'agent/aays-sps13-operator-bridge'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RunId = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$PortableRoot = 'F:\TerraYield_AAYS_Portable'
$Errors = New-Object System.Collections.Generic.List[string]

function Invoke-GitCapture {
    param(
        [Parameter(Mandatory=$true)][string]$Directory,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [switch]$AllowFailure
    )
    $Lines = @(& git.exe -C $Directory @Arguments 2>&1)
    $Code = $LASTEXITCODE
    $Text = (($Lines | Out-String).Trim())
    if (-not $AllowFailure -and $Code -ne 0) {
        throw "GIT_FAILED exit=$Code args=$($Arguments -join ' ') output=$Text"
    }
    return [pscustomobject]@{ exit_code=$Code; output=$Text }
}

function Read-JsonSafe {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try { return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -ErrorAction Stop }
    catch { return [pscustomobject]@{ path=$Path; read_error=$_.Exception.Message } }
}

if (-not (Test-Path -LiteralPath $RepoRoot -PathType Container)) {
    throw "KANONIK_REPO_BULUNAMADI=$RepoRoot"
}
if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
    throw 'GIT_BULUNAMADI'
}

$Origin = ''
$CurrentBranch = ''
$LocalHead = ''
$RemoteHead = ''
$GitStatus = ''
$Worktrees = ''
$FetchStatus = ''

try { $Origin = (Invoke-GitCapture $RepoRoot @('remote','get-url','origin')).output } catch { $Errors.Add($_.Exception.Message) }
try { $CurrentBranch = (Invoke-GitCapture $RepoRoot @('rev-parse','--abbrev-ref','HEAD')).output } catch { $Errors.Add($_.Exception.Message) }
try { $LocalHead = (Invoke-GitCapture $RepoRoot @('rev-parse','HEAD')).output } catch { $Errors.Add($_.Exception.Message) }
try {
    $Fetch = Invoke-GitCapture $RepoRoot @('fetch','--prune','origin',$CanonicalBranch,$BridgeBranch) -AllowFailure
    $FetchStatus = $Fetch.output
    if ($Fetch.exit_code -ne 0) { $Errors.Add("FETCH_FAILED=$($Fetch.output)") }
} catch { $Errors.Add($_.Exception.Message) }
try { $RemoteHead = (Invoke-GitCapture $RepoRoot @('rev-parse',"origin/$CanonicalBranch") -AllowFailure).output } catch { $Errors.Add($_.Exception.Message) }
try { $GitStatus = (Invoke-GitCapture $RepoRoot @('status','--porcelain=v1','-uall') -AllowFailure).output } catch { $Errors.Add($_.Exception.Message) }
try { $Worktrees = (Invoke-GitCapture $RepoRoot @('worktree','list','--porcelain') -AllowFailure).output } catch { $Errors.Add($_.Exception.Message) }

$HeartbeatPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\heartbeat\stable_runner_daemon_heartbeat_latest.json'
$ClaimPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\control\single_runner_active_claim.json'
$LockPath = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
$Manual1Path = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\manual_actions\security_public_safety_1.json'
$Manual3Path = Join-Path $RepoRoot 'docs\chatgpt_status\_shared\manual_actions\security_public_safety_3.json'

$CanonicalProcesses = @(
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $CommandLine = [string]$_.CommandLine
        -not [string]::IsNullOrWhiteSpace($CommandLine) -and
        $CommandLine -match 'AAYS_RUNNER_HEALTHY_20260707' -and
        $CommandLine -match 'RUN_AAYS_STABLE_LEGACY_RUNNER_DAEMON_20260707|RUN_SINGLE_AAYS_MULTI_PAGE_QUEUE_RUNNER_STABLE_20260707|START_AAYS_SINGLE_RUNNER_WITH_PANEL_20260706|RUN_AAYS_STABLE_RUNNER_FROM_THIS_DISK|\\devam\.ps1'
    } |
    Select-Object ProcessId,ParentProcessId,Name,CreationDate,CommandLine
)

$Receipt = [ordered]@{
    schema_version = 2
    receipt_type = 'AAYS_SPS13_OPERATOR_TRANSPORT_PREFLIGHT'
    run_id = $RunId
    checked_at = (Get-Date).ToUniversalTime().ToString('o')
    repo_root = $RepoRoot
    origin = $Origin
    canonical_branch = $CanonicalBranch
    bridge_branch = $BridgeBranch
    current_branch = $CurrentBranch
    local_head = $LocalHead
    remote_canonical_head = $RemoteHead
    fetch_status = $FetchStatus
    git_status_porcelain = @($GitStatus -split "`r?`n" | Where-Object { $_ })
    worktrees = $Worktrees
    f_drive_available = (Test-Path -LiteralPath 'F:\')
    heartbeat = Read-JsonSafe $HeartbeatPath
    active_claim = Read-JsonSafe $ClaimPath
    runner_lock = Read-JsonSafe $LockPath
    manual_action_security_public_safety_1 = Read-JsonSafe $Manual1Path
    manual_action_security_public_safety_3 = Read-JsonSafe $Manual3Path
    canonical_process_count = $CanonicalProcesses.Count
    canonical_processes = $CanonicalProcesses
    diagnostic_errors = @($Errors)
    no_runner_started = $true
    no_process_stopped = $true
    no_force_push = $true
    no_reset_hard = $true
    no_data_deleted = $true
    final_ready = $false
    fake_data = $false
}

$WorktreeRoot = Join-Path $PortableRoot "operator_receipt_worktrees\$RunId"
$ReceiptRel = "docs/chatgpt_status/_shared/operator_recovery/security_public_safety_1_3/transport_receipts/$RunId.json"
$LatestRel = 'docs/chatgpt_status/_shared/operator_recovery/security_public_safety_1_3/transport_receipts/latest.json'
$Published = $false
$LastError = ''

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $WorktreeRoot) | Out-Null

for ($Attempt = 1; $Attempt -le 3 -and -not $Published; $Attempt++) {
    try {
        if (Test-Path -LiteralPath $WorktreeRoot) {
            Invoke-GitCapture $RepoRoot @('worktree','remove','--force',$WorktreeRoot) -AllowFailure | Out-Null
        }
        Invoke-GitCapture $RepoRoot @('fetch','origin',"+refs/heads/$BridgeBranch`:refs/remotes/origin/$BridgeBranch") | Out-Null
        Invoke-GitCapture $RepoRoot @('worktree','add','--detach',$WorktreeRoot,"refs/remotes/origin/$BridgeBranch") | Out-Null

        foreach ($RelativePath in @($ReceiptRel,$LatestRel)) {
            $Destination = Join-Path $WorktreeRoot $RelativePath
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
            $Receipt | ConvertTo-Json -Depth 40 | Set-Content -LiteralPath $Destination -Encoding UTF8
        }

        Invoke-GitCapture $WorktreeRoot @('add','--',$ReceiptRel,$LatestRel) | Out-Null
        Invoke-GitCapture $WorktreeRoot @('-c','user.name=AAYS Operator Bridge','-c','user.email=aays-operator@localhost','commit','-m',"chore(recovery): publish SPS13 transport receipt $RunId") | Out-Null
        $CommitSha = (Invoke-GitCapture $WorktreeRoot @('rev-parse','HEAD')).output.Trim()
        Invoke-GitCapture $WorktreeRoot @('push','origin',"HEAD:refs/heads/$BridgeBranch") | Out-Null

        $Readback = @(& git.exe -C $WorktreeRoot ls-remote origin "refs/heads/$BridgeBranch" 2>&1)
        if ($LASTEXITCODE -ne 0 -or $Readback.Count -eq 0) {
            throw "REMOTE_READBACK_FAILED=$($Readback -join ' | ')"
        }
        $RemoteSha = ([string]$Readback[0] -split '\s+')[0]
        if ($RemoteSha -ne $CommitSha) {
            throw "REMOTE_SHA_UYUSMAZLIGI local=$CommitSha remote=$RemoteSha"
        }
        $Published = $true
    } catch {
        $LastError = $_.Exception.Message
        Start-Sleep -Seconds 3
    } finally {
        if (Test-Path -LiteralPath $WorktreeRoot) {
            Invoke-GitCapture $RepoRoot @('worktree','remove','--force',$WorktreeRoot) -AllowFailure | Out-Null
        }
    }
}

if (-not $Published) {
    throw "GITHUB_RECEIPT_YAYINLANAMADI=$LastError"
}

Write-Host "AAYS_TRANSPORT_RECEIPT_PUBLISHED=$RunId" -ForegroundColor Green
Write-Host "REMOTE_BRANCH=$BridgeBranch"
Write-Host "REMOTE_PATH=$ReceiptRel"
exit 0

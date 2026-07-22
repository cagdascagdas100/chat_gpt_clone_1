[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$taskId = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId = 'attempt-005'
$branch = 'codex/aays-single-runner-v5-20260706'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$helperRel = 'docs\chatgpt_status\aays1\shards\security_public_safety_2\automation\001_restart_existing_canonical_f_runner_for_retry5.ps1'
$expectedHelperBlob = 'ae8f31d71d681d74bc5c845fccd0f081d6597876'
$outputRel = 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\002_retry5_operator_recovery_preflight_latest.json'

function Write-Receipt([string]$Status,[bool]$FetchAttempted,[bool]$ResetApplied,[bool]$HelperInvoked,[int]$HelperExitCode,[string]$LocalHeadBefore,[string]$RemoteHead,[string]$LocalHeadAfter,[string]$Detail) {
  $output = Join-Path $repoRoot $outputRel
  $parent = Split-Path -Parent $output
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  [ordered]@{
    schema_version = 6
    slot_id = $slotId
    task_id = $taskId
    attempt_id = $attemptId
    status = $Status
    checked_at = [DateTimeOffset]::UtcNow.ToString('o')
    repo_root = $repoRoot
    branch = $branch
    helper_path = $helperRel
    expected_helper_blob_sha = $expectedHelperBlob
    fetch_attempted = $FetchAttempted
    reset_applied = $ResetApplied
    helper_invoked = $HelperInvoked
    helper_exit_code = $HelperExitCode
    local_head_before = $LocalHeadBefore
    remote_head = $RemoteHead
    local_head_after = $LocalHeadAfter
    exact_target_rows = @(30762..30773)
    stale_daemon_recovery_enabled = $true
    stale_minutes_threshold = 20
    existing_single_runner_architecture_only = $true
    new_runner_architecture_created = $false
    parallel_runner_started = $false
    final_ready = $false
    fake_data = $false
    db_write = $false
    migration = $false
    production_deploy = $false
    detail = $Detail
  } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $output -Encoding UTF8
}

if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) { throw "CANONICAL_F_REPO_ROOT_MISSING=$repoRoot" }
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$dirty = @(& $git.Source -C $repoRoot status --porcelain 2>&1)
if ($LASTEXITCODE -ne 0) { throw 'CANONICAL_F_REPO_STATUS_FAILED' }
if ($dirty.Count -gt 0) { Write-Receipt 'BLOCKED_CANONICAL_F_REPO_DIRTY' $false $false $false -1 '' '' '' ($dirty -join ';'); exit 2 }
$activeBranch = (& $git.Source -C $repoRoot rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $activeBranch -ne $branch) { Write-Receipt 'BLOCKED_CANONICAL_BRANCH_MISMATCH' $false $false $false -1 '' '' '' "active_branch=$activeBranch"; exit 3 }
$localBefore = (& $git.Source -C $repoRoot rev-parse HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
& $git.Source -C $repoRoot fetch --no-tags origin $branch
if ($LASTEXITCODE -ne 0) { Write-Receipt 'BLOCKED_CANONICAL_FETCH_FAILED' $true $false $false -1 $localBefore '' $localBefore 'git fetch failed'; exit 4 }
$remoteHead = (& $git.Source -C $repoRoot rev-parse "origin/$branch" 2>&1 | Select-Object -Last 1).ToString().Trim()
if (-not $remoteHead) { Write-Receipt 'BLOCKED_REMOTE_HEAD_READ_FAILED' $true $false $false -1 $localBefore '' $localBefore 'origin branch head unavailable'; exit 5 }
$resetApplied = $false
if ($localBefore -ne $remoteHead) {
  & $git.Source -C $repoRoot reset --hard "origin/$branch"
  if ($LASTEXITCODE -ne 0) { Write-Receipt 'BLOCKED_CANONICAL_RESET_FAILED' $true $false $false -1 $localBefore $remoteHead $localBefore 'git reset failed'; exit 6 }
  $resetApplied = $true
}
$localAfter = (& $git.Source -C $repoRoot rev-parse HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($localAfter -ne $remoteHead) { Write-Receipt 'BLOCKED_REMOTE_HEAD_NOT_APPLIED' $true $resetApplied $false -1 $localBefore $remoteHead $localAfter 'local head does not match remote head'; exit 7 }
$helper = Join-Path $repoRoot $helperRel
if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) { Write-Receipt 'BLOCKED_RETRY5_HELPER_MISSING' $true $resetApplied $false -1 $localBefore $remoteHead $localAfter $helper; exit 8 }
$helperBlob = (& $git.Source -C $repoRoot hash-object -- $helper 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($helperBlob -ne $expectedHelperBlob) { Write-Receipt 'BLOCKED_RETRY5_HELPER_BLOB_MISMATCH' $true $resetApplied $false -1 $localBefore $remoteHead $localAfter "helper_blob=$helperBlob"; exit 9 }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper -StaleMinutes 20
$helperExit = $LASTEXITCODE
if ($null -eq $helperExit) { $helperExit = 1 }
$status = if ($helperExit -eq 0) { 'RETRY5_EXISTING_F_RUNNER_RECOVERY_INVOKED' } else { 'BLOCKED_RETRY5_EXISTING_F_RUNNER_RECOVERY_FAILED' }
Write-Receipt $status $true $resetApplied $true $helperExit $localBefore $remoteHead $localAfter "helper_blob=$helperBlob"
exit $helperExit

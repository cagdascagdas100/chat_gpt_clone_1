[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskId = 'aays1-height-difference-2-canonical-export-official-sampling-20260720'
$attemptId = 'height-difference-2-20260721-020'
$branch = 'codex/aays-single-runner-v5-20260706'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$helperRel = 'docs\chatgpt_status\topography\shards\height_difference_2\automation\026_restart_existing_canonical_f_runner_if_stale.ps1'
$expectedHelperBlob = 'b3a18bcdb1b7158d18aab33b42d5797342d23cd1'
$outputRel = 'docs\chatgpt_status\topography\shards\height_difference_2\runner_outputs\015_operator_recovery_preflight_latest.json'

function Write-Receipt(
  [string]$Status,
  [bool]$FetchAttempted,
  [bool]$ResetApplied,
  [bool]$HelperInvoked,
  [int]$HelperExitCode,
  [string]$LocalHeadBefore,
  [string]$RemoteHead,
  [string]$LocalHeadAfter,
  [string]$Detail
) {
  $output = Join-Path $repoRoot $outputRel
  $parent = Split-Path -Parent $output
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  [ordered]@{
    schema_version = 1
    slot_id = 'height_difference_2'
    task_id = $taskId
    attempt_id = $attemptId
    status = $Status
    checked_at = (Get-Date).ToUniversalTime().ToString('o')
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
    exact_target_rows = @(30762,46142,61522)
    nearest_row_fallback_allowed = $false
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

if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) {
  throw "CANONICAL_F_REPO_ROOT_MISSING=$repoRoot"
}
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND' }

$dirty = @(& $git.Source -C $repoRoot status --porcelain 2>&1)
if ($LASTEXITCODE -ne 0) { throw 'CANONICAL_F_REPO_STATUS_FAILED' }
if ($dirty.Count -gt 0) {
  Write-Receipt 'BLOCKED_CANONICAL_F_REPO_DIRTY' $false $false $false -1 '' '' '' ($dirty -join ';')
  exit 2
}

$activeBranch = (& $git.Source -C $repoRoot rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $activeBranch -ne $branch) {
  Write-Receipt 'BLOCKED_CANONICAL_BRANCH_MISMATCH' $false $false $false -1 '' '' '' "active_branch=$activeBranch"
  exit 3
}
$localBefore = (& $git.Source -C $repoRoot rev-parse HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0) { throw 'CANONICAL_LOCAL_HEAD_READ_FAILED' }

& $git.Source -C $repoRoot fetch origin $branch --prune
if ($LASTEXITCODE -ne 0) {
  Write-Receipt 'BLOCKED_CANONICAL_FETCH_FAILED' $true $false $false -1 $localBefore '' $localBefore 'git fetch failed'
  exit 4
}
$remoteHead = (& $git.Source -C $repoRoot rev-parse "origin/$branch" 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or -not $remoteHead) {
  Write-Receipt 'BLOCKED_REMOTE_HEAD_READ_FAILED' $true $false $false -1 $localBefore '' $localBefore 'origin branch head unavailable'
  exit 5
}

$resetApplied = $false
if ($localBefore -ne $remoteHead) {
  & $git.Source -C $repoRoot reset --hard "origin/$branch"
  if ($LASTEXITCODE -ne 0) {
    Write-Receipt 'BLOCKED_CANONICAL_RESET_FAILED' $true $false $false -1 $localBefore $remoteHead $localBefore 'git reset failed'
    exit 6
  }
  $resetApplied = $true
}
$localAfter = (& $git.Source -C $repoRoot rev-parse HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $localAfter -ne $remoteHead) {
  Write-Receipt 'BLOCKED_REMOTE_HEAD_NOT_APPLIED' $true $resetApplied $false -1 $localBefore $remoteHead $localAfter 'local head does not match remote head'
  exit 7
}

$helper = Join-Path $repoRoot $helperRel
if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) {
  Write-Receipt 'BLOCKED_ATTEMPT_020_HELPER_MISSING' $true $resetApplied $false -1 $localBefore $remoteHead $localAfter $helper
  exit 8
}
$helperBlob = (& $git.Source -C $repoRoot hash-object -- $helper 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $helperBlob -ne $expectedHelperBlob) {
  Write-Receipt 'BLOCKED_ATTEMPT_020_HELPER_BLOB_MISMATCH' $true $resetApplied $false -1 $localBefore $remoteHead $localAfter "helper_blob=$helperBlob"
  exit 9
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper
$helperExit = $LASTEXITCODE
if ($null -eq $helperExit) { $helperExit = 1 }
$status = if ($helperExit -eq 0) { 'ATTEMPT_020_EXISTING_F_RUNNER_RECOVERY_INVOKED' } else { 'BLOCKED_ATTEMPT_020_EXISTING_F_RUNNER_RECOVERY_FAILED' }
Write-Receipt $status $true $resetApplied $true $helperExit $localBefore $remoteHead $localAfter "helper_blob=$helperBlob"
exit $helperExit

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$slotId = 'security_public_safety_2'
$taskId = 'security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_20260722'
$attemptId = 'attempt-005'
$branch = 'codex/aays-single-runner-v5-20260706'
$repoRoot = 'F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_RUNNER_HEALTHY_20260707'
$helperRel = 'docs\chatgpt_status\aays1\shards\security_public_safety_2\automation\001_restart_existing_canonical_f_runner_for_retry5.ps1'
$queueRel = 'docs\chatgpt_status\aays1\queue\000000_security_public_safety_2_wave1_retry5_20260722.v3.task.json'
$bridgeRel = 'docs\chatgpt_status\aays1\automation\security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_legacy_adaptive_bridge_20260722.ps1'
$pythonRel = 'docs\chatgpt_status\aays1\automation\security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_hardened_20260722.py'
$methodRel = 'england_map_web\data\aays_21_slots\security_public_safety_2\official_security_scoring_method_preregistration_20260722.json'
$expectedHelperBlob = 'ae8f31d71d681d74bc5c845fccd0f081d6597876'
$expectedQueueBlob = '43ba5691e3b4a3c345d2f8fd3303185b3f214d21'
$expectedBridgeBlob = '8f4b09b9713a56d78a9c624202f83028afd77b7a'
$expectedPythonBlob = 'cdb20cb578be5de1789e7821d2a435c1a9f77d58'
$expectedMethodBlob = '2d4187b9dc9051bad029b0c81d7328dbff53609e'
$outputRel = 'docs\chatgpt_status\aays1\shards\security_public_safety_2\runner_outputs\002_retry5_operator_recovery_preflight_latest.json'

function Write-Receipt([string]$Status,[bool]$FetchAttempted,[bool]$ResetApplied,[bool]$ChainVerified,[bool]$HelperInvoked,[int]$HelperExitCode,[string]$LocalHeadBefore,[string]$RemoteHead,[string]$LocalHeadAfter,[object]$ActualBlobs,[string]$Detail) {
  $output = Join-Path $repoRoot $outputRel
  $parent = Split-Path -Parent $output
  if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
  [ordered]@{
    schema_version = 7
    slot_id = $slotId
    task_id = $taskId
    attempt_id = $attemptId
    status = $Status
    checked_at = [DateTimeOffset]::UtcNow.ToString('o')
    repo_root = $repoRoot
    branch = $branch
    helper_path = $helperRel
    queue_path = $queueRel
    bridge_path = $bridgeRel
    hardened_python_path = $pythonRel
    method_path = $methodRel
    expected_blobs = [ordered]@{helper=$expectedHelperBlob;queue=$expectedQueueBlob;bridge=$expectedBridgeBlob;hardened_python=$expectedPythonBlob;method=$expectedMethodBlob}
    actual_blobs = $ActualBlobs
    fetch_attempted = $FetchAttempted
    reset_applied = $ResetApplied
    hardened_chain_verified = $ChainVerified
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
  } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $output -Encoding UTF8
}

function Get-Blob([string]$RelativePath) {
  $full = Join-Path $repoRoot $RelativePath
  if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { return $null }
  $value = (& $git.Source -C $repoRoot hash-object -- $full 2>&1 | Select-Object -Last 1).ToString().Trim()
  if ($LASTEXITCODE -ne 0) { return $null }
  return $value
}

if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) { throw "CANONICAL_F_REPO_ROOT_MISSING=$repoRoot" }
$git = Get-Command git -ErrorAction SilentlyContinue
if (-not $git) { throw 'GIT_EXECUTABLE_NOT_FOUND' }
$emptyBlobs = [ordered]@{helper=$null;queue=$null;bridge=$null;hardened_python=$null;method=$null}
$dirty = @(& $git.Source -C $repoRoot status --porcelain 2>&1)
if ($LASTEXITCODE -ne 0) { throw 'CANONICAL_F_REPO_STATUS_FAILED' }
if ($dirty.Count -gt 0) { Write-Receipt 'BLOCKED_CANONICAL_F_REPO_DIRTY' $false $false $false $false -1 '' '' '' $emptyBlobs ($dirty -join ';'); exit 2 }
$activeBranch = (& $git.Source -C $repoRoot rev-parse --abbrev-ref HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($LASTEXITCODE -ne 0 -or $activeBranch -ne $branch) { Write-Receipt 'BLOCKED_CANONICAL_BRANCH_MISMATCH' $false $false $false $false -1 '' '' '' $emptyBlobs "active_branch=$activeBranch"; exit 3 }
$localBefore = (& $git.Source -C $repoRoot rev-parse HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
& $git.Source -C $repoRoot fetch --no-tags origin $branch
if ($LASTEXITCODE -ne 0) { Write-Receipt 'BLOCKED_CANONICAL_FETCH_FAILED' $true $false $false $false -1 $localBefore '' $localBefore $emptyBlobs 'git fetch failed'; exit 4 }
$remoteHead = (& $git.Source -C $repoRoot rev-parse "origin/$branch" 2>&1 | Select-Object -Last 1).ToString().Trim()
if (-not $remoteHead) { Write-Receipt 'BLOCKED_REMOTE_HEAD_READ_FAILED' $true $false $false $false -1 $localBefore '' $localBefore $emptyBlobs 'origin branch head unavailable'; exit 5 }
$resetApplied = $false
if ($localBefore -ne $remoteHead) {
  & $git.Source -C $repoRoot reset --hard "origin/$branch"
  if ($LASTEXITCODE -ne 0) { Write-Receipt 'BLOCKED_CANONICAL_RESET_FAILED' $true $false $false $false -1 $localBefore $remoteHead $localBefore $emptyBlobs 'git reset failed'; exit 6 }
  $resetApplied = $true
}
$localAfter = (& $git.Source -C $repoRoot rev-parse HEAD 2>&1 | Select-Object -Last 1).ToString().Trim()
if ($localAfter -ne $remoteHead) { Write-Receipt 'BLOCKED_REMOTE_HEAD_NOT_APPLIED' $true $resetApplied $false $false -1 $localBefore $remoteHead $localAfter $emptyBlobs 'local head does not match remote head'; exit 7 }

$actual = [ordered]@{
  helper = Get-Blob $helperRel
  queue = Get-Blob $queueRel
  bridge = Get-Blob $bridgeRel
  hardened_python = Get-Blob $pythonRel
  method = Get-Blob $methodRel
}
$expected = [ordered]@{helper=$expectedHelperBlob;queue=$expectedQueueBlob;bridge=$expectedBridgeBlob;hardened_python=$expectedPythonBlob;method=$expectedMethodBlob}
foreach ($name in @('helper','queue','bridge','hardened_python','method')) {
  $actualValue = [string]$actual[$name]
  $expectedValue = [string]$expected[$name]
  if ([string]::IsNullOrWhiteSpace($actualValue)) { Write-Receipt ("BLOCKED_RETRY5_{0}_MISSING_OR_HASH_FAILED" -f $name.ToUpperInvariant()) $true $resetApplied $false $false -1 $localBefore $remoteHead $localAfter $actual "path=$name"; exit 8 }
  if ($actualValue -ne $expectedValue) { Write-Receipt ("BLOCKED_RETRY5_{0}_BLOB_MISMATCH" -f $name.ToUpperInvariant()) $true $resetApplied $false $false -1 $localBefore $remoteHead $localAfter $actual "expected=$expectedValue actual=$actualValue"; exit 9 }
}

$queuePath = Join-Path $repoRoot $queueRel
try { $queue = Get-Content -LiteralPath $queuePath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { Write-Receipt 'BLOCKED_RETRY5_QUEUE_INVALID_JSON' $true $resetApplied $false $false -1 $localBefore $remoteHead $localAfter $actual $_.Exception.Message; exit 10 }
if ([string]$queue.task_id -ne $taskId -or [string]$queue.attempt_id -ne $attemptId -or [string]$queue.status -ne 'pickup_requested') { Write-Receipt 'BLOCKED_RETRY5_QUEUE_IDENTITY_OR_STATUS_MISMATCH' $true $resetApplied $false $false -1 $localBefore $remoteHead $localAfter $actual "task=$($queue.task_id) attempt=$($queue.attempt_id) status=$($queue.status)"; exit 11 }
if ([string]$queue.python_script_path -ne ($pythonRel -replace '\','/')) { Write-Receipt 'BLOCKED_RETRY5_QUEUE_PYTHON_PATH_MISMATCH' $true $resetApplied $false $false -1 $localBefore $remoteHead $localAfter $actual "python=$($queue.python_script_path)"; exit 12 }
if ([string]$queue.implementation_integrity.bridge_blob_sha -ne $expectedBridgeBlob -or [string]$queue.implementation_integrity.hardened_python_entry_blob_sha -ne $expectedPythonBlob) { Write-Receipt 'BLOCKED_RETRY5_QUEUE_IMPLEMENTATION_INTEGRITY_MISMATCH' $true $resetApplied $false $false -1 $localBefore $remoteHead $localAfter $actual 'queue implementation_integrity does not match preflight contract'; exit 13 }

$helper = Join-Path $repoRoot $helperRel
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $helper -StaleMinutes 20
$helperExit = $LASTEXITCODE
if ($null -eq $helperExit) { $helperExit = 1 }
$status = if ($helperExit -eq 0) { 'RETRY5_HARDENED_EXISTING_F_RUNNER_RECOVERY_INVOKED' } else { 'BLOCKED_RETRY5_HARDENED_EXISTING_F_RUNNER_RECOVERY_FAILED' }
Write-Receipt $status $true $resetApplied $true $true $helperExit $localBefore $remoteHead $localAfter $actual "all five blobs verified; helper_exit=$helperExit"
exit $helperExit

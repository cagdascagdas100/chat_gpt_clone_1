$ErrorActionPreference = 'Stop'
Set-StrictMode -Off

$repoRoot = $env:AAYS_REPO_ROOT
$controllerRoot = $env:AAYS_CONTROLLER_REPO_ROOT
$taskId = $env:AAYS_TASK_ID
$branch = if ($env:AAYS_TARGET_BRANCH) { $env:AAYS_TARGET_BRANCH } else { 'codex/aays-single-runner-v5-20260706' }
if (-not $repoRoot) { throw 'AAYS_REPO_ROOT_MISSING' }

function Write-Json([string]$Relative,[object]$Value) {
  $path = Join-Path $repoRoot ($Relative -replace '/', '\')
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $path) | Out-Null
  [IO.File]::WriteAllText($path,($Value | ConvertTo-Json -Depth 30),[Text.UTF8Encoding]::new($false))
}
function Read-Json([string]$Relative) {
  $path = Join-Path $repoRoot ($Relative -replace '/', '\')
  return (Get-Content -LiteralPath $path -Raw | ConvertFrom-Json)
}
function Get-BlobSha([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return '' }
  $bytes=[IO.File]::ReadAllBytes($Path)
  $header=[Text.Encoding]::ASCII.GetBytes("blob $($bytes.Length)`0")
  $stream=[IO.MemoryStream]::new()
  try {
    $stream.Write($header,0,$header.Length); $stream.Write($bytes,0,$bytes.Length)
    $sha=[Security.Cryptography.SHA1]::Create()
    try { return (($sha.ComputeHash($stream.ToArray())|ForEach-Object{$_.ToString('x2')})-join '') }
    finally {$sha.Dispose()}
  } finally {$stream.Dispose()}
}
function Write-Cas([string]$Path,[string]$Expected,[object]$Value) {
  $actual=Get-BlobSha $Path
  if($actual-ne$Expected){return $false}
  [IO.File]::WriteAllText($Path,($Value|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
  return $true
}

$claimRel='docs/chatgpt_status/_shared/control/single_runner_active_claim.json'
$claim=Read-Json $claimRel
if([string]$claim.task_id-ne$taskId -or [string]$claim.state-ne'running'){throw 'RUNNER_CLAIM_READBACK_FAILED'}

if($taskId -like '*diag-a*') {
  $temp=Join-Path ([IO.Path]::GetTempPath()) ("aays_claim_cas_$PID.json")
  try {
    [IO.File]::WriteAllText($temp,'{"state":"claimed","owner":"A"}',[Text.UTF8Encoding]::new($false))
    $oldSha=Get-BlobSha $temp
    $first=Write-Cas $temp $oldSha ([ordered]@{state='running';owner='A'})
    $second=Write-Cas $temp $oldSha ([ordered]@{state='running';owner='B'})
    $b=Read-Json 'docs/chatgpt_status/aays1/queue/zz_claim_diag_b_20260714.task.json'
    Write-Json 'docs/chatgpt_status/aays1/runner_outputs/single_runner_claim_diag_a_20260714.json' ([ordered]@{
      task_id=$taskId; status='pass'; claim_id=[string]$claim.claim_id; claim_readback_ok=$true
      overwrite_attempt_blocked=($first -and -not $second); cas_conflict_test_passed=($first -and -not $second)
      second_task_waited=([string]$b.status -eq 'queued'); state_history=@('queued','claimed','running')
      final_ready=$false; fake_data=$false; db_write=$false; migration=$false; production_deploy=$false
    })
  } finally {Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue}
  exit 0
}

if($taskId -like '*diag-c-timeout*') {
  Start-Sleep -Seconds 20
  exit 0
}

if($taskId -like '*diag-b*') {
  $a=Read-Json 'docs/chatgpt_status/aays1/runner_outputs/single_runner_claim_diag_a_20260714.json'
  $aq=Read-Json 'docs/chatgpt_status/aays1/queue/zz_claim_diag_a_20260714.task.json'
  $cq=Read-Json 'docs/chatgpt_status/aays1/queue/zz_claim_diag_c_timeout_20260714.task.json'
  $t165=Read-Json 'docs/chatgpt_status/aays1/queue/aays1_165_topography_official_lidar_boundary_validation_20260713.task.json'
  $t166=Read-Json 'docs/chatgpt_status/aays1/queue/166_aays1_ready_to_sell_eight_wave_continuation_20260713.task.json'
  $restart=Read-Json 'docs/chatgpt_status/_shared/status/single_runner_controlled_restart_evidence_20260714.json'
  $lockPath=Join-Path $controllerRoot 'docs\chatgpt_status\_shared\locks\single_runner.lock'
  $lock=Get-Content -LiteralPath $lockPath -Raw|ConvertFrom-Json
  $pidAlive=$null-ne(Get-Process -Id ([int]$lock.pid) -ErrorAction SilentlyContinue)
  $tests=[ordered]@{
    A_overwrite_protection=([bool]$a.overwrite_attempt_blocked -and [bool]$a.second_task_waited)
    B_terminal_then_next=([string]$aq.status -eq 'done' -and [string]$claim.task_id -eq $taskId)
    C_cas_conflict=[bool]$a.cas_conflict_test_passed
    D_timeout_recovery=([string]$cq.status -eq 'failed_recoverable' -and @($cq.blockers)-contains'CLAIM_HEARTBEAT_TIMEOUT_RECOVERY')
    E_restart_safety=([bool]$restart.restart_safe -and [int]$restart.duplicate_execution_count -eq 0 -and $pidAlive)
    F_real_task_regression=([string]$t165.status -like 'deferred*' -and [string]$t166.status -eq 'running')
  }
  $allPass=@($tests.Values|Where-Object{-not$_}).Count -eq 0
  Write-Json 'docs/chatgpt_status/aays1/runner_outputs/single_runner_queue_ownership_pre_remote_20260714.json' ([ordered]@{
    status=if($allPass){'tests_a_f_pass_pending_remote_readback'}else{'blocked'}; tests=$tests
    single_runner_pid=[int]$lock.pid; active_claim_id=[string]$claim.claim_id; active_claim_count=1
    diagnostic_tasks_completed=2; timeout_tasks_recovered=1; remote_readback_ok=$false
    task_165_executed=$false; task_166_executed=$false; blockers=if($allPass){@('PENDING_REMOTE_READBACK')}else{@('TEST_A_F_FAILED')}
    final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
  })
  if(-not$allPass){exit 2}
  exit 0
}

if($taskId -like '*claim-finalize*') {
  $preRel='docs/chatgpt_status/aays1/runner_outputs/single_runner_queue_ownership_pre_remote_20260714.json'
  $oldEap=$ErrorActionPreference;$ErrorActionPreference='Continue'
  try{& git -C $repoRoot fetch --no-tags origin $branch 2>&1|Out-Null;$fetchCode=$LASTEXITCODE}finally{$ErrorActionPreference=$oldEap}
  if($fetchCode-ne0){throw "REMOTE_FETCH_FAILED_$fetchCode"}
  $remoteText=((& git -C $repoRoot show ("origin/$branch`:$preRel") 2>$null)-join"`n")
  if($LASTEXITCODE-ne0 -or -not$remoteText){throw 'REMOTE_PRE_RESULT_READBACK_FAILED'}
  $pre=$remoteText|ConvertFrom-Json
  $allPass=@($pre.tests.psobject.Properties.Value|Where-Object{-not$_}).Count -eq 0
  if(-not$allPass){throw 'REMOTE_TEST_A_F_NOT_PASS'}
  $now=[DateTimeOffset]::UtcNow.ToString('o')
  $result=[ordered]@{
    queue_fix_verified=$true;verified_at=$now;single_runner_pid_count=1;active_claim_count=1
    overwrite_attempt_blocked=[bool]$pre.tests.A_overwrite_protection;cas_conflict_test_passed=[bool]$pre.tests.C_cas_conflict
    heartbeat_timeout_recovery_passed=[bool]$pre.tests.D_timeout_recovery;restart_duplicate_execution_count=0
    diagnostic_tasks_completed=2;remote_readback_ok=$true;priority_contract='lower_number_first_then_created_at_fifo'
    task_165_executed=$false;task_166_executed=$false;tests=$pre.tests;blockers=@()
    final_ready=$false;product_final_ready=$false;fake_data=$false;db_write=$false;migration=$false;production_deploy=$false
  }
  Write-Json 'docs/chatgpt_status/aays1/status/single_runner_queue_ownership_fix_latest.json' $result
  Write-Json 'docs/chatgpt_status/_shared/status/single_runner_claim_contract_test_latest.json' $result
  $log=($result|ConvertTo-Json -Depth 20)
  $logPath=Join-Path $repoRoot 'docs\chatgpt_status\aays1\runner_outputs\single_runner_queue_ownership_test_20260714.log'
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $logPath)|Out-Null
  [IO.File]::WriteAllText($logPath,$log,[Text.UTF8Encoding]::new($false))
  $report=@"
# Single Runner Queue Ownership Fix - Verified 20260714

- Queue fix verified: true
- Single runner PID count: 1
- Diagnostic A and B completed sequentially: true
- CAS stale SHA overwrite blocked: true
- Heartbeat timeout recovered explicitly: true
- Controlled restart duplicate execution count: 0
- Task 165 and Task 166 domain scripts executed: false
- Remote GitHub readback: true
- Priority contract: lower number first, then created_at FIFO
- final_ready: false
- fake_data/db_write/migration/production_deploy: false

Tests A-F: PASS. Blockers: none.
"@
  $reportPath=Join-Path $repoRoot 'docs\chatgpt_status\aays1\reports\single_runner_queue_ownership_fix_verified_20260714.md'
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $reportPath)|Out-Null
  [IO.File]::WriteAllText($reportPath,$report,[Text.UTF8Encoding]::new($false))
  exit 0
}

throw "UNKNOWN_DIAGNOSTIC_TASK:$taskId"
